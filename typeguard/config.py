"""
TypeGuard Configuration
All tunable constants live here.
"""
import os

# ── App Identity ──────────────────────────────────────────────
APP_NAME = "TypeGuard"
APP_VERSION = "1.0.0"

# ── Paths ─────────────────────────────────────────────────────
APP_DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP_NAME)
DB_PATH = os.path.join(APP_DATA_DIR, "typeguard.db")
LOCK_FILE = os.path.join(APP_DATA_DIR, "typeguard.lock")
LOG_FILE = os.path.join(APP_DATA_DIR, "typeguard.log")

# ── Word Buffer ───────────────────────────────────────────────
MAX_WORDS = 2000                # Rolling buffer size (FIFO)

# ── Storage ───────────────────────────────────────────────────
FLUSH_INTERVAL = 5              # Seconds between DB writes

# ── Web Dashboard ─────────────────────────────────────────────
WEB_HOST = "127.0.0.1"
WEB_PORT = 5757

# ── Clipboard ─────────────────────────────────────────────────
CLIPBOARD_POLL_INTERVAL = 1.0   # Seconds between clipboard checks

# ── Hotkeys ───────────────────────────────────────────────────
PAUSE_HOTKEY = "<ctrl>+<shift>+p"       # Toggle pause/resume
RECOVERY_HOTKEY = "<ctrl>+<shift>+r"    # Copy last 100 words to clipboard

# ── Misc ──────────────────────────────────────────────────────
RECOVERY_WORD_COUNT = 100       # Words copied by recovery hotkey
QUICK_COPY_SMALL = 50           # "Copy last 50 words" tray option
QUICK_COPY_LARGE = 200          # "Copy last 200 words" tray option

# Ensure app data directory exists
os.makedirs(APP_DATA_DIR, exist_ok=True)
