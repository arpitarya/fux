"""The materialise-first display cache — PRIORITY.md P5, Arpit's verdict

(`meta-privacy.compare.md`, reopened 2026-08-21). Content-addressed by `sha`
(unlike `refer/fetchcache.py`'s TTL, keyed by `loc`) — a title is a pure
function of a document's bytes, so a hit never goes stale by the clock.
"""

from __future__ import annotations

import json

from fux.store.displaycache import DisplayCache


def test_a_put_entry_is_returned(tmp_path):
    cache = DisplayCache(tmp_path)
    cache.put("sha1", "url:https://x.test/p", "The Handbook")
    assert cache.get("sha1") == "The Handbook"


def test_a_missing_sha_is_a_miss(tmp_path):
    cache = DisplayCache(tmp_path)
    assert cache.get("nope") is None


def test_a_corrupt_entry_is_a_miss_not_an_error(tmp_path):
    """The cache is disposable; a reader must not die for it."""
    cache = DisplayCache(tmp_path)
    cache.put("sha1", "url:https://x.test/p", "T")
    next(cache.directory.glob("*.json")).write_text("{not json", encoding="utf-8")
    assert cache.get("sha1") is None


def test_the_cache_lives_under_the_gitignored_runtime_plane(tmp_path):
    cache = DisplayCache(tmp_path)
    cache.put("sha1", "url:https://x.test/p", "T")
    assert cache.directory.is_relative_to(tmp_path / ".fux" / "runtime")
    assert not (tmp_path / ".fux" / "index").exists()


# -- the size cap ------------------------------------------------------------


def test_unbounded_growth_is_capped(tmp_path):
    cache = DisplayCache(tmp_path, max_bytes=1000)
    for i in range(20):
        cache.put(f"sha{i}", f"url:https://x.test/{i}", "x" * 100)
    total = sum(p.stat().st_size for p in cache.directory.glob("*.json"))
    assert total <= 1000


def _entry_size(sha: str, doc_id: str, title: str, seq: int = 0) -> int:
    """The exact on-disk size of one entry at a given `seq` width — measured
    rather than guessed, same reasoning as `test_fetchcache.py`'s sibling."""
    return len(json.dumps({"sha": sha, "doc_id": doc_id, "title": title, "seq": seq}))


def test_eviction_is_oldest_first(tmp_path):
    entries = [("sha-a", "url:https://x.test/a"), ("sha-b", "url:https://x.test/b"), ("sha-c", "url:https://x.test/c")]
    title = "x" * 400
    one = _entry_size(entries[0][0], entries[0][1], title)
    cache = DisplayCache(tmp_path, max_bytes=one * 2 + 10)
    for sha, doc_id in entries:
        cache.put(sha, doc_id, title)

    assert cache.get("sha-a") is None       # oldest, evicted
    assert cache.get("sha-b") is not None   # survives
    assert cache.get("sha-c") is not None   # newest


def test_seq_orders_by_write_not_by_sha_string(tmp_path):
    """Regression: eviction must follow write order, not lexical sha order —
    guards against an implementation that (mis-)sorts by filename instead."""
    title = "x" * 400
    one = _entry_size("sha-zzz", "url:https://x.test/z", title)
    cache = DisplayCache(tmp_path, max_bytes=one * 2 + 10)
    cache.put("sha-zzz", "url:https://x.test/z", title)  # lexically last, written first
    cache.put("sha-aaa", "url:https://x.test/a", title)
    cache.put("sha-mmm", "url:https://x.test/m", title)

    assert cache.get("sha-zzz") is None     # oldest by write order, evicted
    assert cache.get("sha-aaa") is not None
    assert cache.get("sha-mmm") is not None


def test_a_single_entry_larger_than_the_cap_is_refused_not_a_wipeout(tmp_path):
    kept_size = _entry_size("sha-kept", "url:https://x.test/kept", "x" * 20)
    cache = DisplayCache(tmp_path, max_bytes=kept_size + 50)
    cache.put("sha-kept", "url:https://x.test/kept", "x" * 20)
    cache.put("sha-toobig", "url:https://x.test/toobig", "x" * 10_000)
    assert cache.get("sha-kept") is not None
    assert cache.get("sha-toobig") is None


def test_updating_an_existing_entry_does_not_evict_itself(tmp_path):
    one = _entry_size("sha-p", "url:https://x.test/p", "x" * 100)
    cache = DisplayCache(tmp_path, max_bytes=one + 20)
    cache.put("sha-p", "url:https://x.test/p", "x" * 100)
    cache.put("sha-p", "url:https://x.test/p", "y" * 100)  # same sha, re-written
    assert cache.get("sha-p") == "y" * 100


def test_clear_removes_every_entry(tmp_path):
    cache = DisplayCache(tmp_path)
    cache.put("sha1", "url:https://x.test/p", "T")
    cache.clear()
    assert cache.get("sha1") is None
    assert not list(cache.directory.glob("*.json"))
