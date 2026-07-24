"""Bootstrap peer discovery."""
from __future__ import annotations
import requests
from node.peer_manager import add_peer, normalize_peer

def discover_from_bootstrap(bootstrap_nodes: list[str], self_url: str | None = None, timeout: float = 4) -> list[str]:
    found = []
    for bootstrap in bootstrap_nodes:
        base = normalize_peer(bootstrap)
        if not base: continue
        try:
            r = requests.get(base + "/nodes/peers", timeout=timeout); r.raise_for_status()
            candidates = r.json().get("peers", [])
            for candidate in candidates:
                url = normalize_peer(candidate)
                if url and url != self_url and url not in found:
                    add_peer(url); found.append(url)
        except (requests.RequestException, ValueError, TypeError):
            continue
    return found
