"""
اختبارات خوارزميّة الإقامة — AST مُعزَّز
معرّف: BSR-V217L-TEST-RESIDENCE-V2-AHMAD-20260613
"""
import pytest


class TestRegionDistribution:
    """اختبار حساب توزيع المناطق"""

    def test_distribution_count(self, sample_region_distribution):
        assert sample_region_distribution['SA'] == 5
        assert sample_region_distribution['US'] == 1

    def test_distribution_total(self, sample_region_distribution):
        assert sum(sample_region_distribution.values()) == 6

    def test_distribution_top_country(self, sample_region_distribution):
        top = max(sample_region_distribution.items(), key=lambda x: x[1])
        assert top[0] == 'SA'

    def test_distribution_percentage(self, sample_region_distribution):
        total = sum(sample_region_distribution.values())
        sa_pct = round(sample_region_distribution['SA'] / total * 100, 1)
        assert sa_pct > 80


class TestSourceCodeIntegrity:
    """اختبارات على مستوى مصدر الكود"""

    def test_detect_residence_function_exists(self):
        with open('/home/user/baseer_v217l/app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        assert 'def detect_actual_residence' in code, "دالة detect_actual_residence مفقودة"

    def test_infer_timezone_function_exists(self):
        with open('/home/user/baseer_v217l/app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        assert 'def _infer_timezone_from_hours' in code, "دالة _infer_timezone_from_hours مفقودة"

    def test_fetch_user_region_exists(self):
        with open('/home/user/baseer_v217l/app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        assert 'def fetch_user_region_tikwm' in code, "دالة fetch_user_region_tikwm مفقودة"

    def test_globe_function_exists(self):
        with open('/home/user/baseer_v217l/app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        assert 'def render_country_globe_3d' in code, "دالة render_country_globe_3d مفقودة"
