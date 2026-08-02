import unittest

import node.node as node_api
from node.transaction import Transaction
from wallet.wallet import Wallet


class TransactionPayloadContractTests(unittest.TestCase):
    def setUp(self):
        self.wallet = Wallet()
        self.receiver = Wallet().address
        self.nonce = "ab" * 16
        self.mint = "c" * 40
        self.target_mint = "d" * 40
        self.nft_id = "e" * 40

    def transaction_for(self, tx_type):
        options = {"tx_type": tx_type, "fee": 1}
        amount = 1
        receiver = self.receiver
        if tx_type in Transaction.TOKEN_TYPES:
            options.update(mint_address=self.mint, nonce=self.nonce)
        if tx_type == "token_create":
            amount = 0
            receiver = self.wallet.address
            options.update(
                dad_address=self.wallet.address,
                name="Contract Token", symbol="CT", decimals=0,
                description="Parser contract test",
                image="https://example.com/token.png",
                metadata_hash="f" * 64,
                uri="https://example.com/token.json",
            )
        if tx_type == "token_set_authority":
            amount = 0
        if tx_type == "cancel":
            amount = 0
            receiver = self.wallet.address
        if tx_type == "token_pool_create":
            options["hlx_amount"] = 1
        if tx_type in {"token_buy", "token_sell", "token_swap"}:
            options["min_receive"] = 1
        if tx_type == "token_swap":
            options["target_mint_address"] = self.target_mint
        if tx_type in Transaction.NFT_TYPES:
            options.update(nft_id=self.nft_id, nonce=self.nonce)
        if tx_type in {
            "nft_mint", "nft_transfer", "nft_cancel_listing",
            "nft_cancel_bid", "nft_accept_bid", "nft_set_royalty",
        }:
            amount = 0
        if tx_type == "nft_mint":
            receiver = self.wallet.address
            options.update(
                name="Contract NFT", description="Parser contract test",
                image="https://example.com/nft.png",
                uri="https://example.com/nft.json",
                metadata_hash="a" * 64, attributes=[], royalty_bps=0,
            )
        if tx_type == "nft_set_royalty":
            receiver = self.wallet.address
            options["royalty_bps"] = 250
        tx = Transaction(
            self.wallet.address, receiver, amount,
            public_key=self.wallet.public_key, **options,
        )
        tx.sign(self.wallet.private_key)
        return tx

    def test_every_wallet_transaction_type_round_trips_through_api_parser(self):
        transaction_types = [
            "transfer", "cancel", *sorted(Transaction.TOKEN_TYPES), *sorted(Transaction.NFT_TYPES),
        ]
        for tx_type in transaction_types:
            with self.subTest(tx_type=tx_type):
                original = self.transaction_for(tx_type)
                parsed = node_api._transaction_from_payload(original.to_dict())
                self.assertEqual(parsed.tx_type, tx_type)
                self.assertEqual(parsed.fee, 1)
                self.assertEqual(parsed.tx_id, original.tx_id)
                self.assertTrue(parsed.verify_signature())

    def test_legacy_fee_less_payload_is_parsed_then_handled_by_consensus(self):
        tx = Transaction(
            self.wallet.address, self.receiver, 1,
            public_key=self.wallet.public_key,
        )
        tx.sign(self.wallet.private_key)
        parsed = node_api._transaction_from_payload(tx.to_dict())
        self.assertIsNone(parsed.fee)
        self.assertTrue(parsed.verify_signature())


if __name__ == "__main__":
    unittest.main()
