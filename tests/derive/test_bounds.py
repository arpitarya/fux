"""Layer 2 of the `mx` correctness proof: the bound is tested, not just argued.

Layer 1 is the analytic argument in `derive/accel.py` — a term's BM25F
contribution is increasing in weighted tf and decreasing in `wlen`, so a
block's `(mx, mnw)` pair dominates every posting in it. Layer 3 is the
end-to-end differential.

**This layer is the one that catches an implementation that disagrees with its
own algebra**, and it is corpus-independent: it walks every block in a built
accelerator and asserts the bound really is ≥ every posting's actual
contribution. A differential can be accidentally green on an easy corpus (it
was — see `tools/differential/run.py:TOPS`); this cannot.
"""

from __future__ import annotations

import pytest

from fux.derive import accel, build
from fux.derive import format as fmt
from fux.derive.format import _FIELD_COUNT
from fux.query.bm25f import derive_wlen, score_record
from fux.store import term_hash, write_index


def _rec(doc_id, title, flen, terms) -> dict:
    return {
        "id": doc_id,
        "src": "git",
        "loc": doc_id.removeprefix("file:"),
        "mode": "extracted",
        "meta": "plain",
        "title": title,
        "phrases": [],
        "terms": terms,
        "flen": flen,
        "edges": [],
    }


def _spread_corpus(n_docs: int = 400) -> list[dict]:
    """A corpus built to stress the bound rather than to look realistic.

    Term frequencies and document lengths both vary widely and *independently*,
    so blocks contain a genuine spread of `wtf` and `wlen` — the case where a
    bound that used `mx` alone, or the wrong `wlen`, would be wrong.

    tf vectors are `[body, heading]` (v2 order — `store.TF_FIELDS`), the
    trailing three fields always absent (trimmed to `[]` by `store.trim` at
    write time, but written explicitly here since these are hand-built
    postings, not run through `hash_terms`).
    """
    records = []
    common = term_hash("common")
    for i in range(n_docs):
        terms = {common: [i % 13 + 1, i % 7]}
        # A rare term every 10th doc, and a mid-frequency one every 3rd.
        if i % 10 == 0:
            terms[term_hash(f"rare{i}")] = [1, i % 5]
        if i % 3 == 0:
            terms[term_hash("mid")] = [i % 17, 1]
        # A single-field flen (body only) so derive_wlen(flen) == flen[0] —
        # the simplest honest translation of the old scalar `wlen`.
        records.append(_rec(f"file:doc{i:04d}.md", f"Doc {i}", [10 + (i * 37) % 900], terms))
    return records


@pytest.fixture
def built(tmp_path):
    write_index(tmp_path, _spread_corpus())
    build(tmp_path)
    return tmp_path


def test_bound_dominates_every_posting_in_every_block(built):
    """The exhaustive assertion: no posting anywhere may exceed its block's bound."""
    runtime = accel.Runtime(built)
    stats = runtime.stats
    n = stats["n"]
    avg_wlen = derive_wlen(list(stats["total_flen"])) / n
    docs = runtime.docs

    checked_blocks = 0
    checked_postings = 0

    for prefix in {f"{b:02x}" for b in range(256)}:
        buf = runtime.offsets(prefix)
        if not buf:
            continue
        for index in range(len(buf) // fmt.ENTRY_SIZE):
            raw = fmt.unpack_entry(buf, index)
            block = accel.Block(raw[0].hex(), raw[1], raw[2], raw[3], raw[4], raw[5], raw[6], raw[7], raw[8])
            df = sum(b.count for b in runtime.blocks_for(block.term))
            bound = accel.block_bound(block, df, n, avg_wlen)
            checked_blocks += 1

            for docidx, tf in runtime.read_block(block):
                actual = score_record(
                    {block.term: tf},
                    docs[docidx]["flen"],
                    [block.term],
                    {block.term: df},
                    n,
                    avg_wlen,
                )
                checked_postings += 1
                assert actual <= bound, (
                    f"bound violated: block {block.term}#{block.block_no} bound={bound!r} "
                    f"but doc {docidx} scores {actual!r} (tf={tf} flen={docs[docidx]['flen']})"
                )

    assert checked_blocks > 10, "fixture too small to be a real test"
    assert checked_postings > 500


def test_mx_is_the_max_weighted_tf_in_its_block(built):
    """`mx` must be exactly the per-field MAXIMUM tf across the block's postings.

    Unweighted since W-76 Phase 1 (`derive/format.py::ENTRY_STRUCT` docstring)
    — `block_bound` recombines with the weights in force at query time.
    """
    runtime = accel.Runtime(built)
    for prefix in {f"{b:02x}" for b in range(256)}:
        buf = runtime.offsets(prefix)
        for index in range(len(buf) // fmt.ENTRY_SIZE):
            raw = fmt.unpack_entry(buf, index)
            block = accel.Block(raw[0].hex(), raw[1], raw[2], raw[3], raw[4], raw[5], raw[6], raw[7], raw[8])
            postings = runtime.read_block(block)
            expected = [0] * _FIELD_COUNT
            for _, tf in postings:
                for i, count in enumerate(tf):
                    if count > expected[i]:
                        expected[i] = count
            assert list(block.mx) == expected


def test_mnw_is_the_min_wlen_in_its_block(built):
    """`mnw` must be the per-field MINIMUM token count — the direction that
    makes the bound valid.

    Using the max would produce a smaller, invalid bound and would still look
    plausible on any corpus whose documents are similar in length.
    """
    runtime = accel.Runtime(built)
    docs = runtime.docs
    for prefix in {f"{b:02x}" for b in range(256)}:
        buf = runtime.offsets(prefix)
        for index in range(len(buf) // fmt.ENTRY_SIZE):
            raw = fmt.unpack_entry(buf, index)
            block = accel.Block(raw[0].hex(), raw[1], raw[2], raw[3], raw[4], raw[5], raw[6], raw[7], raw[8])
            postings = runtime.read_block(block)
            docidxs = [d for d, _ in postings]
            expected = [
                min((docs[d]["flen"][i] if i < len(docs[d]["flen"]) else 0) for d in docidxs)
                for i in range(_FIELD_COUNT)
            ]
            assert list(block.mnw) == expected


def test_doc_range_covers_every_posting(built):
    """`first_doc`/`last_doc` gate which blocks a deferred term reads at all.

    If either were wrong, a block covering a candidate would be skipped and that
    candidate would be scored on a subset of the query — a silent wrong answer.
    """
    runtime = accel.Runtime(built)
    for prefix in {f"{b:02x}" for b in range(256)}:
        buf = runtime.offsets(prefix)
        for index in range(len(buf) // fmt.ENTRY_SIZE):
            raw = fmt.unpack_entry(buf, index)
            block = accel.Block(raw[0].hex(), raw[1], raw[2], raw[3], raw[4], raw[5], raw[6], raw[7], raw[8])
            docidxs = [d for d, _ in runtime.read_block(block)]
            assert block.first_doc == min(docidxs) == docidxs[0]
            assert block.last_doc == max(docidxs) == docidxs[-1]
            assert docidxs == sorted(docidxs), "postings must be docidx-ascending for range gating"


def test_bound_is_not_vacuous(built):
    """A bound that is merely huge proves nothing — it must be reachable.

    Guards against a future "fix" that widens the bound until the differential
    passes: at least one block's bound must be attained by a real posting.
    """
    runtime = accel.Runtime(built)
    stats = runtime.stats
    n, avg_wlen = stats["n"], derive_wlen(list(stats["total_flen"])) / stats["n"]
    docs = runtime.docs

    attained = 0
    for prefix in {f"{b:02x}" for b in range(256)}:
        buf = runtime.offsets(prefix)
        for index in range(len(buf) // fmt.ENTRY_SIZE):
            raw = fmt.unpack_entry(buf, index)
            block = accel.Block(raw[0].hex(), raw[1], raw[2], raw[3], raw[4], raw[5], raw[6], raw[7], raw[8])
            df = sum(b.count for b in runtime.blocks_for(block.term))
            bound = accel.block_bound(block, df, n, avg_wlen)
            for docidx, tf in runtime.read_block(block):
                actual = score_record(
                    {block.term: tf}, docs[docidx]["flen"], [block.term], {block.term: df}, n, avg_wlen
                )
                if actual == bound:
                    attained += 1
                    break

    assert attained > 0, "no block's bound is attained by any posting — the bound is vacuous"


def test_a_v3_runtime_plane_is_refused_with_an_actionable_message(tmp_path):
    """The upgrade door, at the one surface that does not go through `is_fresh`.

    `RUNTIME_SCHEMA` moved to `fux.runtime.v4` on 2026-08-24 because
    `stats.json` stopped storing a pre-weighted `total_wlen` (ADR-TUNE). The
    CLI never reaches this — `is_fresh` refuses a stale schema and the query
    falls back to the scan — but `accel.accel_candidates` is also a direct
    call, and there a missing key would surface as a `KeyError` naming nothing
    a consumer can act on.
    """
    import json

    import pytest

    from fux.derive import accel, format as fmt
    from fux.errors import FuxError

    directory = fmt.runtime_dir(tmp_path)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / fmt.STATS_NAME).write_text(
        json.dumps({"n": 3, "total_wlen": 300, "newest_mtime": 0}), encoding="utf-8"
    )
    runtime = accel.Runtime(tmp_path)
    with pytest.raises(FuxError, match=r"run `fux build`"):
        accel.accel_candidates(runtime, ["deadbeefdeadbeef"], 5)
