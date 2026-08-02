import sys
import unittest
from pathlib import Path

from install_pool import (
    PoolSettings,
    PoolSetupApp,
    WEB_LEGACY_RECOVERY_WORDS,
    cloudflared_command,
    pool_environment,
    validate_settings,
)
from wallet.wallet import Wallet


VALID_SEED = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"


class PoolGuiTests(unittest.TestCase):
    def test_pool_settings_create_expected_process_environment(self):
        settings = PoolSettings(
            nodes="https://one.example,https://two.example",
            public_url="https://pool.example",
            port=8123,
            fee_percent=2.5,
            share_subtract=3,
            min_share_difficulty=2,
        )
        self.assertEqual(validate_settings(settings, VALID_SEED), [])
        env = pool_environment(settings, VALID_SEED)
        self.assertEqual(env["HELIX_POOL_PORT"], "8123")
        self.assertEqual(env["HELIX_POOL_FEE_PERCENT"], "2.5")
        self.assertEqual(env["HELIX_POOL_NODE"], settings.nodes)
        self.assertEqual(env["HELIX_POOL_SEED"], VALID_SEED)
        self.assertEqual(env["HELIX_POOL_SEED_FORMAT"], "web")

    def test_web_and_python_seed_derivations_are_explicit_and_stable(self):
        web_wallet = Wallet.from_web_seed_phrase(VALID_SEED)
        same_web_wallet = Wallet.from_web_seed_phrase(VALID_SEED)
        python_wallet = Wallet.from_seed_phrase(VALID_SEED)
        self.assertEqual(web_wallet.address, same_web_wallet.address)
        self.assertNotEqual(web_wallet.address, python_wallet.address)
        self.assertRegex(web_wallet.address, r"^[0-9a-f]{40}$")

    def test_legacy_website_recovery_words_remain_supported(self):
        self.assertIn("errupt", WEB_LEGACY_RECOVERY_WORDS)
        legacy_seed = "errupt " + " ".join(VALID_SEED.split()[1:])
        wallet = Wallet.from_web_seed_phrase(legacy_seed)
        self.assertRegex(wallet.address, r"^[0-9a-f]{40}$")
        app = PoolSetupApp.__new__(PoolSetupApp)
        self.assertTrue(app._validate_seed(Path(sys.executable), legacy_seed, "web"))

    def test_invalid_pool_settings_are_rejected(self):
        settings = PoolSettings(nodes="not-a-url", public_url="http://unsafe.example", port=70000,
                                fee_percent=101, share_subtract=20, min_share_difficulty=0)
        errors = validate_settings(settings, "too short")
        self.assertGreaterEqual(len(errors), 6)

    def test_cloudflare_token_and_quick_tunnel_commands(self):
        named = cloudflared_command("cloudflared", 8100, "secret-token")
        self.assertEqual(named, ["cloudflared", "tunnel", "run", "--token", "secret-token"])
        quick = cloudflared_command("cloudflared", 8123)
        self.assertEqual(quick, ["cloudflared", "tunnel", "--url", "http://localhost:8123"])

    def test_node_gui_has_masked_cloudflare_token_input(self):
        source = Path("install_node.py").read_text(encoding="utf-8")
        self.assertIn("self.cf_token_var", source)
        self.assertIn('show="•"', source)
        self.assertIn('["cloudflared", "tunnel", "run", "--token", token]', source)
        self.assertNotIn('config["cloudflare_token"]', source)


if __name__ == "__main__":
    unittest.main()
