# BSR-V217L-DOCKERFILE-CLEAN-FINAL-AHMAD-20260613
# تجاوز كامل لمشكلة mkdir + دعم TikTok lookup

FROM python:3.11-slim

WORKDIR /app

# تثبيت dependencies نظام
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# نسخ وتثبيت Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# نسخ كل المشروع (بدون mkdir لأن /app/data موجود في الريبو)
COPY . .

# متغيّرات بيئة
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MODE=production

# تشغيل البوت
CMD ["python", "bot.py"]
