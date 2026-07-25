"""DAD-only token burn reduces supply and the DAD's balance."""
import os
from collections import defaultdict

from node.blockchain import Blockchain
from node.transaction import Transaction

DAD = "a" * 40
OTHER = "b" * 40
MINT = "c" * 40
NONCE = "0" * 32


def _chain(tmp_path):
    return Blockchain({}, database_path=os.path.join(tmp_path, "burn_db.json"))


def _state():
    tokens = {MINT: {"dad_address": DAD, "pool_hlx_reserve": 0, "pool_token_reserve": 0, "decimals": 0}}
    balances = defaultdict(int, {(MINT, DAD): 100})
    supply = defaultdict(int, {MINT: 100})
    return tokens, balances, supply


def test_token_burn_registered():
    assert "token_burn" in Transaction.TOKEN_TYPES
    assert "token_burn" not in Transaction.ZERO_AMOUNT_TYPES


def test_dad_can_burn_reduces_supply(tmp_path):
    chain = _chain(tmp_path)
    tokens, balances, supply = _state()
    tx = Transaction(DAD, DAD, 30, tx_type="token_burn", mint_address=MINT, nonce=NONCE)
    error = chain._apply_token_transaction(tx, tokens, balances, supply, block_index=1, hlx_balances=defaultdict(int))
    assert error is None
    assert supply[MINT] == 70
    assert balances[(MINT, DAD)] == 70


def test_non_dad_cannot_burn(tmp_path):
    chain = _chain(tmp_path)
    tokens, balances, supply = _state()
    balances[(MINT, OTHER)] = 50
    tx = Transaction(OTHER, OTHER, 5, tx_type="token_burn", mint_address=MINT, nonce=NONCE)
    error = chain._apply_token_transaction(tx, tokens, balances, supply, block_index=1, hlx_balances=defaultdict(int))
    assert error == "only the token DAD authority can burn supply"
    assert supply[MINT] == 100


def test_cannot_over_burn(tmp_path):
    chain = _chain(tmp_path)
    tokens, balances, supply = _state()
    tx = Transaction(DAD, DAD, 1000, tx_type="token_burn", mint_address=MINT, nonce=NONCE)
    error = chain._apply_token_transaction(tx, tokens, balances, supply, block_index=1, hlx_balances=defaultdict(int))
    assert "exceeds" in error
    assert supply[MINT] == 100


def test_burn_receiver_must_be_sender(tmp_path):
    chain = _chain(tmp_path)
    tokens, balances, supply = _state()
    tx = Transaction(DAD, OTHER, 5, tx_type="token_burn", mint_address=MINT, nonce=NONCE)
    error = chain._apply_token_transaction(tx, tokens, balances, supply, block_index=1, hlx_balances=defaultdict(int))
    assert "receiver" in error
