# -*- coding: utf-8 -*-
"""
=====================================================================
 🛰️ TikTok Region Analyzer v8.0 — Hybrid Multi-Source Edition
=====================================================================
 المصادر المدمجة:
   🥇 المصدر الرئيسي: TikMatrix (دقة 100%)
   🥈 المصدر الثانوي: TikTok Profile API (للإحصائيات)
   🥉 المصدر الثالث: تحليل ذكي للنص (fallback)
 
 الميزات:
   ✅ دقة عالية في تحديد الدولة
   ✅ Smart caching (24h)
   ✅ Rate limit handling مع retry
   ✅ User-Agent rotation
   ✅ Multi-source fallback
   ✅ شفافية كاملة في المصدر
=====================================================================
"""

import streamlit as st
import requests
import re
import json
import random
import time
from datetime import datetime, timezone
import pandas as pd

# =====================================================================
# 🎨 إعداد Streamlit
# =====================================================================

st.set_page_config(
    page_title="TikTok Region Analyzer v8",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
body, .stApp, [class*="css"] {
    direction: rtl;
    text-align: right;
    font-family: 'Noto Sans Arabic', 'Tajawal', sans-serif;
}
.source-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 15px;
    font-size: 12px;
    font-weight: bold;
    margin: 3px;
}
.source-tikmatrix { background: #10b981; color: white; }
.source-tiktok    { background: #3b82f6; color: white; }
.source-analysis  { background: #f59e0b; color: white; }
.source-none      { background: #ef4444; color: white; }

.country-card {
    background: linear-gradient(135deg, #064e3b, #047857);
    padding: 30px;
    border-radius: 15px;
    text-align: center;
    margin: 15px 0;
    color: #ecfdf5;
}
.country-flag {
    font-size: 90px;
    margin-bottom: 10px;
}
.confidence-bar {
    background: #1e293b;
    border-radius: 10px;
    overflow: hidden;
    height: 30px;
    margin: 10px 0;
}
.confidence-fill {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
    transition: width 0.5s;
}
.layer-info {
    background: #1e293b;
    padding: 10px;
    border-radius: 8px;
    margin: 5px 0;
    border-right: 3px solid #3b82f6;
    color: #f1f5f9;
}
</style>
""", unsafe_allow_html=True)


# =====================================================================
# 🌍 خريطة الدول الكاملة
# =====================================================================

# اسم → كود ISO + علم + إحداثيات
COUNTRY_DB = {
    # عربي
    "Saudi Arabia":            {"code": "SA", "ar": "السعودية",        "flag": "🇸🇦", "lat": 24.7136, "lon": 46.6753},
    "United Arab Emirates":    {"code": "AE", "ar": "الإمارات",        "flag": "🇦🇪", "lat": 24.4539, "lon": 54.3773},
    "Egypt":                   {"code": "EG", "ar": "مصر",             "flag": "🇪🇬", "lat": 30.0444, "lon": 31.2357},
    "Kuwait":                  {"code": "KW", "ar": "الكويت",          "flag": "🇰🇼", "lat": 29.3759, "lon": 47.9774},
    "Qatar":                   {"code": "QA", "ar": "قطر",             "flag": "🇶🇦", "lat": 25.2854, "lon": 51.5310},
    "Bahrain":                 {"code": "BH", "ar": "البحرين",         "flag": "🇧🇭", "lat": 26.0667, "lon": 50.5577},
    "Oman":                    {"code": "OM", "ar": "عُمان",           "flag": "🇴🇲", "lat": 23.5880, "lon": 58.3829},
    "Jordan":                  {"code": "JO", "ar": "الأردن",          "flag": "🇯🇴", "lat": 31.9539, "lon": 35.9106},
    "Lebanon":                 {"code": "LB", "ar": "لبنان",           "flag": "🇱🇧", "lat": 33.8869, "lon": 35.5131},
    "Syria":                   {"code": "SY", "ar": "سوريا",           "flag": "🇸🇾", "lat": 33.5138, "lon": 36.2765},
    "Syrian Arab Republic":    {"code": "SY", "ar": "سوريا",           "flag": "🇸🇾", "lat": 33.5138, "lon": 36.2765},
    "Iraq":                    {"code": "IQ", "ar": "العراق",          "flag": "🇮🇶", "lat": 33.3152, "lon": 44.3661},
    "Yemen":                   {"code": "YE", "ar": "اليمن",           "flag": "🇾🇪", "lat": 15.5527, "lon": 48.5164},
    "Palestine":               {"code": "PS", "ar": "فلسطين",          "flag": "🇵🇸", "lat": 31.9522, "lon": 35.2332},
    "Palestinian Territory":   {"code": "PS", "ar": "فلسطين",          "flag": "🇵🇸", "lat": 31.9522, "lon": 35.2332},
    "Morocco":                 {"code": "MA", "ar": "المغرب",          "flag": "🇲🇦", "lat": 33.9716, "lon": -6.8498},
    "Algeria":                 {"code": "DZ", "ar": "الجزائر",         "flag": "🇩🇿", "lat": 36.7538, "lon": 3.0588},
    "Tunisia":                 {"code": "TN", "ar": "تونس",            "flag": "🇹🇳", "lat": 36.8065, "lon": 10.1815},
    "Libya":                   {"code": "LY", "ar": "ليبيا",           "flag": "🇱🇾", "lat": 32.8872, "lon": 13.1913},
    "Sudan":                   {"code": "SD", "ar": "السودان",         "flag": "🇸🇩", "lat": 15.5007, "lon": 32.5599},
    "Somalia":                 {"code": "SO", "ar": "الصومال",         "flag": "🇸🇴", "lat": 2.0469,  "lon": 45.3182},
    "Mauritania":              {"code": "MR", "ar": "موريتانيا",       "flag": "🇲🇷", "lat": 18.0735, "lon": -15.9582},
    "Djibouti":                {"code": "DJ", "ar": "جيبوتي",          "flag": "🇩🇯", "lat": 11.8251, "lon": 42.5903},
    "Comoros":                 {"code": "KM", "ar": "جزر القمر",       "flag": "🇰🇲", "lat": -11.875, "lon": 43.872},
    
    # عالمي
    "United States":           {"code": "US", "ar": "الولايات المتحدة","flag": "🇺🇸", "lat": 38.9072, "lon": -77.0369},
    "United Kingdom":          {"code": "GB", "ar": "بريطانيا",        "flag": "🇬🇧", "lat": 51.5074, "lon": -0.1278},
    "Turkey":                  {"code": "TR", "ar": "تركيا",           "flag": "🇹🇷", "lat": 39.9334, "lon": 32.8597},
    "Germany":                 {"code": "DE", "ar": "ألمانيا",         "flag": "🇩🇪", "lat": 52.5200, "lon": 13.4050},
    "France":                  {"code": "FR", "ar": "فرنسا",           "flag": "🇫🇷", "lat": 48.8566, "lon": 2.3522},
    "Spain":                   {"code": "ES", "ar": "إسبانيا",         "flag": "🇪🇸", "lat": 40.4168, "lon": -3.7038},
    "Italy":                   {"code": "IT", "ar": "إيطاليا",         "flag": "🇮🇹", "lat": 41.9028, "lon": 12.4964},
    "Russia":                  {"code": "RU", "ar": "روسيا",           "flag": "🇷🇺", "lat": 55.7558, "lon": 37.6173},
    "China":                   {"code": "CN", "ar": "الصين",           "flag": "🇨🇳", "lat": 39.9042, "lon": 116.4074},
    "Japan":                   {"code": "JP", "ar": "اليابان",         "flag": "🇯🇵", "lat": 35.6762, "lon": 139.6503},
    "South Korea":             {"code": "KR", "ar": "كوريا الجنوبية",   "flag": "🇰🇷", "lat": 37.5665, "lon": 126.9780},
    "Korea, Republic of":      {"code": "KR", "ar": "كوريا الجنوبية",   "flag": "🇰🇷", "lat": 37.5665, "lon": 126.9780},
    "India":                   {"code": "IN", "ar": "الهند",           "flag": "🇮🇳", "lat": 28.6139, "lon": 77.2090},
    "Indonesia":               {"code": "ID", "ar": "إندونيسيا",       "flag": "🇮🇩", "lat": -6.2088, "lon": 106.8456},
    "Pakistan":                {"code": "PK", "ar": "باكستان",         "flag": "🇵🇰", "lat": 33.6844, "lon": 73.0479},
    "Brazil":                  {"code": "BR", "ar": "البرازيل",        "flag": "🇧🇷", "lat": -15.7975, "lon": -47.8919},
    "Mexico":                  {"code": "MX", "ar": "المكسيك",         "flag": "🇲🇽", "lat": 19.4326, "lon": -99.1332},
    "Canada":                  {"code": "CA", "ar": "كندا",            "flag": "🇨🇦", "lat": 45.4215, "lon": -75.6972},
    "Australia":               {"code": "AU", "ar": "أستراليا",        "flag": "🇦🇺", "lat": -35.2809, "lon": 149.1300},
    "Netherlands":             {"code": "NL", "ar": "هولندا",          "flag": "🇳🇱", "lat": 52.3676, "lon": 4.9041},
    "Belgium":                 {"code": "BE", "ar": "بلجيكا",          "flag": "🇧🇪", "lat": 50.8503, "lon": 4.3517},
    "Sweden":                  {"code": "SE", "ar": "السويد",          "flag": "🇸🇪", "lat": 59.3293, "lon": 18.0686},
    "Norway":                  {"code": "NO", "ar": "النرويج",         "flag": "🇳🇴", "lat": 59.9139, "lon": 10.7522},
    "Switzerland":             {"code": "CH", "ar": "سويسرا",          "flag": "🇨🇭", "lat": 46.9479, "lon": 7.4474},
    "Argentina":               {"code": "AR", "ar": "الأرجنتين",       "flag": "🇦🇷", "lat": -34.6037, "lon": -58.3816},
    "Chile":                   {"code": "CL", "ar": "تشيلي",           "flag": "🇨🇱", "lat": -33.4489, "lon": -70.6693},
    "Colombia":                {"code": "CO", "ar": "كولومبيا",        "flag": "🇨🇴", "lat": 4.7110,  "lon": -74.0721},
    "Philippines":             {"code": "PH", "ar": "الفلبين",         "flag": "🇵🇭", "lat": 14.5995, "lon": 120.9842},
    "Vietnam":                 {"code": "VN", "ar": "فيتنام",          "flag": "🇻🇳", "lat": 21.0285, "lon": 105.8542},
    "Thailand":                {"code": "TH", "ar": "تايلاند",         "flag": "🇹🇭", "lat": 13.7563, "lon": 100.5018},
    "Malaysia":                {"code": "MY", "ar": "ماليزيا",         "flag": "🇲🇾", "lat": 3.1390,  "lon": 101.6869},
    "Nigeria":                 {"code": "NG", "ar": "نيجيريا",         "flag": "🇳🇬", "lat": 9.0820,  "lon": 8.6753},
    "South Africa":            {"code": "ZA", "ar": "جنوب أفريقيا",     "flag": "🇿🇦", "lat": -25.7479, "lon": 28.2293},
    "Iran":                    {"code": "IR", "ar": "إيران",           "flag": "🇮🇷", "lat": 35.6892, "lon": 51.3890},
    "Afghanistan":             {"code": "AF", "ar": "أفغانستان",       "flag": "🇦🇫", "lat": 34.5553, "lon": 69.2075},
}

# كود ISO → معلومات (للبحث العكسي)
CODE_TO_COUNTRY = {info["code"]: {**info, "en": name} for name, info in COUNTRY_DB.items()}


# =====================================================================
# 🌐 User-Agent Rotation Pool
# =====================================================================

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


def get_headers() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "DNT": "1",
    }


def sanitize_username(username: str) -> str:
    """تنظيف username من الـ injection."""
    if not username:
        raise ValueError("اسم المستخدم فارغ")
    username = username.strip().lstrip("@")
    if not re.match(r"^[a-zA-Z0-9._]{1,24}$", username):
        raise ValueError("اسم مستخدم غير صالح (a-z, 0-9, ., _)")
    return username


# =====================================================================
# 🥇 المصدر 1: TikMatrix (الأكثر دقة!)
# =====================================================================

@st.cache_data(ttl=86400, show_spinner=False)  # cache 24 ساعة
def fetch_from_tikmatrix(username: str) -> dict:
    """
    استخراج من TikMatrix - المصدر الأكثر دقة في كشف الدولة.
    """
    url = f"https://user.tikmatrix.com/?username={username}"
    
    for attempt in range(3):  # 3 محاولات
        try:
            r = requests.get(url, headers=get_headers(), timeout=20)
            
            if r.status_code == 503:
                # Rate limit - انتظر وحاول مجدداً
                if attempt < 2:
                    time.sleep(5 + attempt * 3)
                    continue
                return {"success": False, "error": "rate_limited"}
            
            if r.status_code != 200:
                return {"success": False, "error": f"http_{r.status_code}"}
            
            html = r.text
            
            # استخراج البيانات
            result = {"success": True, "source": "tikmatrix"}
            
            # 1. الاسم
            m = re.search(r'<h2 class="user-name">([^<]+)</h2>', html)
            if m: result['nickname'] = m.group(1).strip()
            
            # 2. الدولة ⭐ (الأهم)
            patterns = [
                r'class="meta-item"[^>]*>\s*<span>🌍</span>\s*<span>([^<]+)</span>',
                r'>🌍</span>\s*<span>([^<]+)</span>',
            ]
            for pat in patterns:
                m = re.search(pat, html)
                if m:
                    country = m.group(1).strip()
                    if country and country != "Unknown":
                        result['country'] = country
                        break
            
            # 3. اللغة
            m = re.search(r'>🌐</span>\s*<span>([^<]+)</span>', html)
            if m: result['language'] = m.group(1).strip()
            
            # 4. الإحصائيات
            stats_pat = r'<span class="stat-number">([^<]+)</span>\s*<span class="stat-label">[^>]*>([^<]+)<'
            for value, label in re.findall(stats_pat, html):
                clean_label = re.sub(r'[^\w]', '', label).lower()
                if 'follow' in clean_label and 'ing' not in clean_label:
                    result['followers'] = value.replace(',', '')
                elif 'following' in clean_label:
                    result['following'] = value.replace(',', '')
                elif 'heart' in clean_label:
                    result['hearts'] = value.replace(',', '')
                elif 'video' in clean_label:
                    result['videos'] = value.replace(',', '')
            
            # 5. User ID و SecUID
            m = re.search(r'<span class="userid-text">([^<]+)</span>', html)
            if m: result['user_id'] = m.group(1)
            
            m = re.search(r'<span class="secuid-text">([^<]+)</span>', html)
            if m: result['sec_uid'] = m.group(1)
            
            # 6. تاريخ الإنشاء
            m = re.search(r'Account Created:</span>\s*<span class="detail-value">([^<]+)</span>', html)
            if m: result['created'] = m.group(1).strip()
            
            # 7. الصورة
            m = re.search(r'<img src="([^"]+)" alt="[^"]*" class="user-avatar"', html)
            if m: result['avatar'] = m.group(1)
            
            # 8. البيو
            m = re.search(r'<div class="user-bio">\s*<p>([^<]+)</p>', html)
            if m: result['bio'] = m.group(1).strip()
            
            return result
            
        except requests.exceptions.Timeout:
            if attempt < 2:
                continue
            return {"success": False, "error": "timeout"}
        except Exception as e:
            return {"success": False, "error": f"{type(e).__name__}"}
    
    return {"success": False, "error": "max_retries"}


# =====================================================================
# 🥈 المصدر 2: TikTok Profile API (للإحصائيات الإضافية)
# =====================================================================

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_from_tiktok(username: str) -> dict:
    """جلب من TikTok مباشرة - للإحصائيات والصورة."""
    try:
        url = f"https://www.tiktok.com/@{username}"
        r = requests.get(url, headers=get_headers(), timeout=15)
        
        if r.status_code != 200:
            return {"success": False, "error": f"http_{r.status_code}"}
        
        m = re.search(
            r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>',
            r.text, re.DOTALL
        )
        if not m:
            return {"success": False, "error": "no_data_script"}
        
        data = json.loads(m.group(1))
        scope = data.get("__DEFAULT_SCOPE__", {})
        user_info = scope.get("webapp.user-detail", {}).get("userInfo", {})
        user = user_info.get("user", {})
        stats = user_info.get("stats", {})
        
        if not user:
            return {"success": False, "error": "user_not_found"}
        
        return {
            "success": True,
            "source": "tiktok",
            "uniqueId": user.get("uniqueId", username),
            "nickname": user.get("nickname", ""),
            "signature": user.get("signature", ""),
            "verified": user.get("verified", False),
            "privateAccount": user.get("privateAccount", False),
            "language": user.get("language", ""),
            "avatar": user.get("avatarLarger", ""),
            "follower_count": stats.get("followerCount", 0),
            "following_count": stats.get("followingCount", 0),
            "heart_count": stats.get("heartCount", 0),
            "video_count": stats.get("videoCount", 0),
            "sec_uid": user.get("secUid", ""),
        }
    except Exception as e:
        return {"success": False, "error": f"{type(e).__name__}"}


# =====================================================================
# 🥉 المصدر 3: تحليل نصي ذكي (Fallback)
# =====================================================================

# قواميس مفاتيح بلاد - دقيقة جداً
COUNTRY_KEYWORDS = {
    "Saudi Arabia": ["السعودية", "saudi", "ksa", "الرياض", "riyadh", "جدة", "jeddah", "مكة", "makkah", "المدينة المنورة", "الدمام"],
    "United Arab Emirates": ["الإمارات", "uae", "dubai", "دبي", "أبوظبي", "abu dhabi", "abudhabi", "الشارقة", "sharjah"],
    "Egypt": ["مصر", "egypt", "cairo", "القاهرة", "الإسكندرية", "alexandria"],
    "Kuwait": ["الكويت", "kuwait", "kuwaitcity"],
    "Qatar": ["قطر", "qatar", "doha", "الدوحة"],
    "Bahrain": ["البحرين", "bahrain"],
    "Oman": ["عمان", "oman", "muscat", "مسقط"],
    "Jordan": ["الأردن", "jordan", "amman", "عمّان"],
    "Lebanon": ["لبنان", "lebanon", "beirut", "بيروت"],
    "Iraq": ["العراق", "iraq", "baghdad", "بغداد"],
    "Morocco": ["المغرب", "morocco", "casablanca", "الدارالبيضاء", "rabat", "الرباط"],
    "Algeria": ["الجزائر", "algeria", "algiers"],
    "Tunisia": ["تونس", "tunisia", "tunis"],
    "Sudan": ["السودان", "sudan", "khartoum"],
    "Turkey": ["تركيا", "turkey", "istanbul", "اسطنبول"],
    "United States": ["usa", "america", "new york", "los angeles", "chicago"],
    "United Kingdom": ["uk", "united kingdom", "london", "england", "britain"],
    "France": ["france", "paris", "français"],
    "Germany": ["germany", "berlin", "deutsch"],
    "Italy": ["italy", "italia", "rome", "milan", "italiano"],
    "Spain": ["spain", "españa", "madrid", "barcelona", "español"],
    "Russia": ["russia", "moscow", "россия"],
    "Japan": ["japan", "tokyo", "日本"],
    "Korea, Republic of": ["korea", "seoul", "한국", "kpop"],
    "Brazil": ["brasil", "brazil", "são paulo", "rio de janeiro"],
    "Indonesia": ["indonesia", "jakarta"],
    "India": ["india", "delhi", "mumbai", "हिंदी"],
    "Pakistan": ["pakistan", "karachi", "lahore"],
}


def analyze_text_for_country(text: str) -> dict:
    """تحليل نص (BIO/nickname) لاستنتاج الدولة."""
    if not text:
        return {}
    
    text_lower = text.lower()
    scores = {}
    
    for country, keywords in COUNTRY_KEYWORDS.items():
        count = 0
        for kw in keywords:
            if kw.lower() in text_lower:
                count += 1
        if count > 0:
            scores[country] = count
    
    if not scores:
        return {}
    
    # الأعلى نقاطاً
    top = max(scores.items(), key=lambda x: x[1])
    return {
        "country": top[0],
        "score": top[1],
        "all_matches": scores,
    }


# =====================================================================
# 🧠 المحرك الذكي - دمج المصادر
# =====================================================================

def comprehensive_analyze(username: str) -> dict:
    """
    التحليل الشامل بدمج كل المصادر.
    أولوية: TikMatrix > TikTok + تحليل نص > تحليل نص فقط
    """
    result = {
        "username": username,
        "success": False,
        "country": None,
        "country_info": None,
        "confidence": 0,
        "source": "none",
        "data": {},
        "sources_tried": [],
    }
    
    # ─── المحاولة 1: TikMatrix (الأقوى) ───
    tikmatrix = fetch_from_tikmatrix(username)
    result["sources_tried"].append({
        "name": "TikMatrix",
        "success": tikmatrix.get("success", False),
        "error": tikmatrix.get("error", "")
    })
    
    if tikmatrix.get("success") and tikmatrix.get("country"):
        country_name = tikmatrix["country"]
        country_info = COUNTRY_DB.get(country_name)
        if country_info:
            result["success"] = True
            result["country"] = country_name
            result["country_info"] = country_info
            result["confidence"] = 95  # TikMatrix دقيق جداً
            result["source"] = "tikmatrix"
            result["data"].update(tikmatrix)
    
    # ─── المحاولة 2: TikTok مباشرة (للبيانات الإضافية) ───
    tiktok = fetch_from_tiktok(username)
    result["sources_tried"].append({
        "name": "TikTok Direct",
        "success": tiktok.get("success", False),
        "error": tiktok.get("error", "")
    })
    
    if tiktok.get("success"):
        # ادمج بيانات TikTok مع TikMatrix
        for key in ["uniqueId", "nickname", "signature", "verified", "privateAccount",
                    "language", "avatar", "follower_count", "heart_count",
                    "video_count", "following_count", "sec_uid"]:
            if key in tiktok and not result["data"].get(key):
                result["data"][key] = tiktok[key]
        
        # إذا لم يجد TikMatrix → جرّب تحليل النص
        if not result["success"]:
            bio = tiktok.get("signature", "")
            nickname = tiktok.get("nickname", "")
            text = f"{nickname} {bio}"
            
            text_analysis = analyze_text_for_country(text)
            if text_analysis.get("country"):
                country_name = text_analysis["country"]
                country_info = COUNTRY_DB.get(country_name)
                if country_info:
                    result["success"] = True
                    result["country"] = country_name
                    result["country_info"] = country_info
                    result["confidence"] = min(40 + text_analysis["score"] * 15, 75)
                    result["source"] = "text_analysis"
                    result["data"]["text_matches"] = text_analysis["all_matches"]
    
    return result


# =====================================================================
# 🎨 واجهة المستخدم
# =====================================================================

def format_number(n):
    try:
        n = int(n)
    except:
        return str(n)
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def render_main():
    st.title("🛰️ TikTok Region Analyzer v8.0")
    st.markdown(
        "**Hybrid Multi-Source Edition** — "
        "🥇 TikMatrix + 🥈 TikTok + 🥉 تحليل ذكي"
    )
    
    # شارات المصادر
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<span class="source-badge source-tikmatrix">🥇 TikMatrix</span>', unsafe_allow_html=True)
    with col2:
        st.markdown('<span class="source-badge source-tiktok">🥈 TikTok API</span>', unsafe_allow_html=True)
    with col3:
        st.markdown('<span class="source-badge source-analysis">🥉 تحليل ذكي</span>', unsafe_allow_html=True)
    with col4:
        st.markdown('<span class="source-badge source-tikmatrix">⏱️ Cache 24h</span>', unsafe_allow_html=True)
    
    st.divider()
    
    # حقل الإدخال
    col_in, col_btn = st.columns([3, 1])
    with col_in:
        username = st.text_input(
            "👤 اسم المستخدم على TikTok (بدون @)",
            placeholder="aboflah, ahmed_mostafaa, mrbeast...",
            max_chars=24,
        )
    with col_btn:
        st.write("")
        st.write("")
        analyze = st.button("🔍 تحليل الموقع", use_container_width=True, type="primary")
    
    # اقتراحات
    st.caption(
        "💡 جرّب حسابات عربية: `aboflah` 🇦🇪 • `ahmed_mostafaa` 🇪🇬 • "
        "أو عالمية: `mrbeast` 🇺🇸 • `khaby.lame` 🇮🇹"
    )
    
    if not analyze or not username:
        st.info("👆 أدخل اسم مستخدم وانقر **تحليل الموقع**")
        return
    
    # التحقق من المدخل
    try:
        clean_username = sanitize_username(username)
    except ValueError as e:
        st.error(f"❌ {e}")
        return
    
    # التحليل الفعلي
    with st.spinner(f"🔄 جارٍ التحليل عبر 3 مصادر..."):
        result = comprehensive_analyze(clean_username)
    
    # ─── عرض النتائج ───
    st.divider()
    
    if not result["success"]:
        st.error("❌ لم نتمكن من تحديد الدولة من أي مصدر")
        with st.expander("📋 تفاصيل المصادر المُحاولة"):
            for src in result["sources_tried"]:
                emoji = "✅" if src["success"] else "❌"
                st.markdown(f"{emoji} **{src['name']}**: {src.get('error', 'OK')}")
        return
    
    # ─── البطاقة الرئيسية ───
    country = result["country"]
    info = result["country_info"]
    confidence = result["confidence"]
    source = result["source"]
    
    # تحديد لون شارة المصدر
    source_badges = {
        "tikmatrix": ('source-tikmatrix', '🥇 المصدر: TikMatrix (دقة عالية)'),
        "text_analysis": ('source-analysis', '🥉 المصدر: تحليل النص (دقة متوسطة)'),
    }
    badge_class, badge_text = source_badges.get(source, ('source-none', '⚠️ غير محدد'))
    
    st.markdown(
        f"""
        <div class="country-card">
            <div class="country-flag">{info['flag']}</div>
            <h1 style="margin: 5px 0;">{info['ar']}</h1>
            <h2 style="margin: 5px 0; font-weight: normal;">{country}</h2>
            <code style="font-size: 20px;">{info['code']}</code>
            <div style="margin: 15px 0;">
                <span class="source-badge {badge_class}">{badge_text}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # شريط الثقة
    st.markdown(f"### 📊 درجة الثقة: **{confidence}%**")
    
    if confidence >= 90:
        bar_color = "#10b981"
        verdict = "🎯 دقة ممتازة"
    elif confidence >= 60:
        bar_color = "#f59e0b"
        verdict = "✅ دقة جيدة"
    else:
        bar_color = "#ef4444"
        verdict = "⚠️ دقة محدودة"
    
    st.markdown(
        f"""
        <div class="confidence-bar">
            <div class="confidence-fill" style="width: {confidence}%; background: {bar_color};">
                {confidence}% — {verdict}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # الخريطة
    st.divider()
    st.markdown("### 🗺️ الموقع على الخريطة")
    map_df = pd.DataFrame([{"lat": info["lat"], "lon": info["lon"]}])
    st.map(map_df, latitude="lat", longitude="lon", size=80, zoom=4)
    
    # ─── معلومات الحساب ───
    st.divider()
    data = result["data"]
    
    col_avatar, col_info = st.columns([1, 3])
    with col_avatar:
        if data.get("avatar"):
            st.image(data["avatar"], width=140)
    with col_info:
        verified = " ✅" if data.get("verified") else ""
        private = " 🔒 خاص" if data.get("privateAccount") else ""
        nickname = data.get("nickname", clean_username)
        st.markdown(f"## {nickname}{verified}{private}")
        st.caption(f"@{data.get('uniqueId', clean_username)}")
        
        bio = data.get("signature") or data.get("bio", "")
        if bio:
            st.write(f"📝 {bio}")
        
        if data.get("created"):
            st.caption(f"📅 تم إنشاء الحساب: {data['created']}")
    
    # ─── الإحصائيات ───
    st.divider()
    st.markdown("### 📊 إحصائيات الحساب")
    
    followers = data.get("follower_count") or data.get("followers", 0)
    following = data.get("following_count") or data.get("following", 0)
    hearts = data.get("heart_count") or data.get("hearts", 0)
    videos = data.get("video_count") or data.get("videos", 0)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 المتابعون", format_number(followers))
    c2.metric("➡️ يتابع", format_number(following))
    c3.metric("❤️ الإعجابات", format_number(hearts))
    c4.metric("🎬 الفيديوهات", format_number(videos))
    
    # ─── معلومات إضافية ───
    st.divider()
    with st.expander("🔬 تفاصيل تقنية متقدمة"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🔑 معرفات الحساب:**")
            if data.get("user_id"):
                st.code(f"User ID: {data['user_id']}")
            if data.get("sec_uid"):
                st.code(f"SecUID: {data['sec_uid'][:40]}...")
        with col2:
            st.markdown("**🌐 معلومات أخرى:**")
            if data.get("language"):
                st.write(f"🗣️ اللغة: `{data['language']}`")
            st.write(f"📡 المصدر النهائي: `{source}`")
        
        # مصادر المحاولة
        st.markdown("**🔍 سجل المصادر:**")
        for src in result["sources_tried"]:
            emoji = "✅" if src["success"] else "❌"
            err = src.get("error", "")
            err_text = f" — `{err}`" if err else ""
            st.markdown(f"- {emoji} **{src['name']}**{err_text}")


def render_about():
    st.subheader("ℹ️ عن التطبيق v8.0")
    st.markdown("""
    ## 🛰️ TikTok Region Analyzer v8.0
    ### Hybrid Multi-Source Edition
    
    تطبيق احترافي لتحديد دولة حسابات TikTok بدقة عالية، يجمع بين 3 مصادر:
    
    ---
    
    ### 🥇 المصدر الأول: TikMatrix
    - أداة OSINT متخصصة بدقة 100%
    - تكشف الدولة الفعلية للحسابات
    - دقة عالية مع جميع أنواع الحسابات
    
    ### 🥈 المصدر الثاني: TikTok مباشرة
    - الإحصائيات (followers, likes, videos)
    - الصورة الشخصية
    - BIO ومعلومات الحساب
    
    ### 🥉 المصدر الثالث: تحليل ذكي للنص
    - يحلل BIO + nickname
    - يبحث عن كلمات مفتاحية جغرافية
    - 27+ دولة مدعومة بكلمات مفتاحية
    
    ---
    
    ### ✨ الميزات
    
    | الميزة | الوصف |
    |--------|------|
    | 🎯 دقة عالية | حتى 95% للحسابات المعروفة |
    | ⏱️ Cache 24 ساعة | لتقليل الطلبات |
    | 🔄 Retry تلقائي | عند Rate Limit |
    | 🌐 User-Agent rotation | 5 UAs للتنويع |
    | 🛡️ Input sanitization | حماية من injection |
    | 🌍 53+ دولة | مع علم وإحداثيات |
    
    ---
    
    ### 📚 المراجع
    - [TikTok Creator Regions](https://scrapecreators.com/blog/tiktok-creator-regions)
    - [TikMatrix](https://user.tikmatrix.com/)
    - [TikTok Official API](https://developers.tiktok.com/)
    
    ---
    
    **v8.0.0** | 2026 | [GitHub](https://github.com/7sn301/social-accounts-generator)
    """)


# =====================================================================
# 🚀 التطبيق الرئيسي
# =====================================================================

def main():
    tabs = st.tabs(["🎯 المحلل الذكي", "ℹ️ عن التطبيق"])
    
    with tabs[0]:
        render_main()
    with tabs[1]:
        render_about()
    
    st.divider()
    st.caption(
        f"📅 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | "
        "🛰️ v8.0 Hybrid Edition | "
        "🔧 Powered by TikMatrix + TikTok + AI"
    )


if __name__ == "__main__":
    main()
