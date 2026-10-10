import time
from typing import Optional, Union, Tuple
from .storage import MemoryStorage, SQLiteStorage


class RateLimitExceeded(Exception):
    """Belgilangan so'rovlar chegarasi oshib ketganda chaqiriluvchi istisno."""

    def __init__(self, key: str, retry_after: float):
        self.key = key
        self.retry_after = retry_after
        super().__init__(f"So'rovlar limiti oshdi '{key}'. Qayta urinish: {retry_after:.2f} soniyadan keyin")


class TokenBucketLimiter:
    """
    Token Bucket algoritmi:
    - capacity: Paqirning maksimal sig'imi (ruxsat etilgan burst so'rovlar).
    - refill_rate: Har soniyada qo'shiladigan tokenlar soni.
    """

    def __init__(
        self,
        capacity: int = 10,
        refill_rate: float = 1.0,
        storage: Optional[Union[MemoryStorage, SQLiteStorage]] = None,
    ):
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self.storage = storage or MemoryStorage()

    def allow_request(self, key: str, cost: float = 1.0) -> Tuple[bool, dict]:
        now = time.time()

        if isinstance(self.storage, SQLiteStorage):
            state = self.storage.get_token_bucket(key)
            if state is None:
                tokens = self.capacity
                last_updated = now
            else:
                tokens, last_updated = state
        else:
            state = self.storage.get(key)
            if state is None:
                tokens = self.capacity
                last_updated = now
            else:
                tokens = state["tokens"]
                last_updated = state["last_updated"]

        # Tokenlarni to'ldirish
        elapsed = max(0.0, now - last_updated)
        tokens = min(self.capacity, tokens + elapsed * self.refill_rate)

        if tokens >= cost:
            tokens -= cost
            allowed = True
            retry_after = 0.0
        else:
            allowed = False
            needed = cost - tokens
            retry_after = needed / self.refill_rate if self.refill_rate > 0 else float("inf")

        # Holatni saqlash
        if isinstance(self.storage, SQLiteStorage):
            self.storage.set_token_bucket(key, tokens, now)
        else:
            self.storage.set(key, {"tokens": tokens, "last_updated": now})

        return allowed, {
            "allowed": allowed,
            "remaining": max(0.0, tokens),
            "capacity": self.capacity,
            "retry_after": retry_after,
        }

    def reset(self, key: str):
        self.storage.delete(key)


class SlidingWindowLimiter:
    """
    Sliding Window Counter algoritmi:
    - max_requests: Belgilangan vaqt oralig'ida ruxsat berilgan maksimal so'rovlar soni.
    - window_seconds: Oyna davomiyligi (soniyalarda).
    """

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        storage: Optional[Union[MemoryStorage, SQLiteStorage]] = None,
    ):
        self.max_requests = max_requests
        self.window_seconds = float(window_seconds)
        self.storage = storage or MemoryStorage()

    def allow_request(self, key: str) -> Tuple[bool, dict]:
        now = time.time()

        if isinstance(self.storage, SQLiteStorage):
            state = self.storage.get_sliding_window(key)
            if state is None:
                count = 0
                window_start = now
            else:
                count, window_start = state
        else:
            state = self.storage.get(f"sw:{key}")
            if state is None:
                count = 0
                window_start = now
            else:
                count = state["count"]
                window_start = state["window_start"]

        elapsed = now - window_start
        if elapsed >= self.window_seconds:
            # Yangi oyna
            count = 1
            window_start = now
            allowed = True
            retry_after = 0.0
        else:
            if count < self.max_requests:
                count += 1
                allowed = True
                retry_after = 0.0
            else:
                allowed = False
                retry_after = max(0.0, self.window_seconds - elapsed)

        # Holatni yangilash
        if isinstance(self.storage, SQLiteStorage):
            self.storage.set_sliding_window(key, count, window_start)
        else:
            self.storage.set(f"sw:{key}", {"count": count, "window_start": window_start})

        return allowed, {
            "allowed": allowed,
            "current_count": count,
            "max_requests": self.max_requests,
            "retry_after": retry_after,
        }

    def reset(self, key: str):
        if isinstance(self.storage, SQLiteStorage):
            self.storage.delete(key)
        else:
            self.storage.delete(f"sw:{key}")
