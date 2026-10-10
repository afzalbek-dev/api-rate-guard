import time
import pytest
from rate_guard.storage import MemoryStorage, SQLiteStorage
from rate_guard.limiter import TokenBucketLimiter, SlidingWindowLimiter


def test_token_bucket_memory():
    limiter = TokenBucketLimiter(capacity=3, refill_rate=1.0)
    
    # 3 ta ketma-ket so'rov ruxsat berilishi kerak
    assert limiter.allow_request("user1")[0] is True
    assert limiter.allow_request("user1")[0] is True
    assert limiter.allow_request("user1")[0] is True
    
    # 4-so'rov rad etilishi kerak
    allowed, meta = limiter.allow_request("user1")
    assert allowed is False
    assert meta["retry_after"] > 0


def test_token_bucket_sqlite(tmp_path):
    db_file = str(tmp_path / "rate_test.db")
    storage = SQLiteStorage(db_file)
    limiter = TokenBucketLimiter(capacity=2, refill_rate=2.0, storage=storage)
    
    assert limiter.allow_request("client_a")[0] is True
    assert limiter.allow_request("client_a")[0] is True
    assert limiter.allow_request("client_a")[0] is False
    
    limiter.reset("client_a")
    assert limiter.allow_request("client_a")[0] is True
    storage.close()


def test_sliding_window_counter():
    limiter = SlidingWindowLimiter(max_requests=2, window_seconds=1)
    
    assert limiter.allow_request("ip_1")[0] is True
    assert limiter.allow_request("ip_1")[0] is True
    assert limiter.allow_request("ip_1")[0] is False
    
    time.sleep(1.1)
    assert limiter.allow_request("ip_1")[0] is True
