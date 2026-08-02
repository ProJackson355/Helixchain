"""Deterministic Helix wallet keys and addresses."""

from __future__ import annotations

import hashlib
import hmac

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from wallet.seed import generate_phrase, phrase_to_private_key

_CURVE_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


class Wallet:
    """A deterministic secp256k1 wallet.

    Account index 0 intentionally uses the original Helix derivation so every
    wallet created before Step 5 keeps exactly the same private key and address.
    Additional account indexes are deterministically derived from the same seed.
    """

    def __init__(self, seed_phrase: str | None = None, account_index: int = 0):
        if seed_phrase is None:
            seed_phrase = generate_phrase()
        seed_phrase = " ".join(seed_phrase.strip().split())
        if not seed_phrase:
            raise ValueError("seed phrase is required")
        if isinstance(account_index, bool) or int(account_index) < 0:
            raise ValueError("account index must be a non-negative integer")

        self.seed_phrase = seed_phrase
        self.account_index = int(account_index)
        root = phrase_to_private_key(seed_phrase)
        if self.account_index == 0:
            private_key_bytes = root
        else:
            private_key_bytes = hmac.new(
                root,
                f"helix/account/{self.account_index}".encode(),
                hashlib.sha256,
            ).digest()

        private_key_int = int.from_bytes(private_key_bytes, "big") % (_CURVE_ORDER - 1) + 1
        self.private_key = ec.derive_private_key(private_key_int, ec.SECP256K1())
        self.public_key = self.private_key.public_key()
        self.address = self.generate_address()

    def generate_address(self) -> str:
        public_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.CompressedPoint,
        )
        return hashlib.sha256(public_bytes).hexdigest()[:40]

    def private_key_string(self) -> str:
        return self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()

    def public_key_string(self) -> str:
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

    @staticmethod
    def from_seed_phrase(seed_phrase: str, account_index: int = 0) -> "Wallet":
        return Wallet(seed_phrase, account_index=account_index)

    @classmethod
    def from_web_seed_phrase(cls, seed_phrase: str) -> "Wallet":
        """Reproduce the browser wallet's original Helix seed derivation.

        Browser wallets choose 12 entries from the BIP-39 word list without a
        BIP-39 checksum, then use PBKDF2-SHA256 with the fixed Helix salt.  This
        is intentionally separate from ``from_seed_phrase`` so existing Python
        BIP-39 wallets retain their original addresses.
        """
        normalized = " ".join(seed_phrase.strip().split())
        if not normalized:
            raise ValueError("seed phrase is required")
        private_key_bytes = hashlib.pbkdf2_hmac(
            "sha256", normalized.encode(), b"helix-wallet-v1", 100_000, dklen=32
        )
        private_key_int = int.from_bytes(private_key_bytes, "big")
        if not 1 <= private_key_int < _CURVE_ORDER:
            raise ValueError("derived browser wallet key is outside the secp256k1 range")
        wallet = cls.__new__(cls)
        wallet.seed_phrase = normalized
        wallet.account_index = 0
        wallet.private_key = ec.derive_private_key(private_key_int, ec.SECP256K1())
        wallet.public_key = wallet.private_key.public_key()
        wallet.address = wallet.generate_address()
        return wallet
