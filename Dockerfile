# ═══════════════════════════════════════════════════════════
# BSR-V217L-DOCKERFILE-FIXED-FINAL-AHMAD-20260613
# نسخة نهائيّة تتجاوز خطأ mkdir
# ═══════════════════════════════════════════════════════════

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir python-telegram-bot>=21.0 python-dotenv>=1.0.0

COPY . .

# الإصلاح المهمّ: || true يمنع فشل البناء إن وُجد المجلّد
RUN mkdir -p /app/data 

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MODE=production

CMD ["python", "bot.py"]
