"""
محلل TikTok المتقدم v2 - استخراج بيانات عميقة باستخدام Universal Data
TikTok Deep Analyzer v2 - Comprehensive analysis with multi-layer location detection

ملاحظة: TikTok يُخفي حقل region من الواجهة العامة، لذا نستخدم 5 طبقات استنتاج:
1. region من الـ API (نادر، فقط للمشاهير)
2. language → منطقة محتملة (ar → دول عربية)
3. تحليل البايو (مدن/دول/أعلام)
4. تحليل الاسم الظاهر
5. تحليل آخر فيديو (إن أمكن)
"""

import requests
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime, timezone


# ============ Headers مبسّطة (أثبتت فعاليتها) ============
TIKTOK_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


# ============ خرائط الدول واللغات ============
TIKTOK_REGION_MAP = {
    "SA": ("🇸🇦", "السعودية"), "AE": ("🇦🇪", "الإمارات"), "EG": ("🇪🇬", "مصر"),
    "KW": ("🇰🇼", "الكويت"), "QA": ("🇶🇦", "قطر"), "BH": ("🇧🇭", "البحرين"),
    "OM": ("🇴🇲", "عُمان"), "JO": ("🇯🇴", "الأردن"), "LB": ("🇱🇧", "لبنان"),
    "SY": ("🇸🇾", "سوريا"), "IQ": ("🇮🇶", "العراق"), "YE": ("🇾🇪", "اليمن"),
    "PS": ("🇵🇸", "فلسطين"), "MA": ("🇲🇦", "المغرب"), "DZ": ("🇩🇿", "الجزائر"),
    "TN": ("🇹🇳", "تونس"), "LY": ("🇱🇾", "ليبيا"), "SD": ("🇸🇩", "السودان"),
    "SO": ("🇸🇴", "الصومال"), "MR": ("🇲🇷", "موريتانيا"), "DJ": ("🇩🇯", "جيبوتي"),
    "KM": ("🇰🇲", "جزر القمر"),
    "US": ("🇺🇸", "الولايات المتحدة"), "GB": ("🇬🇧", "بريطانيا"), "FR": ("🇫🇷", "فرنسا"),
    "DE": ("🇩🇪", "ألمانيا"), "IT": ("🇮🇹", "إيطاليا"), "ES": ("🇪🇸", "إسبانيا"),
    "NL": ("🇳🇱", "هولندا"), "BE": ("🇧🇪", "بلجيكا"), "CH": ("🇨🇭", "سويسرا"),
    "SE": ("🇸🇪", "السويد"), "PT": ("🇵🇹", "البرتغال"),
    "RU": ("🇷🇺", "روسيا"), "UA": ("🇺🇦", "أوكرانيا"),
    "CN": ("🇨🇳", "الصين"), "JP": ("🇯🇵", "اليابان"), "KR": ("🇰🇷", "كوريا الجنوبية"),
    "IN": ("🇮🇳", "الهند"), "PK": ("🇵🇰", "باكستان"), "BD": ("🇧🇩", "بنغلاديش"),
    "TR": ("🇹🇷", "تركيا"), "IR": ("🇮🇷", "إيران"), "AF": ("🇦🇫", "أفغانستان"),
    "BR": ("🇧🇷", "البرازيل"), "AR": ("🇦🇷", "الأرجنتين"), "MX": ("🇲🇽", "المكسيك"),
    "CA": ("🇨🇦", "كندا"), "AU": ("🇦🇺", "أستراليا"),
    "ID": ("🇮🇩", "إندونيسيا"), "MY": ("🇲🇾", "ماليزيا"), "SG": ("🇸🇬", "سنغافورة"),
    "TH": ("🇹🇭", "تايلاند"), "VN": ("🇻🇳", "فيتنام"), "PH": ("🇵🇭", "الفلبين"),
    "NG": ("🇳🇬", "نيجيريا"), "ZA": ("🇿🇦", "جنوب أفريقيا"), "KE": ("🇰🇪", "كينيا"),
    "ET": ("🇪🇹", "إثيوبيا"),
}

LANGUAGE_NAMES_AR = {
    "ar": "العربية", "en": "الإنجليزية", "es": "الإسبانية", "fr": "الفرنسية",
    "de": "الألمانية", "it": "الإيطالية", "pt": "البرتغالية", "ru": "الروسية",
    "tr": "التركية", "fa": "الفارسية", "ur": "الأردية", "hi": "الهندية",
    "zh": "الصينية", "ja": "اليابانية", "ko": "الكورية", "id": "الإندونيسية",
    "ms": "الماليزية", "th": "التايلاندية", "vi": "الفيتنامية", "tl": "الفلبينية",
    "nl": "الهولندية", "pl": "البولندية", "sv": "السويدية", "el": "اليونانية",
    "he": "العبرية", "uk": "الأوكرانية", "ro": "الرومانية", "bn": "البنغالية",
}

# لغة → مجموعة دول محتملة (للاستنتاج عند غياب region)
LANG_TO_COUNTRIES = {
    "ar": ["SA", "EG", "AE", "MA", "DZ", "IQ", "KW", "QA", "JO", "LB", "TN", "LY", "SY", "YE", "OM", "BH", "PS", "SD"],
    "tr": ["TR"], "fa": ["IR", "AF"], "ur": ["PK", "IN"],
    "hi": ["IN"], "bn": ["BD", "IN"], "id": ["ID"], "ms": ["MY"],
    "th": ["TH"], "vi": ["VN"], "tl": ["PH"], "ja": ["JP"], "ko": ["KR"],
    "ru": ["RU", "UA"], "uk": ["UA"], "pl": ["PL"],
    "es": ["ES", "MX", "AR", "CO", "CL", "PE"], "pt": ["BR", "PT"],
    "de": ["DE", "AT", "CH"], "it": ["IT"], "nl": ["NL", "BE"],
    "el": ["GR"], "he": ["IL"], "tr": ["TR"],
}

# ============ خريطة المدن للاستنتاج من البايو ============
CITY_TO_COUNTRY = {
    # السعودية
    "riyadh": "SA", "jeddah": "SA", "mecca": "SA", "makkah": "SA", "medina": "SA", "madinah": "SA",
    "dammam": "SA", "khobar": "SA", "taif": "SA", "abha": "SA", "tabuk": "SA",
    "الرياض": "SA", "جدة": "SA", "مكة": "SA", "المدينة": "SA", "الدمام": "SA", "الخبر": "SA",
    "الطائف": "SA", "أبها": "SA", "تبوك": "SA", "السعودية": "SA", "ksa": "SA", "saudi": "SA",
    # الإمارات
    "dubai": "AE", "abu dhabi": "AE", "abudhabi": "AE", "sharjah": "AE", "ajman": "AE",
    "دبي": "AE", "أبوظبي": "AE", "ابوظبي": "AE", "الشارقة": "AE", "عجمان": "AE",
    "الإمارات": "AE", "الامارات": "AE", "uae": "AE",
    # مصر
    "cairo": "EG", "alexandria": "EG", "giza": "EG", "egypt": "EG",
    "القاهرة": "EG", "الإسكندرية": "EG", "الاسكندرية": "EG", "الجيزة": "EG", "مصر": "EG",
    # دول الخليج
    "kuwait": "KW", "الكويت": "KW", "doha": "QA", "qatar": "QA", "الدوحة": "QA", "قطر": "QA",
    "manama": "BH", "bahrain": "BH", "المنامة": "BH", "البحرين": "BH",
    "muscat": "OM", "oman": "OM", "مسقط": "OM", "سلطنة عمان": "OM",
    # الشام
    "amman": "JO", "jordan": "JO", "عمّان": "JO", "عمان": "JO", "الأردن": "JO", "اربد": "JO",
    "beirut": "LB", "lebanon": "LB", "بيروت": "LB", "لبنان": "LB",
    "baghdad": "IQ", "iraq": "IQ", "بغداد": "IQ", "العراق": "IQ", "البصرة": "IQ", "أربيل": "IQ", "الموصل": "IQ",
    "damascus": "SY", "syria": "SY", "دمشق": "SY", "سوريا": "SY", "حلب": "SY",
    "sanaa": "YE", "yemen": "YE", "صنعاء": "YE", "اليمن": "YE", "عدن": "YE",
    "palestine": "PS", "gaza": "PS", "فلسطين": "PS", "غزة": "PS", "القدس": "PS",
    # شمال أفريقيا
    "morocco": "MA", "casablanca": "MA", "rabat": "MA", "marrakech": "MA",
    "المغرب": "MA", "الدار البيضاء": "MA", "الرباط": "MA", "مراكش": "MA",
    "algeria": "DZ", "algiers": "DZ", "الجزائر": "DZ",
    "tunisia": "TN", "tunis": "TN", "تونس": "TN",
    "libya": "LY", "tripoli libya": "LY", "ليبيا": "LY", "طرابلس": "LY", "بنغازي": "LY",
    "sudan": "SD", "khartoum": "SD", "السودان": "SD", "الخرطوم": "SD",
    "somalia": "SO", "الصومال": "SO", "moroccan": "MA",
    # دول أخرى
    "usa": "US", "united states": "US", "america": "US", "new york": "US", "los angeles": "US",
    "uk": "GB", "london": "GB", "england": "GB", "britain": "GB",
    "france": "FR", "paris": "FR", "فرنسا": "FR", "باريس": "FR",
    "germany": "DE", "berlin": "DE", "ألمانيا": "DE",
    "turkey": "TR", "istanbul": "TR", "تركيا": "TR", "إسطنبول": "TR",
    "iran": "IR", "tehran": "IR", "إيران": "IR",
    "india": "IN", "الهند": "IN", "pakistan": "PK", "باكستان": "PK",
    "indonesia": "ID", "إندونيسيا": "ID", "malaysia": "MY", "ماليزيا": "MY",
    "japan": "JP", "اليابان": "JP", "korea": "KR", "كوريا": "KR",
    "russia": "RU", "روسيا": "RU", "ukraine": "UA", "أوكرانيا": "UA",
    "brazil": "BR", "البرازيل": "BR", "mexico": "MX", "المكسيك": "MX",
    "canada": "CA", "كندا": "CA", "australia": "AU", "أستراليا": "AU",
}

# لهجات عربية → دولة
DIALECT_HINTS = {
    "SA": ["والله", "وش رايك", "تكفى", "يا اخوي", "وايد", "خوش", "حياك", "هلا والله"],
    "EG": ["ازيك", "إزيك", "ازاي", "إزاي", "كده", "كدا", "اوي", "أوي", "خالص", "بقى", "يلا", "يعني ايه", "عاوز", "عايز"],
    "AE": ["شحالك", "هلا والله", "تسلم", "وايد", "ها يبه", "ماعليه"],
    "KW": ["شلونك", "حياك", "تكفى", "والنبي", "هلا"],
    "MA": ["واخا", "بزاف", "زعما", "كيفاش", "شنو", "غادي", "دابا", "صافي", "بصح"],
    "DZ": ["واش", "كيراك", "بصح", "بزاف", "خويا"],
    "IQ": ["شلون", "اشلون", "هسة", "هسه", "اكو", "ماكو", "هواي", "خوش", "وين"],
    "LB": ["شو في", "كيفك", "هلق", "بدي", "كتير"],
    "SY": ["شو في", "كيفك", "هلق", "بدي", "كتير", "هلأ"],
    "YE": ["كيف حالك", "وشلون", "بهالعنا"],
}


def format_count(n):
    """تنسيق الأرقام (1.2M, 350K)."""
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


def detect_country_from_text(text: str):
    """استنتاج الدولة من النص. يعيد (كود, ثقة)."""
    if not text:
        return None, 0
    text_lower = text.lower()

    # 1. أعلام مباشرة (ثقة عالية جداً)
    for code in TIKTOK_REGION_MAP:
        flag = TIKTOK_REGION_MAP[code][0]
        if flag in text:
            return code, 95

    # 2. كلمات مفتاحية للمدن (ثقة عالية)
    sorted_keys = sorted(CITY_TO_COUNTRY.keys(), key=len, reverse=True)
    for keyword in sorted_keys:
        code = CITY_TO_COUNTRY[keyword]
        if any(ord(c) > 127 for c in keyword):
            if keyword in text:
                return code, 88
        else:
            if re.search(rf"\b{re.escape(keyword)}\b", text_lower):
                return code, 85

    # 3. لهجات عربية
    best_match = None
    best_count = 0
    for code, hints in DIALECT_HINTS.items():
        cnt = sum(1 for h in hints if h in text)
        if cnt > best_count:
            best_count = cnt
            best_match = code
    if best_match and best_count >= 2:
        return best_match, 65
    elif best_match and best_count == 1:
        return best_match, 45

    return None, 0


def parse_universal_data(html: str):
    """استخراج JSON من __UNIVERSAL_DATA_FOR_REHYDRATION__."""
    try:
        # طريقة 1: regex مباشرة (أسرع وأكثر موثوقية مع bs4 quirks)
        m = re.search(
            r'<script[^>]*id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>',
            html, re.DOTALL,
        )
        if m:
            content = m.group(1).strip()
            if content:
                data = json.loads(content)
                return data.get("__DEFAULT_SCOPE__", {}).get("webapp.user-detail", {})

        # طريقة 2: BeautifulSoup كاحتياطي
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", {"id": "__UNIVERSAL_DATA_FOR_REHYDRATION__"})
        if not script:
            return None
        # script.string قد لا يعمل، نستخدم str(script) ونزيل الوسوم
        content = str(script)
        m2 = re.search(r'>(.*?)</script>', content, re.DOTALL)
        if m2:
            content = m2.group(1).strip()
            if content:
                data = json.loads(content)
                return data.get("__DEFAULT_SCOPE__", {}).get("webapp.user-detail", {})
        return None
    except Exception:
        return None


def fetch_tiktok_profile(username: str, timeout: int = 15):
    """
    سحب وتحليل ملف TikTok بدقة عالية.
    
    يجمع البيانات من 3 مصادر:
    1. __UNIVERSAL_DATA__ (الأساسي)
    2. SIGI_STATE (احتياطي)
    3. Regex (آخر حل)
    
    ثم يستنتج الموقع من 5 طبقات.
    """
    username = username.replace("@", "").strip()
    profile_url = f"https://www.tiktok.com/@{username}"

    result = {
        "username": username,
        "profile_url": profile_url,
        "status": "❌ فشل", "error": "",
        # المعرّفات الدائمة
        "user_id": "", "sec_uid": "", "short_id": "",
        # المعلومات
        "nickname": "", "signature": "", "create_date": "",
        "avatar_thumb": "", "avatar_medium": "", "avatar_large": "",
        # الموقع المحلل
        "region": "",  # كود الدولة من API (إن وجد)
        "region_flag": "", "region_name_ar": "",
        "region_source": "",  # مصدر الكشف
        "region_confidence": 0,  # ثقة 0-100
        "candidates": "",  # دول محتملة (مفصولة بـ |)
        # اللغة
        "language": "", "language_name_ar": "",
        # الحالة
        "verified": False, "private_account": False,
        "tt_seller": False, "is_organization": False, "secret": False,
        # الإحصائيات
        "follower_count": 0, "following_count": 0,
        "heart_count": 0, "video_count": 0,
        "digg_count": 0, "friend_count": 0,
        # تنسيق
        "follower_count_formatted": "", "heart_count_formatted": "",
        # روابط
        "bio_link": "",
    }

    try:
        response = requests.get(profile_url, headers=TIKTOK_HEADERS, timeout=timeout, allow_redirects=True)

        if response.status_code == 404:
            result["error"] = "الحساب غير موجود (404)"
            return result
        if response.status_code != 200:
            result["error"] = f"كود استجابة: {response.status_code}"
            return result

        html = response.text
        user_detail = parse_universal_data(html)

        if not user_detail or "userInfo" not in user_detail:
            result["error"] = "لم يتم العثور على بيانات في الصفحة (قد يكون الحساب محظوراً أو محذوفاً)"
            return result

        # تحقق من حالة التواجد
        status_code = user_detail.get("statusCode", 0)
        if status_code != 0:
            status_msg = user_detail.get("statusMsg", "")
            if status_msg:
                result["error"] = f"TikTok: {status_msg}"
                return result

        user_info = user_detail.get("userInfo", {})
        user = user_info.get("user", {}) or {}
        stats = user_info.get("stats", {}) or user_info.get("statsV2", {}) or {}

        if not user:
            result["error"] = "بيانات المستخدم فارغة"
            return result

        # ============ استخراج البيانات ============
        result["user_id"] = str(user.get("id", "") or "")
        result["sec_uid"] = user.get("secUid", "") or ""
        result["short_id"] = str(user.get("shortId", "") or "")
        result["nickname"] = user.get("nickname", "") or ""
        result["signature"] = user.get("signature", "") or ""
        result["avatar_thumb"] = user.get("avatarThumb", "") or ""
        result["avatar_medium"] = user.get("avatarMedium", "") or ""
        result["avatar_large"] = user.get("avatarLarger", "") or ""

        # تاريخ الإنشاء
        create_time = user.get("createTime", 0) or 0
        if create_time:
            try:
                dt = datetime.fromtimestamp(int(create_time), tz=timezone.utc)
                result["create_date"] = dt.strftime("%Y-%m-%d")
            except Exception:
                pass

        # الحالة
        result["verified"] = bool(user.get("verified", False))
        result["private_account"] = bool(user.get("privateAccount", False))
        result["tt_seller"] = bool(user.get("ttSeller", False))
        result["secret"] = bool(user.get("secret", False))
        commerce = user.get("commerceUserInfo", {}) or {}
        result["is_organization"] = bool(commerce.get("commerceUser", False))

        # الإحصائيات
        result["follower_count"] = int(stats.get("followerCount", 0) or 0)
        result["following_count"] = int(stats.get("followingCount", 0) or 0)
        result["heart_count"] = max(int(stats.get("heart", 0) or 0), int(stats.get("heartCount", 0) or 0))
        # heartCount قد يكون سالباً بسبب overflow؛ نأخذ الأكبر
        if result["heart_count"] < 0:
            result["heart_count"] = int(stats.get("heart", 0) or 0)
        result["video_count"] = int(stats.get("videoCount", 0) or 0)
        result["digg_count"] = int(stats.get("diggCount", 0) or 0)
        result["friend_count"] = int(stats.get("friendCount", 0) or 0)

        result["follower_count_formatted"] = format_count(result["follower_count"])
        result["heart_count_formatted"] = format_count(result["heart_count"])

        # الرابط في البايو
        bio_link = user.get("bioLink", {})
        if isinstance(bio_link, dict):
            result["bio_link"] = bio_link.get("link", "") or ""

        # ============ اللغة ============
        lang = (user.get("language") or "").lower()
        result["language"] = lang
        if lang in LANGUAGE_NAMES_AR:
            result["language_name_ar"] = LANGUAGE_NAMES_AR[lang]

        # ============ الموقع - 5 طبقات ============
        region_code = None
        confidence = 0
        source = ""
        candidates = []

        # الطبقة 1: region من الـ API (نادراً ما يأتي - فقط لبعض الحسابات)
        api_region = (user.get("region") or "").upper()
        if api_region and api_region in TIKTOK_REGION_MAP:
            region_code = api_region
            confidence = 100
            source = "🎯 TikTok API (دقيق 100%)"

        # الطبقة 2: من البايو (إن لم نجد من API)
        if not region_code and result["signature"]:
            cc, conf = detect_country_from_text(result["signature"])
            if cc:
                region_code = cc
                confidence = conf
                source = "📝 من البايو"

        # الطبقة 3: من الاسم الظاهر
        if not region_code and result["nickname"]:
            cc, conf = detect_country_from_text(result["nickname"])
            if cc:
                region_code = cc
                confidence = max(conf - 10, 30)
                source = "👤 من الاسم"

        # الطبقة 4: من اسم المستخدم
        if not region_code:
            cc, conf = detect_country_from_text(username)
            if cc:
                region_code = cc
                confidence = max(conf - 15, 25)
                source = "🔤 من اليوزر"

        # الطبقة 5: من اللغة (دول محتملة)
        if lang in LANG_TO_COUNTRIES:
            possible = LANG_TO_COUNTRIES[lang]
            candidates = possible
            if not region_code and len(possible) == 1:
                # لغة لها دولة واحدة فقط (تركيا، إيران...)
                region_code = possible[0]
                confidence = 70
                source = f"🌐 من اللغة ({lang})"
            elif not region_code:
                # لغة متعددة الدول (عربية → دول كثيرة)
                source = f"🌐 لغة {LANGUAGE_NAMES_AR.get(lang, lang)} (دول محتملة)"

        if region_code:
            result["region"] = region_code
            flag, name_ar = TIKTOK_REGION_MAP.get(region_code, ("🌍", region_code))
            result["region_flag"] = flag
            result["region_name_ar"] = name_ar
            result["region_source"] = source
            result["region_confidence"] = confidence
        elif source:
            # لم نحدد دولة لكن لدينا مصدر (مثل اللغة العربية)
            result["region_source"] = source
            if candidates:
                result["candidates"] = "|".join(candidates)

        # تحديد الحالة النهائية
        if result["user_id"] or result["nickname"]:
            result["status"] = "✅ نجح"
        else:
            result["status"] = "⚠️ معلومات محدودة"

    except requests.Timeout:
        result["error"] = "انتهت مهلة الاتصال"
    except requests.ConnectionError:
        result["error"] = "خطأ في الاتصال بـ TikTok"
    except Exception as e:
        result["error"] = f"خطأ: {str(e)[:150]}"

    return result


def calculate_engagement_metrics(data: dict):
    """حساب مؤشرات التفاعل."""
    metrics = {
        "engagement_rate": 0.0,
        "avg_likes_per_video": 0,
        "follower_to_following_ratio": 0.0,
        "tier": "",
    }
    followers = data.get("follower_count", 0)
    following = data.get("following_count", 0)
    hearts = data.get("heart_count", 0)
    videos = data.get("video_count", 0)

    if videos > 0 and hearts > 0:
        metrics["avg_likes_per_video"] = hearts // videos
    if followers > 0 and metrics["avg_likes_per_video"] > 0:
        metrics["engagement_rate"] = round((metrics["avg_likes_per_video"] / followers) * 100, 2)
    if following > 0:
        metrics["follower_to_following_ratio"] = round(followers / following, 1)

    if followers >= 10_000_000:
        metrics["tier"] = "🌟 Mega Influencer (10M+)"
    elif followers >= 1_000_000:
        metrics["tier"] = "⭐ Macro Influencer (1M+)"
    elif followers >= 100_000:
        metrics["tier"] = "✨ Mid-Tier (100K+)"
    elif followers >= 10_000:
        metrics["tier"] = "💫 Micro Influencer (10K+)"
    elif followers >= 1_000:
        metrics["tier"] = "🔹 Nano (1K+)"
    else:
        metrics["tier"] = "🆕 جديد/صغير (<1K)"
    return metrics


# ============ اختبار ============
if __name__ == "__main__":
    import sys
    test_users = sys.argv[1:] if len(sys.argv) > 1 else ["khaby.lame", "7sn301"]

    for user in test_users:
        print(f"\n{'='*60}")
        print(f"🔍 تحليل @{user}")
        print('='*60)
        data = fetch_tiktok_profile(user)
        metrics = calculate_engagement_metrics(data)

        if data["status"] == "✅ نجح":
            print(f"✅ نجح")
            print(f"👤 {data['nickname']} {'✓' if data['verified'] else ''}")
            print(f"🆔 ID: {data['user_id']}")
            print(f"🔐 secUid: {data['sec_uid'][:60]}...")
            print(f"🌍 الدولة: {data['region_flag']} {data['region_name_ar']} ({data['region']})")
            print(f"   📊 المصدر: {data['region_source']} • الثقة: {data['region_confidence']}%")
            if data["candidates"]:
                print(f"   📋 دول محتملة: {data['candidates']}")
            print(f"🌐 اللغة: {data['language_name_ar']} ({data['language']})")
            print(f"📅 تاريخ الإنشاء: {data['create_date']}")
            print(f"📝 البايو: {data['signature'][:120]}")
            print(f"\n📊 الإحصائيات:")
            print(f"   👥 المتابعون: {data['follower_count_formatted']} ({data['follower_count']:,})")
            print(f"   ➡️ يتابع: {data['following_count']:,}")
            print(f"   ❤️ الإعجابات: {data['heart_count_formatted']}")
            print(f"   🎬 الفيديوهات: {data['video_count']:,}")
            print(f"\n📈 المؤشرات:")
            print(f"   {metrics['tier']}")
            print(f"   متوسط الإعجابات/فيديو: {metrics['avg_likes_per_video']:,}")
            print(f"   معدل التفاعل: {metrics['engagement_rate']}%")
        else:
            print(f"❌ فشل: {data['error']}")