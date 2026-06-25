# ─────────────────────────────────────
# Backward compatibility aliases
# ─────────────────────────────────────
def revoke_session(token: str):
    """Alias for logout() - keeps backward compatibility"""
    return logout(token)


def revoke_all_sessions(username: str = None):
    """إلغاء جميع الجلسات"""
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
    """قائمة الجلسات النشطة"""
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
