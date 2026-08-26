"""W-82 §3.2 — the detector: a changed URL becomes a dirty-list entry.

The loop this closes: the refer plane already fetched every cited URL and
already knew its sha had moved. It rendered `stale` and discarded the fact, so
the index kept the old terms, the document stopped ranking, and **nothing ever
noticed**. These tests pin the three restrictions that keep it honest.
"""

from __future__ import annotations

import pytest

from fux import refer as refer_mod
from fux.maintain import dirty
from fux.refer import Cited
from fux.refer.freshness import Policy, verify


@pytest.fixture
def root(tmp_path):
    (tmp_path / "fux.toml").write_text("", encoding="utf-8")
    return tmp_path


def _cited(doc_id, *, indexed, fetched, note=""):
    return Cited(doc_id, doc_id.split(":", 1)[1], verify(indexed, fetched, note), "http")


def test_a_changed_url_is_recorded(root):
    refer_mod._mark_changed_urls_dirty(root, [_cited("url:https://a", indexed="old", fetched="new")])
    assert dirty.read(root) == ["url:https://a"]


def test_an_unchanged_url_is_not_recorded(root):
    refer_mod._mark_changed_urls_dirty(root, [_cited("url:https://a", indexed="same", fetched="same")])
    assert dirty.read(root) == []


def test_unverified_is_never_recorded(root):
    """`current is None` means *we did not look* — a refused fetch, a network
    failure, a `never` policy.

    Marking those dirty would churn the list on exactly the days the network is
    bad, which is when the mechanism helps least.
    """
    refer_mod._mark_changed_urls_dirty(
        root, [_cited("url:https://a", indexed="old", fetched=None, note="fetch failed")]
    )
    assert dirty.read(root) == []


def test_a_changed_file_document_is_not_recorded(root):
    """A `file:` change already has an event: git observes it and `post-commit`
    re-indexes. Recording it here would be a second write path into a flow that
    already works."""
    refer_mod._mark_changed_urls_dirty(root, [_cited("file:a.md", indexed="old", fetched="new")])
    assert dirty.read(root) == []


def test_recording_is_a_union_not_a_replacement(root):
    """Inherited from `dirty.record`, and asserted here because the detector is
    now a second producer: two answers about different stale URLs must leave
    both pending, not just the most recent."""
    refer_mod._mark_changed_urls_dirty(root, [_cited("url:https://a", indexed="o", fetched="n")])
    refer_mod._mark_changed_urls_dirty(root, [_cited("url:https://b", indexed="o", fetched="n")])
    assert dirty.read(root) == ["url:https://a", "url:https://b"]


def test_nothing_changed_writes_no_file_at_all(root):
    """A read command must not materialise `.fux/runtime/` just to write nothing
    into it — that is how a query surface starts leaving droppings."""
    refer_mod._mark_changed_urls_dirty(root, [_cited("url:https://a", indexed="s", fetched="s")])
    assert not (root / ".fux" / "runtime").exists()


def test_an_unwritable_runtime_dir_does_not_break_the_answer(root, monkeypatch):
    """Best-effort by contract. A detector that can fail an answer is worse than
    no detector."""

    def boom(*_a, **_k):
        raise OSError("read-only file system")

    monkeypatch.setattr(dirty, "record", boom)
    refer_mod._mark_changed_urls_dirty(root, [_cited("url:https://a", indexed="o", fetched="n")])  # no raise


def test_the_detector_does_not_change_what_the_bundle_reports(root):
    """The differential law, applied to this change.

    Recording a doc id is local, gitignored state. It must be invisible in the
    bundle — otherwise two identical runs differ because of detector state,
    which is the exact failure the ARC cache's `"note": "cache hit"` leak was.
    """
    documents = [_cited("url:https://a", indexed="old", fetched="new")]
    before = [d.as_record() for d in documents]
    refer_mod._mark_changed_urls_dirty(root, documents)
    refer_mod._mark_changed_urls_dirty(root, documents)  # again, now with a non-empty list
    assert [d.as_record() for d in documents] == before


def test_a_cached_verdict_that_is_definitively_stale_still_counts(root):
    """A TTL hit is older evidence, not absent evidence.

    `cached` carries `current` computed on bytes that really were fetched, so a
    `stale` reading from one is a genuine observation — just an earlier one. The
    dirty list is advisory and the refresh re-fetches anyway, so acting on it
    costs a fetch at worst and recovers recall at best.
    """
    from fux.refer.freshness import cached

    documents = [Cited("url:https://a", "https://a", cached("old", "new", 10, 300), "http")]
    refer_mod._mark_changed_urls_dirty(root, documents)
    assert dirty.read(root) == ["url:https://a"]


def test_policy_that_forbids_fetching_yields_nothing_to_detect(root):
    """`never` produces `unverified` for every external document, so the
    detector is silent by construction rather than by a special case."""
    policy = Policy(mode="never")
    decision = refer_mod.freshness_mod.decide(policy)
    assert not decision.fetch
    documents = [_cited("url:https://a", indexed="old", fetched=None, note=decision.reason)]
    refer_mod._mark_changed_urls_dirty(root, documents)
    assert dirty.read(root) == []
