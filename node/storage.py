"""Transactional SQLite persistence for Helix node state.

The consensus objects remain JSON-compatible, while SQLite supplies atomic
commits, WAL recovery, schema migrations, and periodic point-in-time snapshots.
"""

from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path


SCHEMA_VERSION = 2


class SQLiteStateStore:
    def __init__(self, path: str | Path, *, snapshot_interval: int = 25, keep_snapshots: int = 20):
        self.path = Path(path)
        self.snapshot_interval = max(1, int(snapshot_interval))
        self.keep_snapshots = max(2, int(keep_snapshots))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._migrate()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _migrate(self) -> None:
        with self._connection() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations ("
                "version INTEGER PRIMARY KEY, applied_at REAL NOT NULL)"
            )
            version = connection.execute(
                "SELECT COALESCE(MAX(version), 0) FROM schema_migrations"
            ).fetchone()[0]
            if version < 1:
                connection.execute(
                    "CREATE TABLE state ("
                    "id INTEGER PRIMARY KEY CHECK (id = 1), payload TEXT NOT NULL, "
                    "height INTEGER NOT NULL, tip_hash TEXT NOT NULL, updated_at REAL NOT NULL)"
                )
                connection.execute(
                    "CREATE TABLE snapshots ("
                    "height INTEGER NOT NULL, tip_hash TEXT NOT NULL, payload TEXT NOT NULL, "
                    "created_at REAL NOT NULL, PRIMARY KEY(height, tip_hash))"
                )
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                    (1, time.time()),
                )
            if version < 2:
                connection.execute(
                    "CREATE TABLE IF NOT EXISTS block_index ("
                    "height INTEGER PRIMARY KEY, hash TEXT NOT NULL UNIQUE, "
                    "timestamp REAL NOT NULL, transaction_count INTEGER NOT NULL)"
                )
                connection.execute(
                    "CREATE TABLE IF NOT EXISTS transaction_index ("
                    "tx_id TEXT PRIMARY KEY, block_height INTEGER NOT NULL, position INTEGER NOT NULL, "
                    "sender TEXT NOT NULL, receiver TEXT NOT NULL, tx_type TEXT NOT NULL, "
                    "payload TEXT NOT NULL, FOREIGN KEY(block_height) REFERENCES block_index(height) "
                    "ON DELETE CASCADE)"
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS transaction_sender_idx "
                    "ON transaction_index(sender, block_height DESC)"
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS transaction_receiver_idx "
                    "ON transaction_index(receiver, block_height DESC)"
                )
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                    (2, time.time()),
                )

    def load(self) -> dict | None:
        with self._connection() as connection:
            row = connection.execute("SELECT payload FROM state WHERE id = 1").fetchone()
        return json.loads(row[0]) if row else None

    def save(self, data: dict, *, height: int, tip_hash: str) -> None:
        payload = json.dumps(data, sort_keys=True, separators=(",", ":"))
        now = time.time()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT INTO state(id, payload, height, tip_hash, updated_at) "
                "VALUES (1, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET "
                "payload=excluded.payload, height=excluded.height, "
                "tip_hash=excluded.tip_hash, updated_at=excluded.updated_at",
                (payload, int(height), str(tip_hash), now),
            )
            connection.execute("DELETE FROM block_index WHERE height > ?", (int(height),))
            for block in data.get("chain", []):
                block_height = int(block["index"])
                connection.execute(
                    "INSERT INTO block_index(height, hash, timestamp, transaction_count) "
                    "VALUES (?, ?, ?, ?) ON CONFLICT(height) DO UPDATE SET "
                    "hash=excluded.hash, timestamp=excluded.timestamp, "
                    "transaction_count=excluded.transaction_count",
                    (
                        block_height, block["hash"], float(block["timestamp"]),
                        len(block.get("transactions", [])),
                    ),
                )
                connection.execute(
                    "DELETE FROM transaction_index WHERE block_height = ?", (block_height,)
                )
                for position, transaction in enumerate(block.get("transactions", [])):
                    tx_id = transaction.get("tx_id")
                    if not tx_id:
                        continue
                    connection.execute(
                        "INSERT OR REPLACE INTO transaction_index("
                        "tx_id, block_height, position, sender, receiver, tx_type, payload) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            tx_id, block_height, position, transaction["sender"],
                            transaction["receiver"], transaction.get("tx_type", "transfer"),
                            json.dumps(transaction, sort_keys=True, separators=(",", ":")),
                        ),
                    )
            if height % self.snapshot_interval == 0:
                connection.execute(
                    "INSERT OR IGNORE INTO snapshots(height, tip_hash, payload, created_at) "
                    "VALUES (?, ?, ?, ?)",
                    (int(height), str(tip_hash), payload, now),
                )
                connection.execute(
                    "DELETE FROM snapshots WHERE rowid NOT IN ("
                    "SELECT rowid FROM snapshots ORDER BY height DESC, created_at DESC LIMIT ?)",
                    (self.keep_snapshots,),
                )

    def list_snapshots(self) -> list[dict]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT height, tip_hash, created_at FROM snapshots "
                "ORDER BY height DESC, created_at DESC"
            ).fetchall()
        return [
            {"height": row[0], "tip_hash": row[1], "created_at": row[2]}
            for row in rows
        ]

    def index_needs_rebuild(self, expected_height: int) -> bool:
        with self._connection() as connection:
            row = connection.execute("SELECT COALESCE(MAX(height), -1) FROM block_index").fetchone()
        return int(row[0]) != int(expected_height)

    def backup(self, destination: str | Path) -> Path:
        target_path = Path(destination)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as source:
            target = sqlite3.connect(target_path)
            try:
                source.backup(target)
            finally:
                target.close()
        return target_path
