"""Wallet HTTP client with configuration-based node failover."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from urllib.parse import urlparse

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = Path(os.getenv("HELIX_CONFIG", PROJECT_ROOT / "config.json"))
_CACHE_LOCK = threading.RLock()
_HEALTHY_NODES: list[str] = []


def _normalize_node(address: str) -> str | None:
    if not isinstance(address, str):
        return None
    candidate = address.strip().rstrip("/")
    if not candidate:
        return None
    if "://" not in candidate:
        candidate = "http://" + candidate
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    try:
        port = parsed.port
    except ValueError:
        return None
    host = parsed.hostname
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    netloc = host if port is None else f"{host}:{port}"
    return f"{parsed.scheme}://{netloc}"


def _load_config() -> dict:
    defaults = {
        "node": {"port": 8000, "request_timeout": 3},
        "network": {"bootstrap_nodes": []},
    }
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            loaded = json.load(file)
        defaults["node"].update(loaded.get("node", {}))
        defaults["network"].update(loaded.get("network", {}))
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    return defaults


def _configured_nodes() -> list[str]:
    config = _load_config()
    candidates = list(config["network"].get("bootstrap_nodes", []))
    env_nodes = os.getenv("HELIX_WALLET_NODES", "")
    if env_nodes:
        candidates = [item.strip() for item in env_nodes.split(",") if item.strip()] + candidates
    candidates.append(f"http://localhost:{int(config['node'].get('port', 8000))}")

    result: list[str] = []
    for candidate in candidates:
        normalized = _normalize_node(candidate)
        if normalized and normalized not in result:
            result.append(normalized)
    return result


def _candidate_nodes() -> list[str]:
    with _CACHE_LOCK:
        ordered = list(_HEALTHY_NODES)
    for node in _configured_nodes():
        if node not in ordered:
            ordered.append(node)
    return ordered


def _mark_healthy(node: str) -> None:
    with _CACHE_LOCK:
        if node in _HEALTHY_NODES:
            _HEALTHY_NODES.remove(node)
        _HEALTHY_NODES.insert(0, node)
        del _HEALTHY_NODES[10:]


def _mark_failed(node: str) -> None:
    with _CACHE_LOCK:
        if node in _HEALTHY_NODES:
            _HEALTHY_NODES.remove(node)


def _request(method: str, path: str, *, timeout: float | None = None, **kwargs):
    config = _load_config()
    request_timeout = timeout or float(config["node"].get("request_timeout", 3))
    for node in _candidate_nodes():
        try:
            response = requests.request(
                method,
                node + path,
                timeout=request_timeout,
                **kwargs,
            )
            response.raise_for_status()
            _mark_healthy(node)
            return response
        except (requests.RequestException, ValueError):
            _mark_failed(node)
    return None


def get_node():
    response = _request("GET", "/chain", timeout=2)
    if response is None:
        return None
    # Return the node URL that was promoted to the front of the healthy cache.
    with _CACHE_LOCK:
        return _HEALTHY_NODES[0] if _HEALTHY_NODES else None


def get_balance(address):
    response = _request("GET", "/balance/" + address)
    return response.json() if response is not None else None


def send_transaction(tx):
    response = _request("POST", "/transaction", json=tx)
    return response.json() if response is not None else None


def mine(address):
    response = _request("POST", "/mine", params={"address": address}, timeout=10)
    return response.json() if response is not None else None


def get_chain():
    response = _request("GET", "/chain")
    return response.json() if response is not None else None


def get_pending():
    response = _request("GET", "/pending")
    return response.json() if response is not None else None


def get_transaction(tx_id):
    response = _request("GET", "/transaction/" + tx_id)
    return response.json() if response is not None else None


def get_history(address, include_pending=True, offset=0, limit=50):
    params = {"include_pending": str(bool(include_pending)).lower(), "offset": max(0, int(offset)), "limit": max(1, int(limit))}
    response = _request("GET", "/history/" + address, params=params)
    return response.json() if response is not None else None


def get_node_stats():
    response = _request("GET", "/stats")
    return response.json() if response is not None else None


def get_health():
    response = _request("GET", "/health", timeout=2)
    return response.json() if response is not None else None
