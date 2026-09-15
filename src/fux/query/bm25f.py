"""BM25F scoring — weighted-tf-then-saturate once, never per-field BM25 summed
(CLAUDE.md law).

**Five fields since 2026-08-23** (W-76 Phase 1): `body`, `heading`, `title`,
`path`, `ctx`, in `store.TF_FIELDS` order. `body` is first because a tf vector
omits trailing zeros and 92.5 % of postings are body-only — see `TF_FIELDS`.

## `wlen` is derived here, not read

The length normaliser is a **weighted** sum of per-field token counts:

    wlen = sum_i  FIELD_WEIGHTS[i] * flen[i]

Until 2026-08-23 that sum was computed at ingest and **committed** as `wlen`,
which made a committed field a function of a tunable — the violation
[SR-TUNE](../../records/0135_tuning.md) decision 6 names, and the reason
field weights could not be tune keys. Changing a weight reweighted the
numerator against a denominator baked in under the old weights: a silent,
corpus-wide ranking error with nothing to see.

Records now commit `flen` (raw per-field counts, a fact) and every consumer
derives `wlen` at query time from the weights in force. `derive_wlen` is the
one place that arithmetic happens, so ingest, the scan, the accelerator's
bound and the refer plane cannot drift apart.

Corpus statistics (`df`, `n`, `avg_wlen`) remain inputs, never derived inside
this module.

## The sixth field is `anchor`, and it is NOT in `TF_FIELDS`

W-168 step 1. A document's anchor terms are the words **other documents use
when they link to it**, and they are folded in here at read time from
`Scoring.anchor` — default `0.0`, so an unconfigured corpus does exactly the
arithmetic it did before the field existed.

🔴 **It is deliberately outside the `weights`/`TF_FIELDS` tuple.** The five
are *committed* fields: each has an entry in the record's own `flen`, and the
index-for-index alignment between `FIELD_WEIGHTS` and `TF_FIELDS` is asserted
below because a misalignment would weight `title` as `path`. Anchor has no
`flen` slot and never enters the committed postings — it is assembled per
query from the `at` maps on **other documents'** edges. Padding it into the
aligned tuple would claim a committed field that does not exist, and would
make every record's `flen` one short.

⚠ **`anchor_tf is None` performs no arithmetic at all** — not a multiply by
zero. Same rule, and the same reason, as `term_weights`: the differential law
must not pick up a last-bit difference from the feature merely being present.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..store import TF_FIELDS

#: Aligned index-for-index with `store.TF_FIELDS`. The two are asserted equal
#: in length below because a silent misalignment would weight `title` as
#: `path` and produce a plausible, wrong ranking.
#:
#: `body` and `heading` keep the values the archived engine calibrated (1.0 and
#: 3.0). `title`, `path` and `ctx` are **new and uncalibrated**: they are set to
#: defensible starting points, not measured optima, and W-76's Phase 1 gate
#: (hit@5 / MRR on the 50 goldens) is what has standing to move them.
FIELD_WEIGHTS: tuple[float, ...] = (1.0, 3.0, 2.0, 1.5, 1.0)

assert len(FIELD_WEIGHTS) == len(TF_FIELDS), "field weights must align with TF_FIELDS"

#: Kept as names so existing callers and records keep reading. They are now
#: *views* on FIELD_WEIGHTS rather than the source of truth.
BODY_WEIGHT = FIELD_WEIGHTS[TF_FIELDS.index("body")]
HEADING_WEIGHT = FIELD_WEIGHTS[TF_FIELDS.index("heading")]

K1 = 1.2
B = 0.75


@dataclass(frozen=True)
class Scoring:
    """`k1`, `b` and the five field weights, carried as ONE object.

    **Why one object and not three parameters.** Every number here appears on
    both sides of the same fraction:

        denom = wtf + k1 * (1 - b + b * wlen / avg_wlen)

    `wtf` is the field weights applied to the numerator; `wlen` is the same
    weights applied to the denominator; `k1` and `b` join them. A caller that
    passes the weights and forgets `k1` reweights half a formula — which is
    the exact defect [SR-TUNE](../../records/0135_tuning.md) decision 6
    recorded as fux's own LUCENE-6819, one level up. Three parameters make
    that mistake possible at every call site; one object makes it
    unrepresentable.

    Immutable, and the default instance is shared — a query that sets nothing
    allocates nothing.
    """

    k1: float = K1
    b: float = B
    weights: tuple[float, ...] = FIELD_WEIGHTS
    #: W-168 step 1 — the anchor field's weight. **Default `0.0`: off**, per
    #: SR-RS decision 19 (a ranking change ships behind a tunable, default off,
    #: and turns on only on a PASS). `0.0` is not "weight zero": every anchor
    #: branch in the engine tests this and is skipped entirely, so a corpus
    #: that configures nothing pays no cost on either candidate path and
    #: scores byte-identically to the build before anchor text existed.
    anchor: float = 0.0

    @property
    def trivial(self) -> bool:
        """True when this is the engine default, so callers can skip work."""
        return (
            self.k1 == K1
            and self.b == B
            and self.weights == FIELD_WEIGHTS
            and self.anchor == 0.0
        )

    @property
    def anchor_on(self) -> bool:
        """The one test for *is the anchor fold live?*

        Read by both candidate generators and by the build. One spelling,
        because a generator that folds anchors and one that does not is the
        differential law failing — and it would fail data-dependently, on the
        documents nobody linked to.
        """
        return self.anchor != 0.0


#: The engine defaults. `tune.load()` returns this when `.fux/tune.toml` is
#: absent, empty, or every key is commented out — the `$0` no-config path.
DEFAULT_SCORING = Scoring()


def idf(df: int, n: int) -> float:
    return math.log((n - df + 0.5) / (df + 0.5) + 1)


def weighted_tf(tf: list[int], scoring: Scoring = DEFAULT_SCORING) -> float:
    """The BM25F numerator for one term in one document.

    `tf` may be shorter than `weights` — trailing zeros are omitted on the
    wire, so a body-only posting arrives as `[1]` and the four absent fields
    contribute nothing. Iterating over `tf` rather than over `weights` is what
    makes the short form free rather than merely small.
    """
    total = 0.0
    weights = scoring.weights
    for i, count in enumerate(tf):
        if count:
            total += weights[i] * count
    return total


def derive_wlen(
    flen: list[int], scoring: Scoring = DEFAULT_SCORING, anchor_len: int = 0
) -> float:
    """The length normaliser, from committed per-field counts and live weights.

    **The one place this arithmetic exists.** Four callers need it — ingest's
    equality gate, the scan's corpus statistics, the accelerator's block bound,
    and the refer plane's passage rescore — and four copies of it is how they
    drift.

    `anchor_len` is W-168's sixth field: the document's anchor token count,
    or the corpus total when the caller is summing `avg_wlen`. **A document
    heavily linked-to is a LONGER document** — leaving anchor out of the
    normaliser is what lets a link farm max out a term with no length price,
    so it is in, at the same weight the numerator uses.
    """
    total = 0.0
    weights = scoring.weights
    for i, count in enumerate(flen):
        if count:
            total += weights[i] * count
    if anchor_len:
        total += scoring.anchor * anchor_len
    return total


def score_record(
    terms: dict[str, list[int]],
    flen: list[int] | int,
    query_hashes: list[str],
    df: dict[str, int],
    n: int,
    avg_wlen: float,
    scoring: Scoring = DEFAULT_SCORING,
    term_weights: dict[str, float] | None = None,
    anchor_tf: dict[str, int] | None = None,
    anchor_len: int = 0,
) -> float:
    """Sum of each matched query term's weight-then-saturate contribution.

    `flen` is a per-field count list. An `int` is accepted and treated as an
    already-derived `wlen` — the accelerator hands one through after computing
    it once per document rather than once per term.

    ## `term_weights` — W-109's `--expand`, and why it is PER TERM

    A per-term multiplier on the summand, not on the total: an expansion adds
    *words*, and only the words it added may be discounted. Scaling the whole
    score would discount the user's own query terms in the same breath.

    ⚠ **`None` performs no multiply at all.** Not a multiply by 1.0 — the
    branch is skipped, so an unexpanded query does exactly the float arithmetic
    it did before the parameter existed and the accelerator/scan differential
    law cannot pick up a last-bit difference from the feature being present.
    `query/expand.py::Expansion.trivial` is what callers test.

    ## `anchor_tf` / `anchor_len` — W-168 step 1's read-time sixth field

    `anchor_tf` is this document's anchor term counts *for the query's hashes*,
    folded by the candidate generator from the `at` maps on the edges of the
    documents that link here. `anchor_len` is its token total, which joins
    `wlen`.

    🔴 **Weighted into `wtf`, never scored as a second BM25.** BM25F is
    weight-then-saturate **once** — summing a separate per-field BM25 is the
    thing CLAUDE.md's law names, and it is what makes an anchor match on a
    short document able to outrank a full body match. One `wtf`, one
    saturation.

    ⚠ **`None` performs no arithmetic at all**, exactly as `term_weights`
    does: an unconfigured corpus must do the float operations it did before
    this parameter existed, or the accelerator/scan differential picks up a
    last-bit difference from the feature being present.

    🔴 **`tf is None` is no longer a reason to skip the term.** A document
    whose own body never uses the word can still be reached by it — that is
    the retrieval half of step 1, and the early `continue` here was the second
    place (after candidate generation) where it would have silently died.
    """
    if n <= 0 or avg_wlen <= 0:
        return 0.0
    if isinstance(flen, (int, float)):
        wlen = float(flen)
    else:
        wlen = derive_wlen(flen, scoring, anchor_len) if anchor_tf is not None else derive_wlen(flen, scoring)
    k1, b = scoring.k1, scoring.b
    anchor_weight = scoring.anchor
    total = 0.0
    for h in query_hashes:
        tf = terms.get(h)
        if anchor_tf is None:
            if tf is None:
                continue
            wtf = weighted_tf(tf, scoring)
        else:
            wtf = weighted_tf(tf, scoring) if tf is not None else 0.0
            count = anchor_tf.get(h)
            if count:
                wtf += anchor_weight * count
        if wtf == 0:
            continue
        denom = wtf + k1 * (1 - b + b * wlen / avg_wlen)
        contribution = idf(df.get(h, 0), n) * wtf * (k1 + 1) / denom
        if term_weights is not None:
            contribution *= term_weights.get(h, 1.0)
        total += contribution
    return total
