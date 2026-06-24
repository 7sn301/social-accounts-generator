# ═══════════════════════════════════════════════════════════
# BSR-V217L-TEST-PII-CONSENT-AHMAD-20260613
# 12 اختبار لكسر القيد #21
# ═══════════════════════════════════════════════════════════
import pytest
from pathlib import Path
import user_storage
import config


@pytest.fixture(autouse=True)
def tmp_data(monkeypatch, tmp_path):
    users_file = tmp_path / "users.json"
    consent_log = tmp_path / "consent.jsonl"
    monkeypatch.setattr(user_storage, "DATA_DIR", tmp_path)
    monkeypatch.setattr(user_storage, "USERS_FILE", users_file)
    monkeypatch.setattr(user_storage, "CONSENT_LOG", consent_log)
    yield


def test_consent_recorded():
    assert user_storage.record_consent(123, "ahmad", "ar-SA")
    assert user_storage.has_consented(123)


def test_no_consent_means_no_storage():
    assert not user_storage.has_consented(999)


def test_raw_user_id_stored():
    user_storage.record_consent(456, "test", "ar")
    u = user_storage.get_user(456)
    assert u["user_id"] == 456  # خام، ليس مُجزَّأ


def test_forget_me_deletes_all():
    user_storage.record_consent(789, "x", "en")
    assert user_storage.forget_user(789)
    assert not user_storage.has_consented(789)


def test_update_activity_increments():
    user_storage.record_consent(111, "y", "ar-EG")
    user_storage.update_activity(111, "EG")
    user_storage.update_activity(111, "EG")
    u = user_storage.get_user(111)
    assert u["total_queries"] == 2
    assert u["country"] == "EG"


def test_consent_version_recorded():
    user_storage.record_consent(222, "z", "ar")
    assert user_storage.get_user(222)["consent_version"] == config.CONSENT_VERSION


def test_consent_log_appended():
    user_storage.record_consent(333, "a", "ar")
    log = Path(user_storage.CONSENT_LOG).read_text()
    assert "CONSENT_GIVEN" in log


def test_forget_logged():
    user_storage.record_consent(444, "b", "ar")
    user_storage.forget_user(444)
    log = Path(user_storage.CONSENT_LOG).read_text()
    assert "DATA_ERASED" in log


def test_activity_without_consent_ignored():
    user_storage.update_activity(555, "SA")
    assert user_storage.get_user(555) is None


def test_all_users_returns_dict():
    user_storage.record_consent(666, "c", "ar")
    assert isinstance(user_storage.all_users(), dict)


def test_pii_flag_enabled():
    assert config.STORE_RAW_USER_ID is True


def test_retention_days_set():
    assert config.DATA_RETENTION_DAYS == 365
