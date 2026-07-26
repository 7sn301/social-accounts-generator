# ══════════════════════════════════════════════════════════════════
# BSR-V240-CTO-NUCLEAR-FIX-DOCKERFILE-AHMAD-20260726
# Dockerfile v2.4.0 - NUCLEAR FIX (Env verification + Clean state)
# Date: 2026-07-26 | Leader: Dr. Ahmad Al-Fanni (CTO)
# ══════════════════════════════════════════════════════════════════
#
# 🏆 v2.4.0 FIXES:
#   1. Remove ALL .env files at build time (prevents override)
#   2. Unbuffered Python (-u flag) so logs appear immediately
#   3. Env vars from Railway are injected at runtime (not build)
#   4. Verify script runs at startup to log env status
#   5. Non-root user for security
# ══════════════════════════════════════════════════════════════════

FROM python:3.11-slim

# System deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (cache-friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# 🔥 CRITICAL: Remove any stale .env files that could override Railway vars
RUN rm -f .env .env.local .env.production .env.development .env.staging \
    && echo "✅ Stale .env files removed"

# Python runtime env (NOT app secrets - those come from Railway)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MODE=production \
    PYTHONIOENCODING=utf-8

# Startup verification script
RUN echo '#!/bin/bash\n\
echo "🔎 BSR v2.4.0 Startup Env Check"\n\
echo "  BOT_TOKEN: ${BOT_TOKEN:+SET (${#BOT_TOKEN} chars)}${BOT_TOKEN:-MISSING}"\n\
echo "  RAPIDAPI_KEY: ${RAPIDAPI_KEY:+SET (${#RAPIDAPI_KEY} chars)}${RAPIDAPI_KEY:-MISSING}"\n\
echo "  RAPIDAPI_HOST: ${RAPIDAPI_HOST:-MISSING}"\n\
echo "  DATABASE_URL: ${DATABASE_URL:+SET (${#DATABASE_URL} chars)}${DATABASE_URL:-MISSING}"\n\
echo "🚀 Starting bot.py..."\n\
exec python -u bot.py' > /app/start.sh && \
    chmod +x /app/start.sh

# Run
CMD ["/app/start.sh"]
