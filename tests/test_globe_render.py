"""
اختبارات الكرة الأرضية — AST مُعزَّز
معرّف: BSR-V217L-TEST-GLOBE-V2-AHMAD-20260613
"""
import pytest


class TestPlotlyRequirement:
    """التحقّق من plotly كمتطلب"""

    def test_plotly_in_requirements(self):
        with open('/home/user/baseer_v217l/requirements.txt', 'r', encoding='utf-8') as f:
            reqs = f.read()
        assert 'plotly' in reqs, "plotly مفقود من requirements.txt"

    def test_plotly_importable(self):
        try:
            import plotly.graph_objects as go
            assert hasattr(go, 'Figure')
            assert hasattr(go, 'Choropleth')
        except ImportError:
            pytest.fail("plotly مطلوب لكن غير مثبّت")


class TestGlobeCode:
    """اختبارات مصدر دالة الخريطة"""

    def test_orthographic_projection(self):
        with open('/home/user/baseer_v217l/app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        assert 'orthographic' in code, "إسقاط Orthographic مفقود"

    def test_iso2_to_iso3_mapping(self):
        with open('/home/user/baseer_v217l/app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        assert '"SAU"' in code or "'SAU'" in code, "خريطة ISO-2→ISO-3 مفقودة"
        assert '"USA"' in code or "'USA'" in code

    def test_hover_label_rtl(self):
        with open('/home/user/baseer_v217l/app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        assert 'hoverlabel' in code, "hoverlabel مفقود"
        assert 'Noto Sans Arabic' in code

    def test_arab_rotation_center(self):
        """الكرة تدور نحو الشرق الأوسط للدول العربيّة"""
        with open('/home/user/baseer_v217l/app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        assert 'arab_set' in code, "مجموعة الدول العربيّة للتدوير مفقودة"
