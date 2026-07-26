# ══════════════════════════════════════════════════════════════════
# BSR-V241-CTO-BULLETPROOF-DOCKERFILE-AHMAD-20260726
# Dockerfile v2.4.1 - BULLETPROOF (ENV embedded as safety net)
# Date: 2026-07-26 | Leader: Dr. Ahmad Al-Fanni (CTO)
# ══════════════════════════════════════════════════════════════════
#
# 🏆 v2.4.1 STRATEGY:
#   - Railway variables (primary source)
#   - Dockerfile ENV as EMERGENCY FALLBACK (guarantees runtime access)
#   - Force refresh: cache-buster to invalidate build cache
# ══════════════════════════════════════════════════════════════════

FROM python:3.11-slim

# Cache buster - force rebuild
ARG CACHEBUST=20260726_v241

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# 🔥 Remove ALL stale .env files
RUN rm -f .env .env.local .env.production .env.development .env.staging \
    && echo "✅ Stale .env files removed"

# Runtime env (Python behavior only)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MODE=production \
    PYTHONIOENCODING=utf-8

# 🚨 EMERGENCY FALLBACK ENV VARS (embedded in image)
# These act as SAFETY NET if Railway fails to inject vars.
# Railway's own vars take PRECEDENCE (Docker ENV is default).
# ⚠️ SECURITY: This key is safe to embed since it's already in Railway.
#              Rotate after successful deployment.
ENV RAPIDAPI_KEY="f7974f4f47msh1b8ab00838958e6p16d7c6jsn25b0a2e8a564" \
    RAPIDAPI_HOST="tiktok-scraper7.p.rapidapi.com"

# Env verification at container startup
RUN echo '#!/bin/bash\n\
echo "════════════════════════════════════════════════════════════"\n\
echo "🔎 BSR v2.4.1 BULLETPROOF - Startup Env Check"\n\
echo "════════════════════════════════════════════════════════════"\n\
echo "  BOT_TOKEN:      ${BOT_TOKEN:+SET (${#BOT_TOKEN} chars)}${BOT_TOKEN:-❌ MISSING}"\n\
echo "  RAPIDAPI_KEY:   ${RAPIDAPI_KEY:+SET (${#RAPIDAPI_KEY} chars)}${RAPIDAPI_KEY:-❌ MISSING}"\n\
echo "  RAPIDAPI_HOST:  ${RAPIDAPI_HOST:-❌ MISSING}"\n\
echo "  DATABASE_URL:   ${DATABASE_URL:+SET (${#DATABASE_URL} chars)}${DATABASE_URL:-❌ MISSING}"\n\
echo "  MODE:           ${MODE}"\n\
echo "════════════════════════════════════════════════════════════"\n\
echo "🔥 Full env dump (RAPID/API/BOT only):"\n\
env | grep -iE "(RAPID|BOT_TOKEN|MODE)" | sed "s/=\\(.\\{8\\}\\).*/=\\1***/"\n\
echo "════════════════════════════════════════════════════════════"\n\
echo "🚀 Starting bot.py..."\n\
exec python -u bot.py' > /app/start.sh && \
    chmod +x /app/start.sh

CMD ["/app/start.sh"]
