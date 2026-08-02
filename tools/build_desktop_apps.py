"""Build Helix Windows executables and the cross-platform desktop bundle."""
from __future__ import annotations

import hashlib
import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
DOWNLOADS = ROOT / "web" / "downloads"
BUILD = ROOT / "build" / "desktop"
DIST = BUILD / "windows"
ICON = BUILD / "helix.ico"


def make_icon() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    with Image.open(ROOT / "web" / "icons" / "icon-512.png") as source:
        source.convert("RGBA").save(
            ICON,
            format="ICO",
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )


def build_executable(
    entry: str,
    name: str,
    hidden_imports: tuple[str, ...] = (),
    excluded_modules: tuple[str, ...] = (),
) -> Path:
    work = BUILD / "work" / name
    spec = BUILD / "spec"
    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onefile", "--windowed",
        "--name", name,
        "--icon", str(ICON),
        "--add-data", f"{ROOT / 'web' / 'icons' / 'icon-192.png'};.",
        "--distpath", str(DIST),
        "--workpath", str(work),
        "--specpath", str(spec),
    ]
    for module in hidden_imports:
        command.extend(("--hidden-import", module))
    for module in excluded_modules:
        command.extend(("--exclude-module", module))
    command.append(str(ROOT / entry))
    subprocess.run(command, cwd=ROOT, check=True)
    executable = DIST / f"{name}.exe"
    if not executable.is_file() or executable.stat().st_size < 1_000_000:
        raise RuntimeError(f"PyInstaller did not create a valid {executable.name}")
    if executable.stat().st_size > 200 * 1024 * 1024:
        raise RuntimeError(
            f"{executable.name} is unexpectedly larger than 200 MiB; "
            "an optional runtime was probably bundled"
        )
    shutil.copy2(executable, DOWNLOADS / executable.name)
    return executable


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_executable(archive: zipfile.ZipFile, source: Path, arcname: str) -> None:
    info = zipfile.ZipInfo.from_file(source, arcname)
    # The archive is produced on Windows, so identify these entries as Unix
    # files explicitly or Linux unzip tools discard the executable permission.
    info.create_system = 3
    info.external_attr = (0o100755 & 0xFFFF) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)


def build_wallet_archives(executables: list[Path]) -> list[Path]:
    # The checksum copy inside the Windows archive covers the executables. The
    # public manifest is rewritten below after both archives exist so it can
    # cover every desktop download too.
    checksums = [f"{sha256(path)}  {path.name}" for path in executables]
    checksums_path = DOWNLOADS / "SHA256SUMS-desktop.txt"
    checksums_path.write_text("\n".join(checksums) + "\n", encoding="utf-8")

    windows_target = DOWNLOADS / "helix-wallet-windows.zip"
    windows_temporary = windows_target.with_suffix(".zip.tmp")
    with zipfile.ZipFile(windows_temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.write(DOWNLOADS / "HELIX_DESKTOP_README.md", "README.md")
        archive.write(checksums_path, "SHA256SUMS.txt")
        archive.write(executables[0], executables[0].name)
    windows_temporary.replace(windows_target)

    linux_target = DOWNLOADS / "helix-wallet-linux.zip"
    linux_temporary = linux_target.with_suffix(".zip.tmp")
    with zipfile.ZipFile(linux_temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.write(DOWNLOADS / "HELIX_DESKTOP_README.md", "README.md")
        archive.write(ROOT / "desktop" / "linux" / "helix-wallet.desktop", "linux-wallet/helix-wallet.desktop")
        archive.write(ROOT / "web" / "icons" / "icon-192.png", "linux-wallet/helix-logo.png")
        write_executable(
            archive, ROOT / "desktop" / "linux" / "helix-wallet",
            "linux-wallet/helix-wallet",
        )
        write_executable(
            archive, ROOT / "desktop" / "linux" / "install-helix-wallet.sh",
            "linux-wallet/install-helix-wallet.sh",
        )
    linux_temporary.replace(linux_target)

    public_files = [*executables, windows_target, linux_target]
    checksums_path.write_text(
        "\n".join(f"{sha256(path)}  {path.name}" for path in public_files) + "\n",
        encoding="utf-8",
    )
    return [windows_target, linux_target]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundle-only", action="store_true",
        help="reuse already-built executables and only rebuild ZIP packages",
    )
    args = parser.parse_args()
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    if args.bundle_only:
        executables = [
            DIST / "HelixWallet.exe",
            DIST / "HelixMiner.exe",
            DIST / "HelixNodeSetup.exe",
        ]
        if any(not path.is_file() for path in executables):
            raise FileNotFoundError("run a full desktop build before --bundle-only")
    else:
        make_icon()
        executables = [
            build_executable("helix_wallet_desktop.py", "HelixWallet"),
            build_executable(
                "helix_miner.py",
                "HelixMiner",
                ("miner_cuda",),
                ("cupy", "cupy_backends", "numpy", "nvidia"),
            ),
            build_executable("install_node.py", "HelixNodeSetup"),
        ]
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_downloads.py")], cwd=ROOT, check=True)
    wallet_archives = build_wallet_archives(executables)
    for path in [*executables, *wallet_archives]:
        print(f"built {path.relative_to(ROOT)} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
