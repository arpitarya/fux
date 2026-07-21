"""The df sidecar and the parity guarantee it exists to make provable.

Amended DoD 7 (Arpit, 2026-07-21): lean rankings are *identical* to full, not
approximately so, because both feed the scorer the same inputs — exact tf from
re-derived text, exact df/n/avg_wlen from `state/df/`.

The headline test here is :func:`test_lean_matches_full_over_the_whole_corpus`:
every term in the corpus, scored both ways, compared exactly.
"""

from __future__ import annotations

import pytest

from fux.config import BM25FParams, load
from fux.errors import FuxError
from fux.index import backend_for, load_searcher
from fux.index.bm25f import Searcher, tokenize
from fux.query.lean import LeanCorpus
from fux.state import df as dfmod

from test_ingest import make_project, run


def rich_project(tmp_path):
    """A corpus with enough vocabulary overlap that idf actually discriminates."""
    make_project(tmp_path)
    docs = tmp_path / "docs"
    (docs / "rollback.md").write_text(
        "---\ntitle: Rollback runbook\n---\n"
        "# Rollback\n\nRollbacks complete within ten minutes of a failed health check.\n"
        "## Procedure\n\nDrain traffic, restore the previous release, verify telemetry.\n",
        encoding="utf-8",
    )
    (docs / "telemetry.md").write_text(
        "---\ntitle: Telemetry pipeline\n---\n"
        "# Telemetry\n\nThe exporter batches telemetry every thirty seconds.\n"
        "## Health checks\n\nHealth checks drive rollback decisions and telemetry alerts.\n",
        encoding="utf-8",
    )
    (docs / "install.md").write_text(
        "---\ntitle: Install guide\n---\n"
        "# Install\n\nInstall the widget service with pip, then verify telemetry flows.\n",
        encoding="utf-8",
    )
    return tmp_path


# -- varint + record format ------------------------------------------------


@pytest.mark.parametrize("value", [0, 1, 127, 128, 300, 2**31, 2**63 - 1])
def test_varint_round_trips(value):
    buf = bytearray()
    dfmod._put_varint(buf, value)
    assert dfmod._get_varint(bytes(buf), 0) == (value, len(buf))


def test_bucket_round_trips_and_sorts_ascending():
    entries = [(500, 3), (10, 1), (2**40, 7)]
    blob = dfmod.pack_bucket(entries)
    assert dfmod.unpack_bucket(blob) == {10: 1, 500: 3, 2**40: 7}


def test_bucket_bytes_are_input_order_independent():
    a = dfmod.pack_bucket([(5, 1), (9, 2), (1, 3)])
    b = dfmod.pack_bucket([(9, 2), (1, 3), (5, 1)])
    assert a == b


def test_stats_round_trip():
    blob = dfmod.pack_stats(12, 40, (100, 200, 300))
    assert dfmod.unpack_stats(blob) == (12, 40, (100, 200, 300))


def test_bad_magic_is_reported():
    with pytest.raises(FuxError, match="corrupt"):
        dfmod.unpack_bucket(b"NOTAHEADER!!" + b"\x00", "df/aa.bin")


def test_term_bucket_matches_the_hash_low_byte():
    for term in ("rollback", "telemetry", "café"):
        assert dfmod.bucket_of_term(term) == f"{dfmod.term_hash(term) & 0xFF:02x}"


# -- correctness of the stored statistics ----------------------------------


def test_sidecar_df_equals_the_searchers_own_df(tmp_path, monkeypatch):
    """The sidecar must agree with what the full Searcher derives, term for term."""
    rich_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    config = load(tmp_path)
    searcher = load_searcher(config)
    stats = dfmod.load_df(tmp_path)

    assert stats.total_chunks == len(searcher.chunks)
    for term, plist in searcher.postings.items():
        assert stats.df_of(term) == len(plist), f"df mismatch for {term!r}"


def test_avg_wlen_matches_the_searchers(tmp_path, monkeypatch):
    rich_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    config = load(tmp_path)
    searcher = load_searcher(config)
    stats = dfmod.load_df(tmp_path)
    assert stats.avg_wlen(config.bm25f) == pytest.approx(searcher.avg_wlen, rel=1e-12)


def test_avg_wlen_recomputes_for_other_weights(tmp_path, monkeypatch):
    """Sums are stored, not averages — so re-weighting needs no re-ingest."""
    rich_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    stats = dfmod.load_df(tmp_path)
    files = backend_for(load(tmp_path)).load(tmp_path)
    params = BM25FParams(heading=1.0, path=5.0, body=2.0)
    assert stats.avg_wlen(params) == pytest.approx(
        Searcher(files, params).avg_wlen, rel=1e-12
    )


def test_sidecar_is_byte_identical_across_ingests(tmp_path, monkeypatch):
    rich_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    first = {p.name: p.read_bytes() for p in (tmp_path / ".fux/state/df").glob("*.bin")}
    run(tmp_path, monkeypatch, "ingest")
    after = {p.name: p.read_bytes() for p in (tmp_path / ".fux/state/df").glob("*.bin")}
    assert after == first


def test_sidecar_tracks_removals(tmp_path, monkeypatch):
    rich_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    before = dfmod.load_df(tmp_path)
    (tmp_path / "docs" / "telemetry.md").unlink()
    run(tmp_path, monkeypatch, "ingest")
    after = dfmod.load_df(tmp_path)
    assert after.total_chunks < before.total_chunks
    assert after.df_of("exporter") == 0  # the only doc using it is gone


def test_stats_live_in_one_file_not_every_bucket(tmp_path, monkeypatch):
    """Repeating corpus counts per bucket would dirty all 256 on every commit."""
    rich_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    base = tmp_path / ".fux/state/df"
    assert (base / dfmod.STATS_NAME).is_file()
    assert len(list(base.glob("*.bin"))) > 2  # terms really are sharded


# -- the guarantee ---------------------------------------------------------


def test_lean_matches_full_over_the_whole_corpus(tmp_path, monkeypatch):
    """Amended DoD 7: every corpus term, scored lean and full, must rank the same.

    The lean profile scores a *candidate subset*, which is precisely where a
    subset-derived idf would diverge — so the subset is what gets compared,
    against full's ranking restricted to those same documents. Every term in
    the vocabulary, not a sample and not the eval set.
    """
    rich_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    config = load(tmp_path)
    full = load_searcher(config)
    corpus = LeanCorpus(config)

    vocabulary = sorted(full.postings)
    assert len(vocabulary) > 40, "corpus too thin to be a meaningful parity test"

    all_docs = sorted(backend_for(config).load(tmp_path))
    subset = all_docs[: max(2, len(all_docs) // 2)]  # a real candidate slice
    assert len(subset) < len(all_docs), "the subset must be smaller, or idf is untested"

    lean = corpus.scored_searcher(subset)
    assert lean is not None, "the sidecar must be present after ingest"

    for term in vocabulary:
        expected = [h for h in full.search(term, top=500) if h.file in set(subset)][:10]
        actual = lean.search(term, top=10)
        assert [(h.file, h.ordinal) for h in actual] == [
            (h.file, h.ordinal) for h in expected
        ], f"ranking diverged for {term!r}"
        for lean_hit, full_hit in zip(actual, expected):
            assert lean_hit.score == pytest.approx(full_hit.score, rel=1e-12), (
                f"score diverged for {term!r} on {full_hit.file}"
            )


def test_lean_matches_full_on_multi_term_queries(tmp_path, monkeypatch):
    rich_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    config = load(tmp_path)
    full = load_searcher(config)
    corpus = LeanCorpus(config)
    all_docs = sorted(backend_for(config).load(tmp_path))
    subset = all_docs[: max(2, len(all_docs) // 2)]
    lean = corpus.scored_searcher(subset)

    for query in (
        "how fast are rollbacks after failed health checks",
        "install the widget service",
        "telemetry exporter batches",
        "rollback telemetry health",
    ):
        expected = [h for h in full.search(query, top=500) if h.file in set(subset)][:10]
        actual = lean.search(query, top=10)
        assert [(h.file, h.ordinal, round(h.score, 12)) for h in actual] == [
            (h.file, h.ordinal, round(h.score, 12)) for h in expected
        ], f"diverged for {query!r}"


def test_subset_scoring_would_diverge_without_the_sidecar(tmp_path, monkeypatch):
    """The control: this is the bug the sidecar exists to prevent.

    Scoring a subset with subset-derived statistics gives different numbers —
    which is exactly why lean must not do it.
    """
    rich_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    config = load(tmp_path)
    full = load_searcher(config)
    files = backend_for(config).load(tmp_path)

    subset = {k: files[k] for k in sorted(files)[:2]}
    naive = Searcher(subset, config.bm25f)  # no stats injected
    stats = dfmod.load_df(tmp_path)
    exact = Searcher(subset, config.bm25f, stats=stats)

    term = next(t for t in sorted(full.postings) if len(naive.search(t, top=1)) == 1)
    assert naive.search(term, top=1)[0].score != exact.search(term, top=1)[0].score


def test_hash_collision_fails_loudly(tmp_path, monkeypatch):
    """Exactness is enforced, not assumed: a collision must never be absorbed."""
    real_hash = dfmod.term_hash
    monkeypatch.setattr(dfmod, "term_hash", lambda term: 0xABCD)  # force a collision

    files = {
        "docs/a.md": {
            "sha256": "aa", "fidelity": "inferred", "title": "A",
            "chunks": [{"heading": "A", "text": "alpha beta", "start": 1,
                        "end": 2, "words": 2}],
        }
    }
    with pytest.raises(FuxError, match="hash collision"):
        dfmod.build(files)
    monkeypatch.setattr(dfmod, "term_hash", real_hash)


def test_empty_corpus_produces_usable_stats(tmp_path):
    stats, buckets = dfmod.build({})
    assert stats.total_chunks == 0 and buckets == {}
    assert stats.avg_wlen(BM25FParams()) == 1.0  # never divides by zero
