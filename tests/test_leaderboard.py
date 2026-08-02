import tempfile
import unittest
from pathlib import Path

from node.blockchain import Blockchain
from wallet.wallet import Wallet


class WalletLeaderboardTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.chain = Blockchain({
            "difficulty": 1,
            "min_difficulty": 1,
            "max_difficulty": 2,
            "difficulty_activation_height": 10_000,
            "reward": 10,
            "mining_reward_activation_height": 10_000,
            "fractional_reward_activation_height": 10_000,
            "transaction_fee_activation_height": 10_000,
            "transaction_envelope_activation_height": 10_000,
            "state_commitment_activation_height": 10_000,
            "max_supply": 1_000,
            "checkpoints": {},
        }, Path(self.temporary.name) / "leaderboard.json")
        self.first = Wallet()
        self.second = Wallet()

    def tearDown(self):
        self.temporary.cleanup()

    def test_confirmed_hlx_and_pooled_tokens_are_ranked_and_charted(self):
        self.chain.mine_pending_transactions(self.first.address)
        self.chain.mine_pending_transactions(self.first.address)
        self.chain.mine_pending_transactions(self.second.address)

        rows = self.chain.wallet_leaderboard()
        self.assertEqual(rows[0]["address"], self.first.address)
        self.assertEqual(rows[0]["estimated_total_hlx"], "20")

        mint = "c" * 40
        self.chain._tokens[mint] = {
            "pool_hlx_reserve": 100,
            "pool_token_reserve": 1000,
        }
        self.chain._token_balances[(mint, self.second.address)] = 500
        rows = self.chain.wallet_leaderboard()
        self.assertEqual(rows[0]["address"], self.second.address)
        self.assertEqual(rows[0]["estimated_token_value_hlx"], "50")
        self.assertEqual(rows[0]["estimated_total_hlx"], "60")

        points = self.chain.wallet_value_history(self.first.address)
        self.assertEqual(len(points), 3)
        self.assertEqual(points[-1]["worth_hlx"], "20")


if __name__ == "__main__":
    unittest.main()
