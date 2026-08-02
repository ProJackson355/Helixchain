"""Rebuild the three downloadable Helix packages reproducibly."""

from __future__ import annotations

import os
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "web" / "downloads"

COMMON = ["gui_branding.py", ("web/icons/icon-192.png", "helix-logo.png")]
PACKAGES = {
    "helix-miner.zip": [
        ("web/downloads/HELIX_MINER_README.md", "README.md"),
        ("web/downloads/HelixMiner.exe", "HelixMiner.exe"),
        "miner_cuda.py", "requirements.txt", "requirements-nvidia.txt",
        "helix_miner.py", "helix_miner_cli.py", *COMMON,
    ],
    "helix-pool.zip": [
        ("web/downloads/HELIX_POOL_README.md", "README.md"),
        "node/transaction.py", "node/__init__.py", "wallet/seed.py",
        "wallet/wallet.py", "wallet/__init__.py", "install_pool.py", "LICENSE",
        "pool.env.example", "pool_server.py", "requirements.txt", "run_pool.py",
        "setup-pool.bat", "start-pool.sh", *COMMON,
    ],
    "helix-node.zip": [
        ("web/downloads/HELIX_NODE_README.md", "INSTALL.md"),
        ("web/downloads/HelixNodeSetup.exe", "HelixNodeSetup.exe"),
        "node/blockchain.py", "node/bootstrap.py", "node/mempool.py", "node/node.py",
        "node/node_manager.py", "node/peer_health.py", "node/peer_manager.py",
        "node/pool_registry.py", "node/security.py", "node/storage.py",
        "node/submissions.py", "node/transaction.py", "node/__init__.py",
        "wallet/cli.py", "wallet/network.py", "wallet/seed.py", "wallet/wallet.py",
        "wallet/wallet_manager.py", "wallet/__init__.py", "web/app.js", "web/index.html",
        "web/jsqr.js", "web/manifest.webmanifest", "web/pwa.js", "web/qrcode.js",
        "web/secp256k1.js", "web/sw.js", "web/token-metadata.example.json",
        "web/_headers", "web/_worker.js", "web/icons/icon-192.png",
        "web/icons/icon-512.png", "web/icons/icon-maskable-512.png", "config.json",
        "helixctl.py", "install_node.py", "LICENSE", "PLAN.md", "pool_server.py",
        "pyproject.toml", "README.md", "requirements.txt", "run_node.py", "run_pool.py",
        "SECURITY_AUDIT_2026-07-27.md", "setup.bat", "start-node.bat",
        "start-node.sh", "tools/release_manifest.py", *COMMON,
    ],
}


def build(name: str, entries: list) -> Path:
    target = OUTPUT / name
    temporary = target.with_suffix(target.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for entry in entries:
            source_name, archive_name = entry if isinstance(entry, tuple) else (entry, entry)
            source = ROOT / source_name
            if not source.is_file():
                raise FileNotFoundError(source)
            archive.write(source, archive_name)
    os.replace(temporary, target)
    return target


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for package, entries in PACKAGES.items():
        target = build(package, entries)
        print(f"built {target.relative_to(ROOT)} ({target.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
