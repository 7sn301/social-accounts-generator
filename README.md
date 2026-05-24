# 🌐 مولد معلومات حسابات التواصل الاجتماعي - النسخة المحسّنة

تطبيق Streamlit لسحب معلومات الحسابات العامة من 14+ منصة تواصل اجتماعي.

## ✨ المزايا الجديدة

- ✅ **إدخال يدوي** يدعم أكثر من 300 حساب/رابط دفعة واحدة
- ✅ **دعم RTL كامل** للغة العربية مع خطوط احترافية
- ✅ **14 منصة مدعومة**: X, Instagram, YouTube, Facebook, TikTok, LinkedIn, Threads, Reddit, Pinterest, Telegram, Twitch, GitHub, Snapchat, Twitter
- ✅ **معالجة متوازية** لتسريع السحب
- ✅ **تخزين مؤقت** (caching) للنتائج لمدة ساعة
- ✅ **شريط تقدم** وإحصائيات مباشرة
- ✅ **معالجة أخطاء قوية** (404, timeout, ...)
- ✅ **تصدير متعدد**: CSV / JSON / Excel
- ✅ **فلترة النتائج** حسب الحالة والمنصة
- ✅ **بطاقات بصرية** للحسابات الناجحة
- ✅ **ملف Excel نموذجي** للتحميل المباشر

## 🚀 التشغيل المحلي

```bash
pip install -r requirements.txt
streamlit run app.py
```

## ☁️ النشر على Streamlit Cloud

1. ارفع المشروع إلى GitHub
2. اربط الريبو بـ [share.streamlit.io](https://share.streamlit.io)
3. حدد `app.py` كملف رئيسي

## 📋 صيغ الإدخال اليدوي المدعومة

```
x,nasa
instagram:natgeo
youtube MrBeast
https://www.tiktok.com/@khaby.lame
https://www.linkedin.com/in/billgates
# الأسطر التي تبدأ بـ # تُعتبر تعليقات
```

## ⚠️ ملاحظات

- التطبيق يجمع **البيانات العامة فقط** المتاحة على صفحات الملفات الشخصية.
- بعض المنصات (Instagram, Facebook) تقيّد scraping بشكل صارم.
- استخدم عدد عمليات متوازية معتدل (10) لتجنب الحظر المؤقت.
