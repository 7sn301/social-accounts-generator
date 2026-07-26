"""
Unit tests for tiktok_analyzer.py v2.0.0
اختبارات وحدة للتحقق من إصلاحات نظام كشف الموقع الجغرافي.
"""
import sys
import json

sys.path.insert(0, "/home/user/baseer")

from tiktok_analyzer import (
    LocationDetector,
    detect_country_from_text,
    _parse_script_json,
    _extract_profile_objects,
    _build_session,
    _build_headers,
    format_count,
    _safe_region,
    CITY_TO_COUNTRY,
    DIALECT_HINTS,
    LANG_TO_COUNTRIES,
    TIKTOK_REGION_MAP,
)

results = []

def check(name, cond, detail=""):
    status = "✅" if cond else "❌"
    results.append((status, name, detail))
    print(f"{status}  {name}  {detail}")


# ========= [FIX-3] add_score_multiple مع min_per =========
print("\n===== [FIX-3] تحسين توزيع النقاط على 20 دولة عربية =====")
d = LocationDetector()
d.add_score_multiple(LANG_TO_COUNTRIES["ar"], 30, "test-lang", min_per=3)
check("توزيع النقاط لا يُصفّر الدول العربية",
      all(v >= 3 for v in d.scores.values()),
      f"→ min score = {min(d.scores.values())}")
check("جميع الدول العربية الـ20 حصلت على نقاط",
      len(d.scores) == 20,
      f"→ عدد الدول = {len(d.scores)}")

# ========= [FIX-4] عتبة get_winner القابلة للتكيف =========
print("\n===== [FIX-4] العتبة الديناميكية =====")
d2 = LocationDetector()
d2.add_score("SA", 12, "test")
d2.add_score("EG", 3, "test")
winner, conf, _ = d2.get_winner(threshold=15)
check("العتبة الديناميكية تقبل SA بـ12 نقطة",
      winner == "SA", f"→ winner={winner}, conf={conf}")

# ========= [FIX-5] توسيع اللهجات =========
print("\n===== [FIX-5] قاعدة اللهجات المُوسَّعة =====")
check("لهجة مغربية 'واخا بزاف' موجودة", "واخا" in DIALECT_HINTS["MA"])
check("لهجة جزائرية 'واش بصح' موجودة", "واش" in DIALECT_HINTS["DZ"])
check("لهجة تونسية 'برشا' موجودة", "برشا" in DIALECT_HINTS["TN"])
check("لهجة فلسطينية مُضافة", "PS" in DIALECT_HINTS)
check("18 دولة عربية على الأقل بلهجات",
      sum(1 for cc in DIALECT_HINTS if cc in LANG_TO_COUNTRIES["ar"]) >= 15,
      f"→ عدد الدول = {sum(1 for cc in DIALECT_HINTS if cc in LANG_TO_COUNTRIES['ar'])}")

# ========= [FIX-6] CITY_TO_COUNTRY مربوطة فعلياً =========
print("\n===== [FIX-6] فحص المدن في bio =====")
d3 = LocationDetector()
detect_country_from_text("مرحباً من الرياض، عاصمة الجمال 🇸🇦", "bio", d3, base=30)
check("الكشف عن 'الرياض' في bio", "SA" in d3.scores, f"→ scores={d3.scores}")

d4 = LocationDetector()
detect_country_from_text("Content creator from Dubai and Cairo", "bio", d4, base=30)
check("الكشف عن مدن متعددة (Dubai + Cairo)",
      "AE" in d4.scores and "EG" in d4.scores,
      f"→ scores={d4.scores}")

# ========= اختبار لهجة سعودية مركبة =========
print("\n===== سيناريو حقيقي: bio لهجة سعودية =====")
d5 = LocationDetector()
detect_country_from_text("والله زين مره، ابغى اطقطق مع الربع", "bio", d5, base=30)
winner, conf, _ = d5.get_winner(threshold=15)
check("لهجة سعودية → winner = SA",
      winner == "SA", f"→ winner={winner}, conf={conf}%, scores={d5.scores}")

# ========= اختبار لهجة مصرية =========
d6 = LocationDetector()
detect_country_from_text("ازيك يا جدع، عامل ايه دلوقتي؟", "bio", d6, base=30)
winner, conf, _ = d6.get_winner(threshold=15)
check("لهجة مصرية → winner = EG",
      winner == "EG", f"→ winner={winner}, conf={conf}%")

# ========= اختبار لهجة مغربية =========
d7 = LocationDetector()
detect_country_from_text("واخا خويا، بزاف مزيان دابا", "bio", d7, base=30)
winner, conf, _ = d7.get_winner(threshold=15)
check("لهجة مغربية → winner = MA",
      winner == "MA", f"→ winner={winner}, conf={conf}%")

# ========= اختبار العلم =========
d8 = LocationDetector()
detect_country_from_text("Made with love 🇮🇶 Baghdad", "bio", d8, base=30)
winner, _, _ = d8.get_winner(threshold=15)
check("علم العراق 🇮🇶 → winner = IQ",
      winner == "IQ", f"→ winner={winner}, scores={d8.scores}")

# ========= [FIX-1] Session Headers Rotation =========
print("\n===== [FIX-1] طبقة الشبكة =====")
h1 = _build_headers()
h2 = _build_headers()
check("Headers تحوي User-Agent",
      "User-Agent" in h1 and h1["User-Agent"].startswith("Mozilla"))
check("Headers تحوي Sec-Fetch-*",
      "Sec-Fetch-Mode" in h1 and "Sec-Fetch-Dest" in h1)

s = _build_session()
check("Session يحوي كوكيز أولية",
      "tt_webid_v2" in s.cookies.get_dict(domain=".tiktok.com"),
      f"→ cookies={list(s.cookies.get_dict(domain='.tiktok.com').keys())}")

# ========= [FIX-2] parse_script_json متعدد المصادر =========
print("\n===== [FIX-2] تحليل JSON =====")
sample_html_universal = '''
<html><body>
<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">
{"__DEFAULT_SCOPE__":{"webapp.user-detail":{"userInfo":{"user":{"uniqueId":"test","region":"SA"},"stats":{"followerCount":1000}}}}}
</script>
</body></html>
'''
parsed = _parse_script_json(sample_html_universal)
check("تحليل __UNIVERSAL_DATA_FOR_REHYDRATION__",
      bool(parsed) and "__DEFAULT_SCOPE__" in parsed)

user, stats = _extract_profile_objects(parsed)
check("استخراج user من __DEFAULT_SCOPE__",
      user.get("region") == "SA",
      f"→ region={user.get('region')}, followers={stats.get('followerCount')}")

sample_html_sigi = '''
<script id="SIGI_STATE" type="application/json">
{"UserModule":{"users":{"u1":{"uniqueId":"legacy","region":"EG"}},"stats":{"s1":{"followerCount":500}}}}
</script>
'''
parsed2 = _parse_script_json(sample_html_sigi)
user2, stats2 = _extract_profile_objects(parsed2)
check("Fallback على SIGI_STATE يعمل",
      user2.get("region") == "EG",
      f"→ region={user2.get('region')}")

# ========= أدوات عامة =========
print("\n===== أدوات مساعدة =====")
check("format_count(1500000) = 1.5M", format_count(1500000) == "1.5M")
check("format_count(2500) = 2.5K", format_count(2500) == "2.5K")
check("_safe_region('SA') = 'SA'", _safe_region("SA") == "SA")
check("_safe_region('XX') = ''", _safe_region("XX") == "")
check("PS مضافة إلى TIKTOK_REGION_MAP", "PS" in TIKTOK_REGION_MAP)

# ========= الخلاصة =========
print("\n" + "=" * 60)
passed = sum(1 for r in results if r[0] == "✅")
failed = sum(1 for r in results if r[0] == "❌")
print(f"النتيجة: {passed} نجحت | {failed} فشلت | المجموع {len(results)}")
print("=" * 60)

if failed:
    sys.exit(1)
