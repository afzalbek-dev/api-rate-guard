import argparse
import sys
from .limiter import TokenBucketLimiter, SlidingWindowLimiter
from .storage import SQLiteStorage


def main():
    parser = argparse.ArgumentParser(description="API Rate Guard - Rate Limiting boshqaruv utilitasi")
    parser.add_argument("--db", default="/tmp/rate_guard.db", help="SQLite ma'lumotlar bazasi fayli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="Mijoz uchun so'rovga ruxsat borligini tekshirish")
    check_parser.add_argument("key", help="Mijoz identifikatori yoki IP manzil")
    check_parser.add_argument("--capacity", type=int, default=5, help="Maksimal token sig'imi")
    check_parser.add_argument("--refill", type=float, default=1.0, help="Soniyadagi refill tezligi")

    reset_parser = subparsers.add_parser("reset", help="Mijoz hisoblagichini tozalash")
    reset_parser.add_argument("key", help="Mijoz identifikatori")

    args = parser.parse_args()
    storage = SQLiteStorage(args.db)

    if args.command == "check":
        limiter = TokenBucketLimiter(capacity=args.capacity, refill_rate=args.refill, storage=storage)
        allowed, meta = limiter.allow_request(args.key)
        if allowed:
            print(f"RUXSAT BERILDI: {args.key} | Qolgan tokenlar: {meta['remaining']:.2f}")
            sys.exit(0)
        else:
            print(f"RAD ETILDI: {args.key} | Qayta urinish vaqti: {meta['retry_after']:.2f}s")
            sys.exit(1)
    elif args.command == "reset":
        limiter = TokenBucketLimiter(storage=storage)
        limiter.reset(args.key)
        print(f"TOZALANDI: {args.key} cheklovlari nolga tenglashtirildi.")
        sys.exit(0)


if __name__ == "__main__":
    main()
