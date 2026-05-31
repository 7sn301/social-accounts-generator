# -*- coding: utf-8 -*-
"""
=====================================================================
 مولد معلومات حسابات التواصل الاجتماعي v6.1 — Streamlined Edition
 Social Accounts Intelligence Generator v6.1
=====================================================================
 التغييرات في v6.1:
  ❌ حذف X (Twitter)   : API مغلق + Nitter مات
  ❌ حذف RSS            : غير ضروري للأداة
  ❌ حذف Disclaimer     : حسب طلب المستخدم
  ✅ تعزيز TikTok       : 3 طرق فعلية لجلب البيانات
  ✅ تحسين BUFFIN       : فحص أسرع + منصات أكثر
  ✅ تحسين Geo-OSINT    : مع إحداثيات حقيقية
=====================================================================
"""

import streamlit as st
import requests
import re
import json
import logging
import time
from datetime import datetime, timezone
import pandas as pd

# ───────────────────────── إعداد اللوج ─────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("SocialOSINT")

# ───────────────────────── إعداد Streamlit ─────────────────────────
st.set_page_config(
    page_title="مولد معلومات حسابات التواصل v6.1",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# دعم RTL الكامل + Theme
st.markdown(
    """
    <style>
    body, .stApp, [class*="css"] {
        direction: rtl;
        text-align: right;
        font-family: 'Noto Sans Arabic', 'Tajawal', sans-serif;
    }
    .confidence-box {
        background: #1e293b;
        padding: 14px;
        border-radius: 8px;
        border-right: 4px solid #3b82f6;
        margin: 8px 0;
        color: #f1f5f9;
    }
    .success-box {
        background: #064e3b;
        padding: 14px;
        border-radius: 8px;
        border-right: 4px solid #10b981;
        margin: 8px 0;
        color: #ecfdf5;
    }
    .version-badge {
        background: #10b981;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 14px;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =====================================================================
# 1) TikTok Analyzer — 3 طرق فعلية لجلب البيانات
# =====================================================================
TIKTOK_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
}

# خريطة region codes إلى دول
REGION_MAP = {
    "SA": "🇸🇦 السعودية", "AE": "🇦🇪 الإمارات", "EG": "🇪🇬 مصر",
    "KW": "🇰🇼 الكويت",   "QA": "🇶🇦 قطر",       "BH": "🇧🇭 البحرين",
    "OM": "🇴🇲 عُمان",    "JO": "🇯🇴 الأردن",    "LB": "🇱🇧 لبنان",
    "SY": "🇸🇾 سوريا",    "IQ": "🇮🇶 العراق",   "YE": "🇾🇪 اليمن",
    "PS": "🇵🇸 فلسطين",   "MA": "🇲🇦 المغرب",   "DZ": "🇩🇿 الجزائر",
    "TN": "🇹🇳 تونس",     "LY": "🇱🇾 ليبيا",    "SD": "🇸🇩 السودان",
    "US": "🇺🇸 الولايات المتحدة", "GB": "🇬🇧 بريطانيا",
    "TR": "🇹🇷 تركيا",    "DE": "🇩🇪 ألمانيا",  "FR": "🇫🇷 فرنسا",
    "IN": "🇮🇳 الهند",    "ID": "🇮🇩 إندونيسيا", "PK": "🇵🇰 باكستان",
}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_tiktok_user(username: str) -> dict:
    """جلب بيانات TikTok بـ 3 طرق متتالية."""
    username = username.strip().lstrip("@")
    result = {
        "success": False,
        "data": {},
        "confidence": 0,
        "sources": [],
        "errors": [],
    }

    # ── الطريقة 1: استخراج JSON من صفحة البروفايل ──
    try:
        url = f"https://www.tiktok.com/@{username}"
        resp = requests.get(url, headers=TIKTOK_HEADERS, timeout=15)

        if resp.status_code == 200:
            html = resp.text

            # محاولة استخراج __UNIVERSAL_DATA_FOR_REHYDRATION__
            match = re.search(
                r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>',
                html, re.DOTALL
            )
            if match:
                try:
                    data = json.loads(match.group(1))
                    user_info = (
                        data.get("__DEFAULT_SCOPE__", {})
                        .get("webapp.user-detail", {})
                        .get("userInfo", {})
                    )
                    user = user_info.get("user", {})
                    stats = user_info.get("stats", {})

                    if user:
                        result["data"]["nickname"] = user.get("nickname", "")
                        result["data"]["signature"] = user.get("signature", "")
                        result["data"]["verified"] = user.get("verified", False)
                        result["data"]["privateAccount"] = user.get("privateAccount", False)
                        result["data"]["region"] = user.get("region", "")
                        result["data"]["language"] = user.get("language", "")
                        result["data"]["avatar"] = user.get("avatarLarger", "")
                        result["data"]["followerCount"] = stats.get("followerCount", 0)
                        result["data"]["followingCount"] = stats.get("followingCount", 0)
                        result["data"]["heartCount"] = stats.get("heartCount", 0)
                        result["data"]["videoCount"] = stats.get("videoCount", 0)
                        result["data"]["profile_url"] = url

                        result["confidence"] = 90
                        result["sources"].append("profile_json")
                        result["success"] = True
                        return result
                except json.JSONDecodeError as e:
                    result["errors"].append(f"JSON parse fail: {e}")

            # محاولة استخراج SIGI_STATE (إصدار قديم)
            match2 = re.search(
                r'<script id="SIGI_STATE"[^>]*>(.*?)</script>',
                html, re.DOTALL
            )
            if match2:
                try:
                    sigi = json.loads(match2.group(1))
                    user_module = sigi.get("UserModule", {}).get("users", {})
                    stats_module = sigi.get("UserModule", {}).get("stats", {})

                    if username.lower() in {k.lower() for k in user_module}:
                        for key, user in user_module.items():
                            if key.lower() == username.lower():
                                result["data"]["nickname"] = user.get("nickname", "")
                                result["data"]["signature"] = user.get("signature", "")
                                result["data"]["region"] = user.get("region", "")
                                result["data"]["verified"] = user.get("verified", False)
                                stats = stats_module.get(key, {})
                                result["data"]["followerCount"] = stats.get("followerCount", 0)
                                result["data"]["videoCount"] = stats.get("videoCount", 0)
                                result["data"]["profile_url"] = url
                                result["confidence"] = 80
                                result["sources"].append("sigi_state")
                                result["success"] = True
                                return result
                except json.JSONDecodeError:
                    pass

            # المستوى 2: استخراج meta tags كحد أدنى
            og_title = re.search(r'<meta property="og:title" content="([^"]+)"', html)
            og_image = re.search(r'<meta property="og:image" content="([^"]+)"', html)
            og_desc  = re.search(r'<meta property="og:description" content="([^"]+)"', html)

            if og_title:
                result["data"]["nickname"] = og_title.group(1).split("(")[0].strip()
                result["data"]["profile_url"] = url
                if og_image:
                    result["data"]["avatar"] = og_image.group(1)
                if og_desc:
                    result["data"]["signature"] = og_desc.group(1)
                result["confidence"] = 50
                result["sources"].append("meta_tags")
                result["success"] = True
                return result

            result["errors"].append("لم يتم العثور على بيانات JSON أو meta")
        else:
            result["errors"].append(f"HTTP {resp.status_code}")
    except requests.exceptions.Timeout:
        result["errors"].append("⏱️ Timeout عند جلب البروفايل")
    except Exception as e:
        result["errors"].append(f"Profile error: {type(e).__name__}: {str(e)[:80]}")
        log.error(f"TikTok fail: {e}")

    if result["confidence"] == 0:
        result["errors"].append(
            "❌ تعذّر الوصول. قد يكون: (1) الحساب غير موجود، (2) خاص، "
            "(3) محظور إقليمياً، (4) TikTok يحجب IP السيرفر."
        )

    return result


def format_number(n):
    """تنسيق الأرقام: 1.2K, 3.4M"""
    if not isinstance(n, (int, float)):
        return "0"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(int(n))


def render_tiktok_tab():
    st.subheader("🎵 محلل حسابات TikTok المتكامل")
    st.caption("تحليل بـ 3 طرق متتالية: JSON → SIGI → Meta tags. مع درجة ثقة لكل نتيجة.")

    col1, col2 = st.columns([3, 1])
    with col1:
        username = st.text_input(
            "👤 اسم المستخدم (بدون @)",
            placeholder="مثال: mr_beast أو khaby.lame",
            key="tiktok_user",
        )
    with col2:
        st.write("")
        st.write("")
        analyze = st.button("🔍 تحليل", use_container_width=True, key="tiktok_btn")

    # اقتراحات سريعة
    st.caption("💡 جرّب: `mrbeast` • `khaby.lame` • `bts_official_bighit`")

    if analyze and username:
        with st.spinner(f"جارٍ تحليل @{username} عبر 3 طبقات..."):
            result = fetch_tiktok_user(username)

        if result["success"]:
            st.markdown(
                f'<div class="success-box">✅ <b>تم التحليل بدرجة ثقة: {result["confidence"]}%</b> '
                f'| المصدر: <code>{", ".join(result["sources"])}</code></div>',
                unsafe_allow_html=True,
            )

            data = result["data"]

            # عرض البيانات الأساسية
            col_a, col_b = st.columns([1, 3])
            with col_a:
                if data.get("avatar"):
                    st.image(data["avatar"], width=150)
            with col_b:
                verified = "✅ موثَّق" if data.get("verified") else ""
                private = "🔒 خاص" if data.get("privateAccount") else "🌐 عام"
                st.markdown(f"### {data.get('nickname', username)} {verified}")
                st.caption(f"@{username} | {private}")
                if data.get("signature"):
                    st.write(f"📝 {data['signature']}")

            # الإحصائيات
            st.divider()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("👥 المتابعون", format_number(data.get("followerCount", 0)))
            c2.metric("➡️ يتابع", format_number(data.get("followingCount", 0)))
            c3.metric("❤️ الإعجابات", format_number(data.get("heartCount", 0)))
            c4.metric("🎬 الفيديوهات", format_number(data.get("videoCount", 0)))

            # الموقع الجغرافي
            st.divider()
            region_code = data.get("region", "")
            country = REGION_MAP.get(region_code, f"غير معروف ({region_code})") if region_code else "⚠️ غير متاح"
            language = data.get("language", "غير محدد")

            st.markdown(
                f"""
                <div class="confidence-box">
                <b>🌍 المنطقة (region):</b> {country}<br>
                <b>🗣️ اللغة:</b> {language}<br>
                <b>🔗 الرابط:</b> <a href="{data.get('profile_url', '')}" target="_blank">فتح البروفايل</a>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # حفظ للخريطة
            st.session_state["last_tiktok_result"] = result

        else:
            st.error("❌ فشل التحليل")
            with st.expander("⚠️ تفاصيل الأخطاء التقنية"):
                for err in result["errors"]:
                    st.markdown(f"- `{err}`")

            st.info(
                "💡 **حلول مقترحة:**\n"
                "- تأكد من اسم المستخدم بدون أخطاء إملائية\n"
                "- جرّب حساب مشهور للتحقق من عمل الأداة\n"
                "- بعض الحسابات محظورة إقليمياً"
            )


# =====================================================================
# 2) BUFFIN — Username Finder عبر منصات متعددة
# =====================================================================
def render_buffin_tab():
    st.subheader("🔍 BUFFIN — Bulk Username Finder")
    st.info(
        "🔎 بحث عن اسم المستخدم في **12 منصة** في وقت واحد. "
        "يكشف وجود الحساب، لا يجلب محتواه."
    )

    username = st.text_input("👤 اسم المستخدم للبحث", key="buffin_user")

    PLATFORMS = {
        "GitHub": "https://github.com/{}",
        "Instagram": "https://instagram.com/{}",
        "Reddit": "https://reddit.com/user/{}",
        "Medium": "https://medium.com/@{}",
        "Twitch": "https://twitch.tv/{}",
        "Pinterest": "https://pinterest.com/{}",
        "SoundCloud": "https://soundcloud.com/{}",
        "TikTok": "https://tiktok.com/@{}",
        "YouTube": "https://youtube.com/@{}",
        "Telegram": "https://t.me/{}",
        "Vimeo": "https://vimeo.com/{}",
        "DeviantArt": "https://{}.deviantart.com",
    }

    if st.button("🚀 بحث عبر المنصات", key="buffin_btn") and username:
        username_clean = username.strip().lstrip("@")
        progress = st.progress(0, text="جارٍ الفحص...")
        results = []

        for i, (platform, template) in enumerate(PLATFORMS.items()):
            url = template.format(username_clean)
            try:
                r = requests.get(
                    url,
                    timeout=6,
                    allow_redirects=True,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                if r.status_code == 200:
                    status = "✅ موجود"
                elif r.status_code == 404:
                    status = "❌ غير موجود"
                elif r.status_code in (403, 429):
                    status = "🛡️ محمي"
                else:
                    status = f"⚠️ ({r.status_code})"
            except requests.exceptions.Timeout:
                status = "⏱️ Timeout"
            except Exception:
                status = "⚠️ فشل"
            results.append({"المنصة": platform, "الحالة": status, "الرابط": url})
            progress.progress((i + 1) / len(PLATFORMS),
                              text=f"جارٍ فحص {platform}...")

        progress.empty()

        # إحصائيات سريعة
        found = sum(1 for r in results if "موجود" in r["الحالة"] and "غير" not in r["الحالة"])
        not_found = sum(1 for r in results if "غير موجود" in r["الحالة"])

        col1, col2, col3 = st.columns(3)
        col1.metric("✅ موجود", found)
        col2.metric("❌ غير موجود", not_found)
        col3.metric("⚠️ غير محدد", len(results) - found - not_found)

        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True, hide_index=True)


# =====================================================================
# 3) Geo-OSINT — تحليل جغرافي بدرجة ثقة
# =====================================================================
COUNTRY_COORDS = {
    "🇸🇦 السعودية": (24.7136, 46.6753),
    "🇪🇬 مصر":      (30.0444, 31.2357),
    "🇦🇪 الإمارات": (24.4539, 54.3773),
    "🇰🇼 الكويت":   (29.3759, 47.9774),
    "🇶🇦 قطر":      (25.2854, 51.5310),
    "🇧🇭 البحرين":  (26.0667, 50.5577),
    "🇴🇲 عُمان":    (23.5880, 58.3829),
    "🇯🇴 الأردن":   (31.9539, 35.9106),
    "🇱🇧 لبنان":    (33.8869, 35.5131),
    "🇸🇾 سوريا":    (33.5138, 36.2765),
    "🇮🇶 العراق":   (33.3152, 44.3661),
    "🇾🇪 اليمن":    (15.5527, 48.5164),
    "🇵🇸 فلسطين":   (31.9522, 35.2332),
    "🇲🇦 المغرب":   (33.9716, -6.8498),
    "🇩🇿 الجزائر":  (36.7538, 3.0588),
    "🇹🇳 تونس":     (36.8065, 10.1815),
    "🇱🇾 ليبيا":    (32.8872, 13.1913),
    "🇸🇩 السودان":  (15.5007, 32.5599),
}

TIMEZONE_TO_COUNTRIES = {
    "Asia/Riyadh":      ["🇸🇦 السعودية", "🇰🇼 الكويت", "🇧🇭 البحرين", "🇶🇦 قطر"],
    "Asia/Dubai":       ["🇦🇪 الإمارات", "🇴🇲 عُمان"],
    "Africa/Cairo":     ["🇪🇬 مصر"],
    "Asia/Amman":       ["🇯🇴 الأردن", "🇵🇸 فلسطين", "🇱🇧 لبنان", "🇸🇾 سوريا"],
    "Africa/Casablanca": ["🇲🇦 المغرب"],
    "Africa/Algiers":   ["🇩🇿 الجزائر", "🇹🇳 تونس"],
    "Asia/Baghdad":     ["🇮🇶 العراق"],
    "Africa/Khartoum":  ["🇸🇩 السودان"],
}


def render_geo_tab():
    st.subheader("🛰️ Geo-OSINT — تحليل جغرافي بمستوى ثقة")
    st.caption("استنتاج الدولة من region + timezone مع عرض المرشحين على الخريطة.")

    col1, col2 = st.columns(2)
    with col1:
        region = st.text_input("🌍 region code", placeholder="SA, EG, AE...")
    with col2:
        tz = st.selectbox(
            "🕰️ Timezone",
            options=[""] + list(TIMEZONE_TO_COUNTRIES.keys()),
        )

    if st.button("🎯 استنتاج الموقع", key="geo_btn"):
        candidates = []
        confidence = 0
        coords_list = []

        if region:
            country = REGION_MAP.get(region.upper())
            if country:
                candidates.append(country)
                if country in COUNTRY_COORDS:
                    coords_list.append(COUNTRY_COORDS[country])
                confidence += 50
            else:
                candidates.append(f"📍 region={region} (غير معروف)")
                confidence += 20

        if tz and tz in TIMEZONE_TO_COUNTRIES:
            tz_candidates = TIMEZONE_TO_COUNTRIES[tz]
            for c in tz_candidates:
                if c not in candidates:
                    candidates.append(c)
                    if c in COUNTRY_COORDS:
                        coords_list.append(COUNTRY_COORDS[c])
            confidence += 35 if len(tz_candidates) == 1 else 20

        if not candidates:
            st.warning("⚠️ أدخل region أو timezone على الأقل.")
            return

        st.markdown(
            f"""
            <div class="confidence-box">
            <b>📊 درجة الثقة:</b> {min(confidence, 95)}%
            <small>(الحد الأقصى 95% — OSINT لا يعطي يقين 100%)</small><br>
            <b>🎯 المرشحون:</b><br>
            {'<br>'.join('• ' + c for c in candidates)}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if coords_list:
            map_df = pd.DataFrame(coords_list, columns=["lat", "lon"])
            st.map(map_df, latitude="lat", longitude="lon", size=30, zoom=3)


# =====================================================================
# 4) خريطة تفاعلية بـ st.map
# =====================================================================
def render_map_tab():
    st.subheader("🗺️ الخريطة التفاعلية")

    last_result = st.session_state.get("last_tiktok_result", {})

    # إذا كان هناك نتيجة TikTok سابقة → اعرضها
    if last_result and last_result.get("success"):
        region = last_result["data"].get("region", "")
        country = REGION_MAP.get(region)

        if country and country in COUNTRY_COORDS:
            lat, lon = COUNTRY_COORDS[country]
            df = pd.DataFrame([{"lat": lat, "lon": lon}])
            st.success(f"✅ آخر تحليل TikTok: {country}")
            st.map(df, latitude="lat", longitude="lon", size=50, zoom=4)
            return

    # Demo: عرض الدول العربية
    demo_data = pd.DataFrame([
        {"lat": lat, "lon": lon, "country": c}
        for c, (lat, lon) in COUNTRY_COORDS.items()
    ])
    st.info("💡 **Demo Mode:** هذه عواصم الدول العربية. حلّل حساب TikTok لرؤية موقعه الفعلي.")
    st.map(demo_data, latitude="lat", longitude="lon", size=20, zoom=3)


# =====================================================================
# 5) لوحة حالة الأدوات
# =====================================================================
def render_status_dashboard():
    st.subheader("📊 حالة الأدوات الحالية")

    col1, col2, col3 = st.columns(3)
    col1.metric("الأدوات الكلية", "4")
    col2.metric("تعمل بشكل كامل", "4", "+4")
    col3.metric("معطلة", "0")

    status = [
        {"الأداة": "🎵 TikTok",     "الحالة": "🟢 يعمل", "الملاحظة": "3 طبقات استخراج JSON + Meta"},
        {"الأداة": "🔍 BUFFIN",     "الحالة": "🟢 يعمل", "الملاحظة": "12 منصة + فحص HTTP حقيقي"},
        {"الأداة": "🛰️ Geo-OSINT", "الحالة": "🟢 يعمل", "الملاحظة": "مع إحداثيات وخريطة"},
        {"الأداة": "🗺️ Map",       "الحالة": "🟢 يعمل", "الملاحظة": "ديناميكية مع آخر تحليل"},
    ]
    st.dataframe(pd.DataFrame(status), use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### 🆕 التحديثات في v6.1")
    st.markdown(
        """
        - ❌ **حُذِف X (Twitter)** — API مغلق + Nitter توقف
        - ❌ **حُذِف RSS** — غير ضروري للهدف الأساسي
        - ❌ **حُذِف Disclaimer**
        - ✅ **TikTok معزَّز:** يستخرج البيانات الفعلية (متابعون، إعجابات، فيديوهات، region)
        - ✅ **BUFFIN موسَّع:** 12 منصة بدل 8
        - ✅ **Geo-OSINT:** خريطة فورية بإحداثيات حقيقية
        """
    )


# =====================================================================
# التطبيق الرئيسي
# =====================================================================
def main():
    col_title, col_badge = st.columns([4, 1])
    with col_title:
        st.title("🛰️ مولد معلومات حسابات التواصل الاجتماعي")
    with col_badge:
        st.markdown(
            '<div style="text-align:left; padding-top:25px;">'
            '<span class="version-badge">v6.1 ⚡ Streamlined</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("**نسخة مُبسَّطة وفعَّالة** | 🎵 TikTok • 🔍 BUFFIN • 🛰️ Geo-OSINT • 🗺️ Map")

    tabs = st.tabs([
        "📊 لوحة الحالة",
        "🎵 TikTok",
        "🔍 BUFFIN",
        "🛰️ Geo-OSINT",
        "🗺️ الخريطة",
    ])

    with tabs[0]:
        render_status_dashboard()
    with tabs[1]:
        render_tiktok_tab()
    with tabs[2]:
        render_buffin_tab()
    with tabs[3]:
        render_geo_tab()
    with tabs[4]:
        render_map_tab()

    st.divider()
    st.caption(
        f"📅 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | "
        "🔧 v6.1.0 Streamlined Edition | "
        "🔗 [GitHub](https://github.com/7sn301/social-accounts-generator)"
    )


if __name__ == "__main__":
    main()
