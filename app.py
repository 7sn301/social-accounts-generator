# ============================================================
# app.py - Social Accounts Generator & OSINT Tool v11.0
# ============================================================
# يجب رفع هذا الملف على GitHub ليحل محل الملف الحالي (HTML)
# ============================================================

import streamlit as st
import os
import sys
import json
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─── إعداد المسار ───────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ─── استيراد الموديلات الخارجية بأمان ──────────────────────
try:
    from x_analyzer import analyze_x_account, analyze_x_tweet
    X_ANALYZER_AVAILABLE = True
    X_ANALYZER_ERROR = None
except Exception as e:
    X_ANALYZER_AVAILABLE = False
    X_ANALYZER_ERROR = str(e)

try:
    from tiktok_analyzer import (
        analyze_tiktok_profile,
        analyze_tiktok_video,
        TIKTOK_REGION_MAP,
    )
    TIKTOK_ANALYZER_AVAILABLE = True
    TIKTOK_ANALYZER_ERROR = None
except Exception as e:
    TIKTOK_ANALYZER_AVAILABLE = False
    TIKTOK_ANALYZER_ERROR = str(e)

try:
    from twitter_osint import (
        build_advanced_search_url,
        geocode_location,
        get_famous_arab_cities,
        analyze_tweet_timestamps,
        build_map_verification_links,
    )
    TWITTER_OSINT_AVAILABLE = True
    TWITTER_OSINT_ERROR = None
except Exception as e:
    TWITTER_OSINT_AVAILABLE = False
    TWITTER_OSINT_ERROR = str(e)

try:
    from tiktok_osint import (
        geocode_tiktok_place,
        build_tiktok_search_links,
        build_tiktok_user_search,
        build_tiktok_verification_links,
        build_tt_map_links,
        infer_user_location_from_videos,
        analyze_timezone_from_videos,
        get_tiktok_region_center,
        FAMOUS_LOCATIONS_TT,
    )
    TIKTOK_OSINT_AVAILABLE = True
    TIKTOK_OSINT_ERROR = None
except Exception as e:
    TIKTOK_OSINT_AVAILABLE = False
    TIKTOK_OSINT_ERROR = str(e)

try:
    from geo_engine import analyze_image_full
    GEO_ENGINE_AVAILABLE = True
    GEO_ENGINE_ERROR = None
except Exception as e:
    GEO_ENGINE_AVAILABLE = False
    GEO_ENGINE_ERROR = str(e)

try:
    from vpn_detector import investigate
    VPN_DETECTOR_AVAILABLE = True
    VPN_DETECTOR_ERROR = None
except Exception as e:
    VPN_DETECTOR_AVAILABLE = False
    VPN_DETECTOR_ERROR = str(e)

try:
    from report_exporter import generate_word_report, generate_pptx_report
    REPORT_EXPORTER_AVAILABLE = True
    REPORT_EXPORTER_ERROR = None
except Exception as e:
    REPORT_EXPORTER_AVAILABLE = False
    REPORT_EXPORTER_ERROR = str(e)

try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except Exception:
    FOLIUM_AVAILABLE = False

# ─── إعداد Gemini ──────────────────────────────────────────
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
except Exception:
    GEMINI_AVAILABLE = False

# ============================================================
# إعداد الصفحة
# ============================================================
st.set_page_config(
    page_title="محلل الحسابات الاجتماعية v11.0",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS داخل st.markdown (الطريقة الصحيحة) ────────────────
st.markdown(
    """
    <style>
        /* الخط العربي */
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');

        /* الخلفية العامة */
        .stApp {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: 'Cairo', sans-serif;
        }

        /* RTL */
        .rtl {
            direction: rtl;
            text-align: right;
        }

        /* الشريط الجانبي */
        [data-testid="stSidebar"] {
            background: rgba(255,255,255,0.07);
            backdrop-filter: blur(12px);
            border-right: 1px solid rgba(255,255,255,0.15);
        }
        [data-testid="stSidebar"] * {
            color: #ffffff !important;
        }

        /* البطاقات */
        .card {
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 16px;
            padding: 20px;
            backdrop-filter: blur(10px);
            margin-bottom: 16px;
        }

        /* صناديق المعلومات */
        .info-box {
            background: rgba(102,126,234,0.25);
            border-left: 4px solid #667eea;
            border-radius: 8px;
            padding: 12px 16px;
            margin: 10px 0;
            direction: rtl;
            color: #ffffff;
        }

        .warn-box {
            background: rgba(234,180,102,0.25);
            border-left: 4px solid #eab466;
            border-radius: 8px;
            padding: 12px 16px;
            margin: 10px 0;
            direction: rtl;
            color: #ffffff;
        }

        .success-box {
            background: rgba(72,199,142,0.25);
            border-left: 4px solid #48c78e;
            border-radius: 8px;
            padding: 12px 16px;
            margin: 10px 0;
            direction: rtl;
            color: #ffffff;
        }

        /* الأزرار */
        .stButton > button {
            background: linear-gradient(135deg, #667eea, #764ba2) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            font-family: 'Cairo', sans-serif !important;
            font-weight: 700 !important;
            padding: 10px 20px !important;
            transition: all 0.3s ease !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 25px rgba(102,126,234,0.5) !important;
        }

        /* حقول الإدخال */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > select {
            background: rgba(255,255,255,0.1) !important;
            border: 1px solid rgba(255,255,255,0.3) !important;
            border-radius: 8px !important;
            color: #ffffff !important;
            font-family: 'Cairo', sans-serif !important;
        }

        /* العنوان الرئيسي */
        .main-title {
            text-align: center;
            color: white;
            font-family: 'Cairo', sans-serif;
            font-size: 2.5rem;
            font-weight: 900;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
            margin-bottom: 8px;
        }

        .sub-title {
            text-align: center;
            color: rgba(255,255,255,0.8);
            font-family: 'Cairo', sans-serif;
            font-size: 1rem;
            margin-bottom: 20px;
        }

        /* Badge الحالة */
        .badge-green  { color: #48c78e; font-weight: bold; }
        .badge-red    { color: #f14668; font-weight: bold; }
        .badge-yellow { color: #ffe08a; font-weight: bold; }

        /* Dataframe */
        .stDataFrame { border-radius: 10px; overflow: hidden; }

        /* Metric */
        [data-testid="stMetricValue"] { color: white !important; }
        [data-testid="stMetricLabel"] { color: rgba(255,255,255,0.7) !important; }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            background: rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 4px;
        }
        .stTabs [data-baseweb="tab"] {
            color: rgba(255,255,255,0.7) !important;
            font-family: 'Cairo', sans-serif !important;
            border-radius: 8px !important;
        }
        .stTabs [aria-selected="true"] {
            background: rgba(102,126,234,0.5) !important;
            color: white !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# تهيئة session_state
# ============================================================
DEFAULTS = {
    "x_result": None,
    "x_tweet_result": None,
    "tiktok_profile_result": None,
    "video_results": [],
    "geo_result": None,
    "vpn_result": None,
    "report_results": [],
    "gemini_api_key": "",
    "max_workers": 3,
}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

max_workers = st.session_state["max_workers"]

# ============================================================
# الشريط الجانبي
# ============================================================
with st.sidebar:
    st.markdown(
        """
        <div style='text-align:center; padding: 10px 0;'>
            <span style='font-size:3rem;'>🕵️</span>
            <h2 style='color:white; font-family:Cairo; margin:0;'>OSINT Pro</h2>
            <small style='color:rgba(255,255,255,0.6);'>v11.0 | Social Analyzer</small>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # مفتاح Gemini
    st.markdown("### 🔑 مفتاح Gemini API")
    gemini_key_input = st.text_input(
        "أدخل مفتاح Gemini API:",
        type="password",
        value=st.session_state["gemini_api_key"],
        placeholder="AIzaSy...",
        key="sidebar_gemini_key",
    )
    if gemini_key_input != st.session_state["gemini_api_key"]:
        st.session_state["gemini_api_key"] = gemini_key_input
        if gemini_key_input:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key_input)
                GEMINI_AVAILABLE = True
                st.success("✅ تم تفعيل Gemini")
            except Exception as e:
                st.error(f"❌ خطأ: {e}")
        os.environ["GEMINI_API_KEY"] = gemini_key_input

    st.markdown("---")

    # عدد الخيوط
    st.markdown("### ⚙️ إعدادات")
    max_workers = st.slider("عدد الخيوط المتوازية:", 1, 10, 3)
    st.session_state["max_workers"] = max_workers

    st.markdown("---")

    # حالة الموديلات
    st.markdown("### 📦 حالة الموديلات")
    modules = {
        "🐦 X Analyzer":      X_ANALYZER_AVAILABLE,
        "🎵 TikTok Analyzer": TIKTOK_ANALYZER_AVAILABLE,
        "🔍 Twitter OSINT":   TWITTER_OSINT_AVAILABLE,
        "🎭 TikTok OSINT":    TIKTOK_OSINT_AVAILABLE,
        "🌍 Geo Engine":      GEO_ENGINE_AVAILABLE,
        "🛡️ VPN Detector":    VPN_DETECTOR_AVAILABLE,
        "📑 Report Exporter": REPORT_EXPORTER_AVAILABLE,
        "🗺️ Folium Maps":     FOLIUM_AVAILABLE,
        "🤖 Gemini AI":       GEMINI_AVAILABLE,
    }
    for name, status in modules.items():
        icon = "🟢" if status else "🔴"
        st.markdown(f"{icon} {name}")

    st.markdown("---")
    st.caption("© 2025 OSINT Social Analyzer v11.0")

# ============================================================
# العنوان الرئيسي
# ============================================================
st.markdown(
    """
    <div class='main-title'>🕵️ محلل الحسابات الاجتماعية</div>
    <div class='sub-title'>أداة OSINT متكاملة | X · TikTok · 14 منصة اجتماعية | v11.0</div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# التبويبات الرئيسية
# ============================================================
(
    tab_x,
    tab_x_tweet,
    tab_x_osint,
    tab_tiktok,
    tab_tiktok_video,
    tab_tiktok_osint,
    tab_geo,
    tab_vpn,
    tab_report,
    tab_about,
) = st.tabs([
    "🐦 تحليل حساب X",
    "📝 تحليل تغريدة",
    "🔍 OSINT Twitter",
    "🎵 تحليل TikTok",
    "🎬 تحليل فيديو TikTok",
    "🕵️ OSINT TikTok",
    "🌍 محرك الجغرافيا",
    "🛡️ كاشف VPN",
    "📑 تصدير التقارير",
    "ℹ️ حول التطبيق",
])

# ============================================================
# 🐦 تحليل حساب X
# ============================================================
with tab_x:
    st.markdown("### 🐦 تحليل حساب X (تويتر)")
    st.markdown(
        """
        <div class='info-box'>
        يحلل حسابات X باستخدام 7 طبقات كشف مع قاموس مدن موسّع (500+ مدينة)
        وتحليل صور المنشورات بالذكاء الاصطناعي.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not X_ANALYZER_AVAILABLE:
        st.error(f"❌ x_analyzer.py غير متوفر: {X_ANALYZER_ERROR}")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            x_username = st.text_input(
                "اسم مستخدم X (بدون @):",
                placeholder="elonmusk",
                key="x_username_input",
            )
        with col2:
            x_tweet_count = st.number_input("عدد التغريدات:", 5, 50, 20, key="x_tweet_count")

        analyze_x_btn = st.button("🚀 تحليل الحساب", type="primary", use_container_width=True, key="btn_analyze_x")

        if analyze_x_btn:
            if not x_username.strip():
                st.error("❌ أدخل اسم المستخدم")
            else:
                username_clean = x_username.strip().lstrip("@")
                with st.spinner(f"جارٍ تحليل @{username_clean}..."):
                    try:
                        result = analyze_x_account(
                            username_clean,
                            tweet_count=int(x_tweet_count),
                            gemini_key=st.session_state["gemini_api_key"],
                        )
                        st.session_state["x_result"] = result
                    except Exception as exc:
                        st.error(f"❌ خطأ في التحليل: {exc}")
                        st.session_state["x_result"] = None

        result = st.session_state.get("x_result")
        if result:
            if result.get("error"):
                st.error(f"❌ {result['error']}")
            else:
                # ملخص الحساب
                profile = result.get("profile", {})
                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("👤 المتابِعون", f"{profile.get('followers_count', 0):,}")
                col_b.metric("📝 التغريدات", f"{profile.get('tweets_count', 0):,}")
                col_c.metric("🎯 الثقة", f"{result.get('confidence', 0)}%")
                col_d.metric("🌍 الدولة", result.get("country_flag", "🌍") + " " + result.get("country_name_ar", "—"))

                # الموقع
                final_country = result.get("country_name_ar", "غير محدد")
                final_flag = result.get("country_flag", "🌍")
                confidence = result.get("confidence", 0)

                if confidence >= 70:
                    st.success(f"📍 الموقع المحتمل: {final_flag} {final_country} — ثقة {confidence}%")
                elif confidence >= 40:
                    st.warning(f"📍 الموقع المحتمل: {final_flag} {final_country} — ثقة {confidence}%")
                else:
                    st.info(f"📍 الموقع المحتمل: {final_flag} {final_country} — ثقة {confidence}%")

                # الطبقات
                layers = result.get("layers", {})
                if layers:
                    st.markdown("#### 🔬 طبقات التحليل")
                    rows = []
                    for layer_name, layer_data in layers.items():
                        if isinstance(layer_data, dict):
                            rows.append({
                                "الطبقة": layer_name,
                                "النتيجة": layer_data.get("country_name_ar", "—"),
                                "الثقة": f"{layer_data.get('confidence', 0)}%",
                                "المصدر": layer_data.get("source", "—"),
                            })
                    if rows:
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

                # التغريدات
                tweets = result.get("tweets", [])
                if tweets:
                    st.markdown(f"#### 📝 آخر {len(tweets)} تغريدة")
                    tweet_rows = []
                    for tw in tweets:
                        tweet_rows.append({
                            "النص": tw.get("text", "")[:120],
                            "التاريخ": tw.get("date", ""),
                            "الإعجابات": tw.get("likes", 0),
                            "الرتويت": tw.get("retweets", 0),
                        })
                    st.dataframe(pd.DataFrame(tweet_rows), use_container_width=True, hide_index=True)

                # تصدير JSON
                export_data = json.dumps(result, ensure_ascii=False, indent=2)
                st.download_button(
                    "📥 تصدير JSON",
                    data=export_data.encode("utf-8"),
                    file_name=f"x_analysis_{x_username}.json",
                    mime="application/json",
                    use_container_width=True,
                )

# ============================================================
# 📝 تحليل تغريدة
# ============================================================
with tab_x_tweet:
    st.markdown("### 📝 تحليل تغريدة محددة")
    st.markdown(
        """
        <div class='info-box'>
        حلّل تغريدة محددة لاستخراج الموقع الجغرافي، الصور، والبيانات الوصفية.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not X_ANALYZER_AVAILABLE:
        st.error(f"❌ x_analyzer.py غير متوفر: {X_ANALYZER_ERROR}")
    else:
        tweet_url = st.text_input(
            "رابط التغريدة:",
            placeholder="https://x.com/username/status/1234567890",
            key="tweet_url_input",
        )

        analyze_tweet_btn = st.button("🔍 تحليل التغريدة", type="primary", use_container_width=True, key="btn_analyze_tweet")

        if analyze_tweet_btn:
            if not tweet_url.strip():
                st.error("❌ أدخل رابط التغريدة")
            else:
                with st.spinner("جارٍ تحليل التغريدة..."):
                    try:
                        tweet_result = analyze_x_tweet(
                            tweet_url.strip(),
                            gemini_key=st.session_state["gemini_api_key"],
                        )
                        st.session_state["x_tweet_result"] = tweet_result
                    except Exception as exc:
                        st.error(f"❌ خطأ: {exc}")
                        st.session_state["x_tweet_result"] = None

        tweet_result = st.session_state.get("x_tweet_result")
        if tweet_result:
            if tweet_result.get("error"):
                st.error(f"❌ {tweet_result['error']}")
            else:
                col1, col2, col3 = st.columns(3)
                col1.metric("🌍 الدولة", tweet_result.get("country_flag", "🌍") + " " + tweet_result.get("country_name_ar", "—"))
                col2.metric("🎯 الثقة", f"{tweet_result.get('confidence', 0)}%")
                col3.metric("📸 الصور", len(tweet_result.get("photos", [])))

                st.markdown("#### 📄 نص التغريدة")
                st.write(tweet_result.get("text", "—"))

                photos = tweet_result.get("photos", [])
                if photos:
                    st.markdown("#### 🖼️ صور التغريدة")
                    photo_cols = st.columns(min(len(photos), 3))
                    for idx, photo_url in enumerate(photos[:3]):
                        with photo_cols[idx]:
                            try:
                                st.image(photo_url, use_column_width=True)
                            except Exception:
                                st.write(f"[صورة {idx+1}]({photo_url})")

# ============================================================
# 🔍 OSINT Twitter
# ============================================================
with tab_x_osint:
    st.markdown("### 🔍 محقق OSINT تويتر / X")
    st.markdown(
        """
        <div class='info-box'>
        أدوات OSINT متخصصة لـ X/Twitter: بحث جغرافي، بناء URLs متقدمة،
        تحليل أوقات النشر، وروابط تحقق سريعة.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not TWITTER_OSINT_AVAILABLE:
        st.error(f"❌ twitter_osint.py غير متوفر: {TWITTER_OSINT_ERROR}")
    else:
        osint_tabs = st.tabs(["🔍 بحث جغرافي", "⏰ تحليل التوقيت", "🔗 روابط التحقق"])

        with osint_tabs[0]:
            c1, c2 = st.columns(2)
            with c1:
                osint_location = st.text_input("المدينة / المنطقة:", placeholder="الرياض", key="osint_location")
                osint_radius = st.number_input("نطاق البحث (كم):", 1, 500, 50, key="osint_radius")
            with c2:
                osint_keyword = st.text_input("كلمة مفتاحية (اختياري):", key="osint_keyword")
                osint_username = st.text_input("حساب محدد (اختياري):", key="osint_username")

            if st.button("🔍 بناء رابط البحث", use_container_width=True, key="btn_osint_search"):
                if osint_location.strip():
                    try:
                        geo = geocode_location(osint_location.strip())
                        if geo:
                            url = build_advanced_search_url(
                                keywords=osint_keyword.strip() or None,
                                geocode=(geo["lat"], geo["lon"], osint_radius),
                                username=osint_username.strip() or None,
                            )
                            st.success(f"📍 {geo.get('display_name', osint_location)}")
                            st.link_button("🔗 فتح نتائج البحث في X", url, use_container_width=True)
                        else:
                            st.error("❌ تعذر تحديد الإحداثيات")
                    except Exception as e:
                        st.error(f"❌ خطأ: {e}")

        with osint_tabs[2]:
            verify_username = st.text_input("اسم المستخدم للتحقق:", key="verify_x_username")
            if st.button("🔗 روابط التحقق", use_container_width=True, key="btn_verify_x"):
                if verify_username.strip():
                    uname = verify_username.strip().lstrip("@")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.link_button("🐦 ملف X", f"https://x.com/{uname}", use_container_width=True)
                    with c2:
                        st.link_button("🕰️ Wayback", f"https://web.archive.org/web/*/x.com/{uname}", use_container_width=True)
                    with c3:
                        st.link_button("🔍 Google", f"https://www.google.com/search?q=site:x.com+{uname}", use_container_width=True)

# ============================================================
# 🎵 تحليل TikTok
# ============================================================
with tab_tiktok:
    st.markdown("### 🎵 تحليل حساب TikTok")
    st.markdown(
        """
        <div class='info-box'>
        يحلل حسابات TikTok لاستخراج الموقع من البروفايل والبايو واللهجة والفيديوهات.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not TIKTOK_ANALYZER_AVAILABLE:
        st.error(f"❌ tiktok_analyzer.py غير متوفر: {TIKTOK_ANALYZER_ERROR}")
    else:
        tt_username = st.text_input(
            "اسم مستخدم TikTok (بدون @):",
            placeholder="khaby.lame",
            key="tt_username_input",
        )

        analyze_tt_btn = st.button("🚀 تحليل الحساب", type="primary", use_container_width=True, key="btn_analyze_tt")

        if analyze_tt_btn:
            if not tt_username.strip():
                st.error("❌ أدخل اسم المستخدم")
            else:
                tt_clean = tt_username.strip().lstrip("@")
                with st.spinner(f"جارٍ تحليل @{tt_clean}..."):
                    try:
                        tt_result = analyze_tiktok_profile(tt_clean)
                        st.session_state["tiktok_profile_result"] = tt_result
                    except Exception as exc:
                        st.error(f"❌ خطأ: {exc}")
                        st.session_state["tiktok_profile_result"] = None

        tt_result = st.session_state.get("tiktok_profile_result")
        if tt_result:
            if tt_result.get("error"):
                st.error(f"❌ {tt_result['error']}")
            else:
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("👥 المتابعون", f"{tt_result.get('followers', 0):,}")
                col_b.metric("❤️ الإعجابات", f"{tt_result.get('total_likes', 0):,}")
                col_c.metric("🌍 الموقع", tt_result.get("country_flag", "🌍") + " " + tt_result.get("country_name_ar", "—"))

                export_tt = json.dumps(tt_result, ensure_ascii=False, indent=2)
                st.download_button(
                    "📥 تصدير JSON",
                    data=export_tt.encode("utf-8"),
                    file_name=f"tiktok_{tt_username}.json",
                    mime="application/json",
                    use_container_width=True,
                )

# ============================================================
# 🎬 تحليل فيديو TikTok
# ============================================================
with tab_tiktok_video:
    st.markdown("### 🎬 تحليل فيديوهات TikTok")
    st.markdown(
        """
        <div class='info-box'>
        يستخرج locationCreated وauthor.region وبيانات الموقع من فيديوهات TikTok.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not TIKTOK_ANALYZER_AVAILABLE:
        st.error(f"❌ tiktok_analyzer.py غير متوفر: {TIKTOK_ANALYZER_ERROR}")
    else:
        tt_video_urls = st.text_area(
            "روابط الفيديوهات (رابط في كل سطر):",
            height=150,
            placeholder="https://www.tiktok.com/@username/video/1234567890",
            key="tt_video_urls_input",
        )

        analyze_tt_video_btn = st.button(
            "🎬 تحليل الفيديوهات",
            type="primary",
            use_container_width=True,
            key="btn_analyze_tt_video",
        )

        if analyze_tt_video_btn:
            urls = [u.strip() for u in tt_video_urls.splitlines() if u.strip() and "tiktok.com" in u.lower()]
            if not urls:
                st.error("❌ أدخل روابط فيديو TikTok صحيحة")
            else:
                with st.spinner(f"جارٍ تحليل {len(urls)} فيديو..."):
                    results_list = []
                    with ThreadPoolExecutor(max_workers=max_workers) as ex:
                        futures = {ex.submit(analyze_tiktok_video, url): url for url in urls}
                        prog = st.progress(0)
                        for i, future in enumerate(as_completed(futures)):
                            try:
                                results_list.append(future.result())
                            except Exception as exc:
                                results_list.append({"video_url": futures[future], "status": "❌", "error": str(exc)})
                            prog.progress((i + 1) / len(urls))
                    st.session_state["video_results"] = results_list
                    st.success(f"✅ تم تحليل {len(results_list)} فيديو!")

        video_results = st.session_state.get("video_results", [])
        if video_results:
            df_videos = pd.DataFrame([{
                "الرابط": r.get("video_url", "")[:60],
                "الحالة": r.get("status", ""),
                "الموقع": r.get("location_created", "—"),
                "المنطقة": r.get("author_region", "—"),
                "الإعجابات": r.get("likes", 0),
                "المشاهدات": r.get("views", 0),
            } for r in video_results])
            st.dataframe(df_videos, use_container_width=True, hide_index=True)

            csv_data = df_videos.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 تصدير CSV",
                data=csv_data,
                file_name="tiktok_videos_analysis.csv",
                mime="text/csv",
                use_container_width=True,
            )

# ============================================================
# 🕵️ OSINT TikTok
# ============================================================
with tab_tiktok_osint:
    st.markdown("### 🕵️ محقق OSINT تيك توك")
    st.markdown(
        """
        <div class='info-box'>
        أدوات OSINT متخصصة لتيك توك: استنتاج الموقع من الفيديوهات، بناء روابط بحث جغرافي،
        تحليل نمط النشر الزمني، خريطة للدول المكتشفة، وروابط تحقق سريعة.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not TIKTOK_OSINT_AVAILABLE:
        st.error(f"❌ tiktok_osint.py غير متوفر: {TIKTOK_OSINT_ERROR}")
        st.stop()

    # تهيئة المفاتيح
    for _k in (
        "tt_osint_location_report", "tt_osint_timezone_report",
        "tt_osint_geo_search", "tt_osint_user_geo_links", "tt_osint_verification_links",
    ):
        st.session_state.setdefault(_k, None)

    sub1, sub2, sub3, sub4, sub5 = st.tabs([
        "🔍 تحديد الموقع عبر الفيديوهات",
        "🌐 بحث TikTok الجغرافي",
        "⏰ تحليل نمط النشر",
        "🗺️ خريطة المواقع",
        "🔗 روابط التحقق",
    ])

    with sub1:
        current_video_results = st.session_state.get("video_results") or []
        if current_video_results:
            st.success(f"تم العثور على {len(current_video_results)} نتيجة فيديو محفوظة")
            if st.button("🔍 تحليل مواقع الفيديوهات", use_container_width=True, key="tt_osint_existing_videos"):
                st.session_state["tt_osint_location_report"] = infer_user_location_from_videos(current_video_results)

            location_report = st.session_state.get("tt_osint_location_report")
            if location_report:
                probable_code = location_report.get("probable_country_code", "")
                probable_flag = location_report.get("probable_flag", "🌍")
                probable_name = location_report.get("probable_country_name_ar", "غير محدد")
                confidence = int(location_report.get("confidence", 0) or 0)

                if probable_code and confidence >= 40:
                    st.success(f"الموقع المحتمل: {probable_flag} {probable_name} — ثقة {confidence}%")
                else:
                    st.warning(f"النتيجة مبدئية: {probable_flag} {probable_name} — ثقة {confidence}%")

                m1, m2, m3 = st.columns(3)
                m1.metric("عدد الفيديوهات", location_report.get("total_videos", 0))
                m2.metric("له موقع", location_report.get("videos_with_location", 0))
                m3.metric("الثقة", f"{confidence}%")
        else:
            st.markdown(
                """
                <div class='warn-box'>
                لم يتم تحليل فيديوهات بعد. اذهب لتبويب 🎬 تحليل فيديو TikTok
                </div>
                """,
                unsafe_allow_html=True,
            )

    with sub5:
        verification_username = st.text_input("أدخل اسم مستخدم TikTok", key="tt_osint_verify_username")
        if st.button("🔗 أنشئ روابط التحقق", use_container_width=True, key="tt_osint_build_verification"):
            if verification_username.strip():
                st.session_state["tt_osint_verification_links"] = build_tiktok_verification_links(verification_username.strip())

        verification_links = st.session_state.get("tt_osint_verification_links")
        if verification_links:
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                st.link_button("🎵 TikTok", verification_links["tiktok_profile"], use_container_width=True)
            with c2:
                st.link_button("🕰️ Wayback", verification_links["wayback"], use_container_width=True)
            with c3:
                st.link_button("🔍 Google", verification_links["google"], use_container_width=True)
            with c4:
                st.link_button("🦅 Yandex", verification_links["yandex"], use_container_width=True)
            with c5:
                st.link_button("🐦 Urlebird", verification_links["urlebird"], use_container_width=True)

# ============================================================
# 🌍 محرك الجغرافيا
# ============================================================
with tab_geo:
    st.markdown("### 🌍 محرك الجغرافيا - GeoSpy Style")
    st.markdown(
        """
        <div class='info-box'>
        تحليل متعدد الطبقات للصور: EXIF، بحث عكسي للصور، تحليل AI، وتثليث الموقع.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not GEO_ENGINE_AVAILABLE:
        st.error(f"❌ geo_engine.py غير متوفر: {GEO_ENGINE_ERROR}")
    else:
        geo_image_url = st.text_input(
            "رابط الصورة:",
            placeholder="https://example.com/image.jpg",
            key="geo_image_url",
        )

        analyze_geo_btn = st.button("🌍 تحليل الصورة", type="primary", use_container_width=True, key="btn_analyze_geo")

        if analyze_geo_btn:
            if not geo_image_url.strip():
                st.error("❌ أدخل رابط الصورة")
            else:
                with st.spinner("جارٍ تحليل الصورة..."):
                    try:
                        geo_result = analyze_image_full(
                            geo_image_url.strip(),
                            gemini_key=st.session_state["gemini_api_key"],
                        )
                        st.session_state["geo_result"] = geo_result
                    except Exception as exc:
                        st.error(f"❌ خطأ: {exc}")
                        st.session_state["geo_result"] = None

        geo_result = st.session_state.get("geo_result")
        if geo_result:
            col1, col2, col3 = st.columns(3)
            col1.metric("🌍 الدولة", geo_result.get("country_flag", "🌍") + " " + geo_result.get("country_name_ar", "—"))
            col2.metric("🎯 الثقة", f"{geo_result.get('confidence', 0)}%")
            col3.metric("📍 الإحداثيات", f"{geo_result.get('lat', 0):.4f}, {geo_result.get('lon', 0):.4f}")

            exif_data = geo_result.get("exif", {})
            if exif_data:
                st.markdown("#### 📷 بيانات EXIF")
                st.json(exif_data)

# ============================================================
# 🛡️ كاشف VPN
# ============================================================
with tab_vpn:
    st.markdown("### 🛡️ كاشف VPN والموقع الحقيقي")
    st.markdown(
        """
        <div class='info-box'>
        يكشف استخدام VPN ويحدد الموقع الحقيقي للمستخدم من خلال 8 إشارات مستقلة.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not VPN_DETECTOR_AVAILABLE:
        st.error(f"❌ vpn_detector.py غير متوفر: {VPN_DETECTOR_ERROR}")
    else:
        vpn_username = st.text_input(
            "اسم مستخدم X للتحليل:",
            placeholder="username",
            key="vpn_username_input",
        )

        analyze_vpn_btn = st.button("🛡️ كشف VPN", type="primary", use_container_width=True, key="btn_analyze_vpn")

        if analyze_vpn_btn:
            if not vpn_username.strip():
                st.error("❌ أدخل اسم المستخدم")
            else:
                with st.spinner("جارٍ التحليل..."):
                    try:
                        vpn_result = investigate(
                            vpn_username.strip().lstrip("@"),
                            gemini_key=st.session_state["gemini_api_key"],
                        )
                        st.session_state["vpn_result"] = vpn_result
                    except Exception as exc:
                        st.error(f"❌ خطأ: {exc}")
                        st.session_state["vpn_result"] = None

        vpn_result = st.session_state.get("vpn_result")
        if vpn_result:
            risk = vpn_result.get("vpn_risk_score", 0)
            col1, col2, col3 = st.columns(3)
            col1.metric("🛡️ خطر VPN", f"{risk}%")
            col2.metric("🌍 الموقع المُعلن", vpn_result.get("declared_country", "—"))
            col3.metric("📍 الموقع الحقيقي", vpn_result.get("real_country_flag", "🌍") + " " + vpn_result.get("real_country_ar", "—"))

            if risk >= 70:
                st.error(f"⚠️ احتمال مرتفع لاستخدام VPN ({risk}%)")
            elif risk >= 40:
                st.warning(f"⚠️ احتمال متوسط لاستخدام VPN ({risk}%)")
            else:
                st.success(f"✅ لا يوجد دليل على استخدام VPN ({risk}%)")

# ============================================================
# 📑 تصدير التقارير
# ============================================================
with tab_report:
    st.markdown("### 📑 تصدير التقارير الاحترافية")
    st.markdown(
        """
        <div class='info-box'>
        إنشاء تقارير Word و PowerPoint احترافية بتنسيق RTL عربي كامل.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not REPORT_EXPORTER_AVAILABLE:
        st.error(f"❌ report_exporter.py غير متوفر: {REPORT_EXPORTER_ERROR}")
    else:
        report_title = st.text_input("عنوان التقرير:", value="تقرير تحليل الحسابات الاجتماعية", key="report_title")

        col1, col2 = st.columns(2)
        with col1:
            gen_word = st.button("📄 إنشاء تقرير Word", use_container_width=True, key="btn_gen_word")
        with col2:
            gen_pptx = st.button("📊 إنشاء تقرير PowerPoint", use_container_width=True, key="btn_gen_pptx")

        # جمع كل النتائج
        all_results = []
        if st.session_state.get("x_result"):
            all_results.append(st.session_state["x_result"])
        if st.session_state.get("x_tweet_result"):
            all_results.append(st.session_state["x_tweet_result"])
        if st.session_state.get("tiktok_profile_result"):
            all_results.append(st.session_state["tiktok_profile_result"])

        if gen_word:
            if not all_results:
                st.warning("⚠️ لا توجد نتائج تحليل بعد. قم بتحليل حساب أولاً.")
            else:
                with st.spinner("جارٍ إنشاء تقرير Word..."):
                    try:
                        word_buffer = generate_word_report(all_results, title=report_title)
                        st.download_button(
                            "⬇️ تحميل تقرير Word",
                            data=word_buffer,
                            file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.error(f"❌ خطأ في إنشاء التقرير: {e}")

# ============================================================
# ℹ️ حول التطبيق
# ============================================================
with tab_about:
    st.markdown("### ℹ️ حول التطبيق")
    st.markdown(
        """
        <div class='card rtl'>
            <h3 style='color:white;'>🕵️ محلل الحسابات الاجتماعية v11.0</h3>
            <p style='color:rgba(255,255,255,0.8);'>
                أداة OSINT متكاملة لتحليل الحسابات الاجتماعية عبر 14 منصة.
            </p>
            <hr style='border-color:rgba(255,255,255,0.2);'>
            <h4 style='color:white;'>🔧 المميزات:</h4>
            <ul style='color:rgba(255,255,255,0.8);'>
                <li>✅ تحليل X/Twitter مع 7 طبقات كشف</li>
                <li>✅ تحليل TikTok مع metadata الفيديوهات</li>
                <li>✅ محرك جغرافيا متعدد الطبقات (GeoSpy Style)</li>
                <li>✅ كاشف VPN بـ 8 إشارات مستقلة</li>
                <li>✅ أدوات OSINT متخصصة</li>
                <li>✅ تصدير تقارير Word و PowerPoint</li>
                <li>✅ دعم كامل للغة العربية RTL</li>
                <li>✅ تكامل مع Gemini AI</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📦 الموديلات", "9")
    with col2:
        st.metric("🌐 المنصات", "14+")
    with col3:
        st.metric("🔬 طبقات الكشف", "7+")
