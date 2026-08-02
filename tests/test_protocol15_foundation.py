import tempfile
import unittest
from pathlib import Path

from node.blockchain import Blockchain
from node.transaction import Transaction
from wallet.wallet import Wallet


class Protocol15FoundationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.database = Path(self.temporary.name) / "chain.json"
        self.consensus = {
            "difficulty": 1,
            "min_difficulty": 1,
            "max_difficulty": 2,
            "difficulty_activation_height": 10_000,
            "reward": 10,
            "transaction_fee": 1,
            "transaction_fee_activation_height": 1,
            "canonical_signature_activation_height": 1,
            "chain_id": "helix-test-v1",
            "transaction_envelope_activation_height": 1,
            "max_transaction_lifetime_blocks": 20,
            "max_supply": 1_000,
            "checkpoints": {},
        }
        self.chain = Blockchain(self.consensus, self.database)
        self.sender = Wallet()
        self.receiver = Wallet()
        self.miner = Wallet()
        self.chain.mine_pending_transactions(self.sender.address)

    def tearDown(self):
        self.temporary.cleanup()

    def signed(self, *, tx_type="transfer", amount=3, fee=1, sequence=0,
               chain_id="helix-test-v1", valid_until_height=10):
        receiver = self.sender.address if tx_type == "cancel" else self.receiver.address
        tx = Transaction(
            self.sender.address, receiver, amount,
            public_key=self.sender.public_key, fee=fee, tx_type=tx_type,
            chain_id=chain_id, sequence=sequence,
            valid_until_height=valid_until_height,
        )
        tx.sign(self.sender.private_key)
        return tx

    def test_chain_replay_expiry_and_sequence_are_enforced(self):
        wrong_chain = self.signed(chain_id="another-chain")
        self.assertIn("chain_id", self.chain.transaction_rejection_reason(wrong_chain))

        expired = self.signed(valid_until_height=0)
        self.assertIn("expired", self.chain.transaction_rejection_reason(expired))

        skipped = self.signed(sequence=1)
        self.assertIn("sequence must be 0", self.chain.transaction_rejection_reason(skipped))

    def test_higher_fee_cancel_replaces_and_consumes_sequence(self):
        original = self.signed(amount=3, fee=1)
        self.assertTrue(self.chain.add_transaction(original))

        too_cheap = self.signed(tx_type="cancel", amount=0, fee=1)
        self.assertFalse(self.chain.add_transaction(too_cheap))

        cancel = self.signed(tx_type="cancel", amount=0, fee=2)
        self.assertTrue(self.chain.add_transaction(cancel))
        self.assertEqual([tx.tx_id for tx in self.chain.pending_transactions], [cancel.tx_id])

        self.chain.mine_pending_transactions(self.miner.address)
        block = self.chain.chain[-1]
        self.assertEqual(
            block.transaction_root,
            self.chain.transaction_merkle_root(block.transactions),
        )
        self.assertEqual(len(block.state_root), 64)
        self.assertEqual(self.chain.confirmed_sequence(self.sender.address), 1)
        self.assertEqual(self.chain.get_balance(self.receiver.address), 0)
        self.assertIn("sequence must be 1", self.chain.transaction_rejection_reason(original))

    def test_sqlite_import_and_reload(self):
        sqlite_consensus = {
            **self.consensus,
            "storage_backend": "sqlite",
            "storage_snapshot_interval": 1,
        }
        sqlite_database = Path(self.temporary.name) / "sqlite-chain.json"
        chain = Blockchain(sqlite_consensus, sqlite_database)
        chain.mine_pending_transactions(self.sender.address)
        sqlite_path = sqlite_database.with_suffix(".sqlite3")
        self.assertTrue(sqlite_path.exists())

        reloaded = Blockchain(sqlite_consensus, sqlite_database)
        self.assertEqual(reloaded.chain[-1].hash, chain.chain[-1].hash)
        self.assertEqual(reloaded.validate_chain(reloaded.chain), (True, None))
        self.assertTrue(reloaded._state_store.list_snapshots())


if __name__ == "__main__":
    unittest.main()
