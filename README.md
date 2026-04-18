<div align="center">

# Aura – Insulin Partner (Backend)

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-API-black?logo=flask)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?logo=postgresql)](https://neon.tech/)
[![JWT](https://img.shields.io/badge/Auth-JWT-purple)](https://flask-jwt-extended.readthedocs.io/)
[![Rate Limit](https://img.shields.io/badge/Security-Rate%20Limiting-orange)](https://flask-limiter.readthedocs.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://www.docker.com/)

AI‑assisted diabetes companion backend: secure user auth, NLP‑powered chat intents, glucose predictions, PDF reports, dashboard analytics, and realistic data simulation.

</div>

---

## Live demo

- Deployed (Render): https://aura-insuline-partner.onrender.com/index.html
- Note: Render free services may sleep or throttle under load; initial request can be slow to “cold start.” See Deployment for alternatives.

---

## Highlights

- Secure by default: JWT auth, per‑route rate limiting, and CORS allow‑list
- Environment‑only secrets (no hardcoded fallbacks)
- Postgres (Neon) database with ready schema and helpers
- AI core to parse intents and log meals automatically
- Background model calibration per user
- PDF report generation endpoint
- Health endpoint with DB status and CORS info
- First‑class Docker + docker‑compose support

> Note on free deployment: Render’s free tier proved insufficient for this stack. Recommended free/low‑friction options: Railway (quick) or Google Cloud Run (scalable). See Deployment below.

---

## Repository layout

```
Aura-Insuline-Partner/
├─ frontend/
│  ├─ combined.html               # Combined UI for auth + dashboard + chat
├─ aura-backend/
│  ├─ app.py                 # Flask app with routes, JWT, limiter, CORS
│  ├─ config.py              # Env‑driven config (DATABASE_URL, JWT_SECRET_KEY, ...)
│  ├─ database.py            # Schema + queries + dashboard aggregates
│  ├─ intelligent_core.py    # AI intent processing
│  ├─ model_trainer.py       # Per‑user fine‑tune entry (async thread)
│  ├─ natural_language_processor.py
│  ├─ prediction_service.py
│  ├─ recommendation_service.py
│  ├─ report_generator.py    # PDF report creation
│  ├─ simulator.py           # Fast bulk data generator
│  ├─ wsgi.py                # Gunicorn entrypoint (wsgi:app)
│  ├─ requirements.txt
│  ├─ Dockerfile             # Production container (Gunicorn)
│  ├─ .dockerignore
│  ├─ .env.example
│  └─ temp_reports/
├─ docker-compose.yml        # One‑command local run
├─ DEPLOYMENT.md             # Cloud Run + Render notes
└─ README.md
```

---

## Security & configuration

- JWT authentication with 12‑hour tokens
- Rate limiting
  - Global: 200/hour
  - Per‑route: stricter limits for login, chat, simulate, calibrate
  - Optional persistent store via `RATELIMIT_STORAGE_URI` (e.g., Redis)
- CORS allow‑list via `CORS_ORIGINS` (comma‑separated origins)
- Secrets only from environment variables (no fallbacks)
- Health endpoint returns DB status; keep DEBUG off in prod

Environment variables (see `aura-backend/.env.example`):

- DATABASE_URL (required) – e.g. `postgresql://user:pass@host:5432/db?sslmode=require`
- JWT_SECRET_KEY (required) – long random secret
- CORS_ORIGINS – comma‑separated list, e.g. `http://127.0.0.1:5500`
- PORT – default 5001 locally; container listens on 8080
- RATELIMIT_STORAGE_URI – optional (Redis), recommended for production
- DEBUG – `false` in production

---

## Quick start (Docker)

1) Copy example env and fill in values

```bash
cp aura-backend/.env.example aura-backend/.env
# edit aura-backend/.env with your DATABASE_URL and JWT_SECRET_KEY
```

2) Start with Docker Compose (recommended)

```bash
docker compose up --build
```

Service will be available at: http://127.0.0.1:5001

3) Health check

```bash
curl http://127.0.0.1:5001/api/health
```

Alternative: plain Docker

```bash
docker build -t aura-backend:local ./aura-backend
docker run --env-file aura-backend/.env -p 5001:8080 aura-backend:local
```

---

## Quick start (local Python)

```bash
cd aura-backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

export DATABASE_URL=postgresql://.../db?sslmode=require
export JWT_SECRET_KEY=your-long-random-secret
export CORS_ORIGINS=http://127.0.0.1:5500
python app.py
```

Server binds to 0.0.0.0 on port 5001 by default. Visit `/api/health` to verify.

---

## API overview

Auth
- POST `/register` – create account: `{ username, password, name, ... }`
- POST `/login` – returns `{ token, user_id }`

Protected (require `Authorization: Bearer <token>` and correct `user_id`)
- POST `/api/chat` – `{ message, user_id }` → AI intent + optional meal logging
- GET  `/api/dashboard?user_id=...` – merged metrics for user
- POST `/api/ai/calibrate` – `{ user_id }` → starts background fine‑tune; returns 202
- POST `/api/dev/simulate-data` – `{ user_id }` → seeds 3 days of demo data
- POST `/api/user/report` – `{ user_id }` → returns a PDF file download

Public
- GET `/api/health` – `{ db: "ok"|error, cors_allowed_origins: [...] }`

Example: Login then Chat

```bash
# login
TOKEN=$(curl -s -X POST http://127.0.0.1:5001/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"demo","password":"secret"}' | jq -r .token)

# chat
curl -X POST http://127.0.0.1:5001/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"message":"I ate pasta and an apple","user_id":1}'
```

---

## How the backend works (end‑to‑end)

This section explains the full flow from a user message to AI output, database writes, and reports. It’s based on these modules: `intelligent_core.py`, `natural_language_processor.py`, `prediction_service.py`, `recommendation_service.py`, `database.py`, and `report_generator.py`.

### 1) NLP parsing (natural_language_processor.py)

- Enhanced dictionary‑driven NLP extracts:
  - Foods and quantities (e.g., “2 slices of pizza”, “an apple”)
  - Estimated carbs using a food carb database with serving sizes
  - Activities with duration and intensity (e.g., “45 minute walk” → moderate)
  - Explicit carbs override (e.g., “80g carbs”)
  - Meal timing hints (breakfast/lunch/dinner)
- Robustness techniques:
  - Variation maps (e.g., “spaghetti” → pasta) and whole‑word regex matching
  - Quantity detection in a narrow text window to avoid false matches
  - Confidence score computed from entities found

Output shape example:

```json
{
  "carbs": 65,
  "foods_detected": [
    {"food": "pasta", "quantity": 1, "carbs": 45, "serving_size": "1 cup"},
    {"food": "apple", "quantity": 1, "carbs": 25}
  ],
  "activities_detected": [
    {"activity": "walk", "intensity": "light", "duration_minutes": 45}
  ],
  "meal_type": "dinner",
  "warnings": ["Used explicit carb amount, ignoring food estimates"],
  "confidence": 0.86,
  "original_text": "Had pasta and an apple, going for a 45 min walk"
}
```

### 2) AI orchestrator (intelligent_core.py)

`process_user_intent(user_id, user_text, glucose_history)` coordinates the pipeline:
- Lazy‑loads the NLP processor on first use (faster app startup)
- Parses text → gets carbs, activities, timing
- Reads current glucose from provided history (or falls back safely)
- Calls dosing recommendation engine with context flags
- Builds future event hints (carbs, activity) and calls the hybrid predictor
- Produces contextual advice (e.g., exercise reductions, timing notes)
- Returns a comprehensive response (see below)

Output shape example:

```json
{
  "parsed_info": { /* output from NLP above */ },
  "dose_recommendation": {"recommended_dose": 4.2, "confidence": 0.9, "reasoning": "..."},
  "glucose_prediction": {
    "status": "success",
    "last_known_glucose": 128,
    "original_prediction": [130,133,...],
    "adjusted_prediction": [129,131,...],
    "prediction_bounds": {"upper": [...], "lower": [...]},
    "analysis": {"trend": "rising", "slope": 0.6}
  },
  "contextual_advice": {"carb_bolus_needed": true, "exercise_reduction": true, ...}
}
```

### 3) Glucose prediction (prediction_service.py)

- Lazy‑loads Keras/TensorFlow only when needed; caches models and scalers
- Personalized model per user if available: `glucose_predictor_user_<id>.h5` + scaler
- Default model fallback: `glucose_predictor.h5` + `scaler.gz`
- Rolling 12‑step prediction horizon (approx. 2 hours), with inverse scaling
- Physiological constraints clamp impossible jumps and keep values within [40, 400]
- Hybrid adjustment layer adds carb and activity effects, then re‑constrains
- Trend analysis (slope and qualitative trend) included when requested

Key error modes handled:
- Missing default model → explicit error in response
- Insufficient history (<12 points) → informative error message

### 4) Insulin dosing recommendation (recommendation_service.py)

- RL agent (Stable‑Baselines3 DQN) is lazy‑loaded; model file `aura_dqn_agent(.zip)`
- If the RL model is absent, returns a clear error so the caller can fallback in UI
- Hybrid approach combines: RL base suggestion + standard carb and correction math
- Contextual modifiers:
  - Exercise reduction (e.g., −30%) for recent activity
  - Stress increase if stress_level is high
- Safety clamping caps dose between 0 and 20 units

### 5) Database I/O (database.py)

- Postgres schema: users, glucose_readings, insulin_doses, meal_logs
- Dashboard aggregation returns profile, last 24h glucose, recent meals, and a computed daily health score
- Health score: primarily based on time‑in‑range with penalties for lows/highs
- Helper to add logs (meals/insulin), with NOW() timestamps

### 6) Report generation (report_generator.py)

- Fetches dashboard data and generates a professional PDF
- Creates a Matplotlib glucose chart image for the last 24 hours
- Adds a summary section: health score, time in range, hypoglycemia events
- Lists recent meals in a simple table
- Saves PDF to `aura-backend/temp_reports/`, returns file path and filename

### 7) Request lifecycle (app.py)

- `/api/chat` (POST, protected):
  - Requires JWT and matching `user_id`
  - Pulls last 12 glucose readings (fallback sample if too few)
  - Invokes `process_user_intent`
  - Saves detected meals to DB (if any)
  - Returns AI output to the client

- `/api/user/report` (POST, protected):
  - Generates a PDF via `report_generator.create_user_report` and sends the file

- `/api/ai/calibrate` (POST, protected):
  - Starts per‑user fine‑tune in a background thread and returns 202 immediately

- `/api/dev/simulate-data` (POST, protected, limited):
  - Seeds 3 days of realistic readings using fast bulk inserts

- `/api/dashboard` (GET, protected):
  - Returns merged dashboard dataset for the user

---

## Deployment

Status: A live instance currently runs on Render. Note that the free tier can sleep and may not handle heavy workloads reliably.

Recommended options:

1) Railway (simple and free‑friendly)
   - New Project → Deploy from Repo → select this repo
   - In service settings, set Monorepo Root to `aura-backend`
   - Set env vars: `DATABASE_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS` (and `RATELIMIT_STORAGE_URI` if used)
   - Deploy and use the provided URL as your API base

2) Google Cloud Run (scalable)
   - Uses `aura-backend/Dockerfile`
   - See `DEPLOYMENT.md` for step‑by‑step `gcloud` build and deploy, and required env vars

Tip: After deployment, update your frontend to point to the deployed API base URL and make sure `CORS_ORIGINS` includes that origin.

---

## New features (recent)

- Dockerized backend with Compose for local development
- JWT auth wired into frontend pages; token stored and attached to requests
- Health endpoint exposes DB status and allowed CORS
- Faster data simulator using bulk inserts
- PDF report generator with glucose chart and meal table
- Detailed README with architecture, data flow, and troubleshooting

---

## Troubleshooting

- DB connection error: verify `DATABASE_URL` (Neon) and that sslmode=require is present
- 401 Unauthorized: missing/expired JWT or `user_id` mismatch with token
- 403 Unauthorized user context: token user_id doesn’t match the provided `user_id`
- 429 Too Many Requests: you hit the rate limit; try later
- CORS blocked: update `CORS_ORIGINS` to include your frontend origin exactly
- PDF generation: ensure `aura-backend/temp_reports/` is writable (kept in repo via `.gitkeep`)

---

## License

This project is licensed under the MIT License – see the `LICENSE` file for details.

---

## Acknowledgements

- Flask, Flask‑JWT‑Extended, Flask‑Limiter, Flask‑CORS
- TensorFlow/Keras, scikit‑learn, SciPy
- psycopg2, Neon Postgres
- Gunicorn

— Made with care to lower the cognitive load of diabetes management.
- **Chart is King**: The glucose visualization is your winning feature
- **AI Must Work**: Models should produce reasonable outputs
- **Web-First**: Optimize for browser performance, not mobile apps

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Team

**Built with by Harsh**

- **Backend Architect** - API & Infrastructure
- **AI Specialist** - ML Models & Predictions  
- **UI/UX Designer** - Beautiful Interfaces
- **Integration Master** - Making it all work together

---

## Future Vision

Project Aura's web-first approach enables rapid scaling and feature development:

#### **Phase 2: Advanced Intelligence**
- **Personalization Engine**: Learn individual insulin sensitivity patterns
- **Progressive Web App**: Offline functionality, push notifications
- **CGM Integration**: Real-time glucose streaming from Dexcom, FreeStyle
- **Advanced Analytics**: HbA1c predictions, time-in-range optimization

#### **Phase 3: Healthcare Ecosystem**
- **Provider Dashboard**: Share insights with endocrinologists
- **Community Features**: Anonymous benchmarking, peer support
- **Research Platform**: Opt-in data contribution for diabetes research
- **Global Scale**: Multi-language support, regional medical guidelines

#### **Phase 4: AI Evolution**  
- **Multi-Modal Learning**: Combine glucose, activity, sleep, stress data
- **Long-term Forecasting**: Weekly/monthly glucose trend predictions
- **Medication Optimization**: AI-suggested therapy adjustments
- **Precision Medicine**: Genetic factors in diabetes managementare
- **Advanced AI**: Multi-modal learning, federated learning across users

---

<div align="center">

### **Ready to revolutionize diabetes management?**

**Star this repo if you believe in AI-powered healthcare!**

</div>
