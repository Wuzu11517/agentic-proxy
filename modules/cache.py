import sqlite3
import hashlib
import json
import os
from datetime import datetime, timedelta
import config

DB_PATH = "cache/cache.db"


def _get_connection():
    os.makedirs("cache", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_cache():
    conn = _get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            response TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_accessed TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def _make_key(body: dict) -> str:
    normalized = json.dumps(body, sort_keys=True)
    return hashlib.sha256(normalized.encode()).hexdigest()


def _is_expired(created_at: str) -> bool:
    created = datetime.fromisoformat(created_at)
    return datetime.utcnow() > created + timedelta(hours=config.CACHE_TTL_HOURS)


def _evict_if_needed(conn: sqlite3.Connection):
    count = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
    if count >= config.CACHE_MAX_ENTRIES:
        # Evict least recently accessed entries to get under limit
        excess = count - config.CACHE_MAX_ENTRIES + 1
        conn.execute("""
            DELETE FROM cache WHERE key IN (
                SELECT key FROM cache ORDER BY last_accessed ASC LIMIT ?
            )
        """, (excess,))
        conn.commit()


def check_cache(body: dict) -> dict | None:
    key = _make_key(body)
    conn = _get_connection()

    row = conn.execute(
        "SELECT * FROM cache WHERE key = ?", (key,)
    ).fetchone()

    if row is None:
        conn.close()
        return None

    if _is_expired(row["created_at"]):
        conn.execute("DELETE FROM cache WHERE key = ?", (key,))
        conn.commit()
        conn.close()
        return None

    # Update last accessed for LRU tracking
    conn.execute(
        "UPDATE cache SET last_accessed = ? WHERE key = ?",
        (datetime.utcnow().isoformat(), key)
    )
    conn.commit()
    conn.close()

    return json.loads(row["response"])


def store_cache(body: dict, response: dict):
    key = _make_key(body)
    now = datetime.utcnow().isoformat()
    conn = _get_connection()

    _evict_if_needed(conn)

    conn.execute("""
        INSERT OR REPLACE INTO cache (key, response, created_at, last_accessed)
        VALUES (?, ?, ?, ?)
    """, (key, json.dumps(response), now, now))
    conn.commit()
    conn.close()


def get_cache_size() -> dict:
    conn = _get_connection()
    count = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
    conn.close()
    return {"entries": count, "max_entries": config.CACHE_MAX_ENTRIES}


def clear_all():
    conn = _get_connection()
    conn.execute("DELETE FROM cache")
    conn.commit()
    conn.close()


init_cache()