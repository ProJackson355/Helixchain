import hashlib
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from node.blockchain import Block, Blockchain
from node.transaction import Transaction


def address_for(public_key) -> str:
    compressed = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint,
    )
    return hashlib.sha256(compressed).hexdigest()[:40]


class BlockchainTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.database = Path(self.temporary.name) / "chain.json"
        self.consensus = {
            "difficulty": 1,
            "min_difficulty": 1,
            "max_difficulty": 2,
            "difficulty_adjustment_interval": 10,
            "target_block_time_seconds": 60,
            "difficulty_activation_height": 10,
            "reward": 7,
            "max_supply": 1_000,
            "checkpoints": {},
        }

    def tearDown(self):
        self.temporary.cleanup()

    def test_consensus_config_is_applied_before_database_load(self):
        miner = ec.generate_private_key(ec.SECP256K1())
        chain = Blockchain(self.consensus, self.database)
        block = chain.mine_pending_transactions(address_for(miner.public_key()))

        self.assertEqual(block.transactions[-1].amount, 7)
        self.assertTrue(block.hash.startswith("0"))

        reloaded = Blockchain(self.consensus, self.database)
        self.assertEqual(len(reloaded.chain), 2)
        self.assertEqual(reloaded.block_reward, 7)
        self.assertEqual(reloaded.max_supply, 1_000)
        self.assertEqual(reloaded.validate_chain(reloaded.chain), (True, None))

    def test_difficulty_retargets_toward_ten_minute_blocks(self):
        consensus = {
            **self.consensus,
            "difficulty": 4,
            "min_difficulty": 2,
            "max_difficulty": 6,
            "difficulty_adjustment_interval": 3,
            "difficulty_activation_height": 3,
            "adaptive_target_block_time_seconds": 600,
            "adaptive_difficulty_activation_height": 3,
        }
        chain = Blockchain(consensus, self.database)
        genesis = chain.chain[0]

        fast_one = Block(1, [], genesis.hash, timestamp=10)
        fast_two = Block(2, [], fast_one.hash, timestamp=20)
        self.assertEqual(chain.expected_difficulty(3, [genesis, fast_one, fast_two]), 5)

        slow_one = Block(1, [], genesis.hash, timestamp=700)
        slow_two = Block(2, [], slow_one.hash, timestamp=1400)
        self.assertEqual(chain.expected_difficulty(3, [genesis, slow_one, slow_two]), 3)

    def test_target_block_time_changes_to_200_seconds_at_height_300(self):
        consensus = {
            **self.consensus,
            "adaptive_target_block_time_seconds": 600,
            "adaptive_difficulty_activation_height": 60,
            "new_target_block_time_seconds": 200,
            "new_target_block_time_activation_height": 300,
        }
        chain = Blockchain(consensus, self.database)
        self.assertEqual(chain.target_block_time_for_height(59), 60)
        self.assertEqual(chain.target_block_time_for_height(60), 600)
        self.assertEqual(chain.target_block_time_for_height(299), 600)
        self.assertEqual(chain.target_block_time_for_height(300), 200)

    def test_one_time_difficulty_reset_then_retargeting_resumes(self):
        consensus = {
            **self.consensus,
            "difficulty": 3,
            "min_difficulty": 1,
            "max_difficulty": 8,
            "difficulty_adjustment_interval": 2,
            "difficulty_activation_height": 2,
            "adaptive_difficulty_activation_height": 2,
            "difficulty_reset_value": 3,
            "difficulty_reset_height": 3,
            "new_target_block_time_seconds": 160,
            "new_target_block_time_activation_height": 3,
        }
        chain = Blockchain(consensus, self.database)
        genesis = chain.chain[0]
        fast_block = Block(1, [], genesis.hash, timestamp=1)
        block_two = Block(2, [], fast_block.hash, timestamp=2)
        reset_block = Block(3, [], block_two.hash, timestamp=3)
        next_block = Block(4, [], reset_block.hash, timestamp=4)

        self.assertEqual(chain.expected_difficulty(2, [genesis, fast_block]), 4)
        self.assertEqual(chain.expected_difficulty(3, [genesis, fast_block, block_two]), 3)
        self.assertEqual(chain.expected_difficulty(4, [genesis, fast_block, block_two, reset_block]), 3)
        self.assertEqual(chain.expected_difficulty(5, [genesis, fast_block, block_two, reset_block, next_block]), 4)
        self.assertEqual(chain.target_block_time_for_height(3), 160)

    def test_two_hlx_reward_activation_and_supply_cap(self):
        consensus = {
            **self.consensus,
            "reward": 10,
            "mining_reward": 2,
            "mining_reward_activation_height": 2,
            "max_supply": 13,
        }
        chain = Blockchain(consensus, self.database)
        miner = address_for(ec.generate_private_key(ec.SECP256K1()).public_key())
        first = chain.mine_pending_transactions(miner)
        second = chain.mine_pending_transactions(miner)
        third = chain.mine_pending_transactions(miner)
        fourth = chain.mine_pending_transactions(miner)

        self.assertEqual(first.transactions[-1].amount, 10)
        self.assertEqual(second.transactions[-1].amount, 2)
        self.assertEqual(third.transactions[-1].amount, 1)
        self.assertEqual(fourth.transactions[-1].amount, 0)
        self.assertEqual(chain.get_total_supply(), 13)
        self.assertEqual(chain.validate_chain(chain.chain), (True, None))

    def test_fractional_reward_is_exact_and_survives_reload(self):
        consensus = {
            **self.consensus,
            "reward": 10,
            "mining_reward": 2,
            "mining_reward_activation_height": 1,
            "fractional_mining_reward": "3.125",
            "fractional_reward_activation_height": 2,
            "native_dad_address": "9" * 40,
            "native_dad_activation_height": 2,
            "max_supply": 100,
        }
        chain = Blockchain(consensus, self.database)
        miner = address_for(ec.generate_private_key(ec.SECP256K1()).public_key())
        first = chain.mine_pending_transactions(miner)
        second = chain.mine_pending_transactions(miner)

        self.assertEqual(first.transactions[-1].amount, 2)
        self.assertIsNone(chain.native_dad_for_height(1))
        self.assertEqual(chain.native_dad_for_height(2), "9" * 40)
        self.assertEqual(second.transactions[-1].amount, Decimal("3.125"))
        self.assertEqual(second.transactions[-1].to_dict()["amount"], "3.125")
        self.assertEqual(chain.get_balance(miner), Decimal("5.125"))
        self.assertEqual(chain.validate_chain(chain.chain), (True, None))

        reloaded = Blockchain(consensus, self.database)
        self.assertEqual(reloaded.get_balance(miner), Decimal("5.125"))
        self.assertEqual(reloaded.validate_chain(reloaded.chain), (True, None))

    def test_ten_hlx_reward_is_restored_at_height_300(self):
        consensus = {
            **self.consensus,
            "reward": 10,
            "mining_reward": 2,
            "mining_reward_activation_height": 90,
            "fractional_mining_reward": "10",
            "fractional_reward_activation_height": 300,
        }
        chain = Blockchain(consensus, self.database)
        self.assertEqual(chain.reward_for_height(89), 10)
        self.assertEqual(chain.reward_for_height(90), 2)
        self.assertEqual(chain.reward_for_height(299), 2)
        self.assertEqual(chain.reward_for_height(300), Decimal("10"))

    def test_invalid_database_fails_closed_without_replacing_chain_file(self):
        original = b'{"chain": [not valid json]}'
        self.database.write_bytes(original)

        with self.assertRaisesRegex(RuntimeError, "left untouched"):
            Blockchain(self.consensus, self.database)

        self.assertEqual(self.database.read_bytes(), original)
        self.assertEqual(
            {path.name for path in Path(self.temporary.name).iterdir()},
            {self.database.name},
        )

    def test_signed_transfer_survives_mining_and_reload(self):
        sender_key = ec.generate_private_key(ec.SECP256K1())
        receiver_key = ec.generate_private_key(ec.SECP256K1())
        sender = address_for(sender_key.public_key())
        receiver = address_for(receiver_key.public_key())
        chain = Blockchain(self.consensus, self.database)
        chain.mine_pending_transactions(sender)

        transaction = Transaction(sender, receiver, 3, sender_key.public_key())
        transaction.sign(sender_key)
        self.assertTrue(chain.add_transaction(transaction))
        chain.mine_pending_transactions(receiver)

        reloaded = Blockchain(self.consensus, self.database)
        self.assertEqual(reloaded.get_balance(sender), 4)
        self.assertEqual(reloaded.get_balance(receiver), 10)
        self.assertIsNotNone(reloaded.find_transaction(transaction.tx_id)[1])

    def test_attacker_cannot_spend_another_wallets_balance(self):
        owner_key = ec.generate_private_key(ec.SECP256K1())
        attacker_key = ec.generate_private_key(ec.SECP256K1())
        owner = address_for(owner_key.public_key())
        attacker = address_for(attacker_key.public_key())
        chain = Blockchain(self.consensus, self.database)
        chain.mine_pending_transactions(owner)

        forged = Transaction(owner, attacker, 3, attacker_key.public_key())
        forged.sign(attacker_key)

        self.assertFalse(chain.add_transaction(forged))
        self.assertEqual(chain.get_balance(owner), 7)
        self.assertEqual(chain.get_balance(attacker), 0)

    def test_sender_can_cancel_pending_transaction_and_tombstone_survives_reload(self):
        owner_key = ec.generate_private_key(ec.SECP256K1())
        receiver_key = ec.generate_private_key(ec.SECP256K1())
        owner = address_for(owner_key.public_key())
        receiver = address_for(receiver_key.public_key())
        chain = Blockchain(self.consensus, self.database)
        chain.mine_pending_transactions(owner)

        transaction = Transaction(owner, receiver, 3, owner_key.public_key())
        transaction.sign(owner_key)
        self.assertTrue(chain.add_transaction(transaction))
        self.assertFalse(chain.cancel_pending_transaction(transaction.tx_id, receiver))
        self.assertTrue(chain.cancel_pending_transaction(transaction.tx_id, owner, now=1000))
        self.assertEqual(chain.pending_ids(), set())
        self.assertEqual(chain.get_available_balance(owner), 7)
        self.assertFalse(chain.add_transaction(transaction))

        reloaded = Blockchain(self.consensus, self.database)
        self.assertTrue(reloaded.is_transaction_cancelled(transaction.tx_id, owner))
        self.assertFalse(reloaded.add_transaction(transaction))
        reloaded.prune_cancelled_transactions(60, now=1061)
        self.assertFalse(reloaded.is_transaction_cancelled(transaction.tx_id, owner))
        self.assertTrue(reloaded.add_transaction(transaction))

    def test_custom_token_state_is_confirmed_by_chain_and_survives_reload(self):
        creator_key = ec.generate_private_key(ec.SECP256K1())
        authority_key = ec.generate_private_key(ec.SECP256K1())
        new_authority_key = ec.generate_private_key(ec.SECP256K1())
        holder_key = ec.generate_private_key(ec.SECP256K1())
        creator = address_for(creator_key.public_key())
        authority = address_for(authority_key.public_key())
        new_authority = address_for(new_authority_key.public_key())
        holder = address_for(holder_key.public_key())
        chain = Blockchain(self.consensus, self.database)

        nonce = "ab" * 16
        mint_address = Transaction.mint_address(creator, nonce)
        description = "A test token stored in Helix metadata"
        image = "https://example.test/token.png"
        metadata_hash = Transaction.token_metadata_hash(
            "Example Token", "EXT", description, image
        )
        create = Transaction(
            creator,
            creator,
            0,
            creator_key.public_key(),
            tx_type="token_create",
            mint_address=mint_address,
            dad_address=authority,
            nonce=nonce,
            name="Example Token",
            symbol="EXT",
            description=description,
            image=image,
            metadata_hash=metadata_hash,
            decimals=2,
            uri="https://example.test/token.json",
        )
        create.sign(creator_key)
        self.assertTrue(chain.add_transaction(create))
        self.assertIsNone(chain.get_token(mint_address))

        chain.mine_pending_transactions(creator)
        token = chain.get_token(mint_address)
        self.assertIsNotNone(token)
        self.assertEqual(token["dad_address"], authority)
        self.assertEqual(token["creator_address"], creator)
        self.assertEqual(token["description"], description)
        self.assertEqual(token["image"], image)
        self.assertEqual(token["metadata_hash"], metadata_hash)
        self.assertEqual(token["supply"], 0)
        self.assertEqual(chain.get_token_balance(mint_address, creator), 0)
        self.assertFalse(chain.token_account_exists(mint_address, creator))

        unauthorized_mint = Transaction(
            creator,
            creator,
            1,
            creator_key.public_key(),
            tx_type="token_mint",
            mint_address=mint_address,
            nonce="bc" * 16,
        )
        unauthorized_mint.sign(creator_key)
        self.assertFalse(chain.add_transaction(unauthorized_mint))

        mint = Transaction(
            authority,
            creator,
            500,
            authority_key.public_key(),
            tx_type="token_mint",
            mint_address=mint_address,
            nonce="cd" * 16,
        )
        mint.sign(authority_key)
        self.assertTrue(chain.add_transaction(mint))

        transfer = Transaction(
            creator,
            holder,
            250,
            creator_key.public_key(),
            tx_type="token_transfer",
            mint_address=mint_address,
            nonce="ef" * 16,
        )
        transfer.sign(creator_key)
        self.assertTrue(chain.add_transaction(transfer))

        repeated_transfer = Transaction(
            creator,
            holder,
            250,
            creator_key.public_key(),
            tx_type="token_transfer",
            mint_address=mint_address,
            nonce="12" * 16,
        )
        repeated_transfer.sign(creator_key)
        self.assertNotEqual(repeated_transfer.tx_id, transfer.tx_id)
        self.assertTrue(chain.add_transaction(repeated_transfer))
        chain.mine_pending_transactions(creator)

        set_authority = Transaction(
            authority,
            new_authority,
            0,
            authority_key.public_key(),
            tx_type="token_set_authority",
            mint_address=mint_address,
            nonce="34" * 16,
        )
        set_authority.sign(authority_key)
        self.assertTrue(chain.add_transaction(set_authority))

        mint_as_new_authority = Transaction(
            new_authority,
            new_authority,
            100,
            new_authority_key.public_key(),
            tx_type="token_mint",
            mint_address=mint_address,
            nonce="56" * 16,
        )
        mint_as_new_authority.sign(new_authority_key)
        self.assertTrue(chain.add_transaction(mint_as_new_authority))

        revoke_authority = Transaction(
            new_authority,
            "0" * 40,
            0,
            new_authority_key.public_key(),
            tx_type="token_set_authority",
            mint_address=mint_address,
            nonce="78" * 16,
        )
        revoke_authority.sign(new_authority_key)
        self.assertTrue(chain.add_transaction(revoke_authority))
        chain.mine_pending_transactions(creator)

        reloaded = Blockchain(self.consensus, self.database)
        self.assertEqual(reloaded.validate_chain(reloaded.chain), (True, None))
        self.assertEqual(reloaded.get_token(mint_address)["supply"], 600)
        self.assertIsNone(reloaded.get_token(mint_address)["dad_address"])
        self.assertEqual(reloaded.get_token_balance(mint_address, creator), 0)
        self.assertEqual(reloaded.get_token_balance(mint_address, holder), 500)
        self.assertEqual(reloaded.get_token_balance(mint_address, new_authority), 100)
        self.assertTrue(reloaded.token_account_exists(mint_address, creator))
        self.assertTrue(reloaded.token_account_exists(mint_address, holder))
        self.assertTrue(reloaded.token_account_exists(mint_address, new_authority))

        after_revoke = Transaction(
            new_authority,
            new_authority,
            1,
            new_authority_key.public_key(),
            tx_type="token_mint",
            mint_address=mint_address,
            nonce="9a" * 16,
        )
        after_revoke.sign(new_authority_key)
        self.assertFalse(reloaded.add_transaction(after_revoke))

    def test_legacy_transaction_serialization_is_unchanged(self):
        key = ec.generate_private_key(ec.SECP256K1())
        sender = address_for(key.public_key())
        receiver = "1" * 40
        transaction = Transaction(sender, receiver, 3, key.public_key())
        transaction.sign(key)

        self.assertEqual(
            set(transaction.to_dict()),
            {"sender", "receiver", "amount", "signature", "tx_id", "public_key"},
        )
        self.assertEqual(
            transaction.data(),
            f'{{"amount":3,"receiver":"{receiver}","sender":"{sender}"}}',
        )

    def test_pre_metadata_token_block_keeps_its_original_hash_and_activation_boundary(self):
        creator_key = ec.generate_private_key(ec.SECP256K1())
        creator = address_for(creator_key.public_key())
        consensus = {**self.consensus, "token_metadata_activation_height": 2}
        chain = Blockchain(consensus, self.database)
        nonce = "ab" * 16
        legacy = Transaction(
            creator,
            creator,
            0,
            creator_key.public_key(),
            tx_type="token_create",
            mint_address=Transaction.mint_address(creator, nonce),
            dad_address=creator,
            nonce=nonce,
            name="Legacy Token",
            symbol="OLD",
            decimals=2,
            uri="https://example.test/legacy.json",
        )
        legacy.sign(creator_key)
        self.assertNotIn("description", legacy.to_dict())
        self.assertNotIn("image", legacy.to_dict())
        self.assertNotIn("metadata_hash", legacy.to_dict())

        genesis = chain.chain[0]
        reward = chain._make_reward(1, creator, genesis.hash)
        block = Block(1, [legacy, reward], genesis.hash)
        block.mine(chain.expected_difficulty(1, [genesis]))
        self.assertEqual(chain.validate_chain([genesis, block]), (True, None))

        # The same legacy schema cannot be introduced once protocol-4
        # metadata enforcement has activated.
        tokens = {}
        token_balances = {}
        token_supply = {}
        self.assertEqual(
            chain._apply_token_transaction(
                legacy, tokens, token_balances, token_supply, block_index=2
            ),
            "token description must contain 1 to 1000 characters",
        )

    def test_constant_product_token_pool_buy_and_sell_change_price(self):
        creator_key = ec.generate_private_key(ec.SECP256K1())
        trader_key = ec.generate_private_key(ec.SECP256K1())
        creator = address_for(creator_key.public_key())
        trader = address_for(trader_key.public_key())
        consensus = {**self.consensus, "token_exchange_activation_height": 0}
        chain = Blockchain(consensus, self.database)
        chain.mine_pending_transactions(creator)
        chain.mine_pending_transactions(creator)

        nonce = "01" * 16
        mint_address = Transaction.mint_address(creator, nonce)
        description = "A token with an on-chain HLX market"
        image = "https://example.test/market.png"
        create = Transaction(
            creator, creator, 0, creator_key.public_key(),
            tx_type="token_create", mint_address=mint_address,
            dad_address=creator, nonce=nonce, name="Market Token", symbol="MKT",
            description=description, image=image,
            metadata_hash=Transaction.token_metadata_hash(
                "Market Token", "MKT", description, image
            ),
            decimals=0, uri="https://example.test/market.json",
        )
        create.sign(creator_key)
        self.assertTrue(chain.add_transaction(create))
        chain.mine_pending_transactions(creator)

        mint = Transaction(
            creator, creator, 1_000, creator_key.public_key(),
            tx_type="token_mint", mint_address=mint_address, nonce="02" * 16,
        )
        mint.sign(creator_key)
        self.assertTrue(chain.add_transaction(mint))
        chain.mine_pending_transactions(creator)

        partial_pool = Transaction(
            creator, creator, 500, creator_key.public_key(),
            tx_type="token_pool_create", mint_address=mint_address,
            nonce="07" * 16, hlx_amount=7,
        )
        partial_pool.sign(creator_key)
        self.assertFalse(chain.add_transaction(partial_pool))

        pool = Transaction(
            creator, creator, 1_000, creator_key.public_key(),
            tx_type="token_pool_create", mint_address=mint_address,
            nonce="03" * 16, hlx_amount=7,
        )
        pool.sign(creator_key)
        self.assertTrue(chain.add_transaction(pool))
        chain.mine_pending_transactions(creator)
        initial = chain.get_token(mint_address)
        self.assertEqual(initial["pool_hlx_reserve"], 7)
        self.assertEqual(initial["pool_token_reserve"], 1_000)

        add_liquidity = Transaction(
            creator, creator, 3, creator_key.public_key(),
            tx_type="token_pool_add_hlx", mint_address=mint_address,
            nonce="06" * 16,
        )
        add_liquidity.sign(creator_key)
        self.assertTrue(chain.add_transaction(add_liquidity))
        chain.mine_pending_transactions(creator)
        funded = chain.get_token(mint_address)
        self.assertEqual(funded["pool_hlx_reserve"], 10)
        self.assertEqual(funded["pool_token_reserve"], 1_000)

        chain.mine_pending_transactions(trader)
        expected_buy = Blockchain._swap_output(2, 10, 1_000)
        buy = Transaction(
            trader, trader, 2, trader_key.public_key(),
            tx_type="token_buy", mint_address=mint_address,
            nonce="04" * 16, min_receive=expected_buy,
        )
        buy.sign(trader_key)
        self.assertTrue(chain.add_transaction(buy))
        chain.mine_pending_transactions(creator)
        after_buy = chain.get_token(mint_address)
        self.assertEqual(chain.get_token_balance(mint_address, trader), expected_buy)
        self.assertGreater(
            after_buy["pool_hlx_reserve"] * funded["pool_token_reserve"],
            funded["pool_hlx_reserve"] * after_buy["pool_token_reserve"],
        )

        expected_sell = Blockchain._swap_output(
            100, after_buy["pool_token_reserve"], after_buy["pool_hlx_reserve"]
        )
        sell = Transaction(
            trader, trader, 100, trader_key.public_key(),
            tx_type="token_sell", mint_address=mint_address,
            nonce="05" * 16, min_receive=expected_sell,
        )
        sell.sign(trader_key)
        self.assertTrue(chain.add_transaction(sell))
        chain.mine_pending_transactions(creator)
        after_sell = chain.get_token(mint_address)
        self.assertEqual(chain.get_balance(trader), 7 - 2 + expected_sell)
        self.assertLess(
            after_sell["pool_hlx_reserve"] * after_buy["pool_token_reserve"],
            after_buy["pool_hlx_reserve"] * after_sell["pool_token_reserve"],
        )
        market_history = chain.get_token_market_history(mint_address)
        self.assertEqual(
            [point["tx_type"] for point in market_history],
            ["token_pool_create", "token_pool_add_hlx", "token_buy", "token_sell"],
        )
        self.assertEqual(market_history[-1]["pool_hlx_reserve"], after_sell["pool_hlx_reserve"])
        self.assertEqual(market_history[-1]["pool_token_reserve"], after_sell["pool_token_reserve"])
        self.assertEqual(market_history[-1]["tx_id"], sell.tx_id)
        self.assertEqual(chain.validate_chain(chain.chain), (True, None))
        self.assertEqual(chain.get_recent_transactions(1)[0][1].sender, "SYSTEM")
        self.assertEqual(chain.get_recent_transactions(1, 1)[0][1].tx_id, sell.tx_id)
        self.assertEqual(
            chain.confirmed_transaction_count(),
            sum(len(block.transactions) for block in chain.chain),
        )
        reloaded = Blockchain(consensus, self.database)
        self.assertEqual(reloaded.get_token(mint_address)["pool_hlx_reserve"], after_sell["pool_hlx_reserve"])
        self.assertEqual(reloaded.get_token_balance(mint_address, trader), expected_buy - 100)
        self.assertEqual(reloaded.get_token_market_history(mint_address), market_history)
        self.assertEqual(reloaded.get_balance(trader), 7 - 2 + expected_sell)

    def test_atomic_token_swap_routes_value_through_hlx_pools(self):
        trader_key = ec.generate_private_key(ec.SECP256K1())
        trader = address_for(trader_key.public_key())
        source_mint = "a1" * 20
        target_mint = "b2" * 20
        tokens = {
            source_mint: {"pool_hlx_reserve": 100, "pool_token_reserve": 1_000},
            target_mint: {"pool_hlx_reserve": 200, "pool_token_reserve": 4_000},
        }
        balances = {(source_mint, trader): 500, (target_mint, trader): 0}
        swap = Transaction(
            trader, trader, 100, trader_key.public_key(),
            tx_type="token_swap", mint_address=source_mint,
            target_mint_address=target_mint, nonce="cd" * 16,
            min_receive=1,
        )
        swap.sign(trader_key)
        self.assertTrue(swap.verify_signature())
        self.assertEqual(swap.to_dict()["target_mint_address"], target_mint)

        chain = Blockchain({
            **self.consensus,
            "token_exchange_activation_height": 0,
            "token_swap_activation_height": 200,
        }, self.database)
        self.assertEqual(
            chain._apply_token_transaction(
                swap, {mint: dict(value) for mint, value in tokens.items()},
                dict(balances), {source_mint: 1_000, target_mint: 4_000},
                block_index=199, hlx_balances={trader: 0},
            ),
            "token-to-token swaps are not active at this block height",
        )

        routed_hlx = Blockchain._swap_output(100, 1_000, 100)
        received = Blockchain._swap_output(routed_hlx, 200, 4_000)
        reason = chain._apply_token_transaction(
            swap, tokens, balances, {source_mint: 1_000, target_mint: 4_000},
            block_index=200, hlx_balances={trader: 0},
        )
        self.assertIsNone(reason)
        self.assertEqual(balances[(source_mint, trader)], 400)
        self.assertEqual(balances[(target_mint, trader)], received)
        self.assertEqual(tokens[source_mint]["pool_hlx_reserve"], 100 - routed_hlx)
        self.assertEqual(tokens[target_mint]["pool_hlx_reserve"], 200 + routed_hlx)


if __name__ == "__main__":
    unittest.main()
