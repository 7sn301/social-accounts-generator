"""
اختبارات سلامة البيانات والقيود الدائمة — Baseer
معرّف: BSR-V217L-TEST-DATA-INTEGRITY-AHMAD-20260613
"""
import pytest


class TestDataIntegrity:
    """اختبار سلامة البيانات الناتجة من lookup_user"""

    def test_no_ip_field_in_result(self):
        """نتيجة lookup_user يجب ألاّ تحتوي حقل IP (القيد #18)"""
        # نختبر شكل result dictionary المتوقّع
        expected_forbidden = ['ip', 'ip_address', 'client_ip', 'remote_ip']
        # ندخل بفحص الكود
        with open('/home/user/baseer_v217l/app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        for field in expected_forbidden:
            assert f"'{field}':" not in code, f"حقل IP محظور: {field}"

    def test_unknown_value_uses_dash(self):
        """القيم غير المعروفة يجب أن تستخدم '—' (القيد #9)"""
        with open('/home/user/baseer_v217l/app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        # نتحقّق من وجود '—' كقيمة افتراضيّة
        assert '—' in code, "رمز '—' للقيم المجهولة غير موجود"

    def test_rtl_in_all_html(self):
        """كل HTML markdown يجب أن يحتوي dir='rtl'"""
        with open('/home/user/baseer_v217l/app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        # عدد البطاقات
        card_count = code.count('<div class="tech-details-card"') + code.count('<div dir="rtl"')
        rtl_count = code.count('dir="rtl"')
        assert rtl_count >= card_count, "بعض البطاقات بدون dir='rtl'"

    def test_noto_sans_arabic_font(self):
        """الخطوط يجب أن تشمل Noto Sans Arabic"""
        with open('/home/user/baseer_v217l/app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        assert 'Noto Sans Arabic' in code, "خط Noto Sans Arabic غير موجود"

    def test_tajawal_font_backup(self):
        """Tajawal كخطّ احتياطي"""
        with open('/home/user/baseer_v217l/app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        assert 'Tajawal' in code, "خط Tajawal الاحتياطي غير موجود"


class TestUIConstraints:
    """اختبار قيود الواجهة (#1, #2, #3)"""

    def test_color_palette(self):
        """الألوان الإلزاميّة موجودة"""
        with open('/home/user/baseer_v217l/app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        assert '#0F172A' in code, "اللون الأساسي #0F172A مفقود"
        assert '#F59E0B' in code, "اللون المميّز #F59E0B مفقود"
        assert '#F1F5F9' in code, "لون النصّ #F1F5F9 مفقود"

    def test_excluded_versions_not_referenced(self):
        """الإصدارات المستبعدة لا تُذكَر (القيد #22)"""
        with open('/home/user/baseer_v217l/app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        excluded = ['v2.1.8', 'v2.1.9', 'v2.2.0', 'v2.3.0', 'v3.0']
        for ver in excluded:
            # نسمح بالذكر فقط في التعليقات (لتحذير)
            lines_with_ver = [l for l in code.split('\n') if ver in l]
            # فلترة الأسطر التي ليست تعليقات
            non_comment = [l for l in lines_with_ver if not l.strip().startswith('#') and 'استبعاد' not in l]
            assert len(non_comment) == 0, f"إصدار مستبعد مذكور: {ver}"


class TestProxyChainCount:
    """اختبار عدد الـ proxies والترتيب"""

    def test_proxy_first_is_jina(self):
        """jina هو الوسيط الأول (الأسرع) — عبر AST لا استيراد مباشر"""
        from tests._extract_constants import CONSTANTS
        assert CONSTANTS['PROXY_CHAIN'][0]['name'] == 'jina'

    def test_proxy_timeouts_reasonable(self):
        """timeouts بين 10-30 ثانية — عبر AST لا استيراد مباشر"""
        from tests._extract_constants import CONSTANTS
        for proxy in CONSTANTS['PROXY_CHAIN']:
            assert 10 <= proxy['timeout'] <= 30, \
                f"timeout غير معقول: {proxy['name']}={proxy['timeout']}"
