"""Persistent node identity management.

Peer storage lives in node.peer_manager. Compatibility wrappers remain so old
imports continue to work while the project transitions to the new layout.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from node.peer_manager import add_peer, clear_peers, get_peers, has_peer, remove_peer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PORT = int(os.getenv("NODE_PORT", "8000"))
NODE_FILE = Path(os.getenv("HELIX_NODE_FILE", PROJECT_ROOT / f"node_{PORT}.json"))


def save_node(node: dict) -> None:
    NODE_FILE.parent.mkdir(parents=True, exist_ok=True)
    required_capabilities = {"transactions", "mining", "chain-sync", "mempool-gossip", "block-relay", "chainwork-consensus", "orphan-pool", "checkpoints", "dynamic-difficulty", "wallet-history", "custom-tokens", "token-exchange", "recent-transactions"}
    capabilities = sorted(required_capabilities | set(node.get("capabilities", [])))
    clean_node = {
        "id": node["id"],
        "port": int(node.get("port", PORT)),
        "created": node.get("created", datetime.now(timezone.utc).isoformat()),
        "version": "1.0.0",
        "capabilities": capabilities,
    }
    temporary = NODE_FILE.with_suffix(NODE_FILE.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as file:
        json.dump(clean_node, file, indent=4)
        file.flush()
        os.fsync(file.fileno())
    os.replace(temporary, NODE_FILE)


def load_node() -> dict | None:
    if not NODE_FILE.exists():
        return None
    try:
        with NODE_FILE.open("r", encoding="utf-8") as file:
            node = json.load(file)
        if not isinstance(node, dict) or not node.get("id"):
            return None

        # One-time migration from the old embedded peer list.
        for peer in node.pop("peers", []) if isinstance(node.get("peers", []), list) else []:
            add_peer(peer)
        save_node(node)
        return node
    except (OSError, json.JSONDecodeError, TypeError, KeyError, ValueError):
        return None


def create_node(port: int) -> dict:
    node = {
        "id": str(uuid.uuid4()),
        "port": int(port),
        "created": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "capabilities": ["transactions", "mining", "chain-sync", "mempool-gossip", "block-relay", "chainwork-consensus", "orphan-pool", "checkpoints", "dynamic-difficulty", "wallet-history", "custom-tokens", "token-exchange", "recent-transactions"],
    }
    save_node(node)
    return node


def get_or_create_node(port: int = PORT) -> dict:
    node = load_node()
    if node is None:
        node = create_node(port)
    elif int(node.get("port", port)) != int(port):
        node["port"] = int(port)
        save_node(node)
    return node


def get_node() -> dict:
    return get_or_create_node(PORT)


def get_node_id() -> str:
    return get_node()["id"]


def update_port(port: int) -> dict:
    node = get_or_create_node(port)
    node["port"] = int(port)
    save_node(node)
    return node
