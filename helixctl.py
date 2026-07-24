"""Administrative utility for local Helix node data and configuration."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = Path(os.getenv("HELIX_CONFIG", ROOT / "config.json"))


def load_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"Could not read {CONFIG_PATH}: {exc}")


def database_path(config: dict) -> Path:
    port = os.getenv("NODE_PORT", str(config.get("node", {}).get("port", 8000)))
    return Path(os.getenv("HELIX_DATABASE", ROOT / f"database_{port}.json"))


def command_status(config: dict) -> int:
    db = database_path(config)
    result = {
        "version": config.get("node", {}).get("version"),
        "network": config.get("node", {}).get("network"),
        "protocol": config.get("node", {}).get("protocol"),
        "database": str(db),
        "database_exists": db.exists(),
        "database_bytes": db.stat().st_size if db.exists() else 0,
    }
    if db.exists():
        try:
            data = json.loads(db.read_text(encoding="utf-8"))
            result.update({
                "height": max(-1, len(data.get("chain", [])) - 1),
                "pending_transactions": len(data.get("pending", [])),
            })
        except (OSError, ValueError):
            result["database_valid_json"] = False
    print(json.dumps(result, indent=2))
    return 0


def command_validate(config: dict) -> int:
    os.environ.setdefault("HELIX_CONFIG", str(CONFIG_PATH))
    os.environ.setdefault("HELIX_DATABASE", str(database_path(config)))
    from node.blockchain import Blockchain
    chain = Blockchain(config.get("blockchain", {}), database_path(config))
    results = chain.verify_chain_integrity()
    valid = all(item.get("ok") for item in results)
    reason = next((item.get("reason") for item in results if not item.get("ok")), None)
    print(json.dumps({
        "valid": valid,
        "reason": reason,
        "height": len(chain.chain) - 1,
        "chain_work": chain.chain_work(),
        "transactions_indexed": len(chain._transaction_index),
        "blocks_checked": len(results),
    }, indent=2))
    return 0 if valid else 1


def command_backup(config: dict, destination: str | None) -> int:
    source = database_path(config)
    if not source.is_file():
        raise SystemExit(f"Database not found: {source}")
    target_dir = Path(destination or ROOT / "backups")
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{source.stem}-{time.strftime('%Y%m%d-%H%M%S')}{source.suffix}"
    shutil.copy2(source, target)
    print(target)
    return 0


def command_compact(config: dict) -> int:
    db = database_path(config)
    if not db.is_file():
        raise SystemExit(f"Database not found: {db}")
    data = json.loads(db.read_text(encoding="utf-8"))
    temporary = db.with_suffix(db.suffix + ".compact")
    temporary.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    os.replace(temporary, db)
    print(json.dumps({"database": str(db), "bytes": db.stat().st_size}, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="helixctl", description="Helix node maintenance utility")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="Show local configuration and database status")
    sub.add_parser("validate", help="Validate the complete local blockchain")
    backup = sub.add_parser("backup", help="Create a timestamped database backup")
    backup.add_argument("destination", nargs="?", help="Backup directory")
    sub.add_parser("compact", help="Rewrite the JSON database without indentation")
    args = parser.parse_args()
    config = load_config()
    return {
        "status": lambda: command_status(config),
        "validate": lambda: command_validate(config),
        "backup": lambda: command_backup(config, args.destination),
        "compact": lambda: command_compact(config),
    }[args.command]()


if __name__ == "__main__":
    sys.exit(main())
