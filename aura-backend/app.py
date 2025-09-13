import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import database as db
import simulator
from intelligent_core import process_user_intent
import threading
import model_trainer
from flask import send_file
import report_generator
import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend for matplotlib
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from config import JWT_SECRET_KEY, CORS_ORIGINS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# JWT configuration
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=12)
jwt = JWTManager(app)

# Rate limiting (per IP). Default global limit; override per-route below.
# Optionally use persistent storage (e.g., Redis) via RATELIMIT_STORAGE_URI.
_rate_limit_storage = os.getenv("RATELIMIT_STORAGE_URI")
if _rate_limit_storage:
    limiter = Limiter(get_remote_address, app=app, default_limits=["200 per hour"], storage_uri=_rate_limit_storage)
else:
    limiter = Limiter(get_remote_address, app=app, default_limits=["200 per hour"])

# --- CORS CONFIGURATION (env-driven & production-safe) ---
# Configure allowed origins via env var CORS_ORIGINS (comma-separated),
# falling back to common localhost origins for development.
DEV_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:5501",
    "http://localhost:5501",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]

raw_origins = (CORS_ORIGINS or "").strip()
if raw_origins:
    allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
else:
    allowed_origins = DEV_ALLOWED_ORIGINS

CORS(app, resources={r"/*": {"origins": allowed_origins}})
# ---------------------------------------------------------

@app.route('/')
def home():
    return "Project Aura Backend is running!"

@app.route("/register", methods=['POST'])
@limiter.limit("5 per minute")
def register():
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400
    username, password, name = data.get('username'), data.get('password'), data.get('name')
    age, gender, phone, weight, height = data.get('age'), data.get('gender'), data.get('phone_number'), data.get('weight_kg'), data.get('height_cm')

    if not all([username, password, name]):
        return jsonify({"error": "Username, password, and name are required"}), 400
    if len(str(password)) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if db.find_user_by_username(username):
        return jsonify({"error": "Username already taken"}), 409

    hashed_password = generate_password_hash(password)
    conn = db.get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, password_hash, name, age, gender, phone_number, weight_kg, height_cm) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (username, hashed_password, name, age, gender, phone, weight, height)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "User registered successfully!"}), 201

@app.route("/login", methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400
    username, password = data.get('username'), data.get('password')
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    user = db.find_user_by_username(username)
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({"error": "Invalid username or password"}), 401
    # Issue JWT with identity = user_id
    access_token = create_access_token(identity=str(user['id']))
    return jsonify({"message": "Login successful", "token": access_token, "user_id": user['id']})

# In app.py

# ... (keep all other code the same) ...
# ==================================================================
# === THE PRIMARY AI ENDPOINT (FINAL DEBUG VERSION) ================
# ==================================================================
@app.route("/api/chat", methods=['POST'])
@limiter.limit("30 per minute")
@jwt_required()
def handle_chat_intent():
    print("\n" + "="*50)
    print("--- Received request at /api/chat ---")
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400
    
    user_message = data.get('message')
    user_id = data.get('user_id')

    if not user_message or not user_id:
        print("--- [ERROR] Request is missing 'message' or 'user_id'. ---")
        return jsonify({"error": "A 'message' and 'user_id' are required"}), 400
        
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        return jsonify({"error": "'user_id' must be an integer"}), 400

    # Enforce that token identity matches user_id
    jwt_user_id = int(get_jwt_identity())
    if jwt_user_id != user_id_int:
        return jsonify({"error": "Unauthorized user context"}), 403

    print(f"--- [INPUT] User ID: {user_id_int}, Message: '{user_message}'")
    
    # --- Step 1: Get Glucose History ---
    glucose_history = db.get_recent_glucose_readings(user_id_int, limit=12)
    if not glucose_history or len(glucose_history) < 12:
        print(f"--- [DATA] Found only {len(glucose_history)} readings. Using fallback mock data for AI. ---")
        glucose_history = [120, 122, 125, 126, 128, 129, 130, 131, 130, 128, 126, 124]
    else:
        print(f"--- [DATA] Found {len(glucose_history)} recent glucose readings. ---")

    # --- Step 2: Call the AI Core ---
    print("--- [AI] Calling 'process_user_intent'... ---")
    ai_response = process_user_intent(
        user_id=user_id_int,
        user_text=user_message,
        glucose_history=glucose_history
    )
    
    # --- !! CRITICAL DEBUGGING STEP !! ---
    # We will now print the entire raw response from the AI to see exactly what it contains.
    import json
    print("--- [AI] Raw response from AI Core:")
    print(json.dumps(ai_response, indent=2))
    # ----------------------------------------

    # --- Step 3: Save Detected Meals to Database ---
    print("--- [DATABASE] Checking AI response for meals to save... ---")
    try:
        # More robust check: ensure keys exist before accessing them
        if "parsed_info" in ai_response and "foods_detected" in ai_response["parsed_info"]:
            foods_to_log = ai_response["parsed_info"]["foods_detected"]
            
            if foods_to_log: # Check if the list is not empty
                print(f"--- [DATABASE] Found {len(foods_to_log)} food item(s). Proceeding to save. ---")
                for food_item in foods_to_log:
                    description = f"{food_item.get('quantity', 1)}x {food_item.get('food', 'Unknown Food')}"
                    carb_value = food_item.get('carbs', 0)
                    
                    print(f"--- [DATABASE] Saving: User='{user_id_int}', Desc='{description}', Carbs='{carb_value}'")
                    db.add_log_entry(
                        user_id=user_id_int,
                        log_type='meal',
                        description=description,
                        value=carb_value
                    )
                print("--- [DATABASE] All detected meals have been saved. ---")
            else:
                print("--- [DATABASE] 'foods_detected' list was empty. Nothing to save. ---")
        else:
            print("--- [DATABASE] 'parsed_info' or 'foods_detected' key not found in AI response. Nothing to save. ---")
            
    except Exception as e:
        print(f"--- [DATABASE] CRITICAL ERROR during save process. The AI response was processed, but saving failed. ---")
        print(f"--- [DATABASE] Error details: {e} ---")
    
    print("--- AI Core processed intent successfully. Returning response to frontend. ---")
    print("="*50 + "\n")
    return jsonify(ai_response)
# ==================================================================
# === NEW: AI CALIBRATION ENDPOINT =================================
# ==================================================================
@app.route('/api/ai/calibrate', methods=['POST'])
@limiter.limit("5 per minute")
@jwt_required()
def calibrate_ai_for_user():
    """
    Triggers the AI fine-tuning process for a specific user in the background.
    """
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({"error": "A 'user_id' is required"}), 400
        
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        return jsonify({"error": "'user_id' must be an integer"}), 400

    # Enforce that token identity matches user_id
    jwt_user_id = int(get_jwt_identity())
    if jwt_user_id != user_id_int:
        return jsonify({"error": "Unauthorized user context"}), 403

    print(f"--- [API] Received calibration request for user_id: {user_id_int} ---")
    
    # Run the slow training process in a separate thread
    # This allows us to send an immediate "started" response back to the frontend
    # without making the user wait for the training to finish.
    training_thread = threading.Thread(
        target=model_trainer.fine_tune_model_for_user,
    args=(user_id_int,) # Ensure user_id is an integer
    )
    training_thread.start() # Start the background task
    
    # Immediately return a 202 Accepted response to the frontend
    return jsonify({
        "status": "Calibration Initiated",
    "message": f"AI model personalization has started for user {user_id_int}. " \
                   "This process runs in the background and may take several minutes. " \
                   "Predictions will automatically use the new model once complete."
    }), 202
@app.route("/api/dashboard", methods=['GET'])
@jwt_required()
def get_dashboard():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "A 'user_id' query parameter is required"}), 400

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        return jsonify({"error": "'user_id' must be an integer"}), 400

    # Enforce token identity
    jwt_user_id = int(get_jwt_identity())
    if jwt_user_id != user_id_int:
        return jsonify({"error": "Unauthorized user context"}), 403

    dashboard_data = db.get_dashboard_data_for_user(user_id_int)
    return jsonify(dashboard_data)
# ==================================================================
# === NEW: PDF REPORT DOWNLOAD ENDPOINT ============================
# ==================================================================
@app.route('/api/user/report', methods=['POST'])
@jwt_required()
def download_user_report():
    """
    Generates a PDF report for a user and sends it as a file download.
    """
    body = request.get_json()
    if not isinstance(body, dict):
        return jsonify({"error": "Invalid JSON body"}), 400
    user_id = body.get('user_id')
    if not user_id:
        return jsonify({"error": "A 'user_id' in the request body is required"}), 400
        
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        return jsonify({"error": "'user_id' must be an integer"}), 400

    # Enforce token identity
    jwt_user_id = int(get_jwt_identity())
    if jwt_user_id != user_id_int:
        return jsonify({"error": "Unauthorized user context"}), 403

    print(f"--- [API] Received report generation request for user_id: {user_id_int} ---")

    try:
        # Call the report generator, which returns the path and a clean filename
        pdf_path, pdf_filename = report_generator.create_user_report(user_id_int)

        # Send the generated file back to the browser for download
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=pdf_filename  # This is the name the user will see
        )

    except Exception as e:
        print(f"--- [API] ERROR: Failed to generate report. Error: {e} ---")
        return jsonify({"error": f"An error occurred while generating the report: {e}"}), 500
@app.route('/api/dev/simulate-data', methods=['POST'])
@limiter.limit("2 per minute")
@jwt_required()
def simulate_data_endpoint():
    body = request.get_json()
    if not isinstance(body, dict):
        return jsonify({"error": "Invalid JSON body"}), 400
    user_id = body.get('user_id')
    if not user_id:
        return jsonify({"error": "A 'user_id' is required"}), 400
    try:
        user_id_int = int(user_id)
        jwt_user_id = int(get_jwt_identity())
        if jwt_user_id != user_id_int:
            return jsonify({"error": "Unauthorized user context"}), 403
        simulator.generate_and_insert_data(user_id=user_id_int, days_of_data=3)
        return jsonify({'message': f'Successfully generated 3 days of data for user {user_id_int}.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================================================================
# === HEALTH CHECK ENDPOINT ========================================
# ==================================================================
@app.route('/api/health', methods=['GET'])
def health_check():
    """Basic health check for DB connectivity and CORS origins."""
    status = {"db": "ok", "cors_allowed_origins": allowed_origins}
    try:
        conn = db.get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
    except Exception as e:
        status["db"] = f"error: {e.__class__.__name__}: {e}"
        return jsonify(status), 500
    return jsonify(status), 200

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5001))
    debug_env = str(os.getenv("DEBUG", "false")).lower() in ("1", "true", "yes", "on")
    app.run(host="0.0.0.0", debug=debug_env, use_reloader=debug_env, port=port)