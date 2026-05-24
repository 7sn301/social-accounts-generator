"""
محلل X (Twitter) المتقدم
X Deep Analyzer - Uses public Twitter Syndication API

🔥 الاكتشاف:
Twitter Syndication API (cdn.syndication.twimg.com) يعمل بدون مصادقة
ويعطي بيانات تغريدة كاملة! يحتاج فقط token محسوب من tweet_id.

البيانات المستخرجة:
- 🆔 Tweet ID و User ID (دائمين)
- 📝 نص التغريدة كاملاً
- 📅 تاريخ النشر بدقة الثانية
- 🌐 لغة التغريدة (مفيد لكشف الموقع)
- ❤️ عدد الإعجابات والردود
- 🖼️ الصور والفيديوهات
- ✓ التوثيق ونوع التوثيق (Government/Business/News)
- 🔗 رابط البروفايل + صورة البروفايل
"""

import requests
import json
import math
import re
from datetime import datetime
from urllib.parse import urlparse


# ============ Headers ============
X_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
}


# ============ خرائط الدول واللغات ============
X_REGION_MAP = {
    "SA": ("🇸🇦", "السعودية"), "AE": ("🇦🇪", "الإمارات"), "EG": ("🇪🇬", "مصر"),
    "KW": ("🇰🇼", "الكويت"), "QA": ("🇶🇦", "قطر"), "BH": ("🇧🇭", "البحرين"),
    "OM": ("🇴🇲", "عُمان"), "JO": ("🇯🇴", "الأردن"), "LB": ("🇱🇧", "لبنان"),
    "SY": ("🇸🇾", "سوريا"), "IQ": ("🇮🇶", "العراق"), "YE": ("🇾🇪", "اليمن"),
    "PS": ("🇵🇸", "فلسطين"), "MA": ("🇲🇦", "المغرب"), "DZ": ("🇩🇿", "الجزائر"),
    "TN": ("🇹🇳", "تونس"), "LY": ("🇱🇾", "ليبيا"), "SD": ("🇸🇩", "السودان"),
    "SO": ("🇸🇴", "الصومال"), "MR": ("🇲🇷", "موريتانيا"),
    "US": ("🇺🇸", "الولايات المتحدة"), "GB": ("🇬🇧", "بريطانيا"), "FR": ("🇫🇷", "فرنسا"),
    "DE": ("🇩🇪", "ألمانيا"), "IT": ("🇮🇹", "إيطاليا"), "ES": ("🇪🇸", "إسبانيا"),
    "NL": ("🇳🇱", "هولندا"), "RU": ("🇷🇺", "روسيا"), "UA": ("🇺🇦", "أوكرانيا"),
    "CN": ("🇨🇳", "الصين"), "JP": ("🇯🇵", "اليابان"), "KR": ("🇰🇷", "كوريا الجنوبية"),
    "IN": ("🇮🇳", "الهند"), "PK": ("🇵🇰", "باكستان"), "TR": ("🇹🇷", "تركيا"),
    "IR": ("🇮🇷", "إيران"), "BR": ("🇧🇷", "البرازيل"), "MX": ("🇲🇽", "المكسيك"),
    "CA": ("🇨🇦", "كندا"), "AU": ("🇦🇺", "أستراليا"),
    "ID": ("🇮🇩", "إندونيسيا"), "MY": ("🇲🇾", "ماليزيا"),
    "TH": ("🇹🇭", "تايلاند"), "JP": ("🇯🇵", "اليابان"),
    "NG": ("🇳🇬", "نيجيريا"), "ZA": ("🇿🇦", "جنوب أفريقيا"),
}

LANGUAGE_NAMES_AR_X = {
    "ar": "العربية", "en": "الإنجليزية", "es": "الإسبانية", "fr": "الفرنسية",
    "de": "الألمانية", "it": "الإيطالية", "pt": "البرتغالية", "ru": "الروسية",
    "tr": "التركية", "fa": "الفارسية", "ur": "الأردية", "hi": "الهندية",
    "zh": "الصينية", "ja": "اليابانية", "ko": "الكورية", "id": "الإندونيسية",
    "ms": "الماليزية", "th": "التايلاندية", "vi": "الفيتنامية",
    "nl": "الهولندية", "pl": "البولندية", "el": "اليونانية",
    "he": "العبرية", "uk": "الأوكرانية", "und": "غير محدد",
}

LANG_TO_COUNTRIES_X = {
    "ar": ["SA", "EG", "AE", "MA", "DZ", "IQ", "KW", "QA", "JO", "LB", "TN", "LY", "SY", "YE"],
    "tr": ["TR"], "fa": ["IR"], "ur": ["PK"], "hi": ["IN"], "id": ["ID"],
    "ja": ["JP"], "ko": ["KR"], "ru": ["RU"], "uk": ["UA"], "pl": ["PL"],
    "es": ["ES", "MX", "AR"], "pt": ["BR", "PT"], "de": ["DE"], "it": ["IT"],
    "nl": ["NL"], "el": ["GR"], "he": ["IL"], "th": ["TH"],
}

# مدن للاستنتاج من البايو
CITY_TO_COUNTRY_X = {
    "riyadh": "SA", "jeddah": "SA", "mecca": "SA", "makkah": "SA", "dammam": "SA",
    "الرياض": "SA", "جدة": "SA", "مكة": "SA", "الدمام": "SA", "السعودية": "SA",
    "ksa": "SA", "saudi arabia": "SA",
    "dubai": "AE", "abu dhabi": "AE", "sharjah": "AE",
    "دبي": "AE", "أبوظبي": "AE", "الشارقة": "AE", "الإمارات": "AE", "الامارات": "AE", "uae": "AE",
    "cairo": "EG", "alexandria": "EG", "egypt": "EG",
    "القاهرة": "EG", "الإسكندرية": "EG", "مصر": "EG",
    "kuwait": "KW", "الكويت": "KW", "doha": "QA", "qatar": "QA", "الدوحة": "QA", "قطر": "QA",
    "manama": "BH", "bahrain": "BH", "البحرين": "BH",
    "muscat": "OM", "oman": "OM", "مسقط": "OM", "سلطنة عمان": "OM",
    "amman": "JO", "jordan": "JO", "عمّان": "JO", "الأردن": "JO",
    "beirut": "LB", "lebanon": "LB", "بيروت": "LB", "لبنان": "LB",
    "baghdad": "IQ", "iraq": "IQ", "بغداد": "IQ", "العراق": "IQ", "البصرة": "IQ",
    "damascus": "SY", "syria": "SY", "دمشق": "SY", "سوريا": "SY", "حلب": "SY",
    "sanaa": "YE", "yemen": "YE", "صنعاء": "YE", "اليمن": "YE",
    "palestine": "PS", "gaza": "PS", "فلسطين": "PS", "غزة": "PS", "القدس": "PS",
    "morocco": "MA", "casablanca": "MA", "rabat": "MA",
    "المغرب": "MA", "الدار البيضاء": "MA", "الرباط": "MA",
    "algeria": "DZ", "الجزائر": "DZ",
    "tunisia": "TN", "تونس": "TN",
    "libya": "LY", "ليبيا": "LY",
    "sudan": "SD", "khartoum": "SD", "السودان": "SD", "الخرطوم": "SD",
    "usa": "US", "united states": "US", "america": "US", "new york": "US",
    "uk": "GB", "london": "GB", "britain": "GB", "england": "GB",
    "france": "FR", "paris": "FR", "germany": "DE", "berlin": "DE",
    "turkey": "TR", "istanbul": "TR", "تركيا": "TR", "إسطنبول": "TR",
    "iran": "IR", "tehran": "IR", "إيران": "IR",
    "india": "IN", "pakistan": "PK", "japan": "JP", "korea": "KR",
    "russia": "RU", "روسيا": "RU", "ukraine": "UA",
    "brazil": "BR", "mexico": "MX", "canada": "CA", "australia": "AU",
}

# لهجات عربية
DIALECT_HINTS_X = {
    "SA": ["والله", "وش رايك", "تكفى", "يا اخوي", "وايد", "خوش", "حياك"],
    "EG": ["ازيك", "إزيك", "ازاي", "إزاي", "كده", "كدا", "اوي", "أوي", "خالص", "بقى", "يلا"],
    "AE": ["شحالك", "هلا والله", "وايد"],
    "KW": ["شلونك", "حياك", "تكفى"],
    "MA": ["واخا", "بزاف", "زعما", "كيفاش", "شنو", "غادي", "دابا"],
    "DZ": ["واش", "كيراك", "بصح", "بزاف"],
    "IQ": ["شلون", "اشلون", "هسة", "اكو", "ماكو", "هواي", "وين"],
    "LB": ["شو في", "كيفك", "هلق", "بدي", "كتير"],
    "SY": ["شو في", "كيفك", "هلق", "بدي", "كتير", "هلأ"],
    "YE": ["كيف حالك", "وشلون"],
}


def format_count(n):
    try:
        n = int(n)
        if n >= 1_000_000_000:
            return f"{n/1_000_000_000:.1f}B"
        elif n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        elif n >= 1_000:
            return f"{n/1_000:.1f}K"
        return str(n)
    except (ValueError, TypeError):
        return "0"


# ============ Token Calculation ============
def calculate_syndication_token(tweet_id):
    """
    حساب token المطلوب للـ Syndication API.
    
    JS algorithm: ((Number(id) / 1e15) * Math.PI).toString(36).replace(zeros and dots, '')
    """
    try:
        n = (int(tweet_id) / 1e15) * math.pi
        digits = "0123456789abcdefghijklmnopqrstuvwxyz"
        int_part = int(n)
        result = ""
        while int_part > 0:
            result = digits[int_part % 36] + result
            int_part //= 36
        if not result:
            result = "0"
        frac = n - int(n)
        if frac > 0:
            result += "."
            for _ in range(25):
                frac *= 36
                d = int(frac)
                result += digits[d]
                frac -= d
                if frac == 0:
                    break
        # إزالة الأصفار والنقاط
        return re.sub(r"(0+|\.)", "", result)
    except Exception:
        return ""


# ============ Parsing ============
def parse_x_url(url):
    """استخراج username و tweet_id من رابط X/Twitter."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower().replace("www.", "")
        if host not in ("x.com", "twitter.com", "mobile.twitter.com", "mobile.x.com"):
            return None, None

        # /username/status/1234567890
        m = re.search(r"^/([\w_]+)/status(?:es)?/(\d+)", parsed.path)
        if m:
            return m.group(1), m.group(2)
    except Exception:
        pass
    return None, None


# ============ كشف الموقع ============
class LocationDetectorX:
    def __init__(self):
        self.scores = {}
        self.evidence = []

    def add_score(self, country_code, points, source):
        if not country_code:
            return
        self.scores[country_code] = self.scores.get(country_code, 0) + points
        self.evidence.append(f"{source} (+{points})")

    def add_score_multiple(self, countries, points, source):
        if not countries:
            return
        per = points // len(countries) if len(countries) > 1 else points
        for cc in countries:
            self.scores[cc] = self.scores.get(cc, 0) + per
        if per > 0:
            self.evidence.append(f"{source} (+{per})")

    def get_winner(self, threshold=20):
        if not self.scores:
            return None, 0, []
        sorted_c = sorted(self.scores.items(), key=lambda x: -x[1])
        top, score = sorted_c[0]
        if score < threshold:
            return None, 0, [c for c, s in sorted_c[:5]]
        total = sum(self.scores.values())
        confidence = min(int((score / total) * 100), 100)
        if len(sorted_c) > 1 and score >= sorted_c[1][1] * 2:
            confidence = min(confidence + 15, 100)
        candidates = [c for c, s in sorted_c[:3] if c != top]
        return top, confidence, candidates


def detect_country_from_text(text, source_name, detector, base=30):
    if not text:
        return
    text_lower = text.lower()
    # أعلام
    for cc, (flag, _) in X_REGION_MAP.items():
        if flag in text:
            detector.add_score(cc, base + 30, f"🚩 علم {cc} في {source_name}")
            return
    # مدن/دول
    for kw in sorted(CITY_TO_COUNTRY_X.keys(), key=len, reverse=True):
        cc = CITY_TO_COUNTRY_X[kw]
        if any(ord(c) > 127 for c in kw):
            if kw in text:
                detector.add_score(cc, base + 20, f"🏙️ '{kw}' في {source_name}")
                return
        else:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                detector.add_score(cc, base + 15, f"🏙️ '{kw}' في {source_name}")
                return
    # لهجات
    for cc, hints in DIALECT_HINTS_X.items():
        cnt = sum(1 for h in hints if h in text)
        if cnt >= 2:
            detector.add_score(cc, base + 5, f"🗣️ لهجة {cc} ({cnt}) في {source_name}")
            return
        elif cnt == 1:
            detector.add_score(cc, base - 10, f"🗣️ احتمال لهجة {cc} في {source_name}")


# ============ التحليل الرئيسي ============
def analyze_x_tweet(tweet_url_or_id, timeout=15):
    """
    🎯 تحليل تغريدة X بكامل التفاصيل.
    
    يقبل: 
    - رابط كامل: https://x.com/elonmusk/status/123456
    - رابط twitter.com: https://twitter.com/elonmusk/status/123456
    - tweet ID فقط: 123456789012345
    
    يستخدم Twitter Syndication API (cdn.syndication.twimg.com)
    """
    result = {
        "tweet_url": "",
        "tweet_id": "",
        "status": "❌ فشل",
        "error": "",
        # Tweet info
        "text": "",
        "lang": "",
        "lang_name_ar": "",
        "created_at": "",
        "favorite_count": 0,  # likes
        "favorite_count_formatted": "",
        "conversation_count": 0,  # replies
        "conversation_count_formatted": "",
        "possibly_sensitive": False,
        # Media
        "media_count": 0,
        "media_type": "",
        "media_urls": "",
        "video_url": "",
        # User info
        "user_id": "",
        "user_screen_name": "",
        "user_name": "",
        "user_profile_image": "",
        "user_verified": False,
        "user_blue_verified": False,
        "user_verified_type": "",
        "user_profile_shape": "",
        # Location
        "region": "",
        "region_flag": "",
        "region_name_ar": "",
        "region_source": "",
        "region_confidence": 0,
        "region_evidence": "",
        "candidates": "",
        # Entities
        "hashtags": "",
        "mentions": "",
        "urls": "",
    }

    # تحديد tweet_id
    s = str(tweet_url_or_id).strip()
    if s.isdigit():
        tweet_id = s
        username = ""
    else:
        username, tweet_id = parse_x_url(s)
        if not tweet_id:
            result["error"] = "رابط غير صالح. يجب أن يكون: https://x.com/username/status/ID"
            return result

    result["tweet_id"] = tweet_id
    if username:
        result["tweet_url"] = f"https://x.com/{username}/status/{tweet_id}"
    else:
        result["tweet_url"] = f"https://x.com/i/status/{tweet_id}"

    # احسب token
    token = calculate_syndication_token(tweet_id)
    if not token:
        result["error"] = "فشل حساب token"
        return result

    api_url = f"https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&token={token}&lang=en"

    try:
        r = requests.get(api_url, headers=X_HEADERS, timeout=timeout)
        if r.status_code == 404:
            result["error"] = "التغريدة غير موجودة (404)"
            return result
        if r.status_code != 200:
            result["error"] = f"كود استجابة: {r.status_code}"
            return result
        if r.text in ("{}", ""):
            result["error"] = "التغريدة محذوفة أو خاصة (استجابة فارغة)"
            return result

        try:
            d = r.json()
        except json.JSONDecodeError:
            result["error"] = "استجابة غير صالحة"
            return result

        if not d:
            result["error"] = "لا توجد بيانات"
            return result

        # ============ Tweet Info ============
        result["text"] = d.get("text", "") or ""
        result["lang"] = d.get("lang", "") or ""
        if result["lang"] in LANGUAGE_NAMES_AR_X:
            result["lang_name_ar"] = LANGUAGE_NAMES_AR_X[result["lang"]]

        result["created_at"] = d.get("created_at", "") or ""
        result["favorite_count"] = int(d.get("favorite_count", 0) or 0)
        result["favorite_count_formatted"] = format_count(result["favorite_count"])
        result["conversation_count"] = int(d.get("conversation_count", 0) or 0)
        result["conversation_count_formatted"] = format_count(result["conversation_count"])
        result["possibly_sensitive"] = bool(d.get("possibly_sensitive", False))

        # ============ Media ============
        media = d.get("mediaDetails", []) or []
        result["media_count"] = len(media)
        if media:
            types = list(set(m.get("type", "") for m in media))
            result["media_type"] = ", ".join(t for t in types if t)
            urls = []
            for m in media[:5]:
                if m.get("type") == "video" or m.get("type") == "animated_gif":
                    # video URL
                    vinfo = m.get("video_info", {})
                    variants = vinfo.get("variants", [])
                    # ابحث عن أعلى bitrate mp4
                    best_video = None
                    best_br = 0
                    for v in variants:
                        if v.get("content_type") == "video/mp4":
                            br = v.get("bitrate", 0) or 0
                            if br > best_br:
                                best_br = br
                                best_video = v.get("url", "")
                    if best_video:
                        result["video_url"] = best_video
                        urls.append(best_video)
                    elif variants:
                        urls.append(variants[0].get("url", ""))
                else:
                    u = m.get("media_url_https", "")
                    if u:
                        urls.append(u)
            result["media_urls"] = " | ".join(urls)

        # ============ User Info ============
        u = d.get("user", {}) or {}
        result["user_id"] = str(u.get("id_str", "") or "")
        result["user_screen_name"] = u.get("screen_name", "") or ""
        result["user_name"] = u.get("name", "") or ""
        result["user_profile_image"] = u.get("profile_image_url_https", "") or ""
        result["user_verified"] = bool(u.get("verified", False))
        result["user_blue_verified"] = bool(u.get("is_blue_verified", False))
        result["user_verified_type"] = u.get("verified_type", "") or ""
        result["user_profile_shape"] = u.get("profile_image_shape", "") or ""

        # ============ Entities (hashtags, mentions, urls) ============
        ent = d.get("entities", {}) or {}
        hashtags = [f"#{h.get('text', '')}" for h in ent.get("hashtags", []) if h.get("text")]
        mentions = [f"@{m.get('screen_name', '')}" for m in ent.get("user_mentions", []) if m.get("screen_name")]
        urls_e = [u_e.get("expanded_url", "") for u_e in ent.get("urls", []) if u_e.get("expanded_url")]
        result["hashtags"] = " ".join(hashtags[:10])
        result["mentions"] = " ".join(mentions[:10])
        result["urls"] = " | ".join(urls_e[:5])

        # ============ Location Detection ============
        detector = LocationDetectorX()

        # 1. تحليل نص التغريدة
        if result["text"]:
            detect_country_from_text(result["text"], "نص التغريدة", detector, 30)

        # 2. تحليل الاسم الظاهر للمستخدم
        if result["user_name"]:
            detect_country_from_text(result["user_name"], "اسم المستخدم", detector, 25)

        # 3. تحليل screen_name
        if result["user_screen_name"]:
            detect_country_from_text(result["user_screen_name"], "اليوزر", detector, 15)

        # 4. تحليل اللغة
        if result["lang"] in LANG_TO_COUNTRIES_X:
            possible = LANG_TO_COUNTRIES_X[result["lang"]]
            if len(possible) == 1:
                detector.add_score(possible[0], 30, f"🌐 اللغة {result['lang']}")
            else:
                detector.add_score_multiple(possible, 20, f"🌐 اللغة {result['lang']}")

        # 5. تحليل hashtags - قد تكشف الدولة
        if result["hashtags"]:
            detect_country_from_text(result["hashtags"], "الهاشتاقات", detector, 20)

        # القرار النهائي
        winner, confidence, candidates = detector.get_winner(threshold=15)
        if winner:
            result["region"] = winner
            flag, name_ar = X_REGION_MAP.get(winner, ("🌍", winner))
            result["region_flag"] = flag
            result["region_name_ar"] = name_ar
            result["region_confidence"] = confidence
            result["region_source"] = "🧠 تحليل ذكي"
            result["region_evidence"] = " | ".join(detector.evidence[:5])
            if candidates:
                result["candidates"] = "|".join(candidates)
        elif candidates:
            result["candidates"] = "|".join(candidates)
            result["region_source"] = "دول محتملة"
            result["region_evidence"] = " | ".join(detector.evidence[:3])

        # ============ Status ============
        if result["text"] or result["user_id"]:
            result["status"] = "✅ نجح"

    except requests.Timeout:
        result["error"] = "انتهت مهلة الاتصال"
    except requests.ConnectionError:
        result["error"] = "خطأ في الاتصال"
    except Exception as e:
        result["error"] = f"خطأ: {str(e)[:150]}"

    return result


# ============ تحليل بروفايل X الكامل ============
def analyze_x_profile_via_tweet(username, tweet_id, timeout=15):
    """
    تحليل بروفايل عبر تغريدة منشورة من المستخدم.
    لأن X لا يسمح بـ scraping للبروفايلات بدون auth، نحلل عبر تغريدة.
    """
    return analyze_x_tweet(f"https://x.com/{username}/status/{tweet_id}", timeout=timeout)


# ============ اختبار ============
if __name__ == "__main__":
    import sys
    test_urls = sys.argv[1:] if len(sys.argv) > 1 else [
        "https://x.com/elonmusk/status/1874342693310259604",
        "https://x.com/SaudiMOH/status/1941171425823576458",
        "https://twitter.com/elonmusk/status/2007910921914769832",
    ]

    for url in test_urls:
        print(f"\n{'='*60}\n🔍 {url}\n{'='*60}")
        d = analyze_x_tweet(url)

        if d["status"] == "✅ نجح":
            verified_mark = ""
            if d["user_blue_verified"]:
                verified_mark = " ✓"
            if d["user_verified_type"]:
                verified_mark += f" ({d['user_verified_type']})"
            print(f"👤 {d['user_name']} (@{d['user_screen_name']}){verified_mark}")
            print(f"🆔 User ID: {d['user_id']}")
            print(f"🐦 Tweet ID: {d['tweet_id']}")
            print(f"📅 {d['created_at']}")
            print(f"🌐 اللغة: {d['lang_name_ar']} ({d['lang']})")
            print(f"\n📝 النص: {d['text'][:200]}")
            if d["media_count"]:
                print(f"\n🖼️ {d['media_count']} وسائط ({d['media_type']}):")
                for u in d["media_urls"].split(" | ")[:2]:
                    print(f"   {u}")
                if d["video_url"]:
                    print(f"🎬 رابط الفيديو: {d['video_url'][:80]}...")
            print(f"\n📊 ❤️ {d['favorite_count_formatted']} | 💬 {d['conversation_count_formatted']}")
            if d["hashtags"]:
                print(f"#️⃣ {d['hashtags']}")
            if d["mentions"]:
                print(f"@️⃣ {d['mentions']}")
            print(f"\n🌍 ===== كشف الموقع =====")
            if d["region"]:
                print(f"   {d['region_flag']} {d['region_name_ar']} ({d['region']}) - ثقة {d['region_confidence']}%")
                print(f"   📋 {d['region_source']}")
                print(f"   🔍 الأدلة:")
                for e in d["region_evidence"].split(" | "):
                    print(f"      - {e}")
                if d["candidates"]:
                    print(f"   🤔 محتمل: {d['candidates']}")
            else:
                print(f"   ❓ لم يتم تحديد دولة")
                if d["candidates"]:
                    print(f"   🤔 محتمل: {d['candidates']}")
        else:
            print(f"❌ {d['error']}")
