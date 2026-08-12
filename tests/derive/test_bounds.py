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
from fux.query.bm25f import BODY_WEIGHT, HEADING_WEIGHT, score_record
from fux.store import term_hash, write_index


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


def _spread_corpus(n_docs: int = 400) -> list[dict]:
    """A corpus built to stress the bound rather than to look realistic.

    Term frequencies and document lengths both vary widely and *independently*,
    so blocks contain a genuine spread of `wtf` and `wlen` — the case where a
    bound that used `mx` alone, or the wrong `wlen`, would be wrong.
    """
    records = []
    common = term_hash("common")
    for i in range(n_docs):
        terms = {common: [i % 7, i % 13 + 1]}
        # A rare term every 10th doc, and a mid-frequency one every 3rd.
        if i % 10 == 0:
            terms[term_hash(f"rare{i}")] = [i % 5, 1]
        if i % 3 == 0:
            terms[term_hash("mid")] = [1, i % 17]
        records.append(_rec(f"file:doc{i:04d}.md", f"Doc {i}", 10 + (i * 37) % 900, terms))
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
    avg_wlen = stats["total_wlen"] / n
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

            for docidx, tf_h, tf_b in runtime.read_block(block):
                actual = score_record(
                    {block.term: [tf_h, tf_b]},
                    docs[docidx]["wlen"],
                    [block.term],
                    {block.term: df},
                    n,
                    avg_wlen,
                )
                checked_postings += 1
                assert actual <= bound, (
                    f"bound violated: block {block.term}#{block.block_no} bound={bound!r} "
                    f"but doc {docidx} scores {actual!r} (tf={tf_h},{tf_b} wlen={docs[docidx]['wlen']})"
                )

    assert checked_blocks > 10, "fixture too small to be a real test"
    assert checked_postings > 500


def test_mx_is_the_max_weighted_tf_in_its_block(built):
    """`mx` must be exactly `max(3*tf_h + tf_b)`, as an integer."""
    runtime = accel.Runtime(built)
    for prefix in {f"{b:02x}" for b in range(256)}:
        buf = runtime.offsets(prefix)
        for index in range(len(buf) // fmt.ENTRY_SIZE):
            raw = fmt.unpack_entry(buf, index)
            block = accel.Block(raw[0].hex(), raw[1], raw[2], raw[3], raw[4], raw[5], raw[6], raw[7], raw[8])
            postings = runtime.read_block(block)
            expected = max(int(HEADING_WEIGHT) * h + int(BODY_WEIGHT) * b for _, h, b in postings)
            assert block.mx == expected


def test_mnw_is_the_min_wlen_in_its_block(built):
    """`mnw` must be the *minimum* length — the direction that makes the bound valid.

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
            assert block.mnw == min(docs[d]["wlen"] for d, _, _ in postings)


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
            docidxs = [d for d, _, _ in runtime.read_block(block)]
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
    n, avg_wlen = stats["n"], stats["total_wlen"] / stats["n"]
    docs = runtime.docs

    attained = 0
    for prefix in {f"{b:02x}" for b in range(256)}:
        buf = runtime.offsets(prefix)
        for index in range(len(buf) // fmt.ENTRY_SIZE):
            raw = fmt.unpack_entry(buf, index)
            block = accel.Block(raw[0].hex(), raw[1], raw[2], raw[3], raw[4], raw[5], raw[6], raw[7], raw[8])
            df = sum(b.count for b in runtime.blocks_for(block.term))
            bound = accel.block_bound(block, df, n, avg_wlen)
            for docidx, tf_h, tf_b in runtime.read_block(block):
                actual = score_record(
                    {block.term: [tf_h, tf_b]}, docs[docidx]["wlen"], [block.term], {block.term: df}, n, avg_wlen
                )
                if actual == bound:
                    attained += 1
                    break

    assert attained > 0, "no block's bound is attained by any posting — the bound is vacuous"
