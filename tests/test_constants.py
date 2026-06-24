"""
اختبارات الثوابت — Baseer (AST-based)
معرّف: BSR-V217L-TEST-CONSTANTS-V2-AHMAD-20260613
"""
import pytest
from tests._extract_constants import CONSTANTS


class TestConstants:
    """اختبار الثوابت الجوهريّة عبر AST"""

    def test_tikwm_base_url(self):
        assert CONSTANTS['TIKWM_BASE'] == "https://www.tikwm.com"

    def test_proxy_chain_count(self):
        assert len(CONSTANTS['PROXY_CHAIN']) == 4

    def test_proxy_chain_names(self):
        names = [p['name'] for p in CONSTANTS['PROXY_CHAIN']]
        assert 'jina' in names
        assert 'allorigins' in names
        assert 'corsproxy' in names
        assert 'codetabs' in names

    def test_user_agents_count(self):
        assert len(CONSTANTS['USER_AGENTS']) >= 20

    def test_country_ar_basic(self):
        """COUNTRY_AR يستخدم أسماء إنجليزية كاملة كمفاتيح (وليس ISO-2)"""
        ar = CONSTANTS['COUNTRY_AR']
        assert 'Saudi Arabia' in ar
        assert 'Egypt' in ar
        assert 'United Arab Emirates' in ar
        assert 'Kuwait' in ar
        assert 'Qatar' in ar


    def test_country_ar_count(self):
        assert len(CONSTANTS['COUNTRY_AR']) >= 180

    def test_country_ar_arabic_names(self):
        for iso, name in list(CONSTANTS['COUNTRY_AR'].items())[:5]:
            assert any('\u0600' <= ch <= '\u06FF' for ch in name), f"{iso} ليس بالعربية"


class TestPrivacyConstraints:
    """اختبار قيود الخصوصيّة (#18, #20, #21)"""

    def test_no_ip_in_proxy_chain(self):
        import re
        for proxy in CONSTANTS['PROXY_CHAIN']:
            assert not re.search(r'\d+\.\d+\.\d+\.\d+', proxy['url']), \
                f"IP صريح في {proxy['url']}"

    def test_no_geocoding_libraries_in_imports(self):
        with open('/home/user/baseer_v217l/app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        forbidden = ['import geopy', 'import geocoder', 'from geopy', 'from opencage']
        for f_imp in forbidden:
            assert f_imp not in code, f"استيراد محظور: {f_imp}"

    def test_no_tikapi_apify_imports(self):
        with open('/home/user/baseer_v217l/app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        assert 'tikapi' not in code.lower(), "tikapi مستخدَم"
        assert 'apify' not in code.lower(), "apify مستخدَم"


class TestProxyChainOrder:
    """اختبار ترتيب PROXY_CHAIN"""

    def test_proxy_first_is_jina(self):
        assert CONSTANTS['PROXY_CHAIN'][0]['name'] == 'jina'

    def test_proxy_timeouts_reasonable(self):
        for proxy in CONSTANTS['PROXY_CHAIN']:
            assert 10 <= proxy['timeout'] <= 30, \
                f"timeout غير معقول: {proxy['name']}={proxy['timeout']}"
