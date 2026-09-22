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

from dataclasses import dataclass
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
    #: The document is retired (SR-ARCHIVED-CONTENT decisions 1 and 3).
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
    #: W-153. The document's committed `mtime` — the git commit timestamp, in
    #: whole unix seconds — or `None` when the document is outside git history.
    #:
    #: 🔴 **`None` is a CLAIM, not an absence.** The key is on every hit, always,
    #: because an absent key cannot be told from an older fux (the W-48 trap);
    #: `None` says *this document carries no committed date*, which a corpus
    #: copied out of its repository produces for every one of its documents.
    #:
    #: **It exposes a fact and orders nothing.** `mtime` reaches the sort only
    #: through the declared tie-break, at an equal score. It was on every record
    #: and reachable by no caller until 2026-09-13, which is the gap closing
    #: `recency_half_life_days` opened (W-152) and W-153 named rather than left
    #: to be discovered.
    mtime: int | None = None
    #: W-162. A human filed `fux correct --pin` for **this exact question**, so
    #: this document was moved to #1 after ranking.
    #:
    #: 🔴 **It is NOT part of the sort key and NOT a score.** `rank()` never
    #: sees it: the pin is applied by `run_query` after the ranking is
    #: complete, so `--why`'s derivation still describes the ranking that
    #: actually ran and the reader can see the pin *on top of* it rather than
    #: baked into it. A pin that changed the score would make the ranking
    #: unreadable for exactly the query somebody had to intervene on.
    #:
    #: **`False` is a claim, not an absence** — the key is on every hit (W-48).
    pinned: bool = False
    #: W-161. The graph walk out of the lexical top-k reached this document, so
    #: the boosted tier's RRF used a PPR rank for it as well as a lexical one.
    #:
    #: 🔴 **It marks a row the WALK REACHED, not a row that moved.** A walked
    #: document that was already #1 is still the reason #1 is #1, and marking
    #: only movers would hide the tier's effect exactly where it agreed with
    #: the words — which is the case a reader most needs to be able to see,
    #: because it is the one that looks like nothing happened.
    #:
    #: **Like `pinned`, it is not part of the sort key and not a score.**
    #: `rank()` never sees it: the tier is applied by `run_query` after the
    #: lexical core is complete. What it explains is the one list fux prints
    #: whose second row may score higher than its first — see
    #: [`compose.py`](compose.py) for why that shape was chosen here and
    #: rejected for `-q` fusion.
    boosted: bool = False
    #: Where the boost came from, as a reader can check it:
    #: `#7 → #2 via graph`. `None` on every unboosted row, and `None` is an
    #: absence here rather than a claim — an unboosted row has no route because
    #: no walk reached it, which the `boosted` key already says.
    route: str | None = None


@dataclass(frozen=True)
class Corpus:
    """The statistics BM25F needs, derived per query and never stored.

    `n` counts every record line; `total_wlen` sums the `wlen` of the records
    that have one. A record without `flen` therefore contributes to the
    denominator and not the numerator — that is `scan.py`'s behaviour, and the
    accelerator's build asserts it reproduces the same statistics.

    **`total_wlen` is a float and is derived per query** (SR-TUNE, 2026-08-24).
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

    @property
    def avg_wlen(self) -> float:
        return self.total_wlen / self.n


def _record_is_archived(record: dict, archived_dirs: frozenset[str]) -> bool:
    """Is this document retired?

    **The record property wins** (SR-ARCHIVED-CONTENT decision 1): a record
    states the rule it was written under, which is the whole reason the property
    exists rather than being recomputed by every reader.

    **The declaration is the fallback**, for one specific and temporary case: an
    index committed before the property shipped carries no `archived` key, and
    re-ingesting the world is not a precondition for the marker being correct.
    Both inputs are *declarations* — the record's own, or the `archived=true`
    line in `.fux/sources/dirs` — so neither path ever derives currency from a
    path convention, which is what SR-DIR-LIST forbids.
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

    #: 🔴 **THE THREE DOCUMENT PRIORS ARE GONE, and `[priority]` is what is
    #: left.** `superseded_weight` went on 2026-09-13 (W-151), `archived_weight`
    #: and `recency_half_life_days` the same day (W-152) — Arpit's rulings on
    #: [VERDICT-W143], which measured that no single global value clears the bar
    #: for any of them. Each shipped as a no-op, so nothing ranks differently.
    #:
    #: **The FACTS survive and are read elsewhere in this file** — `archived` is
    #: computed for every candidate and reaches the marker and the hit,
    #: `superseded` and `mtime` break a tie. A fact is not a weight, and this
    #: class is now only about weights.
    #:
    #: `archived_dirs` stays because `_record_is_archived` is the FACT's
    #: fallback for an index built before the record property shipped — it has
    #: not scaled a score since 2026-09-13.
    archived_dirs: frozenset[str] = frozenset()
    #: `.fux/tune.toml`'s `[priority]` (SR-TUNE decision 8), **sorted
    #: longest-key-first** by the loader so `priority_for` can stop at the
    #: first match. Empty is the default and costs nothing.
    priority: tuple[tuple[str, float], ...] = ()

    def priority_for(self, loc: str) -> float:
        """The per-source multiplier for a document location; unlisted is `1.0`.

        **Longest matching entry wins** (SR-TUNE decision 8a). Elasticsearch
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
        scores and orders **byte-identically** (SR-ARCHIVED-CONTENT decision
        2's veto) and the differential evidence gathered at the default still
        stands unmodified.

        ⚠ **Since 2026-09-13 this is true of every corpus that configures no
        `[priority]`** — the three document priors that could also make it false
        were removed. That is not a reason to delete the short-circuit: the
        property it guards is the one the accelerator's bound rests on, and
        `[priority]` can still make it false.
        """
        return not self.priority

    @property
    def maximum(self) -> float:
        """`sup_d w(d)` over every document the configuration can produce.

        `1.0` is always attainable — an unlisted document is never scaled — so
        the supremum is `max(1.0, ...)` and never the configured weight alone.
        Taking the configured weight alone would make the ceiling too small for
        `w < 1`, which is the demotion direction and the one that looks safe.

        ⚠ **It was a PRODUCT of independent suprema until 2026-09-13**, when
        `archived_weight` joined `superseded_weight` in being removed. One
        multiplier is left, so the product has one factor. **Restore the product
        the moment a second one arrives** — a document can carry two independent
        weights and be scaled twice, and taking the larger under-estimates the
        ceiling, which is the W-73 defect's exact shape.
        """
        return max([1.0, *(w for _, w in self.priority)])

    def of(self, record: dict) -> float:
        """The multiplier for one record: per-source priority, and nothing else."""
        if self.trivial:
            return 1.0
        return self.priority_for(record.get("loc", ""))


def rank(
    candidates: list[dict],
    query_hashes: list[str],
    df: dict[str, int],
    corpus: Corpus,
    top: int,
    *,
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

    `archived_dirs` is the FACT's fallback, for an index built before the
    `archived` record property shipped. 🔴 **It is no longer a demotion:**
    SR-ARCHIVED-CONTENT decision 6's `archived_weight` was REMOVED on 2026-09-13
    (W-152, SR-TUNE decision 15), so being retired can no longer move a score at
    all. What decision 2's veto asserted — that the marker does not move the
    ranking — is now structural rather than a consequence of a default
    (`tests/query/test_scan.py::test_the_marker_does_not_move_the_ranking`).

    **Every result still carries `archived`** (decision 3). The flag is computed
    for all candidates, never enters the sort key, and is what the marker, the
    response note and the JSON hit read. Telling a reader a document is retired
    and reordering because it is retired were two different decisions; only the
    first one survives.

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
    (SR-CONFIDENCE decision 2). **It is an out-parameter rather than a second
    return value on purpose:** every existing caller of `rank()` is unchanged,
    the differential law's two paths keep one shared signature, and the dict is
    owned by the caller rather than by this module, which matters now that
    fux runs threads. **Nothing read back out of it can reach a score or an
    ordering** — it is written after the sort and never consulted.
    """
    if stats_out is not None:
        stats_out["df"] = dict(df)
        stats_out["n"] = corpus.n
        # W-210 — the two remaining inputs of the BM25F summand, so that
        # `--why` can attribute a score per term with the SAME expression that
        # produced it (`bm25f.term_contribution`) instead of a second copy.
        # `corpus.avg_wlen` is a property and `scoring` is a frozen dataclass;
        # both are written after the sort, like everything else here, and
        # nothing read back out of this dict reaches a score or an ordering.
        stats_out["avg_wlen"] = corpus.avg_wlen
        stats_out["scoring"] = scoring
    if corpus.n == 0:
        return []
    if expansion is None:
        from .expand import Expansion

        expansion = Expansion.none(query_hashes)
    term_weights = expansion.weights or None
    avg_wlen = corpus.avg_wlen
    if weighting is None:
        weighting = Weighting(archived_dirs=archived_dirs)
    demote = not weighting.trivial

    # 🔴 **W-168 step 1 — the anchor fold lands HERE, once, for both paths.**
    #
    # Each candidate generator attaches two keys to the record dicts it hands
    # over: `atf` (this document's anchor term counts, restricted to the
    # query's hashes) and `alen` (its anchor token total). The scan folds them
    # out of the `at` maps on the committed edges of the documents that link
    # here; `derive/accel.py` reads the same numbers out of the anchor plane it
    # built from those same bytes.
    #
    # **The fold is one line, in the one function both paths reach**, which is
    # what makes it checkable: [`accel.py`](../derive/accel.py) states the
    # contract as *"the accelerator generates candidates and statistics, never
    # scores"*, so a fold written into the accelerator alone would ship
    # `--fast`/`--scan` drift — data-dependent, silent, and visible only on the
    # documents somebody linked to.
    #
    # `None` when the anchor field is off, and `None` performs no arithmetic:
    # see `score_record`.
    anchor_on = scoring.anchor_on

    scored = []
    for record in candidates:
        terms = record.get("terms", {})
        anchor_tf = record.get("atf") if anchor_on else None
        # 🔴 The hallucinated-citation guard, before anything is scored.
        if not expansion.matches(terms, anchor_tf):
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
            anchor_tf,
            record.get("alen", 0) if anchor_on else 0,
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
    # 🔴 **NONE of these is a weight, and after 2026-09-13 none of them can be
    # one.** `superseded_weight` (W-151), `archived_weight` and
    # `recency_half_life_days` (W-152) were all REMOVED, so `superseded` and
    # `mtime` reach ranking **here and nowhere else**. What the key reads is the
    # *facts* — and only where the rounded scores are equal. A corpus with no
    # ties orders exactly as it did before.
    #
    # **W-94's "doing nothing is legitimate" is untouched, and is now the whole
    # story.** That decision asked whether these should move off their no-op
    # defaults and change SCORES; the answer was that no global value is
    # correct, so the knobs went. This changes no score, and it cannot promote
    # or demote a document past one that outscores it.
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

    # SR-CONFIDENCE: which of the query's terms the TOP-RANKED document itself
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
            # Both candidate paths carry `mtime` on the record dict — the scan
            # reads it off the line, `derive/_build.py` copies it into the doc
            # table — so reading it here is under the differential law like
            # every other field, rather than being a second read on one path.
            mtime=record.get("mtime"),
        )
        for i, (record, s, archived) in enumerate(scored[:top])
    ]
