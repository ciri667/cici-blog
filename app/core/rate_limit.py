import time
from collections import defaultdict


class RateLimiter:
    """简单的内存限流器。按键（IP）追踪失败尝试次数。"""

    def __init__(self, max_attempts: int = 5, window_seconds: int = 900):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: dict[str, list[float]] = defaultdict(list)

    def is_locked(self, key: str) -> bool:
        self._cleanup(key)
        return len(self._attempts[key]) >= self.max_attempts

    def record_failure(self, key: str) -> None:
        self._cleanup(key)
        self._attempts[key].append(time.time())

    def reset(self, key: str) -> None:
        self._attempts.pop(key, None)

    def _cleanup(self, key: str) -> None:
        now = time.time()
        cutoff = now - self.window_seconds
        self._attempts[key] = [t for t in self._attempts[key] if t > cutoff]


login_rate_limiter = RateLimiter(max_attempts=5, window_seconds=900)
