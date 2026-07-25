"""Mining-pool directory: normalize, dedupe, gossip-merge."""
import os

os.environ["HELIX_POOLS_FILE"] = "/tmp/test_pool_registry.json"

from node import pool_registry


def setup_function(_):
    pool_registry._write([])


def test_add_and_dedupe():
    pool_registry.add_pool("https://a.example.com")
    pool_registry.add_pool("https://a.example.com/")   # trailing slash normalizes the same
    pool_registry.add_pool("https://b.example.com")
    pools = pool_registry.get_pools()
    assert pools.count("https://a.example.com") == 1
    assert "https://b.example.com" in pools
    assert len(pools) == 2


def test_gossip_merge():
    pool_registry.add_pool("https://a.example.com")
    pool_registry.add_pools(["https://a.example.com", "https://c.example.com", ""])
    pools = pool_registry.get_pools()
    assert "https://c.example.com" in pools
    assert pools.count("https://a.example.com") == 1


def test_empty_is_ignored():
    before = pool_registry.get_pools()
    pool_registry.add_pool("")
    assert pool_registry.get_pools() == before


def test_remove():
    pool_registry.add_pool("https://a.example.com")
    pool_registry.remove_pool("https://a.example.com")
    assert "https://a.example.com" not in pool_registry.get_pools()
