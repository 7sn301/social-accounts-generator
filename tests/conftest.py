# ═══════════════════════════════════════════════════════════
# BSR-V217L-CONFTEST-PII-AHMAD-20260613
# ═══════════════════════════════════════════════════════════
import sys
from pathlib import Path

# إضافة جذر المشروع إلى sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
