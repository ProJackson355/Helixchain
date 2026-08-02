"""Helix mining pool coordinator.

Anyone can host a pool. The coordinator repeatedly asks a Helix node for a block
template addressed to the *pool's own wallet*, hands that template to connected
miners at a reduced "share" difficulty, and counts each miner's accepted shares.
When a miner's share also satisfies the full network difficulty the pool submits
the real block to the node, then pays every miner a slice of the block reward in
proportion to the shares (i.e. the hashrate) they contributed this round.

Bitcoin-style proportional split: payout_i = (reward - fee) * shares_i / total_shares.

Run it with run_pool.py. Configuration comes from environment variables:

  HELIX_POOL_SEED            12-word seed of the pool wallet (required for payouts)
  HELIX_POOL_ADDRESS         override the payout address (defaults to the seed's)
  HELIX_POOL_NODE            node URL(s) for templates/submits (default https://node.hlxchain.com)
  HELIX_POOL_SHARE_SUBTRACT  share difficulty = network difficulty - this (default 2)
  HELIX_POOL_MIN_SHARE_DIFFICULTY  floor for share difficulty (default 1)
  HELIX_POOL_FEE_PERCENT     operator fee kept from each block (default 1.0)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
from collections import Counter, defaultdict, deque
from contextlib import asynccontextmanager

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from node.transaction import Transaction
from wallet.wallet import Wallet

ADDRESS_RE = re.compile(r"^[0-9a-f]{40}$")
REQUEST_TIMEOUT = 5
MAX_HASH = 16 ** 64 - 1


def difficulty_to_target(difficulty: int) -> int:
    return 16 ** (64 - max(0, min(64, int(difficulty)))) - 1


def leading_zero_difficulty(target: int) -> int:
    hexstr = f"{int(target):064x}"
    return len(hexstr) - len(hexstr.lstrip("0"))


def _env_nodes() -> list[str]:
    raw = os.getenv("HELIX_POOL_NODE", "https://node.hlxchain.com")
    return [item.strip().rstrip("/") for item in raw.split(",") if item.strip()]


def block_hash(block: dict, nonce: int | None = None) -> str:
    """The exact SHA-256 block hash used by Helix consensus (see node/blockchain.py)."""
    payload = {
        "index": block["index"],
        "transactions": block["transactions"],
        "previous_hash": block["previous_hash"],
        "timestamp": block["timestamp"],
        "nonce": block["nonce"] if nonce is None else nonce,
    }
    if block.get("transaction_root") is not None:
        payload["transaction_root"] = block["transaction_root"]
    if block.get("state_root") is not None:
        payload["state_root"] = block["state_root"]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def meets_difficulty(digest: str, difficulty: int) -> bool:
    return digest.startswith("0" * int(difficulty))


def compute_payouts(
    reward: int, fee_percent: float, shares: dict[str, int], transaction_fee: int = 0
) -> tuple[dict[str, int], int, int]:
    """Proportional split. Returns (payouts, fee, remainder-kept-by-pool).

    Each miner earns (reward - fee) * shares_i / total_shares, floored to whole
    HLX. Any rounding remainder and the fee stay in the pool wallet.
    """
    total = sum(shares.values())
    reward = int(reward)
    if total <= 0 or reward <= 0:
        return {}, 0, reward if reward > 0 else 0
    fee = int(reward * max(0.0, fee_percent) / 100)
    # Each payout is itself an on-chain transaction. Reserve its network fee so
    # the pool never promises more than its confirmed block income can spend.
    network_cost = max(0, int(transaction_fee)) * len(shares)
    distributable = max(0, reward - fee - network_cost)
    payouts: dict[str, int] = {}
    for address, count in sorted(shares.items()):
        amount = distributable * count // total
        if amount > 0:
            payouts[address] = amount
    kept = reward - sum(payouts.values())
    return payouts, fee, kept


class Pool:
    def __init__(self):
        self.lock = threading.RLock()
        seed = os.getenv("HELIX_POOL_SEED", "").strip()
        seed_format = os.getenv("HELIX_POOL_SEED_FORMAT", "bip39").strip().lower()
        self.wallet = (
            Wallet.from_web_seed_phrase(seed)
            if seed and seed_format == "web"
            else Wallet.from_seed_phrase(seed) if seed
            else None
        )
        self.address = (os.getenv("HELIX_POOL_ADDRESS", "").strip().lower()
                        or (self.wallet.address if self.wallet else ""))
        self.nodes = _env_nodes()
        self.share_subtract = int(os.getenv("HELIX_POOL_SHARE_SUBTRACT", "2"))
        self.min_share_difficulty = max(1, int(os.getenv("HELIX_POOL_MIN_SHARE_DIFFICULTY", "1")))
        self.fee_percent = float(os.getenv("HELIX_POOL_FEE_PERCENT", "1.0"))
        self.pplns_window = max(100, int(os.getenv("HELIX_POOL_PPLNS_WINDOW", "10000")))
        self.share_seconds = max(2.0, float(os.getenv("HELIX_POOL_SHARE_SECONDS", "15")))
        self.job: dict | None = None
        self.job_fetched = 0.0
        self.seen: set[tuple[str, int]] = set()
        self.round_shares: dict[str, int] = defaultdict(int)
        self.share_window = deque(maxlen=self.pplns_window)
        self.miner_share_targets: dict[str, int] = {}
        self.round_started = time.time()
        self.miner_last_share: dict[str, float] = {}
        self.blocks_found = 0
        self.total_paid = 0
        self.payouts: list[dict] = []

    # --- node I/O -----------------------------------------------------------
    def _node(self) -> str:
        return self.nodes[0] if self.nodes else "https://node.hlxchain.com"

    def refresh_job(self, force: bool = False) -> dict | None:
        with self.lock:
            fresh = self.job is not None and (time.time() - self.job_fetched) < 3
            if fresh and not force:
                return self.job
            address = self.address
        if not ADDRESS_RE.fullmatch(address or ""):
            return None
        try:
            response = requests.get(self._node() + "/mining/work", params={"address": address}, timeout=REQUEST_TIMEOUT)
            work = response.json()
        except (requests.RequestException, ValueError):
            return self.job
        if not response.ok or "block" not in work:
            return self.job
        block = work["block"]
        network_difficulty = int(work.get("difficulty", 0))
        # Prefer the node's exact numeric target; fall back to leading-zero difficulty.
        network_target = int(work["target"], 16) if work.get("target") else difficulty_to_target(network_difficulty)
        # A share is easier than the block by `share_subtract` hex levels (a larger
        # target), so miners submit frequent shares that prove their hashrate.
        share_target = min(MAX_HASH, network_target * (16 ** self.share_subtract))
        share_difficulty = max(self.min_share_difficulty, leading_zero_difficulty(share_target))
        with self.lock:
            new_round = (
                self.job is None
                or self.job["block"]["previous_hash"] != block["previous_hash"]
                or int(self.job["block"]["index"]) != int(block["index"])
            )
            if new_round:
                # A stable template per round keeps in-flight shares valid.
                job_id = hashlib.sha256(
                    f"{block['previous_hash']}:{block['index']}:{time.time()}".encode()
                ).hexdigest()[:16]
                self.job = {
                    "job_id": job_id,
                    "block": block,
                    "network_difficulty": network_difficulty,
                    "share_difficulty": share_difficulty,
                    "network_target": network_target,
                    "share_target": share_target,
                    "reward": int(work.get("miner_payment", work.get("reward", 0)) or 0),
                    "subsidy": int(work.get("reward", 0) or 0),
                    "transaction_fees": int(work.get("transaction_fees", 0) or 0),
                    "transaction_fee": int(work.get("transaction_fee", 1) or 1),
                    "height": int(block["index"]),
                }
                self.job_fetched = time.time()
            else:
                self.job["network_difficulty"] = network_difficulty
                self.job["share_difficulty"] = share_difficulty
                self.job["network_target"] = network_target
                self.job["share_target"] = share_target
                self.job_fetched = time.time()
            return self.job

    def _submit_block(self, solved: dict) -> bool:
        for node in self.nodes:
            try:
                response = requests.post(node + "/mining/submit", json={"block": solved}, timeout=REQUEST_TIMEOUT)
                if response.ok and response.json().get("accepted"):
                    return True
            except (requests.RequestException, ValueError):
                continue
        return False

    def _send_payout(self, receiver: str, amount: int, transaction_fee: int) -> None:
        if self.wallet is None or amount <= 0:
            return
        envelope = None
        for node in self.nodes:
            try:
                response = requests.get(
                    node + f"/transaction/envelope/{self.address}", timeout=REQUEST_TIMEOUT
                )
                if response.ok:
                    envelope = response.json()
                    break
            except (requests.RequestException, ValueError):
                continue
        if not isinstance(envelope, dict):
            return
        tx = Transaction(
            self.address, receiver, int(amount), fee=int(transaction_fee),
            chain_id=envelope["chain_id"], sequence=envelope["next_sequence"],
            valid_until_height=envelope["valid_until_height"],
        )
        tx.public_key = self.wallet.public_key
        tx.sign(self.wallet.private_key)
        payload = {
            "sender": tx.sender, "receiver": tx.receiver, "amount": tx.amount, "fee": tx.fee,
            "chain_id": tx.chain_id, "sequence": tx.sequence,
            "valid_until_height": tx.valid_until_height,
            "signature": tx.signature, "public_key": self.wallet.public_key_string(),
            "tx_id": tx.tx_id,
        }
        for node in self.nodes:
            try:
                if requests.post(node + "/transaction", json=payload, timeout=REQUEST_TIMEOUT).ok:
                    return
            except requests.RequestException:
                continue

    # --- share handling -----------------------------------------------------
    def share_target_for(self, address: str, job: dict) -> int:
        """Return the miner's vardiff target, bounded by real network work."""
        with self.lock:
            default_target = job.get("share_target")
            if default_target is None:
                default_target = difficulty_to_target(job.get("share_difficulty", 1))
            network_target = job.get("network_target")
            if network_target is None:
                network_target = difficulty_to_target(job.get("network_difficulty", 1))
            target = self.miner_share_targets.get(address, default_target)
            return max(network_target, min(MAX_HASH, int(target)))

    def submit_share(self, job_id: str, address: str, nonce: int) -> dict:
        address = (address or "").strip().lower()
        if ADDRESS_RE.fullmatch(address) is None:
            return {"accepted": False, "reason": "invalid miner address"}
        try:
            nonce = int(nonce)
        except (TypeError, ValueError):
            return {"accepted": False, "reason": "invalid nonce"}
        with self.lock:
            job = self.job
            if job is None or job_id != job["job_id"]:
                return {"accepted": False, "reason": "stale or unknown job", "job_id": job["job_id"] if job else None}
            if (job_id, nonce) in self.seen:
                return {"accepted": False, "reason": "duplicate share"}
            block = job["block"]
            share_difficulty = job["share_difficulty"]
            # Numeric targets (fall back to leading-zero difficulty if absent).
            share_target = self.share_target_for(address, job)
            if share_target is None:
                share_target = difficulty_to_target(job["share_difficulty"])
            network_target = job.get("network_target")
            if network_target is None:
                network_target = difficulty_to_target(job["network_difficulty"])
        digest = block_hash(block, nonce)
        if int(digest, 16) > share_target:
            return {"accepted": False, "reason": "hash is above the share target"}
        with self.lock:
            if self.job is None or self.job["job_id"] != job_id:
                return {"accepted": False, "reason": "stale job"}
            self.seen.add((job_id, nonce))
            self.round_shares[address] += 1
            share_work = max(1, MAX_HASH // (int(share_target) + 1))
            self.share_window.append((address, share_work))
            previous_share = self.miner_last_share.get(address)
            self.miner_last_share[address] = time.time()
            next_target = share_target
            if previous_share is not None:
                interval = max(0.001, time.time() - previous_share)
                if interval < self.share_seconds / 2:
                    next_target = max(network_target, share_target // 2)
                elif interval > self.share_seconds * 2:
                    next_target = min(MAX_HASH, share_target * 2)
                self.miner_share_targets[address] = next_target
        result = {
            "accepted": True,
            "share_difficulty": leading_zero_difficulty(next_target),
            "share_target": f"{next_target:064x}",
        }
        if int(digest, 16) <= network_target:
            solved = dict(block)
            solved["nonce"] = nonce
            solved["hash"] = digest
            if self._submit_block(solved):
                result["block"] = True
                self._settle_round(job, address)
            else:
                result["block"] = False
        return result

    def _settle_round(self, job: dict, finder: str) -> None:
        with self.lock:
            shares = dict(Counter({
                address: sum(work for owner, work in self.share_window if owner == address)
                for address, _work in self.share_window
            }))
            self.blocks_found += 1
        payouts, fee, kept = compute_payouts(
            job["reward"], self.fee_percent, shares, job.get("transaction_fee", 1)
        )
        for address, amount in payouts.items():
            self._send_payout(address, amount, job.get("transaction_fee", 1))
        with self.lock:
            self.payouts.insert(0, {
                "height": job["height"], "reward": job["reward"], "fee": fee,
                "kept": kept, "total_shares": sum(self.round_shares.values()),
                "pplns_work": sum(shares.values()),
                "recipients": len(payouts), "finder": finder, "at": time.time(),
                "breakdown": payouts,
            })
            self.payouts = self.payouts[:20]
            self.total_paid += sum(payouts.values())
            self.round_shares = defaultdict(int)
            self.round_started = time.time()
            self.seen = set()
        self.refresh_job(force=True)

    # --- reporting ----------------------------------------------------------
    def _hashrate(self, shares: int, elapsed: float, share_target: int) -> float:
        if elapsed <= 0 or share_target <= 0:
            return 0.0
        work_per_share = MAX_HASH // (int(share_target) + 1)  # expected hashes per share
        return shares * work_per_share / elapsed

    def stats(self) -> dict:
        with self.lock:
            job = self.job
            elapsed = max(1e-6, time.time() - self.round_started)
            share_difficulty = job["share_difficulty"] if job else self.min_share_difficulty
            share_target = job["share_target"] if job else difficulty_to_target(self.min_share_difficulty)
            total_shares = sum(self.round_shares.values())
            miners = [
                {
                    "address": address,
                    "shares": count,
                    "round_percent": round(count * 100 / total_shares, 2) if total_shares else 0.0,
                    "estimated_hashrate": round(self._hashrate(count, elapsed, share_target), 2),
                    "last_share": self.miner_last_share.get(address),
                }
                for address, count in sorted(self.round_shares.items(), key=lambda item: -item[1])
            ]
            return {
                "pool_address": self.address,
                "fee_percent": self.fee_percent,
                "scheme": "proportional",
                "share_difficulty": share_difficulty,
                "network_difficulty": job["network_difficulty"] if job else None,
                "height": job["height"] if job else None,
                "reward": job["reward"] if job else None,
                "round_shares": total_shares,
                "round_seconds": round(elapsed, 1),
                "pool_hashrate": round(self._hashrate(total_shares, elapsed, share_target), 2),
                "blocks_found": self.blocks_found,
                "total_paid": self.total_paid,
                "miners": miners,
                "recent_payouts": self.payouts,
                "payouts_enabled": self.wallet is not None,
            }


pool = Pool()
_worker_started = False


def _background_refresh():
    while True:
        try:
            pool.refresh_job()
        except Exception as exc:  # keep the loop alive
            print("pool refresh error:", exc)
        time.sleep(2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _worker_started
    if not _worker_started:
        _worker_started = True
        threading.Thread(target=_background_refresh, daemon=True).start()
    yield


app = FastAPI(lifespan=lifespan, title="Helix Mining Pool")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["Content-Type"],
)


@app.middleware("http")
async def _disable_caching(request, call_next):
    """Pool stats are live and change every round. Without this, Cloudflare (or
    the browser) can serve a stale snapshot -- e.g. old block counts or miners
    still listed after the pool is restarted. Force every response fresh."""
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response


@app.get("/pool/info")
def pool_info():
    job = pool.refresh_job()
    return {
        "pool_address": pool.address,
        "fee_percent": pool.fee_percent,
        "scheme": "PPLNS",
        "pplns_window": pool.pplns_window,
        "vardiff_target_seconds": pool.share_seconds,
        "payouts_enabled": pool.wallet is not None,
        "share_difficulty": job["share_difficulty"] if job else pool.min_share_difficulty,
        "network_difficulty": job["network_difficulty"] if job else None,
        "height": job["height"] if job else None,
        "reward": job["reward"] if job else None,
    }


@app.get("/pool/work")
def pool_work(address: str):
    address = (address or "").strip().lower()
    if ADDRESS_RE.fullmatch(address) is None:
        return {"message": "A 40-character reward address is required to receive work."}
    job = pool.refresh_job()
    if job is None:
        return {"message": "The pool has no block template yet; is its node reachable?"}
    share_target = pool.share_target_for(address, job)
    return {
        "job_id": job["job_id"],
        "block": job["block"],
        "share_difficulty": leading_zero_difficulty(share_target),
        "network_difficulty": job["network_difficulty"],
        "share_target": f"{share_target:064x}",
        "network_target": f"{job['network_target']:064x}",
        "height": job["height"],
        "reward": job["reward"],
    }


@app.post("/pool/submit")
def pool_submit(data: dict):
    if not isinstance(data, dict):
        return {"accepted": False, "reason": "malformed submission"}
    return pool.submit_share(
        str(data.get("job_id", "")),
        str(data.get("address", "")),
        data.get("nonce"),
    )


@app.get("/pool/stats")
def pool_stats():
    pool.refresh_job()
    return pool.stats()
