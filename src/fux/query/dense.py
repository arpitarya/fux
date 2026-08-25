"""The dense lane, over committed per-chunk vectors. W-76 Phase 7.

Three stages, cheapest first:

    Hamming prefilter (derived sign codes)  ->  int8 rescore  ->  max-sim per doc

The prefilter is the same 256-bit scan the removed `code` field used to *be*.
It is now the fast first pass over real data rather than the answer, and it
lives in the derived plane because it is a cache of a sign test on committed
bytes — deleting it costs speed and nothing else.

## The default is OFF, and that is a measurement rather than a preference

The old document-level lane fixed 3 graded queries and **broke 9**, which is
why `--hybrid` shipped off. The per-chunk unit is what should fix that — a
12 KB document with ten sections averaged into one point sits near none of
them — but *should* is not a number, and W-76's Phase 7 gate says so
explicitly:

> RUN 2026-08-24, and it FAILED: **0 fixed / 2 broken**, at every setting that
> fires. `[dense] mode` stays `off`.
> [DENSE-CHUNK](../../../work/regression/2026-08-24-dense-lane-gate/VERDICT.md).
>
> **The cause is this module's input, not this module.** `embed/model.py`
> mean-pools static token vectors -- no layers, no attention -- so the dense
> lane is as order-blind as BM25F, and `always` mode breaks the one
> current-vs-superseded query a semantic lane was most expected to rescue. The
> committed vectors stay: they cost nothing while `mode = off`, and a better
> pooling reuses them unchanged.
>
> the 3-fixed/9-broken result must become **>= 3-fixed / 0-broken**

Until that runs on the 50 goldens, `[dense] mode` defaults to `off` and the
committed vectors sit there unused. That is the honest state: the data is in
the index, the fusion is not switched on, and the switch is a measurement away.

## Gating, when it is on

`gated` fuses only when the **lexical lane is weak** — too few candidates, or a
top score below a configured floor. A strong lexical match is not improved by a
second opinion; it is only put at risk by one. This is the same principle the
derived plane and enrichment both follow: **a generated signal may rescue a
query, never demote a document that already answered it.**
"""

from __future__ import annotations

from pathlib import Path

#: Below this many lexical results, the lexical lane is weak by definition —
#: there is nothing for a strong match to be strong *against*.
MIN_LEXICAL_RESULTS = 3


def query_vector(query: str):
    """The query's own int8 components, or `None` with no model bundle."""
    from ..embed import get_model

    model = get_model()
    if model is None:
        return None
    vec = model.embed(query)
    return tuple(vec.q) if vec is not None else None


def should_fuse(mode: str, results, threshold: float) -> bool:
    """The gate. `off` never fuses; `always` always does; `gated` decides.

    Deliberately reads only the lexical results — the gate must be decidable
    **before** any dense work happens, or the cost it exists to avoid has
    already been paid.
    """
    if mode == "off":
        return False
    if mode == "always":
        return True
    if len(results) < MIN_LEXICAL_RESULTS:
        return True
    return results[0].score < threshold


#: How many documents the Hamming prefilter hands to the exact rescore.
#: doc 03 says "k x 8"; this is that, floored so a small `top` still gets a
#: candidate pool worth rescoring.
RESCORE_FACTOR = 8
MIN_RESCORE = 40


def dense_scores(root: Path, query: str, top: int, extra: set[str] | None = None) -> dict[str, float]:
    """`{doc_id: best chunk similarity}` — a CORPUS-WIDE pass, not a re-rank.

    **This retrieves; it does not merely reorder.** An earlier draft scoped it
    to the lexical candidates, which quietly made the whole lane useless in the
    one case the gate exists for: when lexical returns too few results there is
    nothing to re-rank, and a dense lane that can only reorder cannot rescue a
    query it found nothing for.

    Three stages, cheapest first:

        Hamming prefilter (derived codes)  ->  int8 rescore  ->  max-sim per doc

    The prefilter is a popcount per chunk; the rescore is 256 multiply-adds per
    chunk. Running the second over a whole corpus is what the first exists to
    prevent -- at 10 000 documents and ~9.8 chunks each that is ~25 M
    multiply-adds per query in pure Python.

    Falls back to scoring `extra` alone when no derived table exists: a fresh
    clone has committed vectors and no accelerator, and answering from what
    lexical found beats refusing.
    """
    from .. import store as store_mod
    from ..derive import dense as derive_dense
    from ..embed import chunkvec, chunkvec as cv

    components = query_vector(query)
    if components is None:
        return {}

    records = store_mod.read_index(root)
    codes = derive_dense.load_codes(root)
    wanted: set[str] | None = None

    if codes:
        # The doc table's order IS the code table's order, by construction in
        # `derive/build.py` (`records.sort(key=id)`), so a docidx maps back
        # through the same sort here rather than through a stored id list.
        ordered_ids = sorted(records)
        query_code = int.from_bytes(cv.sign_code(components), "little")
        limit = max(MIN_RESCORE, top * RESCORE_FACTOR)
        near = derive_dense.nearest_docs(query_code, codes, limit)
        wanted = {ordered_ids[i] for i in near if i < len(ordered_ids)}
        if extra:
            wanted |= extra
    elif extra:
        wanted = set(extra)

    out: dict[str, float] = {}
    for doc_id, record in records.items():
        if wanted is not None and doc_id not in wanted:
            continue
        vectors = record.get("vectors") or ()
        if vectors:
            out[doc_id] = chunkvec.max_sim(components, vectors)
    return out


def merge(results, dense: dict[str, float], weight: float, top: int, records: dict):
    """Boost what lexical found, and ADMIT what only the dense lane found.

    A document lexical missed entirely enters with a score derived from its
    similarity alone. It is scaled by `weight` so it competes on the fusion's
    terms rather than on a scale of its own, and it can only ever be admitted
    below a document the lexical lane actually scored -- which keeps the
    principle every gate in this system follows: **a generated signal may
    rescue a query, never demote a document that already answered it.**
    """
    boosted = list(fuse(results, dense, weight))
    if not weight:
        return boosted
    known = {r.id for r in boosted}
    floor = min((r.score for r in boosted), default=0.0)
    from .rank import AskResult
    from .. import store as store_mod

    admitted = []
    for doc_id, similarity in dense.items():
        if doc_id in known or similarity <= 0:
            continue
        record = records.get(doc_id)
        if record is None:
            continue
        admitted.append(
            AskResult(
                id=doc_id,
                title=store_mod.display_title(record),
                loc=record["loc"],
                # Strictly below the weakest lexical hit: dense rescues, it
                # does not outrank a real term match.
                score=floor * 0.999 * similarity if floor else similarity * weight,
                archived=bool(record.get("archived", False)),
            )
        )
    admitted.sort(key=lambda r: (-round(r.score, 9), r.id))
    return (boosted + admitted)[:top]


def fuse(results, dense: dict[str, float], weight: float):
    """Blend a dense similarity into an existing lexical ranking.

    **A booster, not a replacement.** The dense score multiplies into a bounded
    uplift rather than being summed with a BM25F score — the two are on
    unrelated scales, and adding them would let a cosine of 0.4 outweigh a term
    match on a corpus where BM25F happens to score low.

    `weight` is the maximum fraction a perfect dense match may add. At the
    shipped default of `0.0` this returns the input untouched, which is what
    keeps the whole lane inert until it is measured.
    """
    if not dense or weight <= 0:
        return results
    import dataclasses

    boosted = [
        dataclasses.replace(r, score=r.score * (1.0 + weight * dense.get(r.id, 0.0)))
        for r in results
    ]
    boosted.sort(key=lambda r: (-round(r.score, 9), r.id))
    return boosted
