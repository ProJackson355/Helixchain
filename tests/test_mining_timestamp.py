"""Regression tests for the block-timestamp rule that was rejecting valid
proofs from fast / whole-second miners with "another miner won this height"."""
import json
import os
import tempfile
import time

from node.blockchain import Blockchain, TIMESTAMP_BACKWARD_TOLERANCE

MINER = "a" * 40


def _fresh():
    return Blockchain({}, database_path=os.path.join(tempfile.mkdtemp(), "db.json"))


def _solve(block, target):
    while int(block.hash, 16) > target:
        block.nonce += 1
        block.hash = block.calculate_hash()
    return block


def test_block_sharing_parents_clock_tick_is_accepted():
    bc = _fresh()
    block, _diff, target = bc.create_mining_candidate(MINER)
    block.timestamp = bc.chain[-1].timestamp  # same instant as parent (fast block)
    _solve(block, target)
    ok, reason = bc.receive_block_detailed(block)
    assert ok, reason


def test_block_at_edge_of_backward_tolerance_is_accepted():
    bc = _fresh()
    block, _diff, target = bc.create_mining_candidate(MINER)
    block.timestamp = bc.chain[-1].timestamp - TIMESTAMP_BACKWARD_TOLERANCE
    _solve(block, target)
    ok, reason = bc.receive_block_detailed(block)
    assert ok, reason


def test_block_too_far_behind_parent_is_rejected():
    bc = _fresh()
    block, _diff, target = bc.create_mining_candidate(MINER)
    block.timestamp = bc.chain[-1].timestamp - (TIMESTAMP_BACKWARD_TOLERANCE + 5)
    _solve(block, target)
    ok, reason = bc.receive_block_detailed(block)
    assert not ok and "older than its parent" in reason


def test_block_far_in_future_is_still_rejected():
    bc = _fresh()
    block, _diff, target = bc.create_mining_candidate(MINER)
    block.timestamp = time.time() + 600
    _solve(block, target)
    ok, reason = bc.receive_block_detailed(block)
    assert not ok and "future" in reason


def test_whole_second_miner_is_accepted():
    """The exact real-world failure: a miner that stamps integer seconds, so the
    child's timestamp truncates below its parent's fractional timestamp."""
    bc = _fresh()
    b1, _d1, t1 = bc.create_mining_candidate(MINER)
    _solve(b1, t1)
    assert bc.receive_block(b1)
    b2, _d2, t2 = bc.create_mining_candidate(MINER)
    b2.timestamp = int(b2.timestamp)  # whole-second stamp < parent's fractional stamp
    _solve(b2, t2)
    ok, reason = bc.receive_block_detailed(b2)
    assert ok, reason


def test_external_mining_json_round_trip_is_accepted():
    """work -> JSON -> solve -> JSON -> submit, exactly as an external miner does."""
    from node.node import block_to_dict, dict_to_block
    bc = _fresh()
    block, _diff, target = bc.create_mining_candidate(MINER)
    template = dict_to_block(json.loads(json.dumps(block_to_dict(block))))
    _solve(template, target)
    submitted = dict_to_block(json.loads(json.dumps(block_to_dict(template))))
    ok, reason = bc.receive_block_detailed(submitted)
    assert ok, reason
