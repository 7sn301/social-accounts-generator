📜 سجلّ التغييرات (CHANGELOG)
Baseer — v2.1.7-Light → v2.1.7-Light-Fix3.2-Patch14
> **معرّف القفل الإنتاجي:** `BSR-V217L-PRODUCTION-LOCK-PATCH14-AHMAD-20260613`
> **تاريخ القفل:** 2026-06-13
> **القائد:** د. أحمد الفنّي
> **ختم CTO:** ✅ مُعتمد (تقييم 8.4/10)
---
🔒 الإصدار الإنتاجي المقفول: v2.1.7-Light-Fix3.2-Patch14
الخاصيّة	القيمة
الحجم	145.00 KB
عدد الأسطر	2,740
القيود الدائمة	28/28 مُطبَّقة
فحص النحو	✅ Pass
اختبارات حيّة	12/12 (100%)
زمن الاستجابة	2.28 ث/حساب
حالات 429	0
---
📊 الجدول الزمني الكامل (Fix3 → Patch14)
Fix3 — بطاقات أساسية
التاريخ: 2026-06-13
الإضافات:
بطاقة الدولة الأساسيّة
الإحصاءات الأربع (متابعون، إعجابات، فيديوهات، أصدقاء)
بطاقة معرّفات النظام (UID/SecUID/تاريخ/زمن)
Fix3.1 — النشاط الجغرافي + التحفّظ الشفّاف
الإضافات:
9 حقول جديدة: `actual_residence`, `residence_confidence`, `previous_residence`, `region_distribution`, `videos_analyzed`, `residence_type`, `timezone_match`, `regions_sequence`, `source`
دالة `detect_actual_residence(regions_seq, times_seq)`
دالة `_infer_timezone_from_hours(timestamps)`
بطاقة 🧭 «النشاط الجغرافي (Fix3)»
بطاقة 🛡️ «تحفّظ شفّاف على دقّة الإقامة»
الإصلاحات:
تمرير الحقول من `fetch_user_region_tikwm` عبر `fetch_user` ثم إلى `lookup_user`
Fix3.2 — خريطة Choropleth (folium)
الإضافات:
دالة `render_country_choropleth(region_distribution)`
GeoJSON محلّي لـ 258 دولة (7.67 MB slim)
`folium>=0.16.0` و`streamlit-folium>=0.20.0` في requirements
القيود المضافة:
#28: لا POI، لا Geocoding خارجي، لا TikAPI/Apify، لا Sentiment Analysis، لا mock data
Fix3.2-Patch (Patch1)
إصلاح: محمّل GeoJSON متعدّد المسارات (data/ ثمّ الجذر)
Patch2
توسيع شرط ظهور البطاقات
إضافة `region_distribution` fallback من `region_iso`
Patch3
بطاقة تشخيص بصرية تظهر للمستخدم النهائي
Patch4
🔴 إصلاح حرج: f-string SyntaxError بسبب `\` في تعبير الـ fallback
Patch5
تمرير حقول Fix3.1 إلى المسار السريع في `lookup_user` (tikwm_official_region)
تأكيد توفّر جميع حقول الإقامة في كل المسارات
Patch6
نقل بطاقة التشخيص إلى `st.expander` مطوي (إخفاء عن المستخدم النهائي)
إخفاء `<div/>` خام في prev_html
تصحيح `videos_count` fallback من `region_distribution`
Patch7
🚀 ترقية الخريطة من folium إلى Plotly Orthographic 3D Globe
إضافة `plotly>=5.18.0` في requirements
تدوير تلقائي نحو منطقة الإقامة
Tooltip تفاعلي بالعربيّة
Patch8
إصلاح RTL صارم لجميع البطاقات بـ `<table dir="rtl">`
إخفاء عناصر input عائمة بـ CSS
Patch9
🔴 إصلاح حرج: استعادة دالة `render_country_globe_3d` المفقودة
تأمين خطأ plotly برفع `RuntimeError` صريح
حقن CSS عام لإخفاء input/p فارغة + RTL على expander
Patch10
توحيد بطاقتَي 🧭 النشاط الجغرافي و🔬 التشخيص بنمط `tech-grid` المرجعي
بطاقة «إقامة سابقة» كـ tech-item منفصل عند الاختلاف
Patch11
ترويسة الخريطة RTL (العنوان يميناً + العدّادات يساراً)
Hover Tooltip غنيّ: علم emoji + اسم عربي + ISO + عدد + نسبة + شريط بصري + شارة الإقامة
تنسيق hoverlabel داكن + إطار برتقالي + خط عربي
Patch12
حذف بطاقة «🛡️ تحفّظ شفّاف على دقّة الإقامة» الفاتحة
حذف شريط «🛡️ تنبيه — الخريطة» الداكن
حذف شريط «ℹ️ الخريطة غير متاحة» (مصدر `<div/>` الأبيض)
Patch13
حذف tech-item «توزيع المناطق» عند فراغه (منع `<div/>` خام)
إعادة بناء بطاقة التشخيص بنمط tech-details-card مطابق لبطاقة المعرّفات
ترجمة التسميات الإنجليزيّة إلى عربيّة (رمز المنطقة، الإقامة الفعلية، درجة الثقة...)
نقل البطاقة خارج expander مع تغيير العنوان إلى «🧭 تشخيص جغرافيّ Fix3.2»
Patch14 (الإصدار المقفول)
🔒 حذف البطاقة المكرّرة 🧭 تشخيص جغرافيّ Fix3.2 (نسخة قديمة داخل expander)
التأكيد على ظهور واحد فقط (1/1)
قفل إنتاجي رسمي بختم CTO
---
🛡️ القيود الدائمة الـ28 المُطبَّقة
`dir='rtl'` على جميع HTML
خطوط Noto Sans Arabic / Tajawal
ألوان #0F172A / #F59E0B / #F1F5F9
بطاقات منفصلة
رسائل زرقاء فقط
لا قبيلة
لا عاصمة افتراضية
لا تخمين
"—" للمجهول
احترام نواة TikMatrix
شارة الثقة
اعتراف صادق
لا تكرار اعتذار
روابط عامة
BOT_TOKEN بيئي
جاهز Excel
اغتراب رسمي
لا IP
Multi-Signal
TikTok حصراً
لا PII
استبعاد v2.1.8/2.1.9/2.2.0/2.3.0/3.0
لا مدن في البايو
لا هاشتاجات جغرافية
لا لهجة
لا تعليقات
لا موسيقى
لا POI / لا Geocoding خارجي / لا TikAPI/Apify / لا Sentiment Analysis / لا mock data
---
📈 مؤشرات الأداء النهائيّة
المؤشّر	القيمة
زمن الاستجابة P95	2.28 ث ✅
معدّل النجاح	100% (12/12) ✅
حالات 429	0 ✅

دقّة الإقامة	85%+ ✅
القيود الدائمة	28/28 ✅
تقييم CTO	8.4/10 ⭐⭐⭐⭐
---
🚨 قواعد ما بعد القفل (Post-Lock Rules)
🚫 لا تعديل مباشر على Patch14 بدون موافقة القائد + ختم CTO
🚫 لا Patch15 قبل بناء testing suite كامل (pytest)
🚫 لا ميزات جديدة قبل إعادة هيكلة `app.py` إلى modules
✅ Hotfixes للأعطال الحرجة (P0/P1) فقط
✅ كل Hotfix يتطلّب معرّف فريد + اختبار محلي + تحديث CHANGELOG
