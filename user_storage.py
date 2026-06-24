# ═══════════════════════════════════════════════════════════
# BSR-V217L-USER-STORAGE-RAW-PII-AHMAD-20260613
# تخزين user_id الخام مع consent (كسر القيد #21)
# ═══════════════════════════════════════════════════════════
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

import config

DATA_DIR = Path("./data")
USERS_FILE = DATA_DIR / "users.json"
CONSENT_LOG = Path(config.CONSENT_LOG_FILE)


def _ensure_files():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.exists():
        USERS_FILE.write_text(json.dumps({"users": {}}, ensure_ascii=False, indent=2))
    if not CONSENT_LOG.exists():
        CONSENT_LOG.parent.mkdir(parents=True, exist_ok=True)
        CONSENT_LOG.touch()


def _load() -> Dict[str, Any]:
    _ensure_files()
    return json.loads(USERS_FILE.read_text(encoding="utf-8"))


def _save(data: Dict[str, Any]):
    USERS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def record_consent(user_id: int, username: Optional[str], language_code: Optional[str]) -> bool:
    _ensure_files()
    data = _load()
    uid = str(user_id)
    now = datetime.now(timezone.utc).isoformat()

    data["users"][uid] = {
        "user_id": user_id,
        "username": username or "—",
        "language_code": language_code or "—",
        "consent_given": True,
        "consent_version": config.CONSENT_VERSION,
        "consent_timestamp": now,
        "first_seen": now,
        "last_seen": now,
        "total_queries": 0,
        "country": "—"
    }
    _save(data)

    with open(CONSENT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "user_id": user_id,
            "action": "CONSENT_GIVEN",
            "version": config.CONSENT_VERSION,
            "timestamp": now
        }, ensure_ascii=False) + "\n")
    return True


def has_consented(user_id: int) -> bool:
    data = _load()
    user = data["users"].get(str(user_id))
    return bool(user and user.get("consent_given"))


def update_activity(user_id: int, country: str = "—") -> None:
    if not has_consented(user_id):
        return
    data = _load()
    uid = str(user_id)
    user = data["users"][uid]
    user["last_seen"] = datetime.now(timezone.utc).isoformat()
    user["total_queries"] = user.get("total_queries", 0) + 1
    if country != "—":
        user["country"] = country
    _save(data)


def forget_user(user_id: int) -> bool:
    data = _load()
    uid = str(user_id)
    if uid not in data["users"]:
        return False
    del data["users"][uid]
    _save(data)
    with open(CONSENT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "user_id": user_id,
            "action": "DATA_ERASED",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, ensure_ascii=False) + "\n")
    return True


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    data = _load()
    return data["users"].get(str(user_id))


def all_users() -> Dict[str, Any]:
    return _load()["users"]
