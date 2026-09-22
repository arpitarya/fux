"""RM3 pseudo-relevance feedback — an `--expand` the engine fills in itself. W-168 step 5.

## What it does

RM3 (Lavrenko & Croft 2001; Abdul-Jaleel et al., TREC 2004) takes the top
documents of a first pass, picks the terms most typical of them, and re-queries
once with those terms at a low weight. **Every choice below is the frozen
pre-registration's** ([`2026-09-23-rm3`](../../../work/regression/2026-09-23-rm3/PRE-REGISTRATION.md)),
fixed before this file existed so the build could not choose any of them after
a number did:

| | value |
|---|---|
| feedback documents | the top `FB_DOCS = 10` of the first pass |
| feedback terms | `FB_TERMS = 10`, excluding every term of the original query |
| term score | RM1: `Σ_d P(t|d) · P(q|d)` over the feedback documents |
| `P(t|d)` | the term's weighted tf over the document's `wlen`, both under the `Scoring` in force |
| `P(q|d)` | the document's first-pass score, normalised to sum to 1 over the feedback set |
| tie-break | ascending term hash |

⚠ **`P(t|d)` is weighted tf over weighted length**, which is the one reading of
the pre-registration's *"`tf / wlen`"* that keeps numerator and denominator in
the same units: `wlen` is the field-weighted token count
([`bm25f.derive_wlen`](bm25f.py)), so the tf beside it is field-weighted too.

## How it is scored — through `query/expand.build`, and nothing new

The ten terms become an [`Expansion`](expand.py) at `[ranking] rm3_weight`, with
`required` = the original query's hashes. So **SR-EXPAND's refusal holds
unchanged**: a document that matches only feedback terms is dropped by `rank()`
before its score is kept. RM3 adds no scoring arithmetic of its own.

## `0.0` is the byte-identity guarantee

At the default no first pass runs, no record is read and the expansion is the
caller's own — `run_query` does exactly what it did before this module existed.

## It reads committed records, and so it is the same on both candidate paths

The first pass returns `(id, score)` pairs that the scan and the accelerator
agree on byte for byte (the differential law). The feedback terms are then
computed from those ten ids' **committed** records, read by shard, in rank
order — so the second pass's input does not depend on which path produced the
first. The Node reader's twin is [`node/src/query/rm3.mjs`](../../../node/src/query/rm3.mjs).

🔴 **The index holds hashes, not words** ([L2](../../../records/0004_LAW-2-content-never-durable.md)),
and so does this: a feedback term is a term hash out of a record's `terms`, and
no document text is opened.
"""

from __future__ import annotations

from pathlib import Path

from .bm25f import DEFAULT_SCORING, Scoring, derive_wlen, weighted_tf

__all__ = ["FB_DOCS", "FB_TERMS", "feedback_terms"]

#: The pre-registration's two counts — Anserini's `fbDocs` / `fbTerms` defaults.
#: Constants, never keys: a second tunable beside `rm3_weight` would be a second
#: lever, and the frozen bar forbids sweeping one.
FB_DOCS = 10
FB_TERMS = 10


def _records_by_id(root: Path, ids: list[str]) -> dict[str, dict]:
    """The committed records for `ids`, reading each shard once."""
    from ..store import shard_for, shard_path
    from ..store.reader import read_shard

    wanted: dict[str, set[str]] = {}
    for doc_id in ids:
        wanted.setdefault(shard_for(doc_id), set()).add(doc_id)
    out: dict[str, dict] = {}
    for shard in sorted(wanted):
        path = shard_path(root, shard)
        if not path.is_file():
            continue
        _header, records = read_shard(path)
        for record in records:
            if record.get("id") in wanted[shard]:
                out[record["id"]] = record
    return out


def feedback_terms(
    root: Path,
    first_pass: list,
    query_hashes: list[str],
    scoring: Scoring = DEFAULT_SCORING,
) -> list[str]:
    """The `FB_TERMS` highest-RM1 term hashes of the top `FB_DOCS` results.

    `first_pass` is `rank()`'s output, best first; only `id` and `score` are
    read. Returns `[]` when there is nothing to feed back — no results, or
    scores that sum to zero — and `build()` then returns the identity.

    🔴 **Summed in a fixed order** — documents in rank order, terms in
    ascending hash order — because float addition is not associative, and the
    Node twin must reproduce the same bits to pick the same ten terms.
    """
    docs = [r for r in first_pass[:FB_DOCS] if r.score > 0]
    total = 0.0
    for r in docs:
        total += r.score
    if not docs or total <= 0:
        return []
    records = _records_by_id(root, [r.id for r in docs])
    exclude = set(query_hashes)
    weight: dict[str, float] = {}
    for r in docs:
        record = records.get(r.id)
        if record is None:
            continue
        wlen = derive_wlen(record.get("flen", []), scoring)
        if wlen <= 0:
            continue
        p_q = r.score / total
        terms = record.get("terms", {})
        for h in sorted(terms):
            if h in exclude:
                continue
            wtf = weighted_tf(terms[h], scoring)
            if wtf <= 0:
                continue
            weight[h] = weight.get(h, 0.0) + (wtf / wlen) * p_q
    ranked = sorted(weight.items(), key=lambda kv: (-kv[1], kv[0]))
    return [h for h, _ in ranked[:FB_TERMS]]
