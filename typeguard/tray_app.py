"""
TypeGuard System Tray Application — Always-visible tray icon with quick-access menu.
Uses pystray for native Windows system-tray integration and Pillow for icon generation.
"""
import threading
import webbrowser
import pyperclip
from PIL import Image, ImageDraw, ImageFont

import pystray
from pystray import MenuItem, Menu

from typeguard.word_buffer import WordBuffer
from typeguard.config import (
    APP_NAME, WEB_HOST, WEB_PORT,
    QUICK_COPY_SMALL, QUICK_COPY_LARGE,
)


def _create_icon_image(active: bool = True) -> Image.Image:
    """Generate a small tray icon using Pillow (no external file needed)."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle
    bg_color = (34, 197, 94, 255) if active else (245, 158, 11, 255)  # green / amber
    draw.ellipse([4, 4, size - 4, size - 4], fill=bg_color)

    # Draw a "T" letter on the icon
    text_color = (255, 255, 255, 255)
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except OSError:
        font = ImageFont.load_default()

    # Center the text
    bbox = draw.textbbox((0, 0), "T", font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) // 2
    ty = (size - th) // 2 - 2
    draw.text((tx, ty), "T", fill=text_color, font=font)

    return img


class TrayApp:
    """
    System tray application with right-click context menu for:
    - Quick View (copy recent words)
    - Open Web Dashboard
    - Pause / Resume
    - Status info
    - Exit
    """

    def __init__(self, word_buffer: WordBuffer, shutdown_callback=None):
        self._buffer = word_buffer
        self._shutdown_callback = shutdown_callback
        self._icon: pystray.Icon | None = None
        self._active_icon = _create_icon_image(active=True)
        self._paused_icon = _create_icon_image(active=False)

    def _build_menu(self) -> Menu:
        pause_label = "▶ Resume Recording" if self._buffer.paused else "⏸ Pause Recording"
        status = f"📊 Words: {self._buffer.get_count()} / 2000"
        state_label = "🟠 PAUSED" if self._buffer.paused else "🟢 ACTIVE"

        return Menu(
            MenuItem(f"🛡️ {APP_NAME}", None, enabled=False),
            MenuItem(state_label, None, enabled=False),
            MenuItem(status, None, enabled=False),
            Menu.SEPARATOR,
            MenuItem(f"📋 Copy Last {QUICK_COPY_SMALL} Words", self._copy_small),
            MenuItem(f"📋 Copy Last {QUICK_COPY_LARGE} Words", self._copy_large),
            MenuItem("📋 Copy All Words", self._copy_all),
            Menu.SEPARATOR,
            MenuItem("🌐 Open Dashboard", self._open_dashboard),
            MenuItem(pause_label, self._toggle_pause),
            Menu.SEPARATOR,
            MenuItem("❌ Exit TypeGuard", self._exit),
        )

    # ── Menu Actions ──────────────────────────────────────────

    def _copy_small(self, icon, item):
        text = self._buffer.get_text(last_n=QUICK_COPY_SMALL)
        if text:
            pyperclip.copy(text)
            self._notify("Copied last {} words to clipboard!".format(QUICK_COPY_SMALL))

    def _copy_large(self, icon, item):
        text = self._buffer.get_text(last_n=QUICK_COPY_LARGE)
        if text:
            pyperclip.copy(text)
            self._notify("Copied last {} words to clipboard!".format(QUICK_COPY_LARGE))

    def _copy_all(self, icon, item):
        text = self._buffer.get_text()
        if text:
            pyperclip.copy(text)
            self._notify("Copied all {} words to clipboard!".format(self._buffer.get_count()))

    def _open_dashboard(self, icon, item):
        webbrowser.open(f"http://{WEB_HOST}:{WEB_PORT}")

    def _toggle_pause(self, icon, item):
        is_paused = self._buffer.toggle_pause()
        self._icon.icon = self._paused_icon if is_paused else self._active_icon
        self._icon.menu = self._build_menu()
        state = "PAUSED" if is_paused else "RESUMED"
        self._notify(f"TypeGuard {state}")

    def _exit(self, icon, item):
        if self._shutdown_callback:
            self._shutdown_callback()
        icon.stop()

    # ── Notifications ─────────────────────────────────────────

    def _notify(self, message: str) -> None:
        if self._icon:
            try:
                self._icon.notify(message, APP_NAME)
            except Exception:
                pass

    # ── Public API ────────────────────────────────────────────

    def update_icon(self, is_paused: bool) -> None:
        """Update icon color based on pause state (called from hotkey manager)."""
        if self._icon:
            self._icon.icon = self._paused_icon if is_paused else self._active_icon
            self._icon.menu = self._build_menu()

    def notify_external(self, message: str) -> None:
        """Show a tray notification from an external caller."""
        self._notify(message)

    def run(self) -> None:
        """Run the tray app (BLOCKS — call from main thread or dedicated thread)."""
        self._icon = pystray.Icon(
            APP_NAME,
            icon=self._active_icon,
            title=f"{APP_NAME} — Text Recovery Active",
            menu=self._build_menu(),
        )
        self._icon.run()
