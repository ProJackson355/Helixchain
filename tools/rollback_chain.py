"""Safely roll a stopped Helix node back to an existing block height."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from node.blockchain import Blockchain


def atomic_json(path: Path, data: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".rollback.tmp")
    with temporary.open("w", encoding="utf-8") as output:
        json.dump(data, output, indent=4)
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, path)


def validate_state(state: dict, consensus: dict) -> tuple[int, str]:
    with tempfile.TemporaryDirectory(prefix="helix-rollback-check-") as directory:
        path = Path(directory) / "candidate.json"
        path.write_text(json.dumps(state), encoding="utf-8")
        validator = Blockchain({**consensus, "storage_backend": "json"}, path)
        valid, reason = validator.validate_chain(validator.chain)
        if not valid:
            raise RuntimeError(f"rollback candidate is invalid: {reason}")
        return validator.chain[-1].index, validator.chain[-1].hash


def rollback(root: Path, target_height: int, expected_tip: int) -> Path:
    config_path = root / "config.json"
    json_path = root / "database_8000.json"
    sqlite_path = root / "database_8000.sqlite3"
    checkpoint_path = root / "auto_checkpoints_database_8000.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))

    connection = sqlite3.connect(sqlite_path, timeout=30)
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        row = connection.execute("SELECT payload FROM state WHERE id = 1").fetchone()
        if row is None:
            raise RuntimeError("SQLite state row is missing")
        state = json.loads(row[0])
        current_height = len(state.get("chain", [])) - 1
        if current_height != expected_tip:
            raise RuntimeError(
                f"refusing rollback: expected tip {expected_tip}, found {current_height}"
            )
        if not 0 <= target_height < current_height:
            raise RuntimeError("target height must be below the current tip")

        removed = state["chain"][target_height + 1:]
        state["chain"] = state["chain"][:target_height + 1]
        # A raw rollback must not resurrect SYSTEM rewards. Eligible user
        # transactions can be resubmitted explicitly after reviewing the backup.
        state["pending"] = list(state.get("pending", []))
        height, tip_hash = validate_state(state, config["blockchain"])
        if height != target_height:
            raise RuntimeError("validated rollback height does not match the target")

        stamp = time.strftime("%Y%m%d-%H%M%S")
        backup = root / "backups" / f"rollback-{current_height}-to-{target_height}-{stamp}"
        backup.mkdir(parents=True, exist_ok=False)
        sqlite_backup = sqlite3.connect(backup / sqlite_path.name)
        try:
            connection.backup(sqlite_backup)
        finally:
            sqlite_backup.close()
        for source in (json_path, checkpoint_path, config_path):
            if source.exists():
                shutil.copy2(source, backup / source.name)
        (backup / "removed_blocks.json").write_text(
            json.dumps(removed, indent=2) + "\n", encoding="utf-8"
        )

        payload = json.dumps(state, sort_keys=True, separators=(",", ":"))
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "UPDATE state SET payload = ?, height = ?, tip_hash = ?, updated_at = ? WHERE id = 1",
            (payload, height, tip_hash, time.time()),
        )
        # Delete child rows explicitly as well as enabling foreign keys above.
        # Older databases may have been created or opened with FK enforcement
        # disabled, in which case relying on ON DELETE CASCADE leaves orphaned
        # transaction-index entries behind.
        connection.execute("DELETE FROM transaction_index WHERE block_height > ?", (height,))
        connection.execute("DELETE FROM block_index WHERE height > ?", (height,))
        connection.execute("DELETE FROM snapshots WHERE height > ?", (height,))
        connection.commit()
        atomic_json(json_path, state)
        return backup
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--target-height", type=int, required=True)
    parser.add_argument("--expected-tip", type=int, required=True)
    args = parser.parse_args()
    backup = rollback(args.root.resolve(), args.target_height, args.expected_tip)
    print(f"rollback complete; backup: {backup}")


if __name__ == "__main__":
    main()
