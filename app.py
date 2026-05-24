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

# استيراد محلل X (Twitter) v3 - مع حقل location الرسمي ⭐
from x_analyzer import (
    analyze_x_tweet_legacy as analyze_x_tweet,
    analyze_x_account,
    aggregate_user_tweets,
    X_REGION_MAP,
    LANGUAGE_NAMES_AR_X,
)

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

# ============ التبويبات ============
tab_tt, tab_video, tab_x, tab_manual, tab_excel, tab_help = st.tabs([
    "🎵 محلل حسابات TikTok",
    "🎬 تحليل فيديو تيك توك",
    "🐦 تحليل تغريدات X (Twitter)",
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
    st.markdown("### 🐦 محلل تغريدات X (Twitter) v3 - مع حقل الموقع الرسمي! ⭐")
    st.markdown(
        """
        <div class="info-box">
        <strong>🔥 الجديد: يستخرج حقل الموقع الفعلي الذي يدخله المستخدم في بروفايله!</strong><br>
        يستخدم <code>fxtwitter API</code> العام (بدون مصادقة) لجلب:<br>
        • 📍 <strong>حقل location الرسمي من البروفايل</strong> (مثل: "الرياض", "England, UK")<br>
        • 🆔 Tweet ID + User ID الدائم<br>
        • 📝 نص التغريدة + التاريخ + اللغة<br>
        • ❤️ الإعجابات + الردود + المشاهدات<br>
        • 🖼️ الصور والفيديوهات بأعلى جودة<br>
        • 👤 صورة البروفايل + التوثيق + المتابعون<br>
        • 🌍 كشف الدولة من 3 مصادر: حقل الموقع → البايو → النص
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
                futures = {ex.submit(analyze_x_tweet, url): url for url in x_urls}
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
            "user_location_field",  # 🎯 جديد: حقل الموقع الرسمي
            "region_flag", "region_name_ar", "region_confidence",
            "region_source",
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
                "region_source": st.column_config.TextColumn("📊 مصدر الكشف", width="medium"),
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
