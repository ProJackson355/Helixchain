"""Helix Miner: competitive proof-of-work desktop miner.

Run from the project directory with:
    python helix_miner.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import multiprocessing as mp
import os
import queue
import re
import threading
import time
import tkinter as tk
from copy import deepcopy
from tkinter import ttk
from urllib.parse import urlparse

import requests


ADDRESS_RE = re.compile(r"^[0-9a-f]{40}$")
DEFAULT_NODE = "https://node.hlxchain.com"
REQUEST_TIMEOUT = 5
TIP_POLL_INTERVAL = 1.0


def format_elapsed(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    minutes, remainder = divmod(seconds, 60)
    if minutes < 60:
        return f"{int(minutes)}m {remainder:04.1f}s"
    hours, minutes = divmod(int(minutes), 60)
    return f"{hours}h {minutes}m {remainder:04.1f}s"


def parse_node_urls(value: str) -> list[str]:
    """Parse one URL, comma/newline-separated URLs, or a JSON URL array."""
    raw = value.strip()
    if not raw:
        raise ValueError("Enter at least one Helix node URL.")
    if raw.startswith("["):
        try:
            values = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("The node URL JSON array is invalid.") from exc
        if not isinstance(values, list):
            raise ValueError("The node URL JSON value must be an array.")
    else:
        values = re.split(r"[\r\n,]+", raw)

    result = []
    for candidate in values:
        if not isinstance(candidate, str) or not candidate.strip():
            continue
        candidate = candidate.strip().rstrip("/")
        parsed = urlparse(candidate)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(f"Invalid node URL: {candidate}")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Node URLs cannot contain credentials, query strings, or fragments.")
        if candidate not in result:
            result.append(candidate)
    if not result:
        raise ValueError("Enter at least one valid Helix node URL.")
    if len(result) > 10:
        raise ValueError("Use no more than 10 node URLs.")
    return result


def block_hash(block: dict, nonce: int | None = None) -> str:
    """Calculate the exact SHA-256 block hash used by Helix consensus."""
    payload = {
        "index": block["index"],
        "transactions": block["transactions"],
        "previous_hash": block["previous_hash"],
        "timestamp": block["timestamp"],
        "nonce": block["nonce"] if nonce is None else nonce,
    }
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def work_target(work: dict) -> int:
    """Numeric proof-of-work target from a node or pool work payload.

    Prefers the exact `target`/`share_target` hex; falls back to the legacy
    leading-zero difficulty (target == 16**(64-difficulty) - 1) for older nodes.
    """
    raw = work.get("target") or work.get("share_target")
    if raw:
        return int(raw, 16)
    difficulty = int(work.get("share_difficulty", work.get("difficulty", 1)))
    return 16 ** (64 - difficulty) - 1


def target_difficulty(target: int) -> float:
    """Effective difficulty implied by a numeric target, in hex-zero units.

    difficulty == 64 - log16(target + 1). A whole leading-zero level gives an
    integer; fine-grained targets give the true fractional difficulty (which can
    exceed the node's displayed integer once fine mode is active).
    """
    target = int(target)
    if target < 0:
        return 64.0
    return round(64 - math.log(target + 1, 16), 2)


def find_solution(
    block: dict,
    difficulty: int,
    start_nonce: int = 0,
    stride: int = 1,
    max_hashes: int | None = None,
) -> tuple[dict | None, int]:
    """Mine one nonce range; also serves as a deterministic testable core."""
    target = "0" * difficulty
    nonce = start_nonce
    hashes = 0
    while max_hashes is None or hashes < max_hashes:
        digest = block_hash(block, nonce)
        hashes += 1
        if digest.startswith(target):
            solved = deepcopy(block)
            solved["nonce"] = nonce
            solved["hash"] = digest
            return solved, hashes
        nonce += stride
    return None, hashes


def _hash_worker(block, target, start_nonce, stride, stop_event, output):
    nonce = start_nonce
    hashes = 0
    started = last_report = time.monotonic()
    while not stop_event.is_set():
        digest = block_hash(block, nonce)
        hashes += 1
        if int(digest, 16) <= target:
            solved = deepcopy(block)
            solved["nonce"] = nonce
            solved["hash"] = digest
            output.put(("solved", start_nonce, hashes, time.monotonic() - started, solved))
            return
        nonce += stride
        now = time.monotonic()
        if now - last_report >= 0.5:
            output.put(("progress", start_nonce, hashes, now - started, None))
            last_report = now


def _share_worker(block, target, start_nonce, stride, stop_event, output):
    """Pool worker: report every hash that meets the share target and keep going."""
    nonce = start_nonce
    hashes = 0
    started = last_report = time.monotonic()
    while not stop_event.is_set():
        digest = block_hash(block, nonce)
        hashes += 1
        if int(digest, 16) <= target:
            output.put(("share", nonce, digest, hashes, time.monotonic() - started))
        nonce += stride
        now = time.monotonic()
        if now - last_report >= 0.5:
            output.put(("progress", start_nonce, hashes, now - started, None))
            last_report = now


class HelixMinerApp:
    BG = "#090b12"
    SURFACE = "#121622"
    SURFACE2 = "#191e2d"
    BORDER = "#2b3348"
    TEXT = "#eef1fa"
    MUTED = "#929bb1"
    ACCENT = "#746cff"
    GREEN = "#53dd91"
    RED = "#ff6c7d"

    def __init__(self, root: tk.Tk, address: str = "", nodes: str = DEFAULT_NODE, threads: int = 1):
        self.root = root
        self.root.title("Helix Miner")
        self.root.geometry("820x820")
        self.root.minsize(620, 620)
        self.root.configure(bg=self.BG)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.stop_event = threading.Event()
        self.round_stop = None
        self.coordinator = None
        self.ui_events: queue.Queue = queue.Queue()
        self.running = False
        self.wins = 0

        self.address_var = tk.StringVar(value=address)
        self.nodes_var = tk.StringVar(value=nodes)
        self.mode_var = tk.StringVar(value="Solo")
        self.pool_var = tk.StringVar(value="")
        self.shares = 0
        self.threads_var = tk.IntVar(value=max(1, min(threads, os.cpu_count() or 1)))
        self.backend_var = tk.StringVar(value="CPU")
        self.status_var = tk.StringVar(value="Stopped")
        self.height_var = tk.StringVar(value="—")
        self.difficulty_var = tk.StringVar(value="—")
        self.reward_var = tk.StringVar(value="—")
        self.hashrate_var = tk.StringVar(value="0 H/s")
        self.hashes_var = tk.StringVar(value="0")
        self.wins_var = tk.StringVar(value="0")

        self._style()
        self._build()
        self.root.after(100, self._drain_ui_events)

    def _style(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Miner.TEntry", fieldbackground=self.SURFACE2, foreground=self.TEXT,
                        bordercolor=self.BORDER, insertcolor=self.TEXT, padding=10)
        style.configure("Miner.TSpinbox", fieldbackground=self.SURFACE2, foreground=self.TEXT,
                        bordercolor=self.BORDER, arrowcolor=self.MUTED, padding=9)
        style.configure("Miner.TCombobox", fieldbackground=self.SURFACE2, foreground=self.TEXT,
                        bordercolor=self.BORDER, arrowcolor=self.MUTED, padding=9)
        style.map("Miner.TEntry", bordercolor=[("focus", self.ACCENT)])
        style.map("Miner.TSpinbox", bordercolor=[("focus", self.ACCENT)])

    def _build(self):
        header = tk.Frame(self.root, bg=self.SURFACE, padx=24, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="H", bg=self.ACCENT, fg="white", font=("Segoe UI", 18, "bold"),
                 width=2, pady=3).pack(side="left")
        title = tk.Frame(header, bg=self.SURFACE)
        title.pack(side="left", padx=12)
        tk.Label(title, text="Helix Miner", bg=self.SURFACE, fg=self.TEXT,
                 font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(title, text="Competitive SHA-256 proof-of-work miner", bg=self.SURFACE,
                 fg=self.MUTED, font=("Segoe UI", 9)).pack(anchor="w")

        scroll_shell = tk.Frame(self.root, bg=self.BG)
        scroll_shell.pack(fill="both", expand=True)
        self.scroll_canvas = tk.Canvas(
            scroll_shell, bg=self.BG, highlightthickness=0, borderwidth=0,
        )
        page_scrollbar = ttk.Scrollbar(
            scroll_shell, orient="vertical", command=self.scroll_canvas.yview,
        )
        self.scroll_canvas.configure(yscrollcommand=page_scrollbar.set)
        page_scrollbar.pack(side="right", fill="y")
        self.scroll_canvas.pack(side="left", fill="both", expand=True)

        canvas = tk.Frame(self.scroll_canvas, bg=self.BG, padx=18, pady=10)
        self.scroll_window = self.scroll_canvas.create_window(
            (0, 0), window=canvas, anchor="nw",
        )
        canvas.bind(
            "<Configure>",
            lambda _event: self.scroll_canvas.configure(
                scrollregion=self.scroll_canvas.bbox("all")
            ),
        )
        self.scroll_canvas.bind(
            "<Configure>",
            lambda event: self.scroll_canvas.itemconfigure(
                self.scroll_window, width=event.width
            ),
        )
        canvas.columnconfigure(0, weight=1)
        canvas.columnconfigure(1, weight=1)

        setup = self._card(canvas, "MINING SETUP", 0, 0)
        self._label(setup, "Reward wallet address").pack(anchor="w")
        ttk.Entry(setup, textvariable=self.address_var, style="Miner.TEntry").pack(fill="x", pady=(4, 12))
        self._label(setup, "Node URL(s)").pack(anchor="w")
        ttk.Entry(setup, textvariable=self.nodes_var, style="Miner.TEntry").pack(fill="x", pady=(4, 12))
        self._label(setup, "Mining mode").pack(anchor="w")
        self.mode_select = ttk.Combobox(
            setup, textvariable=self.mode_var, values=("Solo", "Pool"),
            state="readonly", style="Miner.TCombobox",
        )
        self.mode_select.pack(fill="x", pady=(4, 12))
        self.mode_select.bind("<<ComboboxSelected>>", self._mode_changed)
        self.pool_label = self._label(setup, "Pool URL (Pool mode)")
        self.pool_label.pack(anchor="w")
        self.pool_entry = ttk.Entry(setup, textvariable=self.pool_var, style="Miner.TEntry")
        self.pool_entry.pack(fill="x", pady=(4, 12))
        self._label(setup, "Mining device").pack(anchor="w")
        self.backend_select = ttk.Combobox(
            setup, textvariable=self.backend_var, values=("CPU", "NVIDIA CUDA"),
            state="readonly", style="Miner.TCombobox",
        )
        self.backend_select.pack(fill="x", pady=(4, 12))
        self.backend_select.bind("<<ComboboxSelected>>", self._backend_changed)
        self._label(setup, "Mining processes").pack(anchor="w")
        self.process_select = ttk.Spinbox(
            setup, from_=1, to=max(1, os.cpu_count() or 1), textvariable=self.threads_var,
            style="Miner.TSpinbox", width=8,
        )
        self.process_select.pack(fill="x", pady=(4, 14))
        controls = tk.Frame(setup, bg=self.SURFACE)
        controls.pack(fill="x")
        self.start_button = tk.Button(controls, text="Start Mining", command=self.start,
                                      bg=self.ACCENT, fg="white", activebackground="#6259ed",
                                      activeforeground="white", relief="flat", padx=16, pady=10,
                                      font=("Segoe UI", 10, "bold"), cursor="hand2")
        self.start_button.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.stop_button = tk.Button(controls, text="Stop", command=self.stop, state="disabled",
                                     bg="#30151d", fg=self.RED, activebackground="#401b26",
                                     activeforeground=self.RED, relief="flat", padx=16, pady=10,
                                     font=("Segoe UI", 10, "bold"), cursor="hand2")
        self.stop_button.pack(side="left", fill="x", expand=True, padx=(5, 0))

        network = self._card(canvas, "NETWORK STATUS", 0, 1)
        tk.Label(network, textvariable=self.status_var, bg=self.SURFACE, fg=self.GREEN,
                 font=("Segoe UI", 11, "bold"), wraplength=310, justify="left").pack(anchor="w", pady=(0, 12))
        metrics = tk.Frame(network, bg=self.SURFACE)
        metrics.pack(fill="both", expand=True)
        for col in range(2):
            metrics.columnconfigure(col, weight=1)
        self._metric(metrics, "HEIGHT", self.height_var, 0, 0)
        self._metric(metrics, "DIFFICULTY", self.difficulty_var, 0, 1)
        self._metric(metrics, "REWARD", self.reward_var, 1, 0)
        self._metric(metrics, "BLOCKS WON", self.wins_var, 1, 1)

        performance = self._card(canvas, "LIVE PERFORMANCE", 1, 0, columnspan=2)
        performance.columnconfigure(0, weight=1)
        performance.columnconfigure(1, weight=1)
        self._metric(performance, "HASH RATE", self.hashrate_var, 0, 0)
        self._metric(performance, "HASHES THIS ROUND", self.hashes_var, 0, 1)

        logs = self._card(canvas, "MINER LOG", 2, 0, columnspan=2)
        logs.rowconfigure(0, weight=1)
        logs.columnconfigure(0, weight=1)
        self.log_widget = tk.Text(logs, height=10, bg="#090c14", fg=self.MUTED,
                                  insertbackground=self.TEXT, relief="flat", padx=10, pady=8,
                                  font=("Consolas", 9), state="disabled", wrap="word")
        self.log_widget.grid(row=0, column=0, sticky="nsew")
        log_scrollbar = ttk.Scrollbar(logs, orient="vertical", command=self.log_widget.yview)
        log_scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_widget.configure(yscrollcommand=log_scrollbar.set)
        self.root.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        self.root.bind_all("<Button-4>", self._on_mousewheel, add="+")
        self.root.bind_all("<Button-5>", self._on_mousewheel, add="+")
        self.log("Ready. Enter a reward address and node URL, then start mining.")

    def _on_mousewheel(self, event):
        if event.widget is self.log_widget:
            return
        if getattr(event, "num", None) == 4:
            units = -3
        elif getattr(event, "num", None) == 5:
            units = 3
        else:
            delta = getattr(event, "delta", 0)
            units = -int(delta / 120) * 3 if delta else 0
        if units:
            self.scroll_canvas.yview_scroll(units, "units")

    def _backend_changed(self, _event=None):
        using_cuda = self.backend_var.get() == "NVIDIA CUDA"
        self.process_select.configure(state="disabled" if using_cuda else "normal")

    def _mode_changed(self, _event=None):
        pool_mode = self.mode_var.get() == "Pool"
        self.pool_entry.configure(state="normal" if pool_mode else "disabled")

    def _card(self, parent, title, row, column, columnspan=1):
        outer = tk.Frame(parent, bg=self.SURFACE, highlightbackground=self.BORDER,
                         highlightthickness=1, padx=16, pady=12)
        outer.grid(row=row, column=column, columnspan=columnspan, sticky="nsew", padx=6, pady=6)
        tk.Label(outer, text=title, bg=self.SURFACE, fg=self.MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 12))
        body = tk.Frame(outer, bg=self.SURFACE)
        body.pack(fill="both", expand=True)
        return body

    def _label(self, parent, text):
        return tk.Label(parent, text=text, bg=self.SURFACE, fg=self.MUTED, font=("Segoe UI", 9))

    def _metric(self, parent, label, variable, row, column):
        box = tk.Frame(parent, bg=self.SURFACE2, highlightbackground=self.BORDER,
                       highlightthickness=1, padx=13, pady=11)
        box.grid(row=row, column=column, sticky="nsew", padx=5, pady=5)
        tk.Label(box, text=label, bg=self.SURFACE2, fg=self.MUTED,
                 font=("Segoe UI", 8)).pack(anchor="w")
        tk.Label(box, textvariable=variable, bg=self.SURFACE2, fg=self.TEXT,
                 font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(3, 0))

    def log(self, message: str):
        stamp = time.strftime("%H:%M:%S")
        self.log_widget.configure(state="normal")
        self.log_widget.insert("end", f"[{stamp}] {message}\n")
        self.log_widget.see("end")
        self.log_widget.configure(state="disabled")

    def emit(self, kind, value):
        self.ui_events.put((kind, value))

    def _drain_ui_events(self):
        try:
            while True:
                kind, value = self.ui_events.get_nowait()
                if kind == "log":
                    self.log(value)
                elif kind == "status":
                    self.status_var.set(value)
                elif kind == "stats":
                    self.height_var.set(str(value.get("height", "—")))
                    self.difficulty_var.set(str(value.get("difficulty", "—")))
                    self.reward_var.set(f"{value.get('reward', '—')} HLX")
                elif kind == "performance":
                    hashes, rate = value
                    self.hashes_var.set(f"{hashes:,}")
                    self.hashrate_var.set(self._format_rate(rate))
                elif kind == "height":
                    self.height_var.set(str(value))
                elif kind == "win":
                    self.wins += 1
                    self.wins_var.set(str(self.wins))
                elif kind == "stopped":
                    self.running = False
                    self.start_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
        except queue.Empty:
            pass
        self.root.after(100, self._drain_ui_events)

    @staticmethod
    def _format_rate(rate):
        if rate >= 1_000_000:
            return f"{rate / 1_000_000:.2f} MH/s"
        if rate >= 1_000:
            return f"{rate / 1_000:.2f} kH/s"
        return f"{rate:.0f} H/s"

    def start(self):
        if self.running:
            return
        address = self.address_var.get().strip().lower()
        if ADDRESS_RE.fullmatch(address) is None:
            self.log("Reward address must be exactly 40 lowercase hexadecimal characters.")
            return
        try:
            nodes = parse_node_urls(self.nodes_var.get())
            processes = int(self.threads_var.get())
            if not 1 <= processes <= max(1, os.cpu_count() or 1):
                raise ValueError("Mining processes are outside the supported range.")
        except (ValueError, tk.TclError) as exc:
            self.log(str(exc))
            return
        pool_mode = self.mode_var.get() == "Pool"
        pool_url = self.pool_var.get().strip().rstrip("/")
        if pool_mode and not re.match(r"^https?://", pool_url):
            self.log("Enter the pool URL (for example https://pool.example.com) to join a pool.")
            return
        self.running = True
        self.shares = 0
        self.stop_event.clear()
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_var.set("Connecting…")
        backend = "nvidia" if self.backend_var.get() == "NVIDIA CUDA" else "cpu"
        target = self._mine_pool_forever if pool_mode else self._mine_forever
        args = (address, pool_url, processes, backend) if pool_mode else (address, nodes, processes, backend)
        self.coordinator = threading.Thread(target=target, args=args, daemon=True)
        self.coordinator.start()

    def stop(self):
        if not self.running:
            return
        self.stop_event.set()
        if self.round_stop is not None:
            self.round_stop.set()
        self.status_var.set("Stopping…")

    def close(self):
        self.stop_event.set()
        if self.round_stop is not None:
            self.round_stop.set()
        self.root.destroy()

    def _compatible_node(self, nodes):
        for node in nodes:
            if self.stop_event.is_set():
                return None
            try:
                response = requests.get(node + "/mining/info", timeout=REQUEST_TIMEOUT)
                data = response.json()
                if response.ok and data.get("external_mining") is True:
                    return node
            except (requests.RequestException, ValueError):
                continue
        return None

    def _mine_forever(self, address, nodes, processes, backend="cpu"):
        try:
            cuda_miner = None
            if backend == "nvidia":
                try:
                    from miner_cuda import NvidiaCudaMiner
                    self.emit("status", "Initializing NVIDIA CUDA...")
                    cuda_miner = NvidiaCudaMiner()
                    self.emit("log", f"NVIDIA CUDA ready: {cuda_miner.device_name}")
                except (ImportError, RuntimeError) as exc:
                    self.emit("status", "NVIDIA CUDA unavailable")
                    self.emit("log", str(exc))
                    return
            while not self.stop_event.is_set():
                node = self._compatible_node(nodes)
                if node is None:
                    self.emit("status", "No compatible node available")
                    self.emit("log", "No configured node supports external mining; retrying in 3 seconds.")
                    self.stop_event.wait(3)
                    continue
                try:
                    response = requests.get(
                        node + "/mining/work", params={"address": address}, timeout=REQUEST_TIMEOUT
                    )
                    work = response.json()
                    if not response.ok or "block" not in work:
                        raise RuntimeError(work.get("message", f"HTTP {response.status_code}"))
                except (requests.RequestException, ValueError, RuntimeError) as exc:
                    self.emit("log", f"Could not get mining work from {node}: {exc}")
                    self.stop_event.wait(2)
                    continue

                block = work["block"]
                target = work_target(work)
                # Show the true difficulty implied by the target, not the node's
                # capped integer, so fine-grained levels display correctly.
                difficulty = target_difficulty(target)
                self.emit("status", f"Mining block {block['index']} through {node}")
                self.emit("stats", {
                    "height": block["index"] - 1,
                    "difficulty": difficulty,
                    "reward": work.get("reward", 0),
                })
                if cuda_miner is not None:
                    self.emit("log", f"Started block {block['index']} at difficulty {difficulty} on {cuda_miner.device_name}.")
                    round_started = time.monotonic()
                    solved = self._mine_round_cuda(node, block, target, cuda_miner)
                else:
                    self.emit("log", f"Started block {block['index']} at difficulty {difficulty} with {processes} CPU process(es).")
                    round_started = time.monotonic()
                    solved = self._mine_round(node, block, target, processes)
                round_elapsed = time.monotonic() - round_started
                if self.stop_event.is_set():
                    break
                if solved is None:
                    continue
                self.emit("status", f"Submitting block {solved['index']}…")
                result = self._submit(nodes, node, solved)
                if result and result.get("accepted"):
                    self.emit("win", None)
                    self.emit("log", f"Block {result['block']} accepted after {format_elapsed(round_elapsed)}; earned {result['reward']} HLX. Hash {result['hash']}")
                else:
                    message = result.get("message", "Submission failed") if result else "No node accepted the submission"
                    self.emit("log", f"{message} Round time: {format_elapsed(round_elapsed)}.")
        finally:
            self.emit("status", "Stopped")
            self.emit("stopped", None)

    def _mine_round(self, node, block, target, process_count):
        started = time.monotonic()
        context = mp.get_context("spawn")
        self.round_stop = context.Event()
        output = context.Queue()
        workers = []
        for index in range(process_count):
            process = context.Process(
                target=_hash_worker,
                args=(block, target, index, process_count, self.round_stop, output),
                daemon=True,
            )
            process.start()
            workers.append(process)

        progress = {}
        solved = None
        last_tip_check = time.monotonic()
        try:
            while not self.stop_event.is_set() and not self.round_stop.is_set():
                try:
                    kind, worker_id, hashes, elapsed, candidate = output.get(timeout=0.2)
                    progress[worker_id] = (hashes, elapsed)
                    total = sum(item[0] for item in progress.values())
                    rate = sum(item[0] / item[1] for item in progress.values() if item[1] > 0)
                    self.emit("performance", (total, rate))
                    if kind == "solved":
                        solved = candidate
                        self.round_stop.set()
                        self.emit("log", f"Found proof {candidate['hash']} after {total:,} reported hashes.")
                        break
                except queue.Empty:
                    pass

                if time.monotonic() - last_tip_check >= TIP_POLL_INTERVAL:
                    last_tip_check = time.monotonic()
                    try:
                        health = requests.get(node + "/health", timeout=REQUEST_TIMEOUT).json()
                        if int(health.get("height", -1)) >= int(block["index"]):
                            self.emit("height", int(health.get("height")))
                            self.emit("log", f"Another miner won block {block['index']} after this app mined for {format_elapsed(time.monotonic() - started)}; refreshing work.")
                            self.round_stop.set()
                            break
                    except (requests.RequestException, ValueError, TypeError):
                        pass
        finally:
            self.round_stop.set()
            for process in workers:
                process.join(timeout=0.5)
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=0.5)
            output.close()
            self.round_stop = None
        return solved

    def _mine_round_cuda(self, node, block, target, cuda_miner):
        self.round_stop = threading.Event()
        cuda_miner.prepare(block, target)
        next_nonce = 0
        total = 0
        started = time.monotonic()
        last_tip_check = started
        solved = None
        try:
            while not self.stop_event.is_set() and not self.round_stop.is_set():
                candidate, hashes, _elapsed = cuda_miner.mine_batch(next_nonce)
                next_nonce += hashes
                total += hashes
                elapsed = max(time.monotonic() - started, 0.000001)
                self.emit("performance", (total, total / elapsed))
                if candidate is not None:
                    solved = candidate
                    self.emit("log", f"Found NVIDIA proof {candidate['hash']} after {total:,} launched hashes.")
                    break
                if time.monotonic() - last_tip_check >= TIP_POLL_INTERVAL:
                    last_tip_check = time.monotonic()
                    try:
                        health = requests.get(node + "/health", timeout=REQUEST_TIMEOUT).json()
                        if int(health.get("height", -1)) >= int(block["index"]):
                            self.emit("height", int(health.get("height")))
                            self.emit("log", f"Another miner won block {block['index']} after this app mined for {format_elapsed(time.monotonic() - started)}; refreshing CUDA work.")
                            break
                    except (requests.RequestException, ValueError, TypeError):
                        pass
        finally:
            self.round_stop.set()
            self.round_stop = None
        return solved

    def _submit(self, nodes, preferred, block):
        ordered = [preferred, *[node for node in nodes if node != preferred]]
        for node in ordered:
            try:
                response = requests.post(
                    node + "/mining/submit", json={"block": block}, timeout=REQUEST_TIMEOUT
                )
                result = response.json()
                if response.ok:
                    return result
            except (requests.RequestException, ValueError):
                continue
        return None

    # --- pool mining --------------------------------------------------------
    def _pool_work(self, pool_url, address):
        try:
            response = requests.get(
                pool_url + "/pool/work", params={"address": address}, timeout=REQUEST_TIMEOUT
            )
            data = response.json()
            if response.ok and "block" in data:
                return data
            self.emit("log", f"Pool: {data.get('message', f'HTTP {response.status_code}')}")
        except (requests.RequestException, ValueError) as exc:
            self.emit("log", f"Could not get pool work from {pool_url}: {exc}")
        return None

    def _submit_share(self, pool_url, job_id, address, nonce):
        try:
            response = requests.post(
                pool_url + "/pool/submit",
                json={"job_id": job_id, "address": address, "nonce": int(nonce)},
                timeout=REQUEST_TIMEOUT,
            )
            return response.json() if response.ok else None
        except (requests.RequestException, ValueError):
            return None

    def _handle_share(self, pool_url, address, job_id, nonce):
        result = self._submit_share(pool_url, job_id, address, nonce)
        if not result:
            return
        if result.get("accepted"):
            self.shares += 1
            self.emit("status", f"Pool mining · {self.shares} share(s) accepted")
            if result.get("block"):
                self.emit("win", None)
                self.emit("log", "Your share solved a block for the pool! The reward is split by shares.")
        elif result.get("reason") not in (None, "duplicate share", "stale or unknown job", "stale job"):
            self.emit("log", f"Share rejected: {result.get('reason')}")

    def _mine_pool_forever(self, address, pool_url, processes, backend="cpu"):
        try:
            cuda_miner = None
            if backend == "nvidia":
                try:
                    from miner_cuda import NvidiaCudaMiner
                    self.emit("status", "Initializing NVIDIA CUDA...")
                    cuda_miner = NvidiaCudaMiner()
                    self.emit("log", f"NVIDIA CUDA ready: {cuda_miner.device_name}")
                except (ImportError, RuntimeError) as exc:
                    self.emit("status", "NVIDIA CUDA unavailable")
                    self.emit("log", str(exc))
                    return
            self.emit("log", f"Joining pool {pool_url} as {address}.")
            while not self.stop_event.is_set():
                job = self._pool_work(pool_url, address)
                if job is None:
                    self.emit("status", "Waiting for pool work…")
                    self.stop_event.wait(3)
                    continue
                block = job["block"]
                share_target = work_target(job)
                network_target = int(job["network_target"], 16) if job.get("network_target") else share_target
                share_difficulty = target_difficulty(share_target)
                network_difficulty = target_difficulty(network_target)
                self.emit("status", f"Pool mining block {block['index']} · share difficulty {share_difficulty}")
                self.emit("stats", {
                    "height": block["index"] - 1,
                    "difficulty": network_difficulty,
                    "reward": job.get("reward", 0),
                })
                self.emit("log", f"New pool job {job['job_id']} for block {block['index']} (share {share_difficulty}, network {network_difficulty}).")
                if cuda_miner is not None:
                    self._mine_pool_round_cuda(pool_url, address, job, cuda_miner)
                else:
                    self._mine_pool_round(pool_url, address, job, processes)
        finally:
            self.emit("status", "Stopped")
            self.emit("stopped", None)

    def _mine_pool_round(self, pool_url, address, job, process_count):
        block = job["block"]
        share_target = work_target(job)
        job_id = job["job_id"]
        context = mp.get_context("spawn")
        self.round_stop = context.Event()
        output = context.Queue()
        workers = []
        for index in range(process_count):
            process = context.Process(
                target=_share_worker,
                args=(block, share_target, index, process_count, self.round_stop, output),
                daemon=True,
            )
            process.start()
            workers.append(process)
        progress = {}
        last_job_check = time.monotonic()
        try:
            while not self.stop_event.is_set() and not self.round_stop.is_set():
                try:
                    item = output.get(timeout=0.2)
                    if item[0] == "share":
                        self._handle_share(pool_url, address, job_id, item[1])
                    elif item[0] == "progress":
                        _, worker_id, hashes, elapsed, _ = item
                        progress[worker_id] = (hashes, elapsed)
                        total = sum(value[0] for value in progress.values())
                        rate = sum(value[0] / value[1] for value in progress.values() if value[1] > 0)
                        self.emit("performance", (total, rate))
                except queue.Empty:
                    pass
                if time.monotonic() - last_job_check >= TIP_POLL_INTERVAL:
                    last_job_check = time.monotonic()
                    latest = self._pool_work(pool_url, address)
                    if latest and latest.get("job_id") != job_id:
                        self.emit("log", f"Pool advanced to block {latest['block']['index']}; refreshing work.")
                        self.round_stop.set()
                        break
        finally:
            self.round_stop.set()
            for process in workers:
                process.join(timeout=0.5)
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=0.5)
            output.close()
            self.round_stop = None

    def _mine_pool_round_cuda(self, pool_url, address, job, cuda_miner):
        block = job["block"]
        share_target = work_target(job)
        job_id = job["job_id"]
        self.round_stop = threading.Event()
        cuda_miner.prepare(block, share_target)
        next_nonce = 0
        total = 0
        started = last_job_check = time.monotonic()
        try:
            while not self.stop_event.is_set() and not self.round_stop.is_set():
                candidate, hashes, _elapsed = cuda_miner.mine_batch(next_nonce)
                next_nonce += hashes
                total += hashes
                elapsed = max(time.monotonic() - started, 0.000001)
                self.emit("performance", (total, total / elapsed))
                if candidate is not None:
                    self._handle_share(pool_url, address, job_id, candidate["nonce"])
                if time.monotonic() - last_job_check >= TIP_POLL_INTERVAL:
                    last_job_check = time.monotonic()
                    latest = self._pool_work(pool_url, address)
                    if latest and latest.get("job_id") != job_id:
                        self.emit("log", f"Pool advanced to block {latest['block']['index']}; refreshing CUDA work.")
                        break
        finally:
            self.round_stop.set()
            self.round_stop = None


def main():
    parser = argparse.ArgumentParser(description="Launch the Helix Miner desktop app.")
    parser.add_argument("--address", default="", help="40-character reward wallet address")
    parser.add_argument("--nodes", default=DEFAULT_NODE, help="node URL, CSV list, or JSON URL array")
    parser.add_argument("--threads", type=int, default=max(1, min(2, os.cpu_count() or 1)), help="mining process count")
    parser.add_argument("--backend", choices=("cpu", "nvidia"), default="cpu", help="mining backend")
    args = parser.parse_args()
    mp.freeze_support()
    root = tk.Tk()
    app = HelixMinerApp(root, args.address, args.nodes, args.threads)
    if args.backend == "nvidia":
        app.backend_var.set("NVIDIA CUDA")
        app._backend_changed()
    root.mainloop()


if __name__ == "__main__":
    main()
