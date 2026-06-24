# ═══════════════════════════════════════════════════════════
# BSR-V217L-DOCKERFILE-FINAL-BYPASS-AHMAD-20260613
# تجاوز Railpack و mise بالكامل
# ═══════════════════════════════════════════════════════════

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MODE=production

CMD ["python", "bot.py"]
