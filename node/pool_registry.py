"""Persistent registry of known mining-pool URLs, gossiped across nodes.

Anyone can list a pool by registering its URL with any node; the list then
propagates to other nodes the same way peers do, so every node's Pools tab
shows the same directory. Live details (fee, active miners, up/down) are read
by the browser directly from each pool's /pool/info and /pool/stats.
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path

from node.peer_manager import normalize_peer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
POOLS_FILE = Path(os.getenv("HELIX_POOLS_FILE", PROJECT_ROOT / "pools.json"))
MAX_POOLS = 200
_LOCK = threading.RLock()


def _read() -> list[str]:
    try:
        raw = json.loads(POOLS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        raw = []
    urls: list[str] = []
    for item in raw if isinstance(raw, list) else []:
        candidate = item if isinstance(item, str) else (item.get("url", "") if isinstance(item, dict) else "")
        url = normalize_peer(candidate)
        if url and url not in urls:
            urls.append(url)
    return urls


def _write(urls: list[str]) -> None:
    POOLS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = POOLS_FILE.with_suffix(POOLS_FILE.suffix + ".tmp")
    tmp.write_text(json.dumps(urls[:MAX_POOLS], indent=2), encoding="utf-8")
    os.replace(tmp, POOLS_FILE)


def get_pools() -> list[str]:
    with _LOCK:
        return _read()


def add_pool(url: str) -> list[str]:
    normalized = normalize_peer(url)
    if not normalized:
        return get_pools()
    with _LOCK:
        urls = _read()
        if normalized not in urls:
            urls.append(normalized)
            _write(urls)
        return urls


def add_pools(url_list) -> list[str]:
    if not isinstance(url_list, (list, tuple)):
        return get_pools()
    with _LOCK:
        urls = _read()
        changed = False
        for candidate in url_list:
            normalized = normalize_peer(candidate if isinstance(candidate, str) else "")
            if normalized and normalized not in urls:
                urls.append(normalized)
                changed = True
        if changed:
            _write(urls)
        return urls


def remove_pool(url: str) -> list[str]:
    normalized = normalize_peer(url)
    with _LOCK:
        urls = [u for u in _read() if u != normalized]
        _write(urls)
        return urls
