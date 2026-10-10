import sqlite3
import time
from typing import Optional, Tuple


class MemoryStorage:
    """Xotirada (in-memory) tezkor ma'lumotlarni saqlash ombori."""

    def __init__(self):
        self._data = {}

    def get(self, key: str) -> Optional[dict]:
        return self._data.get(key)

    def set(self, key: str, value: dict):
        self._data[key] = value

    def delete(self, key: str):
        if key in self._data:
            del self._data[key]

    def clear(self):
        self._data.clear()


class SQLiteStorage:
    """SQLite orqali doimiy (diskda) saqlanuvchi rate limiter ombori."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path)
        self._init_db()

    def _init_db(self):
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rate_limits (
                    key TEXT PRIMARY KEY,
                    tokens REAL,
                    last_updated REAL,
                    request_count INTEGER,
                    window_start REAL
                )
                """
            )

    def get_token_bucket(self, key: str) -> Optional[Tuple[float, float]]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT tokens, last_updated FROM rate_limits WHERE key = ?", (key,))
        row = cursor.fetchone()
        return (row[0], row[1]) if row else None

    def set_token_bucket(self, key: str, tokens: float, last_updated: float):
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO rate_limits (key, tokens, last_updated)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    tokens = excluded.tokens,
                    last_updated = excluded.last_updated
                """,
                (key, tokens, last_updated),
            )

    def get_sliding_window(self, key: str) -> Optional[Tuple[int, float]]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT request_count, window_start FROM rate_limits WHERE key = ?", (key,))
        row = cursor.fetchone()
        return (row[0], row[1]) if row else None

    def set_sliding_window(self, key: str, count: int, window_start: float):
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO rate_limits (key, request_count, window_start)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    request_count = excluded.request_count,
                    window_start = excluded.window_start
                """,
                (key, count, window_start),
            )

    def delete(self, key: str):
        with self._conn:
            self._conn.execute("DELETE FROM rate_limits WHERE key = ?", (key,))

    def close(self):
        self._conn.close()
