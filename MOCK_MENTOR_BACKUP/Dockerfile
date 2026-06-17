# Dockerfile  –  MockMentor production image
# Used by GCP Cloud Run (and optionally Railway / Render).
#
# Build:   docker build -t mockmentor .
# Run:     docker run -p 8080:8080 --env-file .env mockmentor

# ── Stage 1: build dependencies ───────────────────────────────
FROM python:3.11-slim AS builder

# mysqlclient requires the MySQL dev headers at compile time.
RUN apt-get update && apt-get install -y --no-install-recommends \
        default-libmysqlclient-dev \
        build-essential \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

RUN pip install --upgrade pip \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime image ─────────────────────────────────────
FROM python:3.11-slim AS runtime

# Runtime MySQL client library (no dev headers needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
        default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN useradd --create-home appuser
WORKDIR /home/appuser/app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code (excludes files in .dockerignore)
COPY --chown=appuser:appuser . .

# Upload folder – /tmp is always writable in containers
ENV UPLOAD_FOLDER=/tmp/mockmentor_uploads
RUN mkdir -p /tmp/mockmentor_uploads

# Cloud Run injects PORT at runtime (default 8080)
ENV PORT=8080
ENV FLASK_ENV=production

USER appuser

# Gunicorn: 2 workers × 2 threads, 120 s timeout
CMD gunicorn wsgi:app \
      --bind "0.0.0.0:${PORT}" \
      --workers 2 \
      --threads 2 \
      --timeout 120 \
      --access-logfile - \
      --error-logfile -
