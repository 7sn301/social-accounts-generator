# ═══════════════════════════════════════════════════════════
# BSR-V218-ADMIN-PAGE-AHMAD-20260613
# صفحة /admin المحميّة — لوحة تحليلات بصير الخاصة
# ═══════════════════════════════════════════════════════════
"""Admin Dashboard - baseer1.streamlit.app/admin"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from admin_auth import authenticate, verify_session, revoke_session
from analytics_db import get_all_users, get_user_searches, get_stats

# ─────────────────────────────────────────────────────────────
# إعدادات الصفحة
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🔐 لوحة بصير الإدارية",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────
# CSS — RTL + Noto Sans Arabic
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;700;900&family=Tajawal:wght@400;700;900&display=swap');
* { font-family: 'Noto Sans Arabic', 'Tajawal', sans-serif !important; }
html, body, [class*="css"] { direction: rtl; text-align: right; }
#MainMenu, footer, header, [data-testid="stSidebar"] { visibility: hidden !important; }
.stApp > header { display: none; }
section[data-testid="stSidebar"] { display: none !important; }
.login-box {
    max-width: 420px; margin: 80px auto;
    background: linear-gradient(135deg, #0F172A, #1E3A8A);
    padding: 40px 35px; border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.4);
    border: 2px solid #F59E0B;
    direction: rtl; text-align: right;
}
.login-title {
    font-size: 28pt; font-weight: 900;
    background: linear-gradient(135deg, #F59E0B, #FCD34D);
    -webkit-background-clip: text; color: transparent;
    text-align: center; margin-bottom: 20px;
}
.kpi-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 14px; margin: 20px 0;
}
.kpi-box {
    background: linear-gradient(135deg, #0F172A, #1E293B);
    border-right: 5px solid #F59E0B; padding: 16px;
    border-radius: 12px; text-align: center; color: #F1F5F9;
}
.kpi-num { font-size: 28pt; font-weight: 900; color: #F59E0B; }
.kpi-label { font-size: 11pt; color: #94A3B8; }
.warning-box {
    background: #FEE2E2; border-right: 4px solid #DC2626;
    padding: 14px; border-radius: 8px; color: #7F1D1D;
    direction: rtl; text-align: right;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────────────────────
if 'admin_token' not in st.session_state:
    st.session_state.admin_token = None

# ─────────────────────────────────────────────────────────────
# فحص الـ session
# ─────────────────────────────────────────────────────────────
is_authenticated = (
    st.session_state.admin_token
    and verify_session(st.session_state.admin_token)
)

# ─────────────────────────────────────────────────────────────
# واجهة تسجيل الدخول
# ─────────────────────────────────────────────────────────────
if not is_authenticated:
    st.markdown('<div class="login-box" dir="rtl">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">🔐 لوحة بصير الإدارية</div>',
                unsafe_allow_html=True)
    st.markdown('<p dir="rtl" style="color:#CBD5E1; text-align:center;">'
                'الدخول مقيّد للمشرف فقط</p>', unsafe_allow_html=True)
    with st.form("admin_login", clear_on_submit=False):
        username = st.text_input("👤 اسم المستخدم", key="admin_user")
        password = st.text_input("🔒 كلمة المرور",
                                  type="password", key="admin_pass")
        submit = st.form_submit_button("🚪 تسجيل دخول",
                                        use_container_width=True,
                                        type="primary")
        if submit:
            if not username or not password:
                st.error("⚠️ أدخل اسم المستخدم وكلمة المرور")
            else:
                # IP placeholder (Streamlit Cloud لا يكشف IP حقيقي)
                ip = st.context.headers.get('x-forwarded-for', 'unknown') \
                    if hasattr(st, 'context') else 'unknown'
                result = authenticate(username, password, ip)
                if result.get('success'):
                    st.session_state.admin_token = result['token']
                    st.success("✅ تمّ تسجيل الدخول بنجاح")
                    st.rerun()
                else:
                    st.error(f"❌ {result.get('error', 'فشل المصادقة')}")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div dir="rtl" style="text-align:center; '
                'color:#94A3B8; margin-top:20px;">'
                '🛡️ محميّ بـ bcrypt + session tokens<br>'
                '🚨 الحدّ الأقصى: 5 محاولات فاشلة لكلّ IP'
                '</div>', unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────
# لوحة التحليلات (بعد المصادقة الناجحة)
# ─────────────────────────────────────────────────────────────
col_a, col_b = st.columns([5, 1])
with col_a:
    st.markdown('<h1 dir="rtl" style="color:#F59E0B; font-weight:900;">'
                '📊 لوحة تحليلات بصير</h1>', unsafe_allow_html=True)
with col_b:
    if st.button("🚪 خروج", type="secondary"):
        revoke_session(st.session_state.admin_token)
        st.session_state.admin_token = None
        st.rerun()

# 📊 إحصائيات عامة
stats = get_stats()
st.markdown('<h2 dir="rtl" style="color:#0F172A;">📈 إحصائيات عامة</h2>',
            unsafe_allow_html=True)
st.markdown(f'''
<div class="kpi-grid">
    <div class="kpi-box">
        <div class="kpi-num">{stats['total_users']}</div>
        <div class="kpi-label">إجمالي المستخدمين</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-num">{stats['total_searches']}</div>
        <div class="kpi-label">إجمالي البحثات</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-num">{len(stats['top_countries'])}</div>
        <div class="kpi-label">عدد الدول</div>
    </div>
</div>
''', unsafe_allow_html=True)

# 👥 جدول المستخدمين
st.markdown('<h2 dir="rtl" style="color:#0F172A;">'
            '👥 المستخدمون الذين ضغطوا /start</h2>',
            unsafe_allow_html=True)
users = get_all_users(limit=100)
if not users:
    st.markdown('<div class="warning-box" dir="rtl">'
                '⚠️ لا توجد بيانات بعد — انتظر موافقة المستخدمين عبر /start'
                '</div>', unsafe_allow_html=True)
else:
    try:
        import pandas as pd
        df_rows = []
        for u in users:
            df_rows.append({
                '🆔 Telegram ID': u['telegram_id'],
                '👤 Username': f"@{u['username']}" if u['username'] else '—',
                '🪪 الاسم': f"{u['first_name'] or ''} {u['last_name'] or ''}".strip() or '—',
                '🌐 IP': u['ip_address'] or '—',
                '🌍 الدولة': u['country'] or '—',
                '🏙️ المدينة': u['city'] or '—',
                '🌐 ISP': u['isp'] or '—',
                '🔍 عدد البحثات': u['total_searches'],
                '🕒 آخر ظهور': u['last_seen'][:19] if u['last_seen'] else '—',
            })
        df = pd.DataFrame(df_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    except ImportError:
        for u in users:
            st.markdown(f'''
            <div dir="rtl" style="background:#F1F5F9;
                 padding:12px; border-radius:8px; margin:8px 0;
                 border-right:4px solid #F59E0B;">
                <strong>🆔 {u['telegram_id']}</strong> —
                @{u['username']} —
                🌍 {u['country'] or '—'} ({u['city'] or '—'}) —
                🔍 {u['total_searches']} بحث
            </div>
            ''', unsafe_allow_html=True)

# 🔍 جدول البحثات حسب مستخدم
st.markdown('<h2 dir="rtl" style="color:#0F172A;">'
            '🔍 عرض بحثات مستخدم معيّن</h2>', unsafe_allow_html=True)
if users:
    user_ids = [u['telegram_id'] for u in users]
    selected_id = st.selectbox("اختر Telegram ID:", user_ids)
    if selected_id:
        searches = get_user_searches(selected_id, limit=50)
        if searches:
            try:
                import pandas as pd
                df_s = pd.DataFrame([{
                    '🔍 الاستعلام': s['query'],
                    '🌍 الدولة المُكتشفة': s['country'] or '—',
                    '👤 الحساب الناتج': s['username'] or '—',
                    '🕒 الوقت': s['timestamp'][:19] if s['timestamp'] else '—',
                } for s in searches])
                st.dataframe(df_s, use_container_width=True, hide_index=True)
            except ImportError:
                for s in searches:
                    st.markdown(f"• `{s['query']}` — {s['timestamp']}")
        else:
            st.info("لا بحثات لهذا المستخدم بعد")

# 🌍 أعلى الدول
if stats['top_countries']:
    st.markdown('<h2 dir="rtl" style="color:#0F172A;">'
                '🌍 أعلى الدول</h2>', unsafe_allow_html=True)
    for country, count in stats['top_countries'].items():
        st.markdown(f'<div dir="rtl" style="background:#F1F5F9;'
                    f' padding:8px 14px; border-radius:8px; margin:4px 0;'
                    f' border-right:4px solid #10B981;">'
                    f'🌍 <strong>{country}</strong>: {count} مستخدم'
                    f'</div>', unsafe_allow_html=True)
