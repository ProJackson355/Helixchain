"""Launch a Helix node with optional TLS settings from config.json."""
from __future__ import annotations
import json
import os
from pathlib import Path
import uvicorn

ROOT = Path(__file__).resolve().parent
CONFIG = Path(os.getenv("HELIX_CONFIG", ROOT / "config.json"))


def load_config() -> dict:
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}


def main():
    config = load_config()
    node = config.get("node", {})
    tls = config.get("security", {}).get("tls", {})
    kwargs = {
        "host": os.getenv("HELIX_HOST", "0.0.0.0"),
        "port": int(os.getenv("NODE_PORT", node.get("port", 8000))),
        "server_header": False,
        "date_header": False,
        "proxy_headers": False,
    }
    if tls.get("enabled"):
        cert = Path(str(tls.get("cert_file", "")))
        key = Path(str(tls.get("key_file", "")))
        if not cert.is_file() or not key.is_file():
            raise SystemExit("TLS is enabled, but cert_file or key_file is missing")
        kwargs.update(ssl_certfile=str(cert), ssl_keyfile=str(key))
    uvicorn.run("node.node:app", **kwargs)


if __name__ == "__main__":
    main()
