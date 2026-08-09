"""FuxVec: sign quantization, the full-corpus Hamming scan, and the rescue.

The rescue test is the one that matters. ADR 0006 recorded a miss class the
v0.22 engine could not fix by design — documents with *zero* lexical overlap
were unreachable, because the dense pass only re-scored BM25F's candidates.
Scanning every document's 32-byte code removes that ceiling, and
:func:`test_rescues_the_recorded_zero_candidate_miss` pins the exact query
ADR 0006 named.
"""

from __future__ import annotations

import json

import pytest

from fux.embed.fuxvec import CODE_BYTES, doc_code, hamming, prefilter, quantize
from fux.embed.model import Vec

from test_ingest import run


def vec(components) -> Vec:
    from math import sqrt

    q = tuple(components)
    return Vec(q=q, scale=1.0, norm=sqrt(sum(x * x for x in q)) or 1.0)


def dims(n=256, fill=0):
    return [fill] * n


# -- quantization ----------------------------------------------------------


def test_code_is_32_bytes():
    assert len(quantize(vec(dims()))) == CODE_BYTES


def test_bit_is_set_for_positive_components():
    components = dims()
    components[0] = 5
    components[7] = 1
    components[8] = -3  # negative and zero must stay clear
    code = quantize(vec(components))
    bits = int.from_bytes(code, "little")
    assert bits >> 0 & 1 and bits >> 7 & 1
    assert not bits >> 8 & 1


def test_quantization_is_deterministic():
    components = dims()
    components[3] = 2
    assert quantize(vec(components)) == quantize(vec(components))


def test_hamming_counts_differing_bits():
    a, b = dims(), dims()
    a[0] = a[1] = 1
    b[1] = 1
    assert hamming(quantize(vec(a)), quantize(vec(b))) == 1
    assert hamming(quantize(vec(a)), quantize(vec(a))) == 0


# -- document codes --------------------------------------------------------


def test_doc_code_is_the_scale_weighted_mean_sign():
    strong = dims()
    strong[0] = 10
    weak = dims()
    weak[0] = -1
    code = doc_code([vec(strong), vec(weak)])
    assert int.from_bytes(code, "little") & 1  # the stronger sign wins


def test_scale_is_respected_across_chunks():
    """A chunk with a large scale must not dominate purely by quantized value."""
    small_scale = Vec(q=tuple([100] + [0] * 255), scale=0.001, norm=100.0)
    large_scale = Vec(q=tuple([-1] + [0] * 255), scale=10.0, norm=1.0)
    assert not int.from_bytes(doc_code([small_scale, large_scale]), "little") & 1


def test_no_embeddable_chunk_yields_no_code():
    assert doc_code([None, None]) is None
    assert doc_code([]) is None


# -- the scan --------------------------------------------------------------


def test_prefilter_ranks_by_distance_and_truncates():
    near, far = dims(), dims()
    near[0] = 1
    far[0] = 1
    for i in range(1, 40):
        far[i] = 1
    codes = {"docs/near.md": quantize(vec(near)), "docs/far.md": quantize(vec(far))}
    query = quantize(vec(near))
    assert prefilter(query, codes, 2) == ["docs/near.md", "docs/far.md"]
    assert prefilter(query, codes, 1) == ["docs/near.md"]


def test_prefilter_ties_break_on_doc_id():
    """Equal distances must order reproducibly, or the candidate set drifts."""
    same = quantize(vec(dims()))
    codes = {"docs/z.md": same, "docs/a.md": same, "docs/m.md": same}
    assert prefilter(same, codes, 3) == ["docs/a.md", "docs/m.md", "docs/z.md"]


def test_prefilter_on_an_empty_corpus():
    assert prefilter(quantize(vec(dims())), {}, 500) == []


# -- integration: the rescue ----------------------------------------------


def corpus_project(tmp_path):
    """A corpus where the *answer* shares no vocabulary with the question.

    Note what "zero lexical candidates" means in ADR 0006: the correct
    *document* has no lexical overlap, not that the query matches nothing at
    all. `decoy.md` is here to give BM25F something to return, exactly as the
    real fixture corpus does — a query matching nothing anywhere is a different
    situation, and one Fux answers with "No confident matches".
    """
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "storage.md").write_text(
        "---\ntitle: ADR-001 Use SQLite for local storage\n---\n"
        "# ADR-001: Use SQLite for local storage\n\n"
        "We chose SQLite because the service is single-node and embedded storage\n"
        "removes an operational dependency. Postgres was rejected for the first\n"
        "version because it requires a separate server process.\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "decoy.md").write_text(
        "---\ntitle: Disk hygiene\n---\n# Disk hygiene\n\n"
        "Technology refresh: prune stale rows from the archive on disk monthly.\n",
        encoding="utf-8",
    )
    (tmp_path / "fux.toml").write_text('[sources]\ndocs = ["docs"]\n', encoding="utf-8")
    return tmp_path


def test_rescues_the_recorded_zero_candidate_miss(tmp_path, monkeypatch, capsys):
    """The ADR 0006 miss class, fixed. Regression guard for the whole feature."""
    corpus_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    query = "what technology stores rows on disk"
    capsys.readouterr()

    run(tmp_path, monkeypatch, "find", query, "--json", "--lexical-only")
    lexical = json.loads(capsys.readouterr().out)["results"]
    assert lexical, "the decoy must give BM25F something, or this is a different test"
    assert not any(r["path"] == "docs/storage.md" for r in lexical), (
        "the premise of this test is that the *answer* has zero lexical overlap "
        "— if this fires, the fixture drifted and the rescue is no longer proven"
    )

    run(tmp_path, monkeypatch, "find", query, "--json")
    hybrid = json.loads(capsys.readouterr().out)["results"]
    assert any(r["path"] == "docs/storage.md" for r in hybrid), (
        "dense_global must reach a document with no lexical overlap"
    )


def test_a_query_matching_nothing_still_says_so(tmp_path, monkeypatch, capsys):
    """dense_global must not turn honest emptiness into confident noise.

    A binary prefilter always has a nearest neighbour, so without this the
    "No confident matches" signal would be unreachable — measured noise scores
    0.23–0.26 cosine, overlapping a true rescue's 0.34, so no floor separates
    them reliably.
    """
    corpus_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    run(tmp_path, monkeypatch, "ask", "flibbertigibbet xyzzy wombat", "--json")
    assert json.loads(capsys.readouterr().out)["results"] == []


def test_rescued_results_are_labelled_with_their_global_rank(tmp_path, monkeypatch, capsys):
    corpus_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    run(tmp_path, monkeypatch, "ask", "what technology stores rows on disk", "--json")
    results = json.loads(capsys.readouterr().out)["results"]
    assert any(
        r.get("hybrid", {}).get("dense_global_rank") for r in results
    ), "a rescued chunk must say which retriever found it"


def test_lexical_only_is_untouched_by_dense_global(tmp_path, monkeypatch, capsys):
    corpus_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    run(tmp_path, monkeypatch, "ask", "sqlite storage", "--json", "--lexical-only")
    first = capsys.readouterr().out
    run(tmp_path, monkeypatch, "ask", "sqlite storage", "--json", "--lexical-only")
    assert capsys.readouterr().out == first
    payload = json.loads(first)
    assert payload["engine"] == "bm25f"
    assert all("hybrid" not in r for r in payload["results"])


def test_dense_global_is_deterministic(tmp_path, monkeypatch, capsys):
    corpus_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    run(tmp_path, monkeypatch, "ask", "what technology stores rows on disk", "--json")
    first = capsys.readouterr().out
    run(tmp_path, monkeypatch, "ask", "what technology stores rows on disk", "--json")
    assert capsys.readouterr().out == first


def test_prefilter_width_is_configurable(tmp_path, monkeypatch):
    from fux.config import load

    corpus_project(tmp_path)
    (tmp_path / "fux.toml").write_text(
        '[sources]\ndocs = ["docs"]\n[index]\nprefilter_width = 7\n', encoding="utf-8"
    )
    run(tmp_path, monkeypatch, "ingest")
    assert load(tmp_path).index.prefilter_width == 7
