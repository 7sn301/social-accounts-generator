[![Telegram Bot](https://img.shields.io/badge/Telegram-@Baseer__Lookup__Bot-0088cc?logo=telegram)](https://t.me/Baseer_Lookup_Bot)
<div dir="rtl">
# 🤖 بوت بصير (Baseer Bot) — Telegram

[![🧪 Baseer Test Suite](https://github.com/7sn301/social-accounts-generator/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/7sn301/social-accounts-generator/actions)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-12%2F12%20PII%20PASS-brightgreen.svg)](#)
[![GDPR](https://img.shields.io/badge/GDPR-Compliant-success.svg)](#)
[![RTL](https://img.shields.io/badge/RTL-Arabic-F59E0B.svg)](#)
[![Production](https://img.shields.io/badge/production-v2.1.7--Patch14-success.svg)](https://baseer1.streamlit.app/)

**المعرّف:** `BSR-V217L-BOT-README-AHMAD-20260613`
**القائد:** د. أحمد الفنّي
**الإصدار:** v2.1.7-Light-Fix3.2-Patch14-Bot-PII-Patch

---

## 📋 الميزات

- ✅ شاشة موافقة صريحة عبر `/start` (GDPR Article 6(1)(a))
- ✅ تخزين `user_id` خام (بعد موافقة المالك على كسر القيد #21)
- ✅ حقّ الوصول `/my_data` (GDPR Article 15)
- ✅ حقّ النسيان `/forget_me` (GDPR Article 17)
- ✅ سجلّ تدقيق `consent_log.jsonl`
- ✅ استنتاج الدولة من `language_code` (بدون Geocoding خارجي)
- ✅ تحليلات شهري / ربعي / سنوي
- ✅ لوحة Streamlit RTL + Noto Sans Arabic

---

## 🚀 التثبيت

```bash
git clone https://github.com/7sn301/social-accounts-generator.git
cd social-accounts-generator
pip install -r requirements.txt
cp .env.example .env
# عدّل .env وضع BOT_TOKEN
python bot.py
```

---

## 🧪 تشغيل الاختبارات

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

**النتيجة المتوقّعة:** 12/12 اختبار PII PASSED في 0.04 ثانية.

---

## 🛡️ الخصوصية

راجع [PRIVACY.md](PRIVACY.md) للاطّلاع على سياسة الخصوصية الكاملة.

---

## 📊 لوحة التحليلات

```bash
streamlit run pages/02_📊_Analytics.py
```

تعرض توزيع المستخدمين حسب الدولة (شهري / ربعي / سنوي) مع RTL + Noto Sans Arabic.

---

## 📜 الترخيص

ملكية خاصّة — د. أحمد الفنّي · 2026

</div>

