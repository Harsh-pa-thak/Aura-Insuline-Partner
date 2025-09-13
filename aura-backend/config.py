import os

# Strictly require environment variables in production.
def _require_env(name: str) -> str:
	value = os.getenv(name)
	if not value:
		raise RuntimeError(f"Missing required environment variable: {name}")
	return value

# Database URL (no fallback)
DATABASE_URL = _require_env("DATABASE_URL")

# JWT secret key (used to sign tokens)
JWT_SECRET_KEY = _require_env("JWT_SECRET_KEY")

# Optional: CORS origins (comma-separated)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "")