# ═══════════════════════════════════════════════════════════
# BSR-V218-ADMIN-AUTH-AHMAD-20260613
# نظام مصادقة آمن للوحة الإدارة (bcrypt + session tokens)
# ═══════════════════════════════════════════════════════════
"""Admin Authentication - تشفير عالٍ مع bcrypt + session management"""
import sqlite3
import hashlib
import secrets
import os
from datetime import datetime, timedelta
from pathlib import Path

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

DB_PATH = os.getenv("ANALYTICS_DB_PATH", "./data/analytics.db")
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30
SESSION_DURATION_MINUTES = 60


def hash_password(password):
    """تشفير كلمة المرور بـ bcrypt (12 rounds)"""
    if BCRYPT_AVAILABLE:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    salt = os.getenv("ADMIN_PASSWORD_SALT", secrets.token_hex(32))
    return hashlib.pbkdf2_hmac('sha256', password.encode(),
                                salt.encode(), 100000).hex()


def verify_password(password, hashed):
    """التحقّق من كلمة المرور"""
    if BCRYPT_AVAILABLE:
        try:
            return bcrypt.checkpw(password.encode('utf-8'),
                                   hashed.encode('utf-8'))
        except Exception:
            return False
    salt = os.getenv("ADMIN_PASSWORD_SALT", "")
    expected = hashlib.pbkdf2_hmac('sha256', password.encode(),
                                    salt.encode(), 100000).hex()
    return secrets.compare_digest(expected, hashed)


def is_ip_locked(ip_address):
    """فحص قفل IP بعد محاولات فاشلة"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    cutoff = (datetime.utcnow() - timedelta(minutes=LOCKOUT_DURATION_MINUTES)).isoformat()
    c.execute('''
        SELECT COUNT(*) FROM login_attempts
        WHERE ip_address = ? AND success = 0 AND timestamp > ?
    ''', (ip_address, cutoff))
    failed_count = c.fetchone()[0]
    conn.close()
    return failed_count >= MAX_LOGIN_ATTEMPTS


def record_login_attempt(ip_address, username, success):
    """تسجيل محاولة تسجيل دخول"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO login_attempts (ip_address, username, success, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (ip_address, username, 1 if success else 0,
          datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def create_session(ip_address):
    """إنشاء session token آمن"""
    token = secrets.token_urlsafe(32)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.utcnow()
    expires = now + timedelta(minutes=SESSION_DURATION_MINUTES)
    c.execute('''
        INSERT INTO admin_sessions (session_token, ip_address,
                                    created_at, expires_at, active)
        VALUES (?, ?, ?, ?, 1)
    ''', (token, ip_address, now.isoformat(), expires.isoformat()))
    conn.commit()
    conn.close()
    return token


def verify_session(token, ip_address=None):
    """التحقّق من صلاحية session"""
    if not token:
        return False
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT ip_address, expires_at, active FROM admin_sessions
        WHERE session_token = ?
    ''', (token,))
    row = c.fetchone()
    conn.close()
    if not row:
        return False
    stored_ip, expires_at, active = row
    if not active:
        return False
    if datetime.utcnow() > datetime.fromisoformat(expires_at):
        return False
    if ip_address and stored_ip != ip_address:
        return False  # IP changed - reject
    return True


def revoke_session(token):
    """إنهاء session"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE admin_sessions SET active = 0 WHERE session_token = ?',
              (token,))
    conn.commit()
    conn.close()


def authenticate(username, password, ip_address):
    """مصادقة المشرف"""
    if is_ip_locked(ip_address):
        return {'success': False,
                'error': f'IP محظور لـ {LOCKOUT_DURATION_MINUTES} دقيقة'}
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password_hash = os.getenv("ADMIN_PASSWORD_HASH", "")
    if not admin_password_hash:
        # تشفير ADMIN_PASSWORD لأوّل مرّة
        plain = os.getenv("ADMIN_PASSWORD", "")
        if plain:
            admin_password_hash = hash_password(plain)
    if username != admin_username:
        record_login_attempt(ip_address, username, False)
        return {'success': False, 'error': 'بيانات خاطئة'}
    if not verify_password(password, admin_password_hash):
        record_login_attempt(ip_address, username, False)
        return {'success': False, 'error': 'بيانات خاطئة'}
    record_login_attempt(ip_address, username, True)
    token = create_session(ip_address)
    return {'success': True, 'token': token}
