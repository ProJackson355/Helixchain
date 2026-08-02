"""Create and verify Ed25519-signed Helix release manifests."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def keygen(private_path: Path, public_path: Path) -> None:
    if private_path.exists() or public_path.exists():
        raise SystemExit("refusing to overwrite an existing signing key")
    private = Ed25519PrivateKey.generate()
    private_path.write_bytes(private.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ))
    public_path.write_bytes(private.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ))


def build(root: Path, version: str, private_path: Path, output: Path) -> None:
    private = serialization.load_pem_private_key(private_path.read_bytes(), password=None)
    if not isinstance(private, Ed25519PrivateKey):
        raise SystemExit("release key is not Ed25519")
    files = {
        path.relative_to(root).as_posix(): {
            "sha256": file_hash(path), "size": path.stat().st_size,
        }
        for path in sorted(root.rglob("*")) if path.is_file()
        and path.resolve() not in {output.resolve(), private_path.resolve()}
    }
    signed = {"format": 1, "product": "helixchain", "version": version, "files": files}
    canonical = json.dumps(signed, sort_keys=True, separators=(",", ":")).encode()
    document = {
        "signed": signed,
        "signature": base64.b64encode(private.sign(canonical)).decode(),
    }
    output.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def verify(root: Path, public_path: Path, manifest_path: Path) -> None:
    public = serialization.load_pem_public_key(public_path.read_bytes())
    if not isinstance(public, Ed25519PublicKey):
        raise SystemExit("release public key is not Ed25519")
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    canonical = json.dumps(document["signed"], sort_keys=True, separators=(",", ":")).encode()
    public.verify(base64.b64decode(document["signature"], validate=True), canonical)
    for relative, expected in document["signed"]["files"].items():
        path = root / relative
        if not path.is_file() or path.stat().st_size != expected["size"] or file_hash(path) != expected["sha256"]:
            raise SystemExit(f"release file verification failed: {relative}")
    print(f"verified {len(document['signed']['files'])} files")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    generate = subcommands.add_parser("keygen")
    generate.add_argument("private", type=Path)
    generate.add_argument("public", type=Path)
    create = subcommands.add_parser("build")
    create.add_argument("root", type=Path)
    create.add_argument("version")
    create.add_argument("private", type=Path)
    create.add_argument("output", type=Path)
    check = subcommands.add_parser("verify")
    check.add_argument("root", type=Path)
    check.add_argument("public", type=Path)
    check.add_argument("manifest", type=Path)
    args = parser.parse_args()
    if args.command == "keygen":
        keygen(args.private, args.public)
    elif args.command == "build":
        build(args.root, args.version, args.private, args.output)
    else:
        verify(args.root, args.public, args.manifest)


if __name__ == "__main__":
    main()
