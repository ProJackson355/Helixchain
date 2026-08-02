import tempfile
import unittest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.utils import (
    decode_dss_signature,
    encode_dss_signature,
)

from node.blockchain import Blockchain
from node.transaction import SECP256K1_ORDER, Transaction
from wallet.wallet import Wallet


class TransactionFeeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.database = Path(self.temporary.name) / "fees.json"
        self.consensus = {
            "difficulty": 1,
            "min_difficulty": 1,
            "max_difficulty": 2,
            "difficulty_activation_height": 10_000,
            "reward": 10,
            "mining_reward_activation_height": 10_000,
            "fractional_reward_activation_height": 10_000,
            "transaction_fee": 1,
            "transaction_fee_activation_height": 1,
            "canonical_signature_activation_height": 1,
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

    def signed_transfer(self, amount=4, fee=1):
        tx = Transaction(
            self.sender.address, self.receiver.address, amount,
            public_key=self.sender.public_key, fee=fee,
        )
        tx.sign(self.sender.private_key)
        return tx

    def test_fee_is_signed_paid_to_miner_and_not_new_supply(self):
        tx = self.signed_transfer()
        self.assertTrue(self.chain.add_transaction(tx))
        block = self.chain.mine_pending_transactions(self.miner.address)

        self.assertEqual(block.transactions[0].fee, 1)
        self.assertEqual(self.chain.get_balance(self.sender.address), 5)
        self.assertEqual(self.chain.get_balance(self.receiver.address), 4)
        self.assertEqual(self.chain.get_balance(self.miner.address), 11)
        self.assertEqual(self.chain.get_total_supply(), 20)

        reloaded = Blockchain(self.consensus, self.database)
        self.assertEqual(reloaded.validate_chain(reloaded.chain), (True, None))
        self.assertEqual(reloaded.get_balance(self.miner.address), 11)
        self.assertEqual(reloaded.get_total_supply(), 20)

    def test_missing_underpaid_and_overspending_fees_are_rejected(self):
        missing = Transaction(
            self.sender.address, self.receiver.address, 1,
            public_key=self.sender.public_key,
        )
        missing.sign(self.sender.private_key)
        self.assertIn("fee is required", self.chain.transaction_rejection_reason(missing))

        underpaid = self.signed_transfer(amount=1, fee=0)
        self.assertIn("at least 1 HLX", self.chain.transaction_rejection_reason(underpaid))

        overspend = self.signed_transfer(amount=10, fee=1)
        self.assertIn("available HLX balance", self.chain.transaction_rejection_reason(overspend))

    def test_fee_tampering_breaks_the_signature(self):
        tx = self.signed_transfer()
        self.assertTrue(tx.verify_signature())
        tx.fee = 2
        self.assertFalse(tx.verify_signature())

    def test_malleated_signature_cannot_replay_a_transaction(self):
        tx = self.signed_transfer()
        self.assertTrue(tx.signature_is_canonical())
        canonical_id = tx.canonical_id()
        r, s = decode_dss_signature(bytes.fromhex(tx.signature))
        tx.signature = encode_dss_signature(r, SECP256K1_ORDER - s).hex()
        tx.tx_id = tx.calculate_id()

        # The high-S twin is mathematically valid ECDSA and has a different
        # transaction ID, which is why explicit canonical enforcement matters.
        self.assertTrue(tx.verify_signature())
        self.assertFalse(tx.signature_is_canonical())
        self.assertEqual(tx.canonical_id(), canonical_id)
        self.assertIn(
            "canonical low-S",
            self.chain.transaction_rejection_reason(tx),
        )


if __name__ == "__main__":
    unittest.main()
