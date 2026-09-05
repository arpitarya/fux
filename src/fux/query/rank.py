"""The single scorer and the single sort — shared by both candidate generators.

**This module is why the differential law is achievable.** Floating-point
addition is not associative, so a term-major accelerator that accumulated each
document's score term-by-term would produce different low-order bits than the
doc-major scan, and `--json` output would differ even though nothing was
logically wrong. The fix is structural rather than careful: the accelerator
generates *candidates and statistics*, never scores. Both paths call `rank()`,
which sums each document's contributions in query-hash order exactly once.

The differential law then reduces to a claim that can actually be tested:
**the candidate set and the corpus statistics are identical.** Everything
downstream is one code path.

See `work/adr/0005_derived-accelerator.md`.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from .. import store as store_mod
from ..ingest.gitdir import is_archived_loc
from .bm25f import DEFAULT_SCORING, Scoring, score_record

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .expand import Expansion


@dataclass(frozen=True)
class AskResult:
    id: str
    title: str
    loc: str
    score: float
    #: The document is retired (ADR-ARCHIVED-CONTENT decisions 1 and 3).
    #: **Never part of the sort key** — decision 2 fixes the order as
    #: byte-identical at the default weight, and this field is what a reader is
    #: told, not what the scorer computes.
    archived: bool = False
    #: W-111. This result's rounded score equals another candidate's, so its
    #: position was decided by the declared tie-break rather than by the
    #: ranking. **Computed over the FULL sorted list, before truncation**, so a
    #: result tied with the document just below the cut is still marked — a
    #: caller reading `--top 5` is told the fifth row was a coin-toss even
    #: though the coin's other side is not on the page.
    tie: bool = False


@dataclass(frozen=True)
class Corpus:
    """The statistics BM25F needs, derived per query and never stored.

    `n` counts every record line; `total_wlen` sums the `wlen` of the records
    that have one. A record without `flen` therefore contributes to the
    denominator and not the numerator — that is `scan.py`'s behaviour, and the
    accelerator's build asserts it reproduces the same statistics.

    **`total_wlen` is a float and is derived per query** (ADR-TUNE, 2026-08-24).
    It used to be an integer summed at build time with the field weights baked
    in, which meant a `tune.toml` field weight moved `avg_wlen` on the scan
    path and not on the accelerator path — the two disagreeing on the same
    corpus, which is a differential-law break, and it would have needed a
    rebuild to fix. The runtime stats plane now stores `total_flen`, the five
    raw per-field token-count totals, and both paths weight them at query time.
    Decision 6a one level up: *no stored value may be a function of a tunable*.
    """

    n: int
    total_wlen: float
    #: The newest commit timestamp in the corpus (W-76 Phase 2), or 0 when no
    #: record carries one. Recency is normalised against it so the freshest
    #: document scores 1.0 and the prior is a pure demotion -- which is what
    #: keeps `Weighting.maximum` finite and the block bound usable.
    newest_mtime: int = 0

    @property
    def avg_wlen(self) -> float:
        return self.total_wlen / self.n


def _record_is_archived(record: dict, archived_dirs: frozenset[str]) -> bool:
    """Is this document retired?

    **The record property wins** (ADR-ARCHIVED-CONTENT decision 1): a record
    states the rule it was written under, which is the whole reason the property
    exists rather than being recomputed by every reader.

    **The declaration is the fallback**, for one specific and temporary case: an
    index committed before the property shipped carries no `archived` key, and
    re-ingesting the world is not a precondition for the marker being correct.
    Both inputs are *declarations* — the record's own, or the `archived=true`
    line in `.fux/sources/dirs` — so neither path ever derives currency from a
    path convention, which is what ADR-DIR-LIST forbids.
    """
    if record.get("archived"):
        return True
    return bool(archived_dirs) and is_archived_loc(record["loc"], archived_dirs)


@dataclass(frozen=True)
class Weighting:
    """The score multiplier policy, in ONE place, for both candidate paths.

    **This type exists because of W-73.** The weight used to be applied only
    inside `rank()`, *after* the accelerator had already truncated the
    candidate set on an **unweighted** bound and an **unweighted** `theta`. At
    any weight but `1.0` the two paths could then return different documents —
    silently, data-dependently, with no exception and no short read.

    The bound is safe on exactly one property::

        for every unseen d:   w(d) * S(d)  <  theta_w

    `S(d)` is bounded above by the block ceiling and `w(d)` by `maximum`, so
    scaling the ceiling by `maximum` and drawing `theta_w` from **weighted**
    candidate scores restores it. Both halves are required: scaling alone
    leaves `theta` too high when weights demote the current top-k, and a
    weighted `theta` alone leaves the ceiling too low when weights promote.

    `maximum` is the supremum over the **configuration**, never over the
    observed candidates: an unseen document may carry a weight that no
    candidate does, which is precisely the case the bound has to survive.
    """

    archived_weight: float = 1.0
    archived_dirs: frozenset[str] = frozenset()
    #: W-76 Phase 2. Both default to no-ops, so a corpus that configures
    #: nothing scores byte-identically to before they existed.
    superseded_weight: float = 1.0
    recency_half_life_days: float = 0.0
    #: The newest commit timestamp in the corpus, used to normalise recency so
    #: the freshest document scores `1.0`. Zero disables the prior.
    newest_mtime: int = 0
    #: `.fux/tune.toml`'s `[priority]` (ADR-TUNE decision 8), **sorted
    #: longest-key-first** by the loader so `priority_for` can stop at the
    #: first match. Empty is the default and costs nothing.
    priority: tuple[tuple[str, float], ...] = ()

    def priority_for(self, loc: str) -> float:
        """The per-source multiplier for a document location; unlisted is `1.0`.

        **Longest matching entry wins** (ADR-TUNE decision 8a). Elasticsearch
        resolves the same overlap with first-match on an ordered array; fux
        cannot copy that, and the reason is a property worth being pleased
        about — its source lists are loader-sorted and file order is
        presentation only, so there is no first. Longest-match is
        order-independent, which is what L3 needs. Ties cannot occur because
        TOML keys are unique.

        **This is the only implementation.** `tune.Tune` carries the data and
        deliberately does not resolve it: the rule has to live next to the
        bound that must agree with it, or the two drift and `--fast` and
        `--scan` disagree — the W-73 class, on a different multiplier.
        """
        if not self.priority:
            return 1.0
        for entry, weight in self.priority:
            if loc == entry or loc.startswith(entry):
                return weight
        return 1.0

    @property
    def trivial(self) -> bool:
        """No document can be scaled — the whole weighting is a no-op.

        When this holds every weighted path short-circuits to the arithmetic
        that shipped before W-73, so a corpus with no configured weight still
        scores and orders **byte-identically** (ADR-ARCHIVED-CONTENT decision
        2's veto) and the differential evidence gathered at the default still
        stands unmodified.
        """
        return (
            self.archived_weight == 1.0
            and self.superseded_weight == 1.0
            and self.recency_half_life_days <= 0
            and not self.priority
        )

    @property
    def maximum(self) -> float:
        """`sup_d w(d)` over every document the configuration can produce.

        `1.0` is always attainable — a document that is not archived is never
        scaled — so the supremum is `max(1.0, archived_weight)` and never the
        configured weight alone. Taking the configured weight alone would make
        the ceiling too small for `w < 1`, which is the demotion direction and
        the one that looks safe.
        """
        #: `archived` and `superseded` are INDEPENDENT flags, so a document can
        #: carry both and be scaled twice. The supremum is therefore the
        #: product of the per-flag suprema, not the larger of the two.
        #:
        #: Recency contributes exactly `1.0`: `recency_multiplier` is bounded
        #: to `(0, 1]` by construction, so it can only ever demote. That bound
        #: is load-bearing here — an unbounded recency prior would make this
        #: supremum unbounded and the block bound useless.
        #: Per-source priority is a third independent multiplier, so it joins
        #: the product. `max(1.0, ...)` again rather than the raw maximum: an
        #: unlisted document is scaled by `1.0`, so `1.0` is always attainable
        #: and a configuration of demotions must not lower the ceiling.
        return (
            max(1.0, self.archived_weight)
            * max(1.0, self.superseded_weight)
            * max([1.0, *(w for _, w in self.priority)])
        )

    def of(self, record: dict) -> float:
        """The multiplier for one record: archived x superseded x recency."""
        if self.trivial:
            return 1.0
        weight = 1.0
        if self.archived_weight != 1.0 and _record_is_archived(record, self.archived_dirs):
            weight *= self.archived_weight
        if self.superseded_weight != 1.0 and record.get("superseded"):
            weight *= self.superseded_weight
        if self.recency_half_life_days > 0:
            from ..ingest.priors import recency_multiplier

            weight *= recency_multiplier(
                record.get("mtime"), self.newest_mtime, self.recency_half_life_days
            )
        if self.priority:
            weight *= self.priority_for(record.get("loc", ""))
        return weight


def rank(
    candidates: list[dict],
    query_hashes: list[str],
    df: dict[str, int],
    corpus: Corpus,
    top: int,
    *,
    archived_weight: float = 1.0,
    archived_dirs: frozenset[str] = frozenset(),
    weighting: "Weighting | None" = None,
    scoring: Scoring = DEFAULT_SCORING,
    stats_out: dict | None = None,
    expansion: "Expansion | None" = None,
) -> list[AskResult]:
    """Score, sort, truncate. The only place any of the three happens.

    A candidate is any record whose raw line matched at least one query term;
    scoring can still return 0 (a matched hash with zero weighted tf), and those
    are dropped rather than ranked — `ask` says "no confident matches" instead
    of listing a document it scored at zero.

    `archived_weight`/`archived_dirs` are ADR-ARCHIVED-CONTENT decision 6's demotion:
    a document declared archived has its score multiplied by the weight. **At the
    shipped default (`1.0`) the multiply is skipped outright**, so a corpus with
    no configured weight scores and orders byte-identically — ADR-ARCHIVED-CONTENT
    decision 2's veto, held, and asserted by
    `tests/query/test_scan.py::test_the_marker_does_not_move_the_ranking`.

    **Every result carries `archived` regardless of the weight** (decision 3).
    The flag is computed for all candidates, never enters the sort key, and is
    what the marker and the disclaimer read. Telling a reader a document is
    retired and reordering because it is retired are two different decisions,
    and only the second one is configurable.

    ## `expansion` — W-109, and the guard that lives here and nowhere else

    🔴 **A candidate matching none of the ORIGINAL query's terms is dropped,
    whatever it scored.** With `--expand` the caller hands fux words it thinks
    the document uses; a document that matches only those is an answer to a
    question **nobody asked**, assembled from words a model invented, and
    returning it with a fresh `sha` beside it is a hallucinated citation with
    provenance attached.

    **It is enforced here rather than in display, and that is the decision.**
    `rank()` is the only place scoring, sorting and truncating happen and the
    one function **both candidate paths reach** — a filter in `cmd_ask` would
    be absent from `fux_search` over MCP, and a filter in the printer would be
    absent from `--json`. The drop runs **before the score is kept**, so an
    expansion-only document never reaches a sort key, a receipt or a budget.

    `None` means no expansion: `Expansion.none` is built from `query_hashes`,
    every hash is required, the test is vacuous and no multiply is performed.

    `stats_out`, when a caller supplies a dict, receives the two corpus
    statistics only this function holds — `df` and `n` — for
    [`confidence.py`](confidence.py) to build its block from
    (ADR-CONFIDENCE decision 2). **It is an out-parameter rather than a second
    return value on purpose:** every existing caller of `rank()` is unchanged,
    the differential law's two paths keep one shared signature, and the dict is
    owned by the caller rather than by this module, which matters now that
    fux runs threads. **Nothing read back out of it can reach a score or an
    ordering** — it is written after the sort and never consulted.
    """
    if stats_out is not None:
        stats_out["df"] = dict(df)
        stats_out["n"] = corpus.n
    if corpus.n == 0:
        return []
    if expansion is None:
        from .expand import Expansion

        expansion = Expansion.none(query_hashes)
    term_weights = expansion.weights or None
    avg_wlen = corpus.avg_wlen
    if weighting is None:
        weighting = Weighting(archived_weight=archived_weight, archived_dirs=archived_dirs)
    # Recency needs the corpus it is being normalised against, and the corpus
    # is only known here. `replace` rather than mutation: `Weighting` is frozen
    # so that a caller can never hand two code paths a policy that drifted.
    if weighting.recency_half_life_days > 0 and corpus.newest_mtime:
        weighting = replace(weighting, newest_mtime=corpus.newest_mtime)
    demote = not weighting.trivial

    scored = []
    for record in candidates:
        terms = record.get("terms", {})
        # 🔴 The hallucinated-citation guard, before anything is scored.
        if not expansion.matches(terms):
            continue
        s = score_record(
            terms,
            record.get("flen", []),
            query_hashes,
            df,
            corpus.n,
            avg_wlen,
            scoring,
            term_weights,
        )
        archived = _record_is_archived(record, weighting.archived_dirs)
        if demote:
            s *= weighting.of(record)
        if s > 0:
            scored.append((record, s, archived))

    # W-111 — the DECLARED tie-break, in Arpit's ratified order:
    #
    #     superseded -> recency -> priority -> id
    #
    # ## Why this is not "add three ranking priors"
    #
    # 🔴 **Every one of these is already a `Weighting` multiplier, and every one
    # of them ships as a NO-OP** (`superseded_weight = 1.0`,
    # `recency_half_life_days = 0.0`, empty `[priority]`). This key does not
    # turn any of them on: it reads the same *facts* those weights read, and it
    # reads them **only where the rounded scores are equal**. A corpus with no
    # ties orders exactly as it did before.
    #
    # **W-94's "doing nothing is legitimate" is untouched.** That decision is
    # about whether `superseded_weight` should move off `1.0` and change
    # SCORES. This changes no score, and it cannot promote or demote a document
    # past one that outscores it.
    #
    # ## What it replaces, and why the old answer was worse
    #
    # `id` alone. 4.38 % of top-5 orderings were decided by nothing but a
    # document's name — *"the same arbitrary answer everywhere"*, which is
    # reproducible and meaningless. Determinism was never the problem; a
    # **stated** answer is strictly better than an arbitrary one at the same
    # cost, and `id` stays as the final, total tie-break so the order is still
    # total and still machine-independent.
    #
    # Ascending on `superseded` (False < True) puts a live document above a
    # retired one; negated on recency and priority because higher is better.
    # `mtime` missing reads as `0` — the oldest — which is what an undated
    # document is.
    scored.sort(
        key=lambda pair: (
            -round(pair[1], 9),
            bool(pair[0].get("superseded", False)),
            -int(pair[0].get("mtime") or 0),
            -weighting.priority_for(pair[0].get("loc", "")),
            pair[0]["id"],
        )
    )
    # Marked AFTER the sort and over the WHOLE list: a neighbour comparison on
    # the truncated window would silently un-mark the last row, which is the
    # one most likely to have been decided by a coin-toss.
    tied: set[int] = set()
    for i in range(len(scored) - 1):
        if round(scored[i][1], 9) == round(scored[i + 1][1], 9):
            tied.add(i)
            tied.add(i + 1)

    # ADR-CONFIDENCE: which of the query's terms the TOP-RANKED document itself
    # contains. Handed out through the same seam as `df`/`n` and for the same
    # reason — **both paths reach this function with the same record dicts**
    # (`derive/accel.py`'s contract is *"the scan's contract"*), so a signal
    # derived here is identical on the accelerator and the scan, and the
    # differential law is untouched. Deriving it anywhere else would mean
    # re-reading the index on one path and not the other.
    if stats_out is not None and scored:
        top_terms = scored[0][0].get("terms", {})
        stats_out["top_doc_hashes"] = [h for h in query_hashes if h in top_terms]

    return [
        AskResult(
            id=record["id"],
            title=store_mod.display_title(record),
            loc=record["loc"],
            score=s,
            archived=archived,
            tie=i in tied,
        )
        for i, (record, s, archived) in enumerate(scored[:top])
    ]
