"""Layer 3: the differential law, as a fast hermetic test.

The wide sweep lives in `tools/differential/` and runs over a real repo. This
is its unit-suite counterpart: synthetic corpora built to hit the shapes that
break candidate generators, checked byte-for-byte at several `top` values.

**Why `top` is swept here too.** A mutation test on the real corpus showed that
at `top=5` the rarest query term already decides the answer, so replacing the
block bound with a constant zero still produced byte-identical output. The
bound only becomes load-bearing at larger `top`. A differential that checked
one `top` would certify an unsound bound as proven — so it checks four.
"""

from __future__ import annotations

import json

import pytest

from fux.derive import accel, build
from fux.query import scan
from fux.store import term_hash, title_hash, write_index

TOPS = (1, 5, 20, 50)


def _rec(doc_id, title, wlen, terms) -> dict:
    return {
        "id": doc_id,
        "src": "git",
        "loc": doc_id.removeprefix("file:"),
        "mode": "extracted",
        "meta": "plain",
        "title": title,
        "phrases": [],
        "terms": terms,
        "wlen": wlen,
        "edges": [],
    }


def _payload(results) -> str:
    """Exactly what `fux ask --json` prints — the surface under test."""
    return json.dumps({"results": [r.__dict__ for r in results]}, indent=2)


def assert_identical(root, queries, tops=TOPS):
    for query in queries:
        for top in tops:
            expected = _payload(scan.ask(root, query, top=top))
            for skipping in (False, True):
                got = _payload(accel.ask(root, query, top=top, skipping=skipping))
                assert got == expected, (
                    f"differential broken: query={query!r} top={top} skipping={skipping}\n"
                    f"scan:\n{expected}\naccel:\n{got}"
                )


@pytest.fixture
def corpus(tmp_path):
    """A corpus with a genuine df spread, ties, and a very common term."""
    records = []
    for i in range(250):
        terms = {term_hash("common"): [0, 1 + i % 4]}
        if i % 5 == 0:
            terms[term_hash("mid")] = [1, i % 9]
        if i % 25 == 0:
            terms[term_hash(f"rare{i}")] = [2, 3]
        # Deliberate exact duplicates: identical tf AND identical wlen, so the
        # scores tie and only the id tie-break separates them.
        wlen = 100 if i % 7 == 0 else 20 + (i * 31) % 700
        records.append(_rec(f"file:d{i:04d}.md", f"Doc {i}", wlen, terms))
    write_index(tmp_path, records)
    build(tmp_path)
    return tmp_path


def test_single_terms(corpus):
    assert_identical(corpus, ["common", "mid", "rare0", "rare25", "absent"])


def test_multi_term_queries(corpus):
    assert_identical(
        corpus,
        ["common mid", "rare0 common", "mid rare25 common", "common common", "rare0 rare25"],
    )


def test_queries_that_match_nothing(corpus):
    assert_identical(corpus, ["", "the", "a of and is", "zzzzzz", "x"])


def test_score_ties_break_identically(corpus):
    """The tie-break on `id` is where a candidate-order difference would show.

    Both paths generate candidates in different orders by construction — shard
    order vs postings order — so a tie is the one case where the sort itself
    has to do the work.
    """
    results = scan.ask(corpus, "common", top=50)
    scores = [r.score for r in results]
    assert len(set(scores)) < len(scores), "fixture no longer produces ties"
    assert_identical(corpus, ["common"], tops=(50,))


def test_top_larger_than_the_corpus(corpus):
    assert_identical(corpus, ["common"], tops=(1000,))


def test_single_document_corpus(tmp_path):
    write_index(tmp_path, [_rec("file:a.md", "A", 10, {term_hash("solo"): [1, 1]})])
    build(tmp_path)
    assert_identical(tmp_path, ["solo", "absent", ""], tops=(1, 5))


def test_document_without_wlen(tmp_path):
    """`scan.py` counts it in `n` but contributes 0 to `total_wlen`.

    The accelerator must reproduce that asymmetry rather than the more
    sensible-looking thing.
    """
    record = _rec("file:a.md", "A", 0, {term_hash("solo"): [1, 1]})
    del record["wlen"]
    write_index(tmp_path, [record, _rec("file:b.md", "B", 40, {term_hash("solo"): [1, 2]})])
    build(tmp_path)
    assert_identical(tmp_path, ["solo"], tops=(1, 5))


def _hashed(doc_id, title, wlen, terms) -> dict:
    """A `meta: hashed` record, the shape `--refresh-urls` actually writes."""
    record = _rec(doc_id, title, wlen, terms)
    del record["title"], record["phrases"]
    record["src"] = "url"
    record["loc"] = doc_id.removeprefix("url:")
    record["meta"] = "hashed"
    record["title_h"] = title_hash(title)
    return record


def test_hashed_meta_titles(tmp_path):
    """`title_h` records must resolve the same display title on both paths."""
    write_index(tmp_path, [_hashed("url:https://x/a", "Page A", 10, {term_hash("solo"): [1, 1]})])
    build(tmp_path)
    assert_identical(tmp_path, ["solo"], tops=(1,))
    # The prefix is storage. What a verb shows is the hash, opaque either way.
    assert accel.ask(tmp_path, "solo", top=1)[0].title == term_hash("Page A")


def test_a_corpus_holding_a_hashed_record_builds_and_agrees(tmp_path):
    """W-47: this harness had never seen a hashed record, so it never saw the bug.

    A bare 16-hex `title_h` is a quoted 16-hex token outside `terms`. The scan
    counts it toward that term's df from the raw bytes; the accelerator counts
    from the postings. The build refused the index rather than diverge — so the
    L5 default shipped an index no `fux build` would accept, and the only thing
    standing between the engine and a fast wrong answer was a stopped run.
    """
    records = [
        _rec("file:a.md", "A", 12, {term_hash("oncall"): [1, 2], term_hash("rotation"): [0, 1]}),
        _rec("file:b.md", "B", 30, {term_hash("oncall"): [0, 1]}),
        _hashed("url:https://x/handbook", "Oncall handbook", 11,
                {term_hash("oncall"): [1, 3], term_hash("pager"): [0, 2]}),
        _hashed("url:https://x/deploys", "Deploy runbook", 20, {term_hash("rotation"): [0, 1]}),
    ]
    write_index(tmp_path, records)
    build(tmp_path)  # must not raise: the invariant holds by field shape
    assert_identical(tmp_path, ["oncall", "rotation", "pager", "oncall rotation"])


def test_a_pre_prefix_title_h_still_stops_the_build_and_names_the_migration(tmp_path):
    """An index written before the prefix is old, not corrupt. Say which."""
    from fux.errors import FuxError

    record = _hashed("url:https://x/a", "Page A", 10, {term_hash("solo"): [1, 1]})
    record["title_h"] = term_hash("Page A")  # the bare, pre-2026-08-19 shape
    write_index(tmp_path, [record])
    with pytest.raises(FuxError, match="predates the `h:` prefix"):
        build(tmp_path)


def test_a_term_spanning_many_blocks(tmp_path):
    """More than `BLOCK_SIZE` postings for one term — the blocking path itself."""
    from fux.derive.format import BLOCK_SIZE

    n = BLOCK_SIZE * 3 + 7
    write_index(
        tmp_path,
        [_rec(f"file:d{i:04d}.md", f"D{i}", 10 + i, {term_hash("everywhere"): [0, 1 + i % 3]}) for i in range(n)],
    )
    build(tmp_path)
    runtime = accel.Runtime(tmp_path)
    assert len(runtime.blocks_for(term_hash("everywhere"))) == 4
    assert_identical(tmp_path, ["everywhere"], tops=(1, 5, 20, 50))
