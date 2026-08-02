"""Network and API hardening utilities for Helix nodes."""
from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import os
import threading
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Iterable

from fastapi.responses import JSONResponse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = Path(os.getenv("HELIX_SECURITY_STATE", PROJECT_ROOT / "security_state.json"))
DEFAULT_ADMIN_PATHS = (
    "/sync", "/nodes/sync_now", "/nodes/discover", "/nodes/audit",
    "/nodes/submissions", "/nodes/register", "/security/status",
)


class SecurityManager:
    def __init__(self, config: dict):
        self.config = config
        self._lock = threading.RLock()
        self._requests: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._violations: dict[str, deque[float]] = defaultdict(deque)
        self._bans: dict[str, float] = {}
        self._load()

    @property
    def max_body_bytes(self) -> int:
        return max(1024, int(self.config.get("max_request_body_bytes", 1_048_576)))

    def _load(self) -> None:
        try:
            raw = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            now = time.time()
            self._bans = {
                str(ip): float(until)
                for ip, until in raw.get("bans", {}).items()
                if float(until) > now
            }
        except (OSError, ValueError, TypeError):
            self._bans = {}

    def _save(self) -> None:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE_FILE.with_suffix(STATE_FILE.suffix + ".tmp")
        tmp.write_text(json.dumps({"bans": self._bans}, indent=2), encoding="utf-8")
        os.replace(tmp, STATE_FILE)

    def client_ip(self, scope: dict) -> str:
        client = scope.get("client")
        value = client[0] if client else "unknown"
        try:
            immediate = ipaddress.ip_address(value)
        except ValueError:
            return "unknown"
        if immediate.is_loopback and bool(
            self.config.get("trust_loopback_proxy_headers", False)
        ):
            headers = {
                key.decode().lower(): val.decode()
                for key, val in scope.get("headers", [])
            }
            forwarded = ""
            worker_forwarded = headers.get("x-helix-client-ip", "").strip()
            if worker_forwarded and self._proxy_headers_trusted(headers.get("x-helix-api-key")):
                forwarded = worker_forwarded
            if not forwarded:
                forwarded = headers.get("cf-connecting-ip", "").strip()
            if not forwarded:
                forwarded = headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
            if forwarded:
                try:
                    return str(ipaddress.ip_address(forwarded))
                except ValueError:
                    pass
        return str(immediate)

    @staticmethod
    def _is_loopback(ip: str) -> bool:
        """A same-host cloudflared tunnel always arrives from loopback. That
        address is trusted local infrastructure carrying every visitor, so it
        must never be banned -- doing so takes the whole node offline."""
        try:
            return ipaddress.ip_address(ip).is_loopback
        except ValueError:
            return False

    def is_banned(self, ip: str) -> bool:
        if self._is_loopback(ip):
            return False
        with self._lock:
            until = self._bans.get(ip, 0)
            if until <= time.time():
                if ip in self._bans:
                    del self._bans[ip]
                    self._save()
                return False
            return True

    def ban_remaining(self, ip: str) -> int:
        return max(0, int(self._bans.get(ip, 0) - time.time()))

    def report_violation(self, ip: str, weight: int = 1) -> None:
        if ip == "unknown" or self._is_loopback(ip):
            return
        now = time.time()
        window = int(self.config.get("violation_window_seconds", 300))
        threshold = int(self.config.get("ban_after_violations", 8))
        duration = int(self.config.get("ban_duration_seconds", 900))
        with self._lock:
            bucket = self._violations[ip]
            for _ in range(max(1, weight)):
                bucket.append(now)
            while bucket and bucket[0] < now - window:
                bucket.popleft()
            if len(bucket) >= threshold:
                self._bans[ip] = now + duration
                bucket.clear()
                self._save()

    def allow_request(self, ip: str, group: str) -> tuple[bool, int]:
        rules = self.config.get("rate_limits", {})
        rule = rules.get(group, rules.get("default", {"requests": 120, "window_seconds": 60}))
        limit = max(1, int(rule.get("requests", 120)))
        window = max(1, int(rule.get("window_seconds", 60)))
        now = time.time()
        with self._lock:
            bucket = self._requests[(ip, group)]
            while bucket and bucket[0] <= now - window:
                bucket.popleft()
            if len(bucket) >= limit:
                retry = max(1, int(window - (now - bucket[0])))
                self.report_violation(ip)
                return False, retry
            bucket.append(now)
            return True, 0

    def route_group(self, path: str) -> str:
        if path.startswith("/p2p/") or path in {"/receive_block", "/sync", "/nodes/register"}:
            return "p2p"
        if path == "/transaction" or (
            path.startswith("/transaction/") and path.endswith("/cancel")
        ):
            return "transactions"
        if path.startswith("/mining/"):
            return "external_mining"
        if path.startswith("/nodes/audit") or path.startswith("/nodes/discover") or path.startswith("/nodes/sync_now"):
            return "admin"
        return "default"

    def admin_required(self) -> bool:
        """Whether admin routes require a key. Optional by default so running a
        node needs no key at all; a public node can force it on with the
        HELIX_REQUIRE_ADMIN_API_KEY environment variable (overrides config)."""
        override = os.getenv("HELIX_REQUIRE_ADMIN_API_KEY")
        if override is not None:
            return override.strip().lower() in ("1", "true", "yes", "on")
        return bool(self.config.get("require_admin_api_key", False))

    def valid_api_key(self, supplied: str | None) -> bool:
        if not self.admin_required():
            return True
        return self._proxy_headers_trusted(supplied)

    def _proxy_headers_trusted(self, supplied: str | None) -> bool:
        """Whether a request carries the real, configured admin key.

        Unlike ``valid_api_key`` this never returns True just because admin
        auth is disabled. It gates trust of the ``x-helix-client-ip`` header
        that the Cloudflare Worker sets: because a same-host tunnel delivers
        every visitor from loopback, trusting that header without proving the
        caller is the Worker would let any direct caller spoof their IP (even
        to ``127.0.0.1``) and evade rate limits and bans. When no key is
        configured the header is ignored and the real edge IP
        (``cf-connecting-ip``) is used instead.
        """
        configured = str(os.getenv("HELIX_ADMIN_API_KEY", self.config.get("admin_api_key", "")))
        if not configured or not supplied:
            return False
        return hmac.compare_digest(configured, supplied)

    def status(self) -> dict:
        now = time.time()
        with self._lock:
            active = {ip: int(until - now) for ip, until in self._bans.items() if until > now}
        return {
            "active_bans": active,
            "max_request_body_bytes": self.max_body_bytes,
            "admin_api_key_required": self.admin_required(),
            "tls_enabled": bool(self.config.get("tls", {}).get("enabled", False)),
        }


class SecurityMiddleware:
    """Small ASGI middleware enforcing body-size, ban, rate, and admin-key rules."""

    def __init__(self, app, manager: SecurityManager):
        self.app = app
        self.manager = manager

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        ip = self.manager.client_ip(scope)
        path = scope.get("path", "")
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}

        if self.manager.is_banned(ip):
            response = JSONResponse(
                {"detail": "Client temporarily banned", "retry_after": self.manager.ban_remaining(ip)},
                status_code=403,
            )
            await response(scope, receive, send)
            return

        content_length = headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.manager.max_body_bytes:
                    self.manager.report_violation(ip, 2)
                    response = JSONResponse({"detail": "Request body too large"}, status_code=413)
                    await response(scope, receive, send)
                    return
            except ValueError:
                self.manager.report_violation(ip)
                response = JSONResponse({"detail": "Invalid Content-Length"}, status_code=400)
                await response(scope, receive, send)
                return

        group = self.manager.route_group(path)
        allowed, retry_after = self.manager.allow_request(ip, group)
        if not allowed:
            response = JSONResponse(
                {"detail": "Rate limit exceeded", "retry_after": retry_after},
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )
            await response(scope, receive, send)
            return

        admin_paths = tuple(self.manager.config.get("admin_paths", DEFAULT_ADMIN_PATHS))
        if admin_paths and any(path == item or path.startswith(item + "/") for item in admin_paths):
            if not self.manager.valid_api_key(headers.get("x-helix-api-key")):
                self.manager.report_violation(ip)
                response = JSONResponse({"detail": "Invalid or missing admin API key"}, status_code=401)
                await response(scope, receive, send)
                return

        consumed = 0

        async def limited_receive():
            nonlocal consumed
            message = await receive()
            if message.get("type") == "http.request":
                consumed += len(message.get("body", b""))
                if consumed > self.manager.max_body_bytes:
                    self.manager.report_violation(ip, 2)
                    raise RuntimeError("request body too large")
            return message

        try:
            await self.app(scope, limited_receive, send)
        except RuntimeError as exc:
            if str(exc) != "request body too large":
                raise
            response = JSONResponse({"detail": "Request body too large"}, status_code=413)
            await response(scope, receive, send)


class WebSecurityHeadersMiddleware:
    """Apply browser defenses when the node serves the bundled wallet UI."""

    _EXACT_PATHS = {
        "/", "/app.js", "/qrcode.js", "/pwa.js", "/jsqr.js",
        "/secp256k1.js", "/manifest.webmanifest", "/sw.js",
    }
    _PREFIXES = ("/icons/", "/downloads/")
    _HEADERS = {
        b"content-security-policy": (
            b"default-src 'self'; script-src 'self'; script-src-attr 'none'; "
            b"style-src 'self' 'unsafe-inline'; connect-src 'self' https:; "
            b"img-src 'self' data: https:; object-src 'none'; base-uri 'none'; "
            b"frame-ancestors 'none'; form-action 'self'"
        ),
        b"permissions-policy": b"camera=(self), microphone=(), geolocation=(), payment=(), usb=()",
        b"referrer-policy": b"no-referrer",
        b"x-content-type-options": b"nosniff",
        b"x-frame-options": b"DENY",
        b"cross-origin-opener-policy": b"same-origin",
        b"cross-origin-resource-policy": b"same-origin",
    }

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")
        is_web_asset = path in self._EXACT_PATHS or path.startswith(self._PREFIXES)

        async def secured_send(message):
            if is_web_asset and message.get("type") == "http.response.start":
                headers = list(message.get("headers", []))
                existing = {name.lower() for name, _ in headers}
                headers.extend(
                    (name, value) for name, value in self._HEADERS.items()
                    if name not in existing
                )
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, secured_send)


def validate_hex(value: object, name: str, lengths: Iterable[int]) -> str:
    if not isinstance(value, str) or len(value) not in set(lengths):
        raise ValueError(f"{name} has an invalid length")
    try:
        bytes.fromhex(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be hexadecimal") from exc
    return value


def safe_identifier(value: object, name: str, max_length: int = 128) -> str:
    if not isinstance(value, str) or not value or len(value) > max_length:
        raise ValueError(f"{name} is invalid")
    if any(ord(char) < 32 for char in value):
        raise ValueError(f"{name} contains control characters")
    return value


def payload_fingerprint(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
