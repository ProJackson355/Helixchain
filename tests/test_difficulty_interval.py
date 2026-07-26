"""The fine-difficulty retarget can switch to a longer window at a set height.
Config here: from the change height on, difficulty retargets every N blocks."""
import os
import tempfile

from node.blockchain import Blockchain


def _fresh(**consensus):
    return Blockchain(consensus, database_path=os.path.join(tempfile.mkdtemp(), "db.json"))


def _solve(block, target):
    while int(block.hash, 16) > target:
        block.nonce += 1
        block.hash = block.calculate_hash()
    return block


def test_schedule_disabled_matches_original_cadence():
    bc = _fresh()  # change disabled by default
    assert list(bc._retarget_schedule(1, 45)) == [(b, 10) for b in range(11, 46, 10)]


def test_schedule_switches_interval_at_change_height():
    bc = _fresh(difficulty_interval_change_height=50, difficulty_new_adjustment_interval=100)
    sched = list(bc._retarget_schedule(1, 260))
    assert [b for b, _ in sched] == [11, 21, 31, 41, 50, 150, 250]
    sizes = dict(sched)
    assert sizes[41] == 10 and sizes[50] == 9 and sizes[150] == 100 and sizes[250] == 100
    # Windows are contiguous and non-overlapping back to the activation height.
    prev = 1
    for boundary, size in sched:
        assert boundary - size == prev
        prev = boundary


def test_chain_mined_across_the_change_boundary_validates():
    """Mining and validation both call expected_target, so if a chain that crosses
    the interval-change height stays acceptable, the two agree at every height."""
    bc = _fresh(
        fine_difficulty_activation_height=1,
        fine_initial_difficulty=1.0,          # trivial target: solves instantly
        min_difficulty=1,
        fine_target_block_time_seconds=1,
        difficulty_adjustment_interval=3,
        difficulty_interval_change_height=6,  # small numbers keep the test fast
        difficulty_new_adjustment_interval=4,
    )
    for _ in range(12):                        # crosses 6 (change) and 6+4=10
        block, _diff, target = bc.create_mining_candidate("a" * 40)
        _solve(block, target)
        accepted, reason = bc.receive_block_detailed(block)
        assert accepted, f"height {block.index}: {reason}"
    assert len(bc.chain) - 1 == 12
    # A full independent re-validation of the whole chain must also pass.
    ok, reason = bc.validate_chain(bc.chain)
    assert ok, reason
