import tempfile
import unittest
from pathlib import Path

import node.node as node_api
from node.blockchain import Blockchain
from node.transaction import Transaction
from wallet.wallet import Wallet


class ExternalMiningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original_blockchain = node_api.blockchain
        self.original_broadcast = node_api.broadcast_block
        consensus = {
            "difficulty": 1,
            "min_difficulty": 1,
            "max_difficulty": 2,
            "difficulty_adjustment_interval": 10,
            "difficulty_activation_height": 10,
            "reward": 10,
            "max_supply": 1_000_000,
        }
        node_api.blockchain = Blockchain(consensus, Path(self.temp.name) / "external.json")
        node_api.broadcast_block = lambda _block: None

    def tearDown(self):
        node_api.blockchain = self.original_blockchain
        node_api.broadcast_block = self.original_broadcast
        self.temp.cleanup()

    def test_external_miner_can_solve_submit_and_lose_a_stale_race(self):
        address = "a" * 40
        work = node_api.external_mining_work(address)
        self.assertEqual(work["difficulty"], 1)
        self.assertEqual(work["block"]["index"], 1)
        candidate = node_api.dict_to_block(work["block"])
        candidate.mine(work["difficulty"])

        accepted = node_api.external_mining_submit({"block": node_api.block_to_dict(candidate)})
        self.assertTrue(accepted["accepted"])
        self.assertEqual(accepted["reward"], 10)
        self.assertEqual(node_api.blockchain.get_balance(address), 10)

        stale = node_api.external_mining_submit({"block": node_api.block_to_dict(candidate)})
        self.assertFalse(stale["accepted"])
        self.assertTrue(stale["stale"])

    def test_candidate_does_not_mutate_chain_before_submission(self):
        work = node_api.external_mining_work("b" * 40)
        self.assertEqual(len(node_api.blockchain.chain), 1)
        self.assertEqual(work["target_prefix"], "0")
        self.assertEqual(work["block"]["transactions"][-1]["receiver"], "b" * 40)

    def test_external_miner_preserves_nft_fields_when_submitting_block(self):
        creator = Wallet()
        nonce = "1" * 32
        attributes = [{"trait_type": "Rarity", "value": "Rare"}]
        nft = Transaction(
            creator.address,
            creator.address,
            0,
            tx_type="nft_mint",
            nft_id=Transaction.nft_address(creator.address, nonce),
            nonce=nonce,
            name="External NFT",
            description="Mined by an external miner",
            image="https://example.com/nft.png",
            uri="https://example.com/nft.json",
            metadata_hash=Transaction.nft_metadata_hash(
                "External NFT",
                "Mined by an external miner",
                "https://example.com/nft.png",
                attributes,
            ),
            attributes=attributes,
            royalty_bps=500,
        )
        nft.public_key = creator.public_key
        nft.sign(creator.private_key)
        self.assertTrue(node_api.blockchain.add_transaction(nft))

        work = node_api.external_mining_work(creator.address)
        candidate = node_api.dict_to_block(work["block"])
        candidate.mine_to_target(int(work["target"], 16))
        accepted = node_api.external_mining_submit({
            "block": node_api.block_to_dict(candidate),
        })

        self.assertTrue(accepted["accepted"], accepted)
        confirmed = node_api.blockchain.get_nft(nft.nft_id)
        self.assertEqual(confirmed["attributes"], attributes)
        self.assertEqual(confirmed["royalty_bps"], 500)


if __name__ == "__main__":
    unittest.main()
