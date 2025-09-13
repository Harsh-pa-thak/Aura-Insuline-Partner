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

## Frontend
- Store the token from `/login` and send it as `Authorization: Bearer <token>` on protected routes.
- Protected routes: `/api/dashboard`, `/api/chat`, `/api/ai/calibrate`, `/api/dev/simulate-data`, `/api/user/report`.
