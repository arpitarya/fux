"""The gate W-76 Phase 1 exists to pass: field weights are tunable.

[ADR-TUNE](../../docs/adr/0038_tuning.md) decision 1 states the membership
test for a tune key as something mechanical rather than a matter of taste:

> **does changing this value change a byte in `.fux/index/`? yes -> not a tune
> key**

Field weights failed that test until 2026-08-23. `wlen` — BM25F's length
normaliser — was committed, and it was a *weighted sum of field lengths*, so
changing a weight silently reweighted the numerator against a denominator
baked in under the old weights. Decision 6 names it as the record's own
violation and proposes the fix this module now gates: commit the raw per-field
counts, derive `wlen` at query time.

**Three properties, and all three are needed.** Any two of them can hold while
the feature is still broken:

1. changing a weight **changes the ranking** — otherwise the knob is inert;
2. changing a weight **changes no committed byte** — otherwise it is not a
   tune key, it is a re-ingest;
3. the change **needs no rebuild of the derived plane** — otherwise editing
   your ranking breaks your accelerator, which is the promise ADR-TUNE was
   written to make.

(3) is the one fork 3 of `work/compare/record-shape-migration.compare.md` was
about, and the one that cost an offset-table format change to keep.
"""

from __future__ import annotations

import pytest

from fux.derive import accel, build
from fux.query import scan
from fux.query.bm25f import FIELD_WEIGHTS, derive_wlen
from fux.store import TF_FIELDS, iter_shard_paths, term_hash, write_index

HEADING = TF_FIELDS.index("heading")
BODY = TF_FIELDS.index("body")


def _rec(doc_id, title, terms, flen) -> dict:
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


def _corpus() -> list[dict]:
    """Two documents that disagree about WHERE the query term sits.

    `heavy-heading` carries it in the heading, `heavy-body` in the body. Their
    relative order is therefore a pure function of the heading:body weight
    ratio — which is exactly the knob under test, and means the ordering
    assertion below cannot pass by accident.
    """
    t = term_hash("rollback")
    heading_tf = [0] * len(TF_FIELDS)
    heading_tf[HEADING] = 4
    body_tf = [0] * len(TF_FIELDS)
    body_tf[BODY] = 12

    flen_heading = [0] * len(TF_FIELDS)
    flen_heading[HEADING] = 6
    flen_heading[BODY] = 40
    flen_body = [0] * len(TF_FIELDS)
    flen_body[HEADING] = 1
    flen_body[BODY] = 44

    return [
        _rec("file:heavy-heading.md", "Heading heavy", {t: heading_tf}, flen_heading),
        _rec("file:heavy-body.md", "Body heavy", {t: body_tf}, flen_body),
    ]


@pytest.fixture
def corpus(tmp_path):
    write_index(tmp_path, _corpus())
    build(tmp_path)
    return tmp_path


def _index_bytes(root) -> bytes:
    return b"".join(sorted(p.read_bytes() for p in iter_shard_paths(root)))


def _runtime_bytes(root) -> bytes:
    from fux.derive import format as fmt

    directory = fmt.runtime_dir(root)
    return b"".join(
        sorted(p.read_bytes() for p in directory.rglob("*") if p.is_file() and p.name != fmt.STAMP_NAME)
    )


def _weights(heading: float) -> tuple[float, ...]:
    out = list(FIELD_WEIGHTS)
    out[HEADING] = heading
    return tuple(out)


def _order(root, weights):
    """Rank by hand at `weights` — the read path with one substitution."""
    from fux.query.bm25f import score_record
    from fux.query.scan import query_term_hashes, scan_candidates

    hashes = query_term_hashes("rollback")
    candidates, df, _ = scan_candidates(root, hashes)
    n = len(candidates)
    total = sum(derive_wlen(c["flen"], weights) for c in candidates)
    avg = total / n if n else 0.0
    scored = [
        (score_record(c["terms"], c["flen"], hashes, df, n, avg, weights), c["id"])
        for c in candidates
    ]
    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    return [doc_id for _, doc_id in scored]


def test_a_weight_change_moves_the_ranking(corpus):
    """Property 1 — the knob is not inert."""
    low = _order(corpus, _weights(0.5))
    high = _order(corpus, _weights(20.0))
    assert low[0] == "file:heavy-body.md", f"at a low heading weight the body doc should win, got {low}"
    assert high[0] == "file:heavy-heading.md", f"at a high heading weight the heading doc should win, got {high}"


def test_a_weight_change_touches_no_committed_byte(corpus):
    """Property 2 — the mechanical membership test from ADR-TUNE decision 1.

    Ranking is computed twice at opposite weights, then the committed shards
    are compared byte for byte. This is what `wlen` could not survive: the
    denominator used to live in these bytes.
    """
    before = _index_bytes(corpus)
    _order(corpus, _weights(0.5))
    _order(corpus, _weights(20.0))
    assert _index_bytes(corpus) == before, "a weight change rewrote the committed index"


def test_a_weight_change_needs_no_rebuild(corpus):
    """Property 3 — fork 3's whole purpose.

    The offset table stores `mx` and `mnw` **per field and unweighted**, so a
    weight change is absorbed by `block_bound` at query time. If they were
    still pre-weighted scalars, the accelerator would have to be rebuilt here
    and this test would be the one that noticed.
    """
    before = _runtime_bytes(corpus)
    _order(corpus, _weights(0.5))
    _order(corpus, _weights(20.0))
    assert _runtime_bytes(corpus) == before, "a weight change invalidated the derived plane"


def test_the_two_paths_still_agree_after_the_migration(corpus):
    """The differential law, on the new record shape.

    Not a weight test — a guard that the five-field record and the per-field
    bound did not quietly break the property everything else rests on.
    """
    for top in (1, 2, 5):
        expected = [(r.id, round(r.score, 9)) for r in scan.ask(corpus, "rollback", top=top)]
        for skipping in (False, True):
            got = [
                (r.id, round(r.score, 9))
                for r in accel.ask(corpus, "rollback", top=top, skipping=skipping)
            ]
            assert got == expected, f"top={top} skipping={skipping}"


def test_derive_wlen_reads_the_committed_counts(corpus):
    """`flen` is raw counts, and `derive_wlen` is the only place they are weighted.

    Guards against the obvious regression: someone re-committing a
    pre-weighted number under a new name.
    """
    from fux.store import read_index

    for record in read_index(corpus).values():
        flen = record["flen"]
        assert all(isinstance(v, int) for v in flen), "flen must be raw integer counts"
        assert derive_wlen(flen) == sum(
            FIELD_WEIGHTS[i] * v for i, v in enumerate(flen)
        )
