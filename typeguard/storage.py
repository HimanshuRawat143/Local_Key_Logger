"""
TypeGuard SQLite Storage — Persistent word storage that survives reboots.
Uses WAL mode for concurrent read/write performance.
"""
import os
import sqlite3
import threading
import time
from typing import List

from typeguard.config import DB_PATH, MAX_WORDS, APP_DATA_DIR
from typeguard.word_buffer import WordEntry


class Storage:
    """
    SQLite-backed persistence layer.
    - On startup: loads existing words from DB into the WordBuffer.
    - Periodically: flushes pending in-memory words to the DB.
    - Enforces the FIFO word limit in the database.
    """

    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    # ── Initialization ────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS words (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        word TEXT NOT NULL,
                        timestamp REAL NOT NULL,
                        source TEXT NOT NULL DEFAULT 'keyboard'
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_words_timestamp
                    ON words(timestamp)
                """)
                conn.commit()
            finally:
                conn.close()

    # ── Load on startup ───────────────────────────────────────

    def load_words(self) -> List[WordEntry]:
        """Load the most recent MAX_WORDS entries from the DB."""
        with self._lock:
            conn = self._get_conn()
            try:
                cursor = conn.execute(
                    "SELECT word, timestamp, source FROM words "
                    "ORDER BY id DESC LIMIT ?",
                    (MAX_WORDS,)
                )
                rows = cursor.fetchall()
                # Reverse so oldest is first (deque append order)
                rows.reverse()
                return [
                    WordEntry(word=r[0], timestamp=r[1], source=r[2])
                    for r in rows
                ]
            finally:
                conn.close()

    # ── Flush pending words ───────────────────────────────────

    def flush(self, entries: List[WordEntry]) -> None:
        """Write a batch of new words to the DB and enforce the word limit."""
        if not entries:
            return
        with self._lock:
            conn = self._get_conn()
            try:
                conn.executemany(
                    "INSERT INTO words (word, timestamp, source) VALUES (?, ?, ?)",
                    [(e.word, e.timestamp, e.source) for e in entries]
                )
                # Enforce FIFO: keep only the newest MAX_WORDS rows
                conn.execute("""
                    DELETE FROM words
                    WHERE id NOT IN (
                        SELECT id FROM words ORDER BY id DESC LIMIT ?
                    )
                """, (MAX_WORDS,))
                conn.commit()
            finally:
                conn.close()

    # ── Clear everything ──────────────────────────────────────

    def clear_all(self) -> None:
        """Delete all words from the database."""
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("DELETE FROM words")
                conn.commit()
            finally:
                conn.close()

    # ── Stats ─────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Return storage statistics."""
        with self._lock:
            conn = self._get_conn()
            try:
                row = conn.execute("SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM words").fetchone()
                db_size = os.path.getsize(self._db_path) if os.path.exists(self._db_path) else 0
                return {
                    "word_count": row[0] or 0,
                    "oldest_timestamp": row[1],
                    "newest_timestamp": row[2],
                    "db_size_bytes": db_size,
                    "db_size_mb": round(db_size / (1024 * 1024), 2),
                }
            finally:
                conn.close()
