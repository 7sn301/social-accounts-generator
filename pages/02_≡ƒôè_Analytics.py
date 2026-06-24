# ═══════════════════════════════════════════════════════════
# BSR-V217L-ANALYTICS-DASHBOARD-RTL-AHMAD-20260613
# لوحة تحكّم Streamlit — RTL + Noto Sans Arabic
# ═══════════════════════════════════════════════════════════
import streamlit as st
import plotly.express as px
from datetime import datetime
import analytics

st.set_page_config(page_title="📊 تحليلات بصير", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;700&family=Tajawal:wght@400;700&display=swap');
* { font-family: 'Noto Sans Arabic', 'Tajawal', sans-serif !important; }
.main, .block-container { direction: rtl; }
.stMetric { background: #F1F5F9; padding: 16px; border-radius: 12px; }
h1, h2, h3 { color: #0F172A; }
</style>
<div dir="rtl"><h1 style="color:#0F172A;">📊 لوحة تحليلات بصير</h1></div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
col1.metric("👥 إجمالي المستخدمين الموافقين", analytics.total_consented_users())
col2.metric("📅 الشهر الحالي", datetime.now().strftime("%Y-%m"))
col3.metric("🛡️ القيد #21", "مكسور بموافقة")

view = st.radio("الفترة", ["شهري", "ربعي", "سنوي"], horizontal=True)
now = datetime.now()

if view == "شهري":
    data = analytics.monthly_country_distribution(now.year, now.month)
elif view == "ربعي":
    q = (now.month - 1) // 3 + 1
    data = analytics.quarterly_summary(now.year, q)
else:
    data = analytics.yearly_summary(now.year)

if data:
    fig = px.bar(
        x=list(data.keys()), y=list(data.values()),
        labels={"x": "الدولة", "y": "عدد المستخدمين"},
        color_discrete_sequence=["#F59E0B"]
    )
    fig.update_layout(font_family="Noto Sans Arabic", title="توزيع المستخدمين حسب الدولة")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("لا توجد بيانات بعد — انتظر موافقة المستخدمين عبر /start.")
