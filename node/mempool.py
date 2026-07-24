import threading
import time
from dataclasses import dataclass, asdict


@dataclass
class RelayRecord:
    tx_id: str
    first_seen: float
    last_seen: float
    last_broadcast: float = 0.0
    relay_count: int = 0


class MempoolRelay:
    """Tracks transaction gossip state without owning consensus validation.

    Blockchain remains the source of truth for which pending transactions are
    valid. This helper only prevents relay loops, expires stale relay metadata,
    and determines when a transaction should be rebroadcast.
    """

    def __init__(self, ttl_seconds: int = 3600, rebroadcast_seconds: int = 60):
        self.ttl_seconds = max(60, int(ttl_seconds))
        self.rebroadcast_seconds = max(5, int(rebroadcast_seconds))
        self._records: dict[str, RelayRecord] = {}
        self._lock = threading.RLock()

    def mark_seen(self, tx_id: str, now: float | None = None) -> bool:
        """Return True only the first time a transaction ID is observed."""
        if not tx_id:
            return False
        timestamp = time.time() if now is None else float(now)
        with self._lock:
            record = self._records.get(tx_id)
            if record is None:
                self._records[tx_id] = RelayRecord(tx_id, timestamp, timestamp)
                return True
            record.last_seen = timestamp
            return False

    def mark_broadcast(self, tx_id: str, now: float | None = None) -> None:
        timestamp = time.time() if now is None else float(now)
        with self._lock:
            record = self._records.get(tx_id)
            if record is None:
                record = RelayRecord(tx_id, timestamp, timestamp)
                self._records[tx_id] = record
            record.last_broadcast = timestamp
            record.relay_count += 1

    def should_rebroadcast(self, tx_id: str, now: float | None = None) -> bool:
        timestamp = time.time() if now is None else float(now)
        with self._lock:
            record = self._records.get(tx_id)
            if record is None:
                return True
            return timestamp - record.last_broadcast >= self.rebroadcast_seconds

    def expire(self, active_tx_ids: set[str], now: float | None = None) -> list[str]:
        """Drop relay records no longer active or older than the configured TTL."""
        timestamp = time.time() if now is None else float(now)
        removed = []
        with self._lock:
            for tx_id, record in list(self._records.items()):
                inactive = tx_id not in active_tx_ids
                stale = timestamp - record.first_seen >= self.ttl_seconds
                if inactive or stale:
                    removed.append(tx_id)
                    self._records.pop(tx_id, None)
        return removed

    def inventory(self, active_tx_ids: set[str]) -> list[str]:
        with self._lock:
            return sorted(tx_id for tx_id in active_tx_ids if tx_id in self._records)

    def stats(self) -> dict:
        with self._lock:
            return {
                "tracked": len(self._records),
                "ttl_seconds": self.ttl_seconds,
                "rebroadcast_seconds": self.rebroadcast_seconds,
                "records": [asdict(record) for record in self._records.values()],
            }
