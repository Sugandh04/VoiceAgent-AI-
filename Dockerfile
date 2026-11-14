# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  VoiceAgent AI — Dockerfile (multi-stage)
#
#  Stages:
#    base    — shared Python deps
#    api     — FastAPI + Uvicorn server
#    worker  — LiveKit voice agent worker
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── Stage 1: Base ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

# System dependencies (audio libs for LiveKit Silero VAD)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (cached layer unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# ── Stage 2: API server ───────────────────────────────────────────────────────
FROM base AS api

EXPOSE 8000

# Non-root user for security
RUN useradd -m -u 1001 voiceagent && chown -R voiceagent:voiceagent /app
USER voiceagent

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

# ── Stage 3: Voice agent worker ───────────────────────────────────────────────
FROM base AS worker

RUN useradd -m -u 1001 voiceagent && chown -R voiceagent:voiceagent /app
USER voiceagent

CMD ["python", "-m", "app.livekit_agent.agent"]

