"""Hybrid retrieval — the lexical lane fused with the dense lane by RRF.

**Default-off, and that is a measured position rather than caution.**

Fusing a second lane changes rankings by construction: it is a new capability,
not a faster route to the same answer, so the differential law cannot apply to
it. `ask` with no flags stays exactly the lexical answer that
`tools/differential/` proves byte-identical to the reference scan; `--hybrid`
opts into something else.

The archived engine shipped hybrid **enabled**, but only after an eval gate
ran on a real graded set (archived ADR-0006). This build has one available —
the fifty ranked goldens in the sibling `fux-playground`, whose
`known_failure` class 3 (`q008`, `q017`, `q030`, `q031`, `q036`) is *named* in
PLAN.md §M2 as the dense lane's target set. So the default is a measurement to
be taken and reported, not a preference to be exercised at build time; and
flipping it is Arpit's call on that evidence, exactly as the v0.26 line's
Option B was authorised default-off and gated on a separate sign-off.

Scores are RRF scores, not BM25F scores. They are not comparable across the
two modes and are not meant to be.
"""

from __future__ import annotations

from pathlib import Path

from ..errors import FuxError
from .fuse import RRF_K, rrf
from .rank import AskResult

__all__ = ["hybrid_ask", "DENSE_WIDTH"]

#: How deep the dense lane reaches before fusion. Wider costs a longer sort on
#: an already-linear scan and mostly adds documents RRF will rank last anyway.
DENSE_WIDTH = 100


def hybrid_ask(root: Path, query: str, top: int = 5, *, k: int = RRF_K) -> list[AskResult]:
    """Fuse the lexical ranking with the dense ranking. Returns RRF-scored hits."""
    from ..derive import accel
    from ..derive import format as derive_fmt

    if not (derive_fmt.runtime_dir(root) / derive_fmt.STATS_NAME).exists():
        raise FuxError("hybrid needs the derived accelerator - run `fux build` first")

    # Lexical lane: reach deeper than `top` so fusion has something to reorder.
    lexical = accel.ask(root, query, top=max(top * 10, DENSE_WIDTH))
    lexical_ids = [r.id for r in lexical]

    dense_ids = _dense_ids(root, query)

    rankings = [lexical_ids] if not dense_ids else [lexical_ids, dense_ids]
    fused = rrf(rankings, k=k)

    by_id = {r.id: r for r in lexical}
    runtime = accel.Runtime(root)
    docs_by_id = {d["id"]: d for d in runtime.docs}

    # Ties break on id, as everywhere else in this engine.
    ordered = sorted(fused.items(), key=lambda kv: (-kv[1], kv[0]))

    out: list[AskResult] = []
    for doc_id, score in ordered[:top]:
        hit = by_id.get(doc_id)
        if hit is not None:
            out.append(AskResult(id=hit.id, title=hit.title, loc=hit.loc, score=score))
            continue
        doc = docs_by_id.get(doc_id)
        if doc is not None:  # dense-only hit: no lexical overlap at all
            out.append(AskResult(id=doc["id"], title=doc["title"], loc=doc["loc"], score=score))
    return out


def _dense_ids(root: Path, query: str) -> list[str]:
    """The dense ranking as doc ids, or empty when the lane cannot run.

    Returns empty rather than raising when the *lane* is unavailable — no code
    table, or no bundled model to embed the query with. Hybrid then degrades to
    the lexical ranking, which is the honest behaviour for a lane that adds
    evidence rather than gating it.

    **The exception list is deliberately narrow.** A bare `except Exception`
    here would turn every real dense-lane bug into "hybrid quietly returns the
    lexical answer" — a silent degradation that looks like a working feature
    and is exactly the failure mode this engine keeps writing tests against.
    Anything that is not a missing model propagates.
    """
    from ..derive import accel, dense

    codes = dense.load_codes(root)
    if not codes:
        return []
    try:
        from ..embed import get_model, quantize

        vec = get_model().embed(query)
    except (FuxError, ImportError, FileNotFoundError):
        return []  # no bundled model in this install; lexical still answers
    if vec is None:
        return []  # nothing embeddable in the query itself

    query_code = int.from_bytes(quantize(vec), "little")
    runtime = accel.Runtime(root)
    docs = runtime.docs
    return [docs[i]["id"] for i in dense.hamming_ranking(query_code, codes, DENSE_WIDTH)]
