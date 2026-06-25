"""
admin_auth.py - Baseer v2.1.8.5
Secure Admin Authentication with bcrypt + session tokens
Complete export of: authenticate, verify_session, logout, revoke_session
"""
import os
import sqlite3
import secrets
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from contextlib import contextmanager

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False


# Configuration
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "baseer_admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Bs2026EagleVisionSecure")
ADMIN_PASSWORD_SALT = os.getenv("ADMIN_PASSWORD_SALT", "default_salt_change_me")
SESSION_SECRET = os.getenv("SESSION_SECRET", secrets.token_hex(32))

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 30
SESSION_HOURS = 8

# Safe DB path
DEFAULT_AUTH_DB = Path(__file__).parent / "data" / "auth.db"
DB_PATH = Path(os.getenv("AUTH_DB_PATH", str(DEFAULT_AUTH_DB)))

try:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
except (FileExistsError, PermissionError, OSError):
    DB_PATH = Path("/tmp/auth.db")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_auth_db():
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT NOT NULL,
                username TEXT,
                success INTEGER DEFAULT 0,
                timestamp TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                ip_address TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_ip ON login_attempts(ip_address, timestamp)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_token ON sessions(token)")


try:
    init_auth_db()
except Exception as e:
    print(f"Auth DB init warning: {e}")


def hash_password(password: str) -> str:
    if BCRYPT_AVAILABLE:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
    salted = (password + ADMIN_PASSWORD_SALT).encode()
    return hashlib.sha256(salted).hexdigest()


def verify_password(password: str, stored: str) -> bool:
    try:
        if BCRYPT_AVAILABLE and stored.startswith("$2"):
            return bcrypt.checkpw(password.encode(), stored.encode())
        if password == stored:
            return True
        salted = (password + ADMIN_PASSWORD_SALT).encode()
        return hashlib.sha256(salted).hexdigest() == stored
    except Exception:
        return False


def is_ip_locked(ip_address: str) -> bool:
    try:
        with get_db() as conn:
            c = conn.cursor()
            cutoff = (datetime.utcnow() - timedelta(minutes=LOCKOUT_MINUTES)).isoformat()
            c.execute("""
                SELECT COUNT(*) as fails FROM login_attempts
                WHERE ip_address = ? AND success = 0 AND timestamp > ?
            """, (ip_address, cutoff))
            row = c.fetchone()
            return row and row["fails"] >= MAX_FAILED_ATTEMPTS
    except Exception:
        return False


def log_attempt(ip_address: str, username: str, success: bool):
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO login_attempts (ip_address, username, success, timestamp)
                VALUES (?, ?, ?, ?)
            """, (ip_address, username, 1 if success else 0, datetime.utcnow().isoformat()))
    except Exception as e:
        print(f"log_attempt error: {e}")


def create_session(username: str, ip_address: str) -> str:
    token = secrets.token_urlsafe(32)
    expires = (datetime.utcnow() + timedelta(hours=SESSION_HOURS)).isoformat()
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO sessions (token, username, ip_address, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (token, username, ip_address, datetime.utcnow().isoformat(), expires))
    except Exception as e:
        print(f"create_session error: {e}")
    return token


def verify_session(token: str) -> bool:
    """Verify session token validity"""
    if not token:
        return False
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT expires_at FROM sessions WHERE token = ?", (token,))
            row = c.fetchone()
            if not row:
                return False
            return datetime.fromisoformat(row["expires_at"]) > datetime.utcnow()
    except Exception:
        return False


def authenticate(username: str, password: str, ip_address: str = "0.0.0.0") -> dict:
    """Full authentication: returns dict with success, message, token"""
    if is_ip_locked(ip_address):
        return {
            "success": False,
            "message": f"تم قفل IP لمدة {LOCKOUT_MINUTES} دقيقة بسبب محاولات فاشلة متكررة",
            "token": None
        }

    if username != ADMIN_USERNAME:
        log_attempt(ip_address, username, False)
        return {
            "success": False,
            "message": "اسم المستخدم أو كلمة المرور غير صحيحة",
            "token": None
        }

    if not verify_password(password, ADMIN_PASSWORD):
        log_attempt(ip_address, username, False)
        return {
            "success": False,
            "message": "اسم المستخدم أو كلمة المرور غير صحيحة",
            "token": None
        }

    log_attempt(ip_address, username, True)
    token = create_session(username, ip_address)
    return {
        "success": True,
        "message": "تم تسجيل الدخول بنجاح",
        "token": token
    }


def logout(token: str):
    """Logout: delete session"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM sessions WHERE token = ?", (token,))
    except Exception:
        pass


# Backward compatibility aliases
def revoke_session(token: str):
    """Alias for logout()"""
    return logout(token)


def revoke_all_sessions(username: str = None):
    try:
        with get_db() as conn:
            c = conn.cursor()
            if username:
                c.execute("DELETE FROM sessions WHERE username = ?", (username,))
            else:
                c.execute("DELETE FROM sessions")
    except Exception:
        pass


def get_active_sessions():
    try:
        with get_db() as conn:
            c = conn.cursor()
            now = datetime.utcnow().isoformat()
            c.execute("""
                SELECT * FROM sessions WHERE expires_at > ?
                ORDER BY created_at DESC
            """, (now,))
            return [dict(row) for row in c.fetchall()]
    except Exception:
        return []


# Explicit exports
__all__ = [
    'authenticate',
    'verify_session',
    'logout',
    'revoke_session',
    'revoke_all_sessions',
    'get_active_sessions',
    'is_ip_locked',
    'hash_password',
    'verify_password',
    'log_attempt',
    'create_session',
]
