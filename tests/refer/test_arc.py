"""ARC — scan resistance, byte bounds, and the property that it cannot lie."""

from __future__ import annotations

import ast
import inspect

import pytest

from fux.refer import arc as arc_mod
from fux.refer.arc import ARC


def test_a_hit_returns_exactly_what_was_put():
    cache = ARC(1000)
    cache.put(("a.md", "sha1"), b"hello")
    assert cache.get(("a.md", "sha1")) == b"hello"


def test_the_sha_is_part_of_the_key_so_a_hit_cannot_be_wrong_bytes():
    """The load-bearing property: a hit is content-addressed, so it IS what a
    fetch would have returned. This is what makes the cache safe to be
    aggressive — and what makes the differential test below true."""
    cache = ARC(1000)
    cache.put(("a.md", "sha1"), b"old")
    assert cache.get(("a.md", "sha2")) is None  # same loc, changed content
    cache.put(("a.md", "sha2"), b"new")
    assert cache.get(("a.md", "sha1")) == b"old"
    assert cache.get(("a.md", "sha2")) == b"new"


def test_the_budget_is_in_bytes_and_is_respected():
    cache = ARC(300)
    for i in range(20):
        cache.put((f"{i}.md", "s"), b"x" * 100)
    assert cache.live_bytes <= 300


def test_an_object_larger_than_the_budget_is_never_cached():
    cache = ARC(100)
    cache.put(("big.md", "s"), b"x" * 500)
    assert ("big.md", "s") not in cache
    assert cache.live_bytes == 0


def test_a_second_read_promotes_into_the_frequency_list():
    cache = ARC(1000)
    cache.put(("a.md", "s"), b"x")
    assert ("a.md", "s") in cache.t1
    cache.get(("a.md", "s"))
    assert ("a.md", "s") in cache.t2 and ("a.md", "s") not in cache.t1


def test_a_scan_does_not_evict_the_twice_read_entry():
    """Scan resistance, which is the whole reason this is not an LRU.

    A hook re-indexing after a large merge is exactly the bulk scan that
    flushes an LRU's hot set — and here a miss costs a network fetch.
    """
    cache = ARC(500)
    cache.put(("hot.md", "s"), b"h" * 100)
    cache.get(("hot.md", "s"))  # promoted to t2

    for i in range(50):  # the scan: fifty documents seen once each
        cache.put((f"cold{i}.md", "s"), b"c" * 100)

    assert cache.get(("hot.md", "s")) == b"h" * 100, "the scan flushed the hot entry"


def test_a_returning_ghost_moves_the_adaptation_target():
    """The ghost lists are what let the policy notice its own mistakes."""
    cache = ARC(300)
    for i in range(10):
        cache.put((f"{i}.md", "s"), b"x" * 100)
    evicted = next(iter(cache.b1))
    before = cache.p
    cache.put(evicted, b"x" * 100)
    assert cache.p > before


def test_ghost_lists_are_bounded():
    """An unbounded ghost list is a slow leak that looks like nothing."""
    cache = ARC(200)
    for i in range(500):
        cache.put((f"{i}.md", "s"), b"x" * 100)
    assert len(cache.b1) + len(cache.b2) <= 2 * max(1, 200 // 64) + 2


def test_nothing_in_this_module_reads_the_clock():
    """Recency is a monotonic ordering, never a timestamp."""
    tree = ast.parse(inspect.getsource(arc_mod))
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert not {"time", "datetime", "random"} & imported, imported


def test_a_zero_budget_is_refused_rather_than_silently_caching_nothing():
    with pytest.raises(ValueError):
        ARC(0)
