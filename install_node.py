"""Helix Node installer — a small GUI that sets up and launches a node.

Run it with your system Python (needs only tkinter, which ships with Python):

    python install_node.py     (or double-click setup.bat)

It lets you fill in the node settings (most are optional), then creates the
virtual environment, installs dependencies, writes the settings into
config.json, and starts the node — optionally opening a Cloudflare tunnel.
"""
from __future__ import annotations

import json
import os
import queue
import secrets
import shutil
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

import tkinter as tk
from tkinter import ttk

ROOT = Path(__file__).resolve().parent
CONFIG_FILE = ROOT / "config.json"


class InstallerApp:
    BG = "#0f1320"
    CARD = "#1a2030"
    TEXT = "#e8ecf6"
    MUTED = "#98a2b8"
    ACCENT = "#7c5cfc"
    GREEN = "#3dd68c"

    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Helix Node Installer")
        root.geometry("620x760")
        root.configure(bg=self.BG)
        self.log_queue: queue.Queue = queue.Queue()
        self.busy = False

        self._build()
        self.root.after(120, self._drain_log)

    # ---- layout -----------------------------------------------------------
    def _label(self, parent, text, optional=False):
        frame = tk.Frame(parent, bg=self.CARD)
        frame.pack(fill="x", pady=(8, 2))
        tk.Label(frame, text=text, bg=self.CARD, fg=self.TEXT,
                 font=("Segoe UI", 10, "bold")).pack(side="left")
        tag = "optional" if optional else "required"
        color = self.MUTED if optional else self.GREEN
        tk.Label(frame, text=f"  ({tag})", bg=self.CARD, fg=color,
                 font=("Segoe UI", 9)).pack(side="left")
        return parent

    def _entry(self, parent, default=""):
        var = tk.StringVar(value=default)
        ttk.Entry(parent, textvariable=var).pack(fill="x")
        return var

    def _build(self):
        header = tk.Frame(self.root, bg=self.BG, padx=22, pady=16)
        header.pack(fill="x")
        tk.Label(header, text="Helix Node Installer", bg=self.BG, fg=self.TEXT,
                 font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(header, text="Fill in the settings, then set up and start your node.",
                 bg=self.BG, fg=self.MUTED, font=("Segoe UI", 10)).pack(anchor="w")

        card = tk.Frame(self.root, bg=self.CARD, padx=20, pady=12)
        card.pack(fill="both", expand=False, padx=18)

        self._label(card, "Node port", optional=True)
        self.port_var = self._entry(card, "8000")

        self._label(card, "Public URL — how others reach this node", optional=True)
        self.public_var = self._entry(card, "")

        self._label(card, "Bootstrap nodes — comma-separated URLs to auto-connect", optional=True)
        self.bootstrap_var = self._entry(card, "")

        self._label(card, "Admin API key — protects mine/sync/discover", optional=True)
        key_row = tk.Frame(card, bg=self.CARD)
        key_row.pack(fill="x")
        self.key_var = tk.StringVar(value="")
        ttk.Entry(key_row, textvariable=self.key_var).pack(side="left", fill="x", expand=True)
        tk.Button(key_row, text="Generate", command=self._generate_key, bg=self.ACCENT,
                  fg="white", relief="flat", padx=10, cursor="hand2").pack(side="left", padx=(8, 0))
        tk.Button(key_row, text="Copy", command=self._copy_key, bg=self.CARD, fg=self.TEXT,
                  relief="flat", padx=10, cursor="hand2").pack(side="left", padx=(6, 0))

        self.require_var = tk.BooleanVar(value=False)
        tk.Checkbutton(card, text="Require the admin key (turn on for a public node)",
                       variable=self.require_var, bg=self.CARD, fg=self.TEXT,
                       selectcolor=self.BG, activebackground=self.CARD,
                       activeforeground=self.TEXT, font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 0))

        self.tunnel_var = tk.BooleanVar(value=False)
        tk.Checkbutton(card, text="Expose with a Cloudflare tunnel after starting (optional)",
                       variable=self.tunnel_var, bg=self.CARD, fg=self.TEXT,
                       selectcolor=self.BG, activebackground=self.CARD,
                       activeforeground=self.TEXT, font=("Segoe UI", 9)).pack(anchor="w")

        self.open_ui_var = tk.BooleanVar(value=True)
        tk.Checkbutton(card, text="Open the wallet UI in my browser when ready",
                       variable=self.open_ui_var, bg=self.CARD, fg=self.TEXT,
                       selectcolor=self.BG, activebackground=self.CARD,
                       activeforeground=self.TEXT, font=("Segoe UI", 9)).pack(anchor="w")

        self.start_button = tk.Button(self.root, text="Set Up & Start Node", command=self._start,
                                      bg=self.ACCENT, fg="white", relief="flat", pady=11,
                                      font=("Segoe UI", 11, "bold"), cursor="hand2")
        self.start_button.pack(fill="x", padx=18, pady=(12, 8))

        log_wrap = tk.Frame(self.root, bg=self.BG, padx=18)
        log_wrap.pack(fill="both", expand=True, pady=(0, 14))
        self.log_widget = tk.Text(log_wrap, height=10, bg="#0a0d17", fg=self.MUTED,
                                  relief="flat", font=("Consolas", 9), wrap="word")
        self.log_widget.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(log_wrap, command=self.log_widget.yview)
        scroll.pack(side="right", fill="y")
        self.log_widget.configure(yscrollcommand=scroll.set, state="disabled")

    # ---- helpers ----------------------------------------------------------
    def _generate_key(self):
        self.key_var.set(secrets.token_hex(32))
        self.log("[*] Generated an admin key. It is optional — only needed if you tick "
                 "'Require the admin key' or host the Pages wallet (use the same value there).")

    def _copy_key(self):
        key = self.key_var.get().strip()
        if not key:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(key)
        self.log("[*] Admin key copied to clipboard.")

    def log(self, message):
        self.log_queue.put(message)

    def _drain_log(self):
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_widget.configure(state="normal")
                self.log_widget.insert("end", message + "\n")
                self.log_widget.see("end")
                self.log_widget.configure(state="disabled")
        except queue.Empty:
            pass
        self.root.after(120, self._drain_log)

    def _start(self):
        if self.busy:
            return
        self.busy = True
        self.start_button.configure(state="disabled", text="Working…")
        threading.Thread(target=self._run_setup, daemon=True).start()

    # ---- setup work (background thread) -----------------------------------
    def _run_setup(self):
        try:
            port = (self.port_var.get().strip() or "8000")
            if not port.isdigit():
                self.log("[X] Port must be a number.")
                return

            self._write_config(port)

            venv_python = self._ensure_venv()
            if not venv_python:
                return
            if not self._install_deps(venv_python):
                return

            self.log(f"[*] Starting the node on http://localhost:{port} …")
            env = os.environ.copy()
            env["NODE_PORT"] = port
            if self.key_var.get().strip():
                env["HELIX_ADMIN_API_KEY"] = self.key_var.get().strip()
            if self.require_var.get():
                env["HELIX_REQUIRE_ADMIN_API_KEY"] = "true"
            self._popen([str(venv_python), "run_node.py"], env=env, new_console=True)

            if self.tunnel_var.get():
                if shutil.which("cloudflared"):
                    self.log("[*] Opening a Cloudflare tunnel — copy the printed URL into Pages HELIX_NODE_URL.")
                    self._popen(["cloudflared", "tunnel", "--url", f"http://localhost:{port}"], new_console=True)
                else:
                    self.log("[!] cloudflared not found — the node runs locally only. Install cloudflared to expose it.")

            if self.open_ui_var.get():
                threading.Timer(4.0, lambda: webbrowser.open(f"http://localhost:{port}")).start()

            self.log("")
            self.log(f"[✓] Done. Wallet UI: http://localhost:{port}")
            self.log("    Close the node's terminal window to stop it.")
        except Exception as exc:  # keep the GUI alive on any error
            self.log(f"[X] Setup failed: {exc}")
        finally:
            self.busy = False
            self.root.after(0, lambda: self.start_button.configure(state="normal", text="Set Up & Start Node"))

    def _write_config(self, port):
        try:
            config = json.loads(CONFIG_FILE.read_text(encoding="utf-8")) if CONFIG_FILE.exists() else {}
        except (OSError, ValueError):
            config = {}
        config.setdefault("node", {})["port"] = int(port)
        network = config.setdefault("network", {})
        public = self.public_var.get().strip()
        if public:
            network["public_url"] = public.rstrip("/")
        bootstrap = [b.strip().rstrip("/") for b in self.bootstrap_var.get().split(",") if b.strip()]
        if bootstrap:
            network["bootstrap_nodes"] = bootstrap
        config.setdefault("security", {})["require_admin_api_key"] = bool(self.require_var.get())
        CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")
        self.log("[*] Saved settings to config.json.")

    def _ensure_venv(self):
        venv_python = ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
        if venv_python.exists():
            self.log("[*] Virtual environment already exists.")
            return venv_python
        self.log("[*] Creating virtual environment (.venv) …")
        result = subprocess.run([sys.executable, "-m", "venv", str(ROOT / ".venv")],
                                capture_output=True, text=True)
        if result.returncode != 0 or not venv_python.exists():
            self.log("[X] Could not create the virtual environment. Install Python 3.11+ first.")
            self.log(result.stderr.strip())
            return None
        return venv_python

    def _install_deps(self, venv_python):
        # Skip the whole install step if the required libraries are already present.
        check = subprocess.run(
            [str(venv_python), "-c", "import cryptography, fastapi, uvicorn, requests, mnemonic"],
            capture_output=True, text=True,
        )
        if check.returncode == 0:
            self.log("[*] Required libraries are already installed — skipping installation.")
            return True
        self.log("[*] Some libraries are missing. Installing dependencies (first run can take a minute) …")
        subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
                       capture_output=True, text=True)
        process = subprocess.Popen(
            [str(venv_python), "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")],
            cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        for line in process.stdout:
            line = line.rstrip()
            if line:
                self.log("    " + line)
        process.wait()
        if process.returncode != 0:
            self.log("[X] Dependency installation failed. See messages above.")
            return False
        self.log("[*] Dependencies installed.")
        return True

    def _popen(self, args, env=None, new_console=False):
        kwargs = {"cwd": str(ROOT)}
        if env is not None:
            kwargs["env"] = env
        if new_console and os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
        subprocess.Popen(args, **kwargs)


def main():
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass
    InstallerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
