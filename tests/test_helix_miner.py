import unittest
from pathlib import Path

from helix_miner import TIP_POLL_INTERVAL, block_hash, find_solution, format_elapsed, parse_node_urls
from miner_cuda import canonical_block_hash, canonical_block_parts


class HelixMinerTests(unittest.TestCase):
    def test_miner_ui_has_page_and_log_scrolling(self):
        source = Path("helix_miner.py").read_text(encoding="utf-8")
        self.assertIn("self.scroll_canvas = tk.Canvas", source)
        self.assertIn("command=self.scroll_canvas.yview", source)
        self.assertIn("command=self.log_widget.yview", source)
        self.assertIn('self.root.bind_all("<MouseWheel>"', source)

    def test_elapsed_time_format_and_fast_tip_refresh(self):
        self.assertEqual(format_elapsed(4.125), "4.12 seconds")
        self.assertEqual(format_elapsed(65.2), "1m 05.2s")
        self.assertLessEqual(TIP_POLL_INTERVAL, 1.0)

    def test_node_url_formats(self):
        self.assertEqual(
            parse_node_urls('https://one.example, https://two.example/'),
            ['https://one.example', 'https://two.example'],
        )
        self.assertEqual(
            parse_node_urls('["http://127.0.0.1:8000", "https://node.example"]'),
            ['http://127.0.0.1:8000', 'https://node.example'],
        )
        with self.assertRaises(ValueError):
            parse_node_urls('javascript:alert(1)')

    def test_python_miner_finds_consensus_hash(self):
        block = {
            'index': 1,
            'transactions': [],
            'previous_hash': '0' * 64,
            'timestamp': 123.25,
            'nonce': 0,
            'hash': '',
        }
        solved, hashes = find_solution(block, difficulty=2, max_hashes=100_000)
        self.assertIsNotNone(solved)
        self.assertGreater(hashes, 0)
        self.assertTrue(solved['hash'].startswith('00'))
        self.assertEqual(solved['hash'], block_hash(solved))

    def test_cuda_nonce_template_matches_consensus_serialization(self):
        block = {
            'index': 7,
            'transactions': [{'nonce': '00' * 16, 'amount': 2}],
            'previous_hash': 'a' * 64,
            'timestamp': 123.25,
            'nonce': 999,
            'hash': 'ignored while mining',
        }
        prefix, suffix = canonical_block_parts(block)
        self.assertTrue(prefix.endswith(b'"nonce":'))
        self.assertGreater(len(suffix), 0)
        for nonce in (0, 9, 10, 999, 4_294_967_297, 18_446_744_073_709_551_615):
            self.assertEqual(canonical_block_hash(block, nonce), block_hash(block, nonce))


if __name__ == '__main__':
    unittest.main()
