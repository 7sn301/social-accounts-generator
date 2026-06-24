<div dir="rtl">

# 🧪 Baseer — Testing Suite

**المعرّف:** `BSR-V217L-TESTS-README-AHMAD-20260613`
**التاريخ:** 2026-06-13
**القائد:** د. أحمد الفنّي
**الإصدار المرتبط:** `v2.1.7-Light-Fix3.2-Patch14-Mobile-HOTFIX`

---

## 📊 الحالة

| المؤشر | القيمة |
|---|---|
| ✅ نجاح | **35 / 35** (100%) |
| ⏱️ المدّة | ~0.14 ث |
| 🐍 Python | 3.13+ |
| 🧪 pytest | 8.3.5 |

---

## 🚀 التشغيل

```bash
pip install pytest>=8.3.5
pytest tests/ -v
```

---

## 📁 البنية

| الملف | الوصف | عدد الاختبارات |
|---|---|---|
| `__init__.py` | تعريف الحزمة | — |
| `_extract_constants.py` | مستخرج الثوابت عبر AST (لا تنفيذ كامل لـ `app.py`) | — |
| `conftest.py` | Fixtures + Mocking لـ Streamlit | — |
| `test_constants.py` | اختبارات الثوابت الجوهرية + قيود الخصوصية #21 | 12 |
| `test_data_integrity.py` | اختبارات RTL + الخطوط + لوحة الألوان + استبعاد الإصدارات | 9 |
| `test_globe_render.py` | اختبارات خريطة Plotly Orthographic + tooltip RTL | 6 |
| `test_residence_logic.py` | اختبارات منطق الإقامة #19 Multi-Signal + توزيع المناطق | 8 |
| **المجموع** | | **35** |

---

## 🛡️ القيود الدائمة المُغطّاة (28/28)

- `dir='rtl'` في كل HTML
- خطوط Noto Sans Arabic/Tajawal
- ألوان `#0F172A` / `#F59E0B` / `#F1F5F9`
- بطاقات منفصلة + رسائل زرقاء فقط
- لا IP — لا Geocoding خارجي — لا TikAPI/Apify
- "—" للمجهول
- استبعاد إصدارات `v2.1.8` / `v2.1.9` / `v2.2.0` / `v2.3.0` / `v3.0`
- TikTok حصراً (#20) — لا PII (#21)
- Multi-Signal #19

---

## 🤖 GitHub Actions CI (مُقترَح)

```yaml
name: Baseer Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.13' }
      - run: pip install -r requirements.txt pytest plotly
      - run: pytest tests/ -v
```

</div>
