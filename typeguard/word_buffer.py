"""
TypeGuard Word Buffer — FIFO rolling buffer of typed words.
Uses collections.deque for O(1) append and automatic overflow eviction.
"""
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional

from typeguard.config import MAX_WORDS


@dataclass
class WordEntry:
    """A single recorded word with metadata."""
    word: str
    timestamp: float = field(default_factory=time.time)
    source: str = "keyboard"          # "keyboard" | "clipboard"

    def to_dict(self) -> dict:
        return {
            "word": self.word,
            "timestamp": self.timestamp,
            "source": self.source,
        }


class WordBuffer:
    """
    Thread-safe FIFO word buffer.
    Automatically evicts the oldest entries when MAX_WORDS is exceeded.
    """

    def __init__(self, max_words: int = MAX_WORDS):
        self._buffer: deque[WordEntry] = deque(maxlen=max_words)
        self._lock = threading.Lock()
        self._paused = False
        # Track words added since last DB flush
        self._pending_words: List[WordEntry] = []
        self._pending_lock = threading.Lock()

    # ── Public API ────────────────────────────────────────────

    def add_word(self, word: str, source: str = "keyboard") -> None:
        """Add a single word to the buffer."""
        if self._paused:
            return
        word = word.strip()
        if not word:
            return
        entry = WordEntry(word=word, source=source)
        with self._lock:
            self._buffer.append(entry)
        with self._pending_lock:
            self._pending_words.append(entry)

    def add_words(self, words: List[str], source: str = "keyboard") -> None:
        """Add multiple words at once (e.g., from clipboard paste)."""
        for w in words:
            self.add_word(w, source)

    def get_all(self) -> List[WordEntry]:
        """Return a snapshot of all words in the buffer."""
        with self._lock:
            return list(self._buffer)

    def get_last_n(self, n: int) -> List[WordEntry]:
        """Return the last N words."""
        with self._lock:
            items = list(self._buffer)
        return items[-n:] if n < len(items) else items

    def get_text(self, last_n: Optional[int] = None) -> str:
        """Join words into a readable string."""
        entries = self.get_last_n(last_n) if last_n else self.get_all()
        return " ".join(e.word for e in entries)

    def get_count(self) -> int:
        with self._lock:
            return len(self._buffer)

    def clear(self) -> None:
        """Manually clear the entire buffer."""
        with self._lock:
            self._buffer.clear()
        with self._pending_lock:
            self._pending_words.clear()

    def load_initial(self, entries: List[WordEntry]) -> None:
        """Load words from DB on startup (oldest → newest order)."""
        with self._lock:
            for entry in entries:
                self._buffer.append(entry)

    # ── Pending words (for DB flush) ──────────────────────────

    def drain_pending(self) -> List[WordEntry]:
        """Return and clear the list of words not yet flushed to DB."""
        with self._pending_lock:
            words = self._pending_words[:]
            self._pending_words.clear()
        return words

    # ── Pause / Resume ────────────────────────────────────────

    @property
    def paused(self) -> bool:
        return self._paused

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def toggle_pause(self) -> bool:
        """Toggle and return the new paused state."""
        self._paused = not self._paused
        return self._paused
