import hashlib
import json
import time
from decimal import Decimal, InvalidOperation
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


class Transaction:
    """A signed value transfer.

    Normal transactions are signed by the sender. Protocol reward transactions
    use sender == "SYSTEM" and are created and validated only by Blockchain.
    """

    TOKEN_TYPES = {
        "token_create", "token_mint", "token_transfer", "token_set_authority",
        "token_pool_create", "token_pool_add_hlx", "token_buy", "token_sell", "token_swap",
    }
    ZERO_AMOUNT_TYPES = {"token_create", "token_set_authority"}

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
        if self.tx_type != "transfer":
            payload.update({
                "tx_type": self.tx_type,
                "mint_address": self.mint_address,
                "nonce": self.nonce,
            })
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

    def calculate_id(self) -> str:
        raw = self.data()
        if self.signature:
            raw += self.signature
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
        self.signature = signature.hex()
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
        # Keep legacy transfers and mining rewards byte-for-byte compatible
        # with existing block hashes. Token fields exist only on token records.
        if self.tx_type != "transfer":
            data.update({
                "tx_type": self.tx_type,
                "mint_address": self.mint_address,
                "nonce": self.nonce,
            })
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
