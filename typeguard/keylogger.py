"""
TypeGuard Keyboard Listener — Captures keystrokes and assembles them into words.
Uses pynput for low-level keyboard event capture.
"""
import threading
import re
from pynput import keyboard
from typeguard.word_buffer import WordBuffer


# Keys that signal the end of a word
WORD_BREAK_KEYS = {
    keyboard.Key.space,
    keyboard.Key.enter,
    keyboard.Key.tab,
}

# Keys to completely ignore (modifiers, function keys, etc.)
IGNORED_KEYS = {
    keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r,
    keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
    keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r,
    keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r,
    keyboard.Key.caps_lock, keyboard.Key.num_lock, keyboard.Key.scroll_lock,
    keyboard.Key.f1, keyboard.Key.f2, keyboard.Key.f3, keyboard.Key.f4,
    keyboard.Key.f5, keyboard.Key.f6, keyboard.Key.f7, keyboard.Key.f8,
    keyboard.Key.f9, keyboard.Key.f10, keyboard.Key.f11, keyboard.Key.f12,
    keyboard.Key.print_screen, keyboard.Key.pause, keyboard.Key.insert,
    keyboard.Key.menu,
    keyboard.Key.home, keyboard.Key.end,
    keyboard.Key.page_up, keyboard.Key.page_down,
    keyboard.Key.up, keyboard.Key.down, keyboard.Key.left, keyboard.Key.right,
}


class KeyboardListener:
    """
    Listens for keyboard events system-wide and feeds completed words
    to the shared WordBuffer.
    """

    def __init__(self, word_buffer: WordBuffer):
        self._buffer = word_buffer
        self._current_chars: list[str] = []
        self._lock = threading.Lock()
        self._listener: keyboard.Listener | None = None
        self._ctrl_held = False

    # ── Start / Stop ──────────────────────────────────────────

    def start(self) -> None:
        """Start listening for keyboard events (non-blocking)."""
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        """Stop the listener."""
        if self._listener:
            self._listener.stop()

    # ── Event handlers ────────────────────────────────────────

    def _on_press(self, key) -> None:
        # Track Ctrl state to ignore keyboard shortcuts
        if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self._ctrl_held = True
            return

        # Skip if paused
        if self._buffer.paused:
            return

        # Ignore modifier keys and function keys
        if key in IGNORED_KEYS:
            return

        # Ignore keyboard shortcuts (Ctrl+C, Ctrl+V, etc.)
        if self._ctrl_held:
            return

        # Word break keys → flush current word
        if key in WORD_BREAK_KEYS:
            self._flush_current_word()
            # Add newline marker for Enter key (preserves paragraph structure)
            if key == keyboard.Key.enter:
                self._buffer.add_word("\n", source="keyboard")
            return

        # Backspace → remove last character
        if key == keyboard.Key.backspace:
            with self._lock:
                if self._current_chars:
                    self._current_chars.pop()
            return

        # Delete and Escape → flush/discard current word
        if key in (keyboard.Key.delete, keyboard.Key.esc):
            with self._lock:
                self._current_chars.clear()
            return

        # Regular character keys
        try:
            char = key.char
            if char is not None:
                # Check if it's a punctuation that should break a word
                if char in ".,;:!?()[]{}\"'<>/\\|@#$%^&*~`":
                    self._flush_current_word()
                    # Add punctuation as its own "word" to preserve context
                    self._buffer.add_word(char, source="keyboard")
                else:
                    with self._lock:
                        self._current_chars.append(char)
        except AttributeError:
            pass

    def _on_release(self, key) -> None:
        if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self._ctrl_held = False

    # ── Helpers ───────────────────────────────────────────────

    def _flush_current_word(self) -> None:
        """Push the current character buffer as a word to the WordBuffer."""
        with self._lock:
            if self._current_chars:
                word = "".join(self._current_chars)
                self._current_chars.clear()
                # Only add non-whitespace words
                word = word.strip()
                if word:
                    self._buffer.add_word(word, source="keyboard")
