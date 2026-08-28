"""How much the index believes its own answer — four signals and one band.

Fux is read by agents, and an agent handed a ranked list has no way to tell
*"these three documents answer your question"* from *"these three documents are
the closest thing in a corpus that does not discuss this at all"*. Both look
identical: a score, a title, a citation. The second one is where an agent
invents an answer and cites a real file while doing it.

This module makes the difference machine-readable.

## The four signals, and why each is computable at all

Every one of them is a **pure function of what ranking already produced** — the
query's term hashes, the `df` and corpus statistics BM25F needed anyway, the
scored result list, and (on `answer` only) the refer plane's freshness verdict.
Nothing here fetches, samples, calls a model, or reads a clock, so L1, L3 and
L4 are untouched — see [ADR-LAWS](../../../docs/adr/0001_laws.md).

| signal | what it answers | shape |
|---|---|---|
| `coverage` | did the corpus contain the words you asked about? | `0.0`–`1.0` |
| `separation` | can the ranking tell first place from second? | `0.0`–`1.0` |
| `support` | how many documents came back at all | `int` |
| `verified` | were the cited bytes still what the index recorded? | four-state |

`missing` carries the surface form of every query term the corpus does not
contain. **It is the field an agent should read first** — it is the difference
between hedging vaguely and saying *"nothing here mentions `mTLS`"*.

## The two floors are the only numbers here, and both are now tunable

`separation_floor` and `doc_coverage_floor` are the *only* values in this
module that are not structural facts, and since 2026-08-28 a repo may set both
in `.fux/tune.toml` under `[confidence]` — ADR-CONFIDENCE decision 13, which
**reverses decision 7.**

⚠ **Read what that gave up.** Decision 7 refused the knob because a consumer
who lowers the floor until their answers read `grounded` is tuning away the
*signal* rather than the ranking, and nothing mechanical catches that. Two
things replace the prohibition, and neither is as strong as it was:

1. **The effective floor is PUBLISHED in the block** (`as_dict`), so a
   `grounded` computed under a slack floor is visible rather than implied. A
   consumer comparing two repos' answers can see they were not judged alike.
2. **`fux ask --no-tune` recomputes the band at the engine defaults**, which is
   the *"is it me or the config?"* switch ADR-TUNE decision 11 already owned.

**Neither floor can reach a score or an ordering** — see *What this can never
do*. A tuned floor moves the BAND and nothing else, so `[confidence]` satisfies
ADR-TUNE decision 1's boundary rule trivially: `.fux/index/` stays
byte-identical, and `tests/test_tune_boundary.py` asserts it over both keys.

## Coverage is idf-weighted, and that is the whole point

A query term the corpus has never seen has `df == 0`, which
[`bm25f.idf`](bm25f.py) scores as the **rarest possible** term. So weighting by
idf means a missed rare word costs far more than a missed common one — which is
correct, because the rare word is what made the question specific. Missing
`the` is nothing; missing `mTLS` is the question.

## Three of the four band boundaries are facts, not thresholds

That distinction is load-bearing, because a threshold nobody measured is an
invented number wearing a decimal point.

- **`none`** — nothing scored above zero. A fact.
- **`partial`** — a query term matched no document anywhere in the corpus, or
  the cited bytes have changed since ingest. Facts.
- **`grounded` vs `weak`** — needs a real cutoff on `separation`, and
  `SEPARATION_FLOOR` is **provisional and unmeasured**. It is registered as
  prediction **R10** and must not be cited as calibrated until that verdict is
  filed.

## What this can never do

**It cannot reach a score or an ordering.** The band is computed from `rank()`'s
output and handed to the caller; nothing downstream feeds back. That keeps the
differential law (`tools/differential/`) exactly as strong as it was — and it is
also why `support` is *not* a corpus-wide count. See `signals`.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .bm25f import idf

__all__ = [
    "BANDS",
    "Confidence",
    "DOC_COVERAGE_FLOOR",
    "GROUNDED",
    "NONE",
    "PARTIAL",
    "SEPARATION_FLOOR",
    "WEAK",
    "signals",
]

#: Every signal is clear: use the result and cite it.
GROUNDED = "grounded"

#: Usable, but something is knowably absent — a query term the corpus does not
#: contain, or bytes that have changed since they were indexed. The consumer is
#: expected to say which, and `missing` is what it says.
PARTIAL = "partial"

#: Everything matched, and the ranking still cannot separate first place from
#: second. Do not answer from this; report what was searched.
WEAK = "weak"

#: Nothing scored. `answerable` is `False` and no consumer should proceed.
NONE = "none"

#: Best first. Order is meaningful — a consumer may compare positions.
BANDS = (GROUNDED, PARTIAL, WEAK, NONE)

#: ⚠ **PROVISIONAL AND UNMEASURED — registered as R10.**
#:
#: The top result must beat the runner-up by this fraction of its own score for
#: the band to be `grounded`. `0.10` is a defensible starting point and nothing
#: more: it is not a measured optimum, no verdict backs it, and it is the only
#: number in this module that is not a structural fact.
#:
#: **This is the ENGINE DEFAULT.** ⚠ It was deliberately *not* a `tune.toml`
#: key until 2026-08-28; **`[confidence] separation_floor` now overrides it**
#: (ADR-CONFIDENCE decision 13, reversing decision 7).
#:
#: ⚠ **The cost decision 7 was buying, stated rather than clamped:** a consumer
#: can lower this until their answers read `grounded`, tuning away the signal
#: rather than the ranking, and no check catches it. What replaces the
#: prohibition is **publication** — `as_dict` emits the floor the band was
#: judged under — and `--no-tune`, which recomputes at this value.
#:
#: **Setting it does not settle R10.** The measurement is still owed, and a
#: repo-local number is a local preference, never a calibration.
SEPARATION_FLOOR = 0.10

#: How much of the question the TOP-RANKED document must itself contain before
#: the band may read `grounded`.
#:
#: 🔴 **`0.0` — THE CLAUSE IS OFF, AND THAT IS A MEASURED RESULT, NOT AN
#: OVERSIGHT.** `doc_coverage` is computed and published; it does not gate the
#: band, because on the only data that exists **it does not separate**:
#:
#: | | n | min | median | max |
#: |---|---:|---:|---:|---:|
#: | real goldens reaching this clause | 37 | **0.401** | 0.882 | 1.000 |
#: | decoys reaching it | 1 | **0.710** | — | 0.710 |
#:
#: The decoy sits **inside** the goldens' range, so any floor that catches it
#: demotes real answers below it. A floor of `1.0` turns **19 of 50** correct
#: answers `partial`; picking a number in a "gap" is impossible because there is
#: no gap, and picking one anyway would be fitting a threshold to 65 queries —
#: the failure R10 is currently INCONCLUSIVE over.
#:
#: ⚠ **Fourteen of fifteen decoys never reach here**: they are already `partial`
#: via `missing`, which is the corpus-wide signal working. The scattered-terms
#: case is **one query in fifteen**, and this module now *reports* it rather than
#: claiming to catch it.
#:
#: ✅ **RULED by Arpit 2026-08-28: leave the gate off; publish the signal.**
#: Shown the table above, he chose reporting over a claim fux cannot support.
#: **Set this above `0.0` only with a bigger decoy set and a PRE-REGISTERED
#: floor** — not a number read off 65 queries. ADR-CONFIDENCE decision 12.
#:
#: **Overridable since 2026-08-28** as `[confidence] doc_coverage_floor`
#: (decision 13). ⚠ **The cost here is MEASURED, not guessed**, which is what
#: separates it from the separation floor: at `1.0` — the only value that reads
#: structural, *"every term the corpus has, the cited document has too"* —
#: **19 of 50 correct answers turn `partial`**, and the one decoy this clause
#: could catch sits at `0.710`, **inside** the goldens' range.
#:
#: A repo that would rather over-hedge than over-claim can pay 38 % false
#: `partial` deliberately. A repo that sets it because the number looks tidy is
#: paying it for nothing.
DOC_COVERAGE_FLOOR = 0.0


@dataclass(frozen=True)
class Confidence:
    """The confidence block, as returned to a caller and emitted in `--json`.

    Frozen, like every other policy object in the query plane, so a caller can
    never hand two code paths a block that drifted between them.
    """

    #: Fraction of the query's idf mass that exists in the corpus at all.
    coverage: float
    #: `(top1 - top2) / top1`, clamped to `[0.0, 1.0]`. **`1.0` when exactly one
    #: document scored** — nothing competes with it, which is the strongest
    #: separation there is, not the weakest.
    separation: float
    #: How many results scored above zero. **Bounded by `--top`, deliberately** —
    #: see `signals`.
    support: int
    #: The refer plane's verdict on the cited bytes: `current` · `stale` ·
    #: `cached` · `unverified`. `ask` and `find` fetch nothing, so they always
    #: report `unverified` — *"we did not look"*, never *"it was fine"*.
    verified: str
    #: The query's own terms that match no document anywhere in the corpus,
    #: in the order they were written. The user's words, echoed back — never
    #: corpus content, so L2 and L5 are not in play.
    missing: tuple[str, ...]

    #: **How much of the question the TOP-RANKED DOCUMENT itself covers**, as
    #: opposed to the corpus. Added 2026-08-28 (Arpit) after the decoy control
    #: found a question no document answers reported `grounded`.
    #:
    #: ⚠ **`coverage` is corpus-wide and stays that way**, so nothing that reads
    #: it changes meaning. A query whose four terms sit in four DIFFERENT
    #: documents scores `coverage: 1.0` — correctly, the corpus does contain
    #: those words — and `doc_coverage` is what says no single document contains
    #: the question.
    #:
    #: `1.0` when there are no results, so an empty answer is never demoted by
    #: this field; `support == 0` already means `none`.
    doc_coverage: float = 1.0

    #: The `separation` cutoff **this block's band was actually computed
    #: under**. Engine default `SEPARATION_FLOOR`; `.fux/tune.toml` may
    #: override it (decision 13).
    #:
    #: ⚠ **Carried on the block rather than read from the module**, and that is
    #: the whole safeguard. Once the floor is local config, a bare `grounded`
    #: no longer means the same thing in two repos — so the block states the
    #: number it was judged by, and a consumer comparing two answers can see
    #: they were not judged alike.
    separation_floor: float = SEPARATION_FLOOR

    #: The `doc_coverage` cutoff, same contract. `0.0` means **the clause is
    #: off**, which is the engine default and a measured ruling rather than an
    #: oversight — see `DOC_COVERAGE_FLOOR`.
    doc_coverage_floor: float = DOC_COVERAGE_FLOOR

    @property
    def band(self) -> str:
        """`grounded` · `partial` · `weak` · `none`, checked in that order.

        **Read top to bottom: the first true clause wins.** `stale` demotes to
        `partial` rather than to `weak` because stale bytes are a *knowable*
        defect a consumer can name, which is exactly what `partial` means; a
        `weak` result is one where nothing is identifiably wrong and the
        ranking simply cannot choose.
        """
        if self.support == 0:
            return NONE
        if self.missing or self.verified == "stale":
            return PARTIAL
        # ⚠ **The clause the decoy control bought.** Corpus-wide coverage cannot
        # see that a question's terms are scattered across four documents while
        # no single one discusses it — and `separation` cannot either, because it
        # measures whether first place is clearly first, and a corpus of
        # near-misses is decisive about its best near-miss. Measured 2026-08-27:
        # "what is the SLA we publish for the payments API" reached `grounded` at
        # separation 0.58, ABOVE the 0.5 R10's selection rule would have picked,
        # so no threshold on separation closes this.
        if self.doc_coverage < self.doc_coverage_floor:
            return PARTIAL
        if self.separation < self.separation_floor:
            return WEAK
        return GROUNDED

    @property
    def answerable(self) -> bool:
        """**A refusal, not a low number.**

        An agent handed `0.3` will use it anyway and hedge in prose; an agent
        handed `answerable: false` has nothing to hedge with. That asymmetry is
        the reason this is a boolean and not the bottom of a scale
        (ADR-CONFIDENCE decision 5).
        """
        return self.band != NONE

    def with_verified(self, verdict: str) -> "Confidence":
        """The same signals with the refer plane's verdict filled in.

        `answer` ranks before it fetches, so the freshness verdict does not
        exist when the other three signals are computed. Returns a new block —
        the band is a property, so it re-derives itself and cannot go stale
        against the field it is computed from.
        """
        return replace(self, verified=verdict)

    def as_dict(self) -> dict:
        """The `--json` shape, declared in `output.schema.json#confidence`.

        `band` and `answerable` are **written out rather than left derivable**.
        A consumer that had to re-implement the band rules would be a second
        copy of this module's policy, in someone else's language, drifting from
        the day it was written.

        ⚠ **`separation_floor` and `doc_coverage_floor` are emitted for the
        opposite reason** — not so a consumer can re-derive the band, but so it
        can see the band is not comparable across repos. Since 2026-08-28 both
        are `tune.toml` keys, and a `grounded` judged at `0.02` is a different
        claim from a `grounded` judged at `0.10`. **Absent publication, the
        difference would be invisible** (decision 13).
        """
        return {
            "band": self.band,
            "answerable": self.answerable,
            "coverage": self.coverage,
            "separation": self.separation,
            "separation_floor": self.separation_floor,
            "doc_coverage": self.doc_coverage,
            "doc_coverage_floor": self.doc_coverage_floor,
            "support": self.support,
            "verified": self.verified,
            "missing": list(self.missing),
        }

    def line(self) -> str:
        """One ASCII line for stderr, or `""` when there is nothing to say.

        **ASCII only, and never on stdout.** Both rules are the query plane's
        existing declaration contract (`_declare_archived`, `_declare_pending`):
        `find` pipes bare paths, `--json` is a contract, and a Windows console's
        default codepage crashes `print()` on a fancy dash rather than degrading.

        Silent at `grounded`, because a note that fires on every healthy query
        is a note nobody reads by the second day.
        """
        if self.band == GROUNDED:
            return ""
        if self.band == NONE:
            return "confidence: none - nothing in the index scored for this query."
        missing = ""
        if self.missing:
            missing = f" Not in this corpus: {', '.join(self.missing)}."
        if self.band == PARTIAL:
            stale = " The cited bytes have changed since ingest." if self.verified == "stale" else ""
            return f"confidence: partial - answer, but say what is missing.{missing}{stale}"
        return (
            "confidence: weak - the ranking cannot separate the top results"
            f" (separation {self.separation:.2f}, floor {self.separation_floor:.2f})."
            " Report what was searched rather than a conclusion."
        )


def signals(
    pairs: list[tuple[str, str]],
    query_hashes: list[str],
    df: dict[str, int],
    n: int,
    scores: list[float],
    *,
    verified: str = "unverified",
    top_doc_hashes: list[str] | None = None,
    separation_floor: float = SEPARATION_FLOOR,
    doc_coverage_floor: float = DOC_COVERAGE_FLOOR,
) -> Confidence:
    """Compute the block from what `rank()` already had in hand.

    `pairs` is `tokenize_pairs(query)` — `(surface, analyzed)` for each of the
    query's terms — and `query_hashes` their hashes in the same order.
    `scan.query_term_hashes` dedupes on the hash, so the pairing here is
    first-surface-per-hash and a hash collision keeps the first spelling.
    `scores` is every score above zero, **already sorted descending**, which is
    what `rank()` produces.

    **The floors arrive from the CALLER, never from this module's globals.**
    `run_query` resolves them from `.fux/tune.toml` once per query and hands
    them down, so a single query cannot be judged by one floor and reported
    with another — the defect a module-global read would make possible the
    moment the value became configurable (decision 13).

    **`missing` reports the surface form, never the analyzed one.** *"`mtl` is
    not in this corpus"* is a worse report than silence: a reader cannot tell
    whether fux misunderstood the question or the corpus is genuinely missing
    the topic. *"`mTLS` is not in this corpus"* is actionable.

    ## `support` is bounded by `--top`, and that is a real constraint

    A corpus-wide *"47 documents matched"* would be the more useful number, and
    fux cannot honestly emit one. The accelerator's block bound skips documents
    it has **proved** cannot reach the top `k`, so it never scores them; the
    reference scan scores everything. A corpus-wide count would therefore differ
    between `--fast` and `--scan`, which is precisely the differential-law break
    [ADR-T1-ACCELERATOR](../../../docs/adr/0011_accelerator.md) exists to
    forbid. Counting only what both paths agree on keeps the law intact, and the
    law is worth more than the better number.
    """
    if not query_hashes or n <= 0:
        return Confidence(
            0.0, 0.0, 0, verified, (),
            separation_floor=separation_floor,
            doc_coverage_floor=doc_coverage_floor,
        )

    # First token per hash, mirroring `query_term_hashes`' de-duplication so the
    # two lists cannot fall out of step on a repeated word.
    from .. import store as store_mod

    first: dict[str, str] = {}
    for surface, analyzed in pairs:
        first.setdefault(store_mod.term_hash(analyzed), surface)

    total = 0.0
    matched = 0.0
    missing: list[str] = []
    for h in query_hashes:
        weight = idf(df.get(h, 0), n)
        total += weight
        if df.get(h, 0) > 0:
            matched += weight
        else:
            missing.append(first.get(h, h))

    coverage = (matched / total) if total > 0 else 0.0

    # The same idf weighting, over the top document's own terms rather than the
    # corpus's. Weighted, not counted, for `coverage`'s reason: missing `the` is
    # nothing, missing `mTLS` is the question.
    if top_doc_hashes is None:
        doc_coverage = 1.0  # not supplied by this caller — never demote on absence
    elif total > 0:
        present = set(top_doc_hashes)
        doc_coverage = sum(idf(df.get(h, 0), n) for h in query_hashes if h in present) / total
    else:
        doc_coverage = 1.0

    # One result separates perfectly: there is no runner-up to be confused with.
    if len(scores) >= 2 and scores[0] > 0:
        separation = (scores[0] - scores[1]) / scores[0]
    elif len(scores) == 1:
        separation = 1.0
    else:
        separation = 0.0

    return Confidence(
        coverage=round(max(0.0, min(1.0, coverage)), 4),
        doc_coverage=round(max(0.0, min(1.0, doc_coverage)), 4),
        separation=round(max(0.0, min(1.0, separation)), 4),
        support=len(scores),
        verified=verified,
        missing=tuple(missing),
        separation_floor=separation_floor,
        doc_coverage_floor=doc_coverage_floor,
    )
