"""Private review queue of submitted node URLs.

Anyone can submit their node URL through the wallet's Nodes tab (POST
/nodes/submit). Submissions are appended here for the operator to review — they
are NOT auto-added as peers or gossiped. The operator reviews them by reading
submissions.json or GET /nodes/submissions on their own node.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

from node.peer_manager import normalize_peer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SUBMISSIONS_FILE = Path(os.getenv("HELIX_SUBMISSIONS_FILE", PROJECT_ROOT / "submissions.json"))
MAX_SUBMISSIONS = 500
_LOCK = threading.RLock()


def _read() -> list[dict]:
    try:
        raw = json.loads(SUBMISSIONS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        raw = []
    return [item for item in raw if isinstance(item, dict)] if isinstance(raw, list) else []


def _write(items: list[dict]) -> None:
    SUBMISSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = SUBMISSIONS_FILE.with_suffix(SUBMISSIONS_FILE.suffix + ".tmp")
    tmp.write_text(json.dumps(items[:MAX_SUBMISSIONS], indent=2), encoding="utf-8")
    os.replace(tmp, SUBMISSIONS_FILE)


def get_submissions() -> list[dict]:
    with _LOCK:
        return _read()


def add_submission(url: str, note: str = "") -> str | None:
    normalized = normalize_peer(url)
    if not normalized:
        return None
    note = str(note or "")[:280]
    with _LOCK:
        items = _read()
        if any(item.get("url") == normalized for item in items):
            return normalized  # already queued; treat as success without duplicating
        items.insert(0, {"url": normalized, "note": note, "at": time.time()})
        _write(items)
        return normalized
