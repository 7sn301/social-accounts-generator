<div dir="rtl">

# 🛠️ دليل إعداد بوت بصير

**المعرّف:** `BSR-V217L-BOT-SETUP-AHMAD-20260613`
**القائد:** د. أحمد الفنّي
**التاريخ:** 2026-06-13

---

## 1️⃣ إنشاء البوت في Telegram

1. افتح [@BotFather](https://t.me/BotFather) على تيليجرام.
2. أرسل `/newbot`.
3. اختر اسمًا (مثلًا: `Baseer Analytics Bot`).
4. اختر username (مثلًا: `BaseerBot`).
5. انسخ التوكن (يبدأ بأرقام ثم `:` ثم أحرف).

---

## 2️⃣ إعداد المتغيّرات

```bash
cp .env.example .env
nano .env  # عدّل BOT_TOKEN
```

⚠️ **لا ترفع ملفّ `.env` إلى GitHub أبدًا** — هو محمي عبر `.gitignore`.

---

## 3️⃣ تثبيت الاعتماديات

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt   # للتطوير فقط
```

---

## 4️⃣ تشغيل الاختبارات

```bash
pytest tests/ -v
```

النتيجة المتوقّعة:
```
12 passed in 0.04s
```

---

## 5️⃣ تشغيل البوت

```bash
python bot.py
```

---

## 6️⃣ تشغيل لوحة التحليلات

```bash
streamlit run pages/02_📊_Analytics.py
```

---

## 7️⃣ النشر على Heroku / Railway

ملفّ `Procfile` جاهز:
```
worker: python bot.py
```

أضف متغيّر البيئة `BOT_TOKEN` في لوحة المنصّة.

---

## 🛡️ الالتزام بـ GDPR

- ✅ شاشة موافقة صريحة عبر `/start`
- ✅ `/my_data` — حقّ الوصول (Article 15)
- ✅ `/forget_me` — حقّ النسيان (Article 17)
- ✅ سجلّ تدقيق `data/consent_log.jsonl`
- ✅ مدّة احتفاظ: 365 يومًا

</div>
