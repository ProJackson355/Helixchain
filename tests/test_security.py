import unittest
import json
from pathlib import Path
from unittest.mock import patch

from node.security import SecurityManager, SecurityMiddleware, WebSecurityHeadersMiddleware


class SecurityClientIpTests(unittest.TestCase):
    @staticmethod
    def manager(trust=True):
        manager = SecurityManager.__new__(SecurityManager)
        manager.config = {"trust_loopback_proxy_headers": trust}
        return manager

    def test_loopback_cloudflare_proxy_uses_forwarded_client_ip(self):
        scope = {
            "client": ("127.0.0.1", 50000),
            "headers": [(b"cf-connecting-ip", b"203.0.113.42")],
        }
        self.assertEqual(self.manager().client_ip(scope), "203.0.113.42")

    def test_direct_remote_client_cannot_spoof_forwarded_ip(self):
        scope = {
            "client": ("198.51.100.8", 50000),
            "headers": [(b"cf-connecting-ip", b"203.0.113.42")],
        }
        self.assertEqual(self.manager().client_ip(scope), "198.51.100.8")

    def test_authenticated_worker_can_preserve_original_client_ip(self):
        manager = self.manager()
        manager.config.update({"require_admin_api_key": True, "admin_api_key": ""})
        scope = {
            "client": ("127.0.0.1", 50000),
            "headers": [
                (b"cf-connecting-ip", b"2a06:98c0:3600::103"),
                (b"x-helix-client-ip", b"198.51.100.25"),
                (b"x-helix-api-key", b"correct-secret"),
            ],
        }
        with patch.dict("os.environ", {"HELIX_ADMIN_API_KEY": "correct-secret"}):
            self.assertEqual(manager.client_ip(scope), "198.51.100.25")

    def test_unauthenticated_custom_client_ip_is_ignored(self):
        manager = self.manager()
        manager.config.update({"require_admin_api_key": True, "admin_api_key": ""})
        scope = {
            "client": ("127.0.0.1", 50000),
            "headers": [
                (b"cf-connecting-ip", b"203.0.113.42"),
                (b"x-helix-client-ip", b"198.51.100.25"),
                (b"x-helix-api-key", b"wrong-secret"),
            ],
        }
        with patch.dict("os.environ", {"HELIX_ADMIN_API_KEY": "correct-secret"}):
            self.assertEqual(manager.client_ip(scope), "203.0.113.42")

    def test_keyless_node_ignores_spoofed_client_ip_header(self):
        # Default posture: no admin key required. A direct caller reaching the
        # node through the loopback tunnel must not be able to spoof its IP via
        # x-helix-client-ip -- the real edge IP (cf-connecting-ip) wins.
        manager = self.manager()  # no require_admin_api_key -> defaults False
        scope = {
            "client": ("127.0.0.1", 50000),
            "headers": [
                (b"cf-connecting-ip", b"203.0.113.42"),
                (b"x-helix-client-ip", b"198.51.100.25"),
            ],
        }
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(manager.client_ip(scope), "203.0.113.42")

    def test_keyless_node_cannot_be_spoofed_to_loopback(self):
        # An attacker setting x-helix-client-ip to 127.0.0.1 must not become the
        # unbannable loopback identity when no admin key is configured.
        manager = self.manager()
        scope = {
            "client": ("127.0.0.1", 50000),
            "headers": [
                (b"cf-connecting-ip", b"203.0.113.42"),
                (b"x-helix-client-ip", b"127.0.0.1"),
            ],
        }
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(manager.client_ip(scope), "203.0.113.42")

    def test_invalid_forwarded_ip_falls_back_to_loopback(self):
        scope = {
            "client": ("127.0.0.1", 50000),
            "headers": [(b"x-forwarded-for", b"not-an-ip")],
        }
        self.assertEqual(self.manager().client_ip(scope), "127.0.0.1")

    def test_only_external_mining_routes_have_a_mining_rate_limit(self):
        manager = self.manager()
        self.assertEqual(manager.route_group("/mine/start"), "default")
        self.assertEqual(manager.route_group("/mining/work"), "external_mining")
        self.assertEqual(manager.route_group("/mining/submit"), "external_mining")

    def test_admin_key_fails_closed_and_accepts_only_exact_secret(self):
        manager = self.manager()
        manager.config.update({"require_admin_api_key": True, "admin_api_key": ""})
        with patch.dict("os.environ", {}, clear=True):
            self.assertFalse(manager.valid_api_key(None))
            self.assertFalse(manager.valid_api_key("guess"))
        with patch.dict("os.environ", {"HELIX_ADMIN_API_KEY": "correct-secret"}):
            self.assertFalse(manager.valid_api_key("wrong-secret"))
            self.assertTrue(manager.valid_api_key("correct-secret"))

    def test_sensitive_node_management_routes_are_admin_protected(self):
        config = json.loads(
            (Path(__file__).resolve().parents[1] / "config.json").read_text(encoding="utf-8")
        )
        protected = set(config["security"]["admin_paths"])
        self.assertTrue({
            "/sync", "/nodes/register", "/nodes/submissions",
            "/nodes/discover", "/nodes/audit", "/security/status",
        }.issubset(protected))


class WebSecurityHeadersTests(unittest.IsolatedAsyncioTestCase):
    async def test_wallet_assets_receive_browser_security_headers(self):
        async def app(scope, receive, send):
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok"})

        messages = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            messages.append(message)

        middleware = WebSecurityHeadersMiddleware(app)
        await middleware({"type": "http", "path": "/"}, receive, send)
        headers = dict(messages[0]["headers"])
        self.assertEqual(headers[b"x-frame-options"], b"DENY")
        self.assertIn(b"script-src 'self'", headers[b"content-security-policy"])
        self.assertNotIn(b"https://esm.sh", headers[b"content-security-policy"])

    async def test_api_responses_do_not_receive_static_asset_corp_header(self):
        async def app(scope, receive, send):
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"{}"})

        messages = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            messages.append(message)

        await WebSecurityHeadersMiddleware(app)(
            {"type": "http", "path": "/health"}, receive, send
        )
        self.assertNotIn(b"cross-origin-resource-policy", dict(messages[0]["headers"]))


class AdminMiddlewareFailClosedTests(unittest.IsolatedAsyncioTestCase):
    async def test_admin_routes_remain_protected_when_config_omits_path_list(self):
        async def app(scope, receive, send):
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok"})

        manager = SecurityManager({
            "require_admin_api_key": True,
            "admin_api_key": "correct-secret",
            "rate_limits": {"default": {"requests": 10, "window_seconds": 60}},
        })
        messages = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            messages.append(message)

        await SecurityMiddleware(app, manager)(
            {"type": "http", "path": "/nodes/register", "client": ("198.51.100.8", 1), "headers": []},
            receive,
            send,
        )
        self.assertEqual(messages[0]["status"], 401)


if __name__ == "__main__":
    unittest.main()
