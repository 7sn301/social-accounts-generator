# -*- coding: utf-8 -*-
"""
مولد معلومات حسابات التواصل الاجتماعي v5
- 🎵 محلل TikTok متخصص (Universal Data + استنتاج ذكي)
- 🌐 14+ منصة أخرى
- 🆔 ID دائم + موقع جغرافي + تحليل عميق
"""

import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import io
import re
import time
import math
import socket
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, parse_qs, quote

# استيراد محلل TikTok المتخصص
from tiktok_analyzer import (
    fetch_tiktok_profile,
    analyze_tiktok_video,
    calculate_engagement_metrics,
    TIKTOK_REGION_MAP,
    LANGUAGE_NAMES_AR,
    format_count as tt_format_count,
)

# استيراد محلل X (Twitter) v4 - محرك ذكي متعدد الطبقات + AI Vision ⭐
from x_analyzer import (
    analyze_x_tweet_legacy as analyze_x_tweet,
    analyze_x_account,
    aggregate_user_tweets,
    X_REGION_MAP,
    LANGUAGE_NAMES_AR_X,
)

# تحميل اختياري للذكاء الاصطناعي Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

import os
import base64
import html
import xml.etree.ElementTree as ET

try:
    import streamlit.components.v1 as components
except Exception:
    components = None

try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    feedparser = None
    FEEDPARSER_AVAILABLE = False


# =====================================================
# 🧠 AI Vision Callback — تحليل صور المنشورات
# =====================================================

def gemini_vision_callback(image_urls, prompt):
    """استخدام Gemini Vision لتحليل الصور واستخراج الدلائل الجغرافية"""
    if not GEMINI_AVAILABLE:
        return "NO_GEO_SIGNALS"

    api_key = os.environ.get("GEMINI_API_KEY") or st.session_state.get("gemini_api_key")
    if not api_key:
        return "NO_GEO_SIGNALS"

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')  # الأسرع والأرخص

        # حمّل الصور
        import io
        from PIL import Image

        images = []
        for url in image_urls[:3]:  # أول 3 صور فقط
            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    img = Image.open(io.BytesIO(resp.content))
                    images.append(img)
            except Exception:
                continue

        if not images:
            return "NO_GEO_SIGNALS"

        response = model.generate_content([prompt] + images)
        return response.text or "NO_GEO_SIGNALS"
    except Exception as e:
        return f"NO_GEO_SIGNALS\n# خطأ: {e}"


def get_vision_callback():
    """يرجع callback إذا كانت AI Vision مفعلة، وإلا None"""
    if st.session_state.get("enable_ai_vision", False):
        if (os.environ.get("GEMINI_API_KEY") or st.session_state.get("gemini_api_key")) and GEMINI_AVAILABLE:
            return gemini_vision_callback
    return None

# ============ إعدادات الصفحة ============
st.set_page_config(
    page_title="مولد معلومات حسابات التواصل الاجتماعي v5",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============ CSS ============
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&family=Tajawal:wght@400;500;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Cairo', 'Tajawal', sans-serif !important;
        direction: rtl; text-align: right;
    }
    .main .block-container { direction: rtl; text-align: right; padding-top: 2rem; }
    h1, h2, h3, h4, h5, h6 { font-family: 'Cairo', sans-serif !important; text-align: right; }
    .stButton > button {
        background: linear-gradient(135deg, #ff0050 0%, #00f2ea 100%);
        color: white; border: none; border-radius: 10px;
        padding: 0.6rem 1.5rem; font-weight: 700;
        font-family: 'Cairo', sans-serif; width: 100%;
    }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(255,0,80,0.4); }
    .stTextArea textarea { direction: rtl; text-align: right; font-family: 'Tajawal', monospace; font-size: 14px; }
    .stTextInput input { direction: ltr; text-align: left; }
    [data-testid="stSidebar"] { direction: rtl; text-align: right; }
    .stDataFrame { direction: ltr; }
    .info-box { background: #dbeafe; border-right: 4px solid #3b82f6; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; }
    .warn-box { background: #fef3c7; border-right: 4px solid #f59e0b; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; }
    .tt-card {
        background: linear-gradient(135deg, #ff0050 0%, #00f2ea 100%);
        color: white; padding: 1.5rem; border-radius: 15px;
        margin: 0.5rem 0;
    }
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ============ المنصات ============
PLATFORMS = {
    "x": {"name": "X (Twitter)", "icon": "🐦", "url": "https://x.com/{}", "host": "x.com"},
    "twitter": {"name": "Twitter", "icon": "🐦", "url": "https://twitter.com/{}", "host": "twitter.com"},
    "instagram": {"name": "Instagram", "icon": "📷", "url": "https://www.instagram.com/{}/", "host": "instagram.com"},
    "youtube": {"name": "YouTube", "icon": "▶️", "url": "https://www.youtube.com/@{}", "host": "youtube.com"},
    "facebook": {"name": "Facebook", "icon": "👥", "url": "https://www.facebook.com/{}", "host": "facebook.com"},
    "snapchat": {"name": "Snapchat", "icon": "👻", "url": "https://www.snapchat.com/add/{}", "host": "snapchat.com"},
    "tiktok": {"name": "TikTok", "icon": "🎵", "url": "https://www.tiktok.com/@{}", "host": "tiktok.com"},
    "linkedin": {"name": "LinkedIn", "icon": "💼", "url": "https://www.linkedin.com/in/{}", "host": "linkedin.com"},
    "threads": {"name": "Threads", "icon": "🧵", "url": "https://www.threads.net/@{}", "host": "threads.net"},
    "reddit": {"name": "Reddit", "icon": "🤖", "url": "https://www.reddit.com/user/{}", "host": "reddit.com"},
    "pinterest": {"name": "Pinterest", "icon": "📌", "url": "https://www.pinterest.com/{}/", "host": "pinterest.com"},
    "telegram": {"name": "Telegram", "icon": "✈️", "url": "https://t.me/{}", "host": "t.me"},
    "twitch": {"name": "Twitch", "icon": "🎮", "url": "https://www.twitch.tv/{}", "host": "twitch.tv"},
    "github": {"name": "GitHub", "icon": "💻", "url": "https://github.com/{}", "host": "github.com"},
}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
}

COUNTRY_COORDS = {
    "SA": [24.7136, 46.6753], "AE": [25.2048, 55.2708], "EG": [30.0444, 31.2357],
    "KW": [29.3759, 47.9774], "QA": [25.2854, 51.5310], "BH": [26.2235, 50.5876],
    "OM": [23.5880, 58.3829], "JO": [31.9539, 35.9106], "LB": [33.8938, 35.5018],
    "SY": [33.5138, 36.2765], "IQ": [33.3152, 44.3661], "YE": [15.3694, 44.1910],
    "PS": [31.9522, 35.2332], "MA": [33.5731, -7.5898], "DZ": [36.7538, 3.0588],
    "TN": [36.8065, 10.1815], "LY": [32.8872, 13.1913], "SD": [15.5007, 32.5599],
    "SO": [2.0469, 45.3182], "MR": [18.0790, -15.9650], "US": [38.9072, -77.0369],
    "GB": [51.5074, -0.1278], "FR": [48.8566, 2.3522], "DE": [52.5200, 13.4050],
    "IT": [41.9028, 12.4964], "ES": [40.4168, -3.7038], "NL": [52.3676, 4.9041],
    "BE": [50.8503, 4.3517], "CH": [46.9480, 7.4474], "SE": [59.3293, 18.0686],
    "NO": [59.9139, 10.7522], "DK": [55.6761, 12.5683], "FI": [60.1699, 24.9384],
    "PT": [38.7223, -9.1393], "AT": [48.2082, 16.3738], "PL": [52.2297, 21.0122],
    "GR": [37.9838, 23.7275], "TR": [41.0082, 28.9784], "IR": [35.6892, 51.3890],
    "PK": [24.8607, 67.0011], "IN": [28.6139, 77.2090], "BD": [23.8103, 90.4125],
    "AF": [34.5553, 69.2075], "CN": [39.9042, 116.4074], "JP": [35.6762, 139.6503],
    "KR": [37.5665, 126.9780], "ID": [-6.2088, 106.8456], "MY": [3.1390, 101.6869],
    "SG": [1.3521, 103.8198], "TH": [13.7563, 100.5018], "VN": [21.0278, 105.8342],
    "PH": [14.5995, 120.9842], "RU": [55.7558, 37.6173], "UA": [50.4501, 30.5234],
    "BR": [-23.5505, -46.6333], "AR": [-34.6037, -58.3816], "MX": [19.4326, -99.1332],
    "CA": [45.4215, -75.6972], "AU": [-33.8688, 151.2093], "NZ": [-36.8485, 174.7633],
    "NG": [9.0765, 7.3986], "ZA": [-26.2041, 28.0473], "KE": [-1.2921, 36.8219],
    "ET": [8.9806, 38.7578], "IL": [31.7683, 35.2137]
}

BUFFIN_PLATFORMS = {
    "twitter": {"label": "Twitter", "icon": "🐦", "url": "https://x.com/{}"},
    "instagram": {"label": "Instagram", "icon": "📷", "url": "https://www.instagram.com/{}/"},
    "tiktok": {"label": "TikTok", "icon": "🎵", "url": "https://www.tiktok.com/@{}"},
    "youtube": {"label": "YouTube", "icon": "▶️", "url": "https://www.youtube.com/@{}"},
    "github": {"label": "GitHub", "icon": "💻", "url": "https://github.com/{}"},
    "linkedin": {"label": "LinkedIn", "icon": "💼", "url": "https://www.linkedin.com/in/{}"},
    "snapchat": {"label": "Snapchat", "icon": "👻", "url": "https://www.snapchat.com/add/{}"},
    "reddit": {"label": "Reddit", "icon": "🤖", "url": "https://www.reddit.com/user/{}"},
    "twitch": {"label": "Twitch", "icon": "🎮", "url": "https://www.twitch.tv/{}"},
    "pinterest": {"label": "Pinterest", "icon": "📌", "url": "https://www.pinterest.com/{}/"},
    "telegram": {"label": "Telegram", "icon": "✈️", "url": "https://t.me/{}"},
    "threads": {"label": "Threads", "icon": "🧵", "url": "https://www.threads.net/@{}"},
    "facebook": {"label": "Facebook", "icon": "👥", "url": "https://www.facebook.com/{}"},
}


# ============ دوال المساعدة العامة (للمنصات الأخرى) ============

def parse_url_to_platform(url: str):
    url = url.strip()
    if not url:
        return None, None
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower().replace("www.", "")
        path = parsed.path.strip("/")
        mapping = {
            "x.com": "x", "twitter.com": "twitter", "instagram.com": "instagram",
            "youtube.com": "youtube", "youtu.be": "youtube", "facebook.com": "facebook",
            "fb.com": "facebook", "snapchat.com": "snapchat", "tiktok.com": "tiktok",
            "linkedin.com": "linkedin", "threads.net": "threads", "reddit.com": "reddit",
            "pinterest.com": "pinterest", "t.me": "telegram", "telegram.me": "telegram",
            "twitch.tv": "twitch", "github.com": "github",
        }
        platform = mapping.get(host)
        if not platform:
            return None, None
        username = path.split("/")[0] if path else ""
        username = username.replace("@", "")
        if platform == "youtube" and "channel/" in parsed.path:
            username = parsed.path.split("channel/")[-1].strip("/")
        elif platform == "linkedin" and "in/" in parsed.path:
            username = parsed.path.split("in/")[-1].strip("/").split("/")[0]
        elif platform == "reddit" and ("user/" in parsed.path or "u/" in parsed.path):
            for prefix in ["user/", "u/"]:
                if prefix in parsed.path:
                    username = parsed.path.split(prefix)[-1].strip("/").split("/")[0]
                    break
        elif platform == "snapchat" and "add/" in parsed.path:
            username = parsed.path.split("add/")[-1].strip("/").split("/")[0]
        return platform, username if username else None
    except Exception:
        return None, None


def parse_manual_input(text: str):
    entries = []
    seen = set()
    for line in [l.strip() for l in text.splitlines() if l.strip()]:
        if line.startswith("#"):
            continue
        platform, username = None, None
        if "http" in line or any(d in line for d in [".com", ".net", ".tv", "t.me"]):
            platform, username = parse_url_to_platform(line)
        else:
            for sep in [",", ":", "\t", "|", " "]:
                if sep in line:
                    parts = [p.strip() for p in line.split(sep, 1)]
                    if len(parts) == 2 and parts[0].lower() in PLATFORMS:
                        platform = parts[0].lower()
                        username = parts[1].replace("@", "").strip()
                        break
        if platform and username:
            key = (platform, username.lower())
            if key not in seen:
                seen.add(key)
                entries.append({"platform": platform, "username": username})
    return entries


# ============ المحلل العام (للمنصات غير TikTok) ============
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_generic_account_info(platform: str, username: str):
    """سحب معلومات عامة لأي منصة غير TikTok."""
    result = {
        "platform": platform, "username": username,
        "permanent_id": "", "profile_url": "",
        "display_name": "", "bio": "", "followers": "",
        "verified": False, "profile_image": "",
        "location_text": "", "language": "",
        "status": "❌ فشل", "error": "",
    }
    if platform not in PLATFORMS:
        result["error"] = "منصة غير مدعومة"
        return result

    profile_url = PLATFORMS[platform]["url"].format(username)
    result["profile_url"] = profile_url

    try:
        response = requests.get(profile_url, headers=HEADERS, timeout=10, allow_redirects=True)
        if response.status_code == 404:
            result["error"] = "الحساب غير موجود"
            return result
        if response.status_code != 200:
            result["error"] = f"كود: {response.status_code}"
            result["status"] = "⚠️ الرابط فقط"
            return result

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        def get_meta(prop):
            tag = soup.find("meta", {"property": prop}) or soup.find("meta", {"name": prop})
            return tag.get("content", "") if tag else ""

        result["display_name"] = (
            get_meta("og:title") or get_meta("twitter:title")
            or (soup.title.string if soup.title else "")
        ).strip()
        result["bio"] = (
            get_meta("og:description") or get_meta("description") or get_meta("twitter:description")
        ).strip()
        result["profile_image"] = get_meta("og:image") or get_meta("twitter:image")

        # ID الدائم لكل منصة
        if platform in ("x", "twitter"):
            m = re.search(r'"rest_id"\s*:\s*"(\d+)"', html) or re.search(r'"id_str"\s*:\s*"(\d+)"', html)
            if m:
                result["permanent_id"] = m.group(1)
        elif platform == "youtube":
            m = re.search(r'"channelId":"(UC[\w-]{20,24})"', html) or re.search(r'"externalId":"(UC[\w-]{20,24})"', html)
            if m:
                result["permanent_id"] = m.group(1)
        elif platform == "github":
            try:
                api = requests.get(f"https://api.github.com/users/{username}",
                                   headers={"User-Agent": USER_AGENT}, timeout=5)
                if api.status_code == 200:
                    j = api.json()
                    result["permanent_id"] = str(j.get("id", ""))
                    result["location_text"] = j.get("location", "") or ""
            except Exception:
                pass
        elif platform == "reddit":
            try:
                api = requests.get(f"https://www.reddit.com/user/{username}/about.json",
                                   headers=HEADERS, timeout=5)
                if api.status_code == 200:
                    data = api.json().get("data", {})
                    result["permanent_id"] = data.get("id", "")
            except Exception:
                pass
        elif platform == "twitch":
            m = re.search(r'"userID":"(\d+)"', html)
            if m:
                result["permanent_id"] = m.group(1)
        elif platform == "instagram":
            m = re.search(r'"profilePage_(\d+)"', html) or re.search(r'"owner":\{"id":"(\d+)"', html)
            if m:
                result["permanent_id"] = m.group(1)

        # الموقع المُعلن
        if platform in ("x", "twitter"):
            m = re.search(r'"location"\s*:\s*"([^"]+)"', html)
            if m:
                val = m.group(1).strip()
                if val and val.lower() not in ("us", "en", "und"):
                    result["location_text"] = val

        if '"is_verified":true' in html.lower() or '"verified":true' in html.lower():
            result["verified"] = True

        # المتابعون
        followers_match = re.search(
            r"([\d,.]+\s*[KMB]?)\s*(?:Followers|متابع|subscribers|مشترك)",
            result["bio"], re.IGNORECASE,
        )
        if followers_match:
            result["followers"] = followers_match.group(1).strip()

        if result["display_name"] or result["permanent_id"]:
            result["status"] = "✅ نجح"
        else:
            result["status"] = "⚠️ معلومات محدودة"

    except requests.Timeout:
        result["error"] = "انتهت مهلة الاتصال"
    except Exception as e:
        result["error"] = str(e)[:100]
    return result


# ============ موجّه الطلبات ============
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_account_info(platform: str, username: str):
    """يوجّه TikTok للمحلل المتخصص، والباقي للمحلل العام."""
    if platform == "tiktok":
        tt_data = fetch_tiktok_profile(username)
        # تحويل لصيغة موحدة
        return {
            "platform": "tiktok",
            "username": tt_data["username"],
            "permanent_id": tt_data["user_id"],
            "sec_uid": tt_data["sec_uid"],
            "profile_url": tt_data["profile_url"],
            "display_name": tt_data["nickname"],
            "bio": tt_data["signature"],
            "followers": tt_data["follower_count_formatted"],
            "follower_count": tt_data["follower_count"],
            "following_count": tt_data["following_count"],
            "heart_count": tt_data["heart_count"],
            "video_count": tt_data["video_count"],
            "verified": tt_data["verified"],
            "private_account": tt_data["private_account"],
            "is_organization": tt_data["is_organization"],
            "profile_image": tt_data["avatar_medium"],
            "location_text": "",
            "country_code": tt_data["region"],
            "country_name_ar": tt_data["region_name_ar"],
            "country_flag": tt_data["region_flag"],
            "country_source": tt_data["region_source"],
            "country_confidence": tt_data["region_confidence"],
            "language": tt_data["language"],
            "language_name_ar": tt_data["language_name_ar"],
            "create_date": tt_data["create_date"],
            "bio_link": tt_data["bio_link"],
            "candidates": tt_data["candidates"],
            "status": tt_data["status"],
            "error": tt_data["error"],
        }
    else:
        return fetch_generic_account_info(platform, username)


def fetch_batch(entries, max_workers=10, progress_callback=None):
    results = []
    total = len(entries)
    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_account_info, e["platform"], e["username"]): e for e in entries}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                entry = futures[future]
                results.append({
                    "platform": entry["platform"], "username": entry["username"],
                    "status": "❌ فشل", "error": str(e)[:100],
                })
            completed += 1
            if progress_callback:
                progress_callback(completed, total)
    return results


def create_sample_excel():
    sample_data = {
        "platform": ["tiktok", "tiktok", "x", "instagram", "youtube", "github"],
        "username": ["khaby.lame", "charlidamelio", "nasa", "natgeo", "MrBeast", "torvalds"],
    }
    df = pd.DataFrame(sample_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="accounts")
    return output.getvalue()



def results_to_excel(results):
    df = pd.DataFrame(results)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="results")
    return output.getvalue()


def safe_int(value, default=0):
    try:
        if value in (None, "", "nan"):
            return default
        return int(float(value))
    except Exception:
        return default


def get_country_coords(country_code: str):
    if not country_code:
        return None
    return COUNTRY_COORDS.get(str(country_code).upper())


def create_country_map(records, country_key, confidence_key, title, popup_builder, map_key, threshold=30):
    if not FOLIUM_AVAILABLE:
        st.info("💡 لتفعيل الخريطة التفاعلية ثبّت: folium + streamlit-folium")
        return

    valid_records = []
    for record in records:
        code = (record.get(country_key) or "").upper()
        coords = get_country_coords(code)
        confidence = safe_int(record.get(confidence_key, 0))
        if coords and confidence >= threshold:
            valid_records.append((record, coords))

    if not valid_records:
        st.info("ℹ️ لا توجد نتائج كافية لعرضها على الخريطة")
        return

    st.markdown(f"#### {title}")
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")
    for record, coords in valid_records:
        popup_html = popup_builder(record)
        folium.Marker(
            coords,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=record.get("username") or record.get("user_screen_name") or record.get("nickname") or "حساب",
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(m)
    st_folium(m, width=None, height=420, key=map_key)


def _build_tiktok_report_results(tt_results, min_conf=30):
    export_results = []
    for r in tt_results:
        if r.get("status") != "✅ نجح":
            continue
        confidence = safe_int(r.get("region_confidence", 0))
        country_name = r.get("region_name_ar", "") if confidence >= min_conf else ""
        export_results.append({
            "success": True,
            "url": r.get("profile_url", ""),
            "tweet": {
                "user_screen_name": r.get("username", ""),
                "user_name": r.get("nickname", ""),
                "user_id": r.get("user_id", ""),
                "user_blue_verified": bool(r.get("verified")),
                "created_at": r.get("create_date", ""),
                "lang": r.get("language", ""),
                "lang_name_ar": r.get("language_name_ar", ""),
                "favorite_count": safe_int(r.get("heart_count", 0)),
                "conversation_count": safe_int(r.get("video_count", 0)),
                "user_profile_image": r.get("avatar_medium", ""),
                "text": r.get("signature", ""),
                "user_location_field": country_name or r.get("region_source", ""),
                "region_flag": r.get("region_flag", ""),
                "region_name_ar": country_name,
                "region_confidence": confidence,
            },
            "photos": [r.get("avatar_medium")] if r.get("avatar_medium") else [],
            "image_analysis": {
                "aggregate": {
                    "country_name": country_name,
                    "confidence_score": confidence,
                }
            },
            "vpn_check": {
                "verdict_ar": "تحليل TikTok",
                "icon": "🎵",
            },
            "post_country": country_name,
        })
    return export_results


def _format_datetime_text(value):
    if not value:
        return ""
    text_val = str(value).strip()
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            dt = datetime.strptime(text_val.replace("Z", "+0000"), fmt)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            continue
    return text_val[:19]


def _clean_summary(value, limit=240):
    if value is None:
        return ""
    txt = re.sub(r"<[^>]+>", " ", str(value))
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt[:limit] + ("…" if len(txt) > limit else "")


def _extract_json_feed_items(payload):
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        items = payload.get("items") or payload.get("entries") or []
    else:
        items = []

    normalized = []
    for item in items[:10]:
        if not isinstance(item, dict):
            continue
        normalized.append({
            "published": _format_datetime_text(
                item.get("date_published") or item.get("published") or item.get("pubDate") or item.get("date_modified")
            ),
            "title": item.get("title") or item.get("summary") or item.get("content_text") or "بدون عنوان",
            "link": item.get("url") or item.get("external_url") or item.get("link") or item.get("id") or "",
            "summary": _clean_summary(
                item.get("summary") or item.get("content_text") or item.get("content_html") or item.get("description") or ""
            ),
        })
    return normalized


def _extract_xml_feed_items(xml_text):
    if not xml_text.strip():
        return []
    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return []

    items = []
    channel_items = root.findall(".//item")
    if channel_items:
        for item in channel_items[:10]:
            items.append({
                "published": _format_datetime_text(item.findtext("pubDate") or item.findtext("published") or ""),
                "title": item.findtext("title") or "بدون عنوان",
                "link": item.findtext("link") or item.findtext("guid") or "",
                "summary": _clean_summary(item.findtext("description") or item.findtext("summary") or ""),
            })
        return items

    atom_ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall(".//atom:entry", atom_ns)
    for entry in entries[:10]:
        link_tag = entry.find("atom:link", atom_ns)
        items.append({
            "published": _format_datetime_text(entry.findtext("atom:published", default="", namespaces=atom_ns) or entry.findtext("atom:updated", default="", namespaces=atom_ns)),
            "title": entry.findtext("atom:title", default="بدون عنوان", namespaces=atom_ns),
            "link": (link_tag.get("href") if link_tag is not None else ""),
            "summary": _clean_summary(entry.findtext("atom:summary", default="", namespaces=atom_ns) or entry.findtext("atom:content", default="", namespaces=atom_ns)),
        })
    return items


def _fetch_single_feed(feed_url, limit=10):
    try:
        response = requests.get(
            feed_url,
            headers={**HEADERS, "Accept": "application/json, application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8"},
            timeout=15,
        )
    except Exception as e:
        return {"ok": False, "error": f"فشل الاتصال: {e}", "items": []}

    if response.status_code != 200:
        return {"ok": False, "error": f"HTTP {response.status_code}", "items": []}

    content_type = (response.headers.get("Content-Type") or "").lower()
    text_payload = response.text or ""

    if "json" in content_type or feed_url.lower().endswith(".json"):
        try:
            payload = response.json()
            items = _extract_json_feed_items(payload)[:limit]
            return {"ok": bool(items), "error": "لا توجد عناصر" if not items else "", "items": items}
        except Exception as e:
            return {"ok": False, "error": f"JSON غير صالح: {e}", "items": []}

    if FEEDPARSER_AVAILABLE:
        try:
            parsed = feedparser.parse(text_payload)
            items = []
            for entry in parsed.entries[:limit]:
                items.append({
                    "published": _format_datetime_text(
                        entry.get("published") or entry.get("updated") or entry.get("pubDate") or ""
                    ),
                    "title": entry.get("title") or "بدون عنوان",
                    "link": entry.get("link") or entry.get("id") or "",
                    "summary": _clean_summary(
                        entry.get("summary") or entry.get("description") or entry.get("title") or ""
                    ),
                })
            if items:
                return {"ok": True, "error": "", "items": items}
        except Exception:
            pass

    items = _extract_xml_feed_items(text_payload)[:limit]
    return {"ok": bool(items), "error": "لا توجد عناصر" if not items else "", "items": items}


def resolve_youtube_channel_id(value: str):
    raw = (value or "").strip()
    if not raw:
        return None
    if re.fullmatch(r"UC[\w-]{20,30}", raw):
        return raw

    if raw.startswith(("http://", "https://")):
        parsed = urlparse(raw)
        qs = parse_qs(parsed.query)
        if qs.get("channel_id"):
            return qs["channel_id"][0]
        m = re.search(r"/channel/(UC[\w-]{20,30})", parsed.path)
        if m:
            return m.group(1)
        page_url = raw
    else:
        handle = raw if raw.startswith("@") else f"@{raw}"
        page_url = f"https://www.youtube.com/{handle}"

    try:
        resp = requests.get(page_url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            html_text = resp.text
            for pattern in [
                r'"channelId":"(UC[\w-]{20,30})"',
                r'"externalId":"(UC[\w-]{20,30})"',
                r'"browseId":"(UC[\w-]{20,30})"',
            ]:
                m = re.search(pattern, html_text)
                if m:
                    return m.group(1)
    except Exception:
        return None
    return None


def build_rss_source(line: str):
    raw = (line or "").strip()
    if not raw:
        return None

    platform = None
    username = None
    display = raw
    feed_urls = []

    if raw.startswith(("http://", "https://")):
        platform, username = parse_url_to_platform(raw)
    else:
        low = raw.lower()
        if "reddit" in low:
            platform = "reddit"
        elif "youtube" in low or low.startswith("uc") or low.startswith("@"):
            platform = "youtube"
        elif "tiktok" in low:
            platform = "tiktok"
        else:
            platform = "x"
        username = raw.strip().replace("@", "")

    if platform == "tiktok":
        if not username:
            if "tiktok.com/@" in raw:
                username = raw.split("tiktok.com/@")[-1].split("/")[0].split("?")[0]
        username = (username or "").replace("@", "").strip()
        if username:
            display = f"TikTok @{username}"
            feed_urls = [
                f"https://rss.app/feeds/v1.1/tiktok/@{quote(username)}.json",
            ]
    elif platform in ("x", "twitter"):
        username = (username or "").replace("@", "").strip()
        if username:
            display = f"X @{username}"
            feed_urls = [
                f"https://nitter.net/{quote(username)}/rss",
                f"https://rss.app/feeds/v1.1/twitter/{quote(username)}.json",
            ]
    elif platform == "youtube":
        channel_id = resolve_youtube_channel_id(raw or username)
        username = (username or raw).replace("@", "").strip()
        display = f"YouTube {('@' + username) if username else channel_id or ''}".strip()
        if channel_id:
            feed_urls = [f"https://www.youtube.com/feeds/videos.xml?channel_id={quote(channel_id)}"]
    elif platform == "reddit":
        if "/user/" in raw:
            username = raw.split("/user/")[-1].strip("/").split("/")[0]
        username = (username or "").replace("@", "").strip()
        if username:
            display = f"Reddit u/{username}"
            feed_urls = [f"https://www.reddit.com/user/{quote(username)}/.rss"]

    if not feed_urls:
        return {
            "ok": False,
            "source": raw,
            "platform": platform or "غير معروف",
            "display": raw,
            "error": "تعذّر تحويل الرابط إلى RSS feed مدعوم",
            "items": [],
        }

    errors = []
    for feed_url in feed_urls:
        result = _fetch_single_feed(feed_url, limit=10)
        if result.get("ok") and result.get("items"):
            return {
                "ok": True,
                "source": raw,
                "platform": platform,
                "display": display,
                "feed_url": feed_url,
                "items": result["items"],
                "error": "",
            }
        errors.append(f"{feed_url} → {result.get('error', 'فشل غير معروف')}")

    return {
        "ok": False,
        "source": raw,
        "platform": platform or "غير معروف",
        "display": display,
        "feed_url": feed_urls[0],
        "items": [],
        "error": " | ".join(errors) if errors else "فشل جلب الـ feed",
    }


@st.cache_data(ttl=300, show_spinner=False)
def fetch_rss_batch(lines):
    results = []
    for line in lines:
        if not str(line).strip():
            continue
        results.append(build_rss_source(str(line).strip()))
    return results


@st.cache_data(ttl=300, show_spinner=False)
def buffin_check_platform(platform_key: str, username: str):
    info = BUFFIN_PLATFORMS[platform_key]
    url = info["url"].format(username)
    status_key = "blocked"
    status_label = "🟡 محجوب"
    code = None
    error = ""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True, stream=True)
        code = resp.status_code
        if code == 200:
            status_key = "exists"
            status_label = "🟢 موجود"
        elif code == 404:
            status_key = "missing"
            status_label = "🔴 غير موجود"
        else:
            status_key = "blocked"
            status_label = "🟡 محجوب"
    except Exception as e:
        error = str(e)[:120]
        status_key = "blocked"
        status_label = "🟡 محجوب"
    return {
        "platform": platform_key,
        "label": info["label"],
        "icon": info["icon"],
        "url": url,
        "username": username,
        "http_status": code,
        "status_key": status_key,
        "status_label": status_label,
        "error": error,
    }


@st.cache_data(ttl=300, show_spinner=False)
def buffin_search_username(username: str):
    username = (username or "").strip().lstrip("@")
    if not username:
        return []

    order = list(BUFFIN_PLATFORMS.keys())
    results = []
    with ThreadPoolExecutor(max_workers=min(13, len(order))) as executor:
        futures = {executor.submit(buffin_check_platform, key, username): key for key in order}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                key = futures[future]
                info = BUFFIN_PLATFORMS[key]
                results.append({
                    "platform": key,
                    "label": info["label"],
                    "icon": info["icon"],
                    "url": info["url"].format(username),
                    "username": username,
                    "http_status": None,
                    "status_key": "blocked",
                    "status_label": "🟡 محجوب",
                    "error": str(e)[:120],
                })
    results.sort(key=lambda x: order.index(x["platform"]))
    return results


def render_buffin_open_all(results):
    existing_urls = [r["url"] for r in results if r.get("status_key") == "exists"]
    if not existing_urls:
        st.caption("لا توجد حسابات موجودة لفتحها")
        return
    if components is None:
        st.caption("components غير متاح — استخدم الروابط أدناه")
        return
    js_calls = "".join([f"window.open('{u}', '_blank');" for u in existing_urls])
    html_block = f"""
    <div dir="rtl" style="margin:0 0 12px 0;">
      <button onclick="{js_calls}" style="width:100%;padding:12px 18px;border:none;border-radius:10px;background:linear-gradient(135deg,#0ea5e9,#22c55e);color:#fff;font-weight:700;cursor:pointer;font-family:Cairo,sans-serif;">
        🔗 فتح الكل ({len(existing_urls)})
      </button>
    </div>
    """
    components.html(html_block, height=70)


# ============ الواجهة ============

st.markdown(
    """
    <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #ff0050 0%, #00f2ea 100%); 
                border-radius: 15px; margin-bottom: 2rem; color: white;">
        <h1 style="color: white; margin: 0;">🌐 مولد معلومات حسابات التواصل الاجتماعي v5</h1>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.95;">
            🎵 TikTok • 🐦 X • 📡 RSS • 🔍 BUFFIN • 🛰️ Geo-OSINT
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============ الشريط الجانبي ============
with st.sidebar:
    st.markdown("### ⚙️ الإعدادات")
    max_workers = st.slider("عدد العمليات المتوازية", 1, 20, 10)
    min_confidence = st.slider("🎯 الحد الأدنى لثقة الدولة", 0, 100, 30)

    st.markdown("---")

    # 🧠 الذكاء الاصطناعي لتحليل صور المنشورات
    st.markdown("### 🧠 الذكاء الاصطناعي (تحليل صور)")
    enable_ai_vision = st.checkbox(
        "تفعيل تحليل صور التغريدات (X فقط)",
        value=False,
        key="enable_ai_vision",
        help="يستخرج دلائل جغرافية من صور المنشور (معالم، لوحات، أعلام، لباس تقليدي). يرفع الدقة بشكل كبير للحسابات بدون بيانات نصية"
    )
    if enable_ai_vision:
        st.text_input(
            "Gemini API Key",
            type="password",
            key="gemini_api_key",
            help="مجاني من https://aistudio.google.com/apikey"
        )
        if not GEMINI_AVAILABLE:
            st.warning("⚠️ ثبّت `google-generativeai` في requirements.txt")
        elif not (os.environ.get("GEMINI_API_KEY") or st.session_state.get("gemini_api_key")):
            st.info("💡 أدخل API Key لتفعيل تحليل الصور")
        else:
            st.success("✅ تحليل الصور مفعل")

    st.markdown("---")
    st.markdown("### 🎵 تحليل TikTok المتقدم")
    st.markdown("""
    **بيانات يستخرجها المحلل:**
    - 🆔 User ID + secUid (دائمين)
    - 👤 الاسم الظاهر + التوثيق
    - 📅 تاريخ إنشاء الحساب
    - 📊 متابعون / متابَعون / إعجابات / فيديوهات
    - 🌍 الدولة (5 طبقات استنتاج)
    - 🌐 اللغة المُعلنة
    - 🛒 حساب تجاري؟ موسسة؟
    - 🔒 خاص؟ سري؟
    """)

    st.markdown("---")
    st.markdown("### 📊 المنصات (14)")
    cols = st.columns(2)
    for i, (key, info) in enumerate(PLATFORMS.items()):
        cols[i % 2].markdown(f"{info['icon']} **{info['name']}**")

    st.markdown("---")
    st.download_button(
        "⬇️ ملف Excel نموذجي",
        data=create_sample_excel(),
        file_name="sample_accounts.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

# استيراد محلل موقع المنشور
from post_location_analyzer import (
    analyze_image_geo,
    analyze_post_images,
    detect_vpn,
    extract_exif_gps,
    reverse_geocode,
)

# استيراد About Account fetcher (X الرسمي) ⭐
from about_account_fetcher import (
    fetch_about_account,
    diagnose_vpn_from_about,
    country_name_to_iso,
    parse_cookies_string,
)

# استيراد مصدّر التقارير (Word + PowerPoint) 📑
try:
    from report_exporter import generate_word_report, generate_pptx_report
    REPORT_EXPORTER_AVAILABLE = True
except ImportError:
    REPORT_EXPORTER_AVAILABLE = False

# 🛰️ استيراد Geo-Engine (GeoSpy.ai + EXIF + Yandex + AI) - المحرّك الجديد
try:
    from geo_engine import (
        analyze_image_full,
        extract_exif_full,
        summarize_exif,
        build_reverse_search_links,
        triangulate,
        detect_vpn as ge_detect_vpn,
        flag as ge_flag,
        country_ar as ge_country_ar,
        ISO_TO_AR,
    )
    GEO_ENGINE_AVAILABLE = True
except ImportError as _e:
    GEO_ENGINE_AVAILABLE = False
    GEO_ENGINE_ERROR = str(_e)

# 🕵️ استيراد Twitter OSINT Toolkit (جديد)
try:
    from twitter_osint import (
        build_geocode_search, build_near_search, build_user_search,
        geocode_place, reverse_geocode as osint_reverse,
        find_place_id, TWITTER_PLACE_IDS,
        analyze_timezone_from_tweets, haversine_km,
        build_map_verification_links, extract_entities,
        cluster_user_locations, FAMOUS_LOCATIONS_AR,
    )
    OSINT_AVAILABLE = True
except ImportError as _e:
    OSINT_AVAILABLE = False
    OSINT_ERROR = str(_e)

# Folium for interactive maps (optional)
try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

# 🛡️ VPN Detector (multi-signal investigation)
try:
    from vpn_detector import investigate as vpn_investigate
    VPN_DETECTOR_AVAILABLE = True
except ImportError as _e:
    VPN_DETECTOR_AVAILABLE = False
    VPN_DETECTOR_ERROR = str(_e)

# ============ TikTok OSINT Functions (Inline) ============
from collections import Counter as _Counter
import math as _math

TIKTOK_REGION_MAP = {
    "US": ("🇺🇸", "الولايات المتحدة"), "GB": ("🇬🇧", "المملكة المتحدة"),
    "SA": ("🇸🇦", "المملكة العربية السعودية"), "AE": ("🇦🇪", "الإمارات العربية المتحدة"),
    "EG": ("🇪🇬", "مصر"), "JO": ("🇯🇴", "الأردن"), "KW": ("🇰🇼", "الكويت"),
    "QA": ("🇶🇦", "قطر"), "BH": ("🇧🇭", "البحرين"), "OM": ("🇴🇲", "عُمان"),
    "IQ": ("🇮🇶", "العراق"), "SY": ("🇸🇾", "سوريا"), "LB": ("🇱🇧", "لبنان"),
    "MA": ("🇲🇦", "المغرب"), "TN": ("🇹🇳", "تونس"), "DZ": ("🇩🇿", "الجزائر"),
    "LY": ("🇱🇾", "ليبيا"), "SD": ("🇸🇩", "السودان"), "YE": ("🇾🇪", "اليمن"),
    "TR": ("🇹🇷", "تركيا"), "IR": ("🇮🇷", "إيران"), "PK": ("🇵🇰", "باكستان"),
    "IN": ("🇮🇳", "الهند"), "ID": ("🇮🇩", "إندونيسيا"), "PH": ("🇵🇭", "الفلبين"),
    "TH": ("🇹🇭", "تايلاند"), "VN": ("🇻🇳", "فيتنام"), "MY": ("🇲🇾", "ماليزيا"),
    "SG": ("🇸🇬", "سنغافورة"), "JP": ("🇯🇵", "اليابان"), "KR": ("🇰🇷", "كوريا الجنوبية"),
    "CN": ("🇨🇳", "الصين"), "RU": ("🇷🇺", "روسيا"), "DE": ("🇩🇪", "ألمانيا"),
    "FR": ("🇫🇷", "فرنسا"), "IT": ("🇮🇹", "إيطاليا"), "ES": ("🇪🇸", "إسبانيا"),
    "BR": ("🇧🇷", "البرازيل"), "MX": ("🇲🇽", "المكسيك"), "CA": ("🇨🇦", "كندا"),
    "AU": ("🇦🇺", "أستراليا"), "NG": ("🇳🇬", "نيجيريا"), "ZA": ("🇿🇦", "جنوب أفريقيا"),
    "KE": ("🇰🇪", "كينيا"), "GH": ("🇬🇭", "غانا"), "ET": ("🇪🇹", "إثيوبيا"),
    "PL": ("🇵🇱", "بولندا"), "UA": ("🇺🇦", "أوكرانيا"), "NL": ("🇳🇱", "هولندا"),
    "SE": ("🇸🇪", "السويد"), "NO": ("🇳🇴", "النرويج"), "DK": ("🇩🇰", "الدنمارك"),
    "FI": ("🇫🇮", "فنلندا"), "PT": ("🇵🇹", "البرتغال"), "GR": ("🇬🇷", "اليونان"),
    "CZ": ("🇨🇿", "التشيك"), "HU": ("🇭🇺", "المجر"), "RO": ("🇷🇴", "رومانيا"),
    "BD": ("🇧🇩", "بنغلاديش"), "NP": ("🇳🇵", "نيبال"), "LK": ("🇱🇰", "سريلانكا"),
    "MM": ("🇲🇲", "ميانمار"), "KH": ("🇰🇭", "كمبوديا"), "LA": ("🇱🇦", "لاوس"),
    "MN": ("🇲🇳", "منغوليا"), "TW": ("🇹🇼", "تايوان"), "HK": ("🇭🇰", "هونغ كونغ"),
    "PS": ("🇵🇸", "فلسطين"), "AF": ("🇦🇫", "أفغانستان"), "UZ": ("🇺🇿", "أوزبكستان"),
    "KZ": ("🇰🇿", "كازاخستان"), "AZ": ("🇦🇿", "أذربيجان"), "GE": ("🇬🇪", "جورجيا"),
    "AM": ("🇦🇲", "أرمينيا"), "BY": ("🇧🇾", "بيلاروسيا"), "RS": ("🇷🇸", "صربيا"),
    "HR": ("🇭🇷", "كرواتيا"), "SK": ("🇸🇰", "سلوفاكيا"), "BG": ("🇧🇬", "بلغاريا"),
    "MK": ("🇲🇰", "مقدونيا الشمالية"), "AL": ("🇦🇱", "ألبانيا"), "BA": ("🇧🇦", "البوسنة"),
    "ME": ("🇲🇪", "الجبل الأسود"), "MD": ("🇲🇩", "مولدوفا"), "LT": ("🇱🇹", "ليتوانيا"),
    "LV": ("🇱🇻", "لاتفيا"), "EE": ("🇪🇪", "إستونيا"), "IS": ("🇮🇸", "أيسلندا"),
    "IE": ("🇮🇪", "أيرلندا"), "CH": ("🇨🇭", "سويسرا"), "AT": ("🇦🇹", "النمسا"),
    "BE": ("🇧🇪", "بلجيكا"), "NZ": ("🇳🇿", "نيوزيلندا"), "ZW": ("🇿🇼", "زيمبابوي"),
    "TZ": ("🇹🇿", "تنزانيا"), "UG": ("🇺🇬", "أوغندا"), "MZ": ("🇲🇿", "موزمبيق"),
    "CM": ("🇨🇲", "الكاميرون"), "CI": ("🇨🇮", "كوت ديفوار"), "SN": ("🇸🇳", "السنغال"),
    "MG": ("🇲🇬", "مدغشقر"), "CO": ("🇨🇴", "كولومبيا"), "AR": ("🇦🇷", "الأرجنتين"),
    "CL": ("🇨🇱", "تشيلي"), "PE": ("🇵🇪", "بيرو"), "VE": ("🇻🇪", "فنزويلا"),
    "EC": ("🇪🇨", "الإكوادور"), "BO": ("🇧🇴", "بوليفيا"), "PY": ("🇵🇾", "باراغواي"),
    "UY": ("🇺🇾", "أوروغواي"), "GT": ("🇬🇹", "غواتيمالا"), "HN": ("🇭🇳", "هندوراس"),
    "SV": ("🇸🇻", "السلفادور"), "CR": ("🇨🇷", "كوستاريكا"), "PA": ("🇵🇦", "بنما"),
    "CU": ("🇨🇺", "كوبا"), "DO": ("🇩🇴", "الدومينيكان"), "HT": ("🇭🇹", "هايتي"),
    "JM": ("🇯🇲", "جامايكا"), "TT": ("🇹🇹", "ترينيداد وتوباغو"),
    "IL": ("🇮🇱", "إسرائيل"), "CY": ("🇨🇾", "قبرص"), "MT": ("🇲🇹", "مالطا"),
    "LU": ("🇱🇺", "لوكسمبورغ"), "LI": ("🇱🇮", "ليختنشتاين"), "MC": ("🇲🇨", "موناكو"),
    "AD": ("🇦🇩", "أندورا"), "SM": ("🇸🇲", "سان مارينو"), "VA": ("🇻🇦", "الفاتيكان"),
}

COUNTRY_CENTERS = {
    "US": (37.09, -95.71), "GB": (55.37, -3.43), "SA": (23.89, 45.07),
    "AE": (23.42, 53.84), "EG": (26.82, 30.80), "JO": (30.59, 36.24),
    "KW": (29.31, 47.48), "QA": (25.35, 51.18), "BH": (26.07, 50.55),
    "OM": (21.51, 55.92), "IQ": (33.22, 43.68), "SY": (34.80, 38.99),
    "LB": (33.85, 35.86), "MA": (31.79, -7.09), "TN": (33.89, 9.54),
    "DZ": (28.03, 1.66), "LY": (26.33, 17.23), "SD": (12.86, 30.22),
    "YE": (15.55, 48.52), "TR": (38.96, 35.24), "IR": (32.43, 53.69),
    "PK": (30.38, 69.35), "IN": (20.59, 78.96), "ID": (-0.79, 113.92),
    "PH": (12.88, 121.77), "TH": (15.87, 100.99), "VN": (14.06, 108.28),
    "MY": (4.21, 108.81), "SG": (1.35, 103.82), "JP": (36.20, 138.25),
    "KR": (35.91, 127.77), "CN": (35.86, 104.20), "RU": (61.52, 105.32),
    "DE": (51.17, 10.45), "FR": (46.23, 2.21), "IT": (41.87, 12.56),
    "ES": (40.46, -3.75), "BR": (-14.24, -51.93), "MX": (23.63, -102.55),
    "CA": (56.13, -106.35), "AU": (-25.27, 133.78), "NG": (9.08, 8.68),
    "ZA": (-30.56, 22.94), "KE": (-0.02, 37.91), "GH": (7.95, -1.02),
    "ET": (9.15, 40.49), "PL": (51.92, 19.15), "UA": (48.38, 31.17),
    "NL": (52.13, 5.29), "SE": (60.13, 18.64), "NO": (60.47, 8.47),
    "DK": (56.26, 9.50), "FI": (61.92, 25.75), "PT": (39.40, -8.22),
    "GR": (39.07, 21.82), "PS": (31.95, 35.23), "IL": (31.05, 34.85),
    "AF": (33.94, 67.71), "BD": (23.68, 90.36), "NP": (28.39, 84.12),
    "LK": (7.87, 80.77), "MM": (17.11, 96.56), "KH": (12.57, 104.99),
    "CO": (4.57, -74.30), "AR": (-38.42, -63.62), "CL": (-35.68, -71.54),
    "PE": (-9.19, -75.02), "VE": (6.42, -66.59),
}

FAMOUS_LOCATIONS_TT = [
    "Riyadh", "Jeddah", "Mecca", "Cairo", "Alexandria", "Dubai", "Abu Dhabi",
    "Amman", "Baghdad", "Damascus", "Beirut", "Kuwait City", "Doha", "Muscat",
    "Sanaa", "Khartoum", "Tunis", "Algiers", "Rabat", "Casablanca", "Tripoli",
    "London", "Paris", "Berlin", "Istanbul", "Tehran", "Karachi", "Mumbai",
    "Jakarta", "Bangkok", "Tokyo", "Seoul", "Beijing", "Moscow", "New York",
    "Los Angeles", "Toronto", "Sydney", "Nairobi", "Lagos", "Johannesburg",
]

TZ_OFFSET_COUNTRIES = {
    -12: [], -11: ["WS", "AS"], -10: ["US", "CK", "PF"], -9: ["US"],
    -8: ["US", "CA", "MX"], -7: ["US", "CA", "MX"], -6: ["US", "CA", "MX", "CR", "GT", "HN", "SV"],
    -5: ["US", "CA", "MX", "CO", "PE", "EC", "CU", "JM"],
    -4: ["VE", "BO", "PY", "TT", "DO", "BB"],
    -3: ["BR", "AR", "CL", "UY", "GF", "SR"],
    -2: ["BR", "GS"], -1: ["CV", "PT"], 0: ["GB", "IE", "PT", "MA", "GH", "SN", "CI"],
    1: ["DE", "FR", "IT", "ES", "NL", "BE", "PL", "AT", "CH", "NG", "CM", "DZ", "TN", "LY"],
    2: ["ZA", "EG", "SD", "KE", "TZ", "UG", "ET", "MZ", "RW", "IL", "CY", "TR", "UA", "RO", "GR", "BG", "FI"],
    3: ["SA", "IQ", "KW", "QA", "BH", "YE", "OM", "JO", "SY", "LB", "RU", "BY"],
    4: ["AE", "AM", "AZ", "GE", "RU"], 5: ["PK", "UZ", "KZ", "TM"],
    5.5: ["IN", "LK"], 6: ["BD", "KZ", "RU"], 6.5: ["MM"],
    7: ["TH", "VN", "LA", "KH", "ID", "RU"], 8: ["CN", "TW", "HK", "SG", "MY", "PH", "ID", "RU"],
    9: ["JP", "KR"], 9.5: ["AU"], 10: ["AU", "PG"],
    11: ["SB", "VU", "NC"], 12: ["NZ", "FJ", "TV"],
}

def get_tiktok_region_center(code: str):
    """Return (lat, lon) center for a country code, or None."""
    code = (code or "").upper().strip()
    return COUNTRY_CENTERS.get(code)

def infer_user_location_from_videos(video_results):
    """Infer user location from video metadata."""
    if not video_results:
        return {"error": "no_videos", "probable_country_code": "", "confidence": 0}

    loc_counter = _Counter()
    author_counter = _Counter()
    total = len(video_results)
    videos_with_location = 0
    videos_with_author_region = 0

    for v in video_results:
        loc = (v.get("location_created") or "").upper().strip()
        if loc and loc in TIKTOK_REGION_MAP:
            loc_counter[loc] += 1
            videos_with_location += 1
        auth_region = (v.get("author_region") or v.get("author", {}).get("region") if isinstance(v.get("author"), dict) else "").upper().strip()
        if auth_region and auth_region in TIKTOK_REGION_MAP:
            author_counter[auth_region] += 1
            videos_with_author_region += 1

    if not loc_counter and not author_counter:
        return {
            "probable_country_code": "", "probable_country_name_ar": "غير محدد",
            "probable_flag": "🌍", "confidence": 0, "total_videos": total,
            "videos_with_location": 0, "location_counts": [], "evidence": [],
            "author_region_counts": {},
        }

    combined = _Counter()
    for k, v in loc_counter.items():
        combined[k] += v * 2
    for k, v in author_counter.items():
        combined[k] += v

    probable_code = combined.most_common(1)[0][0] if combined else ""
    top_loc_count = loc_counter.get(probable_code, 0)
    total_loc = max(sum(loc_counter.values()), 1)
    dominance = combined.get(probable_code, 0) / max(sum(combined.values()), 1)
    coverage = videos_with_location / max(total, 1)
    author_agreement = (author_counter.get(probable_code, 0) / max(videos_with_author_region, 1)) if videos_with_author_region else 0
    confidence = int(round(min(95, (dominance * 55) + (coverage * 25) + (author_agreement * 15) + (5 if top_loc_count >= 2 else 0))))

    flag, name_ar = TIKTOK_REGION_MAP.get(probable_code, ("🌍", probable_code))
    location_counts = [
        {"country_code": k, "count": v, "flag": TIKTOK_REGION_MAP.get(k, ("🌍", k))[0],
         "country_name_ar": TIKTOK_REGION_MAP.get(k, ("🌍", k))[1]}
        for k, v in loc_counter.most_common()
    ]

    evidence = []
    if top_loc_count > 0:
        evidence.append(f"locationCreated='{probable_code}' ظهر في {top_loc_count}/{total_loc} فيديو")
    if author_counter.get(probable_code, 0) > 0:
        evidence.append(f"author.region='{probable_code}' في {author_counter[probable_code]} فيديو")

    return {
        "probable_country_code": probable_code, "probable_country_name_ar": name_ar,
        "probable_flag": flag, "confidence": confidence, "total_videos": total,
        "videos_with_location": videos_with_location, "location_counts": location_counts,
        "evidence": evidence, "author_region_counts": dict(author_counter),
    }

def analyze_timezone_from_videos(video_results):
    """Analyze posting times to infer timezone."""
    timestamps = []
    for v in video_results:
        ts = v.get("create_time") or v.get("createTime") or v.get("created_at")
        if ts:
            try:
                timestamps.append(int(ts))
            except (ValueError, TypeError):
                pass

    if len(timestamps) < 3:
        return {"error": "insufficient_data", "sample_size": len(timestamps), "confidence": 0}

    hour_counters = {}
    for offset_raw in list(range(-12, 13)) + [5.5, 6.5, 9.5]:
        offset = float(offset_raw)
        hours = []
        for ts in timestamps:
            import datetime as _dt
            utc_dt = _dt.datetime.utcfromtimestamp(ts)
            local_h = (utc_dt.hour + offset) % 24
            hours.append(int(local_h))
        morning_evening = sum(1 for h in hours if 6 <= h <= 9 or 17 <= h <= 23)
        score = morning_evening / len(hours)
        midnight_penalty = sum(1 for h in hours if 2 <= h <= 5) / len(hours)
        score -= midnight_penalty * 0.5
        hour_counters[offset] = {"hours": hours, "score": score}

    sorted_offsets = sorted(hour_counters.items(), key=lambda x: -x[1]["score"])
    best_offset = sorted_offsets[0][0]
    best_offset_int = int(best_offset) if best_offset == int(best_offset) else best_offset
    sign = "+" if best_offset >= 0 else ""
    best_offset_str = f"UTC{sign}{best_offset_int}"

    offset_key = round(best_offset * 2) / 2
    candidate_countries = TZ_OFFSET_COUNTRIES.get(int(best_offset) if best_offset == int(best_offset) else best_offset, [])
    if not candidate_countries:
        offset_key2 = offset_key if offset_key in TZ_OFFSET_COUNTRIES else int(best_offset)
        candidate_countries = TZ_OFFSET_COUNTRIES.get(offset_key2, [])

    top_offsets = []
    for off, data in sorted_offsets[:5]:
        sign2 = "+" if off >= 0 else ""
        off_int = int(off) if off == int(off) else off
        ccs = TZ_OFFSET_COUNTRIES.get(off_int, TZ_OFFSET_COUNTRIES.get(int(off), []))
        top_offsets.append({
            "offset_str": f"UTC{sign2}{off_int}",
            "score": round(data["score"], 3),
            "confidence": int(min(90, data["score"] * 100)),
            "candidate_countries": ccs[:5],
        })

    histogram = {}
    import datetime as _dt
    for ts in timestamps:
        utc_dt = _dt.datetime.utcfromtimestamp(ts)
        local_h = int((utc_dt.hour + best_offset) % 24)
        histogram[str(local_h)] = histogram.get(str(local_h), 0) + 1

    return {
        "best_offset_str": best_offset_str,
        "confidence": int(min(90, sorted_offsets[0][1]["score"] * 100)),
        "sample_size": len(timestamps),
        "candidate_countries": candidate_countries[:8],
        "top_offsets": top_offsets,
        "histogram_local_hours": histogram,
    }

def geocode_tiktok_place(place_name: str, lang: str = "ar"):
    """Geocode a place name using Nominatim."""
    try:
        import requests as _req
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": place_name, "format": "json", "limit": 1, "accept-language": lang}
        headers = {"User-Agent": "TikTokOSINT/1.0"}
        r = _req.get(url, params=params, headers=headers, timeout=6)
        data = r.json()
        if data:
            return {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"]),
                    "display_name": data[0].get("display_name", ""),
                    "country": data[0].get("address", {}).get("country", "")}
    except Exception:
        pass
    return None

def build_tiktok_search_links(place: str, keywords: str = "", geo_result=None):
    """Build TikTok search links for a location."""
    from urllib.parse import quote as _q
    query = f"{place} {keywords}".strip()
    links = {
        "general_search": f"https://www.tiktok.com/search?q={_q(query)}",
        "hashtag_search": f"https://www.tiktok.com/tag/{_q(place.replace(' ', ''))}",
        "regional_search": f"https://www.google.com/search?q=site:tiktok.com+{_q(query)}",
    }
    if geo_result:
        lat, lon = geo_result["lat"], geo_result["lon"]
        links["maps"] = {
            "google_maps": f"https://www.google.com/maps?q={lat},{lon}",
            "yandex_maps": f"https://yandex.com/maps/?ll={lon},{lat}&z=10",
            "openstreetmap": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=10",
            "apple_maps": f"https://maps.apple.com/?ll={lat},{lon}",
        }
    return links

def build_tiktok_user_search(username: str, place: str, keywords: str = ""):
    """Build TikTok user search links."""
    from urllib.parse import quote as _q
    return {
        "profile_url": f"https://www.tiktok.com/@{username}",
        "tiktok_search": f"https://www.tiktok.com/search?q={_q(f'{username} {place}'.strip())}",
        "google_search": f"https://www.google.com/search?q={_q(f'site:tiktok.com {username} {place}')}",
    }

def build_tiktok_verification_links(username: str):
    """Build verification links for a TikTok user."""
    from urllib.parse import quote as _q
    return {
        "tiktok_profile": f"https://www.tiktok.com/@{username}",
        "wayback": f"https://web.archive.org/web/*/tiktok.com/@{username}",
        "google": f"https://www.google.com/search?q={_q(f'TikTok @{username}')}",
        "yandex": f"https://yandex.com/search/?text={_q(f'TikTok {username}')}",
        "urlebird": f"https://urlebird.com/user/{username}/",
    }

def build_tt_map_links(lat: float, lon: float):
    """Build map links for a location."""
    return {
        "google_maps": f"https://www.google.com/maps?q={lat},{lon}",
        "yandex_maps": f"https://yandex.com/maps/?ll={lon},{lat}&z=10",
        "openstreetmap": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=10",
        "apple_maps": f"https://maps.apple.com/?ll={lat},{lon}",
    }


TIKTOK_OSINT_AVAILABLE = True
TIKTOK_OSINT_ERROR = ""


def normalize_tiktok_username(value: str):
    text_val = (value or "").strip()
    if not text_val:
        return ""
    if "tiktok.com/@" in text_val:
        text_val = text_val.split("tiktok.com/@")[-1].split("/")[0].split("?")[0]
    return text_val.replace("@", "").strip()


def extract_tiktok_usernames(raw_text: str):
    usernames = []
    seen = set()
    for line in (raw_text or "").splitlines():
        username = normalize_tiktok_username(line)
        if username and username.lower() not in seen:
            seen.add(username.lower())
            usernames.append(username)
    return usernames


def extract_tiktok_video_urls(raw_text: str):
    urls = []
    seen = set()
    for line in (raw_text or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "tiktok.com" in line.lower() and "/video/" in line.lower() and line not in seen:
            seen.add(line)
            urls.append(line)
    return urls


def get_tiktok_country_meta(code: str):
    code = (code or "").upper().strip()
    if not code:
        return ("🌍", "غير محدد")
    return TIKTOK_REGION_MAP.get(code, ("🌍", code))


@st.cache_data(ttl=86400, show_spinner=False)
def resolve_tiktok_geo_point(country_code: str = "", country_name_ar: str = ""):
    code = (country_code or "").upper().strip()
    coords = get_tiktok_region_center(code) or get_country_coords(code)
    if coords:
        return {
            "lat": float(coords[0]),
            "lon": float(coords[1]),
            "display_name": country_name_ar or get_tiktok_country_meta(code)[1],
            "resolved_from": "country_center",
        }

    label = (country_name_ar or get_tiktok_country_meta(code)[1]).strip()
    if label and label != "غير محدد":
        geo_result = geocode_tiktok_place(label, lang="ar") or geocode_tiktok_place(label, lang="en")
        if geo_result:
            return {
                "lat": float(geo_result["lat"]),
                "lon": float(geo_result["lon"]),
                "display_name": geo_result.get("display_name") or label,
                "resolved_from": "geocoding",
            }
    return None


def combine_tiktok_geo_signals(account_row=None, user_video_rows=None):
    account_row = account_row or {}
    user_video_rows = user_video_rows or []

    username = normalize_tiktok_username(account_row.get("username") or (user_video_rows[0].get("username", "") if user_video_rows else ""))
    profile_url = account_row.get("profile_url") or (f"https://www.tiktok.com/@{username}" if username else "")

    scores = {}
    evidence = []

    account_code = (account_row.get("region") or account_row.get("country_code") or "").upper().strip()
    account_conf = safe_int(account_row.get("region_confidence") or account_row.get("country_confidence"), 0)
    if account_code:
        scores[account_code] = scores.get(account_code, 0) + max(account_conf, 35)
        account_flag, account_name = get_tiktok_country_meta(account_code)
        evidence.append(f"الحساب: {account_flag} {account_name} عبر region بثقة {max(account_conf, 35)}%")

    video_report = infer_user_location_from_videos(user_video_rows) if user_video_rows else {}
    video_code = (video_report.get("probable_country_code") or "").upper().strip()
    video_conf = safe_int(video_report.get("confidence"), 0)
    if video_code:
        scores[video_code] = scores.get(video_code, 0) + (max(video_conf, 40) * 1.35)
        video_flag, video_name = get_tiktok_country_meta(video_code)
        evidence.append(
            f"الفيديوهات: {video_flag} {video_name} من locationCreated/author.region بثقة {max(video_conf, 40)}%"
        )

    tz_report = analyze_timezone_from_videos(user_video_rows) if user_video_rows else {}
    tz_error = tz_report.get("error")
    tz_best = "" if tz_error else (tz_report.get("best_offset_str") or "")
    tz_conf = 0 if tz_error else safe_int(tz_report.get("confidence"), 0)
    tz_candidates = [] if tz_error else list(tz_report.get("candidate_countries") or [])
    for idx, code in enumerate(tz_candidates[:6]):
        scores[code] = scores.get(code, 0) + max(4, (tz_conf * 0.35) / (idx + 1))
    if tz_best:
        labels = []
        for code in tz_candidates[:4]:
            flag, _name = get_tiktok_country_meta(code)
            labels.append(f"{flag} {code}")
        evidence.append(
            f"التوقيت: {tz_best} بعينة {tz_report.get('sample_size', 0)} فيديو؛ الدول المرجحة: {', '.join(labels) if labels else 'غير محدد'}"
        )

    if account_code and video_code and account_code == video_code:
        scores[account_code] = scores.get(account_code, 0) + 20
        evidence.append("تعزيز: region في الحساب يطابق locationCreated في الفيديوهات")

    if video_code and video_code in tz_candidates[:3]:
        scores[video_code] = scores.get(video_code, 0) + 10
    if account_code and account_code in tz_candidates[:3]:
        scores[account_code] = scores.get(account_code, 0) + 6

    final_code = ""
    final_conf = 0
    if scores:
        final_code = max(scores.items(), key=lambda kv: kv[1])[0]
        total_score = sum(scores.values()) or 1
        weighted_conf = int(round((scores[final_code] / total_score) * 100))
        if final_code == account_code:
            weighted_conf = max(weighted_conf, account_conf)
        if final_code == video_code:
            weighted_conf = max(weighted_conf, video_conf)
        if final_code in tz_candidates[:3]:
            weighted_conf = min(98, weighted_conf + 5)
        final_conf = min(98, weighted_conf)

    final_flag, final_name = get_tiktok_country_meta(final_code)
    geo_point = resolve_tiktok_geo_point(final_code, final_name) if final_code else None
    map_links = build_tt_map_links(geo_point["lat"], geo_point["lon"]) if geo_point else {}

    return {
        "username": username,
        "profile_url": profile_url,
        "account_country_code": account_code,
        "account_country_name_ar": get_tiktok_country_meta(account_code)[1] if account_code else "",
        "account_confidence": account_conf,
        "video_country_code": video_code,
        "video_country_name_ar": video_report.get("probable_country_name_ar") or (get_tiktok_country_meta(video_code)[1] if video_code else ""),
        "video_confidence": video_conf,
        "video_location_report": video_report,
        "timezone_best": tz_best,
        "timezone_confidence": tz_conf,
        "timezone_candidates": tz_candidates,
        "timezone_report": tz_report,
        "final_country_code": final_code,
        "final_country_name_ar": final_name if final_code else "غير محدد",
        "final_flag": final_flag,
        "final_confidence": final_conf,
        "geo_point": geo_point,
        "map_links": map_links,
        "signal_breakdown": {k: round(v, 2) for k, v in sorted(scores.items(), key=lambda item: -item[1])},
        "evidence": evidence,
        "matched_video_count": len(user_video_rows),
    }


def build_tiktok_geo_records(tt_results, video_results):
    tt_results = tt_results or []
    video_results = video_results or []

    account_index = {}
    for row in tt_results:
        username = normalize_tiktok_username(row.get("username"))
        if username and row.get("status") == "✅ نجح":
            account_index[username.lower()] = row

    videos_by_user = {}
    for row in video_results:
        if row.get("status") != "✅ نجح":
            continue
        username = normalize_tiktok_username(row.get("username"))
        if not username:
            continue
        videos_by_user.setdefault(username.lower(), []).append(row)

    all_keys = sorted(set(account_index.keys()) | set(videos_by_user.keys()))
    records = []
    for key in all_keys:
        combined = combine_tiktok_geo_signals(account_index.get(key), videos_by_user.get(key, []))
        if combined.get("username"):
            records.append(combined)
    return records


def render_tiktok_interactive_map(records, map_key="tt_integrated_geo_map"):
    if not FOLIUM_AVAILABLE:
        st.info("💡 لتفعيل الخريطة التفاعلية ثبّت: folium + streamlit-folium")
        return

    usable_records = [record for record in (records or []) if record.get("geo_point")]
    if not usable_records:
        st.info("ℹ️ لا توجد نتائج جغرافية قابلة للرسم حالياً")
        return

    center = [usable_records[0]["geo_point"]["lat"], usable_records[0]["geo_point"]["lon"]]
    fmap = folium.Map(location=center, zoom_start=2, tiles="CartoDB positron", control_scale=True)

    for record in usable_records:
        point = record["geo_point"]
        source_labels = []
        if record.get("account_country_code"):
            source_labels.append("بيانات الحساب")
        if record.get("video_country_code"):
            source_labels.append("الفيديوهات")
        if record.get("timezone_best"):
            source_labels.append("المنطقة الزمنية")
        source_text = " + ".join(source_labels) if source_labels else "إشارة عامة"
        popup_html = (
            f"<div dir='rtl' style='min-width:220px'>"
            f"<b>@{html.escape(record.get('username', ''))}</b><br>"
            f"📍 {html.escape(record.get('final_flag', '🌍'))} {html.escape(record.get('final_country_name_ar', 'غير محدد'))}<br>"
            f"🎯 الثقة: {record.get('final_confidence', 0)}%<br>"
            f"🧭 المصادر: {html.escape(source_text)}<br>"
            f"📌 {html.escape(point.get('display_name', ''))}</div>"
        )
        color = "green" if record.get("final_confidence", 0) >= 70 else "orange"
        folium.Marker(
            location=[point["lat"], point["lon"]],
            tooltip=f"@{record.get('username', '')}",
            popup=folium.Popup(popup_html, max_width=320),
            icon=folium.Icon(color=color, icon="info-sign"),
        ).add_to(fmap)

    st_folium(fmap, width=None, height=520, key=map_key)


# ============ التبويبات ============
(tab_tt, tab_video, tab_x, tab_postloc, tab_geo, tab_osint,
 tab_rss, tab_buffin, tab_manual, tab_excel, tab_help) = st.tabs([
    "🎵 محلل حسابات TikTok المتكامل",
    "🎬 تحليل فيديو تيك توك",
    "🐦 تحليل تغريدات X (Twitter)",
    "🌍 موقع المنشور + كاشف VPN",
    "🛰️ Geo-Engine (GeoSpy + EXIF + Yandex)",
    "🕵️ OSINT محقّق تويتر",
    "📡 أداة RSS",
    "🔍 BUFFIN - بحث المنصات",
    "📝 إدخال يدوي (كل المنصات)",
    "📂 رفع Excel",
    "ℹ️ التعليمات",
])


# ============ تبويب TikTok المتكامل ============
with tab_tt:
    st.markdown("### 🎵 محلل حسابات TikTok المتكامل")
    st.markdown(
        """
        <div class="info-box">
        تم دمج <strong>محلل الحسابات</strong> مع <strong>محقق TikTok</strong> في تبويبة واحدة.
        يمكنك الآن تحليل الحساب، واستنتاج الدولة من <code>region</code> و <code>locationCreated</code>،
        وتحليل المنطقة الزمنية، ثم عرض النتيجة النهائية على <strong>خريطة تفاعلية</strong> مع روابط تحقق جاهزة.
        </div>
        """,
        unsafe_allow_html=True,
    )

    input_col1, input_col2 = st.columns(2)
    with input_col1:
        tt_input = st.text_area(
            "أسماء حسابات TikTok أو الروابط المباشرة",
            value="""khaby.lame
charlidamelio
@bellapoarch
https://www.tiktok.com/@addisonre
zachking
""",
            height=230,
            key="tt_integrated_accounts_input",
            help="يقبل: username أو @username أو رابط الحساب الكامل",
        )
    with input_col2:
        integrated_video_input = st.text_area(
            "روابط فيديوهات TikTok لدعم تحديد الموقع",
            value="""https://www.tiktok.com/@noorstars/video/7518458932478725406
https://www.tiktok.com/@khaby.lame/video/7402695860712164641
""",
            height=230,
            key="tt_integrated_videos_input",
            help="اختياري لكنه يرفع دقة تحديد الموقع عبر locationCreated ووقت النشر",
        )

    usernames = extract_tiktok_usernames(tt_input)
    video_urls = extract_tiktok_video_urls(integrated_video_input)
    c_count1, c_count2, c_count3, c_count4 = st.columns(4)
    c_count1.metric("👤 الحسابات", len(usernames))
    c_count2.metric("🎬 الفيديوهات", len(video_urls))
    c_count3.metric("🗺️ الخريطة", "Folium" if FOLIUM_AVAILABLE else "غير مفعلة")
    c_count4.metric("📍 الموقع", "متكامل")

    b1, b2, b3 = st.columns(3)
    analyze_accounts_btn = b1.button("🚀 تحليل الحسابات", type="primary", use_container_width=True, key="tt_integrated_analyze_accounts")
    analyze_videos_btn = b2.button("📍 تحليل الفيديوهات", use_container_width=True, key="tt_integrated_analyze_videos")
    analyze_all_btn = b3.button("🧠 تشغيل التحليل المتكامل", use_container_width=True, key="tt_integrated_analyze_all")

    if analyze_accounts_btn or analyze_all_btn:
        if not usernames:
            st.error("❌ لم يتم العثور على أسماء حسابات TikTok صحيحة")
        else:
            progress = st.progress(0)
            status = st.empty()
            tt_results = []
            start = time.time()
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futures = {ex.submit(fetch_tiktok_profile, username): username for username in usernames}
                for idx, future in enumerate(as_completed(futures), start=1):
                    try:
                        tt_results.append(future.result())
                    except Exception as exc:
                        username = futures[future]
                        tt_results.append({"username": username, "status": "❌ فشل", "error": str(exc)})
                    progress.progress(idx / len(usernames))
                    status.text(f"⏳ تحليل الحسابات: {idx}/{len(usernames)}")
            progress.empty()
            status.empty()
            st.session_state["tt_results"] = sorted(tt_results, key=lambda row: row.get("username", ""))
            st.session_state["tt_elapsed"] = time.time() - start
            st.success(f"✅ تم تحليل {len(tt_results)} حساب TikTok")

    if analyze_videos_btn or analyze_all_btn:
        if not video_urls:
            if analyze_videos_btn or (analyze_all_btn and integrated_video_input.strip()):
                st.error("❌ لم يتم العثور على روابط فيديو TikTok صحيحة")
        else:
            progress_v = st.progress(0)
            status_v = st.empty()
            video_results = []
            start_v = time.time()
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futures = {ex.submit(analyze_tiktok_video, url): url for url in video_urls}
                for idx, future in enumerate(as_completed(futures), start=1):
                    try:
                        video_results.append(future.result())
                    except Exception as exc:
                        video_results.append({"video_url": futures[future], "status": "❌ فشل", "error": str(exc)})
                    progress_v.progress(idx / len(video_urls))
                    status_v.text(f"⏳ تحليل الفيديوهات: {idx}/{len(video_urls)}")
            progress_v.empty()
            status_v.empty()
            st.session_state["video_results"] = sorted(video_results, key=lambda row: row.get("username", ""))
            st.session_state["video_elapsed"] = time.time() - start_v
            st.success(f"✅ تم تحليل {len(video_results)} فيديو TikTok")

    tt_results = st.session_state.get("tt_results") or []
    video_results = st.session_state.get("video_results") or []
    geo_records = build_tiktok_geo_records(tt_results, video_results)
    st.session_state["tt_geo_records"] = geo_records

    sub_accounts, sub_geo, sub_map, sub_verify, sub_osint = st.tabs([
        "👤 تحليل الحسابات",
        "📍 استنتاج الموقع",
        "🗺️ الخريطة التفاعلية",
        "🔗 روابط التحقق",
        "🕵️ تحقيق TikTok",
    ])

    with sub_accounts:
        if not tt_results:
            st.info("ℹ️ ابدأ بتحليل حساب واحد على الأقل لعرض بيانات الحساب الكاملة هنا")
        else:
            df_tt = pd.DataFrame(tt_results)
            total = len(tt_results)
            success = sum(1 for r in tt_results if r.get("status") == "✅ نجح")
            verified = sum(1 for r in tt_results if r.get("verified"))
            private = sum(1 for r in tt_results if r.get("private_account"))
            with_region = sum(1 for r in tt_results if safe_int(r.get("region_confidence", 0)) >= min_confidence)
            total_followers = sum(safe_int(r.get("follower_count", 0)) for r in tt_results if r.get("status") == "✅ نجح")
            total_videos = sum(safe_int(r.get("video_count", 0)) for r in tt_results if r.get("status") == "✅ نجح")

            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("📋 الإجمالي", total)
            m2.metric("✅ ناجح", success)
            m3.metric("✓ موثّق", verified)
            m4.metric("🔒 خاص", private)
            m5.metric("🌍 له دولة", with_region)
            m6.metric("👥 المتابعون", tt_format_count(total_followers))
            st.caption(f"🎬 إجمالي الفيديوهات في الحسابات الناجحة: {tt_format_count(total_videos)}")

            if any(safe_int(r.get("region_confidence", 0)) >= min_confidence for r in tt_results):
                countries_data = [
                    f"{r.get('region_flag', '🌍')} {r.get('region_name_ar', '')}"
                    for r in tt_results
                    if safe_int(r.get("region_confidence", 0)) >= min_confidence and r.get("region_name_ar")
                ]
                if countries_data:
                    st.markdown(f"#### 🌍 توزيع الدول من بيانات الحساب (ثقة ≥ {min_confidence}%)")
                    st.bar_chart(pd.Series(countries_data).value_counts())

            display_cols = [
                "username", "nickname", "user_id", "sec_uid", "region_flag", "region_name_ar",
                "region_source", "region_confidence", "language_name_ar", "create_date",
                "follower_count_formatted", "follower_count", "following_count", "video_count",
                "heart_count_formatted", "verified", "private_account", "is_organization",
                "signature", "bio_link", "profile_url", "status", "error",
            ]
            display_cols = [col for col in display_cols if col in df_tt.columns]
            df_display = df_tt.copy()
            if "region_confidence" in df_display.columns:
                low_mask = df_display["region_confidence"].fillna(0).astype(int) < min_confidence
                for col in ["region_flag", "region_name_ar", "region_source"]:
                    if col in df_display.columns:
                        df_display.loc[low_mask, col] = ""

            st.dataframe(
                df_display[display_cols],
                use_container_width=True,
                height=520,
                column_config={
                    "profile_url": st.column_config.LinkColumn("🔗 الملف"),
                    "bio_link": st.column_config.LinkColumn("🔗 رابط البايو"),
                    "verified": st.column_config.CheckboxColumn("✓"),
                    "private_account": st.column_config.CheckboxColumn("🔒"),
                    "is_organization": st.column_config.CheckboxColumn("🏢"),
                    "follower_count": st.column_config.NumberColumn("👥 المتابعون", format="%d"),
                    "following_count": st.column_config.NumberColumn("➕ يتابع", format="%d"),
                    "video_count": st.column_config.NumberColumn("🎬 فيديوهات", format="%d"),
                    "region_confidence": st.column_config.ProgressColumn("الثقة %", min_value=0, max_value=100, format="%d%%"),
                    "signature": st.column_config.TextColumn("📝 البايو", width="large"),
                },
            )

            export_name = datetime.now().strftime("%Y%m%d_%H%M%S")
            ex1, ex2, ex3 = st.columns(3)
            ex1.download_button(
                "⬇️ CSV الحسابات",
                data=df_display.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"tiktok_integrated_accounts_{export_name}.csv",
                mime="text/csv",
                use_container_width=True,
                key="tt_integrated_accounts_csv",
            )
            ex2.download_button(
                "⬇️ JSON الحسابات",
                data=df_display.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8"),
                file_name=f"tiktok_integrated_accounts_{export_name}.json",
                mime="application/json",
                use_container_width=True,
                key="tt_integrated_accounts_json",
            )
            ex3.download_button(
                "⬇️ Excel الحسابات",
                data=results_to_excel(df_display.to_dict("records")),
                file_name=f"tiktok_integrated_accounts_{export_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="tt_integrated_accounts_excel",
            )

            st.markdown("#### 🎴 بطاقات مختصرة")
            cards = [row for row in tt_results if row.get("status") == "✅ نجح"][:9]
            if cards:
                cols = st.columns(3)
                for idx, row in enumerate(cards):
                    metrics = calculate_engagement_metrics(row)
                    with cols[idx % 3]:
                        with st.container(border=True):
                            if row.get("avatar_medium"):
                                try:
                                    st.image(row["avatar_medium"], width=90)
                                except Exception:
                                    pass
                            title = row.get("nickname") or row.get("username") or "TikTok"
                            flags = f" {row.get('region_flag', '')}" if row.get("region_flag") else ""
                            st.markdown(f"### {title}{' ✓' if row.get('verified') else ''}")
                            st.caption(f"@{row.get('username', '')}{flags}")
                            if row.get("region_name_ar") and safe_int(row.get("region_confidence", 0)) >= min_confidence:
                                st.caption(
                                    f"📍 {row.get('region_name_ar')} • {row.get('region_source', '')} ({row.get('region_confidence', 0)}%)"
                                )
                            c_a, c_b = st.columns(2)
                            c_a.metric("👥 متابعون", row.get("follower_count_formatted", "0"))
                            c_b.metric("❤️ إعجابات", row.get("heart_count_formatted", "0"))
                            c_a.metric("🎬 فيديوهات", f"{safe_int(row.get('video_count', 0)):,}")
                            c_b.metric("📊 التفاعل", f"{metrics.get('engagement_rate', 0)}%")
                            if row.get("signature"):
                                st.caption(row.get("signature", "")[:120])
                            if row.get("bio_link"):
                                st.markdown(f"[رابط البايو ↗]({row.get('bio_link')})")
                            if row.get("profile_url"):
                                st.markdown(f"[فتح الحساب ↗]({row.get('profile_url')})")

            # ═══════════════════════════════════════════════════════
            # 🗺️ خريطة تفاعلية مدمجة داخل تبويب الحسابات
            # ═══════════════════════════════════════════════════════
            accounts_with_geo = [
                r for r in tt_results
                if r.get("status") == "✅ نجح"
                and (r.get("region") or r.get("country_code"))
                and safe_int(r.get("region_confidence", r.get("country_confidence", 0))) >= min_confidence
            ]
            if accounts_with_geo:
                st.markdown("---")
                st.markdown("### 🗺️ خريطة تفاعلية — مواقع الحسابات المحللة")
                st.caption(f"يعرض {len(accounts_with_geo)} حساب تم تحديد دولتهم بثقة ≥ {min_confidence}%")

                if FOLIUM_AVAILABLE:
                    import folium as _folium
                    from streamlit_folium import st_folium as _st_folium

                    _fmap = _folium.Map(location=[25, 30], zoom_start=2,
                                        tiles="CartoDB positron", control_scale=True)

                    # Color-code markers by confidence
                    for _r in accounts_with_geo:
                        _code = (_r.get("region") or _r.get("country_code") or "").upper()
                        _coords = get_tiktok_region_center(_code) or get_country_coords(_code)
                        if not _coords:
                            continue
                        _lat, _lon = float(_coords[0]), float(_coords[1])
                        _conf = safe_int(_r.get("region_confidence", _r.get("country_confidence", 0)))
                        _flag, _name_ar = get_tiktok_country_meta(_code)
                        _nick = _r.get("nickname") or _r.get("username", "")
                        _followers = _r.get("follower_count_formatted") or tt_format_count(safe_int(_r.get("follower_count", 0)))
                        _verified = "✅ موثّق" if _r.get("verified") else ""
                        _private = "🔒 خاص" if _r.get("private_account") else ""
                        _source = _r.get("region_source") or _r.get("country_source") or ""
                        _profile_url = _r.get("profile_url") or f"https://www.tiktok.com/@{_r.get('username','')}"

                        # Marker color by confidence
                        if _conf >= 75:
                            _color = "green"
                        elif _conf >= 50:
                            _color = "orange"
                        else:
                            _color = "red"

                        _popup_html = (
                            f"<div dir='rtl' style='min-width:240px;font-family:Arial;'>"
                            f"<b style='font-size:15px'>@{html.escape(_r.get('username',''))}</b>"
                            f"{'&nbsp;✅' if _r.get('verified') else ''}<br>"
                            f"<span style='color:#555'>{html.escape(_nick)}</span><br><hr style='margin:4px 0'>"
                            f"<b>📍 الدولة:</b> {html.escape(_flag)} {html.escape(_name_ar)}<br>"
                            f"<b>🎯 الثقة:</b> {_conf}%<br>"
                            f"<b>🔎 المصدر:</b> {html.escape(_source)}<br>"
                            f"<b>👥 المتابعون:</b> {html.escape(_followers)}<br>"
                            f"<b>🎬 الفيديوهات:</b> {safe_int(_r.get('video_count',0)):,}<br>"
                            f"{_verified} {_private}<br>"
                            f"<a href='{_profile_url}' target='_blank' "
                            f"style='color:#ff0050;font-weight:bold;'>فتح الحساب ↗</a>"
                            f"</div>"
                        )
                        _folium.Marker(
                            location=[_lat, _lon],
                            tooltip=f"@{_r.get('username','')} · {_flag} {_name_ar} ({_conf}%)",
                            popup=_folium.Popup(_popup_html, max_width=300),
                            icon=_folium.Icon(color=_color, icon="user", prefix="fa"),
                        ).add_to(_fmap)

                    _st_folium(_fmap, width=None, height=520, key="tt_accounts_inline_map")

                    # Legend
                    _leg1, _leg2, _leg3 = st.columns(3)
                    _leg1.success("🟢 ثقة ≥ 75% — موثوق")
                    _leg2.warning("🟠 ثقة 50–74% — محتمل")
                    _leg3.error("🔴 ثقة < 50% — ضعيف")
                else:
                    # Fallback: show as st.map
                    _map_rows = []
                    for _r in accounts_with_geo:
                        _code = (_r.get("region") or _r.get("country_code") or "").upper()
                        _coords = get_tiktok_region_center(_code) or get_country_coords(_code)
                        if _coords:
                            _map_rows.append({"lat": float(_coords[0]), "lon": float(_coords[1])})
                    if _map_rows:
                        import pandas as _pd_map
                        st.map(_pd_map.DataFrame(_map_rows), zoom=1)
                    st.info("💡 ثبّت folium + streamlit-folium للحصول على خريطة تفاعلية كاملة")


    with sub_geo:
        if not geo_records:
            st.info("ℹ️ لا توجد إشارات كافية بعد. حلّل حسابات أو فيديوهات TikTok أولاً.")
        else:
            st.markdown(
                """
                <div class="info-box">
                يتم دمج 3 مصادر رئيسية: <strong>بيانات الحساب</strong>، <strong>موقع الفيديو</strong>، و<strong>المنطقة الزمنية</strong>.
                النتيجة النهائية تُعرض مع نسبة الثقة والأدلة وروابط الخرائط.
                </div>
                """,
                unsafe_allow_html=True,
            )
            geo_rows = []
            for record in geo_records:
                tz_candidates = []
                for code in record.get("timezone_candidates", [])[:4]:
                    flag, name = get_tiktok_country_meta(code)
                    tz_candidates.append(f"{flag} {name}")
                geo_rows.append({
                    "username": record.get("username", ""),
                    "الحساب": record.get("account_country_name_ar", "") or "—",
                    "ثقة الحساب": record.get("account_confidence", 0),
                    "الفيديو": record.get("video_country_name_ar", "") or "—",
                    "ثقة الفيديو": record.get("video_confidence", 0),
                    "أفضل توقيت": record.get("timezone_best", "—") or "—",
                    "الدول الزمنية": "، ".join(tz_candidates) if tz_candidates else "—",
                    "النتيجة النهائية": f"{record.get('final_flag', '🌍')} {record.get('final_country_name_ar', 'غير محدد')}",
                    "الثقة النهائية": record.get("final_confidence", 0),
                    "عدد الفيديوهات": record.get("matched_video_count", 0),
                    "الملف": record.get("profile_url", f"https://www.tiktok.com/@{record.get('username', '')}"),
                })

            df_geo = pd.DataFrame(geo_rows)
            st.dataframe(
                df_geo,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "الملف": st.column_config.LinkColumn("🔗 الحساب"),
                    "الثقة النهائية": st.column_config.ProgressColumn("الثقة النهائية", min_value=0, max_value=100, format="%d%%"),
                    "ثقة الحساب": st.column_config.ProgressColumn("ثقة الحساب", min_value=0, max_value=100, format="%d%%"),
                    "ثقة الفيديو": st.column_config.ProgressColumn("ثقة الفيديو", min_value=0, max_value=100, format="%d%%"),
                },
            )

            if video_results:
                successful_videos = [row for row in video_results if row.get("status") == "✅ نجح"]
                with_location = [row for row in successful_videos if row.get("location_created")]
                v1, v2, v3, v4 = st.columns(4)
                v1.metric("🎬 فيديوهات ناجحة", len(successful_videos))
                v2.metric("📍 لها locationCreated", len(with_location))
                v3.metric("👤 حسابات مرتبطة", len({normalize_tiktok_username(row.get('username')) for row in successful_videos if row.get('username')}))
                v4.metric("👁️ المشاهدات", tt_format_count(sum(safe_int(row.get("video_views", 0)) for row in successful_videos)))

            for record in geo_records:
                with st.container(border=True):
                    title_cols = st.columns([3, 1])
                    with title_cols[0]:
                        st.markdown(
                            f"### @{record.get('username', '')} — {record.get('final_flag', '🌍')} {record.get('final_country_name_ar', 'غير محدد')}"
                        )
                        st.caption(f"🎯 الثقة النهائية: {record.get('final_confidence', 0)}%")
                    with title_cols[1]:
                        if record.get("profile_url"):
                            st.link_button("فتح الحساب", record.get("profile_url"), use_container_width=True)

                    detail1, detail2, detail3 = st.columns(3)
                    detail1.metric("من الحساب", record.get("account_country_name_ar", "—") or "—", f"{record.get('account_confidence', 0)}%" if record.get('account_country_code') else None)
                    detail2.metric("من الفيديوهات", record.get("video_country_name_ar", "—") or "—", f"{record.get('video_confidence', 0)}%" if record.get('video_country_code') else None)
                    detail3.metric("أفضل توقيت", record.get("timezone_best", "—") or "—", f"{record.get('timezone_confidence', 0)}%" if record.get('timezone_best') else None)

                    if record.get("evidence"):
                        st.markdown("**الأدلة:**")
                        for item in record.get("evidence", []):
                            st.markdown(f"- {item}")

                    if record.get("signal_breakdown"):
                        st.caption(f"تفصيل الإشارات: {record.get('signal_breakdown')}")

                    point = record.get("geo_point")
                    if point:
                        st.caption(
                            f"📌 الإحداثيات: {point['lat']:.5f}, {point['lon']:.5f} — المصدر: {point.get('resolved_from', '')}"
                        )
                        map_links = record.get("map_links", {})
                        if map_links:
                            ml1, ml2, ml3, ml4 = st.columns(4)
                            with ml1:
                                st.link_button("Google Maps", map_links["google_maps"], use_container_width=True)
                            with ml2:
                                st.link_button("Yandex", map_links["yandex_maps"], use_container_width=True)
                            with ml3:
                                st.link_button("OpenStreetMap", map_links["openstreetmap"], use_container_width=True)
                            with ml4:
                                st.link_button("Apple Maps", map_links["apple_maps"], use_container_width=True)

            export_geo_name = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                "📥 تصدير تقرير الموقع JSON",
                data=json.dumps(geo_records, ensure_ascii=False, indent=2).encode("utf-8"),
                file_name=f"tiktok_integrated_geo_{export_geo_name}.json",
                mime="application/json",
                use_container_width=True,
                key="tt_integrated_geo_json",
            )

    with sub_map:
        if not geo_records:
            st.info("ℹ️ لا توجد بيانات كافية لرسم الخريطة بعد")
        else:
            st.markdown("#### 🗺️ خريطة TikTok التفاعلية")
            render_tiktok_interactive_map(
                [record for record in geo_records if record.get("final_country_code") and record.get("final_confidence", 0) >= max(20, min_confidence)],
                map_key="tt_integrated_map_view",
            )

            fallback_rows = []
            for record in geo_records:
                point = record.get("geo_point")
                if not point:
                    continue
                fallback_rows.append({
                    "المستخدم": record.get("username", ""),
                    "النتيجة": f"{record.get('final_flag', '🌍')} {record.get('final_country_name_ar', 'غير محدد')}",
                    "الثقة": record.get("final_confidence", 0),
                    "الإحداثيات": f"{point['lat']:.5f}, {point['lon']:.5f}",
                    "المصدر": point.get("resolved_from", ""),
                })
            if fallback_rows:
                st.markdown("#### 📋 نقاط الخريطة")
                st.dataframe(pd.DataFrame(fallback_rows), use_container_width=True, hide_index=True)

    with sub_verify:
        available_usernames = []
        seen_verify = set()
        for source in tt_results:
            username = normalize_tiktok_username(source.get("username"))
            if username and username.lower() not in seen_verify:
                seen_verify.add(username.lower())
                available_usernames.append(username)
        for source in video_results:
            username = normalize_tiktok_username(source.get("username"))
            if username and username.lower() not in seen_verify:
                seen_verify.add(username.lower())
                available_usernames.append(username)

        selected_username = st.selectbox(
            "اختر حساباً لروابط التحقق",
            options=[""] + available_usernames,
            key="tt_integrated_verify_select",
        )
        manual_verify_username = st.text_input("أو أدخل اسم مستخدم يدوياً", key="tt_integrated_verify_manual")
        verification_username = normalize_tiktok_username(manual_verify_username or selected_username)

        if verification_username:
            verification_links = build_tiktok_verification_links(verification_username)
            st.markdown(f"### 🔗 روابط التحقق لـ @{verification_username}")
            v1, v2, v3, v4, v5 = st.columns(5)
            with v1:
                st.link_button("TikTok", verification_links["tiktok_profile"], use_container_width=True)
            with v2:
                st.link_button("Wayback", verification_links["wayback"], use_container_width=True)
            with v3:
                st.link_button("Google", verification_links["google"], use_container_width=True)
            with v4:
                st.link_button("Yandex", verification_links["yandex"], use_container_width=True)
            with v5:
                st.link_button("Urlebird", verification_links["urlebird"], use_container_width=True)

            matching_record = next((record for record in geo_records if record.get("username", "").lower() == verification_username.lower()), None)
            if matching_record and matching_record.get("map_links"):
                st.markdown("#### 🗺️ روابط التحقق الجغرافي")
                map_links = matching_record["map_links"]
                ml1, ml2, ml3, ml4 = st.columns(4)
                with ml1:
                    st.link_button("Google Maps", map_links["google_maps"], use_container_width=True)
                with ml2:
                    st.link_button("Yandex Maps", map_links["yandex_maps"], use_container_width=True)
                with ml3:
                    st.link_button("OpenStreetMap", map_links["openstreetmap"], use_container_width=True)
                with ml4:
                    st.link_button("Apple Maps", map_links["apple_maps"], use_container_width=True)
        else:
            st.info("ℹ️ اختر حساباً أو أدخل اسم مستخدم لإظهار روابط التحقق")

    with sub_osint:
        st.markdown("### 🕵️ أدوات TikTok OSINT المدمجة")
        st.markdown(
            """
            <div class="info-box" dir="rtl">
            استخدم هذه الأدوات للبحث الجغرافي عن الأماكن والمعالم المرتبطة بالمحتوى،
            وبناء روابط بحث وتحقيق خارجية بسرعة، مع خريطة تفاعلية للموقع المستنتج.
            </div>
            """,
            unsafe_allow_html=True,
        )

        osint_available_usernames = []
        osint_seen = set()
        for source in tt_results:
            username = normalize_tiktok_username(source.get("username"))
            if username and username.lower() not in osint_seen:
                osint_seen.add(username.lower())
                osint_available_usernames.append(username)
        for source in video_results:
            username = normalize_tiktok_username(source.get("username"))
            if username and username.lower() not in osint_seen:
                osint_seen.add(username.lower())
                osint_available_usernames.append(username)

        preset_place = st.selectbox(
            "📌 مواقع مشهورة جاهزة",
            options=[""] + FAMOUS_LOCATIONS_TT,
            key="tt_osint_preset_place",
            help="يمكنك الاختيار من قائمة أماكن شائعة مرتبطة بعمليات التحقق على TikTok",
        )

        os1, os2, os3 = st.columns(3)
        with os1:
            place_query = st.text_input(
                "📍 اسم المكان أو المعلم",
                value=st.session_state.get("tt_osint_place_query", ""),
                key="tt_osint_place_query_input",
                placeholder="مثال: Riyadh Boulevard أو Times Square",
            )
        with os2:
            place_keywords = st.text_input(
                "🔎 كلمات مفتاحية إضافية",
                value=st.session_state.get("tt_osint_keywords", ""),
                key="tt_osint_keywords_input",
                placeholder="حفلة، مطعم، شارع، event",
            )
        with os3:
            selected_osint_username = st.selectbox(
                "👤 اسم المستخدم للتحقق",
                options=[""] + osint_available_usernames,
                key="tt_osint_username_select",
            )

        manual_osint_username = st.text_input(
            "أو أدخل اسم مستخدم TikTok يدوياً",
            key="tt_osint_username_manual",
            placeholder="username",
        )

        active_place = (place_query or preset_place or "").strip()
        active_keywords = (place_keywords or "").strip()
        active_username = normalize_tiktok_username(manual_osint_username or selected_osint_username)

        oa, ob = st.columns(2)
        run_place_osint = oa.button(
            "🚀 تشغيل تحقيق المكان",
            type="primary",
            use_container_width=True,
            key="tt_osint_run_place",
        )
        clear_place_osint = ob.button(
            "🗑️ مسح نتيجة التحقيق",
            use_container_width=True,
            key="tt_osint_clear_place",
        )

        if preset_place and preset_place != st.session_state.get("tt_osint_place_query", ""):
            st.session_state["tt_osint_place_query"] = preset_place

        if clear_place_osint:
            st.session_state["tt_osint_place_result"] = None
            st.session_state["tt_osint_place_query"] = ""
            st.session_state["tt_osint_keywords"] = ""
            st.rerun()

        if run_place_osint:
            if not active_place:
                st.error("❌ أدخل اسم مكان أو اختر موقعاً جاهزاً أولاً")
            else:
                geo_result = geocode_tiktok_place(active_place, lang="ar") or geocode_tiktok_place(active_place, lang="en")
                search_links = build_tiktok_search_links(active_place, active_keywords, geo_result)
                verification_links = build_tiktok_verification_links(active_username) if active_username else {}
                st.session_state["tt_osint_place_result"] = {
                    "place": active_place,
                    "keywords": active_keywords,
                    "username": active_username,
                    "geo_result": geo_result,
                    "search_links": search_links,
                    "verification_links": verification_links,
                    "map_links": build_tt_map_links(geo_result["lat"], geo_result["lon"]) if geo_result else {},
                }
                st.session_state["tt_osint_place_query"] = active_place
                st.session_state["tt_osint_keywords"] = active_keywords

        tt_osint_result = st.session_state.get("tt_osint_place_result")
        if tt_osint_result:
            geo_result = tt_osint_result.get("geo_result") or {}
            search_links = tt_osint_result.get("search_links") or {}
            verification_links = tt_osint_result.get("verification_links") or {}
            map_links = tt_osint_result.get("map_links") or {}
            st.markdown(f"#### 📌 نتيجة التحقيق للمكان: {tt_osint_result.get('place', '')}")

            r1, r2, r3, r4 = st.columns(4)
            r1.metric("📍 المكان", tt_osint_result.get("place", "—") or "—")
            r2.metric("🧭 الإحداثيات", f"{geo_result.get('lat', 0):.4f}, {geo_result.get('lon', 0):.4f}" if geo_result else "غير متاح")
            r3.metric("🌍 الدولة", geo_result.get("country", "غير معروفة") if geo_result else "غير معروفة")
            r4.metric("👤 المستخدم", f"@{tt_osint_result.get('username')}" if tt_osint_result.get("username") else "غير محدد")

            st.markdown("#### 🔎 روابط البحث على TikTok ومحركات البحث")
            link_cols = st.columns(3)
            with link_cols[0]:
                st.link_button("TikTok Search", search_links.get("general_search", "https://www.tiktok.com/search"), use_container_width=True)
            with link_cols[1]:
                st.link_button("Hashtag Search", search_links.get("hashtag_search", "https://www.tiktok.com/discover"), use_container_width=True)
            with link_cols[2]:
                st.link_button("Google Site Search", search_links.get("regional_search", "https://www.google.com"), use_container_width=True)

            if verification_links:
                st.markdown("#### ✅ روابط التحقق من الحساب")
                verify_cols = st.columns(5)
                with verify_cols[0]:
                    st.link_button("TikTok", verification_links.get("tiktok_profile", "https://www.tiktok.com"), use_container_width=True)
                with verify_cols[1]:
                    st.link_button("Wayback", verification_links.get("wayback", "https://web.archive.org"), use_container_width=True)
                with verify_cols[2]:
                    st.link_button("Google", verification_links.get("google", "https://www.google.com"), use_container_width=True)
                with verify_cols[3]:
                    st.link_button("Yandex", verification_links.get("yandex", "https://yandex.com"), use_container_width=True)
                with verify_cols[4]:
                    st.link_button("Urlebird", verification_links.get("urlebird", "https://urlebird.com"), use_container_width=True)

            if geo_result:
                st.markdown("#### 🗺️ روابط الخرائط")
                map_cols = st.columns(4)
                with map_cols[0]:
                    st.link_button("Google Maps", map_links.get("google_maps", search_links.get("maps", {}).get("google_maps", "https://www.google.com/maps")), use_container_width=True)
                with map_cols[1]:
                    st.link_button("Yandex Maps", map_links.get("yandex_maps", search_links.get("maps", {}).get("yandex_maps", "https://yandex.com/maps")), use_container_width=True)
                with map_cols[2]:
                    st.link_button("OpenStreetMap", map_links.get("openstreetmap", search_links.get("maps", {}).get("openstreetmap", "https://www.openstreetmap.org")), use_container_width=True)
                with map_cols[3]:
                    st.link_button("Apple Maps", map_links.get("apple_maps", search_links.get("maps", {}).get("apple_maps", "https://maps.apple.com")), use_container_width=True)

                if FOLIUM_AVAILABLE:
                    place_map = folium.Map(
                        location=[geo_result["lat"], geo_result["lon"]],
                        zoom_start=12,
                        tiles="CartoDB positron",
                        control_scale=True,
                    )
                    popup_html = (
                        f"<div dir='rtl' style='min-width:220px'>"
                        f"<b>{html.escape(tt_osint_result.get('place', ''))}</b><br>"
                        f"🌍 {html.escape(str(geo_result.get('country', 'غير معروفة')))}<br>"
                        f"📌 {html.escape(str(geo_result.get('display_name', '')))}</div>"
                    )
                    folium.Marker(
                        location=[geo_result["lat"], geo_result["lon"]],
                        tooltip=tt_osint_result.get("place", "TikTok OSINT"),
                        popup=folium.Popup(popup_html, max_width=320),
                        icon=folium.Icon(color="red", icon="info-sign"),
                    ).add_to(place_map)
                    st_folium(place_map, width=None, height=420, key="tt_osint_place_map")
                else:
                    st.info("💡 لتفعيل الخريطة التفاعلية ثبّت: folium + streamlit-folium")
            else:
                st.warning("⚠️ تعذّر تحديد إحداثيات المكان. ما زالت روابط البحث النصي متاحة.")

            st.download_button(
                "📥 تنزيل نتيجة TikTok OSINT بصيغة JSON",
                data=json.dumps(tt_osint_result, ensure_ascii=False, indent=2).encode("utf-8"),
                file_name=f"tiktok_osint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
                key="tt_osint_download_json",
            )
        else:
            st.caption("ابدأ بإدخال مكان أو اختيار موقع مشهور ثم اضغط تشغيل تحقيق المكان.")

# ============ تبويب تحليل فيديو تيك توك (الجديد) ============
with tab_video:
    st.markdown("### 🎬 تحليل فيديو TikTok - الحل الذهبي للموقع!")
    st.markdown(
        """
        <div class="info-box">
        <strong>🔥 الحل الأفضل لمعرفة موقع حساب TikTok!</strong><br>
        بدلاً من تحليل البروفايل (الذي يحجب الموقع)، ألصق <strong>روابط فيديو مباشرة</strong>.<br>
        كل فيديو يحوي حقل <code>locationCreated</code> الذي يعكس <strong>مكان التصوير الفعلي</strong>.<br>
        دقة النتيجة: <strong>عالية جداً!</strong> 🎯
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### 💡 كيف تستخدم هذه الميزة:")
    st.markdown("""
    1. افتح بروفايل الحساب على TikTok في المتصفح
    2. اضغط على أي فيديو لفتحه
    3. انسخ رابط الفيديو والصقه هنا (أو عدة روابط، سطر لكل فيديو)
    4. دع المحلل يعمل عمله ✨
    """)

    video_urls_input = st.text_area(
        "ألصق روابط فيديوهات TikTok (رابط لكل سطر):",
        value="""https://www.tiktok.com/@noorstars/video/7518458932478725406
https://www.tiktok.com/@khaby.lame/video/7402695860712164641
""",
        height=200,
        key="video_urls_input",
    )

    col_v1, col_v2 = st.columns([3, 1])
    with col_v2:
        live_video_count = len([l for l in video_urls_input.splitlines() if l.strip() and 'tiktok.com' in l.lower()])
        st.metric("🎬 عدد الفيديوهات", live_video_count)

    if st.button("🚀 تحليل الفيديوهات + مواقعها", type="primary", use_container_width=True, key="video_analyze"):
        # استخراج الروابط
        video_urls = []
        for line in video_urls_input.splitlines():
            line = line.strip()
            if line and 'tiktok.com' in line.lower() and '/video/' in line:
                video_urls.append(line)

        if not video_urls:
            st.error("❌ لم يتم العثور على روابط فيديو صحيحة")
        else:
            st.info(f"🔄 جارٍ تحليل **{len(video_urls)}** فيديو...")
            progress = st.progress(0)
            status = st.empty()
            start = time.time()

            video_results = []
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futures = {ex.submit(analyze_tiktok_video, url): url for url in video_urls}
                done = 0
                for f in as_completed(futures):
                    try:
                        video_results.append(f.result())
                    except Exception as e:
                        video_results.append({"video_url": futures[f], "status": "❌", "error": str(e)})
                    done += 1
                    progress.progress(done / len(video_urls))
                    status.text(f"⏳ {done}/{len(video_urls)}")

            elapsed = time.time() - start
            progress.empty()
            status.empty()
            st.session_state["video_results"] = video_results
            st.success(f"✅ تم تحليل {len(video_results)} فيديو في {elapsed:.1f} ثانية!")

    # عرض نتائج الفيديوهات
    if "video_results" in st.session_state and st.session_state["video_results"]:
        v_results = st.session_state["video_results"]
        df_v = pd.DataFrame(v_results)

        st.markdown("---")
        st.markdown("## 📊 نتائج تحليل الفيديوهات")

        # إحصائيات
        total_v = len(v_results)
        success_v = sum(1 for r in v_results if r.get("status") == "✅ نجح")
        with_loc = sum(1 for r in v_results if r.get("location_created"))
        total_views = sum(r.get("video_views", 0) for r in v_results if r.get("status") == "✅ نجح")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🎬 الإجمالي", total_v)
        c2.metric("✅ ناجح", success_v)
        c3.metric("📍 له موقع", with_loc)
        c4.metric("👁️ إجمالي المشاهدات", tt_format_count(total_views))

        # توزيع المواقع
        if with_loc > 0:
            st.markdown("#### 🌍 توزيع أماكن التصوير")
            loc_data = [f"{r['location_flag']} {r['location_name_ar']}" for r in v_results if r.get("location_created")]
            if loc_data:
                loc_counts = pd.Series(loc_data).value_counts()
                col_chart, col_list = st.columns([2, 1])
                with col_chart:
                    st.bar_chart(loc_counts)
                with col_list:
                    st.markdown("**أكثر الأماكن:**")
                    for loc, count in loc_counts.head(10).items():
                        st.markdown(f"- {loc}: **{count}**")

        # تجميع حسب الحساب - لرؤية موقع كل حساب
        st.markdown("#### 👤 تجميع حسب الحساب (الموقع الأكثر تكراراً)")
        if success_v > 0:
            users_locations = {}
            for r in v_results:
                if r.get("status") == "✅ نجح":
                    u = r.get("username", "")
                    loc = r.get("location_created", "")
                    if u not in users_locations:
                        users_locations[u] = {"locations": [], "data": r}
                    if loc:
                        users_locations[u]["locations"].append(loc)

            for u, info in users_locations.items():
                if info["locations"]:
                    locs = info["locations"]
                    most_common = max(set(locs), key=locs.count)
                    flag = TIKTOK_REGION_MAP.get(most_common, ("🌍", most_common))[0]
                    name = TIKTOK_REGION_MAP.get(most_common, ("", most_common))[1]
                    count = locs.count(most_common)
                    st.markdown(f"**@{u}**: {flag} **{name}** ({count}/{len(locs)} فيديو)")
                    if len(set(locs)) > 1:
                        st.caption(f"أماكن أخرى: {', '.join(set(locs) - {most_common})}")

        # جدول الفيديوهات
        st.markdown("#### 📋 جدول الفيديوهات")
        v_cols = [
            "username", "author_nickname", "location_flag", "location_name_ar",
            "location_created", "text_language", "create_date",
            "video_views", "video_likes", "video_comments",
            "author_id", "author_verified", "video_desc", "video_url", "status",
        ]
        v_cols = [c for c in v_cols if c in df_v.columns]

        st.dataframe(
            df_v[v_cols], use_container_width=True, height=400,
            column_config={
                "video_url": st.column_config.LinkColumn("🔗 الفيديو"),
                "author_verified": st.column_config.CheckboxColumn("✓"),
                "location_flag": st.column_config.TextColumn("🚩", width="small"),
                "location_name_ar": st.column_config.TextColumn("🌍 الموقع"),
                "location_created": st.column_config.TextColumn("رمز", width="small"),
                "video_views": st.column_config.NumberColumn("👁️ مشاهدات", format="%d"),
                "video_likes": st.column_config.NumberColumn("❤️ إعجابات", format="%d"),
                "video_comments": st.column_config.NumberColumn("💬 تعليقات", format="%d"),
                "author_id": st.column_config.TextColumn("🆔 ID المؤلف"),
                "video_desc": st.column_config.TextColumn("📝 الوصف", width="large"),
            },
        )

        # تصدير
        timestamp_v = datetime.now().strftime("%Y%m%d_%H%M%S")
        ev1, ev2, ev3 = st.columns(3)
        csv_v = df_v.to_csv(index=False).encode("utf-8-sig")
        ev1.download_button("⬇️ CSV", data=csv_v,
                            file_name=f"tiktok_videos_{timestamp_v}.csv",
                            mime="text/csv", use_container_width=True)
        json_v = df_v.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8")
        ev2.download_button("⬇️ JSON", data=json_v,
                            file_name=f"tiktok_videos_{timestamp_v}.json",
                            mime="application/json", use_container_width=True)
        excel_v = results_to_excel(df_v.to_dict("records"))
        ev3.download_button("⬇️ Excel", data=excel_v,
                            file_name=f"tiktok_videos_{timestamp_v}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True)


# ============ تبويب تحليل تغريدات X ============
with tab_x:
    st.markdown("### 🐦 محلل تغريدات X v4 - محرك ذكي 7 طبقات + AI Vision! 🧠")
    st.markdown(
        """
        <div class="info-box">
        <strong>🔥 محرك كشف الدولة الجذري (7 طبقات):</strong><br>
        • 📍 <strong>طبقة 1: حقل الموقع الرسمي</strong> (ثقة 90-95%) — "الرياض"، "Oslo, Norway"<br>
        • 🏳️ <strong>طبقة 2: الأعلام في البايو/الاسم</strong> (ثقة 70-80%)<br>
        • 🏛️ <strong>طبقة 3: تحليل السياق (انتماء/سفر)</strong> — "مصاب بالعراق" = انتماء<br>
        • 📝 <strong>طبقة 4: مدن في البايو/الاسم</strong> (ثقة 65-75%)<br>
        • 🖼️ <strong>طبقة 5: AI Vision للصور</strong> — معالم، لوحات سيارات، لباس تقليدي (ثقة 65-75%)<br>
        • 📄 <strong>طبقة 6: نص التغريدة</strong> (ثقة إضافية 35-40%)<br>
        • 🔬 <strong>طبقة 7: دمج وأوزان</strong> — ثقة نهائية تصل لـ 95%<br>
        ✅ <strong>بيانات تحدث: User ID دائم + تغريدة كاملة + صور + إحصائيات + توثيق</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # تحذير دقة الموقع
    st.markdown(
        """
        <div class="warn-box">
        ⚠️ <strong>ملاحظة مهمة عن دقة الموقع:</strong><br>
        • <strong>حقل الموقع الرسمي</strong> = أدق طريقة (يدخله المستخدم بنفسه) — دقة 90-95%<br>
        • <strong>تحليل نص التغريدة</strong> = قد يخطئ إذا تكلم المستخدم عن دولة أخرى<br>
        • ميزة "About this account" من X (نوفمبر 2025) قد تظهر منطقة عامة (مثل "North America") بناءً على IP<br>
        • مثال: حساب @salim_Aljomaili → الموقع الرسمي "England, UK" 🇬🇧 (عراقي مغترب)
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### 💡 ألصق روابط تغريدات X / Twitter (رابط لكل سطر):")

    x_urls_input = st.text_area(
        "روابط التغريدات:",
        value="""https://x.com/elonmusk/status/1874342693310259604
https://x.com/SaudiMOH/status/1941171425823576458
https://twitter.com/elonmusk/status/2007910921914769832
""",
        height=200,
        key="x_urls_input",
        help="يدعم: x.com و twitter.com",
    )

    col_x1, col_x2 = st.columns([3, 1])
    with col_x2:
        live_x_count = len([l for l in x_urls_input.splitlines() 
                            if l.strip() and ('x.com' in l.lower() or 'twitter.com' in l.lower())])
        st.metric("🐦 عدد التغريدات", live_x_count)

    if st.button("🚀 تحليل التغريدات", type="primary", use_container_width=True, key="x_analyze"):
        x_urls = []
        for line in x_urls_input.splitlines():
            line = line.strip()
            if line and ('x.com' in line.lower() or 'twitter.com' in line.lower()):
                x_urls.append(line)

        if not x_urls:
            st.error("❌ لم يتم العثور على روابط صحيحة")
        else:
            st.info(f"🔄 جارٍ تحليل **{len(x_urls)}** تغريدة...")
            progress = st.progress(0)
            status = st.empty()
            start = time.time()

            x_results = []
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                vc = get_vision_callback()
                if vc:
                    st.info("🧠 AI Vision مفعل — سيتم تحليل صور التغريدات (وقت أطول)")
                futures = {ex.submit(analyze_x_tweet, url, vision_callback=vc): url for url in x_urls}
                done = 0
                for f in as_completed(futures):
                    try:
                        x_results.append(f.result())
                    except Exception as e:
                        x_results.append({"tweet_url": futures[f], "status": "❌", "error": str(e)})
                    done += 1
                    progress.progress(done / len(x_urls))
                    status.text(f"⏳ {done}/{len(x_urls)}")

            elapsed = time.time() - start
            progress.empty()
            status.empty()
            st.session_state["x_results"] = x_results
            st.success(f"✅ تم تحليل {len(x_results)} تغريدة في {elapsed:.1f} ثانية!")

    # عرض النتائج
    if "x_results" in st.session_state and st.session_state["x_results"]:
        x_results = st.session_state["x_results"]
        df_x = pd.DataFrame(x_results)

        st.markdown("---")
        st.markdown("## 📊 نتائج تحليل تغريدات X")

        # الإحصائيات
        total_x = len(x_results)
        success_x = sum(1 for r in x_results if r.get("status") == "✅ نجح")
        with_country_x = sum(1 for r in x_results if r.get("region") and r.get("region_confidence", 0) >= 30)
        verified_x = sum(1 for r in x_results if r.get("user_blue_verified") or r.get("user_verified"))
        total_likes = sum(r.get("favorite_count", 0) for r in x_results if r.get("status") == "✅ نجح")
        total_replies = sum(r.get("conversation_count", 0) for r in x_results if r.get("status") == "✅ نجح")

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("🐦 الإجمالي", total_x)
        c2.metric("✅ ناجح", success_x)
        c3.metric("🌍 له دولة", with_country_x)
        c4.metric("✓ موثّق", verified_x)
        c5.metric("❤️ إجمالي الإعجابات", tt_format_count(total_likes))
        c6.metric("💬 إجمالي الردود", tt_format_count(total_replies))

        # 🎯 الميزة الذهبية: تجميع ذكي لنفس المستخدم
        users_aggregated = aggregate_user_tweets(x_results, min_confidence=30)

        if len(users_aggregated) > 0:
            st.markdown("#### 🎯 تحليل موحد حسب الحساب (تصويت ذكي)")
            st.info(
                "💡 عندما تحلل عدة تغريدات لنفس الحساب، نستخدم نظام التصويت لتحديد موقعه الفعلي. "
                "الدولة الأكثر تكراراً = موقع المستخدم. الذكر العابر لدولة في تغريدة واحدة = تجاهل."
            )

            for key, ud in users_aggregated.items():
                with st.container(border=True):
                    cu1, cu2 = st.columns([1, 4])
                    with cu1:
                        if ud.get("user_profile_image"):
                            try:
                                st.image(ud["user_profile_image"], width=80)
                            except Exception:
                                pass
                    with cu2:
                        verified = " ✓" if ud.get("user_blue_verified") else ""
                        vtype = f" ({ud['user_verified_type']})" if ud.get("user_verified_type") else ""
                        st.markdown(f"### {ud.get('user_name', '')}{verified}{vtype}")
                        st.caption(f"@{ud.get('user_screen_name', '')} • ID: `{ud.get('user_id', '')}`")

                        # 📍 حقل الموقع الرسمي
                        if ud.get("location_field"):
                            st.markdown(
                                f"📍 <strong>حقل الموقع الرسمي:</strong> <code>{ud['location_field']}</code>",
                                unsafe_allow_html=True
                            )
                        # 📝 البايو المختصر
                        if ud.get("user_bio"):
                            bio_short = ud['user_bio'][:120]
                            st.caption(f"📝 {bio_short}" + ("..." if len(ud['user_bio']) > 120 else ""))

                        # القرار النهائي
                        if ud.get("final_region"):
                            flag = ud.get("final_region_flag", "")
                            name = ud.get("final_region_name_ar", "")
                            conf = ud.get("final_confidence", 0)
                            method = ud.get("final_method", "")
                            st.success(
                                f"### {flag} **{name}** — ثقة {conf}%"
                            )
                            st.caption(f"📝 {method}")
                            if ud.get("final_evidence"):
                                st.caption(f"🔍 {ud['final_evidence']}")
                        else:
                            st.warning("❓ لم يتم تحديد دولة بثقة كافية")
                            if ud.get("final_evidence"):
                                st.caption(f"📝 الأدلة المتوفرة: {ud['final_evidence']}")

                        # إحصائيات سريعة
                        cs1, cs2, cs3, cs4 = st.columns(4)
                        cs1.metric("🐦 تغريدات", ud.get("tweet_count", 0))
                        cs2.metric("❤️ إجمالي", tt_format_count(ud.get("total_likes", 0)))
                        cs3.metric("💬 ردود", tt_format_count(ud.get("total_replies", 0)))
                        cs4.metric("🌐 لغة", ud.get("dominant_language", "-"))

            st.markdown("---")

        # 📸 عرض نتائج AI Vision (إن توفرت)
        ai_results = [r for r in x_results if r.get("image_findings")]
        if ai_results:
            with st.expander(f"🧠 نتائج تحليل الصور بالذكاء الاصطناعي ({len(ai_results)} تغريدة)", expanded=False):
                for r in ai_results:
                    st.markdown(f"**@{r.get('user_screen_name')}** - [التغريدة]({r.get('tweet_url')})")
                    for f in r.get("image_findings", []):
                        code = f.get("country_code", "?")
                        info = X_REGION_MAP.get(code, {})
                        st.markdown(
                            f"  - {info.get('flag', '?')} **{info.get('ar', code)}** — {f.get('description', '')}"
                        )
                    st.markdown("---")

        # 🔍 عرض أدلة مفصلة لكل تغريدة
        with st.expander("🔍 الأدلة المفصلة وسبب الكشف (لكل تغريدة)", expanded=False):
            for r in x_results:
                if not r.get("all_evidence"):
                    continue
                st.markdown(
                    f"**@{r.get('user_screen_name', '?')}** → "
                    f"{r.get('region_flag', '?')} {r.get('region_name_ar', '?')} "
                    f"({r.get('region_confidence', 0)}%)"
                )
                for ev in r.get("all_evidence", [])[:5]:
                    st.caption(f"  • {ev}")
                st.markdown("---")

        # توزيع الدول (التغريدات الفردية)
        countries_x = [
            f"{r['region_flag']} {r['region_name_ar']}" for r in x_results
            if r.get("region") and r.get("region_confidence", 0) >= 30
        ]
        if countries_x:
            st.markdown("#### 🌍 توزيع الدول في التغريدات الفردية")
            st.caption("⚠️ هذه الدول لمواضيع التغريدات، ليس بالضرورة موقع المستخدم")
            x_country_counts = pd.Series(countries_x).value_counts()
            cl, cr = st.columns([2, 1])
            with cl:
                st.bar_chart(x_country_counts)
            with cr:
                st.markdown("**الدول المذكورة:**")
                for c, n in x_country_counts.head(10).items():
                    st.markdown(f"- {c}: **{n}**")

        # الجدول
        st.markdown("#### 📋 جدول التغريدات")
        x_cols = [
            "user_screen_name", "user_name", "user_id",
            "user_location_field",
            "region_flag", "region_name_ar", "region_confidence",
            "region_evidence",
            "used_image_ai",
            "lang_name_ar", "created_at",
            "favorite_count", "conversation_count", "media_count", "media_type",
            "user_blue_verified",
            "text", "hashtags", "mentions", "tweet_url", "status",
        ]
        x_cols = [c for c in x_cols if c in df_x.columns]

        st.dataframe(
            df_x[x_cols], use_container_width=True, height=400,
            column_config={
                "tweet_url": st.column_config.LinkColumn("🔗 الرابط"),
                "user_blue_verified": st.column_config.CheckboxColumn("✓"),
                "user_id": st.column_config.TextColumn("🆔 User ID"),
                "user_screen_name": st.column_config.TextColumn("@يوزر"),
                "user_name": st.column_config.TextColumn("الاسم"),
                "user_location_field": st.column_config.TextColumn("📍 حقل الموقع الرسمي", width="medium"),
                "region_evidence": st.column_config.TextColumn("🔍 دليل الكشف", width="medium"),
                "used_image_ai": st.column_config.TextColumn("🧠 AI", width="small", help="هل تم تحليل صورة التغريدة؟"),
                "region_flag": st.column_config.TextColumn("🚩", width="small"),
                "region_name_ar": st.column_config.TextColumn("الدولة"),
                "region_confidence": st.column_config.ProgressColumn(
                    "ثقة", min_value=0, max_value=100, format="%d%%",
                ),
                "favorite_count": st.column_config.NumberColumn("❤️", format="%d"),
                "conversation_count": st.column_config.NumberColumn("💬", format="%d"),
                "media_count": st.column_config.NumberColumn("🖼️", format="%d"),
                "text": st.column_config.TextColumn("📝 النص", width="large"),
                "created_at": st.column_config.TextColumn("📅 التاريخ"),
            },
        )

        # 🗺️ خريطة X
        x_map_records = [
            r for r in x_results
            if r.get("status") == "✅ نجح" and r.get("region") and safe_int(r.get("region_confidence", 0)) >= 30 and get_country_coords(r.get("region"))
        ]
        if x_map_records:
            create_country_map(
                x_map_records,
                country_key="region",
                confidence_key="region_confidence",
                title="🗺️ خريطة نتائج X (Twitter)",
                popup_builder=lambda r: (
                    f"<div dir='rtl'><b>@{html.escape(str(r.get('user_screen_name', '')))}</b><br>"
                    f"{html.escape(str(r.get('region_flag', '')))} {html.escape(str(r.get('region_name_ar', '')))}<br>"
                    f"❤️ {html.escape(str(r.get('favorite_count', 0)))} • 💬 {html.escape(str(r.get('conversation_count', 0)))}</div>"
                ),
                map_key="x_tweets_map",
                threshold=30,
            )

        # تصدير
        st.markdown("#### 📥 تصدير")
        ts_x = datetime.now().strftime("%Y%m%d_%H%M%S")
        ex1, ex2, ex3 = st.columns(3)
        csv_x = df_x.to_csv(index=False).encode("utf-8-sig")
        ex1.download_button("⬇️ CSV", data=csv_x,
                            file_name=f"x_tweets_{ts_x}.csv",
                            mime="text/csv", use_container_width=True)
        json_x = df_x.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8")
        ex2.download_button("⬇️ JSON", data=json_x,
                            file_name=f"x_tweets_{ts_x}.json",
                            mime="application/json", use_container_width=True)
        excel_x = results_to_excel(df_x.to_dict("records"))
        ex3.download_button("⬇️ Excel", data=excel_x,
                            file_name=f"x_tweets_{ts_x}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True)

        # بطاقات بصرية للتغريدات
        successful_x = [r for r in x_results if r.get("status") == "✅ نجح"][:9]
        if successful_x:
            st.markdown("#### 🎴 بطاقات التغريدات")
            cols = st.columns(3)
            for i, t in enumerate(successful_x):
                with cols[i % 3]:
                    with st.container(border=True):
                        # الرأس: صورة + الاسم
                        col_img, col_info = st.columns([1, 3])
                        with col_img:
                            if t.get("user_profile_image"):
                                try:
                                    st.image(t["user_profile_image"], width=50)
                                except Exception:
                                    pass
                        with col_info:
                            verified = " ✓" if t.get("user_blue_verified") else ""
                            vtype = f" ({t['user_verified_type']})" if t.get("user_verified_type") else ""
                            st.markdown(f"**{t.get('user_name', '')}{verified}**{vtype}")
                            flag = t.get("region_flag", "")
                            st.caption(f"@{t.get('user_screen_name', '')} {flag}")
                        # النص
                        if t.get("text"):
                            st.markdown(t["text"][:280])
                        # الوسائط
                        if t.get("media_count", 0) > 0 and t.get("media_urls"):
                            first_media = t["media_urls"].split(" | ")[0]
                            if first_media and "video" not in first_media:
                                try:
                                    st.image(first_media, width=200)
                                except Exception:
                                    pass
                        # الإحصائيات
                        st.caption(
                            f"❤️ {t.get('favorite_count_formatted', '0')} | "
                            f"💬 {t.get('conversation_count_formatted', '0')} | "
                            f"📅 {t.get('created_at', '')[:10]}"
                        )
                        if t.get("region_name_ar") and t.get("region_confidence", 0) >= 30:
                            st.caption(
                                f"🌍 {t['region_name_ar']} "
                                f"({t['region_confidence']}% - {t['region_source']})"
                            )
                        st.markdown(f"[🔗 فتح في X]({t.get('tweet_url', '')})")


# ============ 🌍 تبويب تحليل موقع المنشور + كاشف VPN — الأقوى! ============
with tab_postloc:
    st.markdown("### 🌍 تحديد موقع المنشور + كاشف VPN — تحليل بصري عميق 🧠")
    st.markdown(
        """
        <div class="info-box">
        <strong>🔥 الفرق الجوهري:</strong> هذا التبويب يحدد <strong>موقع تصوير المنشور الفعلي</strong>
        (وليس ما يدّعيه الحساب في بروفايله)!
        <ul>
        <li>🛰️ <strong>EXIF GPS</strong>: الدقة القصوى 100% — يستخرج إحداثيات فعلية إن وجدت</li>
        <li>🤖 <strong>Gemini Vision (GEO-Detective)</strong>: تحليل بصري 5 فئات (معمار، بنية تحتية، بيئة، تخطيط، لافتات)</li>
        <li>🚨 <strong>كاشف VPN</strong>: يقارن موقع الحساب مع موقع التصوير → التناقض = احتمال VPN</li>
        <li>🏛️ يكتشف: معالم، لوحات سيارات، لافتات، لباس تقليدي، علامات تجارية محلية</li>
        </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # اختيار وضع التحليل
    st.markdown("#### 📝 وضع التحليل")
    pl_mode = st.radio(
        "اختر طريقة الإدخال:",
        [
            "🔗 روابط منشورات X (تحليل صور + كشف VPN)",
            "🖼️ رفع صورة مباشرة لتحديد موقعها",
            "🔗 روابط صور مباشرة",
        ],
        horizontal=False,
        key="pl_mode",
    )

    # تحقق من API key
    api_key_for_post = (
        os.environ.get("GEMINI_API_KEY")
        or st.session_state.get("gemini_api_key")
    )

    if not api_key_for_post:
        st.warning(
            "⚠️ تحتاج **Gemini API Key** لتفعيل تحليل الصور. "
            "احصل عليه مجاناً من: https://aistudio.google.com/apikey"
        )
        new_key = st.text_input(
            "أدخل Gemini API Key:",
            type="password",
            key="gemini_api_key_postloc",
        )
        if new_key:
            st.session_state["gemini_api_key"] = new_key
            api_key_for_post = new_key
            st.rerun()
    else:
        st.success("✅ Gemini API مفعل — جاهز للتحليل!")

    # ✅ رسالة إعلامية - لا حاجة لـ cookies!
    st.markdown(
        """
        <div style="background: #d1fae5; border-right: 4px solid #10b981; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;">
        <strong>✅ آمن بنسبة 100% — لا حاجة لتسجيل دخول!</strong><br>
        هذا التبويب يستخدم فقط APIs عامة وآمنة:
        <ul style="margin: 0.5rem 0;">
        <li>🌐 <strong>fxtwitter API</strong>: مجاني ومفتوح — يجلب حقل الموقع المعلن في البروفايل</li>
        <li>🤖 <strong>Gemini Vision</strong>: يحلل صور المنشور لتحديد موقع التصوير الفعلي</li>
        <li>🔍 <strong>EXIF GPS</strong>: إحداثيات مباشرة إن وجدت</li>
        </ul>
        🎯 <strong>كشف VPN</strong>: بمقارنة الموقع المعلن في البروفايل مع موقع التصوير من الصور = التناقض يكشف VPN!
        </div>
        """,
        unsafe_allow_html=True,
    )

    # الوضع الآمن: لا نستخدم cookies أبداً
    use_about_api = False
    x_cookies = ""

    st.markdown("---")

    # وضع 1: روابط منشورات X
    if pl_mode.startswith("🔗 روابط منشورات X"):
        st.markdown("#### 🔗 أدخل روابط تغريدات X تحتوي صور:")
        pl_x_urls = st.text_area(
            "رابط لكل سطر:",
            height=150,
            placeholder="https://x.com/username/status/1234567890\nhttps://x.com/another/status/9876543210",
            key="pl_x_urls_input",
        )

        col_pl1, col_pl2 = st.columns([3, 1])
        with col_pl2:
            pl_max_imgs = st.number_input(
                "صور لكل تغريدة", min_value=1, max_value=4, value=2,
                help="عدد الصور التي ستحلل لكل تغريدة (أقل = أسرع)",
            )

        if st.button(
            "🚀 تحليل مواقع المنشورات + كشف VPN",
            type="primary",
            use_container_width=True,
            key="pl_x_analyze",
            disabled=not api_key_for_post,
        ):
            urls = [u.strip() for u in pl_x_urls.splitlines()
                    if u.strip() and ('x.com' in u or 'twitter.com' in u)]

            if not urls:
                st.error("❌ لم يتم العثور على روابط صحيحة")
            else:
                st.info(f"🔄 جارٍ تحليل **{len(urls)}** منشورات... (قد يستغرق دقيقة لكل منشور)")
                progress = st.progress(0)
                status = st.empty()
                pl_results = []

                for i, url in enumerate(urls):
                    status.text(f"⏳ تحليل {i+1}/{len(urls)}: {url[:60]}...")

                    # 1. جلب بيانات التغريدة (تتضمن روابط الصور + موقع الحساب)
                    tweet_data = analyze_x_tweet(url)

                    if tweet_data.get("status") != "✅ نجح":
                        pl_results.append({
                            "url": url, "error": tweet_data.get("error"),
                            "success": False,
                        })
                        progress.progress((i+1) / len(urls))
                        continue

                    # 2. استخرج روابط الصور
                    photos_urls = []
                    # من النتيجة الجديدة (legacy wrapper)
                    media = tweet_data.get("media") if isinstance(tweet_data.get("media"), dict) else {}
                    if not media:
                        # جلب مباشر
                        from x_analyzer import fetch_x_tweet, parse_x_url
                        u_, tid_ = parse_x_url(url)
                        if u_ and tid_:
                            full = fetch_x_tweet(u_, tid_)
                            photos_urls = full.get("photos_urls", [])
                    else:
                        for p in (media.get("photos") or []):
                            if isinstance(p, dict) and p.get("url"):
                                photos_urls.append(p["url"])

                    # 3. حلل الصور بـ Gemini Vision (مع hint من موقع الحساب ⚡)
                    image_analysis = None
                    if photos_urls:
                        # مرر موقع الحساب لتحسين الكشف
                        account_loc_hint = (
                            tweet_data.get("user_location_field") or
                            tweet_data.get("region_name_ar") or
                            ""
                        )
                        image_analysis = analyze_post_images(
                            photos_urls, api_key_for_post,
                            max_images=int(pl_max_imgs),
                            account_location=account_loc_hint,
                        )

                    # 4. لا نستخدم About API (آمن بدون cookies)
                    about_data = None
                    about_diagnosis = None
                    screen_name = tweet_data.get("user_screen_name")

                    # 5. كشف VPN: بالموقع المعلن في البروفايل (fxtwitter)
                    account_country_iso = tweet_data.get("region")

                    post_country = None
                    if image_analysis and image_analysis.get("aggregate"):
                        post_country = image_analysis["aggregate"].get("country_code")

                    vpn_check = detect_vpn(
                        account_country=account_country_iso,
                        post_country=post_country,
                        lang=tweet_data.get("lang", ""),
                        name=tweet_data.get("user_name", ""),
                        bio=tweet_data.get("user_bio", ""),
                    )

                    pl_results.append({
                        "success": True,
                        "url": url,
                        "tweet": tweet_data,
                        "photos": photos_urls,
                        "image_analysis": image_analysis,
                        "about_data": about_data,
                        "about_diagnosis": about_diagnosis,
                        "vpn_check": vpn_check,
                        "account_country": account_country_iso,
                        "post_country": post_country,
                    })

                    progress.progress((i+1) / len(urls))

                progress.empty()
                status.empty()
                st.session_state["pl_results"] = pl_results
                st.success(f"✅ تم تحليل {len(pl_results)} منشورات!")

        # عرض النتائج
        if "pl_results" in st.session_state and st.session_state["pl_results"]:
            results = st.session_state["pl_results"]

            st.markdown("---")
            st.markdown("## 📊 نتائج تحليل مواقع المنشورات")

            # إحصائيات سريعة
            total = len([r for r in results if r.get("success")])
            with_post_loc = sum(1 for r in results if r.get("post_country"))
            vpn_alerts = sum(1 for r in results if r.get("vpn_check", {}).get("verdict") == "likely_vpn")
            matched = sum(1 for r in results if r.get("vpn_check", {}).get("verdict") == "matched")
            travel = sum(1 for r in results if r.get("vpn_check", {}).get("verdict") in ("travel", "expat_visit"))

            ms1, ms2, ms3, ms4, ms5 = st.columns(5)
            ms1.metric("🔗 الإجمالي", total)
            ms2.metric("🌍 لها موقع صورة", with_post_loc)
            ms3.metric("🚨 احتمال VPN", vpn_alerts, delta=f"{vpn_alerts}/{total}" if total else None)
            ms4.metric("✅ تطابق", matched)
            ms5.metric("✈️ سفر/مغترب", travel)

            # عرض كل نتيجة
            for idx, r in enumerate(results):
                if not r.get("success"):
                    with st.container(border=True):
                        st.error(f"❌ فشل تحليل: {r.get('url')} — {r.get('error')}")
                    continue

                tweet = r.get("tweet", {})
                vpn = r.get("vpn_check", {})
                img_an = r.get("image_analysis", {})

                with st.container(border=True):
                    # Header
                    h1, h2 = st.columns([1, 4])
                    with h1:
                        if tweet.get("user_profile_image"):
                            try:
                                st.image(tweet["user_profile_image"], width=80)
                            except Exception:
                                pass
                    with h2:
                        st.markdown(
                            f"### {tweet.get('user_name', '')} "
                            f"{'✓' if tweet.get('user_blue_verified') else ''}"
                        )
                        st.caption(
                            f"@{tweet.get('user_screen_name', '')} • "
                            f"ID: `{tweet.get('user_id', '')}`"
                        )
                        st.markdown(f"🔗 [فتح التغريدة]({tweet.get('tweet_url', '')})")

                    # 🎯 عرض بيانات About Account (إن توفرت)
                    about = r.get("about_data") or {}
                    about_diag = r.get("about_diagnosis") or {}
                    if about.get("success"):
                        with st.container(border=True):
                            st.markdown("### 🎯 بيانات /about من X مباشرة (الأدق!)")
                            ab1, ab2, ab3, ab4 = st.columns(4)
                            ab1.metric(
                                "📍 account_based_in",
                                about.get("account_based_in") or "-",
                            )
                            la = about.get("location_accurate")
                            if la is True:
                                ab2.metric("✅ location_accurate", "True", delta="موثوق")
                            elif la is False:
                                ab2.metric("🚨 location_accurate", "False", delta="VPN!", delta_color="inverse")
                            else:
                                ab2.metric("❓ location_accurate", "unknown")
                            ab3.metric("📱 source", (about.get("source") or "-")[:25])
                            ab4.metric(
                                "🔄 username_changes",
                                about.get("username_changes_count", 0),
                            )

                            # تشخيص X الرسمي
                            if about_diag:
                                if about_diag["risk_score"] >= 80:
                                    st.error(f"## {about_diag['verdict_ar']}")
                                elif about_diag["risk_score"] >= 40:
                                    st.warning(f"## {about_diag['verdict_ar']}")
                                else:
                                    st.success(f"## {about_diag['verdict_ar']}")

                                for ind in about_diag.get("indicators", []):
                                    st.markdown(f"• {ind}")

                    # المقارنة الرئيسية: حساب vs منشور
                    cmp1, cmp2 = st.columns(2)
                    with cmp1:
                        st.markdown("#### 🏠 موقع الحساب")
                        # أولوية لـ about_data
                        if about.get("success") and about.get("account_based_in"):
                            st.markdown(
                                f"**🎯 من X مباشرة:** {about['account_based_in']}"
                            )
                            iso = country_name_to_iso(about["account_based_in"])
                            if iso:
                                from x_analyzer import X_REGION_MAP
                                ci = X_REGION_MAP.get(iso, {})
                                st.markdown(f"### {ci.get('flag', '')} {ci.get('ar', iso)}")
                            if about.get("location_accurate") is False:
                                st.error("🚨 X أبلغ: الموقع غير دقيق (VPN/Proxy)")
                        elif tweet.get("user_location_field"):
                            st.markdown(f"**حقل الموقع:** `{tweet['user_location_field']}`")
                            if tweet.get("region_flag"):
                                st.markdown(
                                    f"### {tweet['region_flag']} {tweet.get('region_name_ar', '')}"
                                )
                                st.caption(f"ثقة: {tweet.get('region_confidence', 0)}%")
                        elif tweet.get("region_flag"):
                            st.markdown(
                                f"### {tweet['region_flag']} {tweet.get('region_name_ar', '')}"
                            )
                            st.caption(f"ثقة: {tweet.get('region_confidence', 0)}%")
                        else:
                            st.warning("لم يحدد الحساب موقعاً")

                    with cmp2:
                        st.markdown("#### 📸 موقع تصوير الصورة (فعلي)")
                        if img_an and img_an.get("aggregate"):
                            agg = img_an["aggregate"]
                            from x_analyzer import X_REGION_MAP
                            cc = agg.get("country_code")
                            country_info = X_REGION_MAP.get(cc, {})
                            flag = country_info.get("flag", "🌍")
                            ar = country_info.get("ar", agg.get("country_name", cc))
                            st.markdown(f"### {flag} {ar}")
                            if agg.get("city"):
                                st.markdown(f"🏙️ **{agg['city']}**")
                            if agg.get("neighborhood"):
                                st.caption(f"📍 {agg['neighborhood']}")
                            st.caption(f"ثقة: {agg.get('confidence_score', 0)}% • مصدر: {agg.get('source', '')}")
                            if agg.get("votes_str"):
                                st.caption(f"🗳️ تصويت: {agg['votes_str']}")
                        elif r.get("photos"):
                            st.warning(
                                f"⚠️ التغريدة فيها صور لكن لم نستخرج موقعاً "
                                f"({len(r['photos'])} صور)"
                            )
                            # عرض الأدلة الجزئية إن وجدت (جديد ⚡)
                            partial_obs = (img_an or {}).get("partial_observations", [])
                            partial_texts = (img_an or {}).get("partial_texts", [])
                            if partial_obs or partial_texts:
                                with st.expander("🔍 عرض الأدلة الجزئية التي رصدها AI", expanded=True):
                                    if partial_texts:
                                        st.markdown("**📝 نصوص في الصورة:**")
                                        for t in partial_texts[:5]:
                                            st.markdown(f"• {t}")
                                    if partial_obs:
                                        st.markdown("**👁️ ملاحظات:**")
                                        for o in partial_obs[:5]:
                                            st.markdown(f"• {o}")
                                    st.caption(
                                        "💡 التحليل رصد هذه الإشارات لكنها غير كافية لتحديد دولة بدقة"
                                    )
                        else:
                            st.info("📝 التغريدة بدون صور")

                    # تشخيص VPN
                    risk = vpn.get("risk_score", 0)
                    if risk >= 80:
                        st.error(f"## {vpn.get('icon', '🚨')} {vpn.get('verdict_ar', '')}")
                    elif risk >= 50:
                        st.warning(f"## {vpn.get('icon', '⚠️')} {vpn.get('verdict_ar', '')}")
                    elif risk >= 25:
                        st.info(f"## {vpn.get('icon', 'ℹ️')} {vpn.get('verdict_ar', '')}")
                    else:
                        st.success(f"## {vpn.get('icon', '✅')} {vpn.get('verdict_ar', '')}")

                    # شريط الخطر
                    st.progress(risk / 100, text=f"📊 درجة خطر VPN: {risk}/100")

                    # المؤشرات
                    if vpn.get("indicators"):
                        with st.expander("🔍 تفاصيل التحليل", expanded=risk >= 70):
                            for ind in vpn.get("indicators", []):
                                st.markdown(f"• {ind}")
                            if vpn.get("recommendation"):
                                st.markdown(f"\n**💡 التوصية:** {vpn['recommendation']}")
                            if vpn.get("real_location_guess"):
                                rg_info = X_REGION_MAP.get(vpn["real_location_guess"], {})
                                st.markdown(
                                    f"\n**🎯 الموقع الفعلي المرجّح:** "
                                    f"{rg_info.get('flag', '')} {rg_info.get('ar', vpn['real_location_guess'])}"
                                )

                    # تفاصيل الصور وأدلة Gemini
                    if img_an and img_an.get("aggregate"):
                        agg = img_an["aggregate"]
                        with st.expander("📸 تفاصيل تحليل الصور بالذكاء الاصطناعي", expanded=True):
                            if agg.get("reasoning"):
                                st.markdown(f"**🧠 الاستنتاج:** {agg['reasoning']}")
                            if agg.get("verification"):
                                ver = agg["verification"]
                                if ver == "MATCHES":
                                    st.success(f"✅ الصورة **تطابق** موقع الحساب المعلن")
                                elif ver == "DIFFERENT":
                                    st.error(f"🚨 الصورة **مختلفة** عن موقع الحساب (VPN!)")
                                else:
                                    st.info("ℹ️ غير محدد")
                            if agg.get("visible_texts"):
                                st.markdown("**📝 نصوص مرئية في الصورة:**")
                                for t in agg["visible_texts"][:5]:
                                    st.markdown(f"• {t}")
                            if agg.get("key_evidence"):
                                st.markdown("**🔑 الأدلة الرئيسية:**")
                                for ev in agg["key_evidence"]:
                                    st.markdown(f"• {ev}")
                            if agg.get("observations"):
                                st.markdown("**👁️ الملاحظات:**")
                                for obs in agg["observations"]:
                                    st.markdown(f"  ○ {obs}")
                            if agg.get("coordinates"):
                                st.markdown(f"**📍 إحداثيات تقريبية:** `{agg['coordinates']}`")
                                try:
                                    lat, lon = [float(x.strip()) for x in agg['coordinates'].split(',')[:2]]
                                    import pandas as pd
                                    map_df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
                                    st.map(map_df, zoom=10)
                                except Exception:
                                    pass

                    # عرض الصور المحللة
                    if r.get("photos"):
                        with st.expander(f"🖼️ عرض صور التغريدة ({len(r['photos'])})", expanded=False):
                            img_cols = st.columns(min(len(r['photos']), 3))
                            for j, pu in enumerate(r['photos'][:3]):
                                with img_cols[j]:
                                    try:
                                        st.image(pu, use_container_width=True)
                                    except Exception:
                                        st.caption(f"فشل تحميل: {pu[:50]}")

            # تصدير النتائج
            st.markdown("---")
            st.markdown("#### 📥 تصدير")
            export_rows = []
            for r in results:
                if not r.get("success"):
                    continue
                tw = r.get("tweet", {})
                ag = (r.get("image_analysis") or {}).get("aggregate") or {}
                vp = r.get("vpn_check", {})
                export_rows.append({
                    "الرابط": r.get("url"),
                    "المستخدم": f"@{tw.get('user_screen_name','')}",
                    "الاسم": tw.get("user_name", ""),
                    "User ID": tw.get("user_id", ""),
                    "موقع الحساب (معلن)": tw.get("region_name_ar", ""),
                    "حقل الموقع": tw.get("user_location_field", ""),
                    "موقع الصورة (فعلي)": ag.get("country_name") or ag.get("country_code", ""),
                    "المدينة": ag.get("city", ""),
                    "ثقة الصورة": f"{ag.get('confidence_score', 0)}%",
                    "تشخيص VPN": vp.get("verdict_ar", ""),
                    "درجة الخطر": vp.get("risk_score", 0),
                    "التوصية": vp.get("recommendation", ""),
                })
            if export_rows:
                df_pl = pd.DataFrame(export_rows)
                csv_pl = df_pl.to_csv(index=False).encode("utf-8-sig")
                json_pl = df_pl.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8")
                ts_pl = datetime.now().strftime("%Y%m%d_%H%M%S")

                # تصدير بسيط
                st.markdown("##### 📊 تصدير بسيط (بيانات)")
                ec1, ec2 = st.columns(2)
                ec1.download_button(
                    "⬇️ CSV", data=csv_pl,
                    file_name=f"post_locations_{ts_pl}.csv",
                    mime="text/csv", use_container_width=True,
                )
                ec2.download_button(
                    "⬇️ JSON", data=json_pl,
                    file_name=f"post_locations_{ts_pl}.json",
                    mime="application/json", use_container_width=True,
                )

                # 📑 تصدير تقارير احترافية (Word + PowerPoint)
                st.markdown("##### 📑 تصدير تقارير احترافية (مع الصور والتنسيق الكامل)")
                if not REPORT_EXPORTER_AVAILABLE:
                    st.warning(
                        "⚠️ ثبّت `python-docx` و `python-pptx` في requirements.txt لتفعيل هذه الميزة"
                    )
                else:
                    er1, er2 = st.columns(2)

                    with er1:
                        if st.button(
                            "📝 توليد تقرير Word (.docx)",
                            use_container_width=True,
                            key="pl_gen_word",
                        ):
                            with st.spinner("⏳ جارٍ توليد تقرير Word مع الصور..."):
                                try:
                                    docx_bytes = generate_word_report(
                                        results,
                                        title="🌍 تقرير تحليل مواقع المنشورات + كاشف VPN",
                                    )
                                    st.session_state["_pl_docx_bytes"] = docx_bytes
                                    st.session_state["_pl_docx_ts"] = ts_pl
                                    st.success(f"✅ تم توليد Word ({len(docx_bytes):,} bytes)")
                                except Exception as e:
                                    st.error(f"❌ فشل: {e}")

                        if st.session_state.get("_pl_docx_bytes"):
                            st.download_button(
                                "⬇️ تحميل Word",
                                data=st.session_state["_pl_docx_bytes"],
                                file_name=f"post_locations_report_{st.session_state.get('_pl_docx_ts', ts_pl)}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True,
                                key="pl_dl_word",
                            )

                    with er2:
                        if st.button(
                            "📊 توليد عرض PowerPoint (.pptx)",
                            use_container_width=True,
                            key="pl_gen_pptx",
                        ):
                            with st.spinner("⏳ جارٍ توليد عرض PowerPoint مع الصور..."):
                                try:
                                    pptx_bytes = generate_pptx_report(
                                        results,
                                        title="🌍 تحليل مواقع المنشورات + كاشف VPN",
                                    )
                                    st.session_state["_pl_pptx_bytes"] = pptx_bytes
                                    st.session_state["_pl_pptx_ts"] = ts_pl
                                    st.success(f"✅ تم توليد PowerPoint ({len(pptx_bytes):,} bytes)")
                                except Exception as e:
                                    st.error(f"❌ فشل: {e}")

                        if st.session_state.get("_pl_pptx_bytes"):
                            st.download_button(
                                "⬇️ تحميل PowerPoint",
                                data=st.session_state["_pl_pptx_bytes"],
                                file_name=f"post_locations_report_{st.session_state.get('_pl_pptx_ts', ts_pl)}.pptx",
                                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                use_container_width=True,
                                key="pl_dl_pptx",
                            )

                    st.info(
                        "💡 **التقارير تحتوي:** صور البروفايل + صور المنشورات + كل البيانات + "
                        "مقارنة المواقع + تشخيص VPN بالألوان. تنسيق RTL عربي كامل."
                    )

    # وضع 2: رفع صورة مباشرة
    elif pl_mode.startswith("🖼️ رفع صورة"):
        st.markdown("#### 🖼️ ارفع صورة لتحديد موقعها:")
        uploaded = st.file_uploader(
            "اختر صورة:",
            type=["jpg", "jpeg", "png", "webp"],
            key="pl_upload",
        )

        if uploaded and api_key_for_post:
            if st.button("🔍 حلل موقع الصورة", type="primary", use_container_width=True):
                col_img, col_res = st.columns([1, 2])
                with col_img:
                    st.image(uploaded, caption="الصورة المحللة", use_container_width=True)

                with col_res:
                    with st.spinner("🔄 جارٍ التحليل بالذكاء الاصطناعي..."):
                        image_bytes = uploaded.read()
                        result = analyze_image_geo(image_bytes, api_key_for_post)

                    if not result.get("success"):
                        st.error(f"❌ فشل: {result.get('error')}")
                    else:
                        # عرض EXIF
                        if result.get("exif"):
                            ex = result["exif"]
                            st.success(f"🛰️ **EXIF GPS وجد!** (الأدق 100%)")
                            st.markdown(f"• الدولة: **{ex.get('country_name')}** ({ex.get('country_code')})")
                            if ex.get("city"):
                                st.markdown(f"• المدينة: **{ex['city']}**")
                            if ex.get("neighborhood"):
                                st.markdown(f"• الحي: **{ex['neighborhood']}**")
                            st.markdown(f"• الإحداثيات: `{ex['lat']:.5f}, {ex['lon']:.5f}`")
                            try:
                                map_df = pd.DataFrame({'lat': [ex['lat']], 'lon': [ex['lon']]})
                                st.map(map_df, zoom=12)
                            except Exception:
                                pass

                        # عرض Gemini
                        if result.get("gemini"):
                            g = result["gemini"]
                            if g.get("country_code"):
                                from x_analyzer import X_REGION_MAP
                                ci = X_REGION_MAP.get(g["country_code"], {})
                                st.markdown(f"### {ci.get('flag','🌍')} {ci.get('ar', g.get('country_name'))}")
                                if g.get("city"):
                                    st.markdown(f"🏙️ **المدينة:** {g['city']}")
                                if g.get("neighborhood"):
                                    st.markdown(f"📍 **الحي:** {g['neighborhood']}")
                                st.markdown(f"🎯 **الثقة:** {g.get('confidence')} ({g.get('confidence_score', 0)}%)")
                                if g.get("reasoning"):
                                    st.markdown(f"**🧠 الاستنتاج:** {g['reasoning']}")
                                if g.get("key_evidence"):
                                    st.markdown("**🔑 الأدلة:**")
                                    for ev in g["key_evidence"]:
                                        st.markdown(f"• {ev}")
                                if g.get("observations"):
                                    with st.expander("👁️ كل الملاحظات"):
                                        for o in g["observations"]:
                                            st.markdown(f"• {o}")
                                if g.get("alternative_locations"):
                                    with st.expander("🔀 مواقع بديلة محتملة"):
                                        for a in g["alternative_locations"]:
                                            st.markdown(f"• {a}")
                            else:
                                st.warning("⚠️ الصورة لا تحتوي على إشارات جغرافية واضحة")
                                if g.get("observations"):
                                    st.markdown("ملاحظات:")
                                    for o in g["observations"]:
                                        st.markdown(f"• {o}")

    # وضع 3: روابط صور مباشرة
    elif pl_mode.startswith("🔗 روابط صور"):
        st.markdown("#### 🔗 أدخل روابط صور مباشرة:")
        pl_img_urls = st.text_area(
            "رابط صورة لكل سطر:",
            height=120,
            placeholder="https://example.com/photo1.jpg\nhttps://example.com/photo2.jpg",
            key="pl_img_urls_input",
        )
        if st.button("🔍 حلل الصور", type="primary", use_container_width=True,
                     key="pl_imgs_analyze", disabled=not api_key_for_post):
            urls = [u.strip() for u in pl_img_urls.splitlines() if u.strip().startswith("http")]
            if not urls:
                st.error("❌ لم تدخل روابط صحيحة")
            else:
                st.info(f"🔄 تحليل {len(urls)} صورة...")
                progress = st.progress(0)
                for i, u in enumerate(urls):
                    with st.container(border=True):
                        col_i, col_d = st.columns([1, 2])
                        with col_i:
                            try:
                                st.image(u, use_container_width=True)
                            except Exception:
                                pass
                        with col_d:
                            res = analyze_image_geo(u, api_key_for_post)
                            if not res.get("success"):
                                st.error(f"❌ {res.get('error')}")
                            elif res.get("gemini") and res["gemini"].get("country_code"):
                                g = res["gemini"]
                                from x_analyzer import X_REGION_MAP
                                ci = X_REGION_MAP.get(g["country_code"], {})
                                st.markdown(f"### {ci.get('flag','🌍')} {ci.get('ar', g.get('country_name'))}")
                                if g.get("city"):
                                    st.markdown(f"🏙️ {g['city']}")
                                st.caption(f"ثقة: {g.get('confidence_score', 0)}%")
                                if g.get("key_evidence"):
                                    for ev in g["key_evidence"][:3]:
                                        st.caption(f"• {ev}")
                            else:
                                st.warning("⚠️ لم توجد إشارات جغرافية واضحة")
                    progress.progress((i+1) / len(urls))


# ════════════════════════════════════════════════════════════
# Helper: render one geo-engine result
# ════════════════════════════════════════════════════════════
def _render_geo_result(label, img_bytes, res):
    if not res or res.get("error"):
        st.error(f"❌ فشل التحليل: {res.get('error', 'unknown')}")
        return

    cols = st.columns([1, 2])
    with cols[0]:
        if img_bytes:
            try:
                st.image(img_bytes, caption=label[:60], use_container_width=True)
            except Exception:
                st.caption("(تعذر عرض الصورة)")

    with cols[1]:
        tri = res.get("triangulation", {})
        vpn = res.get("vpn", {})

        # Final answer
        if tri.get("final_iso"):
            st.markdown(
                f"<div style='background:#e8f5e9; padding:14px;"
                f"border-radius:10px; border-right:5px solid #2e7d32;'>"
                f"<h3 style='margin:0;'>{tri['final_flag']} {tri['country_ar']} "
                f"<span style='color:#555;font-size:14px;'>(ثقة {tri['confidence']}%)</span></h3>"
                f"<b>🏙️ المدينة:</b> {tri.get('city') or '—'}<br>"
                f"<b>📍 الحي:</b> {tri.get('neighbourhood') or '—'}<br>"
                f"<b>🌐 الإحداثيات:</b> {tri.get('lat')}, {tri.get('lon')}<br>"
                f"<b>🔍 الطريقة:</b> <code>{tri.get('method')}</code>"
                f"</div>",
                unsafe_allow_html=True,
            )
            if tri.get("lat") and tri.get("lon"):
                st.markdown(f"[🗺️ فتح على OpenStreetMap]"
                            f"(https://www.openstreetmap.org/?mlat={tri['lat']}"
                            f"&mlon={tri['lon']}&zoom=16)")
        else:
            st.warning("⚠️ لم يتمكّن أي من الطبقات من تحديد الدولة — جرّب Yandex يدوياً")

        # VPN
        risk = vpn.get("risk_score", 0)
        risk_color = ("#c62828" if risk >= 80 else
                      "#ef6c00" if risk >= 50 else
                      "#f9a825" if risk >= 25 else "#2e7d32")
        st.markdown(
            f"<div style='background:#fafafa;padding:12px;border-radius:8px;"
            f"border-right:5px solid {risk_color}; margin-top:10px;'>"
            f"<b>🛡️ تشخيص VPN:</b> {vpn.get('verdict')} "
            f"<span style='color:{risk_color};font-weight:bold;'>({risk}/100)</span><br>"
            f"‪{'<br>'.join('• ' + r for r in vpn.get('reasons', []))}‬"
            f"<br><i>💡 {vpn.get('recommendation','')}</i>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ─── EXIF table ───
    e = res.get("exif", {})
    with st.expander(f"🔍 فحص EXIF التفصيلي ({e.get('total_tags', 0)} حقل)", expanded=False):
        if e.get("available"):
            exif_show = {k: v for k, v in e.items() if v not in (None, "", {})
                         and k not in ("available", "total_tags")}
            st.json(exif_show)
        else:
            st.info("لا توجد بيانات EXIF (غالباً X/Twitter يحذفها عند الرفع).")

    # ─── AI Vision details ───
    ai = res.get("ai_vision", {})
    with st.expander("🤖 تفاصيل AI GEO-Detective", expanded=False):
        if "error" in ai:
            st.warning(f"AI غير متاح: {ai['error']}")
        else:
            st.json(ai)

    # ─── Reverse-image search links ───
    rev = res.get("reverse_search", {})
    if rev:
        st.markdown("##### 🔗 Reverse Image Search (افتح يدوياً للتحقّق):")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.link_button("🧬 Yandex", rev.get("yandex", "#"), use_container_width=True)
        c2.link_button("🔍 Google Lens", rev.get("google_lens", "#"), use_container_width=True)
        c3.link_button("🌐 Google", rev.get("google", "#"), use_container_width=True)
        c4.link_button("🅱️ Bing", rev.get("bing", "#"), use_container_width=True)
        c5.link_button("👁️ TinEye", rev.get("tineye", "#"), use_container_width=True)


# ════════════════════════════════════════════════════════════
# 🛰️ تبويب Geo-Engine (GeoSpy + EXIF + Yandex + AI Vision)
# ════════════════════════════════════════════════════════════
with tab_geo:
    st.markdown("### 🛰️ Geo-Engine — محرّك التحليل الجغرافي المتعدد الطبقات")
    st.markdown(
        """
<div style='background: linear-gradient(135deg, #0f2027, #2c5364);
            padding: 18px; border-radius: 12px; color: white;
            border-left: 5px solid #00d4ff;'>
  <b>🎯 محرّك مستوحى من GeoSpy.ai وورقة PIGEON من Stanford</b>
  <ul style='margin-top: 10px; font-size: 14px;'>
    <li>🔍 <b>الطبقة 1 — ExifTool Deep Scan</b>: فحص 100+ حقل (GPS، كاميرا، توقيت، برامج، XMP، IPTC) — بنفس محرّك ExifGlass</li>
    <li>🔗 <b>الطبقة 2 — Reverse Image Search</b>: روابط جاهزة لـ Yandex (الأقوى عالمياً)، Google Lens، Bing، TinEye</li>
    <li>🤖 <b>الطبقة 3 — AI GEO-Detective</b>: Gemini 2.0 يفحص 6 فئات (لافتات، عمارة، مركبات، طبيعة، أشخاص، رقميّة)</li>
    <li>🎯 <b>الطبقة 4 — Triangulation Voting</b>: تصويت موزون بين الطبقات للحصول على دليل واحد موثوق</li>
    <li>🛡️ <b>الطبقة 5 — VPN Detector</b>: يقارن موقع الحساب × موقع الصورة × اللغة × المنطقة الزمنية</li>
  </ul>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    if not GEO_ENGINE_AVAILABLE:
        st.error(f"⚠️ geo_engine.py غير متوفر: {GEO_ENGINE_ERROR}")
        st.stop()

    # ─── إعدادات الإدخال ───
    geo_mode = st.radio(
        "📁 وضع الإدخال:",
        [
            "📎 رفع صورة مباشرة (أدقّ فحص EXIF)",
            "🔗 روابط صور مباشرة (URLs)",
            "🐦 روابط منشورات X (استخراج تلقائي)",
        ],
        horizontal=True, key="geo_mode",
    )

    # API key
    geo_api_key = st.session_state.get("gemini_api_key", "") \
                  or os.environ.get("GEMINI_API_KEY", "")
    if not geo_api_key:
        with st.expander("🔑 إعداد Gemini API Key (مجاني 1500 طلب/يوم)", expanded=False):
            st.markdown(
                "احصل على مفتاح مجاني من [Google AI Studio]"
                "(https://aistudio.google.com/apikey) — بدون بطاقة بنكية."
            )
            geo_api_key = st.text_input(
                "AIza...", type="password", key="geo_api_input",
                placeholder="اتركه فارغاً لتعطيل AI والاكتفاء بـ EXIF + Reverse-Search",
            )
            if geo_api_key:
                st.session_state["gemini_api_key"] = geo_api_key

    col_a, col_b = st.columns(2)
    with col_a:
        geo_account_iso = st.selectbox(
            "🏠 الدولة المعلنة للحساب (للمقارنة/كشف VPN)",
            ["— غير محدد —"] + [f"{ge_flag(k)} {k} — {v}" for k, v in ISO_TO_AR.items()],
            key="geo_acc_iso",
        )
    with col_b:
        geo_lang = st.selectbox(
            "🗣️ لغة المنشور (لكشف VPN)",
            ["—", "ar", "en", "fr", "es", "ru", "tr", "fa", "ur", "id", "ms"],
            key="geo_lang",
        )

    parsed_account_iso = (geo_account_iso.split(" ")[1]
                          if geo_account_iso and "—" not in geo_account_iso[:5]
                          else None)
    parsed_lang = geo_lang if geo_lang and geo_lang != "—" else None

    # ─── وضع 1: رفع صورة ###############################
    if geo_mode.startswith("📎"):
        uploaded = st.file_uploader(
            "اختر صورة (jpg/jpeg/png/webp/heic) — حتى 8 MB",
            type=["jpg", "jpeg", "png", "webp", "heic", "heif"],
            accept_multiple_files=True,
            key="geo_upload",
        )
        if uploaded and st.button("🚀 تحليل عبر 5 طبقات", type="primary", key="geo_run_upload"):
            for idx, file in enumerate(uploaded):
                st.markdown(f"---\n#### 📸 صورة {idx+1}: `{file.name}`")
                img_bytes = file.read()
                with st.spinner("جارٍ فحص EXIF + Reverse Search + AI …"):
                    res = analyze_image_full(
                        image_bytes=img_bytes,
                        gemini_api_key=geo_api_key or None,
                        account_iso=parsed_account_iso,
                        tweet_lang=parsed_lang,
                    )
                _render_geo_result(file.name, img_bytes, res)

    # ─── وضع 2: روابط صور مباشرة #####################
    elif geo_mode.startswith("🔗"):
        urls_text = st.text_area(
            "ألصق روابط صور مباشرة (رابط لكل سطر):",
            height=140, key="geo_urls_in",
            placeholder="https://pbs.twimg.com/media/XXX.jpg\nhttps://example.com/photo.jpg",
        )
        if urls_text and st.button("🚀 تحليل الروابط", type="primary", key="geo_run_urls"):
            urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
            for idx, url in enumerate(urls):
                st.markdown(f"---\n#### 🔗 رابط {idx+1}")
                st.caption(url)
                with st.spinner("جارٍ تحليل 5 طبقات …"):
                    res = analyze_image_full(
                        image_url=url,
                        gemini_api_key=geo_api_key or None,
                        account_iso=parsed_account_iso,
                        tweet_lang=parsed_lang,
                    )
                # try to fetch bytes for preview
                try:
                    img_bytes = requests.get(url, timeout=15,
                        headers={"User-Agent":"Mozilla/5.0"}).content
                except Exception:
                    img_bytes = None
                _render_geo_result(url, img_bytes, res)

    # ─── وضع 3: منشورات X #################################
    else:
        x_links = st.text_area(
            "ألصق روابط منشورات X (رابط لكل سطر):",
            height=140, key="geo_x_in",
            placeholder="https://x.com/username/status/1234567890",
        )
        if x_links and st.button("🚀 استخراج الصور + تحليل", type="primary", key="geo_run_x"):
            from x_analyzer import analyze_x_tweet_legacy as _atl
            urls = [u.strip() for u in x_links.splitlines() if u.strip()]
            for idx, url in enumerate(urls):
                st.markdown(f"---\n#### 🐦 تغريدة {idx+1}")
                st.caption(url)
                with st.spinner("جارٍ جلب بيانات التغريدة …"):
                    try:
                        tw = _atl(url) or {}
                    except Exception as e:
                        st.error(f"تعذّر جلب التغريدة: {e}")
                        continue
                    media_urls = tw.get("media_urls") or tw.get("images") or []
                    acc_iso = parsed_account_iso or (tw.get("region_iso") or None)
                    acc_lang = parsed_lang or tw.get("lang")

                if not media_urls:
                    st.warning("لا توجد صور في هذه التغريدة.")
                    continue
                st.success(f"تمّ استخراج {len(media_urls)} صورة — الحساب @{tw.get('user_screen_name','?')} "
                           f"({ge_flag(acc_iso) if acc_iso else ''} {acc_iso or '—'})")
                for j, mu in enumerate(media_urls[:4]):
                    st.markdown(f"##### 🖼️ صورة {j+1}/{len(media_urls[:4])}")
                    with st.spinner("تحليل 5 طبقات …"):
                        res = analyze_image_full(
                            image_url=mu,
                            gemini_api_key=geo_api_key or None,
                            account_iso=acc_iso,
                            tweet_lang=acc_lang,
                        )
                    try:
                        img_bytes = requests.get(mu, timeout=15,
                            headers={"User-Agent":"Mozilla/5.0"}).content
                    except Exception:
                        img_bytes = None
                    _render_geo_result(mu, img_bytes, res)



# ════════════════════════════════════════════════════════════
# 🕵️ تبويب OSINT محقّق تويتر  (نسخة دائمة — النتائج تبقى)
# ════════════════════════════════════════════════════════════
with tab_osint:
    st.markdown("### 🕵️ محقّق تويتر — أدوات OSINT جغرافية متكاملة")
    st.markdown(
        """
<div style='background:linear-gradient(135deg,#1a1a2e,#16213e);padding:18px;
            border-radius:12px;color:white;border-right:5px solid #e94560;'>
  <b>🎯 أدوات مستوحاة من Bellingcat &amp; BirdHunt &amp; Tinfoleak &amp; TWINT</b>
  <ul style='font-size:14px;margin-top:10px;'>
    <li>🗺 <b>geocode</b>: ابحث عن تغريدات داخل دائرة جغرافية</li>
    <li>📍 <b>near + within</b>: تغريدات قرب مدينة بنصف قطر</li>
    <li>🆔 <b>place: ID</b>: بحث بـ Twitter Place ID</li>
    <li>⏰ <b>Timezone Detection</b>: استنتاج المنطقة الزمنية من النشر</li>
    <li>🗺️ <b>9 محرّكات خرائط</b>: Google · Bing · Yandex · Apple · Mapillary · Wikimapia · OSM · Earth · StreetView</li>
    <li>🔗 <b>Entity Extraction</b>: @mentions · #hashtags · URLs (دعم عربي كامل)</li>
  </ul>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    if not OSINT_AVAILABLE:
        st.error(f"twitter_osint.py غير متوفر: {OSINT_ERROR}")
        st.stop()

    # 🔑 تهيئة الذاكرة الدائمة لكل وضع
    for k in ("osint_geo_result", "osint_place_result",
              "osint_tz_result", "osint_full_result",
              "osint_rev_result"):
        st.session_state.setdefault(k, None)

    osint_mode = st.radio(
        "📡 وضع التحقيق:",
        [
            "🗺️ بحث جغرافي (إحداثيات + نصف قطر)",
            "🏙️ بحث باسم مدينة/معلم",
            "⏰ تحليل المنطقة الزمنية لحساب",
            "🕵️ محقّق شامل لحساب (دولة + منطقة زمنية + أنماط)",
            "📍 تحويل إحداثيات → عنوان + خرائط",
        ],
        key="osint_mode",
    )

    # ═══════════════════════════════════════════════════════════
    # 1️⃣ بحث جغرافي دائري
    # ═══════════════════════════════════════════════════════════
    if osint_mode.startswith("🗺️"):
        with st.form("osint_form_geo", clear_on_submit=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                preset = st.selectbox(
                    "📌 مواقع جاهزة:",
                    ["— اختر يدوياً —"] + [n for n, _, _ in FAMOUS_LOCATIONS_AR],
                    key="osint_preset",
                )
            if preset != "— اختر يدوياً —":
                pdata = next(p for p in FAMOUS_LOCATIONS_AR if p[0] == preset)
                dlat, dlon = pdata[1], pdata[2]
            else:
                dlat, dlon = 24.7136, 46.6753
            with col2:
                lat_in = st.number_input("🌐 خط العرض", value=dlat,
                                         format="%.6f", key="osint_lat")
            with col3:
                lon_in = st.number_input("🌐 خط الطول", value=dlon,
                                         format="%.6f", key="osint_lon")

            col4, col5, col6 = st.columns(3)
            with col4:
                radius_km = st.number_input("📏 نصف القطر (كم)", 0.1, 500.0,
                                            5.0, 0.5, key="osint_radius")
            with col5:
                keywords = st.text_input("🔍 كلمات (اختياري)",
                                         placeholder="حريق OR حادث",
                                         key="osint_kw")
            with col6:
                lang_filter = st.selectbox("🗣️ لغة:",
                    ["—", "ar", "en", "fr", "es", "ru", "tr", "fa", "ur"],
                    key="osint_lang")

            col7, col8, col9 = st.columns(3)
            with col7:
                date_since = st.date_input("📅 من", value=None, key="osint_since")
            with col8:
                date_until = st.date_input("📅 إلى", value=None, key="osint_until")
            with col9:
                min_likes = st.number_input("❤️ أدنى إعجابات", 0, value=0,
                                            step=10, key="osint_minlikes")
            filter_media = st.checkbox("🖼️ صور/فيديو فقط", key="osint_media")

            submitted_geo = st.form_submit_button("🚀 بناء روابط البحث",
                                                  type="primary",
                                                  use_container_width=True)

        if submitted_geo:
            st.session_state["osint_geo_result"] = {
                "lat": lat_in, "lon": lon_in, "radius_km": radius_km,
                "keywords": keywords, "lang": lang_filter,
                "since": str(date_since) if date_since else None,
                "until": str(date_until) if date_until else None,
                "min_likes": int(min_likes), "filter_media": filter_media,
                "x_url": build_geocode_search(
                    lat_in, lon_in, radius_km, keywords or "",
                    lang_filter if lang_filter and lang_filter != "—" else None,
                    str(date_since) if date_since else None,
                    str(date_until) if date_until else None,
                    filter_media, int(min_likes)),
                "maps": build_map_verification_links(lat_in, lon_in),
            }

        # ─── دائماً اعرض النتيجة المحفوظة ───
        R = st.session_state.get("osint_geo_result")
        if R:
            st.success(f"✅ تم بناء البحث داخل دائرة "
                       f"{R['radius_km']} كم من ({R['lat']:.4f}, {R['lon']:.4f})")
            st.markdown(f"#### 🔗 رابط البحث في X (انقر للفتح):")
            st.markdown(f"[🐦 افتح في X الآن]({R['x_url']})")
            with st.expander("📝 الرابط الكامل"):
                st.code(R['x_url'], language="text")

            st.markdown("#### 🗺️ تحقّق بصري عبر 9 محركات خرائط:")
            ckeys = list(R["maps"].keys())
            for row in range(0, 9, 3):
                cs = st.columns(3)
                for i, k in enumerate(ckeys[row:row+3]):
                    with cs[i]:
                        st.link_button(f"🌐 {k}", R["maps"][k],
                                       use_container_width=True)

            if FOLIUM_AVAILABLE:
                st.markdown("#### 📌 الخريطة التفاعلية (الدائرة الزرقاء = نطاق البحث)")
                m = folium.Map([R["lat"], R["lon"]],
                               zoom_start=max(8, 18 - int(math.log2(R["radius_km"]+1))))
                folium.Marker([R["lat"], R["lon"]],
                              popup=f"مركز البحث<br>{R['lat']:.5f}, {R['lon']:.5f}",
                              icon=folium.Icon(color="red", icon="star")).add_to(m)
                folium.Circle([R["lat"], R["lon"]], radius=R["radius_km"]*1000,
                              color="#1976d2", fill=True,
                              fill_opacity=0.15).add_to(m)
                st_folium(m, width=720, height=420, key="osint_map_geo")

            if st.button("🗑️ مسح النتيجة", key="osint_clear_geo"):
                st.session_state["osint_geo_result"] = None
                st.rerun()

    # ═══════════════════════════════════════════════════════════
    # 2️⃣ بحث باسم مدينة/معلم
    # ═══════════════════════════════════════════════════════════
    elif osint_mode.startswith("🏙️"):
        with st.form("osint_form_place", clear_on_submit=False):
            place_q = st.text_input("📍 اسم المدينة أو المعلم:",
                placeholder="مثال: برج العرب، الدوحة، Times Square",
                key="osint_place_q")
            ca, cb, cc = st.columns(3)
            with ca:
                place_radius = st.number_input("📏 نصف القطر (كم)",
                    0.5, 200.0, 5.0, 0.5, key="osint_pradius")
            with cb:
                place_kw = st.text_input("🔍 كلمات (اختياري)",
                    key="osint_pkw")
            with cc:
                place_lang = st.selectbox("🗣️ لغة",
                    ["—", "ar", "en"], key="osint_plang")

            submitted_place = st.form_submit_button("🚀 ابحث",
                type="primary", use_container_width=True)

        if submitted_place and place_q:
            with st.spinner("جارٍ تحديد الإحداثيات عبر OpenStreetMap…"):
                geo = geocode_place(place_q)
            if not geo:
                st.error("⛔ تعذّر العثور على المكان. جرب صياغة أخرى.")
                st.session_state["osint_place_result"] = None
            else:
                lang = place_lang if place_lang != "—" else None
                st.session_state["osint_place_result"] = {
                    "query": place_q, "geo": geo,
                    "radius_km": place_radius, "kw": place_kw, "lang": lang,
                    "url_geo":  build_geocode_search(
                        geo["lat"], geo["lon"], place_radius, place_kw, lang),
                    "url_near": build_near_search(
                        place_q, place_radius, place_kw, lang=lang),
                    "place_id": find_place_id(place_q),
                    "maps": build_map_verification_links(
                        geo["lat"], geo["lon"]),
                }

        R = st.session_state.get("osint_place_result")
        if R:
            geo = R["geo"]
            st.success(f"✅ تم العثور: **{geo['display_name']}**")
            cdata = st.columns(4)
            cdata[0].metric("🌐 العرض",  f"{geo['lat']:.4f}")
            cdata[1].metric("🌐 الطول",  f"{geo['lon']:.4f}")
            cdata[2].metric("🏳️ الدولة", geo.get("country_code") or "—")
            cdata[3].metric("🏙️ المدينة", geo.get("city") or "—")

            st.markdown("#### 🔗 ثلاثة أساليب بحث مختلفة في X:")
            cols = st.columns(3)
            cols[0].link_button("🎯 geocode (الأدقّ)", R["url_geo"],
                                use_container_width=True)
            cols[1].link_button("📍 near + within", R["url_near"],
                                use_container_width=True)
            if R["place_id"]:
                cols[2].link_button(f"🆔 place:{R['place_id']['name']}",
                    R["place_id"]["search_url"], use_container_width=True)
            else:
                cols[2].caption("(لا يوجد place_id معروف لهذا المكان)")

            st.markdown("#### 🗺️ تحقّق عبر 9 محركات خرائط:")
            ks = list(R["maps"].keys())
            for row in range(0, 9, 3):
                cs = st.columns(3)
                for i, k in enumerate(ks[row:row+3]):
                    with cs[i]:
                        st.link_button(f"🌐 {k}", R["maps"][k],
                                       use_container_width=True)

            if FOLIUM_AVAILABLE:
                m = folium.Map([geo["lat"], geo["lon"]], zoom_start=12)
                folium.Marker([geo["lat"], geo["lon"]],
                              popup=geo["display_name"][:80],
                              icon=folium.Icon(color="red")).add_to(m)
                folium.Circle([geo["lat"], geo["lon"]],
                              radius=R["radius_km"]*1000,
                              color="#e94560", fill=True,
                              fill_opacity=0.2).add_to(m)
                st_folium(m, width=720, height=420, key="osint_map_place")

            if st.button("🗑️ مسح النتيجة", key="osint_clear_place"):
                st.session_state["osint_place_result"] = None
                st.rerun()

    # ═══════════════════════════════════════════════════════════
    # 3️⃣ تحليل المنطقة الزمنية
    # ═══════════════════════════════════════════════════════════
    elif osint_mode.startswith("⏰"):
        st.markdown("💡 **أدخل تواريخ UTC لتغريدات المستخدم** (سطر لكل تغريدة). "
                    "الصيغ المدعومة: ISO `2026-05-24T14:30:00Z` أو "
                    "RFC `Sat May 24 14:30:00 +0000 2026`")
        with st.form("osint_form_tz", clear_on_submit=False):
            timestamps_text = st.text_area("📅 أوقات UTC:", height=180,
                key="osint_ts_in",
                placeholder="2026-05-24T08:30:00Z\n2026-05-24T14:15:00Z\n2026-05-25T19:45:00Z")
            submitted_tz = st.form_submit_button("⏰ حلّل المنطقة الزمنية",
                type="primary", use_container_width=True)

        if submitted_tz and timestamps_text:
            ts_list = []
            for line in timestamps_text.splitlines():
                line = line.strip()
                if not line: continue
                try:
                    if "T" in line:
                        dt = datetime.fromisoformat(line.replace("Z", "+00:00"))
                    else:
                        dt = datetime.strptime(line, "%a %b %d %H:%M:%S %z %Y")
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    ts_list.append(dt.astimezone(timezone.utc))
                except Exception:
                    continue
            if not ts_list:
                st.error("⛔ لم يتم تحليل أي تاريخ صحيح.")
                st.session_state["osint_tz_result"] = None
            else:
                st.session_state["osint_tz_result"] = analyze_timezone_from_tweets(ts_list)

        R = st.session_state.get("osint_tz_result")
        if R:
            colA, colB, colC = st.columns(3)
            colA.metric("🌐 المنطقة الزمنية", R["best_offset_str"])
            colB.metric("📊 الثقة", f"{R['confidence']}%")
            colC.metric("📈 العينة", R["sample_size"])

            st.markdown("##### 🎯 الدول المحتملة:")
            if R["candidate_countries"]:
                st.success(" · ".join(R["candidate_countries"]))
            else:
                st.info("لا توجد دول معروفة بهذا الفارق")

            hist = R.get("histogram_local_hours") or {}
            if hist:
                df_hist = pd.DataFrame(sorted(hist.items()),
                    columns=["الساعة المحلية", "عدد التغريدات"])
                st.markdown("#### 📊 توزيع النشاط على 24 ساعة:")
                st.bar_chart(df_hist.set_index("الساعة المحلية"))
                st.caption("النشاط يتركّز عادة بين 8ص و11م بالتوقيت المحلي.")

            with st.expander("🔍 كل الفروق المحتملة"):
                df_off = pd.DataFrame([
                    {"UTC offset": f"UTC{k:+d}",
                     "نسبة النشاط 8ص-11م": f"{v*100:.0f}%"}
                    for k, v in R["score_by_offset"].items()
                ])
                st.dataframe(df_off, use_container_width=True, height=300)

            if st.button("🗑️ مسح النتيجة", key="osint_clear_tz"):
                st.session_state["osint_tz_result"] = None
                st.rerun()

    # ═══════════════════════════════════════════════════════════
    # 4️⃣ المحقّق الشامل  —  كاشف VPN + موقع فعلي دقيق (8 إشارات)
    # ═══════════════════════════════════════════════════════════
    elif osint_mode.startswith("🕵️"):
        if not VPN_DETECTOR_AVAILABLE:
            st.error("vpn_detector.py غير متوفر — أعد تثبيت v19+")
        else:
            st.markdown(
                "<div style='background:#1a1a2e;color:white;padding:14px;"
                "border-radius:8px;border-right:5px solid #e94560;'>"
                "<b>🛡️ كاشف VPN متعدد الإشارات</b> — يجمع 8 مصادر مستقلة:"
                "<ol style='margin:8px 0 0 20px;font-size:13px;'>"
                "<li>الموقع المعلن (fxtwitter)</li>"
                "<li>تحويله لإحداثيات (OpenStreetMap)</li>"
                "<li>آخر 30 تغريدة (Nitter RSS / Syndication)</li>"
                "<li>⏰ المنطقة الزمنية الفعلية من أوقات النشر</li>"
                "<li>🤖 AI Vision على آخر صورة (إن وُجدت)</li>"
                "<li>EXIF GPS من الصور</li>"
                "<li>تحليل اللهجة العربية</li>"
                "<li>إشارات الذكر الجغرافي</li>"
                "</ol></div>", unsafe_allow_html=True)
            st.write("")

            with st.form("osint_form_full", clear_on_submit=False):
                col_u, col_n = st.columns([3, 1])
                with col_u:
                    username = st.text_input(
                        "👤 اسم مستخدم X (بدون @):",
                        placeholder="مثال: salim_Aljomaili", key="osint_user")
                with col_n:
                    max_imgs = st.number_input("🖼️ صور للتحليل",
                        0, 4, 2, key="osint_maximg",
                        help="0 = بدون AI Vision (أسرع)")

                use_ai = max_imgs > 0
                if use_ai:
                    api_key = (st.session_state.get("gemini_api_key", "")
                               or os.environ.get("GEMINI_API_KEY", ""))
                    if not api_key:
                        api_key = st.text_input(
                            "🔑 Gemini API key (مجاني):",
                            type="password", key="osint_gem_in",
                            placeholder="AIza... — اتركه فارغاً لتعطيل AI")
                        if api_key:
                            st.session_state["gemini_api_key"] = api_key
                else:
                    api_key = None

                submitted_full = st.form_submit_button(
                    "🚀 ابدأ التحقيق الشامل (8 إشارات)",
                    type="primary", use_container_width=True)

            if submitted_full and username:
                uname = username.strip().lstrip("@")
                progress = st.progress(0, "جارٍ جلب البروفايل…")
                with st.spinner("⏳ يستغرق 10-30 ثانية حسب عدد الصور"):
                    try:
                        progress.progress(20, "جلب التغريدات الأخيرة…")
                        report = vpn_investigate(
                            uname, gemini_api_key=api_key,
                            analyze_images=use_ai, max_images=int(max_imgs))
                        progress.progress(100, "تم!")
                    except Exception as e:
                        st.error(f"خطأ: {e}")
                        report = None
                progress.empty()

                if report and "error" in report:
                    st.error(f"⛔ {report['error']}")
                    st.session_state["osint_full_result"] = None
                elif report:
                    st.session_state["osint_full_result"] = report

            # ─── Display the persistent result ───
            R = st.session_state.get("osint_full_result")
            if R and "final_verdict" in R:
                p = R["profile"]
                d = R["declared_location"]
                v = R["final_verdict"]

                # ── Header card with profile + verdict side by side ──
                st.markdown("---")
                top = st.columns([1, 2, 2])
                with top[0]:
                    if p.get("avatar_url"):
                        st.image(p["avatar_url"], width=130)
                with top[1]:
                    st.markdown(f"### {p.get('name','')}")
                    st.markdown(f"**@{p.get('screen_name','')}** "
                                f"{'✅' if p.get('verified') else ''}")
                    st.caption(
                        f"🆔 `{p.get('id')}` · "
                        f"📅 {(p.get('joined') or '')[:16]} · "
                        f"👥 {p.get('followers') or 0:,}")
                    if d.get("raw"):
                        st.markdown(f"📍 **معلن:** {d['flag']} {d['raw']}")
                    else:
                        st.info("📍 لا يوجد موقع معلن")
                with top[2]:
                    # The big verdict box
                    st.markdown(
                        f"<div style='background:#fff;padding:14px;"
                        f"border-radius:10px;border-right:6px solid {v['vpn_color']};"
                        f"box-shadow:0 2px 6px rgba(0,0,0,.1);'>"
                        f"<h3 style='margin:0;color:{v['vpn_color']};'>"
                        f"{v['vpn_label']}</h3>"
                        f"<div style='font-size:38px;font-weight:bold;color:{v['vpn_color']};'>"
                        f"{v['vpn_score']}/100</div>"
                        f"<small>درجة احتمال VPN</small>"
                        f"</div>", unsafe_allow_html=True)

                # ── Actual location box ──
                st.markdown("---")
                cloc = st.columns([2, 3])
                with cloc[0]:
                    st.markdown(
                        f"<div style='background:#e8f5e9;padding:14px;"
                        f"border-radius:10px;border-right:5px solid #2e7d32;'>"
                        f"<h4 style='margin:0;'>🎯 الموقع الفعلي المُستنتج</h4>"
                        f"<div style='font-size:32px;'>{v['actual_flag']} "
                        f"{v['actual_country_ar']}</div>"
                        f"<b>الثقة: {v['actual_confidence']}%</b><br>"
                        f"<b>المدينة:</b> {v.get('actual_city') or '—'}<br>"
                        f"<b>الإحداثيات:</b> {v.get('actual_coords') or '—'}"
                        f"</div>", unsafe_allow_html=True)
                with cloc[1]:
                    st.markdown("##### 🛡️ أسباب التشخيص:")
                    for reason in v["vpn_reasons"]:
                        st.markdown(f"• {reason}")

                # ── Side-by-side maps: declared vs actual ──
                if FOLIUM_AVAILABLE and (d.get("coords") or v.get("actual_coords")):
                    st.markdown("---")
                    st.markdown("#### 🗺️ مقارنة: المعلن مقابل الفعلي")
                    mc1, mc2 = st.columns(2)
                    if d.get("coords"):
                        with mc1:
                            st.caption(f"📍 المعلن: {d['flag']} {d.get('raw','')}")
                            m1 = folium.Map(d["coords"], zoom_start=5)
                            folium.Marker(d["coords"],
                                popup=d.get("raw",""),
                                icon=folium.Icon(color="orange")).add_to(m1)
                            st_folium(m1, width=350, height=300,
                                      key="map_declared")
                    if v.get("actual_coords"):
                        with mc2:
                            st.caption(f"🎯 الفعلي: {v['actual_flag']} "
                                       f"{v['actual_country_ar']}")
                            m2 = folium.Map(list(v["actual_coords"]),
                                            zoom_start=8)
                            folium.Marker(list(v["actual_coords"]),
                                popup=v.get("actual_city",""),
                                icon=folium.Icon(color="red", icon="screenshot")
                            ).add_to(m2)
                            st_folium(m2, width=350, height=300,
                                      key="map_actual")

                # ── Signal breakdown ──
                with st.expander("📊 تحليل الإشارات الـ8 المستقلة", expanded=True):
                    sigs = st.columns(2)
                    with sigs[0]:
                        st.markdown("##### ⏰ الإشارة 1: المنطقة الزمنية")
                        tz = R.get("timezone_analysis")
                        if tz:
                            st.metric("UTC offset (من النشر)",
                                      tz["best_offset_str"],
                                      f"{tz['confidence']}% ثقة")
                            st.caption(f"🌍 دول مرشحة: "
                                       f"{', '.join(tz.get('candidate_countries', [])[:6])}")
                            hist = tz.get("histogram_local_hours") or {}
                            if hist:
                                df = pd.DataFrame(sorted(hist.items()),
                                    columns=["ساعة محلية", "تغريدات"])
                                st.bar_chart(df.set_index("ساعة محلية"),
                                             height=180)
                        else:
                            st.info("⚠ لا توجد تغريدات كافية لتحليل التوقيت")

                    with sigs[1]:
                        st.markdown("##### 🤖 الإشارة 2: AI Vision على الصور")
                        imgs = R.get("image_locations") or []
                        if imgs:
                            for ii, ir in enumerate(imgs):
                                if ir.get("country_iso"):
                                    st.success(
                                        f"صورة {ii+1}: "
                                        f"{ge_flag(ir['country_iso'])} "
                                        f"{ir['country_iso']} / "
                                        f"{ir.get('city') or '—'} "
                                        f"({ir.get('confidence')}%)")
                                elif ir.get("error"):
                                    st.warning(f"صورة {ii+1}: {ir['error'][:80]}")
                                else:
                                    st.info(f"صورة {ii+1}: لم يتم الكشف")
                        else:
                            st.info("⚠ لم يتم تشغيل AI Vision (مفعّل بـ صور > 0)")

                    sigs2 = st.columns(2)
                    with sigs2[0]:
                        st.markdown("##### 🌍 الإشارة 3: الذكر الجغرافي")
                        gm = R.get("geo_mentions") or {}
                        if gm:
                            df_gm = pd.DataFrame(
                                [{"الدولة": ge_flag(k)+" "+k, "تكرار": v}
                                 for k, v in list(gm.items())[:6]])
                            st.dataframe(df_gm, hide_index=True,
                                         use_container_width=True)
                        else:
                            st.info("لا توجد إشارات جغرافية")

                    with sigs2[1]:
                        st.markdown("##### 🗣️ الإشارة 4: اللهجة")
                        di = R.get("dialect")
                        ds = R.get("dialect_scores") or {}
                        if di:
                            st.success(f"اللهجة الغالبة: **{di}**")
                        st.caption(f"التوزيع: {ds}")

                # ── Vote breakdown ──
                with st.expander("🗳️ تفصيل أصوات الترجيح"):
                    vd = v.get("vote_breakdown") or {}
                    if vd:
                        df_vote = pd.DataFrame([
                            {"الدولة": ge_flag(k) + " " + k +
                             " — " + ge_country_ar(k),
                             "الوزن": round(w, 1)}
                            for k, w in vd.items()])
                        st.dataframe(df_vote, hide_index=True,
                                     use_container_width=True)
                    voters = v.get("all_voters") or []
                    if voters:
                        st.markdown("##### 📋 سجل المصادر:")
                        df_vt = pd.DataFrame(voters)
                        st.dataframe(df_vt, hide_index=True,
                                     use_container_width=True)

                # ── Map verification for actual location ──
                if v.get("maps_links"):
                    st.markdown("#### 🗺️ تحقّق بصري للموقع الفعلي عبر 9 محرّكات:")
                    ks = list(v["maps_links"].keys())
                    for row in range(0, 9, 3):
                        cs = st.columns(3)
                        for i, k in enumerate(ks[row:row+3]):
                            with cs[i]:
                                st.link_button(f"🌐 {k}", v["maps_links"][k],
                                               use_container_width=True)

                # ── Quick OSINT links ──
                st.markdown("#### 🔍 روابط تحقيق جاهزة:")
                uname = R["username"]
                cinv = st.columns(2)
                cinv[0].link_button("📌 كل تغريدات المستخدم (live)",
                    f"https://x.com/search?q=from%3A{uname}&f=live",
                    use_container_width=True)
                cinv[1].link_button("📞 ردود المستخدم",
                    f"https://x.com/search?q=to%3A{uname}&f=live",
                    use_container_width=True)
                if v.get("actual_coords"):
                    cinv2 = st.columns(2)
                    lat, lon = v["actual_coords"]
                    cinv2[0].link_button(
                        f"📍 تغريدات قرب موقعه الفعلي ({v['actual_iso']})",
                        build_user_search(uname, lat, lon, 50),
                        use_container_width=True)
                    cinv2[1].link_button("📱 بروفايل X",
                        f"https://x.com/{uname}", use_container_width=True)

                # ── Download report JSON ──
                rep_json = json.dumps(R, default=str, ensure_ascii=False,
                                      indent=2)
                st.download_button("📥 تحميل التقرير JSON",
                    rep_json,
                    file_name=f"osint_{R['username']}_{int(time.time())}.json",
                    mime="application/json")

                if st.button("🗑️ مسح النتيجة", key="osint_clear_full"):
                    st.session_state["osint_full_result"] = None
                    st.rerun()

    # ═══════════════════════════════════════════════════════════
    # 5️⃣ تحويل إحداثيات → عنوان
    # ═══════════════════════════════════════════════════════════
    else:
        with st.form("osint_form_rev", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                r_lat = st.number_input("🌐 خط العرض", value=24.7136,
                    format="%.6f", key="osint_rlat")
            with col2:
                r_lon = st.number_input("🌐 خط الطول", value=46.6753,
                    format="%.6f", key="osint_rlon")
            submitted_rev = st.form_submit_button("🔍 استخرج العنوان",
                type="primary", use_container_width=True)

        if submitted_rev:
            with st.spinner("جارٍ البحث في OpenStreetMap…"):
                rev = osint_reverse(r_lat, r_lon)
            st.session_state["osint_rev_result"] = {
                "lat": r_lat, "lon": r_lon, "rev": rev,
                "maps": build_map_verification_links(r_lat, r_lon),
            }

        R = st.session_state.get("osint_rev_result")
        if R:
            rev = R["rev"]
            if rev:
                st.success(f"✅ العنوان: {rev['display_name']}")
                cols = st.columns(2)
                with cols[0]:
                    st.json({"الدولة": rev.get("country"),
                             "الدولة (ISO)": rev.get("country_code"),
                             "الولاية/المحافظة": rev.get("state"),
                             "المدينة": rev.get("city"),
                             "الحي": rev.get("neighbourhood"),
                             "الشارع": rev.get("road"),
                             "الرمز البريدي": rev.get("postcode")})
                if FOLIUM_AVAILABLE:
                    with cols[1]:
                        m = folium.Map([R["lat"], R["lon"]], zoom_start=17)
                        folium.Marker([R["lat"], R["lon"]],
                            popup=(rev.get("display_name") or "")[:80],
                            icon=folium.Icon(color="red", icon="info-sign")).add_to(m)
                        st_folium(m, width=400, height=380, key="osint_map_rev")
            else:
                st.error("⛔ لم يتم العثور على عنوان لهذه الإحداثيات.")

            st.markdown("#### 🗺️ تحقّق بصري عبر كل المحرّكات:")
            ks = list(R["maps"].keys())
            for row in range(0, 9, 3):
                cm = st.columns(3)
                for i, k in enumerate(ks[row:row+3]):
                    with cm[i]:
                        st.link_button(f"🌐 {k}", R["maps"][k],
                                       use_container_width=True)

            if st.button("🗑️ مسح النتيجة", key="osint_clear_rev"):
                st.session_state["osint_rev_result"] = None
                st.rerun()


# ============ تبويب RSS ============
with tab_rss:
    st.markdown("### 📡 أداة RSS")
    st.markdown(
        """
        <div class="info-box" dir="rtl">
        ألصق روابط الحسابات المدعومة سطرًا لكل رابط: <strong>TikTok / X / YouTube / Reddit</strong>.<br>
        الأداة تحاول تحويل كل رابط إلى RSS feed مناسب ثم تجلب آخر 10 منشورات لكل حساب.
        </div>
        """,
        unsafe_allow_html=True,
    )

    rss_input = st.text_area(
        "روابط الحسابات:",
        value="""https://x.com/elonmusk
https://www.tiktok.com/@khaby.lame
https://www.youtube.com/@MrBeast
https://www.reddit.com/user/spez
""",
        height=220,
        key="rss_input",
        help="رابط واحد في كل سطر",
    )

    rss_lines = [line.strip() for line in rss_input.splitlines() if line.strip()]
    r1, r2 = st.columns([3, 1])
    with r2:
        st.metric("📎 عدد الروابط", len(rss_lines))

    if st.button("🚀 جلب آخر المنشورات من RSS", type="primary", use_container_width=True, key="rss_fetch"):
        if not rss_lines:
            st.error("❌ أدخل رابطًا واحدًا على الأقل")
        else:
            with st.spinner("⏳ جارٍ تحويل الروابط وجلب آخر المنشورات..."):
                rss_sources = fetch_rss_batch(rss_lines)
            st.session_state["rss_sources"] = rss_sources

            flat_rows = []
            for src in rss_sources:
                for item in src.get("items", [])[:10]:
                    flat_rows.append({
                        "platform": src.get("platform", ""),
                        "source": src.get("display", src.get("source", "")),
                        "feed_url": src.get("feed_url", ""),
                        "date": item.get("published", ""),
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "summary": item.get("summary", ""),
                    })
            st.session_state["rss_rows"] = flat_rows
            st.success(f"✅ تم جلب {len(flat_rows)} منشور من {len(rss_sources)} مصدر")

    if st.session_state.get("rss_sources"):
        rss_sources = st.session_state["rss_sources"]
        rss_rows = st.session_state.get("rss_rows", [])

        ok_count = sum(1 for src in rss_sources if src.get("ok"))
        fail_count = sum(1 for src in rss_sources if not src.get("ok"))
        stats = st.columns(4)
        stats[0].metric("📡 المصادر", len(rss_sources))
        stats[1].metric("✅ نجح", ok_count)
        stats[2].metric("❌ فشل", fail_count)
        stats[3].metric("📰 المنشورات", len(rss_rows))

        with st.expander("📋 حالة كل Feed", expanded=fail_count > 0):
            state_rows = []
            for src in rss_sources:
                state_rows.append({
                    "المصدر": src.get("display", src.get("source", "")),
                    "المنصة": src.get("platform", ""),
                    "الحالة": "✅ نجح" if src.get("ok") else "❌ فشل",
                    "Feed": src.get("feed_url", ""),
                    "الخطأ": src.get("error", ""),
                })
            st.dataframe(pd.DataFrame(state_rows), use_container_width=True, height=240)

        if rss_rows:
            df_rss = pd.DataFrame(rss_rows)
            st.markdown("#### 📰 آخر 10 منشورات من كل Feed")
            st.dataframe(
                df_rss[["date", "title", "link", "summary", "platform", "source"]],
                use_container_width=True,
                height=420,
                column_config={
                    "link": st.column_config.LinkColumn("🔗 الرابط"),
                    "summary": st.column_config.TextColumn("الملخص", width="large"),
                    "title": st.column_config.TextColumn("العنوان", width="medium"),
                    "date": st.column_config.TextColumn("التاريخ"),
                },
            )

            ts_rss = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_rss = df_rss.to_csv(index=False).encode("utf-8-sig")
            json_rss = df_rss.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8")
            er1, er2 = st.columns(2)
            er1.download_button(
                "⬇️ تصدير CSV",
                data=csv_rss,
                file_name=f"rss_posts_{ts_rss}.csv",
                mime="text/csv",
                use_container_width=True,
            )
            er2.download_button(
                "⬇️ تصدير JSON",
                data=json_rss,
                file_name=f"rss_posts_{ts_rss}.json",
                mime="application/json",
                use_container_width=True,
            )
        else:
            st.info("ℹ️ لم يتم العثور على منشورات قابلة للعرض")


# ============ تبويب BUFFIN ============
with tab_buffin:
    st.markdown("### 🔍 BUFFIN - بحث المنصات")
    st.markdown(
        """
        <div class="info-box" dir="rtl">
        أدخل اسم مستخدم واحد وسنبحث عنه بالتوازي في 13 منصة مختلفة.<br>
        القاعدة المستخدمة هنا بسيطة ومباشرة: <strong>HTTP 200 = موجود</strong>، <strong>404 = غير موجود</strong>، وما عدا ذلك يُعرض كمحجوب/مقيّد.
        </div>
        """,
        unsafe_allow_html=True,
    )

    buffin_username = st.text_input(
        "اسم المستخدم:",
        value="elonmusk",
        key="buffin_username",
        help="بدون @",
    )

    if st.button("🚀 ابدأ BUFFIN", type="primary", use_container_width=True, key="buffin_search"):
        clean_username = (buffin_username or "").strip().lstrip("@")
        if not clean_username:
            st.error("❌ أدخل اسم مستخدم صحيح")
        else:
            with st.spinner("⏳ جارٍ فحص 13 منصة بشكل متوازٍ..."):
                st.session_state["buffin_results"] = buffin_search_username(clean_username)

    if st.session_state.get("buffin_results"):
        buffin_results = st.session_state["buffin_results"]
        existing = sum(1 for r in buffin_results if r.get("status_key") == "exists")
        checked = len(buffin_results)
        blocked = sum(1 for r in buffin_results if r.get("status_key") == "blocked")
        missing = sum(1 for r in buffin_results if r.get("status_key") == "missing")

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("🟢 الحسابات الموجودة", existing)
        s2.metric("📊 المنصات المفحوصة", checked)
        s3.metric("🔴 غير موجود", missing)
        s4.metric("🟡 محجوب", blocked)

        render_buffin_open_all(buffin_results)

        color_map = {
            "exists": ("#dcfce7", "#166534", "#22c55e"),
            "missing": ("#fee2e2", "#991b1b", "#ef4444"),
            "blocked": ("#fef3c7", "#92400e", "#f59e0b"),
        }
        st.markdown("#### 🧩 بطاقات النتائج")
        cols = st.columns(3)
        for i, row in enumerate(buffin_results):
            bg, fg, border = color_map.get(row.get("status_key"), ("#f3f4f6", "#111827", "#9ca3af"))
            card = f"""
            <div dir="rtl" style="background:{bg};color:{fg};border-right:6px solid {border};padding:14px;border-radius:12px;min-height:150px;">
                <div style="font-size:20px;font-weight:700;">{row.get('icon','')} {row.get('label','')}</div>
                <div style="margin-top:8px;font-size:18px;font-weight:700;">{row.get('status_label','')}</div>
                <div style="margin-top:8px;"><code>@{html.escape(str(row.get('username','')))}</code></div>
                <div style="margin-top:6px;">HTTP: {row.get('http_status') or '—'}</div>
                <div style="margin-top:8px;"><a href="{row.get('url','')}" target="_blank">فتح الرابط ↗</a></div>
            </div>
            """
            with cols[i % 3]:
                st.markdown(card, unsafe_allow_html=True)

        df_buffin = pd.DataFrame(buffin_results)
        st.markdown("#### 📋 جدول النتائج")
        st.dataframe(
            df_buffin[["label", "status_label", "http_status", "url", "error"]],
            use_container_width=True,
            height=320,
            column_config={
                "url": st.column_config.LinkColumn("🔗 الرابط"),
            },
        )

        ts_buffin = datetime.now().strftime("%Y%m%d_%H%M%S")
        buffin_json = df_buffin.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8")
        st.download_button(
            "⬇️ تصدير JSON",
            data=buffin_json,
            file_name=f"buffin_{ts_buffin}.json",
            mime="application/json",
            use_container_width=True,
        )


# ============ تبويب الإدخال اليدوي ============
with tab_manual:
    st.markdown("### 📝 إدخال يدوي - كل المنصات (300+ حساب)")
    st.markdown(
        """
        <div class="info-box">
        <strong>الصيغ:</strong> <code>platform,username</code> • <code>platform:username</code> • 
        <code>https://x.com/nasa</code>
        </div>
        """,
        unsafe_allow_html=True,
    )

    default_text = """# الصق ما يصل إلى 300+ حساب أو رابط
tiktok,khaby.lame
x,nasa
instagram,natgeo
youtube:MrBeast
github,torvalds
twitch,shroud
"""

    col_input, col_actions = st.columns([4, 1])
    with col_input:
        manual_input = st.text_area(
            "الحسابات أو الروابط:",
            value=default_text, height=400, key="manual_input",
        )
    with col_actions:
        if st.button("🔍 معاينة", use_container_width=True):
            st.session_state["preview_entries"] = parse_manual_input(manual_input)
        if st.button("🧹 مسح", use_container_width=True):
            st.session_state["manual_input"] = ""
            st.rerun()
        live_count = len([l for l in manual_input.splitlines() if l.strip() and not l.strip().startswith("#")])
        st.metric("📊 الأسطر", live_count)

    if "preview_entries" in st.session_state:
        entries = st.session_state["preview_entries"]
        if entries:
            st.success(f"✅ {len(entries)} حساب صحيح")
            with st.expander(f"عرض ({len(entries)})"):
                st.dataframe(pd.DataFrame(entries), use_container_width=True, height=300)

    if st.button("🚀 ابدأ سحب المعلومات", type="primary", use_container_width=True, key="manual_fetch"):
        entries = parse_manual_input(manual_input)
        if not entries:
            st.error("❌ لم يتم العثور على حسابات صحيحة.")
        else:
            st.info(f"🔄 جارٍ سحب **{len(entries)}** حساب...")
            progress = st.progress(0)
            status = st.empty()
            start = time.time()

            def cb(d, t):
                progress.progress(d / t)
                status.text(f"⏳ {d}/{t}")

            results = fetch_batch(entries, max_workers=max_workers, progress_callback=cb)
            elapsed = time.time() - start
            progress.empty()
            status.empty()
            st.session_state["results"] = results
            st.session_state["elapsed"] = elapsed
            st.success(f"✅ تم في {elapsed:.1f} ثانية!")

# ============ تبويب Excel ============
with tab_excel:
    st.markdown("### 📂 رفع ملف Excel")
    uploaded = st.file_uploader("اختر ملف (.xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"])
    if uploaded:
        try:
            df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
            df.columns = [c.lower().strip() for c in df.columns]
            if "platform" not in df.columns or "username" not in df.columns:
                st.error("❌ الملف يجب أن يحتوي على `platform` و `username`")
            else:
                df = df[["platform", "username"]].dropna()
                df["platform"] = df["platform"].astype(str).str.lower().str.strip()
                df["username"] = df["username"].astype(str).str.replace("@", "").str.strip()
                st.success(f"✅ {len(df)} حساب")
                with st.expander("معاينة"):
                    st.dataframe(df.head(20), use_container_width=True)
                if st.button("🚀 ابدأ", type="primary", use_container_width=True, key="excel_fetch"):
                    entries = df.to_dict("records")
                    progress = st.progress(0)
                    status = st.empty()
                    start = time.time()

                    def cb(d, t):
                        progress.progress(d / t)
                        status.text(f"⏳ {d}/{t}")

                    results = fetch_batch(entries, max_workers=max_workers, progress_callback=cb)
                    elapsed = time.time() - start
                    progress.empty()
                    status.empty()
                    st.session_state["results"] = results
                    st.session_state["elapsed"] = elapsed
                    st.success(f"✅ تم في {elapsed:.1f} ثانية!")
        except Exception as e:
            st.error(f"❌ {e}")

# ============ تبويب التعليمات ============
with tab_help:
    st.markdown("""
    ### ℹ️ دليل الاستخدام - الإصدار v5

    #### 🎵 محلل TikTok المتقدم (جديد!)
    تم بناء محلل متخصص لـ TikTok يستخدم تقنية `__UNIVERSAL_DATA_FOR_REHYDRATION__` 
    وهو نفس مصدر البيانات الذي يستخدمه موقع TikTok نفسه.

    **البيانات المستخرجة بدقة 100%:**
    - 🆔 **User ID** (رقمي، دائم، لا يتغير)
    - 🔐 **secUid** (مُعرّف مشفّر دائم)
    - 📅 تاريخ إنشاء الحساب (دقيق لليوم)
    - 👥 عدد المتابعين / المتابَعين
    - ❤️ إجمالي الإعجابات / عدد الفيديوهات
    - ✓ التوثيق / 🔒 الخصوصية / 🛒 حساب تجاري
    - 🌐 لغة الحساب
    - 📝 البايو الكامل + الرابط

    #### 🌍 كشف موقع TikTok (5 طبقات)
    | الطبقة | المصدر | الثقة |
    |--------|--------|-------|
    | 1 | TikTok API region (نادر) | 100% |
    | 2 | تحليل البايو | 65-95% |
    | 3 | تحليل الاسم الظاهر | 30-85% |
    | 4 | تحليل اسم المستخدم | 25-75% |
    | 5 | استنتاج من اللغة | 65% (واحدة) |

    #### ⚠️ ملاحظات صادقة عن TikTok
    - **TikTok يحجب حقل region للحسابات العادية** (يأتي `null` غالباً).
    - **الحسابات الخاصة (Private)** تُرجع خطأ `ErrBizUserSecret` - لا يمكن قراءة بياناتها.
    - **الحسابات المحظورة/المحذوفة** تُرجع خطأ "لم يتم العثور".
    - **التحليل دقيق 100% للحسابات العامة** غير الخاصة.

    #### 💡 نصائح
    - استخدم **شريط الثقة الجانبي** لتصفية النتائج.
    - الحسابات العربية تُكشف غالباً من **اللهجة في البايو** (سعودية، مصرية، عراقية...).
    - حسابات الـ TikTok التي لا تحوي بايو/مدينة → يصعب تحديد دولتها.

    #### 🆔 الـ ID الدائم - فائدته
    حتى لو غيّر المستخدم اسم حسابه (@username)، يبقى **User ID و secUid ثابتين**.
    يمكنك استخدامهما للوصول للحساب لاحقاً عبر:
    `https://www.tiktok.com/@username` أو عبر API الرسمي.

    #### 📡 أداة RSS الجديدة
    - تحويل روابط TikTok وX وYouTube وReddit إلى RSS feeds.
    - جلب آخر 10 منشورات لكل حساب مع تصدير CSV وJSON.

    #### 🔍 BUFFIN - بحث المنصات
    - فحص اسم مستخدم واحد على 13 منصة بالتوازي.
    - بطاقات حالة: موجود / غير موجود / محجوب + زر فتح الكل.

    #### 🗺️ الخرائط التفاعلية
    - تمت إضافة خرائط Folium لنتائج TikTok وX عندما تتوفر دولة بثقة كافية.
    - تحتاج تثبيت `folium` و `streamlit-folium` لتعمل داخل Streamlit.
    """)

# ============ عرض نتائج المنصات الأخرى ============
if "results" in st.session_state and st.session_state["results"]:
    results = st.session_state["results"]
    df_results = pd.DataFrame(results)

    st.markdown("---")
    st.markdown("## 📊 نتائج كل المنصات")

    total = len(results)
    success = sum(1 for r in results if r.get("status") == "✅ نجح")
    with_id = sum(1 for r in results if r.get("permanent_id"))
    failed = sum(1 for r in results if r.get("status") == "❌ فشل")
    verified = sum(1 for r in results if r.get("verified"))

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📋 الإجمالي", total)
    c2.metric("✅ ناجح", success)
    c3.metric("🆔 ID دائم", with_id)
    c4.metric("✓ موثّق", verified)
    c5.metric("❌ فشل", failed)

    if "elapsed" in st.session_state:
        st.caption(f"⏱️ {st.session_state['elapsed']:.1f} ثانية")

    # فلترة
    st.markdown("#### 🔍 فلترة")
    col_f1, col_f2 = st.columns(2)
    status_filter = col_f1.multiselect(
        "حسب الحالة", df_results["status"].unique().tolist(),
        default=df_results["status"].unique().tolist(),
    )
    platform_filter = col_f2.multiselect(
        "حسب المنصة", df_results["platform"].unique().tolist(),
        default=df_results["platform"].unique().tolist(),
    )
    filtered = df_results[
        df_results["status"].isin(status_filter) & df_results["platform"].isin(platform_filter)
    ]

    # جدول
    st.markdown(f"#### 📋 النتائج ({len(filtered)})")
    cols_to_show = [
        "platform", "username", "permanent_id", "display_name",
        "country_flag", "country_name_ar", "country_source", "country_confidence",
        "language_name_ar", "follower_count", "video_count", "create_date",
        "verified", "private_account", "bio", "profile_url", "status", "error",
    ]
    cols_to_show = [c for c in cols_to_show if c in filtered.columns]
    st.dataframe(
        filtered[cols_to_show],
        use_container_width=True, height=400,
        column_config={
            "profile_url": st.column_config.LinkColumn("🔗"),
            "verified": st.column_config.CheckboxColumn("✓"),
            "private_account": st.column_config.CheckboxColumn("🔒"),
            "permanent_id": st.column_config.TextColumn("🆔 ID"),
            "country_flag": st.column_config.TextColumn("🚩", width="small"),
            "country_name_ar": st.column_config.TextColumn("الدولة"),
            "country_confidence": st.column_config.ProgressColumn(
                "ثقة", min_value=0, max_value=100, format="%d%%",
            ),
        },
    )

    # تصدير
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    e1, e2, e3 = st.columns(3)
    csv = filtered.to_csv(index=False).encode("utf-8-sig")
    e1.download_button("⬇️ CSV", csv, f"results_{timestamp}.csv", "text/csv", use_container_width=True)
    js = filtered.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8")
    e2.download_button("⬇️ JSON", js, f"results_{timestamp}.json", "application/json", use_container_width=True)
    xl = results_to_excel(filtered.to_dict("records"))
    e3.download_button("⬇️ Excel", xl, f"results_{timestamp}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       use_container_width=True)
