"""Shared Helix branding for the Tk desktop applications."""
from __future__ import annotations

import os
from pathlib import Path
import tkinter as tk


def set_windows_app_id(app_name: str) -> None:
    """Give Windows a stable taskbar identity before ``Tk`` is created."""
    if os.name != "nt":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            f"HelixChain.{app_name}.1"
        )
    except (AttributeError, OSError):
        # Window creation should never fail just because branding is unavailable.
        pass


def find_helix_logo(base_dir: Path) -> Path | None:
    """Locate the logo in either a source checkout or a download bundle."""
    candidates = (
        base_dir / "helix-logo.png",
        base_dir / "icons" / "icon-192.png",
        base_dir / "web" / "icons" / "icon-192.png",
    )
    return next((path for path in candidates if path.is_file()), None)


def apply_helix_icon(root: tk.Tk, base_dir: Path) -> bool:
    """Apply and retain the Tk photo used by the title bar and taskbar."""
    logo_path = find_helix_logo(base_dir)
    if logo_path is None:
        return False
    try:
        icon = tk.PhotoImage(file=str(logo_path))
        root.iconphoto(True, icon)
        # Tk only keeps a Tcl-side reference on some platforms. Retaining the
        # Python object prevents the taskbar image from disappearing later.
        root._helix_icon = icon
        return True
    except tk.TclError:
        return False
