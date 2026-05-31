# 🛰️ TikTok Region Analyzer v7.0 — GDPR-Compliant Edition

تطبيق احترافي لاستخراج الموقع الجغرافي لحسابات TikTok بطريقة قانونية تماماً.

## ✨ المميزات

- 🎯 **5 طبقات تحليل** ذكية للموقع
- 🛡️ **GDPR Compliant** بالكامل
- 🔒 **PDPL** متوافق
- 🌍 **40+ دولة** مدعومة
- 🗺️ **خريطة تفاعلية** مع كل تحليل
- 📊 **Confidence Score** شفاف
- 🔐 **Privacy Policy** مدمجة

## 🧠 منهجية التحليل

| الطبقة | الوزن | المصدر |
|--------|------|--------|
| Profile Region | 50% | TikTok API |
| Profile Language | 10% | تفضيل اللغة |
| Text Language Detection | 5-20% | BIO + nickname |
| Geographic Keywords | 8-25% | hashtags جغرافية |
| Currency Indicators | 15% | عملات في النص |

## 🚀 التشغيل

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 🛡️ امتثال GDPR

- Article 6(1)(f) — Legitimate Interest كأساس قانوني
- Data Minimization (cache 1 ساعة فقط)
- لا تخزين دائم
- لا logging للـ usernames
- DNT header مفعَّل

## 📚 المراجع

- [GDPR Official](https://gdpr-info.eu/)
- [TikTok Creator Regions](https://scrapecreators.com/blog/tiktok-creator-regions)

---

**v7.0.0** | 2026
