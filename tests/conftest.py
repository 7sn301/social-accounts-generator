"""
Baseer Test Configuration — محسّن
معرّف: BSR-V217L-TEST-CONFTEST-FIX-AHMAD-20260613
"""
import sys
import os
from unittest.mock import MagicMock

# إنشاء streamlit mock شامل
streamlit_mock = MagicMock()

# st.tabs يجب أن يُرجع قائمة بنفس عدد العناصر المطلوبة
def _mock_tabs(labels):
    return [MagicMock() for _ in labels]
streamlit_mock.tabs = _mock_tabs

# st.columns يُرجع قائمة بنفس عدد المتغيّرات
def _mock_columns(spec):
    if isinstance(spec, int):
        n = spec
    elif isinstance(spec, (list, tuple)):
        n = len(spec)
    else:
        n = 2
    return [MagicMock() for _ in range(n)]
streamlit_mock.columns = _mock_columns

# st.cache_data + st.cache_resource decorators
def _passthrough_decorator(*args, **kwargs):
    # يدعم @st.cache_data و @st.cache_data(ttl=...)
    if len(args) == 1 and callable(args[0]):
        return args[0]
    def wrapper(fn):
        return fn
    return wrapper
streamlit_mock.cache_data = _passthrough_decorator
streamlit_mock.cache_resource = _passthrough_decorator

# st.set_page_config / st.markdown / st.expander
streamlit_mock.set_page_config = MagicMock()
streamlit_mock.markdown = MagicMock()
streamlit_mock.expander = MagicMock()

# session_state يجب أن يكون dict-like
class _SessionState(dict):
    def __getattr__(self, key):
        return self.get(key)
    def __setattr__(self, key, value):
        self[key] = value
streamlit_mock.session_state = _SessionState()

sys.modules['streamlit'] = streamlit_mock
sys.modules['streamlit.runtime'] = MagicMock()
sys.modules['streamlit.runtime.scriptrunner_utils'] = MagicMock()
sys.modules['streamlit_folium'] = MagicMock()

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


@pytest.fixture
def sample_regions_seq():
    """تسلسل دول لاختبار خوارزميّة الإقامة"""
    return ['SA', 'SA', 'SA', 'US', 'SA']


@pytest.fixture
def sample_timestamps():
    """timestamps لساعات النشر (UTC)"""
    return [
        1735689600, 1735776000, 1735862400, 1735948800, 1736035200,
    ]


@pytest.fixture
def sample_region_distribution():
    """توزيع مناطق نموذجي"""
    return {'SA': 5, 'US': 1}


@pytest.fixture
def sample_tikwm_response():
    """استجابة TikWM نموذجيّة"""
    return {
        'code': 0,
        'data': {
            'videos': [
                {'region': 'SA', 'create_time': 1735689600},
                {'region': 'SA', 'create_time': 1735776000},
                {'region': 'SA', 'create_time': 1735862400},
                {'region': 'US', 'create_time': 1735948800},
                {'region': 'SA', 'create_time': 1736035200},
            ]
        }
    }
