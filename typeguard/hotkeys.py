"""
TypeGuard Global Hotkeys — System-wide keyboard shortcuts for quick access.
"""
import threading
import pyperclip
from pynput import keyboard
from typeguard.word_buffer import WordBuffer
from typeguard.config import PAUSE_HOTKEY, RECOVERY_HOTKEY, RECOVERY_WORD_COUNT


class HotkeyManager:
    """
    Registers global hotkeys:
      Ctrl+Shift+P  →  Pause / Resume recording
      Ctrl+Shift+R  →  Copy last N words to clipboard
    """

    def __init__(self, word_buffer: WordBuffer, on_toggle_pause=None, on_recovery=None):
        self._buffer = word_buffer
        self._on_toggle_pause = on_toggle_pause  # callback(is_paused: bool)
        self._on_recovery = on_recovery            # callback(text: str)
        self._hotkeys: keyboard.GlobalHotKeys | None = None

    def start(self) -> None:
        """Register and start listening for hotkeys."""
        self._hotkeys = keyboard.GlobalHotKeys({
            PAUSE_HOTKEY: self._handle_pause,
            RECOVERY_HOTKEY: self._handle_recovery,
        })
        self._hotkeys.daemon = True
        self._hotkeys.start()

    def stop(self) -> None:
        if self._hotkeys:
            self._hotkeys.stop()

    def _handle_pause(self) -> None:
        is_paused = self._buffer.toggle_pause()
        if self._on_toggle_pause:
            self._on_toggle_pause(is_paused)

    def _handle_recovery(self) -> None:
        text = self._buffer.get_text(last_n=RECOVERY_WORD_COUNT)
        if text:
            try:
                pyperclip.copy(text)
            except Exception:
                pass
        if self._on_recovery:
            self._on_recovery(text)
