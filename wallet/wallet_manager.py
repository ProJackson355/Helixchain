"""Versioned encrypted wallet storage with legacy migration support."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import tempfile
import time
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from wallet.wallet import Wallet

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
WALLET_FILE = Path(os.getenv("HELIX_WALLET_FILE", BASE_DIR / "wallets.json"))
LEGACY_WALLET_FILE = PROJECT_ROOT / "wallets.json"
PBKDF2_ITERATIONS = 390_000
SCRYPT_N = 2**15
SCRYPT_R = 8
SCRYPT_P = 1
RECORD_VERSION = 2


def _atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, sort_keys=True)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def _migrate_legacy_wallets() -> None:
    if not LEGACY_WALLET_FILE.exists() or LEGACY_WALLET_FILE == WALLET_FILE:
        return
    try:
        with LEGACY_WALLET_FILE.open("r", encoding="utf-8") as file:
            legacy = json.load(file)
    except (OSError, json.JSONDecodeError, TypeError):
        return
    wallets = load_wallets(skip_migration=True)
    changed = False
    for name, entry in legacy.items():
        if name not in wallets and isinstance(entry, dict):
            entry.setdefault("name", name)
            wallets[name] = entry
            changed = True
    if changed:
        save_wallets(wallets)
    backup_path = LEGACY_WALLET_FILE.with_suffix(LEGACY_WALLET_FILE.suffix + ".bak")
    if not backup_path.exists():
        os.replace(LEGACY_WALLET_FILE, backup_path)


def load_wallets(skip_migration: bool = False) -> dict:
    if not skip_migration:
        _migrate_legacy_wallets()
    if not WALLET_FILE.exists():
        return {}
    try:
        with WALLET_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_wallets(data: dict) -> None:
    _atomic_write(WALLET_FILE, data)


def _derive_key(password: str, salt: bytes, kdf: str = "scrypt", params: dict | None = None) -> bytes:
    if not isinstance(password, str) or not password:
        raise ValueError("password is required")
    params = params or {}
    if kdf == "pbkdf2-sha256":
        raw = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt,
            int(params.get("iterations", PBKDF2_ITERATIONS)), dklen=32,
        )
    elif kdf == "scrypt":
        raw = hashlib.scrypt(
            password.encode(), salt=salt,
            n=int(params.get("n", SCRYPT_N)),
            r=int(params.get("r", SCRYPT_R)),
            p=int(params.get("p", SCRYPT_P)), dklen=32, maxmem=128 * 1024 * 1024,
        )
    else:
        raise ValueError("unsupported wallet KDF")
    return base64.urlsafe_b64encode(raw)


def _store_wallet(name: str, wallet: Wallet, password: str, *, created_at: float | None = None) -> dict:
    salt = os.urandom(16)
    kdf_params = {"n": SCRYPT_N, "r": SCRYPT_R, "p": SCRYPT_P}
    encrypted_seed = Fernet(_derive_key(password, salt, "scrypt", kdf_params)).encrypt(
        wallet.seed_phrase.encode()
    )
    return {
        "version": RECORD_VERSION,
        "type": "encrypted",
        "name": name,
        "address": wallet.address,
        "account_index": wallet.account_index,
        "public_key": wallet.public_key_string(),
        "encrypted_seed": encrypted_seed.decode(),
        "salt": base64.b64encode(salt).decode(),
        "kdf": "scrypt",
        "kdf_params": kdf_params,
        "created_at": float(created_at or time.time()),
        "updated_at": time.time(),
    }


def _decrypt_seed(entry: dict, password: str) -> str | None:
    try:
        salt = base64.b64decode(entry["salt"])
        kdf = entry.get("kdf", "pbkdf2-sha256")
        params = entry.get("kdf_params", {"iterations": PBKDF2_ITERATIONS})
        return Fernet(_derive_key(password, salt, kdf, params)).decrypt(
            entry["encrypted_seed"].encode()
        ).decode()
    except (KeyError, ValueError, TypeError, InvalidToken):
        return None


def create_wallet(name: str, password: str, account_index: int = 0):
    wallets = load_wallets()
    if name in wallets:
        return None
    wallet = Wallet(account_index=account_index)
    wallets[name] = _store_wallet(name, wallet, password)
    save_wallets(wallets)
    print("\nRECOVERY PHRASE:\n" + wallet.seed_phrase + "\n")
    return wallet


def recover_wallet(name: str, seed_phrase: str, password: str, overwrite: bool = False, account_index: int = 0):
    wallets = load_wallets()
    if name in wallets and not overwrite:
        return None
    wallet = Wallet.from_seed_phrase(" ".join(seed_phrase.strip().split()), account_index)
    wallets[name] = _store_wallet(name, wallet, password)
    save_wallets(wallets)
    return wallet


def add_watch_only_wallet(name: str, address: str, public_key: str | None = None):
    wallets = load_wallets()
    if name in wallets or len(address) != 40 or any(c not in "0123456789abcdef" for c in address):
        return False
    wallets[name] = {
        "version": RECORD_VERSION,
        "type": "watch-only",
        "name": name,
        "address": address,
        "public_key": public_key,
        "created_at": time.time(),
        "updated_at": time.time(),
    }
    save_wallets(wallets)
    return True


def unlock_wallet(name: str, password: str):
    wallets = load_wallets()
    entry = wallets.get(name)
    if not entry or entry.get("type") == "watch-only":
        return None
    seed_phrase = _decrypt_seed(entry, password)
    if seed_phrase is None:
        return None
    wallet = Wallet.from_seed_phrase(seed_phrase, int(entry.get("account_index", 0)))
    if wallet.address != entry.get("address"):
        return None
    # Successful unlock transparently upgrades legacy PBKDF2 records.
    if entry.get("version", 1) < RECORD_VERSION or entry.get("kdf") != "scrypt":
        wallets[name] = _store_wallet(name, wallet, password, created_at=entry.get("created_at"))
        save_wallets(wallets)
    return wallet


def change_wallet_password(name: str, old_password: str, new_password: str) -> bool:
    wallet = unlock_wallet(name, old_password)
    if wallet is None:
        return False
    wallets = load_wallets()
    old = wallets[name]
    wallets[name] = _store_wallet(name, wallet, new_password, created_at=old.get("created_at"))
    save_wallets(wallets)
    return True


def delete_wallet(name: str, password: str | None = None) -> bool:
    wallets = load_wallets()
    entry = wallets.get(name)
    if entry is None:
        return False
    if entry.get("type") != "watch-only" and unlock_wallet(name, password or "") is None:
        return False
    wallets = load_wallets()
    wallets.pop(name, None)
    save_wallets(wallets)
    return True


def export_wallet_backup(destination: str) -> str:
    destination_path = Path(destination).expanduser().resolve()
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    if WALLET_FILE.exists():
        shutil.copy2(WALLET_FILE, destination_path)
    else:
        _atomic_write(destination_path, {})
    return str(destination_path)


def get_wallet_address(name: str):
    entry = load_wallets().get(name)
    return entry.get("address") if entry else None


def get_wallet_info(name: str):
    entry = load_wallets().get(name)
    if not entry:
        return None
    return {key: value for key, value in entry.items() if key not in {"encrypted_seed", "salt", "kdf_params"}}


def list_wallets(detailed: bool = False):
    wallets = load_wallets()
    if not detailed:
        return list(wallets.keys())
    return [
        {"name": name, "address": entry.get("address"), "type": entry.get("type", "encrypted")}
        for name, entry in wallets.items()
    ]
