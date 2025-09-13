FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System packages needed for psycopg2, opencv, and scientific libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy backend source
COPY . .

# Cloud Run uses PORT env (defaults to 8080 if not set)
ENV PORT=8080
EXPOSE 8080

# Start via Gunicorn using the WSGI entrypoint
CMD gunicorn -w 1 --timeout 120 -k gthread -b 0.0.0.0:${PORT} wsgi:app
