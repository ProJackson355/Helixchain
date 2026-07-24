import unittest
from unittest.mock import patch

from node.security import SecurityManager


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

    def test_invalid_forwarded_ip_falls_back_to_loopback(self):
        scope = {
            "client": ("127.0.0.1", 50000),
            "headers": [(b"x-forwarded-for", b"not-an-ip")],
        }
        self.assertEqual(self.manager().client_ip(scope), "127.0.0.1")

    def test_background_mining_routes_share_mining_rate_limit(self):
        manager = self.manager()
        self.assertEqual(manager.route_group("/mine/start"), "mining")
        self.assertEqual(manager.route_group("/mine/status/" + "a" * 32), "mining")
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


if __name__ == "__main__":
    unittest.main()
