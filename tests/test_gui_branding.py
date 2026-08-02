import unittest
from pathlib import Path

from gui_branding import find_helix_logo


ROOT = Path(__file__).resolve().parents[1]


class GuiBrandingTests(unittest.TestCase):
    def test_source_checkout_logo_is_found(self):
        self.assertEqual(find_helix_logo(ROOT), ROOT / "web" / "icons" / "icon-192.png")

    def test_all_gui_entry_points_apply_shared_branding(self):
        for filename in ("install_node.py", "install_pool.py", "helix_miner.py"):
            with self.subTest(filename=filename):
                source = (ROOT / filename).read_text(encoding="utf-8")
                self.assertIn("set_windows_app_id(", source)
                self.assertIn("apply_helix_icon(", source)


if __name__ == "__main__":
    unittest.main()
