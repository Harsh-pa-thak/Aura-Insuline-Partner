# Deploying Aura Backend to Render

## Required environment variables
- DATABASE_URL: Your Postgres connection string (include `sslmode=require` if needed)
- JWT_SECRET_KEY: A strong random secret for signing JWTs

## Optional environment variables
- CORS_ORIGINS: Comma-separated list of allowed origins (e.g., your frontend URL)
- PORT: Port to bind (Render sets this automatically)
- RATELIMIT_STORAGE_URI: Persistent storage for rate limiting (recommended). Example: `redis://:password@redis-host:6379/0`

## Steps
1. Create a new Web Service on Render.
2. Build Command: `pip install -r aura-backend/requirements.txt`
3. Start Command: `gunicorn -w 2 -k gthread -b 0.0.0.0:$PORT aura-backend.wsgi:app`
4. Set Environment Variables:
   - DATABASE_URL
   - JWT_SECRET_KEY
   - CORS_ORIGINS (your frontend url)
   - RATELIMIT_STORAGE_URI (e.g., Redis) to avoid in-memory limiter in production
5. Deploy. Use `/api/health` to verify DB connectivity and CORS origins.

## One-click with render.yaml
You can commit the included `render.yaml` and click “New +” → “Blueprint” in Render to auto-provision the service with correct build/start commands. Fill in env vars during setup.

# Deploying to Google Cloud Run (alternative)

## Prereqs
- Google Cloud project with billing enabled
- gcloud CLI installed and authenticated (`gcloud auth login` and `gcloud config set project <PROJECT_ID>`)

## Build and deploy
1. From the `aura-backend/` directory, build the image:
   - `gcloud builds submit --tag gcr.io/<PROJECT_ID>/aura-backend`
2. Deploy to Cloud Run:
   - `gcloud run deploy aura-backend \
      --image gcr.io/<PROJECT_ID>/aura-backend \
      --platform managed \
      --region <REGION> \
      --allow-unauthenticated \
      --set-env-vars DATABASE_URL=<your-neon-url>,JWT_SECRET_KEY=<random-secret>,CORS_ORIGINS=<frontend-url>,RATELIMIT_STORAGE_URI=<optional-redis-uri>`
3. Visit the URL output by Cloud Run and check `/api/health`.

Notes:
- Cloud Run automatically sets PORT; Dockerfile already uses `${PORT}`.
- For Redis (rate limits) consider Memorystore (Redis) or a hosted Redis provider and pass its URI via `RATELIMIT_STORAGE_URI`.

## Frontend
- Store the token from `/login` and send it as `Authorization: Bearer <token>` on protected routes.
- Protected routes: `/api/dashboard`, `/api/chat`, `/api/ai/calibrate`, `/api/dev/simulate-data`, `/api/user/report`.
