# API Rate Guard

Yuqori unumdor Token Bucket va Sliding Window algoritmlariga asoslangan Python rate limiter moduli va boshqaruv CLI vositasi.

## Xususiyatlari
- **Token Bucket Limiter**: Burst so'rovlarni va barqaror oqimni xotirada yoki SQLite'da boshqarish.
- **Sliding Window Counter**: Belgilangan vaqt oralig'ida aniq kvotalarni nazorat qilish.
- **SQLite & In-Memory saqlash**: Doimiy fayl yoki tezkor RAM asosidagi holat saqlovchi omborlar.
- **CLI Boshqaruvi**: Mijozlar limitini terminaldan tekshirish va tozalash.

## O'rnatish
```bash
pip install -e .
```

## Foydalanish (Python)
```python
from rate_guard import TokenBucketLimiter, SQLiteStorage

storage = SQLiteStorage("limits.db")
limiter = TokenBucketLimiter(capacity=10, refill_rate=2.0, storage=storage)

allowed, meta = limiter.allow_request("client_ip_192.168.1.1")
if allowed:
    print(f"Ruxsat berildi. Qolgan tokenlar: {meta['remaining']}")
else:
    print(f"Limit tugadi. Qayta urinish: {meta['retry_after']}s")
```

## CLI
```bash
python3 -m rate_guard.cli check user_123 --capacity 10 --refill 2
python3 -m rate_guard.cli reset user_123
```

## Testlar
```bash
pytest tests/ -v
```

## Litsenziya
MIT
