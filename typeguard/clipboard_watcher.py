"""
TypeGuard Clipboard Watcher — Monitors clipboard for text changes.
Captures copied text as a bonus safety net.
"""
import threading
import time
import pyperclip
from typeguard.word_buffer import WordBuffer
from typeguard.config import CLIPBOARD_POLL_INTERVAL


class ClipboardWatcher:
    """
    Polls the system clipboard at regular intervals.
    When new text is detected, it splits the text into words and
    adds them to the shared WordBuffer with source='clipboard'.
    """

    def __init__(self, word_buffer: WordBuffer):
        self._buffer = word_buffer
        self._last_content = ""
        self._running = False
        self._thread: threading.Thread | None = None
        # Initialize with current clipboard content so we don't
        # re-capture whatever is already there.
        try:
            self._last_content = pyperclip.paste() or ""
        except Exception:
            self._last_content = ""

    def start(self) -> None:
        """Start the clipboard polling thread."""
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the polling thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)

    def _poll_loop(self) -> None:
        """Main polling loop — checks clipboard every interval."""
        while self._running:
            try:
                current = pyperclip.paste() or ""
                if current and current != self._last_content:
                    self._last_content = current
                    # Don't record if paused
                    if not self._buffer.paused:
                        words = current.split()
                        if words:
                            self._buffer.add_words(words, source="clipboard")
            except Exception:
                # Clipboard access can occasionally fail (e.g., locked by
                # another process). Silently continue.
                pass
            time.sleep(CLIPBOARD_POLL_INTERVAL)
