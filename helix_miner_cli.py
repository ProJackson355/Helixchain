"""Headless command-line interface for Helix Miner.

Solo CPU example::

    python helix_miner_cli.py --address 0123456789abcdef0123456789abcdef01234567

Pool example::

    python helix_miner_cli.py --address ADDRESS --pool https://pool.example.com
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
import os
import signal
import sys
import threading
import time

from helix_miner import ADDRESS_RE, DEFAULT_NODE, HelixMinerApp, parse_node_urls


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mine Helix from a terminal using local CPU or NVIDIA hardware.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--address", required=True,
        help="40-character Helix reward wallet address",
    )
    parser.add_argument(
        "--nodes", default=DEFAULT_NODE,
        help="solo node URL, comma-separated URLs, or a JSON URL array",
    )
    parser.add_argument(
        "--pool", default="",
        help="pool URL; when supplied, pool mode replaces solo mode",
    )
    parser.add_argument(
        "--threads", type=int, default=max(1, min(2, os.cpu_count() or 1)),
        help="CPU worker-process count",
    )
    parser.add_argument(
        "--backend", choices=("cpu", "nvidia"), default="cpu",
        help="mining backend; NVIDIA requires the optional CuPy package",
    )
    parser.add_argument(
        "--status-interval", type=float, default=5.0,
        help="seconds between terminal hash-rate updates",
    )
    return parser


def validated_settings(args: argparse.Namespace, parser: argparse.ArgumentParser) -> dict:
    address = args.address.strip().lower()
    if ADDRESS_RE.fullmatch(address) is None:
        parser.error("--address must contain exactly 40 hexadecimal characters")

    cpu_count = max(1, os.cpu_count() or 1)
    if not 1 <= args.threads <= cpu_count:
        parser.error(f"--threads must be between 1 and {cpu_count}")
    if args.status_interval < 0.5:
        parser.error("--status-interval must be at least 0.5 seconds")

    try:
        nodes = parse_node_urls(args.nodes)
        pool_urls = parse_node_urls(args.pool) if args.pool.strip() else []
    except ValueError as exc:
        parser.error(str(exc))
    if len(pool_urls) > 1:
        parser.error("--pool accepts exactly one pool URL")
    pool_url = pool_urls[0] if pool_urls else ""

    return {
        "address": address,
        "nodes": nodes,
        "pool_url": pool_url,
        "threads": args.threads,
        "backend": args.backend,
        "status_interval": args.status_interval,
    }


class HelixMinerCLI(HelixMinerApp):
    """Use the shared mining engine while replacing all Tk events with output."""

    def __init__(self, status_interval: float = 5.0):
        # Deliberately do not call HelixMinerApp.__init__: the CLI owns no window
        # and remains usable on servers where tkinter is not installed.
        self.stop_event = threading.Event()
        self.round_stop = None
        self.shares = 0
        self.wins = 0
        self.status_interval = status_interval
        self._last_status = None
        self._last_stats = None
        self._last_performance = 0.0

    @staticmethod
    def _write(label: str, message: str) -> None:
        stamp = time.strftime("%H:%M:%S")
        print(f"[{stamp}] {label:<7} {message}", flush=True)

    def emit(self, kind, value):
        if kind == "log":
            self._write("LOG", str(value))
        elif kind == "status":
            if value != self._last_status:
                self._last_status = value
                self._write("STATUS", str(value))
        elif kind == "stats":
            snapshot = (
                value.get("height", "-"),
                value.get("difficulty", "-"),
                value.get("reward", "-"),
            )
            if snapshot != self._last_stats:
                self._last_stats = snapshot
                self._write(
                    "NETWORK",
                    f"height {snapshot[0]} | difficulty {snapshot[1]} | reward {snapshot[2]} HLX",
                )
        elif kind == "performance":
            now = time.monotonic()
            if now - self._last_performance >= self.status_interval:
                self._last_performance = now
                hashes, rate = value
                self._write("RATE", f"{self._format_rate(rate)} | {hashes:,} hashes this round")
        elif kind == "height":
            self._write("NETWORK", f"chain advanced to height {value}")
        elif kind == "win":
            self.wins += 1
            self._write("BLOCK", f"accepted blocks this session: {self.wins}")
        elif kind == "stopped":
            self._write("STATUS", "Miner exited cleanly")

    def request_stop(self, *_args) -> None:
        if self.stop_event.is_set():
            return
        self._write("STATUS", "Stop requested; closing workers...")
        self.stop_event.set()
        if self.round_stop is not None:
            self.round_stop.set()

    def run(self, settings: dict) -> None:
        self._write(
            "HELIX",
            f"starting {settings['backend'].upper()} miner with {settings['threads']} CPU process(es)",
        )
        if settings["pool_url"]:
            self._mine_pool_forever(
                settings["address"], settings["pool_url"],
                settings["threads"], settings["backend"],
            )
        else:
            self._mine_forever(
                settings["address"], settings["nodes"],
                settings["threads"], settings["backend"],
            )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    settings = validated_settings(parser.parse_args(argv), parser)
    mp.freeze_support()
    miner = HelixMinerCLI(settings["status_interval"])
    for name in ("SIGINT", "SIGTERM"):
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), miner.request_stop)
    try:
        miner.run(settings)
    except KeyboardInterrupt:
        miner.request_stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
