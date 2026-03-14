"""
TypeGuard Main Entry Point — Orchestrates all components.
Start with:  python -m typeguard.main
"""
import sys
import os
import time
import threading
import atexit
import logging

# ── Logging setup ─────────────────────────────────────────────
from typeguard.config import LOG_FILE, APP_DATA_DIR, FLUSH_INTERVAL, APP_NAME

os.makedirs(APP_DATA_DIR, exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(APP_NAME)

# ── Single-instance lock ──────────────────────────────────────
from typeguard.config import LOCK_FILE

_lock_handle = None


def acquire_lock() -> bool:
    """Ensure only one instance of TypeGuard is running."""
    global _lock_handle
    try:
        if os.path.exists(LOCK_FILE):
            # Check if the PID in the lock file is still running
            try:
                with open(LOCK_FILE, "r") as f:
                    old_pid = int(f.read().strip())
                # On Windows, check if the process exists
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(0x1000, False, old_pid)  # PROCESS_QUERY_LIMITED_INFORMATION
                if handle:
                    kernel32.CloseHandle(handle)
                    return False  # Another instance is running
            except (ValueError, OSError, AttributeError):
                pass  # Stale lock file, proceed

        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
        _lock_handle = LOCK_FILE
        return True
    except Exception as e:
        log.error(f"Lock acquisition failed: {e}")
        return True  # Proceed anyway if lock check fails


def release_lock():
    """Remove the lock file on exit."""
    try:
        if _lock_handle and os.path.exists(_lock_handle):
            os.remove(_lock_handle)
    except Exception:
        pass


# ── Component imports ─────────────────────────────────────────
from typeguard.word_buffer import WordBuffer
from typeguard.storage import Storage
from typeguard.keylogger import KeyboardListener
from typeguard.clipboard_watcher import ClipboardWatcher
from typeguard.hotkeys import HotkeyManager
from typeguard.tray_app import TrayApp
from typeguard.web_dashboard import initialize as init_web, run_server


def main():
    log.info("=" * 50)
    log.info(f"{APP_NAME} starting up...")

    # ── Single-instance check ─────────────────────────────
    if not acquire_lock():
        log.warning("Another instance is already running. Exiting.")
        print("TypeGuard is already running!")
        sys.exit(1)
    atexit.register(release_lock)

    # ── Initialize core components ────────────────────────
    log.info("Initializing components...")

    # 1. Word buffer (in-memory FIFO)
    word_buffer = WordBuffer()

    # 2. Storage (SQLite)
    storage = Storage()

    # 3. Load existing words from DB (survives reboots)
    existing_words = storage.load_words()
    if existing_words:
        word_buffer.load_initial(existing_words)
        log.info(f"Loaded {len(existing_words)} words from database")

    # 4. Keyboard listener
    keyboard_listener = KeyboardListener(word_buffer)

    # 5. Clipboard watcher
    clipboard_watcher = ClipboardWatcher(word_buffer)

    # 6. Web dashboard
    init_web(word_buffer, storage)

    # 7. System tray app (will be the shutdown coordinator)
    shutdown_event = threading.Event()

    def on_shutdown():
        log.info("Shutdown requested...")
        shutdown_event.set()

    tray_app = TrayApp(word_buffer, shutdown_callback=on_shutdown)

    # 8. Hotkey manager (with callbacks to tray app for visual feedback)
    def on_pause_toggle(is_paused):
        tray_app.update_icon(is_paused)
        state = "paused" if is_paused else "resumed"
        tray_app.notify_external(f"TypeGuard {state}")
        log.info(f"Recording {state}")

    def on_recovery(text):
        if text:
            tray_app.notify_external(f"Last 100 words copied to clipboard!")
            log.info("Recovery hotkey activated — text copied to clipboard")
        else:
            tray_app.notify_external("No text to recover yet")

    hotkey_manager = HotkeyManager(
        word_buffer,
        on_toggle_pause=on_pause_toggle,
        on_recovery=on_recovery,
    )

    # ── Start all components ──────────────────────────────
    log.info("Starting keyboard listener...")
    keyboard_listener.start()

    log.info("Starting clipboard watcher...")
    clipboard_watcher.start()

    log.info("Starting hotkey manager...")
    hotkey_manager.start()

    log.info("Starting web dashboard...")
    web_thread = threading.Thread(target=run_server, daemon=True)
    web_thread.start()

    # ── Periodic DB flush ─────────────────────────────────
    def flush_loop():
        while not shutdown_event.is_set():
            try:
                pending = word_buffer.drain_pending()
                if pending:
                    storage.flush(pending)
                    log.debug(f"Flushed {len(pending)} words to database")
            except Exception as e:
                log.error(f"Flush error: {e}")
            shutdown_event.wait(timeout=FLUSH_INTERVAL)

    flush_thread = threading.Thread(target=flush_loop, daemon=True)
    flush_thread.start()

    log.info(f"All systems go! Dashboard at http://127.0.0.1:5757")
    log.info("TypeGuard is now protecting your typed text.")

    # ── Run tray app (blocks main thread) ─────────────────
    try:
        tray_app.run()
    except KeyboardInterrupt:
        log.info("Interrupted by user")
    finally:
        # ── Graceful shutdown ─────────────────────────────
        log.info("Shutting down...")
        shutdown_event.set()

        # Final flush — save any remaining words
        pending = word_buffer.drain_pending()
        if pending:
            storage.flush(pending)
            log.info(f"Final flush: {len(pending)} words saved")

        keyboard_listener.stop()
        clipboard_watcher.stop()
        hotkey_manager.stop()
        release_lock()
        log.info("TypeGuard stopped. Your text is safely stored.")


if __name__ == "__main__":
    # Handle --install / --uninstall flags (for .exe distribution)
    if "--install" in sys.argv or "--uninstall" in sys.argv:
        from typeguard.install import main as install_main
        install_main()
    else:
        main()
