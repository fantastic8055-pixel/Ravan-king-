from __future__ import annotations

import time
from collections import defaultdict, deque


class RateLimiter:
    """Small in-memory per-user limiter; reset on process restart."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._events: dict[int, deque[float]] = defaultdict(deque)

    def allow(self, user_id: int) -> bool:
        now = time.monotonic()
        events = self._events[user_id]
        cutoff = now - self.window_seconds
        while events and events[0] <= cutoff:
            events.popleft()
        if len(events) >= self.max_requests:
            return False
        events.append(now)
        return True
