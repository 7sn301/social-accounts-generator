"""
╔══════════════════════════════════════════════════════════════════╗
║  BSR-V260-CTO-RATE-LIMITER-AHMAD-20260727                       ║
║  rate_limiter.py v2.6.0 - Token-bucket rate limiter             ║
║  Date: 2026-07-27 | Leader: Dr. Ahmad Al-Fanni (CTO)            ║
╚══════════════════════════════════════════════════════════════════╝

Protects RapidAPI from abuse by limiting per-user requests.

Default limits:
  - 10 requests per 60 seconds per user (Telegram user_id)
  - Cooldown message shown in Arabic when exceeded
  - Global admin bypass via ADMIN_USER_IDS
"""

import time
import threading
from typing import Dict, Optional, Tuple
from collections import deque


class RateLimiter:
    """Sliding-window rate limiter per user."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Args:
            max_requests: Max requests allowed per window
            window_seconds: Window size in seconds
        """
        self.max_requests = max_requests
        self.window = window_seconds
        self._user_requests: Dict[str, deque] = {}
        self._lock = threading.RLock()
        self._admin_ids: set = set()
        self._stats = {"allowed": 0, "blocked": 0, "total": 0}

    def add_admin(self, user_id: str) -> None:
        """Register a user_id to bypass rate limits."""
        with self._lock:
            self._admin_ids.add(str(user_id))

    def check(self, user_id: str) -> Tuple[bool, Optional[int]]:
        """
        Check if user can make a request.

        Returns:
            (allowed, seconds_until_reset)
        """
        user_id_str = str(user_id)

        with self._lock:
            self._stats["total"] += 1

            # Admin bypass
            if user_id_str in self._admin_ids:
                self._stats["allowed"] += 1
                return True, None

            now = time.time()
            window_start = now - self.window

            # Get or create user's request timestamps
            if user_id_str not in self._user_requests:
                self._user_requests[user_id_str] = deque()

            user_reqs = self._user_requests[user_id_str]

            # Remove expired timestamps (older than window)
            while user_reqs and user_reqs[0] < window_start:
                user_reqs.popleft()

            # Check limit
            if len(user_reqs) >= self.max_requests:
                # Blocked - compute seconds until oldest expires
                oldest = user_reqs[0]
                seconds_left = int(oldest + self.window - now) + 1
                self._stats["blocked"] += 1
                return False, seconds_left

            # Allowed - record this request
            user_reqs.append(now)
            self._stats["allowed"] += 1
            return True, None

    def get_remaining(self, user_id: str) -> int:
        """Get remaining requests for user in current window."""
        user_id_str = str(user_id)
        with self._lock:
            if user_id_str in self._admin_ids:
                return 999
            now = time.time()
            window_start = now - self.window
            if user_id_str not in self._user_requests:
                return self.max_requests
            user_reqs = self._user_requests[user_id_str]
            while user_reqs and user_reqs[0] < window_start:
                user_reqs.popleft()
            return max(0, self.max_requests - len(user_reqs))

    def reset_user(self, user_id: str) -> None:
        """Clear rate limit history for a user."""
        with self._lock:
            self._user_requests.pop(str(user_id), None)

    def cleanup(self) -> int:
        """Remove empty deques from users with no recent activity."""
        with self._lock:
            now = time.time()
            window_start = now - self.window
            to_delete = []
            for uid, reqs in self._user_requests.items():
                while reqs and reqs[0] < window_start:
                    reqs.popleft()
                if not reqs:
                    to_delete.append(uid)
            for uid in to_delete:
                del self._user_requests[uid]
            return len(to_delete)

    def stats(self) -> Dict[str, int]:
        """Return usage statistics."""
        with self._lock:
            total = self._stats["total"]
            block_rate = (self._stats["blocked"] / total * 100) if total > 0 else 0
            return {
                **self._stats,
                "active_users": len(self._user_requests),
                "admin_users": len(self._admin_ids),
                "max_requests_per_window": self.max_requests,
                "window_seconds": self.window,
                "block_rate_pct": round(block_rate, 2),
            }


# ═══════════════════════════════════════════════════════════════
# Global singleton
# ═══════════════════════════════════════════════════════════════
_RATE_LIMITER = RateLimiter(max_requests=10, window_seconds=60)


def check_rate_limit(user_id: str) -> Tuple[bool, Optional[int]]:
    """Check if user is within rate limit. Returns (allowed, retry_after_seconds)."""
    return _RATE_LIMITER.check(user_id)


def add_admin(user_id: str) -> None:
    """Register admin (unlimited access)."""
    _RATE_LIMITER.add_admin(user_id)


def get_remaining(user_id: str) -> int:
    """Get remaining requests for user."""
    return _RATE_LIMITER.get_remaining(user_id)


def rate_limit_stats() -> dict:
    """Return rate limiter stats."""
    return _RATE_LIMITER.stats()


def format_rate_limit_message(retry_after: int, remaining: int = 0) -> str:
    """Build an Arabic cooldown message (HTML for Telegram)."""
    minutes = retry_after // 60
    seconds = retry_after % 60

    if minutes > 0:
        time_str = f"{minutes} دقيقة و {seconds} ثانية"
    else:
        time_str = f"{seconds} ثانية"

    return (
        f"⏳ <b>تجاوزت حد الاستخدام</b>\n\n"
        f"لقد قمت بـ <b>10 عمليات بحث</b> خلال آخر دقيقة.\n"
        f"يرجى الانتظار <b>{time_str}</b> ثم المحاولة مرة أخرى.\n\n"
        f"💡 هذا الحد يحمي الخدمة من الإساءة."
    )


if __name__ == "__main__":
    # Self-test
    rl = RateLimiter(max_requests=3, window_seconds=1)
    assert rl.check("user1") == (True, None)
    assert rl.check("user1") == (True, None)
    assert rl.check("user1") == (True, None)
    allowed, _ = rl.check("user1")
    assert not allowed
    assert rl.check("user2") == (True, None)  # different user
    time.sleep(1.1)
    assert rl.check("user1") == (True, None)  # window expired
    print("✅ rate_limiter.py self-test passed")
    print(f"Stats: {rl.stats()}")
