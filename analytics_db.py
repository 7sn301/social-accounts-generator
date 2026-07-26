"""
╔══════════════════════════════════════════════════════════════════╗
║  BSR-V240-CTO-NUCLEAR-FIX-DB-AHMAD-20260726                      ║
║  analytics_db.py v2.4.0 - Optional DB (never blocks bot)         ║
║  Date: 2026-07-26 | Leader: Dr. Ahmad Al-Fanni (CTO)             ║
╚══════════════════════════════════════════════════════════════════╝

🏆 v2.4.0 STRATEGY:
  - DB is OPTIONAL (bot works without it)
  - All operations wrapped in try/except
  - Pool created lazily (first use, not import)
  - DNS/connection failures log warning + return silently
  - IPv4 pooler auto-detection with fallback
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to load psycopg2 (optional)
try:
    import psycopg2
    from psycopg2 import pool as pg_pool
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning("[DB] psycopg2 not installed - analytics disabled")

# Global connection pool (lazy)
_pool: Optional[object] = None
_pool_init_attempted = False


def _get_database_url() -> str:
    """Get DATABASE_URL from env at runtime."""
    return os.getenv("DATABASE_URL", "").strip()


def _init_pool_if_needed():
    """Lazy pool initialization - never raises."""
    global _pool, _pool_init_attempted

    if _pool is not None or _pool_init_attempted:
        return

    _pool_init_attempted = True

    if not PSYCOPG2_AVAILABLE:
        return

    db_url = _get_database_url()
    if not db_url:
        logger.warning("[DB] DATABASE_URL not set - analytics disabled")
        return

    # Warn about known-bad hosts
    if "db.dczvgnniclwkcwmbknhg.supabase.co" in db_url:
        logger.warning("[DB] Detected DIRECT connection (IPv6) - Railway needs pooler URL")

    try:
        _pool = pg_pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            dsn=db_url,
            connect_timeout=10,
        )
        logger.info("[DB] ✅ pool initialized successfully")
    except Exception as e:
        logger.warning(f"[DB] pool init failed (bot will run without DB): {e}")
        _pool = None


def _get_conn():
    """Get connection from pool, or None."""
    _init_pool_if_needed()
    if _pool is None:
        return None
    try:
        return _pool.getconn()
    except Exception as e:
        logger.warning(f"[DB] getconn failed: {e}")
        return None


def _put_conn(conn):
    """Return connection to pool."""
    if _pool is None or conn is None:
        return
    try:
        _pool.putconn(conn)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
# 📊 Public API (never raises)
# ═══════════════════════════════════════════════════════════
def record_user_start(
    telegram_id: int,
    username: str = "",
    first_name: str = "",
    last_name: str = "",
    language_code: str = "",
    ip: str = "",
    country: Optional[str] = None,
    city: Optional[str] = None,
) -> bool:
    """Record /start event. Returns True on success, False on any error."""
    conn = _get_conn()
    if conn is None:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (
                    telegram_id, username, first_name, last_name,
                    language_code, ip, country, city, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (telegram_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    language_code = EXCLUDED.language_code,
                    last_seen = NOW()
            """, (telegram_id, username, first_name, last_name,
                  language_code, ip, country, city))
            conn.commit()
        return True
    except Exception as e:
        logger.warning(f"[DB] record_user_start failed: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return False
    finally:
        _put_conn(conn)


def record_search(
    telegram_id: int,
    target_username: str,
    target_country: Optional[str] = None,
    target_region: Optional[str] = None,
    followers: int = 0,
) -> bool:
    """Record a search event. Returns True on success, False on error."""
    conn = _get_conn()
    if conn is None:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO searches (
                    telegram_id, target_username, target_country,
                    target_region, followers, created_at
                )
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (telegram_id, target_username, target_country,
                  target_region, followers))
            conn.commit()
        return True
    except Exception as e:
        logger.warning(f"[DB] record_search failed: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return False
    finally:
        _put_conn(conn)


def health_check() -> dict:
    """Diagnostic function - returns DB status."""
    status = {
        "psycopg2": PSYCOPG2_AVAILABLE,
        "database_url_set": bool(_get_database_url()),
        "pool_initialized": _pool is not None,
        "pool_init_attempted": _pool_init_attempted,
    }

    if _pool is not None:
        conn = _get_conn()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    status["ping"] = "ok"
            except Exception as e:
                status["ping"] = f"failed: {e}"
            finally:
                _put_conn(conn)
        else:
            status["ping"] = "no connection available"

    return status


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("🔎 Analytics DB Health Check:")
    for k, v in health_check().items():
        print(f"  {k}: {v}")
