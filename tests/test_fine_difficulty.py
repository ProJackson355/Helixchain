"""Fine-grained (Bitcoin-style) numeric-target difficulty.

Verifies the new target rule is exactly the old leading-zero rule below the
activation height (so the existing chain stays valid) and that above it the
target retargets smoothly *between* whole hex levels instead of only in 16x
jumps.
"""
import os
from types import SimpleNamespace

from node.blockchain import Blockchain, Block, MAX_HASH


def _chain(tmp_path, **overrides):
    bc = Blockchain({}, database_path=os.path.join(tmp_path, "db.json"))
    for key, value in overrides.items():
        setattr(bc, key, value)
    return bc


def test_difficulty_to_target_matches_leading_zeros(tmp_path):
    bc = _chain(tmp_path)
    for difficulty, sample, expected in [
        (3, "000f" + "0" * 60, True),
        (3, "00f0" + "0" * 60, False),
        (1, "0" + "a" * 63, True),
        (1, "a" + "0" * 63, False),
        (4, "0000" + "f" * 60, True),
    ]:
        target = bc.difficulty_to_target(difficulty)
        result = bc.hash_meets_target(sample, target)
        assert result == sample.startswith("0" * difficulty)
        assert result == expected


def test_target_equals_legacy_below_activation(tmp_path):
    # Default activation is effectively off, so every height uses the legacy rule.
    bc = _chain(tmp_path)
    for index in (5, 50, 161, 500):
        assert bc.expected_target(index, bc.chain) == bc.difficulty_to_target(
            bc.expected_difficulty(index, bc.chain)
        )


def test_mine_to_target_produces_valid_proof(tmp_path):
    bc = _chain(tmp_path)
    block = Block(1, [], "0" * 64, timestamp=1, nonce=0)
    target = bc.difficulty_to_target(1)
    block.mine_to_target(target)
    assert int(block.hash, 16) <= target
    assert block.hash.startswith("0")


def test_retarget_is_fine_grained_between_levels(tmp_path):
    # Activation at 0, 4-block windows, seed difficulty 4, 60s expected per block.
    bc = _chain(
        tmp_path,
        fine_difficulty_activation_height=0,
        difficulty_adjustment_interval=4,
        difficulty=4,
        min_difficulty=1,
        difficulty_activation_height=10,      # so expected_difficulty(0) == self.difficulty
        fine_target_block_time_seconds=60,
    )
    # Four blocks 45s apart -> window elapsed 135s vs expected 60*3=180s (fast).
    chain = [SimpleNamespace(index=i, timestamp=i * 45.0, hash="0" * 64) for i in range(5)]
    seed = bc.difficulty_to_target(4)
    result = bc.expected_target(4, chain)

    # Fast blocks -> harder -> smaller target, adjusted by the 135/180 ratio.
    assert result == seed * 135 // 180
    # Crucially, it lands strictly BETWEEN whole difficulty levels 4 and 5,
    # which the old 16x-per-level scheme could never express.
    assert bc.difficulty_to_target(5) < result < bc.difficulty_to_target(4)


def test_retarget_direction_two_minute_target(tmp_path):
    # Interval 10, 2-minute (120s) target: avg block time < 2min raises difficulty.
    bc = _chain(
        tmp_path,
        fine_difficulty_activation_height=0,
        difficulty_adjustment_interval=10,
        difficulty=4,
        min_difficulty=1,
        difficulty_activation_height=100,     # expected_difficulty(0) == self.difficulty
        fine_target_block_time_seconds=120,
    )
    seed = bc.difficulty_to_target(4)
    # 10 blocks averaging 60s apart (< 2 min) -> harder -> smaller target.
    fast = [SimpleNamespace(index=i, timestamp=i * 60.0, hash="0" * 64) for i in range(11)]
    assert bc.expected_target(10, fast) < seed
    # 10 blocks averaging 300s apart (> 2 min) -> easier -> larger target.
    slow = [SimpleNamespace(index=i, timestamp=i * 300.0, hash="0" * 64) for i in range(11)]
    assert bc.expected_target(10, slow) > seed


def test_difficulty_rises_without_upper_cap(tmp_path):
    # Sustained fast blocks push difficulty past the old max_difficulty ceiling.
    bc = _chain(
        tmp_path,
        fine_difficulty_activation_height=0,
        difficulty_adjustment_interval=4,
        difficulty=4,
        min_difficulty=1,
        max_difficulty=5,                     # old cap; must be exceeded now
        difficulty_activation_height=100,
        fine_target_block_time_seconds=120,
    )
    # Many windows of 1s-apart blocks -> keeps hardening 4x per window.
    fast = [SimpleNamespace(index=i, timestamp=float(i), hash="0" * 64) for i in range(41)]
    hardest_old_cap = bc.difficulty_to_target(bc.max_difficulty)
    result = bc.expected_target(40, fast)
    assert result < hardest_old_cap  # smaller target than the old ceiling = harder than it


def test_difficulty_floor_at_min(tmp_path):
    bc = _chain(
        tmp_path,
        fine_difficulty_activation_height=0,
        difficulty_adjustment_interval=4,
        difficulty=4,
        min_difficulty=3,
        difficulty_activation_height=100,
        fine_target_block_time_seconds=120,
    )
    # Sustained very slow blocks -> eases but never past the min_difficulty floor.
    slow = [SimpleNamespace(index=i, timestamp=i * 1_000_000.0, hash="0" * 64) for i in range(41)]
    assert bc.expected_target(40, slow) <= bc.difficulty_to_target(bc.min_difficulty)
