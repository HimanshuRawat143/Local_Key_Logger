"""
TypeGuard Web Dashboard — Beautiful local web UI for browsing and searching typed text.
Flask server on a daemon thread at http://localhost:5757
"""
import time
import os
import json
from flask import Flask, render_template, jsonify, request, send_from_directory
from typeguard.word_buffer import WordBuffer
from typeguard.storage import Storage
from typeguard.config import WEB_HOST, WEB_PORT, MAX_WORDS, APP_NAME

# Resolve template and static paths
# When bundled with PyInstaller, files are extracted to sys._MEIPASS
import sys
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    _base_dir = sys._MEIPASS
    _template_dir = os.path.join(_base_dir, "typeguard", "assets", "templates")
    _static_dir = os.path.join(_base_dir, "typeguard", "assets", "static")
else:
    _base_dir = os.path.dirname(os.path.abspath(__file__))
    _template_dir = os.path.join(_base_dir, "assets", "templates")
    _static_dir = os.path.join(_base_dir, "assets", "static")

app = Flask(
    APP_NAME,
    template_folder=_template_dir,
    static_folder=_static_dir,
)

# Suppress Flask's default logging (runs silently in background)
import logging
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

# These will be set by initialize()
_word_buffer: WordBuffer = None  # type: ignore
_storage: Storage = None          # type: ignore


def initialize(word_buffer: WordBuffer, storage: Storage) -> None:
    """Inject dependencies before starting the server."""
    global _word_buffer, _storage
    _word_buffer = word_buffer
    _storage = storage


# ── Routes ────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/words")
def api_words():
    """Return words as JSON, optionally limited by ?last=N"""
    last_n = request.args.get("last", type=int)
    if last_n:
        entries = _word_buffer.get_last_n(last_n)
    else:
        entries = _word_buffer.get_all()

    # Group words into time segments (5-minute windows)
    segments = _group_into_segments(entries)
    return jsonify({
        "segments": segments,
        "total_words": _word_buffer.get_count(),
        "max_words": MAX_WORDS,
    })


@app.route("/api/stats")
def api_stats():
    """Return buffer and storage statistics."""
    stats = _storage.get_stats()
    stats["buffer_count"] = _word_buffer.get_count()
    stats["max_words"] = MAX_WORDS
    stats["is_paused"] = _word_buffer.paused
    return jsonify(stats)


@app.route("/api/text")
def api_text():
    """Return all words as plain text."""
    last_n = request.args.get("last", type=int)
    text = _word_buffer.get_text(last_n=last_n)
    return jsonify({"text": text})


@app.route("/api/clear", methods=["POST"])
def api_clear():
    """Clear all words from buffer and database."""
    _word_buffer.clear()
    _storage.clear_all()
    return jsonify({"status": "cleared"})


# ── Helpers ───────────────────────────────────────────────────

def _group_into_segments(entries, window_seconds=300):
    """Group word entries into time-based segments (default 5 min)."""
    if not entries:
        return []

    segments = []
    current_segment = {
        "start_time": entries[0].timestamp,
        "end_time": entries[0].timestamp,
        "words": [],
        "sources": set(),
    }

    for entry in entries:
        # Check if this entry falls in the current window
        if entry.timestamp - current_segment["start_time"] <= window_seconds:
            current_segment["words"].append(entry.word)
            current_segment["sources"].add(entry.source)
            current_segment["end_time"] = entry.timestamp
        else:
            # Finalize current segment and start a new one
            current_segment["sources"] = list(current_segment["sources"])
            current_segment["text"] = " ".join(current_segment["words"])
            current_segment["word_count"] = len(current_segment["words"])
            del current_segment["words"]
            segments.append(current_segment)
            current_segment = {
                "start_time": entry.timestamp,
                "end_time": entry.timestamp,
                "words": [entry.word],
                "sources": {entry.source},
            }

    # Don't forget the last segment
    current_segment["sources"] = list(current_segment["sources"])
    current_segment["text"] = " ".join(current_segment["words"])
    current_segment["word_count"] = len(current_segment["words"])
    del current_segment["words"]
    segments.append(current_segment)

    return segments


def run_server():
    """Start the Flask dev server (call from a daemon thread)."""
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False, use_reloader=False)
