"""
analytics_db.py - Baseer v2.1.8
SQLite Analytics Database with safe path handling
"""
import os
import sqlite3
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

# ✅ مسار آمن: نسبي افتراضياً، يُستخدم متغيّر البيئة إن وُجد
DEFAULT_DB = Path(__file__).parent / "data" / "analytics.db"
DB_PATH = Path(os.getenv("ANALYTICS_DB_PATH", str(DEFAULT_DB)))

# ✅ إنشاء المجلد بأمان مع معالجة كل الحالات
try:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
except FileExistsError:
    # المجلد موجود (أو هناك ملف بنفس الاسم) — نتجاهل بأمان
    if not DB_PATH.parent.is_dir():
        # إذا كان ملفاً وليس مجلداً، نعيد التوجيه لـ /tmp
        DB_PATH = Path("/tmp") / "analytics.db"
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
except PermissionError:
    # Streamlit Cloud read-only filesystem
    DB_PATH = Path("/tmp") / "analytics.db"
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
