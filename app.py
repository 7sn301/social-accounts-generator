# -*- coding: utf-8 -*-
"""
=====================================================================
 🦅 بَصِير v1.2 — Fixed Edition
=====================================================================
 الإصلاحات:
   ✅ حذف SVG المعقد (كان يكسر التصميم)
   ✅ استخدام emoji كبير مع CSS احترافي
   ✅ HTML مبسط ومضمون العمل
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
    page_title="🦅 بَصِير",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =====================================================================
# 🎨 CSS احترافي
# =====================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&family=Amiri:wght@400;700&family=JetBrains+Mono:wght@500;700&display=swap');

body, .stApp, [class*="css"] {
    direction: rtl;
    text-align: right;
    font-family: 'Cairo', sans-serif !important;
}

#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

.stApp {
    background: linear-gradient(135deg, #0A0E1A 0%, #0F172A 50%, #1E293B 100%);
}

/* 🦅 الصقر الكبير */
.baseer-falcon {
    font-size: 180px;
    line-height: 1;
    text-align: center;
    margin: 30px auto 10px auto;
    filter: drop-shadow(0 0 40px rgba(255,215,0,0.6));
    animation: floatFalcon 4s ease-in-out infinite;
    display: block;
}

@keyframes floatFalcon {
    0%, 100% { transform: translateY(0) rotate(-3deg); }
    50% { transform: translateY(-20px) rotate(3deg); }
}

/* 📝 اسم بَصِير */
.baseer-title {
    text-align: center;
    font-size: 120px;
    font-weight: 900;
    background: linear-gradient(135deg, #FFD700 0%, #F59E0B 50%, #FFD700 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 40px 0;
    letter-spacing: -3px;
    font-family: 'Amiri', 'Cairo', serif;
    line-height: 1;
    text-shadow: 0 0 60px rgba(255,215,0,0.4);
}

/* 🎯 صندوق البحث */
.search-section {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    padding: 30px;
    border-radius: 20px;
    border: 2px solid rgba(255,215,0,0.2);
    margin: 30px 0;
    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
}

.stTextInput input {
    font-size: 20px !important;
    padding: 15px 20px !important;
    height: 60px !important;
    border-radius: 15px !important;
    border: 2px solid rgba(255,215,0,0.3) !important;
    background: rgba(15,23,42,0.6) !important;
    color: #F1F5F9 !important;
    font-family: 'Cairo', sans-serif !important;
}

.stTextInput input:focus {
    border-color: #FFD700 !important;
    box-shadow: 0 0 0 4px rgba(255,215,0,0.2) !important;
}

.stButton button {
    font-size: 20px !important;
    padding: 15px 30px !important;
    height: 60px !important;
    border-radius: 15px !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, #FFD700 0%, #F59E0B 100%) !important;
    color: #0F172A !important;
    border: none !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(255,215,0,0.3) !important;
    font-family: 'Cairo', sans-serif !important;
}

.stButton button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 25px rgba(255,215,0,0.5) !important;
}

/* 🌍 بطاقة الدولة */
.country-card-premium {
    background: linear-gradient(135deg, #064E3B 0%, #047857 50%, #065F46 100%);
    padding: 50px 30px;
    border-radius: 25px;
    text-align: center;
    margin: 30px 0;
    color: #ECFDF5;
    box-shadow: 0 20px 60px rgba(16,185,129,0.3);
    border: 3px solid rgba(255,215,0,0.4);
}

.country-flag-huge {
    font-size: 160px;
    line-height: 1;
    margin-bottom: 20px;
    filter: drop-shadow(0 10px 30px rgba(0,0,0,0.3));
}

.country-name-ar {
    font-size: 56px;
    font-weight: 900;
    margin: 10px 0;
}

.country-name-en {
    font-size: 28px;
    font-weight: 400;
    color: rgba(236,253,245,0.8);
    margin-bottom: 15px;
}

.country-code-badge {
    display: inline-block;
    background: rgba(0,0,0,0.4);
    padding: 10px 25px;
    border-radius: 30px;
    font-size: 28px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    border: 2px solid rgba(255,215,0,0.5);
    color: #FFD700;
}

/* 📊 إحصائيات */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 20px;
    margin: 30px 0;
}

.stat-card-premium {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    padding: 25px 20px;
    border-radius: 18px;
    text-align: center;
    border: 2px solid rgba(255,215,0,0.15);
    transition: all 0.3s ease;
}

.stat-card-premium:hover {
    transform: translateY(-5px);
    border-color: #FFD700;
    box-shadow: 0 15px 40px rgba(255,215,0,0.2);
}

.stat-icon-big {
    font-size: 64px;
    margin-bottom: 10px;
    display: block;
}

.stat-value {
    font-size: 36px;
    font-weight: 900;
    color: #FFD700;
    font-family: 'JetBrains Mono', monospace;
    margin: 5px 0;
}

.stat-label {
    font-size: 16px;
    color: #94A3B8;
    font-weight: 600;
}

/* 🎯 شريط الثقة */
.confidence-container {
    background: #0F172A;
    padding: 20px;
    border-radius: 15px;
    margin: 20px 0;
    border: 1px solid rgba(255,215,0,0.2);
}

.confidence-label {
    font-size: 18px;
    color: #FFD700;
    margin-bottom: 12px;
    font-weight: 700;
}

.confidence-bar-bg {
    background: #1E293B;
    border-radius: 12px;
    overflow: hidden;
    height: 40px;
    border: 2px solid rgba(255,215,0,0.2);
}

.confidence-bar-fill {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #0F172A;
    font-weight: 900;
    font-size: 18px;
    background: linear-gradient(90deg, #10B981 0%, #FFD700 100%);
}

/* 🔍 شارات */
.badge-gold {
    display: inline-block;
    background: linear-gradient(135deg, #FFD700, #F59E0B);
    color: #0F172A;
    padding: 10px 20px;
    border-radius: 25px;
    font-weight: 700;
    font-size: 15px;
}

/* 🎨 Streamlit overrides */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    padding: 20px;
    border-radius: 15px;
    border: 2px solid rgba(255,215,0,0.15);
}

[data-testid="stMetricValue"] {
    font-size: 32px !important;
    color: #FFD700 !important;
    font-weight: 900 !important;
}

hr {
    border-color: rgba(255,215,0,0.2) !important;
    margin: 30px 0 !important;
}

.footer-area {
    text-align: center;
    padding: 30px;
    margin-top: 50px;
    color: #94A3B8;
}

.footer-logo {
    font-size: 50px;
}
</style>
""", unsafe_allow_html=True)


# =====================================================================
# 🌍 خريطة الدول
# =====================================================================

COUNTRY_DB = {
    "Saudi Arabia":            {"code": "SA", "ar": "المملكة العربية السعودية",     "flag": "🇸🇦", "lat": 24.7136, "lon": 46.6753},
    "United Arab Emirates":    {"code": "AE", "ar": "الإمارات العربية المتحدة",      "flag": "🇦🇪", "lat": 24.4539, "lon": 54.3773},
    "Egypt":                   {"code": "EG", "ar": "جمهورية مصر العربية",          "flag": "🇪🇬", "lat": 30.0444, "lon": 31.2357},
    "Kuwait":                  {"code": "KW", "ar": "دولة الكويت",                "flag": "🇰🇼", "lat": 29.3759, "lon": 47.9774},
    "Qatar":                   {"code": "QA", "ar": "دولة قطر",                  "flag": "🇶🇦", "lat": 25.2854, "lon": 51.5310},
    "Bahrain":                 {"code": "BH", "ar": "مملكة البحرين",              "flag": "🇧🇭", "lat": 26.0667, "lon": 50.5577},
    "Oman":                    {"code": "OM", "ar": "سلطنة عُمان",                "flag": "🇴🇲", "lat": 23.5880, "lon": 58.3829},
    "Jordan":                  {"code": "JO", "ar": "المملكة الأردنية الهاشمية",    "flag": "🇯🇴", "lat": 31.9539, "lon": 35.9106},
    "Lebanon":                 {"code": "LB", "ar": "الجمهورية اللبنانية",          "flag": "🇱🇧", "lat": 33.8869, "lon": 35.5131},
    "Syria":                   {"code": "SY", "ar": "الجمهورية العربية السورية",    "flag": "🇸🇾", "lat": 33.5138, "lon": 36.2765},
    "Iraq":                    {"code": "IQ", "ar": "جمهورية العراق",             "flag": "🇮🇶", "lat": 33.3152, "lon": 44.3661},
    "Yemen":                   {"code": "YE", "ar": "الجمهورية اليمنية",          "flag": "🇾🇪", "lat": 15.5527, "lon": 48.5164},
    "Palestine":               {"code": "PS", "ar": "دولة فلسطين",               "flag": "🇵🇸", "lat": 31.9522, "lon": 35.2332},
    "Morocco":                 {"code": "MA", "ar": "المملكة المغربية",            "flag": "🇲🇦", "lat": 33.9716, "lon": -6.8498},
    "Algeria":                 {"code": "DZ", "ar": "الجزائر",                  "flag": "🇩🇿", "lat": 36.7538, "lon": 3.0588},
    "Tunisia":                 {"code": "TN", "ar": "تونس",                    "flag": "🇹🇳", "lat": 36.8065, "lon": 10.1815},
    "Libya":                   {"code": "LY", "ar": "ليبيا",                   "flag": "🇱🇾", "lat": 32.8872, "lon": 13.1913},
    "Sudan":                   {"code": "SD", "ar": "السودان",                  "flag": "🇸🇩", "lat": 15.5007, "lon": 32.5599},
    "Somalia":                 {"code": "SO", "ar": "الصومال",                  "flag": "🇸🇴", "lat": 2.0469,  "lon": 45.3182},
    "United States":           {"code": "US", "ar": "الولايات المتحدة الأمريكية", "flag": "🇺🇸", "lat": 38.9072, "lon": -77.0369},
    "United Kingdom":          {"code": "GB", "ar": "المملكة المتحدة",            "flag": "🇬🇧", "lat": 51.5074, "lon": -0.1278},
    "Turkey":                  {"code": "TR", "ar": "تركيا",                   "flag": "🇹🇷", "lat": 39.9334, "lon": 32.8597},
    "Germany":                 {"code": "DE", "ar": "ألمانيا",                  "flag": "🇩🇪", "lat": 52.5200, "lon": 13.4050},
    "France":                  {"code": "FR", "ar": "فرنسا",                   "flag": "🇫🇷", "lat": 48.8566, "lon": 2.3522},
    "Spain":                   {"code": "ES", "ar": "إسبانيا",                  "flag": "🇪🇸", "lat": 40.4168, "lon": -3.7038},
    "Italy":                   {"code": "IT", "ar": "إيطاليا",                  "flag": "🇮🇹", "lat": 41.9028, "lon": 12.4964},
    "Russia":                  {"code": "RU", "ar": "روسيا",                   "flag": "🇷🇺", "lat": 55.7558, "lon": 37.6173},
    "Japan":                   {"code": "JP", "ar": "اليابان",                  "flag": "🇯🇵", "lat": 35.6762, "lon": 139.6503},
    "South Korea":             {"code": "KR", "ar": "كوريا الجنوبية",            "flag": "🇰🇷", "lat": 37.5665, "lon": 126.9780},
    "Korea, Republic of":      {"code": "KR", "ar": "كوريا الجنوبية",            "flag": "🇰🇷", "lat": 37.5665, "lon": 126.9780},
    "India":                   {"code": "IN", "ar": "الهند",                   "flag": "🇮🇳", "lat": 28.6139, "lon": 77.2090},
    "Indonesia":               {"code": "ID", "ar": "إندونيسيا",                "flag": "🇮🇩", "lat": -6.2088, "lon": 106.8456},
    "Pakistan":                {"code": "PK", "ar": "باكستان",                  "flag": "🇵🇰", "lat": 33.6844, "lon": 73.0479},
    "Brazil":                  {"code": "BR", "ar": "البرازيل",                 "flag": "🇧🇷", "lat": -15.7975, "lon": -47.8919},
    "Canada":                  {"code": "CA", "ar": "كندا",                    "flag": "🇨🇦", "lat": 45.4215, "lon": -75.6972},
    "Australia":               {"code": "AU", "ar": "أستراليا",                "flag": "🇦🇺", "lat": -35.2809, "lon": 149.1300},
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
]


def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "DNT": "1",
    }


def sanitize_username(username: str) -> str:
    if not username:
        raise ValueError("اسم المستخدم فارغ")
    username = username.strip().lstrip("@")
    if not re.match(r"^[a-zA-Z0-9._]{1,24}$", username):
        raise ValueError("اسم مستخدم غير صالح (a-z, 0-9, ., _)")
    return username


# =====================================================================
# 🥇 المصدر 1: TikMatrix
# =====================================================================

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_from_tikmatrix(username: str) -> dict:
    url = f"https://user.tikmatrix.com/?username={username}"
    
    for attempt in range(3):
        try:
            r = requests.get(url, headers=get_headers(), timeout=20)
            
            if r.status_code == 503:
                if attempt < 2:
                    time.sleep(5 + attempt * 3)
                    continue
                return {"success": False, "error": "rate_limited"}
            
            if r.status_code != 200:
                return {"success": False, "error": f"http_{r.status_code}"}
            
            html = r.text
            result = {"success": True, "source": "tikmatrix"}
            
            m = re.search(r'<h2 class="user-name">([^<]+)</h2>', html)
            if m: result['nickname'] = m.group(1).strip()
            
            for pat in [
                r'class="meta-item"[^>]*>\s*<span>🌍</span>\s*<span>([^<]+)</span>',
                r'>🌍</span>\s*<span>([^<]+)</span>',
            ]:
                m = re.search(pat, html)
                if m:
                    country = m.group(1).strip()
                    if country and country != "Unknown":
                        result['country'] = country
                        break
            
            m = re.search(r'>🌐</span>\s*<span>([^<]+)</span>', html)
            if m: result['language'] = m.group(1).strip()
            
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
            
            m = re.search(r'<span class="userid-text">([^<]+)</span>', html)
            if m: result['user_id'] = m.group(1)
            
            m = re.search(r'<span class="secuid-text">([^<]+)</span>', html)
            if m: result['sec_uid'] = m.group(1)
            
            m = re.search(r'Account Created:</span>\s*<span class="detail-value">([^<]+)</span>', html)
            if m: result['created'] = m.group(1).strip()
            
            m = re.search(r'<img src="([^"]+)" alt="[^"]*" class="user-avatar"', html)
            if m: result['avatar'] = m.group(1)
            
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
# 🥈 المصدر 2: TikTok مباشرة
# =====================================================================

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_from_tiktok(username: str) -> dict:
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
            return {"success": False, "error": "no_data"}
        
        data = json.loads(m.group(1))
        scope = data.get("__DEFAULT_SCOPE__", {})
        user_info = scope.get("webapp.user-detail", {}).get("userInfo", {})
        user = user_info.get("user", {})
        stats = user_info.get("stats", {})
        
        if not user:
            return {"success": False, "error": "no_user"}
        
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


COUNTRY_KEYWORDS = {
    "Saudi Arabia": ["السعودية", "saudi", "ksa", "الرياض", "riyadh", "جدة", "jeddah", "مكة", "makkah"],
    "United Arab Emirates": ["الإمارات", "uae", "dubai", "دبي", "أبوظبي", "abu dhabi"],
    "Egypt": ["مصر", "egypt", "cairo", "القاهرة"],
    "Kuwait": ["الكويت", "kuwait"],
    "Qatar": ["قطر", "qatar", "doha"],
    "Bahrain": ["البحرين", "bahrain"],
    "Oman": ["عمان", "oman", "muscat"],
    "Jordan": ["الأردن", "jordan", "amman"],
    "Lebanon": ["لبنان", "lebanon", "beirut"],
    "Iraq": ["العراق", "iraq", "baghdad"],
    "Morocco": ["المغرب", "morocco", "casablanca"],
    "Algeria": ["الجزائر", "algeria"],
    "Tunisia": ["تونس", "tunisia"],
    "Turkey": ["تركيا", "turkey", "istanbul"],
    "United States": ["usa", "america", "new york"],
    "United Kingdom": ["uk", "london", "england"],
}


def analyze_text(text: str) -> dict:
    if not text:
        return {}
    text_lower = text.lower()
    scores = {}
    for country, keywords in COUNTRY_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw.lower() in text_lower)
        if count > 0:
            scores[country] = count
    if not scores:
        return {}
    top = max(scores.items(), key=lambda x: x[1])
    return {"country": top[0], "score": top[1], "all": scores}


def analyze_account(username: str) -> dict:
    result = {
        "username": username,
        "success": False,
        "country": None,
        "country_info": None,
        "confidence": 0,
        "source": None,
        "data": {},
        "sources_log": [],
    }
    
    tm = fetch_from_tikmatrix(username)
    result["sources_log"].append({"name": "TikMatrix", "success": tm.get("success", False), "error": tm.get("error", "")})
    
    if tm.get("success") and tm.get("country"):
        info = COUNTRY_DB.get(tm["country"])
        if info:
            result.update({
                "success": True,
                "country": tm["country"],
                "country_info": info,
                "confidence": 95,
                "source": "tikmatrix",
            })
            result["data"].update(tm)
    
    tt = fetch_from_tiktok(username)
    result["sources_log"].append({"name": "TikTok API", "success": tt.get("success", False), "error": tt.get("error", "")})
    
    if tt.get("success"):
        for key in ["uniqueId", "nickname", "signature", "verified", "privateAccount",
                    "language", "avatar", "follower_count", "heart_count",
                    "video_count", "following_count", "sec_uid"]:
            if key in tt and not result["data"].get(key):
                result["data"][key] = tt[key]
        
        if not result["success"]:
            text = f"{tt.get('nickname', '')} {tt.get('signature', '')}"
            analysis = analyze_text(text)
            if analysis.get("country"):
                info = COUNTRY_DB.get(analysis["country"])
                if info:
                    result.update({
                        "success": True,
                        "country": analysis["country"],
                        "country_info": info,
                        "confidence": min(40 + analysis["score"] * 15, 75),
                        "source": "text_analysis",
                    })
    
    return result


# =====================================================================
# 🎨 المكونات
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
    return f"{n:,}"


# =====================================================================
# 🎯 الصفحة الرئيسية
# =====================================================================

def main():
    # ═══════════════════════════════════════════
    # 🦅 Hero — صقر + بَصِير
    # ═══════════════════════════════════════════
    st.markdown('<div class="baseer-falcon">🦅</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="baseer-title">بَصِير</h1>', unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════
    # 🔍 صندوق البحث
    # ═══════════════════════════════════════════
    col1, col2 = st.columns([3, 1])
    with col1:
        username = st.text_input(
            "username",
            placeholder="🔎 ادخل اسم المستخدم (مثال: aboflah)",
            max_chars=24,
            label_visibility="collapsed",
        )
    with col2:
        analyze = st.button("🦅 ابحث", use_container_width=True, type="primary")
    
    # ═══════════════════════════════════════════
    # 🚀 التحليل
    # ═══════════════════════════════════════════
    if not analyze:
        return
    
    if not username:
        st.error("⚠️ من فضلك أدخل اسم مستخدم")
        return
    
    try:
        clean = sanitize_username(username)
    except ValueError as e:
        st.error(f"❌ {e}")
        return
    
    with st.spinner("🦅 جارٍ التحليل..."):
        result = analyze_account(clean)
    
    st.divider()
    
    if not result["success"]:
        st.error("😔 لم نتمكن من تحديد الدولة لهذا الحساب")
        with st.expander("🔍 تفاصيل المحاولات"):
            for src in result["sources_log"]:
                emoji = "✅" if src["success"] else "❌"
                st.markdown(f"{emoji} **{src['name']}** — `{src.get('error') or 'OK'}`")
        return
    
    info = result["country_info"]
    
    # ═══════════════════════════════════════════
    # 🌍 بطاقة الدولة
    # ═══════════════════════════════════════════
    country_html = (
        '<div class="country-card-premium">'
        f'<div class="country-flag-huge">{info["flag"]}</div>'
        f'<div class="country-name-ar">{info["ar"]}</div>'
        f'<div class="country-name-en">{result["country"]}</div>'
        f'<div class="country-code-badge">{info["code"]}</div>'
        '</div>'
    )
    st.markdown(country_html, unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════
    # 📊 شريط الثقة
    # ═══════════════════════════════════════════
    confidence = result["confidence"]
    verdict = "🎯 دقة ممتازة" if confidence >= 90 else ("✅ دقة جيدة" if confidence >= 60 else "⚠️ دقة محدودة")
    
    conf_html = (
        '<div class="confidence-container">'
        f'<div class="confidence-label">📊 درجة الثقة: {confidence}% — {verdict}</div>'
        '<div class="confidence-bar-bg">'
        f'<div class="confidence-bar-fill" style="width: {confidence}%;">{confidence}%</div>'
        '</div></div>'
    )
    st.markdown(conf_html, unsafe_allow_html=True)
    
    # المصدر
    source_emoji = {"tikmatrix": "🥇", "text_analysis": "🥉"}.get(result["source"], "📡")
    source_name = {"tikmatrix": "TikMatrix", "text_analysis": "تحليل ذكي"}.get(result["source"], "غير محدد")
    st.markdown(f'<span class="badge-gold">{source_emoji} المصدر: {source_name}</span>', unsafe_allow_html=True)
    
    st.divider()
    
    # ═══════════════════════════════════════════
    # 👤 بطاقة الحساب
    # ═══════════════════════════════════════════
    data = result["data"]
    nickname = data.get("nickname", clean)
    handle = data.get("uniqueId", clean)
    bio = data.get("signature") or data.get("bio", "")
    avatar = data.get("avatar", "")
    verified = "✅" if data.get("verified") else ""
    private = "🔒" if data.get("privateAccount") else ""
    created = data.get("created", "")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if avatar:
            st.image(avatar, width=150)
    with col2:
        st.markdown(f"## {nickname} {verified} {private}")
        st.markdown(f"**@{handle}**")
        if bio:
            st.markdown(f"📝 {bio}")
        if created:
            st.caption(f"📅 تأسس الحساب: {created}")
    
    st.divider()
    
    # ═══════════════════════════════════════════
    # 📊 الإحصائيات
    # ═══════════════════════════════════════════
    followers = data.get("follower_count") or data.get("followers", 0)
    following = data.get("following_count") or data.get("following", 0)
    hearts = data.get("heart_count") or data.get("hearts", 0)
    videos = data.get("video_count") or data.get("videos", 0)
    
    st.markdown("### 📊 الإحصائيات")
    
    stats_html = (
        '<div class="stats-grid">'
        '<div class="stat-card-premium">'
        '<span class="stat-icon-big">👥</span>'
        f'<div class="stat-value">{format_number(followers)}</div>'
        '<div class="stat-label">المتابعون</div>'
        '</div>'
        '<div class="stat-card-premium">'
        '<span class="stat-icon-big">➡️</span>'
        f'<div class="stat-value">{format_number(following)}</div>'
        '<div class="stat-label">يتابع</div>'
        '</div>'
        '<div class="stat-card-premium">'
        '<span class="stat-icon-big">❤️</span>'
        f'<div class="stat-value">{format_number(hearts)}</div>'
        '<div class="stat-label">الإعجابات</div>'
        '</div>'
        '<div class="stat-card-premium">'
        '<span class="stat-icon-big">🎬</span>'
        f'<div class="stat-value">{format_number(videos)}</div>'
        '<div class="stat-label">الفيديوهات</div>'
        '</div>'
        '</div>'
    )
    st.markdown(stats_html, unsafe_allow_html=True)
    
    st.divider()
    
    # ═══════════════════════════════════════════
    # 🗺️ الخريطة
    # ═══════════════════════════════════════════
    st.markdown("### 🗺️ الموقع على الخريطة")
    map_df = pd.DataFrame([{"lat": info["lat"], "lon": info["lon"]}])
    st.map(map_df, latitude="lat", longitude="lon", size=100, zoom=4)
    
    # ═══════════════════════════════════════════
    # 🔬 تفاصيل تقنية
    # ═══════════════════════════════════════════
    with st.expander("🔬 تفاصيل تقنية"):
        if data.get("user_id"):
            st.code(f"User ID: {data['user_id']}")
        if data.get("sec_uid"):
            st.code(f"SecUID: {data['sec_uid']}")
        
        st.markdown("**📡 سجل المصادر:**")
        for src in result["sources_log"]:
            emoji = "✅" if src["success"] else "❌"
            st.markdown(f"- {emoji} **{src['name']}** — `{src.get('error') or 'نجاح'}`")
    
    # Footer
    st.markdown(
        '<div class="footer-area">'
        '<div class="footer-logo">🦅</div>'
        '<div>بَصِير © 2026</div>'
        '</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
