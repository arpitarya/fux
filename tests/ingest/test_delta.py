"""Delta ingest — the same bytes, without re-extracting what did not change.

The property that matters is **byte-identity with a full run**. A faster ingest
that produced a different index would break L3 and the differential law at
once, so every test here is written against the full run's output rather than
against a hand-written expectation.
"""

from __future__ import annotations

import hashlib

import pytest

from fux.ingest.run import run
from fux.store import HEADER, iter_shard_paths, read_index, shard_path
from fux.store.reader import read_shard


def _doc(i: int, revision: int = 0) -> str:
    return (
        f"---\ntitle: Document {i}\n---\n\n# Document {i}\n\n"
        f"Revision {revision} of a page about widget{i} and gadget{revision}.\n\n"
        f"See [next](doc-{i + 1}.md).\n"
    )


def _init(tmp_path) -> None:
    listing = tmp_path / ".fux" / "sources" / "dirs"
    listing.parent.mkdir(parents=True, exist_ok=True)
    listing.write_text("docs\n", encoding="utf-8")
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (tmp_path / "docs").mkdir(exist_ok=True)


@pytest.fixture
def corpus(tmp_path):
    _init(tmp_path)
    for i in range(6):
        (tmp_path / "docs" / f"doc-{i}.md").write_text(_doc(i), encoding="utf-8")
    run(tmp_path)
    return tmp_path


def _digest(root) -> dict[str, str]:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in iter_shard_paths(root)}


# -- the property the whole feature rests on -------------------------------


def test_a_delta_run_is_byte_identical_to_a_full_run(corpus):
    run(corpus, full=True)
    full = _digest(corpus)
    report = run(corpus)
    assert report.reused_count == 6
    assert _digest(corpus) == full


def test_byte_identical_after_an_edit_too(corpus):
    (corpus / "docs" / "doc-2.md").write_text(_doc(2, 9), encoding="utf-8")
    delta = run(corpus)
    after_delta = _digest(corpus)
    run(corpus, full=True)
    assert _digest(corpus) == after_delta
    assert delta.reused_count == 5      # everything but the one that changed


def test_byte_identical_after_an_addition(corpus):
    """An added document can resolve a link that dangled — edges must re-resolve."""
    (corpus / "docs" / "doc-6.md").write_text(_doc(6), encoding="utf-8")
    run(corpus)
    after_delta = _digest(corpus)
    run(corpus, full=True)
    assert _digest(corpus) == after_delta


def test_an_addition_repairs_a_dangling_edge_in_an_unchanged_document(corpus):
    """The reason `edges` is never carried forward, asserted rather than argued."""
    before = read_index(corpus)["file:docs/doc-5.md"]["edges"]
    (corpus / "docs" / "doc-6.md").write_text(_doc(6), encoding="utf-8")
    run(corpus)
    after = read_index(corpus)["file:docs/doc-5.md"]["edges"]
    assert after != before, "doc-5's link to doc-6 should have resolved"


def test_byte_identical_after_a_deletion(corpus):
    (corpus / "docs" / "doc-3.md").unlink()
    run(corpus)
    after_delta = _digest(corpus)
    run(corpus, full=True)
    assert _digest(corpus) == after_delta


# -- what reuse is gated on -------------------------------------------------


def test_ver_still_bumps_only_on_this_documents_own_sha(corpus):
    before = read_index(corpus)["file:docs/doc-0.md"]["ver"]
    run(corpus)
    assert read_index(corpus)["file:docs/doc-0.md"]["ver"] == before
    (corpus / "docs" / "doc-0.md").write_text(_doc(0, 1), encoding="utf-8")
    report = run(corpus)
    assert read_index(corpus)["file:docs/doc-0.md"]["ver"] == before + 1
    assert report.changed_count == 1


def test_an_analyzer_bump_can_never_be_silently_carried_forward(corpus):
    """Two analyzers inside one index would be undetectable afterwards.

    The reader refuses outright — `ADR-recorded analyzer bumps only` — so a
    delta run cannot reach the reuse decision with a stale analyzer's records
    in hand. `_reusable` re-checks the header anyway, because a check whose
    only guard is another module's behaviour is a check that leaves on the day
    that module changes.
    """
    import json

    from fux.errors import FuxError

    shard = iter_shard_paths(corpus)[0]
    header, records = read_shard(shard)
    lines = [json.dumps(dict(header, analyzer="v0"), sort_keys=True, separators=(",", ":"))]
    lines += [json.dumps(r, sort_keys=True, separators=(",", ":")) for r in records]
    shard.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(FuxError, match="analyzer"):
        run(corpus)


def test_reusable_refuses_a_header_that_is_not_the_current_one(corpus, monkeypatch):
    """The re-check itself, exercised directly."""
    import sys

    # `fux.ingest.run` names the *function* on the package — the module is in
    # sys.modules under the same dotted path.
    run_mod = sys.modules["fux.ingest.run"]
    monkeypatch.setattr(run_mod.store_mod, "HEADER", dict(HEADER, tf_fields=["body"]))
    assert run(corpus).reused_count == 0


def test_full_forces_re_extraction(corpus):
    assert run(corpus, full=True).reused_count == 0


def test_a_first_ingest_reuses_nothing(tmp_path):
    _init(tmp_path)
    (tmp_path / "docs" / "a.md").write_text(_doc(0), encoding="utf-8")
    assert run(tmp_path).reused_count == 0
