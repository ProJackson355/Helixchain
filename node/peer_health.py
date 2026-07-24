"""Peer probing and compatibility checks."""
from __future__ import annotations
import time, requests
from node.peer_manager import record_failure, record_success

def probe_peer(url: str, timeout: float = 3) -> dict | None:
    started = time.perf_counter()
    try:
        response = requests.get(url + "/nodes/info", timeout=timeout)
        response.raise_for_status(); data = response.json()
        latency = (time.perf_counter() - started) * 1000
        record_success(url, latency, height=data.get("height"), version=data.get("version"),
                       protocol=data.get("protocol"), network=data.get("network"))
        return data | {"url": url, "latency_ms": round(latency, 2)}
    except (requests.RequestException, ValueError, TypeError):
        record_failure(url); return None

def compatible(local: dict, remote: dict) -> bool:
    return remote.get("network") == local.get("network") and remote.get("protocol") == local.get("protocol")
