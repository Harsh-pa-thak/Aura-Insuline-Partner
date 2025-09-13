# file: prediction_service.py (Upgraded for Personalization & Lazy Loading)

import os
import numpy as np
import joblib
# NOTE: We have REMOVED "from keras.models import load_model" from the top of the file.
from scipy import stats
import warnings

warnings.filterwarnings('ignore', category=UserWarning, module='keras')
warnings.filterwarnings('ignore', category=FutureWarning, module='keras')

# --- UPGRADED DYNAMIC MODEL LOADING & CACHING SYSTEM ---
MODEL_CACHE = {}
SCALER_CACHE = {}
DEFAULT_MODEL_PATH = 'glucose_predictor.h5'
DEFAULT_SCALER_PATH = 'scaler.gz'

LOOK_BACK = 12

def get_model_for_user(user_id: int):
    """
    Dynamically loads and caches a user's personalized model.
    This function LAZY LOADS Keras/TensorFlow to ensure fast server startup.
    """
    # --- LAZY LOADING PATTERN ---
    # By importing here, TensorFlow is only loaded when a prediction is
    # actually requested, not when the application first starts.
    from keras.models import load_model
    # --- END OF PATTERN ---

    user_model_path = f'glucose_predictor_user_{user_id}.h5'
    user_scaler_path = f'scaler_user_{user_id}.gz'
    
    if os.path.exists(user_model_path) and os.path.exists(user_scaler_path):
        model_path_to_load = user_model_path
        scaler_path_to_load = user_scaler_path
        print(f"--- [Predictor] Found personalized model for user {user_id}. ---")
    else:
        model_path_to_load = DEFAULT_MODEL_PATH
        scaler_path_to_load = DEFAULT_SCALER_PATH
        
    if model_path_to_load in MODEL_CACHE:
        return MODEL_CACHE[model_path_to_load], SCALER_CACHE[scaler_path_to_load]
    else:
        print(f"--- [Predictor] Loading model into cache for the first time: {model_path_to_load} ---")
        try:
            model = load_model(model_path_to_load)
            scaler = joblib.load(scaler_path_to_load)
            
            MODEL_CACHE[model_path_to_load] = model
            SCALER_CACHE[scaler_path_to_load] = scaler
            
            return model, scaler
        except Exception as e:
            print(f"--- [Predictor] FATAL ERROR: Could not load model file {model_path_to_load}. Error: {e} ---")
            if model_path_to_load == DEFAULT_MODEL_PATH:
                 raise IOError(f"Default model '{DEFAULT_MODEL_PATH}' is missing or corrupted.")
            else:
                 return get_model_for_user(0)

class GlucosePredictionError(Exception):
    """Custom exception for prediction errors"""
    pass

def validate_glucose_history(glucose_history: list) -> list:
    if not glucose_history or len(glucose_history) < LOOK_BACK:
        raise GlucosePredictionError(f"Insufficient history: need at least {LOOK_BACK} readings.")
    return [float(v) for v in glucose_history]

def apply_physiological_constraints(predictions: list, last_known_value: float) -> list:
    constrained = []
    prev_value = last_known_value
    MAX_CHANGE_RATE = 4
    for pred in predictions:
        if pred > prev_value + MAX_CHANGE_RATE: pred = prev_value + MAX_CHANGE_RATE
        elif pred < prev_value - MAX_CHANGE_RATE: pred = prev_value - MAX_CHANGE_RATE
        constrained.append(max(40, min(400, pred)))
        prev_value = pred
    return constrained

def calculate_trend_confidence(glucose_history: list) -> dict:
    recent_values = glucose_history[-LOOK_BACK:]
    slope, _, _, _, _ = stats.linregress(np.arange(len(recent_values)), recent_values)
    trend = "stable"
    if slope > 0.5: trend = "rising"
    elif slope < -0.5: trend = "falling"
    return {"trend": trend, "slope": round(slope, 2)}

def predict_future_glucose(user_id: int, recent_glucose_history: list, include_analysis: bool = False) -> dict:
    try:
        model, scaler = get_model_for_user(user_id)
        cleaned_history = validate_glucose_history(recent_glucose_history)
        
        input_data = np.array(cleaned_history[-LOOK_BACK:]).reshape(-1, 1)
        scaled_input = scaler.transform(input_data)
        
        predictions = []
        current_sequence = scaled_input.reshape((1, LOOK_BACK, 1))
        
        for _ in range(12):
            pred_scaled = model.predict(current_sequence, verbose=0)
            pred_glucose = scaler.inverse_transform(pred_scaled)[0][0]
            predictions.append(pred_glucose)
            new_sequence = np.append(current_sequence[0][1:], pred_scaled)
            current_sequence = new_sequence.reshape((1, LOOK_BACK, 1))
        
        last_known = cleaned_history[-1]
        final_predictions = apply_physiological_constraints(predictions, last_known)
        int_predictions = [int(round(p)) for p in final_predictions]
        
        response = {
            "prediction": int_predictions, "status": "success",
            "last_known_glucose": int(last_known)
        }
        
        if include_analysis:
            response["analysis"] = calculate_trend_confidence(cleaned_history)
        
        return response
        
    except (GlucosePredictionError, IOError) as e:
        return {"prediction": [], "status": "error", "error_message": str(e)}
    except Exception as e:
        return {"prediction": [], "status": "error", "error_message": f"Unexpected prediction error: {str(e)}"}

def generate_hybrid_prediction(user_id: int, recent_glucose_history: list, future_events: dict = None) -> dict:
    baseline_response = predict_future_glucose(user_id, recent_glucose_history, include_analysis=True)
    
    if baseline_response["status"] == "error":
        return baseline_response
        
    adjusted_predictions = list(baseline_response["prediction"])
    if future_events:
        carbs = future_events.get("carbs", 0)
        if carbs > 0:
            carb_impact = (carbs / 10) * 3.5 / 12
            for i in range(len(adjusted_predictions)):
                if i >= 3: adjusted_predictions[i] += carb_impact * (i - 2)
        
        activity_type = future_events.get("activity_type")
        if activity_type:
            activity_impact = 25 / 12
            for i in range(len(adjusted_predictions)):
                if i >= 2: adjusted_predictions[i] -= activity_impact

    last_known = baseline_response["last_known_glucose"]
    final_predictions = apply_physiological_constraints(adjusted_predictions, last_known)
    
    baseline_response["adjusted_prediction"] = [int(round(p)) for p in final_predictions]
    baseline_response["original_prediction"] = baseline_response.pop("prediction")
    
    variability = baseline_response.get("analysis", {}).get("variability", 5)
    baseline_response["prediction_bounds"] = {
        "upper": [int(round(p + (variability * (1 + i*0.1)))) for i, p in enumerate(final_predictions)],
        "lower": [int(round(p - (variability * (1 + i*0.1)))) for i, p in enumerate(final_predictions)]
    }

    return baseline_response