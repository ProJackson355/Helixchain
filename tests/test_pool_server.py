"""Mining pool coordinator: share validation and proportional payout split."""
import os

os.environ.pop("HELIX_POOL_SEED", None)

from pool_server import Pool, block_hash, compute_payouts, meets_difficulty

ADDR_A = "a" * 40
ADDR_B = "b" * 40


def _find_nonce(block, difficulty, meets=True):
    nonce = 0
    while meets_difficulty(block_hash(block, nonce), difficulty) is not meets:
        nonce += 1
    return nonce


def _job(block, share_difficulty=1, network_difficulty=64):
    return {
        "job_id": "job1", "block": block,
        "share_difficulty": share_difficulty, "network_difficulty": network_difficulty,
        "reward": 10, "height": block["index"],
    }


def test_compute_payouts_proportional():
    payouts, fee, kept = compute_payouts(100, 1.0, {ADDR_A: 3, ADDR_B: 1})
    assert fee == 1
    # 99 distributable split 3:1 -> 74 and 24 (floored)
    assert payouts[ADDR_A] == 74
    assert payouts[ADDR_B] == 24
    # fee + rounding remainder stays with the pool
    assert kept == 100 - 98


def test_compute_payouts_more_shares_more_pay():
    payouts, _, _ = compute_payouts(1000, 0.0, {ADDR_A: 9, ADDR_B: 1})
    assert payouts[ADDR_A] > payouts[ADDR_B]
    assert payouts[ADDR_A] == 900 and payouts[ADDR_B] == 100


def test_compute_payouts_no_shares():
    payouts, fee, kept = compute_payouts(100, 1.0, {})
    assert payouts == {} and kept == 100


def test_compute_payouts_reserves_each_on_chain_payout_fee():
    payouts, fee, kept = compute_payouts(10, 0.0, {ADDR_A: 1, ADDR_B: 1}, transaction_fee=1)
    assert fee == 0
    assert payouts == {ADDR_A: 4, ADDR_B: 4}
    # Two HLX remain available to pay the two signed payout transactions.
    assert kept == 2


def test_valid_share_is_counted():
    block = {"index": 5, "transactions": [], "previous_hash": "0" * 64, "timestamp": 1, "nonce": 0}
    nonce = _find_nonce(block, 1, meets=True)
    pool = Pool()
    pool.job = _job(block)
    result = pool.submit_share("job1", ADDR_A, nonce)
    assert result["accepted"] is True
    assert pool.round_shares[ADDR_A] == 1


def test_duplicate_and_stale_and_low_shares_rejected():
    block = {"index": 5, "transactions": [], "previous_hash": "0" * 64, "timestamp": 1, "nonce": 0}
    good = _find_nonce(block, 1, meets=True)
    bad = _find_nonce(block, 1, meets=False)
    pool = Pool()
    pool.job = _job(block)
    assert pool.submit_share("job1", ADDR_A, good)["accepted"] is True
    assert pool.submit_share("job1", ADDR_A, good)["reason"] == "duplicate share"
    assert pool.submit_share("wrong-job", ADDR_A, good)["accepted"] is False
    assert pool.submit_share("job1", ADDR_A, bad)["accepted"] is False
    assert pool.submit_share("job1", "not-an-address", good)["accepted"] is False
