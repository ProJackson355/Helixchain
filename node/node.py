from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from node.blockchain import Blockchain, Block
from node.transaction import Transaction
from node.node_manager import get_node
from node.peer_manager import add_peer, get_peers, get_peer_records, has_peer, normalize_peer, record_failure, record_success
from node.pool_registry import add_pool, add_pools, get_pools
from node.submissions import add_submission, get_submissions
from node.bootstrap import discover_from_bootstrap
from node.peer_health import compatible, probe_peer
from node.mempool import MempoolRelay
from node.security import SecurityManager, SecurityMiddleware, safe_identifier, validate_hex
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
import hashlib
import json
import requests
import os
import secrets
import time
import threading
import socket


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.getenv("HELIX_CONFIG", os.path.join(PROJECT_ROOT, "config.json"))


def _load_config() -> dict:
    defaults = {
        "node": {"port": 8000, "sync_interval": 30, "version": "1.0.0", "protocol": 10, "network": "mainnet"},
        "network": {"discovery_ports": [8000, 8001, 8002, 8003, 8004, 8005], "bootstrap_nodes": [], "public_url": ""},
        "mempool": {"transaction_ttl_seconds": 3600, "rebroadcast_interval": 60, "inventory_batch_size": 500, "max_pending_transactions": 5000},
        "blockchain": {"difficulty": 3, "difficulty_reset_value": 3, "difficulty_reset_height": 161, "reward": 10, "mining_reward": 2, "mining_reward_activation_height": 90, "fractional_mining_reward": "10", "fractional_reward_activation_height": 300, "native_dad_address": "9d7c721b209cee99a8158c524fa433ead9236781", "native_dad_activation_height": 300, "max_supply": 20000000, "min_difficulty": 3, "max_difficulty": 8, "difficulty_adjustment_interval": 10, "target_block_time_seconds": 60, "adaptive_target_block_time_seconds": 600, "adaptive_difficulty_activation_height": 60, "new_target_block_time_seconds": 160, "new_target_block_time_activation_height": 161, "difficulty_activation_height": 10, "fine_difficulty_activation_height": 100000000, "fine_target_block_time_seconds": 120, "token_metadata_activation_height": 41, "token_exchange_activation_height": 41, "token_swap_activation_height": 200, "max_orphans": 100, "orphan_ttl_seconds": 1800, "checkpoints": {}},
        "security": {"max_request_body_bytes": 1048576, "require_admin_api_key": False, "cors_allowed_origins": ["http://localhost", "http://127.0.0.1"]},
        "performance": {"default_page_size": 50, "max_page_size": 500},
    }
    try:
        import json
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            loaded = json.load(file)
        defaults["node"].update(loaded.get("node", {}))
        defaults["network"].update(loaded.get("network", {}))
        defaults["mempool"].update(loaded.get("mempool", {}))
        defaults["blockchain"].update(loaded.get("blockchain", {}))
        defaults["security"].update(loaded.get("security", {}))
        defaults["performance"].update(loaded.get("performance", {}))
    except (OSError, ValueError, TypeError):
        pass
    # HELIX_BOOTSTRAP_NODES (comma-separated URLs) merges into the configured
    # bootstrap list without editing config.json. Empty by default, so this is a
    # no-op until a stable seed node (e.g. a named-tunnel domain) is provided.
    env_bootstrap = os.getenv("HELIX_BOOTSTRAP_NODES", "")
    if env_bootstrap:
        existing = list(defaults["network"].get("bootstrap_nodes", []))
        for candidate in env_bootstrap.split(","):
            candidate = candidate.strip()
            if candidate and candidate not in existing:
                existing.append(candidate)
        defaults["network"]["bootstrap_nodes"] = existing
    return defaults


_CONFIG = _load_config()
_DISCOVER_PORTS_RAW = os.getenv("HELIX_DISCOVER_PORTS")
DISCOVER_PORTS = (
    [int(value.strip()) for value in _DISCOVER_PORTS_RAW.split(",") if value.strip()]
    if _DISCOVER_PORTS_RAW
    else [int(value) for value in _CONFIG["network"]["discovery_ports"]]
)
BACKGROUND_INTERVAL = int(
    os.getenv("HELIX_SYNC_INTERVAL", str(_CONFIG["node"]["sync_interval"]))
)
DEFAULT_PAGE_SIZE = int(_CONFIG["performance"].get("default_page_size", 50))
MAX_PAGE_SIZE = int(_CONFIG["performance"].get("max_page_size", 500))

def _page_bounds(offset: int, limit: int) -> tuple[int, int]:
    return max(0, int(offset)), max(1, min(int(limit), MAX_PAGE_SIZE))


# ---------------------------------------------------------------------------
# Block / chain serialisation helpers
# ---------------------------------------------------------------------------

def block_to_dict(block) -> dict:
    return {
        "index":         block.index,
        "previous_hash": block.previous_hash,
        "timestamp":     block.timestamp,
        "nonce":         block.nonce,
        "hash":          block.hash,
        "transactions":  [tx.to_dict() for tx in block.transactions],
    }


def dict_to_block(data: dict) -> Block:
    if not isinstance(data, dict):
        raise ValueError("block payload must be an object")

    required = ("index", "transactions", "previous_hash", "timestamp", "nonce", "hash")
    missing = [field for field in required if field not in data]
    if missing:
        raise ValueError(f"missing block fields: {', '.join(missing)}")
    if not isinstance(data["transactions"], list):
        raise ValueError("transactions must be a list")
    if len(data["transactions"]) > 5000:
        raise ValueError("block contains too many transactions")
    if not isinstance(data["index"], int) or data["index"] < 0:
        raise ValueError("block index is invalid")
    if not isinstance(data["nonce"], int) or data["nonce"] < 0:
        raise ValueError("block nonce is invalid")
    validate_hex(data["hash"], "block hash", (64,))
    if data["index"] > 0:
        validate_hex(data["previous_hash"], "previous hash", (64,))

    txs = []
    for td in data["transactions"]:
        if not isinstance(td, dict):
            raise ValueError("transaction payload must be an object")
        tx = Transaction(
            td["sender"],
            td["receiver"],
            td["amount"],
            tx_type=td.get("tx_type", "transfer"),
            mint_address=td.get("mint_address"),
            dad_address=td.get("dad_address"),
            nonce=td.get("nonce"),
            name=td.get("name"),
            symbol=td.get("symbol"),
            description=td.get("description"),
            image=td.get("image"),
            metadata_hash=td.get("metadata_hash"),
            decimals=td.get("decimals"),
            uri=td.get("uri"),
            hlx_amount=td.get("hlx_amount"),
            min_receive=td.get("min_receive"),
            target_mint_address=td.get("target_mint_address"),
        )
        tx.signature = td.get("signature")
        tx.tx_id = td.get("tx_id")
        pem = td.get("public_key")
        if pem:
            tx.public_key = serialization.load_pem_public_key(pem.encode())
        txs.append(tx)

    return Block(
        data["index"], txs, data["previous_hash"],
        data["timestamp"], data["nonce"], data["hash"],
    )


# ---------------------------------------------------------------------------
# Broadcast helpers
# ---------------------------------------------------------------------------

def _transaction_from_payload(data: dict) -> Transaction:
    if not isinstance(data, dict):
        raise ValueError("transaction payload must be an object")
    tx_type = data.get("tx_type", "transfer")
    if tx_type not in {"transfer", *Transaction.TOKEN_TYPES, *Transaction.NFT_TYPES}:
        raise ValueError("transaction type is unsupported")
    common_fields = {
        "sender", "receiver", "amount", "signature", "public_key",
        "tx_id", "received_at",
    }
    token_fields = {"tx_type", "mint_address", "nonce"}
    create_fields = {
        "dad_address", "name", "symbol", "description", "image",
        "metadata_hash", "decimals", "uri",
    }
    pool_create_fields = {"hlx_amount"}
    swap_fields = {"min_receive"}
    token_swap_fields = {"target_mint_address"}
    nft_fields = {"tx_type", "nft_id", "nonce"}
    nft_mint_fields = {"name", "description", "image", "uri", "metadata_hash", "attributes", "royalty_bps"}
    allowed_fields = common_fields
    if tx_type in Transaction.TOKEN_TYPES:
        allowed_fields = allowed_fields | token_fields
    if tx_type == "token_create":
        allowed_fields = allowed_fields | create_fields
    if tx_type == "token_pool_create":
        allowed_fields = allowed_fields | pool_create_fields
    if tx_type in {"token_buy", "token_sell", "token_swap"}:
        allowed_fields = allowed_fields | swap_fields
    if tx_type == "token_swap":
        allowed_fields = allowed_fields | token_swap_fields
    if tx_type in Transaction.NFT_TYPES:
        allowed_fields = allowed_fields | nft_fields
    if tx_type == "nft_mint":
        allowed_fields = allowed_fields | nft_mint_fields
    unknown = set(data) - allowed_fields
    if unknown:
        raise ValueError(f"unexpected transaction fields: {', '.join(sorted(unknown))}")
    required = ("sender", "receiver", "amount", "signature", "public_key")
    if tx_type in Transaction.TOKEN_TYPES:
        required += ("tx_type", "mint_address", "nonce")
    if tx_type == "token_create":
        required += (
            "dad_address", "name", "symbol", "description", "image",
            "metadata_hash", "decimals", "uri",
        )
    if tx_type == "token_pool_create":
        required += ("hlx_amount",)
    if tx_type in {"token_buy", "token_sell", "token_swap"}:
        required += ("min_receive",)
    if tx_type == "token_swap":
        required += ("target_mint_address",)
    if tx_type in Transaction.NFT_TYPES:
        required += ("tx_type", "nft_id", "nonce")
    if tx_type == "nft_mint":
        required += ("name", "description", "image", "uri", "metadata_hash")
    missing = [field for field in required if data.get(field) in (None, "")]
    if missing:
        raise ValueError(f"missing transaction fields: {', '.join(missing)}")
    sender = validate_hex(data["sender"], "sender", (40,))
    receiver = validate_hex(data["receiver"], "receiver", (40,))
    signature = data["signature"]
    if not isinstance(signature, str) or len(signature) < 128 or len(signature) > 160 or len(signature) % 2:
        raise ValueError("signature is invalid")
    try:
        bytes.fromhex(signature)
    except ValueError as exc:
        raise ValueError("signature must be hexadecimal") from exc
    public_key = data["public_key"]
    if not isinstance(public_key, str) or len(public_key) > 2048:
        raise ValueError("public_key is invalid")
    tx = Transaction(
        sender,
        receiver,
        data["amount"],
        received_at=data.get("received_at"),
        tx_type=tx_type,
        mint_address=data.get("mint_address"),
        dad_address=data.get("dad_address"),
        nonce=data.get("nonce"),
        name=data.get("name"),
        symbol=data.get("symbol"),
        description=data.get("description"),
        image=data.get("image"),
        metadata_hash=data.get("metadata_hash"),
        decimals=data.get("decimals"),
        uri=data.get("uri"),
        hlx_amount=data.get("hlx_amount"),
        min_receive=data.get("min_receive"),
        target_mint_address=data.get("target_mint_address"),
        nft_id=data.get("nft_id"),
        attributes=data.get("attributes"),
        royalty_bps=data.get("royalty_bps"),
    )
    tx.signature = signature
    tx.public_key = serialization.load_pem_public_key(data["public_key"].encode())
    supplied_id = data.get("tx_id")
    if supplied_id is not None:
        validate_hex(supplied_id, "tx_id", (64,))
    calculated_id = tx.calculate_id()
    if supplied_id and supplied_id != calculated_id:
        raise ValueError("transaction ID does not match signed contents")
    tx.tx_id = supplied_id or calculated_id
    return tx


def transaction_to_relay_dict(tx: Transaction) -> dict:
    payload = tx.to_dict()
    payload["received_at"] = tx.received_at
    return payload


def _cancellation_payload(tx_id: str, sender: str) -> bytes:
    return json.dumps(
        {"action": "cancel_pending", "sender": sender, "tx_id": tx_id},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def _verify_cancellation(tx_id: str, data: dict) -> tuple[str, str, str]:
    tx_id = validate_hex(tx_id, "tx_id", (64,))
    if not isinstance(data, dict):
        raise ValueError("cancellation payload must be an object")
    sender = validate_hex(data.get("sender"), "sender", (40,))
    signature = validate_hex(data.get("signature"), "signature", range(128, 289, 2))
    public_pem = data.get("public_key")
    if not isinstance(public_pem, str) or not 1 <= len(public_pem) <= 1024:
        raise ValueError("public key is invalid")
    try:
        public_key = serialization.load_pem_public_key(public_pem.encode())
    except (TypeError, ValueError) as exc:
        raise ValueError("public key is invalid") from exc
    if not isinstance(public_key, ec.EllipticCurvePublicKey) or not isinstance(
        public_key.curve, ec.SECP256K1
    ):
        raise ValueError("public key must use secp256k1")
    compressed = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint,
    )
    if hashlib.sha256(compressed).hexdigest()[:40] != sender:
        raise ValueError("public key does not belong to sender")
    try:
        public_key.verify(
            bytes.fromhex(signature),
            _cancellation_payload(tx_id, sender),
            ec.ECDSA(hashes.SHA256()),
        )
    except (InvalidSignature, TypeError, ValueError) as exc:
        raise ValueError("cancellation signature is invalid") from exc
    return tx_id, sender, public_pem


def broadcast_transaction(tx_data: dict, exclude_peer: str | None = None):
    tx_id = tx_data.get("tx_id")
    for peer in get_peers():
        if exclude_peer and peer.rstrip("/") == exclude_peer.rstrip("/"):
            continue
        try:
            response = requests.post(
                peer + "/p2p/transaction",
                json={"transaction": tx_data, "origin": ADVERTISED_URL},
                timeout=3,
            )
            if response.ok and tx_id:
                relay.mark_broadcast(tx_id)
        except Exception as e:
            print("broadcast tx →", peer, "failed:", e)


def broadcast_cancellation(tx_id: str, data: dict, exclude_peer: str | None = None):
    payload = {**data, "origin": ADVERTISED_URL}
    for peer in get_peers():
        if exclude_peer and peer.rstrip("/") == exclude_peer.rstrip("/"):
            continue
        try:
            requests.post(
                peer + f"/p2p/transaction/{tx_id}/cancel", json=payload, timeout=3
            )
        except Exception as exc:
            print("broadcast cancellation ->", peer, "failed:", exc)


def broadcast_inventory(tx_ids: list[str]):
    if not tx_ids:
        return
    payload = {"tx_ids": tx_ids[:INVENTORY_BATCH_SIZE], "origin": ADVERTISED_URL}
    for peer in get_peers():
        try:
            requests.post(peer + "/p2p/inventory", json=payload, timeout=3)
        except Exception as e:
            print("broadcast inventory →", peer, "failed:", e)


def broadcast_block(block, exclude_peer: str | None = None):
    data = block_to_dict(block)
    data["origin"] = ADVERTISED_URL
    for peer in get_peers():
        if exclude_peer and peer.rstrip("/") == exclude_peer.rstrip("/"):
            continue
        try:
            requests.post(peer + "/receive_block", json=data, timeout=3)
        except Exception as e:
            print("broadcast block →", peer, "failed:", e)


# ---------------------------------------------------------------------------
# Auto-discovery
# ---------------------------------------------------------------------------

def _get_local_ips() -> list[str]:
    """Return the machine's own LAN IP addresses (plus loopback)."""
    ips = {"127.0.0.1"}
    try:
        hostname = socket.gethostname()
        ips.update(socket.gethostbyname_ex(hostname)[2])
    except Exception:
        pass
    return list(ips)


def discover_nodes(extra_hosts: list[str] | None = None) -> list[str]:
    """Probe every combination of known local IPs + DISCOVER_PORTS.
    Returns URLs of responsive Helix nodes (excluding ourselves)."""

    hosts = _get_local_ips()
    if extra_hosts:
        hosts = list(set(hosts + extra_hosts))

    found = []
    my_port = PORT  # resolved after app init

    def probe(host, port):
        if host in ("127.0.0.1", "localhost") and port == my_port:
            return          # skip self
        url = f"http://{host}:{port}"
        try:
            r = requests.get(url + "/chain", timeout=1.5)
            if r.status_code == 200 and "chain" in r.json():
                found.append(url)
        except Exception:
            pass

    threads = [
        threading.Thread(target=probe, args=(h, p), daemon=True)
        for h in hosts
        for p in DISCOVER_PORTS
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=2)

    return found

# ---------------------------------------------------------------------------
# Chain sync  (longest-chain rule)
# ---------------------------------------------------------------------------

def _node_info() -> dict:
    node = get_node()
    return {
        "id": node["id"],
        "version": str(_CONFIG["node"].get("version", "0.2.0")),
        "protocol": int(_CONFIG["node"].get("protocol", 1)),
        "network": str(_CONFIG["node"].get("network", "mainnet")),
        "height": len(blockchain.chain) - 1,
        "chain_work": blockchain.chain_work(),
        "next_difficulty": blockchain.expected_difficulty(len(blockchain.chain), blockchain.chain),
        "port": PORT,
        "capabilities": node.get("capabilities", []),
    }


def sync_from_peers():
    """Probe peers, select the compatible peer with the highest chain, then sync once."""
    local = _node_info()
    candidates = []
    for peer in get_peers():
        info = probe_peer(peer, timeout=3)
        if info and compatible(local, info) and (int(info.get("chain_work", 0)) > int(local["chain_work"]) or ("chain_work" not in info and int(info.get("height", -1)) > local["height"])):
            candidates.append(info)
    if not candidates:
        print("Sync: no compatible peer has a heavier chain")
        return
    best = max(candidates, key=lambda item: (int(item.get("chain_work", 0)), int(item.get("height", -1)), -float(item.get("latency_ms", 999999))))
    peer = best["url"]
    started = time.perf_counter()
    try:
        response = requests.get(peer + "/chain/full", timeout=8)
        response.raise_for_status()
        chain = [dict_to_block(block) for block in response.json().get("chain", [])]
        replaced = blockchain.replace_chain(chain)
        record_success(peer, (time.perf_counter() - started) * 1000, height=len(chain) - 1,
                       version=best.get("version"), protocol=best.get("protocol"), network=best.get("network"))
        print(f"Sync: source={peer}, replaced={replaced}, new length={len(blockchain.chain)}")
    except (requests.RequestException, ValueError, TypeError, KeyError) as exc:
        record_failure(peer)
        print("sync download →", peer, "failed:", exc)


# ---------------------------------------------------------------------------
# Chain audit  (block-level hash verification against peers)
# ---------------------------------------------------------------------------

def audit_chain_with_peers() -> dict:
    """Compare our chain against every peer block-by-block.

    Steps per peer:
      1. Fetch their /chain/hashes  (cheap — just index+hash pairs).
      2. Find indexes we are missing → request each via /block/{index}.
         Re-calculate the hash from received data; only accept if it matches.
      3. Find indexes where hashes differ → flag for the UI; we do NOT
         silently overwrite — a human (or longest-chain sync) decides.
      4. Locally run verify_chain_integrity() on our own chain.

    Returns a summary dict consumed by /nodes/audit.
    """

    peers        = get_peers()
    local_audit  = blockchain.verify_chain_integrity()
    local_ok     = all(r["ok"] for r in local_audit)
    fetched      = []   # blocks we successfully pulled and verified
    conflicts    = []   # {index, our_hash, peer_hash, peer}
    unreachable  = []

    for peer in peers:
        # --- Step 1: get peer's hash list ---
        try:
            r            = requests.get(peer + "/chain/hashes", timeout=4)
            peer_hashes  = r.json().get("hashes", [])
        except Exception as e:
            unreachable.append({"peer": peer, "error": str(e)})
            continue

        # --- Step 2: missing blocks ---
        missing = blockchain.get_missing_indexes(peer_hashes)
        for idx in missing:
            try:
                rb   = requests.get(peer + f"/block/{idx}", timeout=4)
                bdat = rb.json().get("block")
                if bdat is None:
                    continue

                candidate = dict_to_block(bdat)

                # Re-calculate hash from contents; reject if it doesn't match
                recalculated = candidate.calculate_hash()
                if recalculated != candidate.hash:
                    print(
                        f"Audit: block {idx} from {peer} — "
                        f"hash mismatch (stored {candidate.hash[:12]}… "
                        f"vs recalculated {recalculated[:12]}…) — REJECTED"
                    )
                    conflicts.append({
                        "index":       idx,
                        "our_hash":    None,
                        "peer_hash":   candidate.hash,
                        "recalculated": recalculated,
                        "peer":        peer,
                        "reason":      "recalculated hash does not match peer's stored hash",
                    })
                    continue

                fetched.append({"index": idx, "hash": candidate.hash, "peer": peer})

            except Exception as e:
                print(f"Audit: could not fetch block {idx} from {peer}: {e}")

        # --- Step 3: differing hashes ---
        for idx in blockchain.get_differing_indexes(peer_hashes):
            our_hash  = blockchain.chain[idx].hash
            peer_hash = next(
                (h["hash"] for h in peer_hashes if h["index"] == idx), None
            )
            print(
                f"Audit: block {idx} hash differs — "
                f"ours={our_hash[:12]}… peer={str(peer_hash)[:12]}… ({peer})"
            )
            conflicts.append({
                "index":    idx,
                "our_hash": our_hash,
                "peer_hash": peer_hash,
                "peer":     peer,
                "reason":   "hash differs from peer — possible fork or corruption",
            })

    return {
        "local_integrity": {
            "ok":     local_ok,
            "blocks": local_audit,
        },
        "peers_checked": len(peers),
        "unreachable":   unreachable,
        "fetched_blocks": fetched,
        "conflicts":     conflicts,
    }

# ---------------------------------------------------------------------------
# Background worker  (auto-discover → register → sync → audit)
# ---------------------------------------------------------------------------

_last_audit: dict = {}       # cached result exposed via /nodes/audit
_worker_running = False


def _background_worker():
    """Runs every BACKGROUND_INTERVAL seconds.
    1. Discover new nodes on the local network and register any found.
    2. Pull the longest chain from all known peers.
    3. Run the block-level audit and cache the result.
    """
    global _last_audit

    while True:
        time.sleep(BACKGROUND_INTERVAL)
        print("Background worker: starting cycle")

        # 1. Internet bootstrap discovery, then local discovery
        try:
            public_url = str(_CONFIG["network"].get("public_url", "")).strip().rstrip("/") or None
            bootstrap_found = discover_from_bootstrap(
                list(_CONFIG["network"].get("bootstrap_nodes", [])), self_url=public_url
            )
            for url in bootstrap_found:
                print("Background worker: bootstrap peer", url)
        except Exception as e:
            print("Background worker: bootstrap error:", e)

        try:
            found = discover_nodes()
            for url in found:
                if url not in get_peers():
                    add_peer(url, PORT)
                    print("Background worker: registered new peer", url)
        except Exception as e:
            print("Background worker: discovery error:", e)

        # 1b. Peer gossip: learn peers-of-peers from every known peer so a peer
        # added on one node propagates to the whole network within a few cycles.
        try:
            public_url = str(_CONFIG["network"].get("public_url", "")).strip().rstrip("/") or None
            gossiped = discover_from_bootstrap(get_peers(), self_url=public_url)
            for url in gossiped:
                print("Background worker: gossiped peer", url)
        except Exception as e:
            print("Background worker: peer gossip error:", e)

        # 1c. Pool gossip: exchange known mining-pool URLs with every peer.
        try:
            for peer in get_peers():
                try:
                    response = requests.get(peer + "/pools", timeout=3)
                    add_pools(response.json().get("pools", []))
                except (requests.RequestException, ValueError, TypeError):
                    continue
        except Exception as e:
            print("Background worker: pool gossip error:", e)

        # 2. Sync longest chain
        try:
            sync_from_peers()
        except Exception as e:
            print("Background worker: sync error:", e)

        # 3. Mempool expiry, inventory exchange, and controlled rebroadcast
        try:
            blockchain.prune_expired_pending(TX_TTL_SECONDS)
            blockchain.prune_cancelled_transactions(TX_TTL_SECONDS * 2)
            blockchain.prune_orphans()
            active_ids = blockchain.pending_ids()
            relay.expire(active_ids)
            broadcast_inventory(sorted(active_ids))
            for tx in list(blockchain.pending_transactions):
                if tx.tx_id and relay.should_rebroadcast(tx.tx_id):
                    broadcast_transaction(transaction_to_relay_dict(tx))
        except Exception as e:
            print("Background worker: mempool error:", e)

        # 4. Audit
        try:
            _last_audit = audit_chain_with_peers()
            ok = _last_audit["local_integrity"]["ok"]
            conflicts = len(_last_audit["conflicts"])
            print(f"Background worker: audit done — local_ok={ok}, conflicts={conflicts}")
        except Exception as e:
            print("Background worker: audit error:", e)


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _worker_running
    # Initial sync before we start serving
    threading.Thread(target=sync_from_peers, daemon=True).start()
    # Kick off background worker
    if not _worker_running:
        _worker_running = True
        threading.Thread(target=_background_worker, daemon=True).start()
    yield


app = FastAPI(lifespan=lifespan)
security = SecurityManager(_CONFIG["security"])
app.add_middleware(SecurityMiddleware, manager=security)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(_CONFIG["security"].get("cors_allowed_origins", ["http://localhost", "http://127.0.0.1"])),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Helix-API-Key"],
)

_consensus = _CONFIG["blockchain"]
blockchain = Blockchain(_consensus)
PORT = int(os.getenv("NODE_PORT", str(_CONFIG["node"]["port"])))
PUBLIC_URL = str(_CONFIG["network"].get("public_url", "")).strip().rstrip("/")
ADVERTISED_URL = PUBLIC_URL or f"http://127.0.0.1:{PORT}"
TX_TTL_SECONDS = int(_CONFIG["mempool"].get("transaction_ttl_seconds", 3600))
REBROADCAST_INTERVAL = int(_CONFIG["mempool"].get("rebroadcast_interval", 60))
INVENTORY_BATCH_SIZE = int(_CONFIG["mempool"].get("inventory_batch_size", 500))
blockchain.max_pending_transactions = int(_CONFIG["mempool"].get("max_pending_transactions", 5000))
relay = MempoolRelay(TX_TTL_SECONDS, REBROADCAST_INTERVAL)
for _pending_tx in blockchain.pending_transactions:
    if _pending_tx.tx_id:
        relay.mark_seen(_pending_tx.tx_id, getattr(_pending_tx, "received_at", None))

_mining_jobs: dict[str, dict] = {}
_mining_jobs_lock = threading.Lock()
_active_mining_job: str | None = None


def _run_mining_job(job_id: str, address: str) -> None:
    """Mine outside the request lifecycle so proxies cannot time the request out."""
    global _active_mining_job
    try:
        block = blockchain.mine_pending_transactions(address)
        result = {
            "status": "completed",
            "message": "Block mined",
            "block": block.index,
            "hash": block.hash,
            "reward": block.transactions[-1].amount,
        }
        broadcast_block(block)
    except (ValueError, RuntimeError) as exc:
        result = {"status": "failed", "message": str(exc)}
    except Exception:
        # Do not expose unexpected server details through the public status API.
        result = {"status": "failed", "message": "Mining failed safely"}
    with _mining_jobs_lock:
        result["updated_at"] = time.time()
        _mining_jobs[job_id].update(result)
        if _active_mining_job == job_id:
            _active_mining_job = None


# ===========================================================================
# Routes
# ===========================================================================

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(os.path.join(PROJECT_ROOT, "web", "index.html"))


@app.get("/app.js", include_in_schema=False)
def web_application_script():
    return FileResponse(
        os.path.join(PROJECT_ROOT, "web", "app.js"),
        media_type="application/javascript",
    )


@app.get("/qrcode.js", include_in_schema=False)
def web_qrcode_library():
    return FileResponse(
        os.path.join(PROJECT_ROOT, "web", "qrcode.js"),
        media_type="application/javascript",
    )


@app.get("/pwa.js", include_in_schema=False)
def web_pwa_script():
    return FileResponse(
        os.path.join(PROJECT_ROOT, "web", "pwa.js"),
        media_type="application/javascript",
    )


@app.get("/jsqr.js", include_in_schema=False)
def web_jsqr_library():
    return FileResponse(
        os.path.join(PROJECT_ROOT, "web", "jsqr.js"),
        media_type="application/javascript",
    )


@app.get("/manifest.webmanifest", include_in_schema=False)
def web_manifest():
    return FileResponse(
        os.path.join(PROJECT_ROOT, "web", "manifest.webmanifest"),
        media_type="application/manifest+json",
    )


@app.get("/sw.js", include_in_schema=False)
def web_service_worker():
    return FileResponse(
        os.path.join(PROJECT_ROOT, "web", "sw.js"),
        media_type="application/javascript",
    )


@app.get("/icons/{filename}", include_in_schema=False)
def web_icon(filename: str):
    allowed = {"icon-192.png", "icon-512.png", "icon-maskable-512.png"}
    if filename not in allowed:
        raise HTTPException(status_code=404, detail="Icon not found")
    return FileResponse(
        os.path.join(PROJECT_ROOT, "web", "icons", filename),
        media_type="image/png",
    )


@app.get("/downloads/{filename}", include_in_schema=False)
def web_download(filename: str):
    allowed = {
        "helix-miner.zip": "helix-miner.zip",
        "helix-node.zip": "helix-node.zip",
    }
    safe_name = allowed.get(filename)
    if safe_name is None:
        raise HTTPException(status_code=404, detail="Download not found")
    path = os.path.join(PROJECT_ROOT, "web", "downloads", safe_name)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Download not found")
    return FileResponse(path, media_type="application/zip", filename=safe_name)


# ---------------------------------------------------------------------------
# Chain endpoints
# ---------------------------------------------------------------------------

@app.get("/chain")
def get_chain():
    """Lightweight summary — used by discovery probe."""
    return {
        "length": len(blockchain.chain),
        "chain": [
            {
                "index":         b.index,
                "hash":          b.hash,
                "previous_hash": b.previous_hash,
                "transactions":  [tx.data() for tx in b.transactions],
            }
            for b in blockchain.chain
        ],
    }


@app.get("/chain/full")
def get_chain_full():
    """Full chain with all tx fields — used for peer sync."""
    return {
        "length": len(blockchain.chain),
        "chain":  [block_to_dict(b) for b in blockchain.chain],
    }


@app.get("/chain/hashes")
def get_chain_hashes():
    """Minimal index+hash list — used by audit to compare chains cheaply."""
    return {
        "length": len(blockchain.chain),
        "hashes": [
            {"index": b.index, "hash": b.hash}
            for b in blockchain.chain
        ],
    }


@app.get("/block/{index}")
def get_block(index: int):
    """Return a single block by index — used when a peer needs to fill a gap."""
    if index < 0 or index >= len(blockchain.chain):
        return {"message": f"Block {index} not found"}
    block = blockchain.chain[index]
    # Always include the recalculated hash so the requester can verify
    data = block_to_dict(block)
    data["recalculated_hash"] = block.calculate_hash()
    return {"block": data}


# ---------------------------------------------------------------------------
# Balance & history
# ---------------------------------------------------------------------------

@app.get("/balance/{address}")
def balance(address: str):
    try:
        address = validate_hex(address, "address", (40,))
    except ValueError as exc:
        return {"error": str(exc)}
    return {"address": address, "balance": blockchain.get_balance(address)}


@app.get("/health")
def health():
    return {"status": "ok", "height": len(blockchain.chain) - 1, "version": _CONFIG["node"]["version"], "network": _CONFIG["node"]["network"]}


@app.get("/nfts")
def list_nfts(limit: int = 200, offset: int = 0):
    items = blockchain.get_nfts()
    limit = max(1, min(500, int(limit)))
    offset = max(0, int(offset))
    return {"count": len(items), "total": len(items), "nfts": items[offset:offset + limit]}


@app.get("/nft/{nft_id}")
def get_nft(nft_id: str):
    try:
        nft_id = validate_hex(nft_id, "nft id", (40,))
    except ValueError as exc:
        return {"error": str(exc), "nft": None}
    nft = blockchain.get_nft(nft_id)
    if nft is None:
        return {"nft": None}
    history = [
        {"block": block.index, "timestamp": block.timestamp,
         "from": tx.sender, "to": tx.receiver, "type": tx.tx_type, "tx_id": tx.tx_id}
        for block, tx in blockchain.get_nft_history(nft_id)
    ]
    return {"nft": nft, "history": history}


@app.get("/nfts/owner/{address}")
def nfts_by_owner(address: str):
    try:
        address = validate_hex(address, "address", (40,))
    except ValueError as exc:
        return {"error": str(exc), "nfts": []}
    return {"nfts": blockchain.get_nfts_by_owner(address)}


@app.get("/stats")
def stats():
    return {
        "height": len(blockchain.chain) - 1,
        "chain_work": blockchain.chain_work(),
        "next_difficulty": blockchain.expected_difficulty(len(blockchain.chain), blockchain.chain),
        "next_target": f"{blockchain.expected_target(len(blockchain.chain), blockchain.chain):064x}",
        "fine_difficulty_active": len(blockchain.chain) >= blockchain.fine_difficulty_activation_height,
        "difficulty": blockchain.target_to_difficulty(
            blockchain.expected_target(len(blockchain.chain), blockchain.chain)
        ),
        "base_difficulty": blockchain.difficulty,
        "chain_work": blockchain.chain_work(),
        "orphan_blocks": len(blockchain.orphan_blocks),
        "block_reward": blockchain.reward_for_height(len(blockchain.chain)),
        "native_dad_address": blockchain.native_dad_address,
        "native_dad_activation_height": blockchain.native_dad_activation_height,
        "native_dad_active": blockchain.native_dad_for_height(len(blockchain.chain) - 1) is not None,
        "native_dad_can_mint": False,
        "total_supply": blockchain.get_total_supply(),
        "max_supply": blockchain.max_supply,
        "pending_transactions": len(blockchain.pending_transactions),
        "target_block_time_seconds": blockchain.target_block_time_for_height(len(blockchain.chain)),
        "token_swap_activation_height": blockchain.token_swap_activation_height,
        "token_swap_active": len(blockchain.chain) >= blockchain.token_swap_activation_height,
    }


@app.get("/network/history")
def network_history(limit: int = 60):
    """Recent per-block difficulty and timestamp, for the network chart.

    Read-only: derives each block's difficulty from the proof-of-work target it
    had to meet (target_to_difficulty of expected_target). Does not touch
    consensus, validation, or mining.
    """
    chain = blockchain.chain
    limit = max(2, min(200, int(limit)))
    start = max(1, len(chain) - limit)   # skip the transactionless genesis block
    points = []
    for index in range(start, len(chain)):
        block = chain[index]
        target = blockchain.expected_target(index, chain)
        points.append({
            "height": index,
            "timestamp": block.timestamp,
            "difficulty": blockchain.target_to_difficulty(target),
            "tx_count": len(block.transactions),
        })
    return {
        "points": points,
        "target_block_time_seconds": blockchain.fine_target_block_time_seconds,
    }


@app.get("/history/{address}")
def get_history(address: str, include_pending: bool = True, offset: int = 0, limit: int = DEFAULT_PAGE_SIZE):
    try:
        address = validate_hex(address, "address", (40,))
    except ValueError as exc:
        return {"error": str(exc), "transactions": []}
    txs = []
    tip = len(blockchain.chain) - 1
    for block, tx in blockchain.get_address_history(address):
        txs.append({
            "tx_id": tx.tx_id,
            "sender": tx.sender,
            "receiver": tx.receiver,
            "amount": tx.amount,
            "tx_type": tx.tx_type,
            "mint_address": tx.mint_address,
            "dad_address": tx.dad_address,
            "symbol": tx.symbol,
            "block": block.index,
            "timestamp": block.timestamp,
            "direction": "out" if tx.sender == address else "in",
            "status": "confirmed",
            "confirmations": tip - block.index + 1,
        })
    if include_pending:
        for tx in blockchain.pending_transactions:
            if tx.sender == address or tx.receiver == address:
                txs.append({
                    "tx_id": tx.tx_id,
                    "sender": tx.sender,
                    "receiver": tx.receiver,
                    "amount": tx.amount,
                    "tx_type": tx.tx_type,
                    "mint_address": tx.mint_address,
                    "dad_address": tx.dad_address,
                    "symbol": tx.symbol,
                    "block": None,
                    "timestamp": tx.received_at,
                    "direction": "out" if tx.sender == address else "in",
                    "status": "pending",
                    "confirmations": 0,
                })
    txs.sort(key=lambda t: t["timestamp"], reverse=True)
    offset, limit = _page_bounds(offset, limit)
    total = len(txs)
    return {
        "address": address,
        "balance": blockchain.get_balance(address),
        "available_balance": blockchain.get_available_balance(address),
        "total": total,
        "offset": offset,
        "limit": limit,
        "transactions": txs[offset:offset + limit],
    }


# ---------------------------------------------------------------------------
# On-chain custom tokens
# ---------------------------------------------------------------------------

def _token_response(token: dict, holder: str | None = None) -> dict:
    result = dict(token)
    block, _ = blockchain.find_transaction(token["creation_tx_id"])
    result["creation_block"] = block.index if block is not None else None
    result["confirmations"] = (
        len(blockchain.chain) - block.index if block is not None else 0
    )
    result["confirmed"] = block is not None
    if holder is not None:
        result["balance"] = blockchain.get_token_balance(
            token["mint_address"], holder
        )
        result["token_account_address"] = Transaction.associated_token_address(
            holder, token["mint_address"]
        )
        result["token_account_exists"] = blockchain.token_account_exists(
            token["mint_address"], holder
        )
    return result


@app.get("/tokens")
def list_tokens(holder: str = ""):
    validated_holder = None
    if holder:
        try:
            validated_holder = validate_hex(holder, "holder", (40,))
        except ValueError as exc:
            return {"message": str(exc), "tokens": []}
    tokens = [
        _token_response(token, validated_holder)
        for token in blockchain.list_tokens(validated_holder)
    ]
    return {"count": len(tokens), "tokens": tokens}


@app.get("/token/{mint_address}")
def get_token(mint_address: str):
    try:
        mint_address = validate_hex(mint_address, "mint address", (40,))
    except ValueError as exc:
        return {"message": str(exc)}
    token = blockchain.get_token(mint_address)
    return (
        {"token": _token_response(token)}
        if token is not None
        else {"message": "Token mint not found on the confirmed chain"}
    )


@app.get("/token/{mint_address}/market/history")
def get_token_market_history(mint_address: str):
    try:
        mint_address = validate_hex(mint_address, "mint address", (40,))
    except ValueError as exc:
        return {"message": str(exc), "points": []}
    token = blockchain.get_token(mint_address)
    if token is None:
        return {
            "message": "Token mint not found on the confirmed chain",
            "points": [],
        }
    return {
        "mint_address": mint_address,
        "symbol": token["symbol"],
        "decimals": token["decimals"],
        "points": blockchain.get_token_market_history(mint_address),
    }


@app.get("/dad/{dad_address}/tokens")
def get_tokens_by_dad_address(dad_address: str):
    try:
        dad_address = validate_hex(dad_address, "DAD address", (40,))
    except ValueError as exc:
        return {"message": str(exc), "tokens": []}
    tokens = [
        _token_response(token)
        for token in blockchain.get_tokens_by_dad_address(dad_address)
    ]
    return {"dad_address": dad_address, "count": len(tokens), "tokens": tokens}


@app.get("/token/{mint_address}/balance/{address}")
def get_token_balance(mint_address: str, address: str):
    try:
        mint_address = validate_hex(mint_address, "mint address", (40,))
        address = validate_hex(address, "address", (40,))
    except ValueError as exc:
        return {"message": str(exc)}
    token = blockchain.get_token(mint_address)
    if token is None:
        return {"message": "Token mint not found on the confirmed chain"}
    return {
        "mint_address": mint_address,
        "address": address,
        "token_account_address": Transaction.associated_token_address(address, mint_address),
        "token_account_exists": blockchain.token_account_exists(mint_address, address),
        "balance": blockchain.get_token_balance(mint_address, address),
        "decimals": token["decimals"],
        "symbol": token["symbol"],
    }


@app.get("/token/{mint_address}/history/{address}")
def get_token_history(mint_address: str, address: str):
    try:
        mint_address = validate_hex(mint_address, "mint address", (40,))
        address = validate_hex(address, "address", (40,))
    except ValueError as exc:
        return {"message": str(exc), "transactions": []}
    tip = len(blockchain.chain) - 1
    transactions = []
    for block, tx in reversed(blockchain.get_token_history(mint_address, address)):
        transactions.append({
            **tx.to_dict(),
            "block": block.index,
            "timestamp": block.timestamp,
            "confirmations": tip - block.index + 1,
            "status": "confirmed",
        })
    return {
        "mint_address": mint_address,
        "address": address,
        "transactions": transactions,
    }


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

@app.get("/pending")
def pending():
    return {
        "pending": [
            {**tx.to_dict(), "received_at": tx.received_at}
            for tx in blockchain.pending_transactions
        ]
    }


@app.get("/transactions/recent")
def recent_transactions(limit: int = 25, offset: int = 0):
    bounded_offset, bounded_limit = _page_bounds(offset, min(limit, 100))
    total = blockchain.confirmed_transaction_count()
    transactions = []
    for block, tx in blockchain.get_recent_transactions(bounded_limit, bounded_offset):
        transactions.append({
            **tx.to_dict(),
            "block": block.index,
            "block_hash": block.hash,
            "timestamp": block.timestamp,
            "confirmations": len(blockchain.chain) - block.index,
        })
    pages = max(1, (total + bounded_limit - 1) // bounded_limit)
    return {
        "count": len(transactions),
        "total": total,
        "offset": bounded_offset,
        "limit": bounded_limit,
        "page": bounded_offset // bounded_limit + 1,
        "pages": pages,
        "transactions": transactions,
    }


@app.get("/transaction/{tx_id}")
def get_transaction(tx_id: str):
    try:
        tx_id = validate_hex(tx_id, "tx_id", (64,))
    except ValueError as exc:
        return {"message": str(exc)}
    block, tx = blockchain.find_transaction(tx_id)
    if tx is not None:
        tx_data = tx.to_dict()
        tx_data["id"] = tx_data.pop("tx_id")
        return {
            "block": block.index,
            "block_hash": block.hash,
            "timestamp": block.timestamp,
            "status": "confirmed",
            "confirmations": len(blockchain.chain) - block.index,
            "transaction": tx_data,
        }

    tx = blockchain.get_pending_transaction(tx_id)
    if tx is not None:
        tx_data = tx.to_dict()
        tx_data["id"] = tx_data.pop("tx_id")
        return {
            "block": None,
            "block_hash": None,
            "timestamp": tx.received_at,
            "status": "pending",
            "confirmations": 0,
            "transaction": tx_data,
        }
    return {"message": "Transaction not found"}


@app.post("/transaction")
def transaction(data: dict):
    try:
        tx = _transaction_from_payload(data)
    except Exception as exc:
        return {"accepted": False, "message": f"Malformed transaction: {exc}"}

    if blockchain.get_pending_transaction(tx.tx_id) is not None:
        return {"accepted": True, "duplicate": True, "tx_id": tx.tx_id}
    if blockchain.find_transaction(tx.tx_id)[1] is not None:
        return {
            "accepted": False,
            "message": "Transaction is already confirmed",
            "tx_id": tx.tx_id,
        }
    rejection = blockchain.transaction_rejection_reason(tx)
    if rejection is not None:
        return {"accepted": False, "message": rejection, "tx_id": tx.tx_id}
    if len(blockchain.pending_transactions) >= blockchain.max_pending_transactions:
        return {
            "accepted": False,
            "message": "The transaction pool is full; try again later",
            "tx_id": tx.tx_id,
        }

    first_seen = relay.mark_seen(tx.tx_id, tx.received_at)
    if not first_seen and blockchain.get_pending_transaction(tx.tx_id):
        return {"accepted": True, "duplicate": True, "tx_id": tx.tx_id}

    if blockchain.add_transaction(tx):
        payload = transaction_to_relay_dict(tx)
        broadcast_transaction(payload)
        return {"accepted": True, "message": "Transaction added", "tx_id": tx.tx_id}

    return {"accepted": False, "message": "Duplicate or invalid transaction", "tx_id": tx.tx_id}


@app.post("/transaction/{tx_id}/cancel")
def cancel_transaction(tx_id: str, data: dict):
    try:
        tx_id, sender, _ = _verify_cancellation(tx_id, data)
    except ValueError as exc:
        return {"cancelled": False, "message": str(exc)}
    if not blockchain.cancel_pending_transaction(tx_id, sender):
        return {
            "cancelled": False,
            "message": "Transaction is not pending or does not belong to this sender",
        }
    cancellation = {
        "sender": sender,
        "signature": data["signature"],
        "public_key": data["public_key"],
    }
    broadcast_cancellation(tx_id, cancellation)
    return {"cancelled": True, "message": "Pending transaction cancelled", "tx_id": tx_id}


@app.get("/mempool/inventory")
def mempool_inventory():
    ids = sorted(blockchain.pending_ids())[:INVENTORY_BATCH_SIZE]
    return {"count": len(ids), "tx_ids": ids}


@app.get("/mempool/transaction/{tx_id}")
def mempool_transaction(tx_id: str):
    try:
        tx_id = validate_hex(tx_id, "tx_id", (64,))
    except ValueError:
        return {"transaction": None}
    tx = blockchain.get_pending_transaction(tx_id)
    if tx is None:
        return {"transaction": None}
    return {"transaction": transaction_to_relay_dict(tx)}


@app.get("/mempool/stats")
def mempool_stats():
    return {
        "pending": len(blockchain.pending_transactions),
        "max_pending": blockchain.max_pending_transactions,
        "relay": relay.stats(),
    }


@app.post("/p2p/transaction")
def receive_transaction(data: dict):
    origin = normalize_peer(str(data.get("origin", ""))) or ""
    if origin and not has_peer(origin):
        origin = ""
    payload = data.get("transaction", data)
    try:
        tx = _transaction_from_payload(payload)
    except Exception as exc:
        return {"accepted": False, "message": f"Malformed transaction: {exc}"}

    first_seen = relay.mark_seen(tx.tx_id, tx.received_at)
    if not first_seen:
        return {"accepted": True, "duplicate": True, "tx_id": tx.tx_id}
    if not blockchain.add_transaction(tx):
        return {"accepted": False, "message": "Invalid transaction", "tx_id": tx.tx_id}

    broadcast_transaction(transaction_to_relay_dict(tx), exclude_peer=origin or None)
    return {"accepted": True, "relayed": True, "tx_id": tx.tx_id}


@app.post("/p2p/transaction/{tx_id}/cancel")
def receive_cancellation(tx_id: str, data: dict):
    origin = normalize_peer(str(data.get("origin", ""))) or ""
    if origin and not has_peer(origin):
        origin = ""
    try:
        tx_id, sender, _ = _verify_cancellation(tx_id, data)
    except ValueError as exc:
        return {"cancelled": False, "message": str(exc)}
    if not blockchain.cancel_pending_transaction(
        tx_id, sender, allow_missing=True
    ):
        return {"cancelled": False, "message": "Cancellation rejected"}
    cancellation = {
        "sender": sender,
        "signature": data["signature"],
        "public_key": data["public_key"],
    }
    broadcast_cancellation(tx_id, cancellation, exclude_peer=origin or None)
    return {"cancelled": True, "relayed": True, "tx_id": tx_id}


@app.post("/p2p/inventory")
def receive_inventory(data: dict):
    origin = normalize_peer(str(data.get("origin", ""))) or ""
    if origin and not has_peer(origin):
        origin = ""
    tx_ids = data.get("tx_ids", [])
    if not isinstance(tx_ids, list):
        return {"requested": 0, "message": "tx_ids must be a list"}
    valid_ids = []
    for candidate in tx_ids[:INVENTORY_BATCH_SIZE]:
        try:
            valid_ids.append(validate_hex(candidate, "tx_id", (64,)))
        except ValueError:
            continue
    missing = [
        tx_id for tx_id in valid_ids
        if tx_id not in blockchain.pending_ids()
        and blockchain.find_transaction(tx_id)[1] is None
    ]
    imported = 0
    if origin:
        for tx_id in missing:
            try:
                response = requests.get(origin + f"/mempool/transaction/{tx_id}", timeout=3)
                payload = response.json().get("transaction")
                if payload and receive_transaction({"transaction": payload, "origin": origin}).get("accepted"):
                    imported += 1
            except Exception:
                continue
    return {"requested": len(missing), "imported": imported}


# ---------------------------------------------------------------------------
# Mining
# ---------------------------------------------------------------------------

@app.get("/mining/info")
def external_mining_info():
    return {
        "external_mining": True,
        "algorithm": "sha256",
        "template_version": 1,
        "height": len(blockchain.chain) - 1,
        "next_difficulty": blockchain.expected_difficulty(len(blockchain.chain), blockchain.chain),
        "target_block_time_seconds": blockchain.target_block_time_for_height(len(blockchain.chain)),
    }


@app.get("/mining/work")
def external_mining_work(address: str):
    """Return a current block template for an independent miner."""
    try:
        address = validate_hex(address, "address", (40,))
        block, difficulty, target = blockchain.create_mining_candidate(address)
    except ValueError as exc:
        return {"message": str(exc)}
    return {
        "block": block_to_dict(block),
        "difficulty": difficulty,
        "target_prefix": "0" * difficulty,
        # Exact numeric target the proof must satisfy: int(hash, 16) <= target.
        # Miners should compare against this; difficulty is kept for display.
        "target": f"{target:064x}",
        "reward": block.transactions[-1].amount,
        "network": _CONFIG["node"]["network"],
    }


@app.post("/mining/submit")
def external_mining_submit(data: dict):
    """Validate, accept, and relay a proof-of-work block solved by a miner."""
    payload = data.get("block", data) if isinstance(data, dict) else data
    try:
        block = dict_to_block(payload)
    except (KeyError, TypeError, ValueError) as exc:
        return {"accepted": False, "message": f"Malformed block: {exc}"}
    accepted, reason = blockchain.receive_block_detailed(block)
    if not accepted:
        stale = block.index <= len(blockchain.chain) - 1
        return {
            "accepted": False,
            "stale": stale,
            "message": reason or ("another miner won this height" if stale else "block rejected"),
        }
    relay.expire(blockchain.pending_ids())
    broadcast_block(block)
    return {
        "accepted": True,
        "message": "Block accepted",
        "block": block.index,
        "hash": block.hash,
        "reward": block.transactions[-1].amount,
        "consensus": blockchain.consensus_status(),
    }

@app.post("/mine")
def mine(address: str):
    try:
        address = validate_hex(address, "address", (40,))
        block = blockchain.mine_pending_transactions(address)
    except ValueError as exc:
        return {"message": str(exc)}
    except RuntimeError as exc:
        return {"message": f"Mining failed safely: {exc}"}
    if block is None:
        return {"message": "No transactions to mine"}
    broadcast_block(block)
    return {
        "message": "Block mined",
        "block": block.index,
        "hash": block.hash,
        "reward": block.transactions[-1].amount,
    }


@app.post("/mine/start")
def start_mining(address: str):
    """Start one mining job and return before a tunnel/proxy can time out."""
    global _active_mining_job
    try:
        address = validate_hex(address, "address", (40,))
    except ValueError as exc:
        return {"status": "failed", "message": str(exc)}

    now = time.time()
    with _mining_jobs_lock:
        # Keep job state bounded; completed results are only needed briefly by UI polling.
        expired = [
            key for key, value in _mining_jobs.items()
            if value.get("status") in {"completed", "failed"}
            and now - float(value.get("updated_at", now)) > 3600
        ]
        for key in expired:
            _mining_jobs.pop(key, None)

        if _active_mining_job:
            active = dict(_mining_jobs[_active_mining_job])
            active["message"] = "Mining is already in progress"
            return active

        job_id = secrets.token_hex(16)
        _active_mining_job = job_id
        _mining_jobs[job_id] = {
            "job_id": job_id,
            "status": "mining",
            "message": "Mining started",
            "updated_at": now,
        }

    threading.Thread(target=_run_mining_job, args=(job_id, address), daemon=True).start()
    return dict(_mining_jobs[job_id])


@app.get("/mine/status/{job_id}")
def mining_status(job_id: str):
    try:
        job_id = validate_hex(job_id, "mining job id", (32,))
    except ValueError as exc:
        return {"status": "failed", "message": str(exc)}
    with _mining_jobs_lock:
        job = _mining_jobs.get(job_id)
        if job is None:
            return {"status": "failed", "message": "Mining job was not found"}
        return dict(job)


# ---------------------------------------------------------------------------
# P2P node management
# ---------------------------------------------------------------------------

@app.post("/receive_block")
def receive_block(data: dict):
    origin = normalize_peer(str(data.get("origin", ""))) or ""
    if origin and not has_peer(origin):
        origin = ""
    try:
        block = dict_to_block(data)
    except (KeyError, TypeError, ValueError) as exc:
        return {"message": f"Malformed block: {exc}"}
    accepted = blockchain.receive_block(block)
    if accepted:
        relay.expire(blockchain.pending_ids())
        broadcast_block(block, exclude_peer=origin or None)
        return {"message": "Block accepted", "consensus": blockchain.consensus_status()}
    if block.hash in blockchain.orphan_blocks:
        threading.Thread(target=sync_from_peers, daemon=True).start()
        return {"message": "Block stored as orphan; synchronization requested"}
    return {"message": "Block rejected"}


@app.get("/consensus/status")
def consensus_status():
    return blockchain.consensus_status()


@app.get("/consensus/orphans")
def consensus_orphans():
    blockchain.prune_orphans()
    return {
        "count": len(blockchain.orphan_blocks),
        "orphans": [
            {
                "index": item["block"].index,
                "hash": item["block"].hash,
                "previous_hash": item["block"].previous_hash,
                "received_at": item["received_at"],
            }
            for item in blockchain.orphan_blocks.values()
        ],
    }


@app.get("/nodes/info")
def node_info():
    return _node_info()


@app.get("/nodes/peers")
def public_peers():
    return {"peers": get_peers()}


@app.get("/pools")
def list_pools():
    """Directory of known mining-pool URLs, gossiped across nodes."""
    return {"pools": get_pools()}


@app.post("/nodes/submit")
def submit_node(data: dict):
    """Queue a node URL for the operator to review (not auto-added or gossiped)."""
    if not isinstance(data, dict) or not isinstance(data.get("url"), str):
        return {"accepted": False, "message": "Malformed submission"}
    if len(data.get("url", "")) > 300 or len(str(data.get("note", ""))) > 280:
        return {"accepted": False, "message": "Submission is too long"}
    url = add_submission(data["url"], data.get("note", ""))
    if not url:
        return {"accepted": False, "message": "That does not look like a valid node URL."}
    return {"accepted": True, "message": "Thanks — your node was submitted for review."}


@app.get("/nodes/submissions")
def node_submissions():
    """Operator-only review queue of submitted nodes."""
    return {"submissions": get_submissions()}


@app.post("/pools/register")
def register_pool(data: dict):
    if not isinstance(data, dict) or not isinstance(data.get("url"), str):
        return {"message": "Malformed pool registration"}
    if len(data.get("url", "")) > 300:
        return {"message": "Pool URL is too long"}
    url = normalize_peer(data["url"])
    if not url:
        return {"message": "Invalid pool URL"}
    pools = add_pool(url)
    return {"message": "Pool listed", "pools": pools}


@app.post("/nodes/register")
def register_node(data: dict):
    if not isinstance(data, dict) or not isinstance(data.get("node"), str):
        return {"message": "Malformed registration"}
    if len(data.get("node", "")) > 300 or len(data.get("self_url", "")) > 300:
        return {"message": "Registration URL is too long"}
    node_url = normalize_peer(data["node"])
    if not node_url:
        return {"message": "Invalid node URL"}
    peers = add_peer(node_url, PORT)
    # Reciprocal registration is sent only to the normalized node itself.
    self_url = normalize_peer(str(data.get("self_url", "")))
    if self_url:
        try:
            requests.post(node_url + "/nodes/register", json={"node": self_url}, timeout=3)
        except Exception:
            pass
    return {"message": "Node added", "peers": peers}


@app.get("/nodes")
def list_nodes():
    return {"node": _node_info(), "peers": get_peer_records()}


@app.post("/sync")
def sync(data: dict):
    """Accept a chain only if it is longer and passes full consensus validation."""
    try:
        raw_chain = data["chain"]
        if not isinstance(raw_chain, list):
            raise ValueError("chain must be a list")
        if len(raw_chain) > len(blockchain.chain) + 10000:
            raise ValueError("chain payload exceeds synchronization limit")
        new_chain = [dict_to_block(b) for b in raw_chain]
    except (KeyError, TypeError, ValueError) as exc:
        return {"replaced": False, "message": f"Malformed chain: {exc}"}
    replaced = blockchain.replace_chain(new_chain)
    return {"replaced": replaced}


@app.post("/nodes/sync_now")
def sync_now():
    """Trigger an immediate pull-sync + audit from all known peers."""
    def _run():
        sync_from_peers()
        global _last_audit
        _last_audit = audit_chain_with_peers()
    threading.Thread(target=_run, daemon=True).start()
    return {"message": "Sync and audit started"}


@app.get("/nodes/discover")
def nodes_discover(extra: str = ""):
    """Scan local network ports for Helix nodes.
    Pass ?extra=192.168.1.x,192.168.1.y to probe additional hosts.
    Newly found nodes are automatically registered as peers.
    """
    extra_hosts = [h.strip() for h in extra.split(",") if h.strip()] if extra else []
    found       = discover_nodes(extra_hosts or None)

    newly_added = []
    for url in found:
        if url not in get_peers():
            add_peer(url, PORT)
            newly_added.append(url)

    return {
        "found":       found,
        "newly_added": newly_added,
        "total_peers": len(get_peers()),
    }


@app.get("/nodes/audit")
def nodes_audit():
    """Run a full block-level integrity check against all peers.
    Each missing block is fetched and its hash is re-calculated before
    it is accepted.  Conflicts are reported but not auto-resolved.
    """
    global _last_audit
    # Run synchronously so the response contains fresh results
    _last_audit = audit_chain_with_peers()
    return _last_audit


@app.get("/security/status")
def security_status():
    return security.status()


@app.get("/nodes/audit/cached")
def nodes_audit_cached():
    """Return the most recent audit result from the background worker
    without triggering a new run — fast, safe to poll."""
    return _last_audit if _last_audit else {"message": "No audit run yet"}
