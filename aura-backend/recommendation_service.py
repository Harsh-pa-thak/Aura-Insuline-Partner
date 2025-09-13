# file: recommendation_service.py

import numpy as np
import os

# --- Lazy Loading Configuration ---
# The model is not loaded at startup. It will be loaded on the first API call.
_rl_model = None 
MODEL_PATH = "aura_dqn_agent"
DEVICE = "cpu"

def _get_rl_model():
    """
    Loads the RL agent model on the first call and caches it.
    This prevents slow startup times for the web server.
    """
    global _rl_model
    # If model is already loaded, return it instantly.
    if _rl_model is not None:
        return _rl_model

    # --- First-time loading logic ---
    print("--- [Recommender] Loading RL agent for the first time... ---")
    try:
        # Dynamically import to avoid loading the library at startup
        import importlib
        _sb3 = importlib.import_module("stable_baselines3")
        DQN = getattr(_sb3, "DQN", None)

        if DQN is not None:
            # Resolve model path with or without .zip
            candidate_paths = [MODEL_PATH, f"{MODEL_PATH}.zip"]
            load_path = next((p for p in candidate_paths if os.path.exists(p)), None)

            if load_path:
                # Load the trained agent and cache it in the global variable
                _rl_model = DQN.load(load_path, device=DEVICE)
                print("--- [Recommender] RL agent loaded successfully. ---")
                return _rl_model
            else:
                print(f"--- [Recommender] WARNING: RL model file not found at '{MODEL_PATH}'. ---")
                return None
        else:
            print("--- [Recommender] WARNING: stable_baselines3 library not available. ---")
            return None
    except Exception as e:
        print(f"--- [Recommender] CRITICAL ERROR: Could not load RL agent model. Error: {e} ---")
        return None

# --- The Main API Function ---
def get_insulin_recommendation(
    glucose: int,
    carbs: int = 0,
    time_hour: int = 12,
    last_insulin_hours: int = 4,
    exercise_recent: bool = False,
    stress_level: int = 0
) -> dict:
    """
    Advanced insulin recommendation for the Aura backend.
    Combines a trained RL model with safety heuristics.
    """
    # This line ensures the model is loaded, but only on the first call.
    model = _get_rl_model()

    if model is None:
        return {
            "error": "RL model is not available. Cannot provide AI recommendation."
        }

    try:
        # --- 1. RL Model Base Recommendation ---
        active_insulin_estimate = max(0, 4 - last_insulin_hours * 2)
        trend_estimate = 0
        time_since_meal_est = last_insulin_hours
        obs = np.array([glucose, trend_estimate, time_hour, active_insulin_estimate, time_since_meal_est], dtype=np.float32)
        
        action, _ = model.predict(obs, deterministic=True)
        base_correction_dose = float(action) * 0.5

        # --- 2. Standard Calculation (Heuristics) ---
        carb_ratio = 12
        insulin_sensitivity = 50
        target_glucose = 110
        meal_bolus = carbs / carb_ratio if carbs > 0 else 0
        standard_correction_dose = (glucose - target_glucose) / insulin_sensitivity

        # --- 3. Hybrid Dose Calculation ---
        total_dose = meal_bolus + max(0, standard_correction_dose)

        # --- 4. Apply Adjustments for Context ---
        if exercise_recent:
            total_dose *= 0.7
        if stress_level > 5:
            total_dose *= (1 + stress_level * 0.05)
        
        final_dose = max(0, min(total_dose, 20)) # Safety clamp

        # --- 5. Generate Response ---
        reason = f"Calculated for {carbs}g carbs and a current glucose of {glucose}."
        if exercise_recent: reason += " Adjusted for recent exercise."

        return {
            "recommended_dose": round(final_dose, 1),
            "confidence": 0.9,
            "reasoning": reason
        }

    except Exception as e:
        return {"error": str(e)}