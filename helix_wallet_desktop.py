"""Native launcher for the hosted Helix wallet desktop experience."""
from __future__ import annotations

import os
import shutil
import subprocess
import webbrowser
from pathlib import Path
from tkinter import Tk, messagebox


WALLET_URL = os.getenv("HELIX_WALLET_URL", "https://wallet.hlxchain.com/")


def browser_candidates() -> list[Path | str]:
    candidates: list[Path | str] = []
    if os.name == "nt":
        for variable in ("PROGRAMFILES(X86)", "PROGRAMFILES", "LOCALAPPDATA"):
            base = os.getenv(variable)
            if not base:
                continue
            candidates.extend((
                Path(base) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
                Path(base) / "Google" / "Chrome" / "Application" / "chrome.exe",
            ))
    candidates.extend(("msedge", "google-chrome", "chromium", "chromium-browser"))
    return candidates


def find_app_browser() -> str | None:
    for candidate in browser_candidates():
        if isinstance(candidate, Path) and candidate.is_file():
            return str(candidate)
        if isinstance(candidate, str):
            resolved = shutil.which(candidate)
            if resolved:
                return resolved
    return None


def launch() -> bool:
    browser = find_app_browser()
    try:
        if browser:
            subprocess.Popen([browser, f"--app={WALLET_URL}", "--start-maximized"])
            return True
        return bool(webbrowser.open(WALLET_URL, new=1))
    except OSError:
        return False


def main() -> None:
    if launch():
        return
    root = Tk()
    root.withdraw()
    messagebox.showerror(
        "Helix Wallet",
        f"Could not open the wallet. Open this address manually:\n\n{WALLET_URL}",
    )
    root.destroy()
    raise SystemExit(1)


if __name__ == "__main__":
    main()
