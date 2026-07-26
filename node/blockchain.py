import hashlib
import json
import math
import os
import re
import threading
import time
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

from cryptography.hazmat.primitives import serialization

from node.transaction import Transaction

PORT = os.getenv("NODE_PORT", "8000")
ADDRESS_RE = re.compile(r"^[0-9a-f]{40}$")
TOKEN_NONCE_RE = re.compile(r"^[0-9a-f]{32}$")
TOKEN_SYMBOL_RE = re.compile(r"^[A-Z][A-Z0-9]{1,11}$")
MAX_TOKEN_UNITS = 9_007_199_254_740_991
ZERO_ADDRESS = "0" * 40
MAX_HASH = 16 ** 64 - 1  # largest possible 256-bit SHA-256 digest value
# A child block's timestamp must not predate its parent's, but low-difficulty
# blocks are solved in a fraction of a second, so consecutive blocks routinely
# land in the same clock tick, and many miners stamp whole seconds. Allow a
# child to be up to this many seconds behind its parent so honest, fast, or
# integer-timestamp miners are not rejected. The block is still capped to the
# near future, so overall time can only trend forward.
TIMESTAMP_BACKWARD_TOLERANCE = 2.0
SWAP_FEE_NUMERATOR = 997
SWAP_FEE_DENOMINATOR = 1000


def _transaction_from_dict(data: dict) -> Transaction:
    tx = Transaction(
        data["sender"],
        data["receiver"],
        data["amount"],
        received_at=data.get("received_at"),
        tx_type=data.get("tx_type", "transfer"),
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
    tx.signature = data.get("signature")
    tx.tx_id = data.get("tx_id")
    pem = data.get("public_key")
    if pem:
        tx.public_key = serialization.load_pem_public_key(pem.encode())
    return tx


class Block:
    def __init__(
        self,
        index,
        transactions,
        previous_hash,
        timestamp=None,
        nonce=0,
        hash=None,
    ):
        self.index = int(index)
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.nonce = int(nonce)
        self.hash = hash or self.calculate_hash()

    def calculate_hash(self) -> str:
        block_data = {
            "index": self.index,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
        }
        return hashlib.sha256(
            json.dumps(block_data, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    def mine(self, difficulty: int) -> None:
        target = "0" * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()

    def mine_to_target(self, target: int) -> None:
        """Bitcoin-style search: find a nonce whose hash is <= a numeric target.

        This generalises leading-zero difficulty (which is just the special case
        target == 16**(64-difficulty) - 1) so difficulty can be tuned finely
        between whole hex levels instead of only in 16x jumps.
        """
        while int(self.hash, 16) > target:
            self.nonce += 1
            self.hash = self.calculate_hash()


class Blockchain:
    def __init__(self, consensus: dict | None = None, database_path: str | Path | None = None):
        consensus = consensus or {}

        def setting(name: str, environment: str, default):
            return os.getenv(environment, str(consensus.get(name, default)))

        self.chain = []
        self.pending_transactions = []
        self.cancelled_transactions: dict[str, dict] = {}
        self.database = Path(
            database_path
            or os.getenv("HELIX_DATABASE", f"database_{PORT}.json")
        )
        self.difficulty = int(setting("difficulty", "HELIX_DIFFICULTY", 3))
        self.min_difficulty = int(
            setting("min_difficulty", "HELIX_MIN_DIFFICULTY", self.difficulty)
        )
        self.max_difficulty = int(setting("max_difficulty", "HELIX_MAX_DIFFICULTY", 8))
        self.difficulty_reset_value = int(setting(
            "difficulty_reset_value", "HELIX_DIFFICULTY_RESET_VALUE", self.difficulty
        ))
        self.difficulty_reset_height = int(setting(
            "difficulty_reset_height", "HELIX_DIFFICULTY_RESET_HEIGHT", -1
        ))
        if not self.min_difficulty <= self.difficulty_reset_value <= self.max_difficulty:
            raise ValueError("difficulty reset value must be within the configured difficulty bounds")
        self.difficulty_adjustment_interval = int(
            setting("difficulty_adjustment_interval", "HELIX_DIFFICULTY_INTERVAL", 10)
        )
        self.target_block_time = int(
            setting("target_block_time_seconds", "HELIX_TARGET_BLOCK_TIME", 60)
        )
        self.adaptive_target_block_time = int(
            setting("adaptive_target_block_time_seconds", "HELIX_ADAPTIVE_TARGET_BLOCK_TIME", 600)
        )
        self.adaptive_difficulty_activation_height = int(
            setting("adaptive_difficulty_activation_height", "HELIX_ADAPTIVE_DIFFICULTY_HEIGHT", 60)
        )
        self.new_target_block_time = int(setting(
            "new_target_block_time_seconds", "HELIX_NEW_TARGET_BLOCK_TIME", 160
        ))
        self.new_target_block_time_activation_height = int(setting(
            "new_target_block_time_activation_height", "HELIX_NEW_TARGET_BLOCK_TIME_HEIGHT", 161
        ))
        if self.new_target_block_time <= 0:
            raise ValueError("new target block time must be positive")
        self.difficulty_activation_height = int(
            setting("difficulty_activation_height", "HELIX_DIFFICULTY_ACTIVATION_HEIGHT", 10)
        )
        # From this height on, proof of work uses a fine-grained numeric target
        # (Bitcoin-style) instead of whole leading-zero levels. Below it the
        # legacy leading-zero rule is preserved exactly, so existing blocks stay
        # valid. Keep this above the current chain tip when enabling it.
        self.fine_difficulty_activation_height = int(setting(
            "fine_difficulty_activation_height", "HELIX_FINE_DIFFICULTY_HEIGHT", 100000000
        ))
        # Fine-difficulty retarget: every difficulty_adjustment_interval blocks,
        # if the average block time over the window is below this it raises the
        # difficulty, and if above it lowers it. Difficulty rises without an
        # upper cap so it never needs manual adjustment; the only floor is
        # min_difficulty (so blocks can't become trivially easy).
        self.fine_target_block_time_seconds = int(setting(
            "fine_target_block_time_seconds", "HELIX_FINE_TARGET_BLOCK_TIME", 120
        ))
        # Starting difficulty the fine retarget seeds from (may be fractional,
        # e.g. 5.5). 0 disables it, falling back to the legacy integer seed.
        self.fine_initial_difficulty = float(setting(
            "fine_initial_difficulty", "HELIX_FINE_INITIAL_DIFFICULTY", 0
        ) or 0)
        # Largest difficulty move allowed in a single retarget window. The move
        # is proportional to how far the window's average block time was from
        # target, so a sub-second average hardens far more than an 8-minute one;
        # this only bounds the extreme so one manipulated timestamp can't swing
        # difficulty arbitrarily. A larger factor = snappier response.
        self.fine_max_adjust_factor = max(2, int(setting(
            "fine_max_adjust_factor", "HELIX_FINE_MAX_ADJUST_FACTOR", 16
        )))
        # At and above this height the fine-difficulty retarget aims for a longer
        # target block time (e.g. 10 minutes), leaving earlier windows unchanged.
        self.fine_new_target_block_time_activation_height = int(setting(
            "fine_new_target_block_time_activation_height",
            "HELIX_FINE_NEW_TARGET_BLOCK_TIME_HEIGHT", 100000000
        ))
        self.fine_new_target_block_time_seconds = int(setting(
            "fine_new_target_block_time_seconds",
            "HELIX_FINE_NEW_TARGET_BLOCK_TIME", 600
        ))
        self.token_metadata_activation_height = int(
            setting("token_metadata_activation_height", "HELIX_TOKEN_METADATA_ACTIVATION_HEIGHT", 41)
        )
        self.token_exchange_activation_height = int(
            setting("token_exchange_activation_height", "HELIX_TOKEN_EXCHANGE_ACTIVATION_HEIGHT", 41)
        )
        self.token_swap_activation_height = int(
            setting("token_swap_activation_height", "HELIX_TOKEN_SWAP_ACTIVATION_HEIGHT", 200)
        )
        self.nft_activation_height = int(
            setting("nft_activation_height", "HELIX_NFT_ACTIVATION_HEIGHT", 1)
        )
        self.max_orphans = int(setting("max_orphans", "HELIX_MAX_ORPHANS", 100))
        self.orphan_ttl_seconds = int(
            setting("orphan_ttl_seconds", "HELIX_ORPHAN_TTL", 1800)
        )
        self.checkpoints = {}
        self.orphan_blocks = {}
        self.block_reward = int(setting("reward", "HELIX_BLOCK_REWARD", 10))
        self.mining_reward = int(setting("mining_reward", "HELIX_MINING_REWARD", 2))
        self.mining_reward_activation_height = int(
            setting("mining_reward_activation_height", "HELIX_MINING_REWARD_HEIGHT", 90)
        )
        self.fractional_mining_reward = Decimal(str(
            setting("fractional_mining_reward", "HELIX_FRACTIONAL_MINING_REWARD", "10")
        ))
        self.fractional_reward_activation_height = int(setting(
            "fractional_reward_activation_height", "HELIX_FRACTIONAL_REWARD_HEIGHT", 300
        ))
        self.native_dad_address = str(setting(
            "native_dad_address", "HELIX_NATIVE_DAD_ADDRESS",
            "9d7c721b209cee99a8158c524fa433ead9236781",
        )).lower()
        self.native_dad_activation_height = int(setting(
            "native_dad_activation_height", "HELIX_NATIVE_DAD_HEIGHT", 300
        ))
        if not self._valid_address(self.native_dad_address):
            raise ValueError("native DAD address must be a 40-character hexadecimal address")
        if (
            not self.fractional_mining_reward.is_finite()
            or self.fractional_mining_reward <= 0
            or self.fractional_mining_reward.as_tuple().exponent < -3
        ):
            raise ValueError("fractional mining reward must be positive with at most 3 decimal places")
        self.max_supply = int(setting("max_supply", "HELIX_MAX_SUPPLY", 20000000))
        self.max_pending_transactions = int(os.getenv("HELIX_MAX_PENDING", "5000"))
        self._lock = threading.RLock()
        self._balance_index: dict[str, int] = {}
        self._transaction_index: dict[str, tuple[Block, Transaction]] = {}
        self._address_history: dict[str, list[tuple[Block, Transaction]]] = defaultdict(list)
        self._total_supply_cache = 0
        self._tokens: dict[str, dict] = {}
        self._token_balances: dict[tuple[str, str], int] = {}
        self._token_supply: dict[str, int] = {}
        self._token_accounts: set[tuple[str, str]] = set()
        self._token_history: dict[tuple[str, str], list[tuple[Block, Transaction]]] = defaultdict(list)
        self.auto_checkpoint_interval = int(setting(
            "auto_checkpoint_interval", "HELIX_AUTO_CHECKPOINT_INTERVAL", 25))
        self.auto_checkpoint_depth = int(setting(
            "auto_checkpoint_depth", "HELIX_AUTO_CHECKPOINT_DEPTH", 50))
        self.auto_checkpoints_file = Path(os.getenv(
            "HELIX_AUTO_CHECKPOINTS_FILE",
            self.database.parent / f"auto_checkpoints_{self.database.stem}.json"))
        self.set_checkpoints(consensus.get("checkpoints", {}))
        self._load_auto_checkpoints()
        self.load()
        self.update_auto_checkpoints()

    @staticmethod
    def _valid_address(address: str) -> bool:
        return isinstance(address, str) and ADDRESS_RE.fullmatch(address) is not None

    @staticmethod
    def _valid_metadata_url(value: str) -> bool:
        if not isinstance(value, str) or not 1 <= len(value) <= 1024:
            return False
        try:
            parsed = urlparse(value)
        except ValueError:
            return False
        return (
            parsed.scheme == "https"
            and bool(parsed.netloc)
            and parsed.username is None
            and parsed.password is None
            and not any(ord(char) < 32 for char in value)
        )

    @staticmethod
    def _genesis_block() -> Block:
        return Block(0, [], "0", timestamp=0, nonce=0)

    def create_genesis(self) -> None:
        self.chain = [self._genesis_block()]
        self.pending_transactions = []
        self.cancelled_transactions = {}
        self._rebuild_indexes()
        self.save()

    def _rebuild_indexes(self) -> None:
        """Build in-memory indexes used by balance, history, and transaction queries."""
        balances: dict[str, int] = defaultdict(int)
        transactions: dict[str, tuple[Block, Transaction]] = {}
        history: dict[str, list[tuple[Block, Transaction]]] = defaultdict(list)
        total_supply = 0
        tokens: dict[str, dict] = {}
        token_balances: dict[tuple[str, str], int] = defaultdict(int)
        token_supply: dict[str, int] = defaultdict(int)
        token_accounts: set[tuple[str, str]] = set()
        token_history: dict[tuple[str, str], list[tuple[Block, Transaction]]] = defaultdict(list)
        nfts: dict[str, dict] = {}
        nft_history: dict[str, list[tuple[Block, Transaction]]] = defaultdict(list)
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == "SYSTEM":
                    total_supply += tx.amount
                    balances[tx.receiver] += tx.amount
                elif tx.tx_type == "transfer":
                    balances[tx.sender] -= tx.amount
                    balances[tx.receiver] += tx.amount
                elif tx.tx_type in Transaction.NFT_TYPES:
                    self._apply_nft_transaction(tx, nfts, block_index=block.index)
                    nft_history[tx.nft_id].append((block, tx))
                else:
                    self._apply_token_transaction(
                        tx, tokens, token_balances, token_supply,
                        block_index=block.index,
                        hlx_balances=balances,
                    )
                    if tx.tx_type in {"token_mint", "token_buy"}:
                        token_accounts.add((tx.mint_address, tx.receiver))
                    elif tx.tx_type in {"token_transfer", "token_sell", "token_pool_create", "token_swap", "token_burn"}:
                        token_accounts.add((tx.mint_address, tx.sender))
                        if tx.tx_type == "token_transfer":
                            token_accounts.add((tx.mint_address, tx.receiver))
                        elif tx.tx_type == "token_swap":
                            token_accounts.add((tx.target_mint_address, tx.sender))
                    token_history[(tx.mint_address, tx.sender)].append((block, tx))
                    if tx.tx_type == "token_swap":
                        token_history[(tx.target_mint_address, tx.sender)].append((block, tx))
                    if tx.receiver != tx.sender:
                        token_history[(tx.mint_address, tx.receiver)].append((block, tx))
                if tx.sender != "SYSTEM":
                    history[tx.sender].append((block, tx))
                if tx.receiver != tx.sender:
                    history[tx.receiver].append((block, tx))
                if tx.tx_id:
                    transactions[tx.tx_id] = (block, tx)
        self._balance_index = dict(balances)
        self._transaction_index = transactions
        self._address_history = history
        self._total_supply_cache = total_supply
        self._tokens = tokens
        self._token_balances = dict(token_balances)
        self._token_supply = dict(token_supply)
        self._token_accounts = token_accounts
        self._token_history = token_history
        self._nfts = nfts
        self._nft_history = nft_history

    def get_nfts(self) -> list[dict]:
        with self._lock:
            return [dict(nft) for nft in getattr(self, "_nfts", {}).values()]

    def get_nft(self, nft_id: str) -> dict | None:
        with self._lock:
            nft = getattr(self, "_nfts", {}).get(nft_id)
            return dict(nft) if nft else None

    def get_nfts_by_owner(self, owner: str) -> list[dict]:
        with self._lock:
            return [dict(nft) for nft in getattr(self, "_nfts", {}).values() if nft.get("owner") == owner]

    def get_nft_history(self, nft_id: str):
        with self._lock:
            return list(getattr(self, "_nft_history", {}).get(nft_id, ()))

    def get_address_history(self, address: str):
        with self._lock:
            return list(self._address_history.get(address, ()))

    def get_recent_transactions(self, limit: int = 25, offset: int = 0):
        """Return the newest confirmed transactions across the whole chain."""
        bounded_limit = max(1, min(int(limit), 100))
        bounded_offset = max(0, int(offset))
        recent = []
        skipped = 0
        with self._lock:
            for block in reversed(self.chain):
                for tx in reversed(block.transactions):
                    if skipped < bounded_offset:
                        skipped += 1
                        continue
                    recent.append((block, tx))
                    if len(recent) >= bounded_limit:
                        return recent
        return recent

    def confirmed_transaction_count(self) -> int:
        """Return the number of confirmed transactions, including rewards."""
        with self._lock:
            return sum(len(block.transactions) for block in self.chain)

    def save(self) -> None:
        try:
            self.update_auto_checkpoints()
        except Exception:
            pass
        data = {
            "chain": [
                {
                    "index": block.index,
                    "transactions": [tx.to_dict() for tx in block.transactions],
                    "previous_hash": block.previous_hash,
                    "timestamp": block.timestamp,
                    "nonce": block.nonce,
                    "hash": block.hash,
                }
                for block in self.chain
            ],
            "pending": [{**tx.to_dict(), "received_at": tx.received_at} for tx in self.pending_transactions],
            "cancelled": self.cancelled_transactions,
        }

        self.database.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.database.with_suffix(self.database.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
            file.flush()
            os.fsync(file.fileno())
        # Windows indexers/antivirus can briefly hold the destination between
        # close and replace. Preserve atomic saves while tolerating that short
        # sharing violation instead of failing a valid transaction or block.
        for attempt in range(5):
            try:
                os.replace(temporary, self.database)
                break
            except PermissionError:
                if attempt == 4:
                    raise
                time.sleep(0.01 * (2 ** attempt))

    def load(self) -> None:
        with self._lock:
            if not self.database.exists():
                self.create_genesis()
                return

            try:
                with self.database.open("r", encoding="utf-8") as file:
                    data = json.load(file)
                loaded_chain = []
                for saved in data.get("chain", []):
                    transactions = [
                        _transaction_from_dict(tx_data)
                        for tx_data in saved.get("transactions", [])
                    ]
                    loaded_chain.append(
                        Block(
                            saved["index"],
                            transactions,
                            saved["previous_hash"],
                            saved["timestamp"],
                            saved["nonce"],
                            saved["hash"],
                        )
                    )

                valid, reason = self.validate_chain(loaded_chain)
                if not valid:
                    raise ValueError(f"saved chain is invalid: {reason}")

                self.chain = loaded_chain
                cancelled = {}
                for tx_id, record in data.get("cancelled", {}).items():
                    if (
                        isinstance(tx_id, str)
                        and re.fullmatch(r"[0-9a-f]{64}", tx_id)
                        and isinstance(record, dict)
                        and self._valid_address(record.get("sender"))
                        and isinstance(record.get("cancelled_at"), (int, float))
                    ):
                        cancelled[tx_id] = {
                            "sender": record["sender"],
                            "cancelled_at": float(record["cancelled_at"]),
                        }
                self.cancelled_transactions = cancelled
                pending = []
                for tx_data in data.get("pending", []):
                    try:
                        tx = _transaction_from_dict(tx_data)
                        if self._validate_pending_transaction(tx, pending):
                            pending.append(tx)
                    except Exception:
                        continue
                self.pending_transactions = pending
                self._rebuild_indexes()
            except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                # Fail closed. A loader bug or temporary schema mismatch must
                # never move a valid chain aside and silently start a new one.
                raise RuntimeError(
                    f"could not load blockchain database {self.database}: {exc}. "
                    "The database was left untouched."
                ) from exc

    def get_balance(self, address: str, chain=None) -> int:
        if chain is None:
            return self._balance_index.get(address, 0)
        balance = 0
        for block in chain:
            for tx in block.transactions:
                if tx.tx_type != "transfer":
                    continue
                if tx.sender == address:
                    balance -= tx.amount
                if tx.receiver == address:
                    balance += tx.amount
        return balance

    def get_available_balance(self, address: str, extra_pending=None) -> int:
        pending = self.pending_transactions if extra_pending is None else extra_pending
        outgoing = sum(
            (
                tx.hlx_amount if tx.tx_type == "token_pool_create"
                else tx.amount
            )
            for tx in pending
            if tx.sender == address and tx.tx_type in {
                "transfer", "token_pool_create", "token_pool_add_hlx", "token_buy"
            }
        )
        return self.get_balance(address) - outgoing

    def get_total_supply(self, chain=None) -> int:
        if chain is None:
            return self._total_supply_cache
        return sum(
            tx.amount for block in chain for tx in block.transactions
            if tx.sender == "SYSTEM"
        )

    @staticmethod
    def _token_record(tx: Transaction) -> dict:
        return {
            "mint_address": tx.mint_address,
            "dad_address": tx.dad_address,
            "creator_address": tx.sender,
            "name": tx.name,
            "symbol": tx.symbol,
            "description": tx.description,
            "image": tx.image,
            "metadata_hash": tx.metadata_hash,
            "decimals": tx.decimals,
            "uri": tx.uri or "",
            "creation_tx_id": tx.tx_id,
            "pool_hlx_reserve": 0,
            "pool_token_reserve": 0,
            "pool_creator": None,
        }

    @staticmethod
    def _swap_output(amount_in: int, reserve_in: int, reserve_out: int) -> int:
        """Constant-product quote with a 0.3% fee retained by the pool."""
        if amount_in <= 0 or reserve_in <= 0 or reserve_out <= 0:
            return 0
        amount_with_fee = amount_in * SWAP_FEE_NUMERATOR
        return (
            amount_with_fee * reserve_out
            // (reserve_in * SWAP_FEE_DENOMINATOR + amount_with_fee)
        )

    @staticmethod
    def _validate_nft_attributes(attributes) -> str | None:
        if not isinstance(attributes, list):
            return "NFT attributes must be a list"
        if len(attributes) > 30:
            return "an NFT can have at most 30 attributes"
        for attr in attributes:
            if not isinstance(attr, dict) or set(attr.keys()) != {"trait_type", "value"}:
                return "each NFT attribute must have exactly trait_type and value"
            trait_type, value = attr.get("trait_type"), attr.get("value")
            if not isinstance(trait_type, str) or not 1 <= len(trait_type) <= 40:
                return "attribute trait_type must be 1 to 40 characters"
            if not isinstance(value, str) or not 1 <= len(value) <= 80:
                return "attribute value must be 1 to 80 characters"
        return None

    def _apply_nft_transaction(self, tx: Transaction, nfts: dict, block_index: int | None = None) -> str | None:
        """Validate and apply one NFT operation.

        ERC-721 style: each NFT is a unique asset with an explicit owner (not a
        fungible balance). ``nft_mint`` creates it (owner = creator); only the
        current owner can ``nft_transfer`` it.
        """
        if tx.tx_type not in Transaction.NFT_TYPES:
            return "transaction type is unsupported"
        if block_index is not None and block_index < self.nft_activation_height:
            return "NFTs are not active at this block height"
        if not self._valid_address(tx.nft_id):
            return "NFT id is invalid"
        if not isinstance(tx.nonce, str) or TOKEN_NONCE_RE.fullmatch(tx.nonce) is None:
            return "NFT transaction nonce must be 32 lowercase hexadecimal characters"
        if tx.amount != 0:
            return "NFT transactions must use amount zero"

        if tx.tx_type == "nft_mint":
            if tx.nft_id in nfts:
                return "NFT id already exists"
            if tx.nft_id != Transaction.nft_address(tx.sender, tx.nonce):
                return "NFT id does not match its creator and nonce"
            if tx.receiver != tx.sender:
                return "an NFT is minted to its creator"
            if not isinstance(tx.name, str) or not 1 <= len(tx.name.strip()) <= 64:
                return "NFT name must contain 1 to 64 characters"
            if tx.name != tx.name.strip() or any(ord(char) < 32 for char in tx.name):
                return "NFT name contains invalid whitespace or control characters"
            if not isinstance(tx.description, str) or not 1 <= len(tx.description.strip()) <= 1000:
                return "NFT description must contain 1 to 1000 characters"
            if tx.description != tx.description.strip() or "\x00" in tx.description:
                return "NFT description contains invalid control characters"
            if not self._valid_metadata_url(tx.image):
                return "NFT image must be a valid HTTPS URL"
            if not self._valid_metadata_url(tx.uri):
                return "NFT metadata URI must be a valid HTTPS URL"
            attributes = tx.attributes if isinstance(tx.attributes, list) else []
            attribute_error = self._validate_nft_attributes(attributes)
            if attribute_error is not None:
                return attribute_error
            expected_hash = Transaction.nft_metadata_hash(tx.name, tx.description, tx.image, attributes)
            if tx.metadata_hash != expected_hash:
                return "NFT metadata hash does not match its on-chain fields"
            royalty = tx.royalty_bps or 0
            if not 0 <= royalty <= 10000:
                return "NFT royalty must be between 0 and 10000 basis points"
            nfts[tx.nft_id] = {
                "nft_id": tx.nft_id,
                "creator": tx.sender,
                "owner": tx.sender,
                "name": tx.name,
                "description": tx.description,
                "image": tx.image,
                "uri": tx.uri or "",
                "metadata_hash": tx.metadata_hash,
                "attributes": attributes,
                "royalty_bps": royalty,
                "minted_block": block_index,
            }
            return None

        # nft_transfer
        nft = nfts.get(tx.nft_id)
        if nft is None:
            return "NFT does not exist on the confirmed chain or earlier in this block"
        if tx.sender != nft["owner"]:
            return "only the current NFT owner can transfer it"
        if not self._valid_address(tx.receiver):
            return "NFT recipient address is invalid"
        nft["owner"] = tx.receiver
        return None

    def _apply_token_transaction(
        self,
        tx: Transaction,
        tokens: dict,
        token_balances: dict,
        token_supply: dict,
        block_index: int | None = None,
        hlx_balances: dict | None = None,
    ) -> str | None:
        """Validate and apply one token operation to the supplied chain state."""
        if tx.tx_type not in Transaction.TOKEN_TYPES:
            return "transaction type is unsupported"
        exchange_types = {"token_pool_create", "token_pool_add_hlx", "token_buy", "token_sell", "token_swap"}
        if (
            tx.tx_type in exchange_types
            and block_index is not None
            and block_index < self.token_exchange_activation_height
        ):
            return "token exchange is not active at this block height"
        if (
            tx.tx_type == "token_swap"
            and block_index is not None
            and block_index < self.token_swap_activation_height
        ):
            return "token-to-token swaps are not active at this block height"
        if not self._valid_address(tx.mint_address):
            return "token mint address is invalid"
        if not isinstance(tx.nonce, str) or TOKEN_NONCE_RE.fullmatch(tx.nonce) is None:
            return "token transaction nonce must be 32 lowercase hexadecimal characters"
        if tx.amount < 0 or tx.amount > MAX_TOKEN_UNITS:
            return "token amount is outside the supported range"
        if tx.tx_type in Transaction.ZERO_AMOUNT_TYPES and tx.amount != 0:
            return "token management transactions must use amount zero"
        if tx.tx_type not in Transaction.ZERO_AMOUNT_TYPES and tx.amount == 0:
            return "token amount is outside the supported range"

        if tx.tx_type == "token_create":
            if tx.mint_address in tokens:
                return "token mint address already exists"
            expected_mint = Transaction.mint_address(tx.sender, tx.nonce)
            if tx.mint_address != expected_mint:
                return "token mint address does not match creator and nonce"
            if not self._valid_address(tx.dad_address):
                return "token DAD authority address is invalid"
            if tx.receiver != tx.sender:
                return "token creation receiver must match its creator"
            if not isinstance(tx.name, str) or not 1 <= len(tx.name.strip()) <= 64:
                return "token name must contain 1 to 64 characters"
            if tx.name != tx.name.strip() or any(ord(char) < 32 for char in tx.name):
                return "token name contains invalid whitespace or control characters"
            if not isinstance(tx.symbol, str) or TOKEN_SYMBOL_RE.fullmatch(tx.symbol) is None:
                return "token symbol must be 2 to 12 uppercase letters or digits"
            if isinstance(tx.decimals, bool) or not isinstance(tx.decimals, int) or not 0 <= tx.decimals <= 9:
                return "token decimals must be an integer from 0 to 9"

            has_metadata_snapshot = any(value is not None for value in (
                tx.description, tx.image, tx.metadata_hash
            ))
            metadata_required = (
                block_index is None
                or block_index >= self.token_metadata_activation_height
            )
            if metadata_required or has_metadata_snapshot:
                if not isinstance(tx.description, str) or not 1 <= len(tx.description.strip()) <= 1000:
                    return "token description must contain 1 to 1000 characters"
                if tx.description != tx.description.strip() or "\x00" in tx.description:
                    return "token description contains invalid whitespace or control characters"
                if not self._valid_metadata_url(tx.image):
                    return "token image must be a valid HTTPS URL"
                if not self._valid_metadata_url(tx.uri):
                    return "token metadata URI must be a valid HTTPS URL"
                expected_metadata_hash = Transaction.token_metadata_hash(
                    tx.name, tx.symbol, tx.description, tx.image
                )
                if tx.metadata_hash != expected_metadata_hash:
                    return "token metadata hash does not match its on-chain fields"

            tokens[tx.mint_address] = self._token_record(tx)
            token_supply[tx.mint_address] = 0
            return None

        token = tokens.get(tx.mint_address)
        if token is None:
            return "token mint does not exist on the confirmed chain or earlier in this block"

        if tx.tx_type == "token_mint":
            if token["dad_address"] is None or tx.sender != token["dad_address"]:
                return "only the token DAD authority can mint more supply"
            new_supply = token_supply[tx.mint_address] + tx.amount
            if new_supply > MAX_TOKEN_UNITS:
                return "token supply would exceed the network limit"
            token_supply[tx.mint_address] = new_supply
            token_balances[(tx.mint_address, tx.receiver)] += tx.amount
            return None

        if tx.tx_type == "token_set_authority":
            if token["dad_address"] is None or tx.sender != token["dad_address"]:
                return "only the current DAD authority can change token authority"
            token["dad_address"] = None if tx.receiver == ZERO_ADDRESS else tx.receiver
            return None

        if tx.tx_type == "token_burn":
            if token["dad_address"] is None or tx.sender != token["dad_address"]:
                return "only the token DAD authority can burn supply"
            if tx.receiver != tx.sender:
                return "token burn receiver must match its sender"
            if token_balances[(tx.mint_address, tx.sender)] < tx.amount:
                return "token burn exceeds the DAD balance"
            token_balances[(tx.mint_address, tx.sender)] -= tx.amount
            token_supply[tx.mint_address] -= tx.amount
            return None

        if tx.tx_type in exchange_types:
            if tx.receiver != tx.sender:
                return "token exchange receiver must match its sender"
            if hlx_balances is None:
                return "HLX balance state is required for token exchange"

        if tx.tx_type == "token_swap":
            if not self._valid_address(tx.target_mint_address):
                return "target token mint address is invalid"
            if tx.target_mint_address == tx.mint_address:
                return "source and target token mints must be different"
            target = tokens.get(tx.target_mint_address)
            if target is None:
                return "target token mint does not exist on the confirmed chain or earlier in this block"
            if not isinstance(tx.min_receive, int) or isinstance(tx.min_receive, bool) or tx.min_receive < 0:
                return "minimum received amount must be a non-negative integer"
            source_hlx = token["pool_hlx_reserve"]
            source_units = token["pool_token_reserve"]
            target_hlx = target["pool_hlx_reserve"]
            target_units = target["pool_token_reserve"]
            if min(source_hlx, source_units, target_hlx, target_units) <= 0:
                return "both tokens must have active exchange pools"
            if token_balances[(tx.mint_address, tx.sender)] < tx.amount:
                return "token swap exceeds the sender source-token balance"
            routed_hlx = self._swap_output(tx.amount, source_units, source_hlx)
            if routed_hlx <= 0 or routed_hlx >= source_hlx:
                return "token swap is too small or would drain the source pool"
            received = self._swap_output(routed_hlx, target_hlx, target_units)
            if received <= 0 or received >= target_units:
                return "token swap is too small or would drain the target pool"
            if received < tx.min_receive:
                return "token swap output is below its minimum"
            token_balances[(tx.mint_address, tx.sender)] -= tx.amount
            token_balances[(tx.target_mint_address, tx.sender)] += received
            token["pool_token_reserve"] += tx.amount
            token["pool_hlx_reserve"] -= routed_hlx
            target["pool_hlx_reserve"] += routed_hlx
            target["pool_token_reserve"] -= received
            return None

        if tx.tx_type == "token_pool_create":
            if token["dad_address"] is None or tx.sender != token["dad_address"]:
                return "only the token DAD authority can create its exchange pool"
            if token["pool_hlx_reserve"] or token["pool_token_reserve"]:
                return "token exchange pool already exists"
            if not isinstance(tx.hlx_amount, int) or isinstance(tx.hlx_amount, bool) or tx.hlx_amount <= 0:
                return "initial HLX liquidity must be a positive integer"
            available_tokens = token_balances[(tx.mint_address, tx.sender)]
            if available_tokens <= 0:
                return "DAD must hold tokens before creating an exchange pool"
            if tx.amount != available_tokens:
                return "initial token liquidity must use the DAD wallet's full confirmed balance"
            if hlx_balances[tx.sender] < tx.hlx_amount:
                return "initial liquidity exceeds the DAD HLX balance"
            token_balances[(tx.mint_address, tx.sender)] -= tx.amount
            hlx_balances[tx.sender] -= tx.hlx_amount
            token["pool_token_reserve"] = tx.amount
            token["pool_hlx_reserve"] = tx.hlx_amount
            token["pool_creator"] = tx.sender
            return None

        if tx.tx_type == "token_pool_add_hlx":
            if token["dad_address"] is None or tx.sender != token["dad_address"]:
                return "only the token DAD authority can add direct HLX liquidity"
            if token["pool_hlx_reserve"] <= 0 or token["pool_token_reserve"] <= 0:
                return "token does not have an active exchange pool"
            if hlx_balances[tx.sender] < tx.amount:
                return "liquidity addition exceeds the DAD HLX balance"
            hlx_balances[tx.sender] -= tx.amount
            token["pool_hlx_reserve"] += tx.amount
            return None

        if tx.tx_type in {"token_buy", "token_sell"}:
            if not isinstance(tx.min_receive, int) or isinstance(tx.min_receive, bool) or tx.min_receive < 0:
                return "minimum received amount must be a non-negative integer"
            hlx_reserve = token["pool_hlx_reserve"]
            token_reserve = token["pool_token_reserve"]
            if hlx_reserve <= 0 or token_reserve <= 0:
                return "token does not have an active exchange pool"

            if tx.tx_type == "token_buy":
                if hlx_balances[tx.sender] < tx.amount:
                    return "token purchase exceeds the sender HLX balance"
                received = self._swap_output(tx.amount, hlx_reserve, token_reserve)
                if received <= 0 or received >= token_reserve:
                    return "token purchase is too small or would drain the pool"
                if received < tx.min_receive:
                    return "token purchase output is below its minimum"
                hlx_balances[tx.sender] -= tx.amount
                token_balances[(tx.mint_address, tx.sender)] += received
                token["pool_hlx_reserve"] += tx.amount
                token["pool_token_reserve"] -= received
                return None

            if token_balances[(tx.mint_address, tx.sender)] < tx.amount:
                return "token sale exceeds the sender token balance"
            received = self._swap_output(tx.amount, token_reserve, hlx_reserve)
            if received <= 0 or received >= hlx_reserve:
                return "token sale is too small or would drain the pool"
            if received < tx.min_receive:
                return "token sale output is below its minimum"
            token_balances[(tx.mint_address, tx.sender)] -= tx.amount
            hlx_balances[tx.sender] += received
            token["pool_token_reserve"] += tx.amount
            token["pool_hlx_reserve"] -= received
            return None

        balance_key = (tx.mint_address, tx.sender)
        if token_balances[balance_key] < tx.amount:
            return "token transfer exceeds the sender balance"
        token_balances[balance_key] -= tx.amount
        token_balances[(tx.mint_address, tx.receiver)] += tx.amount
        return None

    def get_token(self, mint_address: str) -> dict | None:
        with self._lock:
            token = self._tokens.get(mint_address)
            if token is None:
                return None
            return {**token, "supply": self._token_supply.get(mint_address, 0)}

    def get_tokens_by_dad_address(self, dad_address: str) -> list[dict]:
        """Return confirmed tokens controlled by the supplied DAD authority."""
        return [
            token for token in self.list_tokens()
            if token["dad_address"] == dad_address
        ]

    def list_tokens(self, holder: str | None = None) -> list[dict]:
        with self._lock:
            result = []
            for mint, token in self._tokens.items():
                item = {**token, "supply": self._token_supply.get(mint, 0)}
                if holder is not None:
                    item["balance"] = self._token_balances.get((mint, holder), 0)
                result.append(item)
            return sorted(result, key=lambda item: (item["symbol"], item["mint_address"]))

    def get_token_balance(self, mint_address: str, address: str) -> int:
        with self._lock:
            return self._token_balances.get((mint_address, address), 0)

    def token_account_exists(self, mint_address: str, address: str) -> bool:
        with self._lock:
            return (mint_address, address) in self._token_accounts

    def get_token_history(self, mint_address: str, address: str):
        with self._lock:
            return list(self._token_history.get((mint_address, address), ()))

    def get_token_market_history(self, mint_address: str) -> list[dict]:
        """Reconstruct confirmed pool reserves after every market operation."""
        with self._lock:
            if mint_address not in self._tokens:
                return []
            pools: dict[str, list[int]] = {}
            points = []
            market_types = {
                "token_pool_create", "token_pool_add_hlx", "token_buy", "token_sell", "token_swap",
            }
            for block in self.chain:
                for tx in block.transactions:
                    if tx.tx_type not in market_types:
                        continue
                    affected = {tx.mint_address}
                    if tx.tx_type == "token_pool_create":
                        pools[tx.mint_address] = [tx.hlx_amount, tx.amount]
                    elif tx.tx_type == "token_pool_add_hlx":
                        pools[tx.mint_address][0] += tx.amount
                    elif tx.tx_type == "token_buy":
                        pool = pools[tx.mint_address]
                        received = self._swap_output(tx.amount, pool[0], pool[1])
                        pool[0] += tx.amount
                        pool[1] -= received
                    elif tx.tx_type == "token_sell":
                        pool = pools[tx.mint_address]
                        received = self._swap_output(tx.amount, pool[1], pool[0])
                        pool[1] += tx.amount
                        pool[0] -= received
                    else:
                        source = pools[tx.mint_address]
                        target = pools[tx.target_mint_address]
                        routed_hlx = self._swap_output(tx.amount, source[1], source[0])
                        received = self._swap_output(routed_hlx, target[0], target[1])
                        source[1] += tx.amount
                        source[0] -= routed_hlx
                        target[0] += routed_hlx
                        target[1] -= received
                        affected.add(tx.target_mint_address)
                    if mint_address in affected:
                        pool = pools[mint_address]
                        points.append({
                            "block": block.index,
                            "timestamp": block.timestamp,
                            "tx_id": tx.tx_id,
                            "tx_type": tx.tx_type,
                            "pool_hlx_reserve": pool[0],
                            "pool_token_reserve": pool[1],
                        })
            return points

    def transaction_rejection_reason(self, tx: Transaction, pending=None) -> str | None:
        pending = self.pending_transactions if pending is None else pending
        if tx.sender == "SYSTEM":
            return "wallets cannot submit SYSTEM transactions"
        if not self._valid_address(tx.sender) or not self._valid_address(tx.receiver):
            return "transaction address is invalid"
        if tx.amount < 0 or (tx.amount == 0 and tx.tx_type not in Transaction.ZERO_AMOUNT_TYPES):
            return "transaction amount must be positive"
        if not tx.verify_signature():
            return "transaction signature is invalid"
        if tx.tx_id != tx.calculate_id():
            return "transaction ID is invalid"
        if self.is_transaction_cancelled(tx.tx_id, tx.sender):
            return "transaction was cancelled by its sender"
        if any(existing.tx_id == tx.tx_id for existing in pending):
            return "transaction is already pending"
        if self.find_transaction(tx.tx_id)[1] is not None:
            return "transaction is already confirmed"

        if tx.tx_type == "transfer":
            if self.get_available_balance(tx.sender, pending) < tx.amount:
                return "transaction exceeds the sender's available HLX balance"
            return None

        if tx.tx_type in Transaction.NFT_TYPES:
            nfts = {nid: dict(nft) for nid, nft in getattr(self, "_nfts", {}).items()}
            for existing in pending:
                if existing.tx_type in Transaction.NFT_TYPES:
                    if self._apply_nft_transaction(existing, nfts, block_index=len(self.chain)) is not None:
                        return "existing pending NFT state is invalid"
            return self._apply_nft_transaction(tx, nfts, block_index=len(self.chain))

        tokens = {mint: dict(token) for mint, token in self._tokens.items()}
        token_balances = defaultdict(int, self._token_balances)
        token_supply = defaultdict(int, self._token_supply)
        hlx_balances = defaultdict(int, self._balance_index)
        for existing in pending:
            if existing.tx_type == "transfer":
                hlx_balances[existing.sender] -= existing.amount
                hlx_balances[existing.receiver] += existing.amount
            if existing.tx_type in Transaction.TOKEN_TYPES:
                reason = self._apply_token_transaction(
                    existing, tokens, token_balances, token_supply,
                    block_index=len(self.chain),
                    hlx_balances=hlx_balances,
                )
                if reason is not None:
                    return "existing pending token state is invalid"
        return self._apply_token_transaction(
            tx, tokens, token_balances, token_supply,
            block_index=len(self.chain),
            hlx_balances=hlx_balances,
        )

    def _validate_pending_transaction(self, tx: Transaction, pending=None) -> bool:
        return self.transaction_rejection_reason(tx, pending) is None

    def add_transaction(self, transaction: Transaction) -> bool:
        with self._lock:
            if transaction.tx_id is None:
                transaction.generate_id()
            if len(self.pending_transactions) >= self.max_pending_transactions:
                return False
            if not self._validate_pending_transaction(transaction):
                return False
            self.pending_transactions.append(transaction)
            self.save()
            return True


    def get_pending_transaction(self, tx_id: str):
        with self._lock:
            return next((tx for tx in self.pending_transactions if tx.tx_id == tx_id), None)

    def is_transaction_cancelled(self, tx_id: str, sender: str) -> bool:
        with self._lock:
            record = self.cancelled_transactions.get(tx_id)
            return bool(record and record.get("sender") == sender)

    def cancel_pending_transaction(
        self, tx_id: str, sender: str, *, allow_missing: bool = False, now=None
    ) -> bool:
        """Cancel only the sender's transaction and retain a short-lived tombstone."""
        with self._lock:
            transaction = next(
                (tx for tx in self.pending_transactions if tx.tx_id == tx_id), None
            )
            if transaction is not None and transaction.sender != sender:
                return False
            if transaction is None and not allow_missing:
                return False
            if self.find_transaction(tx_id)[1] is not None:
                return False
            self.cancelled_transactions[tx_id] = {
                "sender": sender,
                "cancelled_at": time.time() if now is None else float(now),
            }
            if transaction is not None:
                self.pending_transactions = [
                    tx for tx in self.pending_transactions if tx.tx_id != tx_id
                ]
            self.save()
            return True

    def prune_cancelled_transactions(self, ttl_seconds: int, now=None) -> list[str]:
        cutoff = (time.time() if now is None else float(now)) - max(60, int(ttl_seconds))
        with self._lock:
            expired = [
                tx_id for tx_id, record in self.cancelled_transactions.items()
                if float(record.get("cancelled_at", 0)) < cutoff
            ]
            if expired:
                for tx_id in expired:
                    self.cancelled_transactions.pop(tx_id, None)
                self.save()
            return expired

    def pending_ids(self) -> set[str]:
        with self._lock:
            return {tx.tx_id for tx in self.pending_transactions if tx.tx_id}

    def prune_expired_pending(self, ttl_seconds: int, now=None) -> list[str]:
        cutoff = (time.time() if now is None else float(now)) - max(60, int(ttl_seconds))
        with self._lock:
            expired = [
                tx.tx_id for tx in self.pending_transactions
                if tx.tx_id and getattr(tx, "received_at", 0) < cutoff
            ]
            if expired:
                expired_set = set(expired)
                self.pending_transactions = [
                    tx for tx in self.pending_transactions if tx.tx_id not in expired_set
                ]
                self.save()
            return expired

    def reward_for_height(self, block_index: int):
        if block_index >= self.fractional_reward_activation_height:
            return self.fractional_mining_reward
        if block_index >= self.mining_reward_activation_height:
            return self.mining_reward
        return self.block_reward

    def native_dad_for_height(self, block_index: int) -> str | None:
        """Return the non-minting native governance identity when active."""
        return (
            self.native_dad_address
            if block_index >= self.native_dad_activation_height
            else None
        )

    def _reward_amount(self, total_supply=None, block_index: int | None = None) -> int:
        supply = self.get_total_supply() if total_supply is None else total_supply
        index = len(self.chain) if block_index is None else block_index
        return max(0, min(self.reward_for_height(index), self.max_supply - supply))

    def _make_reward(self, block_index: int, miner_address: str, previous_hash: str) -> Transaction:
        amount = self._reward_amount(block_index=block_index)
        reward = Transaction("SYSTEM", miner_address, amount)
        reward.tx_id = Transaction.reward_id(
            block_index, miner_address, amount, previous_hash
        )
        return reward

    def mine_pending_transactions(self, miner_address: str):
        if not self._valid_address(miner_address):
            raise ValueError("invalid miner address")

        with self._lock:
            block, _difficulty, target = self.create_mining_candidate(miner_address)
            block.mine_to_target(target)

            valid, reason = self.validate_next_block(block)
            if not valid:
                raise RuntimeError(f"locally mined invalid block: {reason}")

            self.chain.append(block)
            self._rebuild_indexes()
            mined_ids = {tx.tx_id for tx in block.transactions}
            self.pending_transactions = [
                tx for tx in self.pending_transactions if tx.tx_id not in mined_ids
            ]
            self.save()
            return block

    def create_mining_candidate(self, miner_address: str) -> tuple[Block, int, int]:
        """Return a non-mutating snapshot miners can hash and submit.

        Returns (block, difficulty, target). `difficulty` is the whole-level
        difficulty kept for display/compatibility; `target` is the exact numeric
        target the proof must satisfy (int(hash,16) <= target).
        """
        if not self._valid_address(miner_address):
            raise ValueError("invalid miner address")
        with self._lock:
            index = len(self.chain)
            previous_hash = self.chain[-1].hash
            transactions = list(self.pending_transactions)
            transactions.append(self._make_reward(index, miner_address, previous_hash))
            block = Block(index, transactions, previous_hash)
            return (
                block,
                self.expected_difficulty(index, self.chain),
                self.expected_target(index, self.chain),
            )

    def find_transaction(self, tx_id: str):
        return self._transaction_index.get(tx_id, (None, None))

    def to_dict(self):
        return [
            {
                "index": block.index,
                "previous_hash": block.previous_hash,
                "timestamp": block.timestamp,
                "nonce": block.nonce,
                "hash": block.hash,
                "transactions": [tx.to_dict() for tx in block.transactions],
            }
            for block in self.chain
        ]

    def _validate_block_against_state(
        self,
        block: Block,
        previous: Block,
        balances: dict,
        seen_tx_ids: set,
        total_supply: int,
        tokens: dict,
        token_balances: dict,
        token_supply: dict,
        chain_context=None,
        nfts: dict | None = None,
    ):
        chain_context = self.chain if chain_context is None else chain_context
        if nfts is None:
            nfts = {}
        if block.index != previous.index + 1:
            return False, "block index is not sequential", total_supply
        if block.previous_hash != previous.hash:
            return False, "previous hash does not match chain tip", total_supply
        if block.timestamp < previous.timestamp - TIMESTAMP_BACKWARD_TOLERANCE:
            return False, "block timestamp is older than its parent", total_supply
        if block.timestamp > time.time() + 120:
            return False, "block timestamp is too far in the future", total_supply
        if block.calculate_hash() != block.hash:
            return False, "block hash does not match contents", total_supply
        expected_target = self.expected_target(block.index, chain_context)
        if not self.hash_meets_target(block.hash, expected_target):
            return False, "proof of work is invalid (hash is above the required target)", total_supply
        if not block.transactions:
            return False, "block contains no transactions", total_supply

        rewards = [tx for tx in block.transactions if tx.sender == "SYSTEM"]
        if len(rewards) != 1:
            return False, "block must contain exactly one reward", total_supply
        reward = rewards[0]
        if block.transactions[-1] is not reward:
            return False, "reward must be the final transaction", total_supply
        if not self._valid_address(reward.receiver):
            return False, "reward receiver address is invalid", total_supply
        expected_reward_amount = self._reward_amount(total_supply, block.index)
        if reward.amount != expected_reward_amount:
            return False, "reward amount is invalid", total_supply
        if reward.signature is not None or reward.public_key is not None:
            return False, "reward must not have a signature or public key", total_supply
        expected_reward_id = Transaction.reward_id(
            block.index, reward.receiver, expected_reward_amount, block.previous_hash
        )
        if reward.tx_id != expected_reward_id:
            return False, "reward transaction ID is invalid", total_supply
        if total_supply + reward.amount > self.max_supply:
            return False, "block exceeds maximum supply", total_supply

        for tx in block.transactions[:-1]:
            if tx.sender == "SYSTEM":
                return False, "unexpected SYSTEM transaction", total_supply
            if not self._valid_address(tx.sender) or not self._valid_address(tx.receiver):
                return False, "transaction address is invalid", total_supply
            if tx.amount < 0 or (tx.amount == 0 and tx.tx_type not in Transaction.ZERO_AMOUNT_TYPES):
                return False, "transaction amount must be positive", total_supply
            if not tx.verify_signature():
                return False, "transaction signature is invalid", total_supply
            if tx.tx_id is None or tx.tx_id != tx.calculate_id():
                return False, "transaction ID is invalid", total_supply
            if tx.tx_id in seen_tx_ids:
                return False, "duplicate transaction ID", total_supply
            if tx.tx_type == "transfer":
                if balances[tx.sender] < tx.amount:
                    return False, "transaction overspends sender balance", total_supply
                balances[tx.sender] -= tx.amount
                balances[tx.receiver] += tx.amount
            elif tx.tx_type in Transaction.NFT_TYPES:
                nft_error = self._apply_nft_transaction(tx, nfts, block_index=block.index)
                if nft_error is not None:
                    return False, nft_error, total_supply
            else:
                token_error = self._apply_token_transaction(
                    tx, tokens, token_balances, token_supply,
                    block_index=block.index,
                    hlx_balances=balances,
                )
                if token_error is not None:
                    return False, token_error, total_supply
            seen_tx_ids.add(tx.tx_id)

        if reward.tx_id in seen_tx_ids:
            return False, "duplicate reward transaction ID", total_supply
        balances[reward.receiver] += reward.amount
        seen_tx_ids.add(reward.tx_id)
        total_supply += reward.amount
        return True, None, total_supply

    def validate_next_block(self, block: Block):
        balances = defaultdict(int)
        seen = set()
        total_supply = 0
        tokens = {}
        token_balances = defaultdict(int)
        token_supply = defaultdict(int)
        nfts = {}
        for existing in self.chain[1:]:
            ok, reason, total_supply = self._validate_block_against_state(
                existing,
                self.chain[existing.index - 1],
                balances,
                seen,
                total_supply,
                tokens,
                token_balances,
                token_supply,
                self.chain[: existing.index],
                nfts,
            )
            if not ok:
                return False, f"local chain invalid before new block: {reason}"
        ok, reason, _ = self._validate_block_against_state(
            block, self.chain[-1], balances, seen, total_supply,
            tokens, token_balances, token_supply, self.chain, nfts
        )
        return ok, reason

    def validate_chain(self, chain):
        if not chain:
            return False, "chain is empty"
        expected_genesis = self._genesis_block()
        genesis = chain[0]
        if (
            genesis.index != 0
            or genesis.previous_hash != "0"
            or genesis.timestamp != 0
            or genesis.nonce != 0
            or genesis.transactions
            or genesis.hash != expected_genesis.hash
            or genesis.calculate_hash() != genesis.hash
        ):
            return False, "genesis block is invalid"

        balances = defaultdict(int)
        seen = set()
        total_supply = 0
        tokens = {}
        token_balances = defaultdict(int)
        token_supply = defaultdict(int)
        nfts = {}
        for position in range(1, len(chain)):
            block = chain[position]
            previous = chain[position - 1]
            expected_checkpoint = self.checkpoints.get(block.index)
            if expected_checkpoint is not None and block.hash != expected_checkpoint:
                return False, f"block {position}: checkpoint mismatch"
            ok, reason, total_supply = self._validate_block_against_state(
                block, previous, balances, seen, total_supply,
                tokens, token_balances, token_supply, chain[:position], nfts
            )
            if not ok:
                return False, f"block {position}: {reason}"
        return True, None

    def expected_difficulty(self, next_index: int, chain=None) -> int:
        chain = self.chain if chain is None else chain
        if next_index < self.difficulty_activation_height:
            return self.difficulty
        interval = max(2, self.difficulty_adjustment_interval)
        reset_active = self.difficulty_reset_height >= 0 and next_index >= self.difficulty_reset_height
        current = self.difficulty_reset_value if reset_active else self.difficulty
        first_boundary = (
            self.difficulty_reset_height + interval if reset_active else interval
        )
        # Recompute completed windows deterministically. After a reset, wait for
        # one complete post-reset window before difficulty can move again.
        for boundary in range(first_boundary, next_index + 1, interval):
            if (
                (not reset_active and boundary < self.difficulty_activation_height)
                or boundary > len(chain)
            ):
                continue
            window = chain[boundary - interval:boundary]
            if len(window) < interval:
                continue
            elapsed = max(1.0, window[-1].timestamp - window[0].timestamp)
            adaptive = boundary >= self.adaptive_difficulty_activation_height
            target_seconds = self.target_block_time_for_height(boundary)
            target = target_seconds * max(1, interval - 1)
            if elapsed < target / 2:
                current += 1
            elif elapsed > target * (1 if adaptive else 2):
                current -= 1
            current = max(self.min_difficulty, min(self.max_difficulty, current))
        return current

    def target_block_time_for_height(self, block_index: int) -> int:
        if block_index >= self.new_target_block_time_activation_height:
            return self.new_target_block_time
        if block_index >= self.adaptive_difficulty_activation_height:
            return self.adaptive_target_block_time
        return self.target_block_time

    def fine_block_time_for_height(self, block_index: int) -> int:
        """Per-block target time used by the fine-difficulty retarget."""
        if block_index >= self.fine_new_target_block_time_activation_height:
            return self.fine_new_target_block_time_seconds
        return self.fine_target_block_time_seconds

    @staticmethod
    def difficulty_to_target(difficulty) -> int:
        """The numeric target for a difficulty level, which may be fractional.

        A whole difficulty `d` maps to `16**(64-d) - 1`, i.e. `2**(256-4d) - 1`,
        so a hash has `d` leading hex zeros iff its value is <= this. Fractional
        difficulty extends the same curve: the target is `2**(256-4d) - 1`. When
        `256 - 4d` is a whole number of bits (any multiple of 0.25, e.g. 5.5 ->
        234 bits) this is computed with exact integer math so it stays
        deterministic across machines; other fractions use a float exponent.
        """
        difficulty = max(0.0, min(64.0, float(difficulty)))
        bits = 256 - 4 * difficulty          # target + 1 == 2 ** bits
        if bits <= 0:
            return 0
        if bits == int(bits):                # exact, deterministic integer path
            return (1 << int(bits)) - 1
        whole = int(bits)
        return int((1 << whole) * (2.0 ** (bits - whole))) - 1

    @staticmethod
    def target_to_difficulty(target: int) -> float:
        """The (possibly fractional) difficulty a numeric target represents.

        Inverse of ``difficulty_to_target``: ``difficulty = 64 - log16(target+1)``.
        For display/stats only -- never used in consensus validation.
        """
        try:
            return round(64 - math.log(int(target) + 1, 16), 2)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def hash_meets_target(block_hash: str, target: int) -> bool:
        try:
            return int(block_hash, 16) <= target
        except (TypeError, ValueError):
            return False

    def expected_target(self, next_index: int, chain=None) -> int:
        """Required proof-of-work target for the block at next_index.

        Below the fine-difficulty activation height this returns the target that
        is exactly equivalent to the legacy leading-zero difficulty, so historic
        blocks validate unchanged. At and above it, the target is retargeted
        smoothly (Bitcoin-style) by the ratio of actual to expected time, bounded
        to a 4x move per window and clamped to the configured difficulty range.
        """
        chain = self.chain if chain is None else chain
        activation = self.fine_difficulty_activation_height
        if next_index < activation:
            return self.difficulty_to_target(self.expected_difficulty(next_index, chain))

        interval = max(2, self.difficulty_adjustment_interval)
        easiest = self.difficulty_to_target(self.min_difficulty)   # largest target = difficulty floor
        # Seed from the configured starting difficulty (which may be fractional),
        # or, if unset, from the difficulty in force at the activation boundary.
        if self.fine_initial_difficulty > 0:
            target = self.difficulty_to_target(self.fine_initial_difficulty)
        else:
            target = self.difficulty_to_target(self.expected_difficulty(activation, chain))
        for boundary in range(activation + interval, next_index + 1, interval):
            if boundary > len(chain):
                continue
            window = chain[boundary - interval:boundary]
            if len(window) < interval:
                continue
            # Expected time for one window across its (interval - 1) gaps. The
            # per-block target lengthens (e.g. to 10 minutes) once the retarget
            # takes effect for blocks at/after its activation height.
            expected = max(1, self.fine_block_time_for_height(boundary) * max(1, interval - 1))
            elapsed = max(1, int(window[-1].timestamp - window[0].timestamp))
            # Average block time above target (elapsed > expected) -> a larger
            # target -> easier. Below target -> a smaller target -> harder. The
            # size of the move scales with elapsed/expected: the further from
            # target the average was, the bigger the change, up to a bounded max.
            factor = self.fine_max_adjust_factor
            adjusted = target * elapsed // expected
            adjusted = min(adjusted, target * factor)  # ease at most factor x per window
            adjusted = max(adjusted, target // factor)  # harden at most factor x per window
            # Floor difficulty at min_difficulty (largest target); no upper cap,
            # so difficulty can keep rising forever without manual changes.
            target = min(easiest, max(1, adjusted))
        return target

    def block_work(self, block: Block, chain_prefix=None) -> int:
        if block.index < self.fine_difficulty_activation_height:
            difficulty = self.expected_difficulty(block.index, chain_prefix or [])
            return 16 ** difficulty
        target = self.expected_target(block.index, chain_prefix or [])
        return MAX_HASH // (target + 1)

    def chain_work(self, chain=None) -> int:
        target_chain = self.chain if chain is None else chain
        # Cache the local chain's total work, keyed by (length, tip hash) — which
        # uniquely identifies the chain's contents — so the many comparisons during
        # a sync cycle don't each recompute it. Any append or reorg changes the tip
        # hash (or length) and invalidates the cache automatically.
        if target_chain is self.chain:
            tip = target_chain[-1].hash if target_chain else ""
            key = (len(target_chain), tip)
            if getattr(self, "_chain_work_key", None) == key:
                return self._chain_work_value
            value = sum(self.block_work(b, target_chain[:b.index]) for b in target_chain[1:])
            self._chain_work_key = key
            self._chain_work_value = value
            return value
        return sum(self.block_work(b, target_chain[:b.index]) for b in target_chain[1:])

    def set_checkpoints(self, checkpoints: dict) -> None:
        cleaned = {}
        for height, block_hash in (checkpoints or {}).items():
            try:
                cleaned[int(height)] = str(block_hash).lower()
            except (TypeError, ValueError):
                continue
        self.checkpoints = cleaned

    def update_auto_checkpoints(self) -> None:
        """Pin this node's own chain at a safe depth so a very deep reorg can't
        rewrite finalized history (local finality). Only interval-aligned blocks
        already ``auto_checkpoint_depth`` behind the tip are pinned, so honest
        short reorgs are never blocked. Persisted so it survives restarts."""
        interval = self.auto_checkpoint_interval
        depth = self.auto_checkpoint_depth
        if interval <= 0 or depth <= 0:
            return
        safe_height = (len(self.chain) - 1) - depth
        if safe_height <= 0:
            return
        pin = (safe_height // interval) * interval
        if pin <= 0 or pin >= len(self.chain):
            return
        block_hash = self.chain[pin].hash
        if self.checkpoints.get(pin) == block_hash:
            return
        self.checkpoints[pin] = block_hash
        self._save_auto_checkpoints()

    def _load_auto_checkpoints(self) -> None:
        try:
            raw = json.loads(self.auto_checkpoints_file.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return
        for height, block_hash in (raw or {}).items():
            try:
                self.checkpoints[int(height)] = str(block_hash).lower()
            except (TypeError, ValueError):
                continue

    def _save_auto_checkpoints(self) -> None:
        try:
            self.auto_checkpoints_file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.auto_checkpoints_file.with_suffix(self.auto_checkpoints_file.suffix + ".tmp")
            tmp.write_text(
                json.dumps({str(h): v for h, v in self.checkpoints.items()}, indent=2),
                encoding="utf-8")
            os.replace(tmp, self.auto_checkpoints_file)
        except OSError:
            pass

    def _checkpoint_valid(self, block: Block) -> bool:
        expected = self.checkpoints.get(block.index)
        return expected is None or block.hash == expected

    def prune_orphans(self, now=None) -> int:
        now = time.time() if now is None else float(now)
        expired = [h for h, item in self.orphan_blocks.items()
                   if now - item["received_at"] > self.orphan_ttl_seconds]
        for block_hash in expired:
            self.orphan_blocks.pop(block_hash, None)
        return len(expired)

    def add_orphan(self, block: Block) -> bool:
        self.prune_orphans()
        if block.hash in self.orphan_blocks or any(b.hash == block.hash for b in self.chain):
            return False
        if len(self.orphan_blocks) >= self.max_orphans:
            oldest = min(self.orphan_blocks, key=lambda h: self.orphan_blocks[h]["received_at"])
            self.orphan_blocks.pop(oldest, None)
        self.orphan_blocks[block.hash] = {"block": block, "received_at": time.time()}
        return True

    def _attach_orphans(self) -> list[Block]:
        attached = []
        while True:
            candidate_hash = next((h for h, item in self.orphan_blocks.items()
                                   if item["block"].previous_hash == self.chain[-1].hash), None)
            if candidate_hash is None:
                break
            candidate = self.orphan_blocks.pop(candidate_hash)["block"]
            valid, reason = self.validate_next_block(candidate)
            if not valid:
                continue
            self.chain.append(candidate)
            attached.append(candidate)
        return attached

    def verify_block(self, block):
        return self.validate_next_block(block)[0]

    def receive_block(self, block):
        return self.receive_block_detailed(block)[0]

    def receive_block_detailed(self, block):
        """Like receive_block, but also returns a human-readable reason so callers
        (e.g. the external-mining endpoint) can tell the miner exactly what
        happened instead of a vague "rejected" message."""
        with self._lock:
            if not self._checkpoint_valid(block):
                print(f"Rejected block {getattr(block, 'index', '?')}: checkpoint mismatch")
                return False, "checkpoint mismatch"
            if block.previous_hash != self.chain[-1].hash:
                if block.index > self.chain[-1].index:
                    self.add_orphan(block)
                    print(f"Stored orphan block {block.index}: parent not available")
                    return False, "parent block not available yet (stored as orphan)"
                return False, "stale: another block already extends this height"
            valid, reason = self.validate_next_block(block)
            if not valid:
                print(f"Rejected block {getattr(block, 'index', '?')}: {reason}")
                return False, reason
            self.chain.append(block)
            attached = self._attach_orphans()
            self._rebuild_indexes()
            mined_ids = {tx.tx_id for b in [block, *attached] for tx in b.transactions}
            self.pending_transactions = [
                tx for tx in self.pending_transactions if tx.tx_id not in mined_ids
            ]
            kept = []
            for tx in self.pending_transactions:
                if self._validate_pending_transaction(tx, kept):
                    kept.append(tx)
            self.pending_transactions = kept
            self.save()
            return True, None

    def replace_chain(self, new_chain):
        with self._lock:
            valid, reason = self.validate_chain(new_chain)
            if not valid:
                print(f"Rejected replacement chain: {reason}")
                return False
            for height, expected_hash in self.checkpoints.items():
                if height < len(new_chain) and new_chain[height].hash != expected_hash:
                    print(f"Rejected replacement chain: checkpoint {height} mismatch")
                    return False
            if self.chain_work(new_chain) <= self.chain_work(self.chain):
                return False

            old_chain = self.chain
            common = 0
            for i in range(min(len(old_chain), len(new_chain))):
                if old_chain[i].hash != new_chain[i].hash:
                    break
                common = i + 1

            confirmed_new = {tx.tx_id for b in new_chain for tx in b.transactions if tx.tx_id}
            detached = [tx for b in old_chain[common:] for tx in b.transactions
                        if tx.sender != "SYSTEM" and tx.tx_id not in confirmed_new]
            existing_pending = list(self.pending_transactions)
            self.chain = list(new_chain)
            self._rebuild_indexes()
            self.pending_transactions = []
            for tx in [*existing_pending, *detached]:
                if self._validate_pending_transaction(tx, self.pending_transactions):
                    self.pending_transactions.append(tx)
            self._attach_orphans()
            self.save()
            return True

    def consensus_status(self) -> dict:
        return {
            "height": len(self.chain) - 1,
            "chain_work": self.chain_work(),
            "next_difficulty": self.expected_difficulty(len(self.chain), self.chain),
            "orphans": len(self.orphan_blocks),
            "checkpoints": len(self.checkpoints),
        }

    def verify_chain_integrity(self):
        results = []
        for position, block in enumerate(self.chain):
            prefix = self.chain[: position + 1]
            ok, reason = self.validate_chain(prefix)
            results.append(
                {
                    "index": block.index,
                    "stored_hash": block.hash,
                    "calculated_hash": block.calculate_hash(),
                    "ok": ok,
                    "reason": None if ok else reason,
                }
            )
        return results

    def get_missing_indexes(self, peer_hashes: list) -> list:
        our_indexes = {b.index for b in self.chain}
        return [item["index"] for item in peer_hashes if item["index"] not in our_indexes]

    def get_differing_indexes(self, peer_hashes: list) -> list:
        our_map = {b.index: b.hash for b in self.chain}
        return [
            item["index"]
            for item in peer_hashes
            if item["index"] in our_map and our_map[item["index"]] != item["hash"]
        ]
