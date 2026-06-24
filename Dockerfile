# ═══════════════════════════════════════════════════════════
# BSR-V217L-DOCKERFILE-MKDIR-FIXED-AHMAD-20260613
# نسخة محدَّثة تتجنّب خطأ mkdir
# ═══════════════════════════════════════════════════════════

FROM python:3.11-slim

WORKDIR /app

# تثبيت اعتماديات النظام
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# نسخ وتثبيت requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir python-telegram-bot>=21.0 python-dotenv>=1.0.0

# نسخ كامل المشروع
COPY . .

# إنشاء مجلّد data بأمان (لا يفشل إن وُجد)
RUN mkdir -p /app/data || true

# متغيّرات البيئة
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MODE=production

# تشغيل البوت
CMD ["python", "bot.py"]
