import time
from collections import deque
from typing import Callable

from app.core.config import settings


class RateLimiter:
    """Sliding-window request counter, keyed by whatever the caller passes.

    In memory, like `ConnectionManager`: it holds for one process and resets on
    restart. That is enough to stop a brute-force loop and to keep Argon2 from
    being used as a CPU exhaustion lever; a distributed attack needs shared
    state, which is the same Redis milestone.
    """

    def __init__(
        self,
        attempts: int,
        window_seconds: float,
        now: Callable[[], float] = time.monotonic,
    ):
        self._attempts = attempts
        self._window = window_seconds
        # Injectable so tests can drive the window without sleeping.
        self._now = now
        self._hits: dict[str, deque[float]] = {}
        self._last_sweep = now()

    def retry_after(self, key: str) -> float | None:
        """Seconds to wait before this key may try again, or None if it may now.

        An allowed call is recorded, so this both asks and counts.
        """
        now = self._now()
        self._sweep(now)

        hits = self._hits.setdefault(key, deque())
        cutoff = now - self._window
        while hits and hits[0] <= cutoff:
            hits.popleft()

        if len(hits) >= self._attempts:
            return self._window - (now - hits[0])

        hits.append(now)
        return None

    def reset(self) -> None:
        self._hits.clear()

    def _sweep(self, now: float) -> None:
        """Drop keys that have gone quiet.

        Without this the dict grows one entry per distinct key forever, which
        would make a rate limiter into its own memory exhaustion vector for an
        attacker rotating addresses.
        """
        if now - self._last_sweep < self._window:
            return

        self._last_sweep = now
        cutoff = now - self._window
        self._hits = {
            key: hits for key, hits in self._hits.items() if hits and hits[-1] > cutoff
        }


login_limiter = RateLimiter(
    attempts=settings.login_max_attempts,
    window_seconds=settings.login_window_seconds,
)
