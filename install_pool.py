"""Helix Pool desktop setup and monitoring GUI.

The GUI installs the pool dependencies, launches the coordinator, optionally
launches a Cloudflare named or quick tunnel, and shows live pool statistics.
Cloudflare tokens and wallet seed phrases are process-only secrets: they are
never written to disk or included in logs.
"""
from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from dataclasses import asdict, dataclass
from pathlib import Path

import tkinter as tk
from tkinter import messagebox, ttk

from gui_branding import apply_helix_icon, set_windows_app_id


ROOT = Path(__file__).resolve().parent
SETTINGS_FILE = ROOT / "pool_gui_settings.json"
TRY_CLOUDFLARE_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com", re.I)
# The original browser wallet shipped with a shortened recovery-word table
# containing these legacy entries, which are not part of the official English
# BIP-39 list.  Existing website wallets must continue to accept them.
WEB_LEGACY_RECOVERY_WORDS = frozenset(
    "errupt fable far feet fellow felt grasp inbox mentor punish rage reach "
    "rooster stop store storm tamper unwrap web_old well".split()
)


@dataclass
class PoolSettings:
    nodes: str = "https://node.hlxchain.com"
    public_url: str = ""
    seed_format: str = "web"
    host: str = "0.0.0.0"
    port: int = 8100
    fee_percent: float = 1.0
    share_subtract: int = 2
    min_share_difficulty: int = 1


def validate_settings(settings: PoolSettings, seed: str) -> list[str]:
    errors = []
    nodes = [item.strip() for item in settings.nodes.split(",") if item.strip()]
    if not nodes or any(not re.match(r"^https?://", node) for node in nodes):
        errors.append("Enter at least one node URL beginning with http:// or https://.")
    if settings.public_url and not re.match(r"^https://[^\s/]+", settings.public_url):
        errors.append("The public pool URL must begin with https://.")
    if not 1 <= settings.port <= 65535:
        errors.append("Pool port must be between 1 and 65535.")
    if not 0 <= settings.fee_percent <= 100:
        errors.append("Pool fee must be between 0 and 100 percent.")
    if not 0 <= settings.share_subtract <= 16:
        errors.append("Share difficulty reduction must be between 0 and 16.")
    if not 1 <= settings.min_share_difficulty <= 64:
        errors.append("Minimum share difficulty must be between 1 and 64.")
    if len(seed.split()) != 12:
        errors.append("The pool payout wallet must have a 12-word seed phrase.")
    if settings.seed_format not in {"web", "bip39"}:
        errors.append("Choose a supported wallet seed source.")
    return errors


def pool_environment(settings: PoolSettings, seed: str) -> dict[str, str]:
    return {
        "HELIX_POOL_SEED": " ".join(seed.split()),
        "HELIX_POOL_SEED_FORMAT": settings.seed_format,
        "HELIX_POOL_NODE": settings.nodes,
        "HELIX_POOL_HOST": settings.host,
        "HELIX_POOL_PORT": str(settings.port),
        "HELIX_POOL_FEE_PERCENT": str(settings.fee_percent),
        "HELIX_POOL_SHARE_SUBTRACT": str(settings.share_subtract),
        "HELIX_POOL_MIN_SHARE_DIFFICULTY": str(settings.min_share_difficulty),
    }


def cloudflared_command(executable: str, port: int, token: str = "") -> list[str]:
    token = token.strip()
    if token:
        return [executable, "tunnel", "run", "--token", token]
    return [executable, "tunnel", "--url", f"http://localhost:{port}"]


class PoolSetupApp:
    BG = "#0f1320"
    CARD = "#1a2030"
    TEXT = "#e8ecf6"
    MUTED = "#98a2b8"
    ACCENT = "#7c5cfc"
    GREEN = "#3dd68c"
    RED = "#ff5c72"

    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Helix Pool Setup")
        root.geometry("760x820")
        root.minsize(650, 620)
        root.configure(bg=self.BG)
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.messages: queue.Queue[str] = queue.Queue()
        self.pool_process: subprocess.Popen | None = None
        self.tunnel_process: subprocess.Popen | None = None
        self.public_url = ""
        self.busy = False

        self._style()
        self._build()
        self._load_settings()
        self.root.after(120, self._drain_messages)
        self.root.after(1500, self._poll_stats)

    def _style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TEntry", fieldbackground="#0b0e16", foreground=self.TEXT,
                        insertcolor=self.TEXT, bordercolor="#30384a", padding=7)
        style.configure("TCombobox", fieldbackground="#0b0e16", foreground=self.TEXT, padding=6)
        style.configure("Treeview", background="#0b0e16", fieldbackground="#0b0e16",
                        foreground=self.TEXT, rowheight=27, borderwidth=0)
        style.configure("Treeview.Heading", background=self.CARD, foreground=self.TEXT)

    def _build(self):
        header = tk.Frame(self.root, bg=self.BG, padx=20, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="Helix Pool Setup", bg=self.BG, fg=self.TEXT,
                 font=("Segoe UI", 20, "bold")).pack(anchor="w")
        tk.Label(header, text="Configure, launch, expose, and monitor a proportional Helix mining pool.",
                 bg=self.BG, fg=self.MUTED, font=("Segoe UI", 10)).pack(anchor="w")

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=18, pady=(0, 10))
        setup_tab = tk.Frame(notebook, bg=self.BG)
        status_tab = tk.Frame(notebook, bg=self.BG)
        notebook.add(setup_tab, text=" Setup ")
        notebook.add(status_tab, text=" Status & Logs ")

        canvas = tk.Canvas(setup_tab, bg=self.BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(setup_tab, orient="vertical", command=canvas.yview)
        self.setup_card = tk.Frame(canvas, bg=self.CARD, padx=18, pady=14)
        window = canvas.create_window((0, 0), window=self.setup_card, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.setup_card.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window, width=e.width))

        self.seed_var = self._field("Pool payout wallet seed", "", secret=True,
                                    help_text="Required for automatic payouts. It stays in memory and is never saved.")
        seed_source = tk.Frame(self.setup_card, bg=self.CARD)
        seed_source.pack(fill="x", pady=(2, 5))
        tk.Label(seed_source, text="Seed source", bg=self.CARD, fg=self.TEXT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.seed_source_var = tk.StringVar(value="Helix website wallet")
        source_box = ttk.Combobox(seed_source, textvariable=self.seed_source_var, state="readonly",
                                  values=("Helix website wallet", "Python/CLI BIP-39 wallet"))
        source_box.pack(fill="x", pady=(2, 0))
        tk.Label(seed_source, text="Website seeds use Helix's browser derivation; Python/CLI seeds use standard BIP-39. Choosing the wrong source produces a different payout address.",
                 bg=self.CARD, fg=self.MUTED, justify="left", wraplength=650,
                 font=("Segoe UI", 8)).pack(anchor="w", pady=(2, 0))
        self.nodes_var = self._field("Helix node URL(s)", "https://node.hlxchain.com",
                                     help_text="Comma-separated failover nodes that supply work and accept solved blocks.")
        row = tk.Frame(self.setup_card, bg=self.CARD)
        row.pack(fill="x", pady=(4, 0))
        self.port_var = self._field("Pool port", "8100", parent=row, side="left")
        self.fee_var = self._field("Operator fee %", "1.0", parent=row, side="left")
        row2 = tk.Frame(self.setup_card, bg=self.CARD)
        row2.pack(fill="x")
        self.share_var = self._field("Share difficulty reduction", "2", parent=row2, side="left")
        self.min_share_var = self._field("Minimum share difficulty", "1", parent=row2, side="left")

        separator = tk.Frame(self.setup_card, bg="#30384a", height=1)
        separator.pack(fill="x", pady=14)
        tk.Label(self.setup_card, text="Cloudflare tunnel", bg=self.CARD, fg=self.TEXT,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(self.setup_card,
                 text="For a named tunnel, configure its public hostname service as http://localhost:8100 (or your chosen port).",
                 bg=self.CARD, fg=self.MUTED, justify="left", wraplength=650,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(1, 5))
        self.cf_token_var = self._field("Cloudflare tunnel token (optional)", "", secret=True,
                                        help_text="Runs cloudflared tunnel run --token TOKEN. The token is never saved.")
        self.public_url_var = self._field("Named tunnel public pool URL (optional)", "",
                                          help_text="For example https://pool.example.com. This allows automatic pool registration; it is safe to save.")
        self.quick_tunnel_var = tk.BooleanVar(value=False)
        self._check("Use a temporary trycloudflare.com tunnel when the token is blank",
                    self.quick_tunnel_var)
        self.register_var = tk.BooleanVar(value=True)
        self._check("Register the public pool URL with the connected Helix node", self.register_var)

        controls = tk.Frame(self.setup_card, bg=self.CARD)
        controls.pack(fill="x", pady=(16, 4))
        self.start_button = self._button(controls, "Set Up & Start Pool", self._start, self.ACCENT)
        self.start_button.pack(side="left", fill="x", expand=True)
        self.stop_button = self._button(controls, "Stop", self._stop, self.RED)
        self.stop_button.configure(state="disabled")
        self.stop_button.pack(side="left", padx=(8, 0))

        self.status_text = tk.StringVar(value="Pool stopped")
        status_head = tk.Frame(status_tab, bg=self.CARD, padx=16, pady=12)
        status_head.pack(fill="x")
        tk.Label(status_head, textvariable=self.status_text, bg=self.CARD, fg=self.TEXT,
                 font=("Segoe UI", 13, "bold")).pack(side="left")
        self.open_button = self._button(status_head, "Open pool stats", self._open_stats, self.ACCENT)
        self.open_button.pack(side="right")

        self.summary_var = tk.StringVar(value="Waiting for the pool to start.")
        tk.Label(status_tab, textvariable=self.summary_var, bg=self.BG, fg=self.MUTED,
                 justify="left", anchor="w", padx=6, pady=10).pack(fill="x")

        miners = tk.Frame(status_tab, bg=self.BG)
        miners.pack(fill="both", expand=True, padx=4)
        self.miner_tree = ttk.Treeview(miners, columns=("address", "shares", "percent", "hashrate"), show="headings", height=7)
        for key, title, width in (("address", "Miner address", 330), ("shares", "Shares", 75),
                                  ("percent", "Round %", 85), ("hashrate", "Est. H/s", 100)):
            self.miner_tree.heading(key, text=title)
            self.miner_tree.column(key, width=width, minwidth=60)
        self.miner_tree.pack(side="left", fill="both", expand=True)
        ttk.Scrollbar(miners, orient="vertical", command=self.miner_tree.yview).pack(side="right", fill="y")

        log_frame = tk.Frame(status_tab, bg=self.BG)
        log_frame.pack(fill="both", expand=True, pady=(10, 0))
        self.log_widget = tk.Text(log_frame, height=10, bg="#090c14", fg=self.MUTED,
                                  insertbackground=self.TEXT, relief="flat", wrap="word",
                                  font=("Consolas", 9), state="disabled")
        self.log_widget.pack(side="left", fill="both", expand=True)
        ttk.Scrollbar(log_frame, command=self.log_widget.yview).pack(side="right", fill="y")

    def _field(self, label, default, *, secret=False, help_text="", parent=None, side=None):
        parent = parent or self.setup_card
        frame = tk.Frame(parent, bg=self.CARD)
        frame.pack(side=side or "top", fill="x", expand=True, padx=(0, 8) if side == "left" else 0, pady=5)
        tk.Label(frame, text=label, bg=self.CARD, fg=self.TEXT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        var = tk.StringVar(value=default)
        ttk.Entry(frame, textvariable=var, show="•" if secret else "").pack(fill="x", pady=(2, 0))
        if help_text:
            tk.Label(frame, text=help_text, bg=self.CARD, fg=self.MUTED, justify="left",
                     wraplength=650, font=("Segoe UI", 8)).pack(anchor="w", pady=(2, 0))
        return var

    def _check(self, text, variable):
        tk.Checkbutton(self.setup_card, text=text, variable=variable, bg=self.CARD, fg=self.TEXT,
                       selectcolor=self.BG, activebackground=self.CARD, activeforeground=self.TEXT,
                       wraplength=650, justify="left").pack(anchor="w", pady=3)

    def _button(self, parent, text, command, color):
        return tk.Button(parent, text=text, command=command, bg=color, fg="white",
                         activebackground=color, activeforeground="white", relief="flat",
                         padx=14, pady=9, font=("Segoe UI", 9, "bold"), cursor="hand2")

    def _settings_from_form(self) -> PoolSettings:
        try:
            return PoolSettings(
                nodes=self.nodes_var.get().strip(), port=int(self.port_var.get().strip()),
                public_url=self.public_url_var.get().strip().rstrip("/"),
                seed_format="web" if self.seed_source_var.get() == "Helix website wallet" else "bip39",
                fee_percent=float(self.fee_var.get().strip()),
                share_subtract=int(self.share_var.get().strip()),
                min_share_difficulty=int(self.min_share_var.get().strip()),
            )
        except ValueError as exc:
            raise ValueError("Port, fee, and difficulty settings must be numbers.") from exc

    def _load_settings(self):
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            self.nodes_var.set(data.get("nodes", self.nodes_var.get()))
            self.public_url_var.set(data.get("public_url", self.public_url_var.get()))
            self.seed_source_var.set("Helix website wallet" if data.get("seed_format", "web") == "web"
                                     else "Python/CLI BIP-39 wallet")
            self.port_var.set(str(data.get("port", self.port_var.get())))
            self.fee_var.set(str(data.get("fee_percent", self.fee_var.get())))
            self.share_var.set(str(data.get("share_subtract", self.share_var.get())))
            self.min_share_var.set(str(data.get("min_share_difficulty", self.min_share_var.get())))
        except (OSError, ValueError, TypeError):
            pass

    @staticmethod
    def _save_settings(settings: PoolSettings):
        # Deliberately contains no seed phrase or Cloudflare token.
        SETTINGS_FILE.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")

    def log(self, message: str):
        # Never let process command lines containing a tunnel token reach logs.
        token = self.cf_token_var.get().strip() if hasattr(self, "cf_token_var") else ""
        self.messages.put(message.replace(token, "[hidden]") if token else message)

    def _drain_messages(self):
        try:
            while True:
                message = self.messages.get_nowait()
                self.log_widget.configure(state="normal")
                self.log_widget.insert("end", message.rstrip() + "\n")
                self.log_widget.see("end")
                self.log_widget.configure(state="disabled")
        except queue.Empty:
            pass
        self.root.after(120, self._drain_messages)

    def _start(self):
        if self.busy or (self.pool_process and self.pool_process.poll() is None):
            return
        try:
            settings = self._settings_from_form()
        except ValueError as exc:
            messagebox.showerror("Invalid pool settings", str(exc), parent=self.root)
            return
        seed = " ".join(self.seed_var.get().split())
        errors = validate_settings(settings, seed)
        if errors:
            messagebox.showerror("Invalid pool settings", "\n\n".join(errors), parent=self.root)
            return
        self.busy = True
        self.start_button.configure(state="disabled", text="Setting up…")
        threading.Thread(target=self._setup_and_start, args=(settings, seed), daemon=True).start()

    def _setup_and_start(self, settings: PoolSettings, seed: str):
        try:
            self._save_settings(settings)
            python = self._ensure_environment()
            if python is None or not self._validate_seed(python, seed, settings.seed_format):
                return
            env = os.environ.copy()
            env.update(pool_environment(settings, seed))
            self.log(f"[*] Starting Helix Pool on http://127.0.0.1:{settings.port}")
            self.pool_process = self._spawn([str(python), "run_pool.py"], env)
            threading.Thread(target=self._pipe_output, args=(self.pool_process, "Pool"), daemon=True).start()
            self.root.after(0, lambda: self.stop_button.configure(state="normal"))

            token = self.cf_token_var.get().strip()
            if token or self.quick_tunnel_var.get():
                self._start_tunnel(settings.port, token)
                if token and settings.public_url:
                    self.public_url = settings.public_url
                    self.log(f"[✓] Public pool URL: {self.public_url}")
                    self._copy_public_url()
                    if self.register_var.get():
                        threading.Thread(target=self._register_pool, args=(self.public_url,), daemon=True).start()
            self.log("[✓] Pool process started. Waiting for a block template…")
        except Exception as exc:
            self.log(f"[X] Pool setup failed: {exc}")
        finally:
            self.busy = False
            self.root.after(0, lambda: self.start_button.configure(state="normal", text="Set Up & Start Pool"))

    def _ensure_environment(self) -> Path | None:
        venv = ROOT / ".venv"
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        if not python.exists():
            self.log("[*] Creating the Python environment…")
            result = subprocess.run([sys.executable, "-m", "venv", str(venv)], cwd=ROOT)
            if result.returncode:
                self.log("[X] Could not create .venv. Install Python 3.11+ with venv support.")
                return None
        probe = subprocess.run([str(python), "-c", "import fastapi,uvicorn,requests,cryptography,mnemonic"], cwd=ROOT)
        if probe.returncode:
            self.log("[*] Installing pool dependencies (first launch can take a minute)…")
            install = subprocess.run([str(python), "-m", "pip", "install", "-r", "requirements.txt"], cwd=ROOT)
            if install.returncode:
                self.log("[X] Dependency installation failed. Check your internet connection and try again.")
                return None
        return python

    def _validate_seed(self, python: Path, seed: str, seed_format: str) -> bool:
        code = ("import sys; from mnemonic import Mnemonic; "
                "m=Mnemonic('english'); p=sys.stdin.read().strip(); words=p.split(); "
                "legacy=set(sys.argv[2].split(',')) if sys.argv[2] else set(); "
                "ok=(m.check(p) if sys.argv[1]=='bip39' else "
                "len(words)==12 and all(w in m.wordlist or w in legacy for w in words)); "
                "sys.exit(0 if ok else 2)")
        legacy_words = ",".join(sorted(WEB_LEGACY_RECOVERY_WORDS))
        result = subprocess.run(
            [str(python), "-c", code, seed_format, legacy_words],
            input=seed,
            text=True,
            cwd=ROOT,
        )
        if result.returncode:
            message = ("The payout seed phrase failed its BIP-39 checksum."
                       if seed_format == "bip39" else
                       "The website seed must contain exactly 12 Helix recovery words.")
            self.log(f"[X] {message} Check the seed source and every word.")
            return False
        return True

    def _spawn(self, command: list[str], env=None) -> subprocess.Popen:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        return subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                errors="replace", creationflags=flags)

    def _pipe_output(self, process: subprocess.Popen, label: str):
        if process.stdout:
            for line in process.stdout:
                self.log(f"[{label}] {line.rstrip()}")

    def _start_tunnel(self, port: int, token: str):
        executable = shutil.which("cloudflared")
        if not executable:
            self.log("[!] cloudflared is not installed or not on PATH; the pool is still local.")
            return
        command = cloudflared_command(executable, port, token)
        mode = "named Cloudflare tunnel" if token else "temporary Cloudflare tunnel"
        self.log(f"[*] Starting {mode}…")
        self.tunnel_process = self._spawn(command)
        threading.Thread(target=self._pipe_tunnel_output, args=(self.tunnel_process,), daemon=True).start()

    def _pipe_tunnel_output(self, process: subprocess.Popen):
        if not process.stdout:
            return
        for line in process.stdout:
            match = TRY_CLOUDFLARE_RE.search(line)
            if match and not self.public_url:
                self.public_url = match.group(0).rstrip("/")
                self.log(f"[✓] Public pool URL: {self.public_url}")
                self._copy_public_url()
                if self.register_var.get():
                    threading.Thread(target=self._register_pool, args=(self.public_url,), daemon=True).start()
            elif "token" not in line.lower():
                self.log(f"[Tunnel] {line.rstrip()}")
        if self.cf_token_var.get().strip():
            self.log("[*] Named tunnel stopped. Its public hostname is the one configured in Cloudflare.")

    def _register_pool(self, public_url: str):
        node = self.nodes_var.get().split(",")[0].strip().rstrip("/")
        try:
            request = urllib.request.Request(node + "/pools/register", method="POST",
                                             data=json.dumps({"url": public_url}).encode(),
                                             headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(request, timeout=8) as response:
                result = json.loads(response.read().decode())
            self.log("[✓] Pool registered with the Helix network." if result.get("added") or result.get("pool")
                     else f"[!] Pool registration response: {result.get('message', result)}")
        except Exception as exc:
            self.log(f"[!] Could not register the pool automatically: {exc}")

    def _copy_public_url(self):
        self.root.after(0, lambda: (self.root.clipboard_clear(), self.root.clipboard_append(self.public_url)))

    def _poll_stats(self):
        if self.pool_process and self.pool_process.poll() is None:
            try:
                port = int(self.port_var.get())
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/pool/stats", timeout=1) as response:
                    stats = json.loads(response.read().decode())
                self._render_stats(stats)
            except (OSError, ValueError, urllib.error.URLError):
                self.status_text.set("Pool starting…")
        elif self.pool_process:
            self.status_text.set("Pool stopped")
            self.stop_button.configure(state="disabled")
        self.root.after(2500, self._poll_stats)

    def _render_stats(self, stats: dict):
        height = stats.get("height")
        self.status_text.set(f"Pool online • block {height if height is not None else 'waiting'}")
        public = f"\nPublic URL: {self.public_url}" if self.public_url else ""
        self.summary_var.set(
            f"Address: {stats.get('pool_address') or 'not configured'}\n"
            f"Round: {stats.get('round_shares', 0)} shares • {stats.get('round_seconds', 0)} seconds • "
            f"{stats.get('pool_hashrate', 0):,.0f} H/s\n"
            f"Network difficulty: {stats.get('network_difficulty')} • Share difficulty: {stats.get('share_difficulty')} • "
            f"Blocks found: {stats.get('blocks_found', 0)} • Paid: {stats.get('total_paid', 0)} HLX{public}"
        )
        for item in self.miner_tree.get_children():
            self.miner_tree.delete(item)
        for miner in stats.get("miners", []):
            self.miner_tree.insert("", "end", values=(miner.get("address"), miner.get("shares"),
                                                       miner.get("round_percent"), miner.get("estimated_hashrate")))

    def _open_stats(self):
        try:
            port = int(self.port_var.get())
        except ValueError:
            port = 8100
        webbrowser.open((self.public_url or f"http://127.0.0.1:{port}") + "/pool/stats")

    def _stop(self):
        for process in (self.tunnel_process, self.pool_process):
            if process and process.poll() is None:
                process.terminate()
        self.tunnel_process = None
        self.pool_process = None
        self.public_url = ""
        self.status_text.set("Pool stopped")
        self.stop_button.configure(state="disabled")
        self.log("[*] Pool and tunnel stopped.")

    def _on_close(self):
        self._stop()
        self.root.destroy()


def main():
    set_windows_app_id("Pool")
    root = tk.Tk()
    apply_helix_icon(root, ROOT)
    PoolSetupApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
