"""
مولد معلومات حسابات التواصل الاجتماعي - النسخة v4
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
import socket
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

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
    page_title="مولد معلومات حسابات التواصل الاجتماعي",
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


# ============ الواجهة ============
st.markdown(
    """
    <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #ff0050 0%, #00f2ea 100%); 
                border-radius: 15px; margin-bottom: 2rem; color: white;">
        <h1 style="color: white; margin: 0;">🌐 مولد معلومات حسابات التواصل الاجتماعي</h1>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.95;">
            🎵 تحليل TikTok عميق • 🆔 ID دائم • 🌍 موقع جغرافي • 14+ منصة
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

# ============ التبويبات ============
tab_tt, tab_video, tab_x, tab_postloc, tab_manual, tab_excel, tab_help = st.tabs([
    "🎵 محلل حسابات TikTok",
    "🎬 تحليل فيديو تيك توك",
    "🐦 تحليل تغريدات X (Twitter)",
    "🌍 موقع المنشور + كاشف VPN",  # التبويب الجديد
    "📝 إدخال يدوي (كل المنصات)",
    "📂 رفع Excel",
    "ℹ️ التعليمات",
])

# ============ تبويب TikTok المتخصص ============
with tab_tt:
    st.markdown("### 🎵 محلل TikTok المتخصص - دقة عالية")
    st.markdown(
        """
        <div class="info-box">
        <strong>هذا المحلل يستخرج بيانات TikTok عميقة باستخدام تقنية</strong> 
        <code>__UNIVERSAL_DATA_FOR_REHYDRATION__</code> وهو نفس مصدر البيانات الذي يستخدمه TikTok نفسه.<br>
        <strong>يدعم تحليل أكثر من 300 حساب TikTok دفعة واحدة</strong>.
        </div>
        """,
        unsafe_allow_html=True,
    )

    tt_input = st.text_area(
        "ضع أسماء حسابات TikTok (سطر لكل حساب، بدون @ أو مع @، أو روابط كاملة):",
        value="""khaby.lame
charlidamelio
@bellapoarch
https://www.tiktok.com/@addisonre
zachking
""",
        height=300,
        help="يقبل: username, @username, https://www.tiktok.com/@username",
    )

    col_a, col_b = st.columns([3, 1])
    with col_b:
        live_lines = len([l for l in tt_input.splitlines() if l.strip() and not l.strip().startswith("#")])
        st.metric("📊 عدد الحسابات", live_lines)

    if st.button("🚀 تحليل TikTok بدقة عالية", type="primary", use_container_width=True):
        # تنظيف المدخلات
        usernames = []
        seen = set()
        for line in tt_input.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # استخراج اسم المستخدم
            if "tiktok.com/@" in line:
                username = line.split("tiktok.com/@")[-1].split("/")[0].split("?")[0]
            else:
                username = line.replace("@", "").strip()
            if username and username.lower() not in seen:
                seen.add(username.lower())
                usernames.append(username)

        if not usernames:
            st.error("❌ لم يتم العثور على أسماء صحيحة.")
        else:
            st.info(f"🔄 جارٍ تحليل **{len(usernames)}** حساب TikTok...")
            progress = st.progress(0)
            status = st.empty()
            start = time.time()

            tt_results = []
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futures = {ex.submit(fetch_tiktok_profile, u): u for u in usernames}
                done = 0
                for f in as_completed(futures):
                    try:
                        tt_results.append(f.result())
                    except Exception as e:
                        tt_results.append({"username": futures[f], "status": "❌", "error": str(e)})
                    done += 1
                    progress.progress(done / len(usernames))
                    status.text(f"⏳ {done}/{len(usernames)}")

            elapsed = time.time() - start
            progress.empty()
            status.empty()
            st.session_state["tt_results"] = tt_results
            st.session_state["tt_elapsed"] = elapsed
            st.success(f"✅ تم تحليل {len(tt_results)} حساب في {elapsed:.1f} ثانية!")

    # عرض نتائج TikTok
    if "tt_results" in st.session_state and st.session_state["tt_results"]:
        tt_results = st.session_state["tt_results"]
        df_tt = pd.DataFrame(tt_results)

        st.markdown("---")
        st.markdown("## 📊 نتائج تحليل TikTok")

        # إحصائيات
        total = len(tt_results)
        success = sum(1 for r in tt_results if r.get("status") == "✅ نجح")
        verified = sum(1 for r in tt_results if r.get("verified"))
        private = sum(1 for r in tt_results if r.get("private_account"))
        with_region = sum(1 for r in tt_results if r.get("region_confidence", 0) >= min_confidence)
        total_followers = sum(r.get("follower_count", 0) for r in tt_results if r.get("status") == "✅ نجح")
        total_videos = sum(r.get("video_count", 0) for r in tt_results if r.get("status") == "✅ نجح")

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("📋 الإجمالي", total)
        c2.metric("✅ ناجح", success)
        c3.metric("✓ موثّق", verified)
        c4.metric("🔒 خاص", private)
        c5.metric("🌍 له دولة", with_region)
        c6.metric("👥 متابعون كلياً", tt_format_count(total_followers))

        # توزيع الدول
        if any(r.get("region_confidence", 0) >= min_confidence for r in tt_results):
            st.markdown(f"#### 🌍 توزيع الدول (ثقة ≥ {min_confidence}%)")
            countries_data = [
                f"{r['region_flag']} {r['region_name_ar']}"
                for r in tt_results
                if r.get("region_confidence", 0) >= min_confidence and r.get("region_name_ar")
            ]
            if countries_data:
                country_counts = pd.Series(countries_data).value_counts()
                st.bar_chart(country_counts)

        # الجدول الكامل
        st.markdown(f"#### 📋 الجدول الكامل ({total} سجل)")
        display_cols = [
            "username", "nickname", "user_id", "sec_uid",
            "region_flag", "region_name_ar", "region_source", "region_confidence",
            "language_name_ar", "create_date",
            "follower_count_formatted", "follower_count",
            "video_count", "heart_count_formatted",
            "verified", "private_account", "is_organization",
            "signature", "bio_link", "profile_url", "status", "error",
        ]
        display_cols = [c for c in display_cols if c in df_tt.columns]

        # تطبيق فلتر الثقة
        df_display = df_tt.copy()
        if "region_confidence" in df_display.columns:
            mask = df_display["region_confidence"] < min_confidence
            for col in ["region_flag", "region_name_ar", "region_source"]:
                if col in df_display.columns:
                    df_display.loc[mask, col] = ""

        st.dataframe(
            df_display[display_cols],
            use_container_width=True,
            height=500,
            column_config={
                "profile_url": st.column_config.LinkColumn("🔗"),
                "verified": st.column_config.CheckboxColumn("✓"),
                "private_account": st.column_config.CheckboxColumn("🔒"),
                "is_organization": st.column_config.CheckboxColumn("🏢"),
                "user_id": st.column_config.TextColumn("🆔 User ID"),
                "sec_uid": st.column_config.TextColumn("🔐 secUid"),
                "follower_count": st.column_config.NumberColumn("👥 المتابعون", format="%d"),
                "video_count": st.column_config.NumberColumn("🎬 فيديوهات", format="%d"),
                "region_flag": st.column_config.TextColumn("🚩", width="small"),
                "region_name_ar": st.column_config.TextColumn("الدولة"),
                "region_source": st.column_config.TextColumn("مصدر الكشف"),
                "region_confidence": st.column_config.ProgressColumn(
                    "الثقة %", min_value=0, max_value=100, format="%d%%",
                ),
                "create_date": st.column_config.TextColumn("📅 الإنشاء"),
                "signature": st.column_config.TextColumn("📝 البايو", width="large"),
                "bio_link": st.column_config.LinkColumn("🔗 رابط البايو"),
            },
        )

        # تصدير
        st.markdown("#### 📥 تصدير نتائج TikTok")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        e1, e2, e3 = st.columns(3)
        csv_data = df_display.to_csv(index=False).encode("utf-8-sig")
        e1.download_button("⬇️ CSV", data=csv_data,
                           file_name=f"tiktok_analysis_{timestamp}.csv",
                           mime="text/csv", use_container_width=True)
        json_data = df_display.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8")
        e2.download_button("⬇️ JSON", data=json_data,
                           file_name=f"tiktok_analysis_{timestamp}.json",
                           mime="application/json", use_container_width=True)
        excel_data = results_to_excel(df_display.to_dict("records"))
        e3.download_button("⬇️ Excel", data=excel_data,
                           file_name=f"tiktok_analysis_{timestamp}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)

        # بطاقات تفصيلية للناجحين
        st.markdown("#### 🎴 بطاقات الحسابات الناجحة")
        successful = [r for r in tt_results if r.get("status") == "✅ نجح"][:9]
        if successful:
            cols = st.columns(3)
            for i, r in enumerate(successful):
                with cols[i % 3]:
                    metrics_data = calculate_engagement_metrics(r)
                    with st.container(border=True):
                        if r.get("avatar_medium"):
                            try:
                                st.image(r["avatar_medium"], width=100)
                            except Exception:
                                pass
                        flag = r.get("region_flag", "")
                        verified_mark = " ✓" if r.get("verified") else ""
                        private_mark = " 🔒" if r.get("private_account") else ""
                        st.markdown(f"### 🎵 {r['nickname']}{verified_mark}{private_mark}")
                        st.caption(f"@{r['username']} {flag}")
                        if r.get("region_name_ar") and r.get("region_confidence", 0) >= min_confidence:
                            st.caption(f"🌍 {r['region_name_ar']} • {r['region_source']} ({r['region_confidence']}%)")
                        st.markdown(f"🆔 `{r['user_id']}`")
                        if r.get("create_date"):
                            st.caption(f"📅 منذ {r['create_date']}")

                        # إحصائيات
                        cc1, cc2 = st.columns(2)
                        cc1.metric("👥 متابعون", r.get("follower_count_formatted", "0"))
                        cc2.metric("❤️ إعجابات", r.get("heart_count_formatted", "0"))
                        cc1.metric("🎬 فيديوهات", f"{r.get('video_count', 0):,}")
                        cc2.metric("📊 التفاعل", f"{metrics_data['engagement_rate']}%")

                        st.caption(f"**{metrics_data['tier']}**")
                        if r.get("signature"):
                            st.caption(r["signature"][:120])
                        if r.get("bio_link"):
                            st.markdown(f"🔗 [{r['bio_link'][:30]}...]({r['bio_link']})")
                        st.markdown(f"[فتح في TikTok ↗]({r['profile_url']})")

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
                    
                    # 3. حلل الصور بـ Gemini Vision
                    image_analysis = None
                    if photos_urls:
                        image_analysis = analyze_post_images(
                            photos_urls, api_key_for_post, max_images=int(pl_max_imgs)
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
                        with st.expander("📸 تفاصيل تحليل الصور بالذكاء الاصطناعي", expanded=False):
                            if agg.get("reasoning"):
                                st.markdown(f"**🧠 الاستنتاج:** {agg['reasoning']}")
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
                                # خريطة
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
    ### ℹ️ دليل الاستخدام - الإصدار v4

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
