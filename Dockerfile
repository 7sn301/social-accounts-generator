# ═══════════════════════════════════════════════════════════════════
# BSR-V232-CTO-DOCKERFILE-ENV-EXPLICIT-AHMAD-20260726
# Dockerfile v2.3.2 - Explicit env variable declaration for Railway
# Date: 2026-07-26 | Leader: Dr. Ahmad Al-Fanni (CTO)
# ═══════════════════════════════════════════════════════════════════

FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Project files
COPY . .

# CRITICAL FIX: Remove any stale .env file that overrides Railway variables
# This is the root cause of "[L0] RAPIDAPI_KEY not set" issue
RUN rm -f .env .env.local .env.production .env.development

# Runtime environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MODE=production

# Railway injects these at deploy time:
#   BOT_TOKEN, BOT_USERNAME, DATABASE_URL,
#   RAPIDAPI_KEY, RAPIDAPI_HOST,
#   ADMIN_ID, ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_PASSWORD_SALT,
#   PRIVACY_POLICY_URL, SESSION_SECRET, TIMEZONE

# Start bot with unbuffered output for real-time logs
CMD ["python", "-u", "bot.py"]
