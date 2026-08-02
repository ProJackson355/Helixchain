import tempfile
import unittest
from pathlib import Path

from node.blockchain import Blockchain
from node.transaction import Transaction
from wallet.wallet import Wallet


class NftMarketplaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.consensus = {
                "difficulty": 1,
                "min_difficulty": 1,
                "max_difficulty": 2,
                "difficulty_activation_height": 10_000,
                "nft_activation_height": 1,
                "nft_market_activation_height": 1,
                "reward": 10,
                "mining_reward_activation_height": 10_000,
                "fractional_reward_activation_height": 10_000,
                "max_supply": 1_000_000,
        }
        self.database = Path(self.temp.name) / "nft-market.json"
        self.chain = Blockchain(self.consensus, self.database)
        self.creator = Wallet()
        self.seller = Wallet()
        self.bidder = Wallet()
        self.other_bidder = Wallet()
        self.miner = Wallet()
        self.nft_id = self._mint_nft(royalty_bps=1000)

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def _signed(wallet, tx_type, receiver, amount, nft_id, nonce, **extra):
        tx = Transaction(
            wallet.address,
            receiver,
            amount,
            tx_type=tx_type,
            nft_id=nft_id,
            nonce=nonce,
            **extra,
        )
        tx.public_key = wallet.public_key
        tx.sign(wallet.private_key)
        return tx

    def _mine(self, address=None):
        block = self.chain.mine_pending_transactions(address or self.miner.address)
        self.assertIsNotNone(block)
        return block

    def _fund(self, wallet, blocks=1):
        for _ in range(blocks):
            self._mine(wallet.address)

    def _mint_nft(self, royalty_bps):
        nonce = "0" * 32
        attributes = [{"trait_type": "Rarity", "value": "Rare"}]
        nft_id = Transaction.nft_address(self.creator.address, nonce)
        tx = Transaction(
            self.creator.address,
            self.creator.address,
            0,
            tx_type="nft_mint",
            nft_id=nft_id,
            nonce=nonce,
            name="Market NFT",
            description="An escrow marketplace test",
            image="https://example.com/nft.png",
            uri="https://example.com/nft.json",
            metadata_hash=Transaction.nft_metadata_hash(
                "Market NFT", "An escrow marketplace test",
                "https://example.com/nft.png", attributes,
            ),
            attributes=attributes,
            royalty_bps=royalty_bps,
        )
        tx.public_key = self.creator.public_key
        tx.sign(self.creator.private_key)
        self.assertTrue(self.chain.add_transaction(tx))
        self._mine()
        return nft_id

    def _transfer_to_seller_and_list(self, price=12):
        move = self._signed(
            self.creator, "nft_transfer", self.seller.address, 0,
            self.nft_id, "1" * 32,
        )
        self.assertTrue(self.chain.add_transaction(move))
        self._mine()
        listing = self._signed(
            self.seller, "nft_list", self.seller.address, price,
            self.nft_id, "2" * 32,
        )
        self.assertTrue(self.chain.add_transaction(listing))
        self._mine()

    def test_escrowed_bid_acceptance_transfers_nft_and_pays_royalty(self):
        self._transfer_to_seller_and_list()
        self._fund(self.bidder, 2)
        bidder_before = self.chain.get_balance(self.bidder.address)
        seller_before = self.chain.get_balance(self.seller.address)
        creator_before = self.chain.get_balance(self.creator.address)

        bid = self._signed(
            self.bidder, "nft_bid", self.seller.address, 10,
            self.nft_id, "3" * 32,
        )
        self.assertTrue(self.chain.add_transaction(bid))
        self._mine()
        self.assertEqual(self.chain.get_balance(self.bidder.address), bidder_before - 10)
        self.assertEqual(self.chain.get_nft(self.nft_id)["bids"][self.bidder.address]["amount"], 10)

        accept = self._signed(
            self.seller, "nft_accept_bid", self.bidder.address, 0,
            self.nft_id, "4" * 32,
        )
        self.assertTrue(self.chain.add_transaction(accept))
        self._mine()

        nft = self.chain.get_nft(self.nft_id)
        self.assertEqual(nft["owner"], self.bidder.address)
        self.assertEqual(nft["last_sale_price"], 10)
        self.assertEqual(nft["sale_count"], 1)
        self.assertEqual(nft["bids"], {})
        self.assertEqual(self.chain.get_balance(self.seller.address), seller_before + 9)
        self.assertEqual(self.chain.get_balance(self.creator.address), creator_before + 1)
        market = self.chain.get_nft_market_history(self.nft_id)
        self.assertEqual(len(market), 1)
        self.assertEqual(market[0]["price"], 10)
        self.assertEqual(market[0]["buyer"], self.bidder.address)

        reloaded = Blockchain(self.consensus, self.database)
        valid, reason = reloaded.validate_chain(reloaded.chain)
        self.assertTrue(valid, reason)
        self.assertEqual(reloaded.get_nft(self.nft_id)["owner"], self.bidder.address)
        self.assertEqual(reloaded.get_nft(self.nft_id)["last_sale_price"], 10)
        self.assertEqual(reloaded.get_balance(self.seller.address), seller_before + 9)

    def test_cancel_bid_refunds_escrow(self):
        self._transfer_to_seller_and_list()
        self._fund(self.bidder)
        starting = self.chain.get_balance(self.bidder.address)
        bid = self._signed(
            self.bidder, "nft_bid", self.seller.address, 6,
            self.nft_id, "5" * 32,
        )
        self.assertTrue(self.chain.add_transaction(bid))
        self._mine()
        cancel = self._signed(
            self.bidder, "nft_cancel_bid", self.bidder.address, 0,
            self.nft_id, "6" * 32,
        )
        self.assertTrue(self.chain.add_transaction(cancel))
        self._mine()
        self.assertEqual(self.chain.get_balance(self.bidder.address), starting)
        self.assertEqual(self.chain.get_nft(self.nft_id)["bids"], {})

    def test_direct_buy_refunds_other_bids_and_records_market_value(self):
        self._transfer_to_seller_and_list(price=8)
        self._fund(self.bidder)
        self._fund(self.other_bidder)
        other_start = self.chain.get_balance(self.other_bidder.address)
        bid = self._signed(
            self.other_bidder, "nft_bid", self.seller.address, 5,
            self.nft_id, "7" * 32,
        )
        self.assertTrue(self.chain.add_transaction(bid))
        self._mine()
        buy = self._signed(
            self.bidder, "nft_buy", self.seller.address, 8,
            self.nft_id, "8" * 32,
        )
        self.assertTrue(self.chain.add_transaction(buy))
        self._mine()
        nft = self.chain.get_nft(self.nft_id)
        self.assertEqual(nft["owner"], self.bidder.address)
        self.assertEqual(nft["last_sale_price"], 8)
        self.assertEqual(self.chain.get_balance(self.other_bidder.address), other_start)
        market = self.chain.get_nft_market_history(self.nft_id)
        self.assertEqual(market[0]["price"], 8)
        self.assertEqual(market[0]["tx_type"], "nft_buy")

    def test_non_owner_cannot_list_or_accept_and_forged_signature_fails(self):
        listing = self._signed(
            self.bidder, "nft_list", self.bidder.address, 5,
            self.nft_id, "9" * 32,
        )
        self.assertIn("current NFT owner", self.chain.transaction_rejection_reason(listing))

        forged = self._signed(
            self.creator, "nft_transfer", self.seller.address, 0,
            self.nft_id, "a" * 32,
        )
        forged.sender = self.seller.address
        forged.tx_id = forged.calculate_id()
        self.assertEqual(
            self.chain.transaction_rejection_reason(forged),
            "transaction signature is invalid",
        )

    def test_creator_can_change_royalty_only_before_first_transfer(self):
        update = self._signed(
            self.creator, "nft_set_royalty", self.creator.address, 0,
            self.nft_id, "b" * 32, royalty_bps=2500,
        )
        self.assertTrue(self.chain.add_transaction(update))
        self._mine()
        self.assertEqual(self.chain.get_nft(self.nft_id)["royalty_bps"], 2500)

        move = self._signed(
            self.creator, "nft_transfer", self.seller.address, 0,
            self.nft_id, "c" * 32,
        )
        self.assertTrue(self.chain.add_transaction(move))
        self._mine()
        move_back = self._signed(
            self.seller, "nft_transfer", self.creator.address, 0,
            self.nft_id, "d" * 32,
        )
        self.assertTrue(self.chain.add_transaction(move_back))
        self._mine()

        locked_update = self._signed(
            self.creator, "nft_set_royalty", self.creator.address, 0,
            self.nft_id, "e" * 32, royalty_bps=5000,
        )
        self.assertIn(
            "permanently locked",
            self.chain.transaction_rejection_reason(locked_update),
        )
        self.assertEqual(self.chain.get_nft(self.nft_id)["royalty_bps"], 2500)

    def test_non_creator_cannot_change_royalty(self):
        update = self._signed(
            self.seller, "nft_set_royalty", self.seller.address, 0,
            self.nft_id, "f" * 32, royalty_bps=500,
        )
        self.assertIn(
            "only the NFT creator",
            self.chain.transaction_rejection_reason(update),
        )

    def test_listing_edit_preserves_existing_bids(self):
        self._transfer_to_seller_and_list(price=12)
        self._fund(self.bidder)
        bid = self._signed(
            self.bidder, "nft_bid", self.seller.address, 6,
            self.nft_id, "1a" * 16,
        )
        self.assertTrue(self.chain.add_transaction(bid))
        self._mine()

        edit = self._signed(
            self.seller, "nft_list", self.seller.address, 15,
            self.nft_id, "2b" * 16,
        )
        self.assertTrue(self.chain.add_transaction(edit))
        self._mine()

        nft = self.chain.get_nft(self.nft_id)
        self.assertEqual(nft["listing_price"], 15)
        self.assertEqual(nft["bids"][self.bidder.address]["amount"], 6)


if __name__ == "__main__":
    unittest.main()
