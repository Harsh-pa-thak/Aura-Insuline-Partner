# file: intelligent_core.py

# DO NOT import EnhancedNLPProcessor at the top level
from prediction_service import generate_hybrid_prediction
from recommendation_service import get_insulin_recommendation
import database as db

# --- Lazy Loading Configuration ---
_nlp_processor = None

def _get_nlp_processor():
    """Loads the NLP Processor on the first call and caches it."""
    global _nlp_processor
    if _nlp_processor is not None:
        return _nlp_processor
    
    # Import here to prevent loading at startup
    from natural_language_processor import EnhancedNLPProcessor
    print("--- [AI Core] Initializing Enhanced NLP Processor for the first time... ---")
    _nlp_processor = EnhancedNLPProcessor()
    print("--- [AI Core] NLP Processor ready. ---")
    return _nlp_processor

def process_user_intent(user_id: int, user_text: str, glucose_history: list) -> dict:
    print(f"--- [AI Core] Processing intent for user {user_id}: '{user_text}' ---")
    
    # Get the NLP processor, loading it if necessary
    NLP_PROCESSOR = _get_nlp_processor()
    
    # ... (The rest of your function logic is the same)
    parsed_entities = NLP_PROCESSOR.parse_user_text(user_text)
    carbs = parsed_entities.get("carbs", 0)
    activity_info = parsed_entities.get("activities_detected", [])
    activity_detected = len(activity_info) > 0
    
    current_glucose = glucose_history[-1] if glucose_history else 120
    dose_recommendation = get_insulin_recommendation(
        glucose=current_glucose,
        carbs=carbs,
        exercise_recent=activity_detected
    )
    
    future_events = {
        "carbs": carbs,
        "activity_type": activity_info[0]['activity'] if activity_info else None,
        "activity_duration": activity_info[0]['duration_minutes'] if activity_info else 0
    }
    
    hybrid_prediction = generate_hybrid_prediction(
        user_id=user_id,
        recent_glucose_history=glucose_history,
        future_events=future_events
    )
    
    contextual_advice = NLP_PROCESSOR.get_insulin_adjustment_suggestion(parsed_entities)
    
    response = {
        "parsed_info": parsed_entities,
        "dose_recommendation": dose_recommendation,
        "glucose_prediction": hybrid_prediction,
        "contextual_advice": contextual_advice
    }
    
    print(f"--- [AI Core] Intent processed successfully. ---")
    return response