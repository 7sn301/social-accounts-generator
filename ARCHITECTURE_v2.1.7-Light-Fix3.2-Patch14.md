# 🏗️ توثيق بنية المشروع — Baseer v2.1.7-Light-Fix3.2-Patch14

> **معرّف التوثيق:** `BSR-V217L-ARCHITECTURE-DOC-AHMAD-20260613`
> **تاريخ التوثيق:** 2026-06-13
> **القائد:** د. أحمد الفنّي
> **الحالة:** 🔒 إصدار إنتاجي مقفول

---

## 📋 نظرة عامّة على المشروع

**Baseer** هو نظام تحليل حسابات TikTok لاستنتاج «الإقامة الفعليّة» للمستخدم من توقيع الفيديوهات الأخيرة + تحليل المنطقة الزمنيّة، دون استخدام IP أو Geocoding خارجي أو أي بيانات شخصيّة حسّاسة (PII).

### 🎯 الهدف الجوهري
استنتاج موقع الإقامة الحقيقي للحسابات بدقّة 85%+ مع التزام صارم بـ:
- ✅ TikTok حصراً كمصدر بيانات
- ✅ لا IP / لا Geocoding / لا PII
- ✅ Multi-Signal (region_iso + timezone + posting sequence)

---

## 🗂️ هيكل الملفات

```
/home/user/baseer_v217l/
├── app.py                          # الملف الرئيسي (2,740 سطر / 145 KB)
├── requirements.txt                # المتطلّبات (7 حزم)
├── data/
│   └── world_countries.geo.json    # GeoJSON محلّي 258 دولة (7.67 MB slim)
├── .streamlit/
│   └── config.toml                 # إعدادات Streamlit
└── CHANGELOG.md
```

---

## 📦 الحزم المُعتمَدة (requirements.txt)

| الحزمة | الإصدار | الغرض |
|--------|---------|------|
| streamlit | >=1.32.0 | الواجهة الأساسيّة |
| requests | >=2.31.0 | HTTP requests إلى TikWM |
| openpyxl | >=3.1.0 | تصدير Excel |
| pandas | >=2.0.0 | معالجة جداول الحسابات |
| folium | >=0.16.0 | (قديم - يبقى كاحتياطي) |
| streamlit-folium | >=0.20.0 | (قديم - يبقى كاحتياطي) |
| plotly | >=5.18.0 | الكرة الأرضية 3D Globe |

---

## 🧩 البنية الداخلية لـ `app.py`

### القسم 1 — الإعدادات والثوابت (Lines 1-110)
- `USER_AGENTS`: 22 user agent للتدوير
- `TIKWM_BASE = "https://www.tikwm.com"`
- `PROXY_CHAIN`: 4 وسطاء (jina, allorigins, corsproxy, codetabs)
- `PATTERNS`: regex لاستخراج user_id / sec_uid
- `_TIKWM_LAST_CALL`, `_RATELIMIT_BURST`: rate-limit ذكي

### القسم 2 — قواميس الترجمة (Lines 110-400)
- `COUNTRY_AR`: ISO-2 → اسم عربي (260 دولة)
- `FLAG_EMOJI_TO_COUNTRY`: علم → ISO-2
- `TIKMATRIX_FALLBACK_ACCOUNTS`: حسابات احتياطيّة
- `CELEBRITIES`: حسابات معروفة → دولة ثابتة

### القسم 3 — منطق استخراج الموقع (Lines 400-700)
- `fetch_user_region_tikwm(username)`: جلب آخر 5 فيديوهات + region + timestamps
- `_infer_timezone_from_hours(timestamps)`: استنتاج Timezone من ساعات النشر
- `detect_actual_residence(regions_seq, times_seq)`: خوارزميّة Multi-Signal

### القسم 4 — جلب البيانات الأساسيّة (Lines 700-1450)
- `fetch_user(username)`: مسار رئيسي (TikWM + Jina + TikMatrix fallback)
- `lookup_user(username)`: نقطة الدخول مع cache
  - Fast path: tikwm_official_region
  - Standard path: fetch_user + معالجة شاملة
- `process_bulk(usernames)`: معالجة دفعات (Excel)

### القسم 5 — رندرنغ الكرة الأرضية (Lines 1450-1600)
- `render_country_globe_3d(region_distribution, actual_residence)`:
  - Plotly Orthographic projection
  - تدوير تلقائي نحو منطقة الإقامة (8 مناطق جغرافيّة)
  - Hover Tooltip غنيّ (علم emoji + اسم عربي + ISO + عدد + نسبة + شريط)
  - ISO-2 → ISO-3 mapping (75 دولة)
- `render_country_choropleth(...)`: نسخة folium قديمة (احتياطي)

### القسم 6 — رندرنغ الواجهة (Lines 1600-2200)
- `display_single_result(result)`: عرض حساب واحد
  - بطاقة الدولة الأساسيّة
  - بطاقة الإحصاءات (4 خانات)
  - بطاقة 🧭 «النشاط الجغرافي (Fix3)» — tech-grid
  - بطاقة 🔬 «تشخيص جغرافيّ Fix3.2» — tech-grid
  - الكرة الأرضية + ترويسة RTL
  - بطاقة المعرّفات (UID/SecUID) داخل expander

### القسم 7 — المعالجة الجماعيّة (Lines 2200-2740)
- `display_bulk_results(results)`: جدول + تصدير Excel
- منطق الـ tabs (فردي / جماعي / Excel)
- CSS عام + التذييل

---

## 🎨 نظام التصميم (Design System)

### 🎨 لوحة الألوان
| الاسم | القيمة | الاستخدام |
|------|--------|----------|
| Slate-900 | `#0F172A` | الخلفيّة الأساسيّة |
| Slate-800 | `#1E293B` | الخلفيّة المتدرّجة |
| Amber-500 | `#F59E0B` | اللون المميّز / الإطارات |
| Slate-100 | `#F1F5F9` | النصّ الأساسي |
| Green-500 | `#10B981` | الثقة العالية / النجاح |
| Cyan-400 | `#22D3EE` | بطاقة التشخيص |
| Slate-400 | `#94A3B8` | النصّ الثانوي |
| Red-500 | `#EF4444` | الأخطاء الحرجة |

### 🔤 الخطوط
- **الأساسي:** Noto Sans Arabic
- **الاحتياطي:** Tajawal
- **عام:** sans-serif

### 🧱 نمط البطاقات الموحَّد (tech-grid)
```css
.tech-details-card {
    background: linear-gradient(135deg, rgba(15,23,42,0.95), rgba(30,41,59,0.8));
    border: 1px solid rgba(245,158,11,0.3);
    border-radius: 16px;
    padding: 1.6rem 1.8rem;
    direction: rtl;
    text-align: right;
}
.tech-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1rem;
}
.tech-item {
    background: rgba(15,23,42,0.6);
    border-right: 3px solid #F59E0B;
    border-radius: 8px;
    padding: 1rem;
}
.tech-label {
    color: #94A3B8;
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.tech-value {
    color: #F1F5F9;
    font-family: 'Courier New', monospace;
    font-size: 0.95rem;
    word-break: break-all;
}
```

---

## 🔄 تدفّق البيانات (Data Flow)

```
المستخدم يُدخل @username
        ↓
   lookup_user(username)
        ↓
   Cache check (st.cache_data)
        ↓
   Fast path: tikwm_official_region → 9 حقول Fix3.1
        ↓ (إن فشل)
   Standard path: fetch_user → TikWM → Jina → TikMatrix
        ↓
   fetch_user_region_tikwm → آخر 5 فيديوهات
        ↓
   detect_actual_residence(regions, timestamps)
        ↓
   نتيجة نهائيّة:
     - region_iso
     - actual_residence
     - residence_confidence
     - region_distribution
     - videos_analyzed
     - previous_residence
     - timezone_match
        ↓
   display_single_result(result)
        ↓
   عرض البطاقات + الكرة الأرضية
```

---

## 🛡️ خوارزميّة Multi-Signal للإقامة

### مدخلات الخوارزميّة
1. **regions_seq**: قائمة الدول من آخر 5 فيديوهات
2. **times_seq**: قائمة timestamps (UTC) لنفس الفيديوهات

### الخطوات
1. **حساب التكرار**: الدولة الأكثر تكراراً
2. **تحليل Timezone**: من ساعات النشر، نستنتج timezone تقريبي
3. **مطابقة Timezone مع الدولة**: إن طابقت، ثقة +15%
4. **التحقّق من التسلسل**: إن كانت الدولة الأخيرة مختلفة، ثقة -10%
5. **النتيجة**: residence_type (ثابت / مسافر / متنقّل) + confidence (0-100%)

### عتبات الثقة
- **85%+** → ثابت / موثوقة جداً (أخضر)
- **70-84%** → مستقر / موثوقة (برتقالي)
- **<70%** → منخفضة (رمادي)

---

## 🌐 معالجة الـ Proxies

### PROXY_CHAIN
```python
PROXY_CHAIN = [
    {'name': 'jina',       'url': 'https://r.jina.ai/',                       'timeout': 15},
    {'name': 'allorigins', 'url': 'https://api.allorigins.win/raw?url=',      'timeout': 18},
    {'name': 'corsproxy',  'url': 'https://corsproxy.io/?',                   'timeout': 15},
    {'name': 'codetabs',   'url': 'https://api.codetabs.com/v1/proxy?quest=', 'timeout': 20},
]
```

### Rate-Limit Logic
- `_TIKWM_LAST_CALL`: آخر استدعاء TikWM (تأخير 0.6 ث بين الطلبات)
- `_RATELIMIT_BURST`: حظر مؤقّت بعد 429 (15 ث)
- Retry: 3 محاولات بـ exponential backoff

---

## 🧪 تغطية الاختبارات (الحاليّة)

| النوع | الحالة |
|-------|--------|
| Unit Tests | ❌ غير موجود |
| Integration Tests | ❌ غير موجود |
| Live Tests | ✅ يدوي (12 حساب → 100%) |
| Syntax Validation | ✅ py_compile قبل كل Patch |

**ملاحظة CTO:** بناء testing suite كامل هو الخطوة التالية القادمة قبل Patch15.

---

## 📡 نقاط الدخول (Entry Points)

| النقطة | الوصف |
|--------|------|
| `streamlit run app.py` | تشغيل التطبيق الرئيسي |
| `lookup_user(username)` | API داخلي لاستعلام حساب |
| `process_bulk(usernames)` | API داخلي للمعالجة الجماعيّة |

---

## ⚠️ الديون التقنيّة المعروفة (Technical Debt)

1. **Monolith:** كل الكود في `app.py` (2,740 سطر) — يحتاج تقسيم إلى modules
2. **CSS Inline:** أكثر من 200 inline style — يحتاج نقل إلى classes
3. **لا اختبارات أوتوماتيكيّة:** مخاطرة Regression
4. **لا Logging مركزي:** صعوبة التشخيص الإنتاجي
5. **Cache بدائي:** `@st.cache_data` فقط — لا Redis
6. **اعتماد على PROXY_CHAIN خارجي:** مخاطرة انقطاع الخدمات المجانيّة

---

## 🎯 خارطة الطريق (Roadmap)

### مرحلة الاستقرار (1-2 أسبوع)
- ✅ قفل Patch14 (مُنجَز)
- 📝 توثيق البنية (هذا المستند)
- 🧪 بناء pytest suite
- 📊 إعداد logging مركزي

### مرحلة إعادة الهيكلة (2-4 أسبوع)
- 🏗️ تقسيم `app.py` إلى modules: `core/`, `ui/`, `api/`, `utils/`
- 🎨 استخراج CSS إلى ملف خارجي
- 💾 نظام Cache بـ Redis

### مرحلة التطوير (شهر+)
- 📱 تحسين الاستجابة مع الجوال (Mobile Optimization)
- 📊 API endpoint REST
- 🔔 Webhooks للإشعارات

---

## 📞 معلومات التواصل

- **القائد:** د. أحمد الفنّي
- **معرّف المشروع:** Baseer
- **مستودع GitHub:** https://github.com/7sn301/social-accounts-generator
- **الموقع الحيّ:** https://baseer1.streamlit.app/

---

## 🔒 ختم القفل الإنتاجي

```
═══════════════════════════════════════════════════════════
🔒 PRODUCTION LOCK: BSR-V217L-PRODUCTION-LOCK-PATCH14
📅 Date: 2026-06-13
✅ CTO Stamp: Approved (8.4/10)
🛡️ Constraints: 28/28 enforced
═══════════════════════════════════════════════════════════
```
