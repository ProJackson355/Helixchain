import threading
import time
import unittest
from types import SimpleNamespace

import node.node as node_api


class MiningJobTests(unittest.TestCase):
    def setUp(self):
        self.original_blockchain = node_api.blockchain
        self.original_broadcast = node_api.broadcast_block
        with node_api._mining_jobs_lock:
            node_api._mining_jobs.clear()
            node_api._active_mining_job = None

    def tearDown(self):
        node_api.blockchain = self.original_blockchain
        node_api.broadcast_block = self.original_broadcast

    def test_background_job_completes_and_duplicate_start_reuses_it(self):
        release = threading.Event()
        reward = SimpleNamespace(amount=10)
        block = SimpleNamespace(index=52, hash="a" * 64, transactions=[reward])

        class FakeBlockchain:
            @staticmethod
            def mine_pending_transactions(_address):
                release.wait(2)
                return block

        node_api.blockchain = FakeBlockchain()
        node_api.broadcast_block = lambda _block: None

        first = node_api.start_mining("b" * 40)
        second = node_api.start_mining("b" * 40)
        self.assertEqual(first["job_id"], second["job_id"])
        self.assertEqual(second["status"], "mining")

        release.set()
        deadline = time.time() + 2
        result = node_api.mining_status(first["job_id"])
        while result["status"] == "mining" and time.time() < deadline:
            time.sleep(0.01)
            result = node_api.mining_status(first["job_id"])

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["block"], 52)
        self.assertEqual(result["hash"], "a" * 64)


if __name__ == "__main__":
    unittest.main()
