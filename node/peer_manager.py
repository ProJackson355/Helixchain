"""Thread-safe persistent peer metadata storage for Helix nodes."""
from __future__ import annotations
import json, os, threading, time
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = Path(os.getenv("HELIX_CONFIG", PROJECT_ROOT / "config.json"))
PEERS_FILE = Path(os.getenv("HELIX_PEERS_FILE", PROJECT_ROOT / "peers.json"))
_LOCK = threading.RLock()


def _config() -> dict:
    data = {"node": {"max_peers": 250}, "network": {"bootstrap_nodes": [], "peer_failure_limit": 5}}
    try:
        loaded = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        data["node"].update(loaded.get("node", {})); data["network"].update(loaded.get("network", {}))
    except (OSError, ValueError, TypeError):
        pass
    env_bootstrap = os.getenv("HELIX_BOOTSTRAP_NODES", "")
    if env_bootstrap:
        existing = list(data["network"].get("bootstrap_nodes", []))
        for candidate in env_bootstrap.split(","):
            candidate = candidate.strip()
            if candidate and candidate not in existing:
                existing.append(candidate)
        data["network"]["bootstrap_nodes"] = existing
    return data


def normalize_peer(value: str) -> str | None:
    if not isinstance(value, str): return None
    value = value.strip().rstrip("/")
    if not value: return None
    if "://" not in value: value = "http://" + value
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname: return None
    try: port = parsed.port
    except ValueError: return None
    host = parsed.hostname
    if ":" in host and not host.startswith("["): host = f"[{host}]"
    return f"{parsed.scheme}://{host}{f':{port}' if port else ''}"


def _default(url: str) -> dict:
    return {"url": url, "last_seen": None, "latency_ms": None, "failures": 0, "score": 50,
            "height": None, "version": None, "protocol": None, "network": None}


def _read() -> list[dict]:
    try: raw = json.loads(PEERS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError): raw = []
    result = []
    for item in raw if isinstance(raw, list) else []:
        if isinstance(item, str): item = _default(item)
        if not isinstance(item, dict): continue
        url = normalize_peer(item.get("url", ""))
        if not url: continue
        merged = _default(url); merged.update(item); merged["url"] = url
        if url not in [p["url"] for p in result]: result.append(merged)
    return result


def _write(records: list[dict]) -> None:
    PEERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = PEERS_FILE.with_suffix(PEERS_FILE.suffix + ".tmp")
    tmp.write_text(json.dumps(records, indent=2), encoding="utf-8")
    os.replace(tmp, PEERS_FILE)


def get_peer_records() -> list[dict]:
    with _LOCK:
        records = _read()
        for value in _config()["network"].get("bootstrap_nodes", []):
            url = normalize_peer(value)
            if url and url not in [p["url"] for p in records]: records.append(_default(url))
        records.sort(key=lambda p: (p.get("score", 0), p.get("last_seen") or 0), reverse=True)
        records = records[:max(1, int(_config()["node"].get("max_peers", 250)))]
        _write(records)
        return [dict(p) for p in records]


def get_peers() -> list[str]: return [p["url"] for p in get_peer_records()]

def add_peer(peer_address: str, *_ignored, **metadata) -> list[str]:
    url = normalize_peer(peer_address)
    if not url: return get_peers()
    with _LOCK:
        records = get_peer_records(); peer = next((p for p in records if p["url"] == url), None)
        if peer is None: peer = _default(url); records.append(peer)
        peer.update({k: v for k, v in metadata.items() if k in peer and v is not None})
        _write(records); return [p["url"] for p in records]

def remove_peer(peer_address: str, *_ignored) -> list[str]:
    url = normalize_peer(peer_address)
    with _LOCK:
        records = [p for p in get_peer_records() if p["url"] != url]; _write(records); return [p["url"] for p in records]

def has_peer(peer_address: str) -> bool:
    url = normalize_peer(peer_address); return bool(url and url in get_peers())

def clear_peers() -> list[str]:
    with _LOCK: _write([]); return []

def record_success(peer_address: str, latency_ms: float, **metadata) -> None:
    url = normalize_peer(peer_address)
    if not url: return
    with _LOCK:
        records = get_peer_records(); peer = next((p for p in records if p["url"] == url), _default(url))
        if peer not in records: records.append(peer)
        peer.update({"last_seen": time.time(), "latency_ms": round(float(latency_ms), 2), "failures": 0,
                     "score": min(100, int(peer.get("score", 50)) + 5)})
        peer.update({k: v for k, v in metadata.items() if k in peer and v is not None}); _write(records)

def record_failure(peer_address: str) -> None:
    url = normalize_peer(peer_address)
    if not url: return
    with _LOCK:
        records = get_peer_records(); peer = next((p for p in records if p["url"] == url), None)
        if peer is None: return
        peer["failures"] = int(peer.get("failures", 0)) + 1; peer["score"] = max(0, int(peer.get("score", 50)) - 10)
        limit = int(_config()["network"].get("peer_failure_limit", 5))
        if peer["failures"] >= limit and url not in [normalize_peer(x) for x in _config()["network"].get("bootstrap_nodes", [])]:
            records.remove(peer)
        _write(records)
