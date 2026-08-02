import json
import unittest
from pathlib import Path

from node.blockchain import Blockchain
from node.transaction import Transaction


class ConsensusVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).parent / "fixtures" / "protocol15_vectors.json"
        cls.vector = json.loads(path.read_text(encoding="utf-8"))

    def test_transaction_canonical_encoding_and_id(self):
        item = self.vector["transaction"]
        tx = Transaction(
            item["sender"], item["receiver"], item["amount"], fee=item["fee"],
            chain_id=self.vector["chain_id"], sequence=item["sequence"],
            valid_until_height=item["valid_until_height"],
        )
        self.assertEqual(tx.data(), item["canonical_data"])
        self.assertEqual(tx.generate_id(), item["unsigned_id"])

    def test_merkle_and_state_roots(self):
        merkle = self.vector["merkle"]
        transactions = []
        for tx_id in merkle["transaction_ids"]:
            tx = Transaction("a" * 40, "b" * 40, 1)
            tx.tx_id = tx_id
            transactions.append(tx)
        self.assertEqual(Blockchain.transaction_merkle_root(transactions), merkle["root"])

        state = self.vector["state"]
        self.assertEqual(
            Blockchain.state_root(state["balances"], {}, {}, {}, {}),
            state["root"],
        )


if __name__ == "__main__":
    unittest.main()
