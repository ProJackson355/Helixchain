import hashlib
import json
import time
from decimal import Decimal, InvalidOperation
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import (
    decode_dss_signature,
    encode_dss_signature,
)


SECP256K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


class Transaction:
    """A signed value transfer.

    Normal transactions are signed by the sender. Protocol reward transactions
    use sender == "SYSTEM" and are created and validated only by Blockchain.
    """

    TOKEN_TYPES = {
        "token_create", "token_mint", "token_burn", "token_transfer", "token_set_authority",
        "token_pool_create", "token_pool_add_hlx", "token_buy", "token_sell", "token_swap",
    }
    # ERC-721-style non-fungible tokens: each is a unique asset with an explicit
    # owner (not a fungible balance). Minted by a creator, transferred by the owner.
    NFT_TYPES = {
        "nft_mint", "nft_transfer", "nft_list", "nft_cancel_listing",
        "nft_bid", "nft_cancel_bid", "nft_accept_bid", "nft_buy",
        "nft_set_royalty",
    }
    ZERO_AMOUNT_TYPES = {
        "token_create", "token_set_authority", "nft_mint", "nft_transfer",
        "nft_cancel_listing", "nft_cancel_bid", "nft_accept_bid",
        "nft_set_royalty", "cancel",
    }

    def __init__(
        self,
        sender: str,
        receiver: str,
        amount: int,
        public_key=None,
        received_at=None,
        *,
        tx_type: str = "transfer",
        mint_address: str | None = None,
        dad_address: str | None = None,
        nonce: str | None = None,
        name: str | None = None,
        symbol: str | None = None,
        description: str | None = None,
        image: str | None = None,
        metadata_hash: str | None = None,
        decimals: int | None = None,
        uri: str | None = None,
        hlx_amount: int | None = None,
        min_receive: int | None = None,
        target_mint_address: str | None = None,
        nft_id: str | None = None,
        attributes: list | None = None,
        royalty_bps: int | None = None,
        fee: int | None = None,
        chain_id: str | None = None,
        sequence: int | None = None,
        valid_until_height: int | None = None,
    ):
        if isinstance(amount, bool):
            raise ValueError("amount must be an integer")

        if sender == "SYSTEM" and (
            isinstance(amount, Decimal)
            or (isinstance(amount, str) and "." in amount)
        ):
            try:
                parsed_decimal = Decimal(str(amount))
            except InvalidOperation as exc:
                raise ValueError("reward amount must be a canonical decimal") from exc
            canonical = format(parsed_decimal, "f")
            if (
                not parsed_decimal.is_finite()
                or parsed_decimal < 0
                or parsed_decimal.as_tuple().exponent < -3
                or (isinstance(amount, str) and amount.strip() != canonical)
            ):
                raise ValueError("reward amount must be a canonical decimal with at most 3 places")
            self.sender = sender
            self.receiver = receiver
            self.amount = parsed_decimal
        else:
            try:
                parsed_amount = int(amount)
            except (TypeError, ValueError) as exc:
                raise ValueError("amount must be an integer") from exc

            # Do not silently accept 1.5 as 1.
            if isinstance(amount, float) and not amount.is_integer():
                raise ValueError("fractional amounts are not supported")
            if isinstance(amount, str) and amount.strip() != str(parsed_amount):
                raise ValueError("amount must be a canonical integer")
            self.sender = sender
            self.receiver = receiver
            self.amount = parsed_amount
        self.tx_type = str(tx_type or "transfer")
        self.mint_address = mint_address
        self.dad_address = dad_address
        self.nonce = nonce
        self.name = name
        self.symbol = symbol
        self.description = description
        self.image = image
        self.metadata_hash = metadata_hash
        self.decimals = decimals
        self.uri = uri
        def optional_integer(value, label):
            if value is None:
                return None
            if isinstance(value, bool):
                raise ValueError(f"{label} must be an integer")
            try:
                parsed = int(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{label} must be an integer") from exc
            if isinstance(value, float) and not value.is_integer():
                raise ValueError(f"{label} must be an integer")
            if isinstance(value, str) and value.strip() != str(parsed):
                raise ValueError(f"{label} must be a canonical integer")
            return parsed

        self.hlx_amount = optional_integer(hlx_amount, "hlx_amount")
        self.min_receive = optional_integer(min_receive, "min_receive")
        self.target_mint_address = target_mint_address
        self.nft_id = nft_id
        self.attributes = attributes if isinstance(attributes, list) else None
        self.royalty_bps = optional_integer(royalty_bps, "royalty_bps")
        self.fee = optional_integer(fee, "fee")
        self.chain_id = None if chain_id is None else str(chain_id)
        self.sequence = optional_integer(sequence, "sequence")
        self.valid_until_height = optional_integer(
            valid_until_height, "valid_until_height"
        )
        self.public_key = public_key
        self.signature = None
        self.tx_id = None
        self.received_at = time.time() if received_at is None else float(received_at)

    def data(self) -> str:
        payload = {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.serialized_amount(self.amount),
        }
        # Transactions confirmed before the fee upgrade did not serialize this
        # field. Omit None so their signatures, IDs, and block hashes stay exact.
        if self.fee is not None:
            payload["fee"] = self.fee
        # Protocol-15 envelope fields are omitted from historical records so
        # every pre-upgrade transaction signature and block hash stays exact.
        if self.chain_id is not None:
            payload["chain_id"] = self.chain_id
        if self.sequence is not None:
            payload["sequence"] = self.sequence
        if self.valid_until_height is not None:
            payload["valid_until_height"] = self.valid_until_height
        if self.tx_type == "cancel":
            payload["tx_type"] = self.tx_type
        elif self.tx_type != "transfer" and self.tx_type not in self.NFT_TYPES:
            payload.update({
                "tx_type": self.tx_type,
                "mint_address": self.mint_address,
                "nonce": self.nonce,
            })
        if self.tx_type in self.NFT_TYPES:
            payload.update({
                "tx_type": self.tx_type,
                "nft_id": self.nft_id,
                "nonce": self.nonce,
            })
        if self.tx_type == "nft_mint":
            payload.update({
                "name": self.name,
                "description": self.description,
                "image": self.image,
                "uri": self.uri or "",
                "metadata_hash": self.metadata_hash,
                "attributes": self.attributes or [],
                "royalty_bps": self.royalty_bps or 0,
            })
        if self.tx_type == "nft_set_royalty":
            payload["royalty_bps"] = self.royalty_bps
        if self.tx_type == "token_create":
            payload.update({
                "dad_address": self.dad_address,
                "name": self.name,
                "symbol": self.symbol,
                "decimals": self.decimals,
                "uri": self.uri or "",
            })
            # Token mints created before protocol 4 did not contain the
            # metadata snapshot fields. Omitting them when all three are
            # absent preserves those transactions' signatures and IDs.
            if any(value is not None for value in (
                self.description, self.image, self.metadata_hash
            )):
                payload.update({
                    "description": self.description,
                    "image": self.image,
                    "metadata_hash": self.metadata_hash,
                })
        if self.tx_type == "token_pool_create":
            payload["hlx_amount"] = self.hlx_amount
        if self.tx_type in {"token_buy", "token_sell", "token_swap"}:
            payload["min_receive"] = self.min_receive
        if self.tx_type == "token_swap":
            payload["target_mint_address"] = self.target_mint_address
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def mint_address(creator: str, nonce: str) -> str:
        """Return the deterministic MNT address for a token creation."""
        return hashlib.sha256(
            f"helix-token-mint:{creator}:{nonce}".encode()
        ).hexdigest()[:40]

    @staticmethod
    def associated_token_address(owner: str, mint_address: str) -> str:
        """Derive the default holding account for one owner and MNT pair."""
        return hashlib.sha256(
            f"helix-associated-token:{owner}:{mint_address}".encode()
        ).hexdigest()[:40]

    @staticmethod
    def token_metadata_hash(name: str, symbol: str, description: str, image: str) -> str:
        metadata = {
            "name": name,
            "symbol": symbol,
            "description": description,
            "image": image,
        }
        encoded = json.dumps(
            metadata, sort_keys=True, separators=(",", ":")
        ).encode()
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def nft_address(creator: str, nonce: str) -> str:
        """Deterministic unique ID for a minted NFT (like an ERC-721 token id)."""
        return hashlib.sha256(
            f"helix-nft:{creator}:{nonce}".encode()
        ).hexdigest()[:40]

    @staticmethod
    def nft_metadata_hash(name, description, image, attributes) -> str:
        metadata = {
            "name": name,
            "description": description,
            "image": image,
            "attributes": attributes or [],
        }
        encoded = json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

    def calculate_id(self) -> str:
        raw = self.data()
        if self.signature:
            raw += self.signature
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def canonical_signature_hex(signature: str) -> str:
        """Normalize an ECDSA signature to its unique low-S representation."""
        r, s = decode_dss_signature(bytes.fromhex(signature))
        if not 1 <= r < SECP256K1_ORDER or not 1 <= s < SECP256K1_ORDER:
            raise ValueError("signature scalar is outside the secp256k1 range")
        if s > SECP256K1_ORDER // 2:
            s = SECP256K1_ORDER - s
        return encode_dss_signature(r, s).hex()

    def signature_is_canonical(self) -> bool:
        try:
            return bool(self.signature) and self.signature == self.canonical_signature_hex(self.signature)
        except (TypeError, ValueError):
            return False

    def canonical_id(self) -> str:
        """ID shared by the low-S and high-S forms of the same signature."""
        raw = self.data()
        if self.signature:
            raw += self.canonical_signature_hex(self.signature)
        return hashlib.sha256(raw.encode()).hexdigest()

    def generate_id(self) -> str:
        self.tx_id = self.calculate_id()
        return self.tx_id

    @staticmethod
    def serialized_amount(amount):
        """Return a JSON-safe amount while preserving legacy integer hashes."""
        if isinstance(amount, Decimal):
            if amount == amount.to_integral_value():
                return int(amount)
            return format(amount, "f")
        return amount

    @staticmethod
    def reward_id(block_index: int, receiver: str, amount, previous_hash: str) -> str:
        """Create a unique, deterministic ID for a protocol reward."""
        raw = json.dumps(
            {
                "type": "coinbase",
                "block_index": block_index,
                "receiver": receiver,
                "amount": Transaction.serialized_amount(amount),
                "previous_hash": previous_hash,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(raw.encode()).hexdigest()

    def sign(self, private_key) -> None:
        if self.sender == "SYSTEM":
            raise ValueError("SYSTEM transactions cannot be signed by wallets")
        if self.amount < 0 or (self.amount == 0 and self.tx_type not in self.ZERO_AMOUNT_TYPES):
            raise ValueError("amount must be greater than zero")

        signature = private_key.sign(
            self.data().encode(),
            ec.ECDSA(hashes.SHA256()),
        )
        self.signature = self.canonical_signature_hex(signature.hex())
        self.generate_id()

    def address_from_public_key(self) -> str:
        if self.public_key is None:
            raise ValueError("public key is missing")
        public_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.CompressedPoint,
        )
        return hashlib.sha256(public_bytes).hexdigest()[:40]

    def verify_signature(self) -> bool:
        if self.sender == "SYSTEM":
            return False
        if (
            self.amount < 0
            or (self.amount == 0 and self.tx_type not in self.ZERO_AMOUNT_TYPES)
            or not self.signature
            or self.public_key is None
        ):
            return False

        try:
            if self.address_from_public_key() != self.sender:
                return False
            self.public_key.verify(
                bytes.fromhex(self.signature),
                self.data().encode(),
                ec.ECDSA(hashes.SHA256()),
            )
            return True
        except (ValueError, TypeError, InvalidSignature, AttributeError):
            return False

    def to_dict(self) -> dict[str, Any]:
        public_key = None
        if self.public_key is not None:
            if isinstance(self.public_key, str):
                public_key = self.public_key
            else:
                public_key = self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                ).decode()

        data = {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.serialized_amount(self.amount),
            "signature": self.signature,
            "tx_id": self.tx_id,
            "public_key": public_key,
        }
        if self.fee is not None:
            data["fee"] = self.fee
        if self.chain_id is not None:
            data["chain_id"] = self.chain_id
        if self.sequence is not None:
            data["sequence"] = self.sequence
        if self.valid_until_height is not None:
            data["valid_until_height"] = self.valid_until_height
        # Keep legacy transfers and mining rewards byte-for-byte compatible
        # with existing block hashes. Token fields exist only on token records.
        if self.tx_type == "cancel":
            data["tx_type"] = self.tx_type
        elif self.tx_type != "transfer" and self.tx_type not in self.NFT_TYPES:
            data.update({
                "tx_type": self.tx_type,
                "mint_address": self.mint_address,
                "nonce": self.nonce,
            })
        if self.tx_type in self.NFT_TYPES:
            data.update({
                "tx_type": self.tx_type,
                "nft_id": self.nft_id,
                "nonce": self.nonce,
            })
        if self.tx_type == "nft_mint":
            data.update({
                "name": self.name,
                "description": self.description,
                "image": self.image,
                "uri": self.uri or "",
                "metadata_hash": self.metadata_hash,
                "attributes": self.attributes or [],
                "royalty_bps": self.royalty_bps or 0,
            })
        if self.tx_type == "nft_set_royalty":
            data["royalty_bps"] = self.royalty_bps
        if self.tx_type == "token_create":
            data.update({
                "dad_address": self.dad_address,
                "name": self.name,
                "symbol": self.symbol,
                "decimals": self.decimals,
                "uri": self.uri or "",
            })
            # Preserve the exact serialized form of pre-protocol-4 mints so
            # loading them cannot alter an existing block hash.
            if any(value is not None for value in (
                self.description, self.image, self.metadata_hash
            )):
                data.update({
                    "description": self.description,
                    "image": self.image,
                    "metadata_hash": self.metadata_hash,
                })
        if self.tx_type == "token_pool_create":
            data["hlx_amount"] = self.hlx_amount
        if self.tx_type in {"token_buy", "token_sell", "token_swap"}:
            data["min_receive"] = self.min_receive
        if self.tx_type == "token_swap":
            data["target_mint_address"] = self.target_mint_address
        return data
