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
[ADR-TUNE](../../docs/adr/0038_tuning.md) decision 6 names, and the reason
field weights could not be tune keys. Changing a weight reweighted the
numerator against a denominator baked in under the old weights: a silent,
corpus-wide ranking error with nothing to see.

Records now commit `flen` (raw per-field counts, a fact) and every consumer
derives `wlen` at query time from the weights in force. `derive_wlen` is the
one place that arithmetic happens, so ingest, the scan, the accelerator's
bound and the refer plane cannot drift apart.

Corpus statistics (`df`, `n`, `avg_wlen`) remain inputs, never derived inside
this module.
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
    the exact defect [ADR-TUNE](../../docs/adr/0038_tuning.md) decision 6
    recorded as fux's own LUCENE-6819, one level up. Three parameters make
    that mistake possible at every call site; one object makes it
    unrepresentable.

    Immutable, and the default instance is shared — a query that sets nothing
    allocates nothing.
    """

    k1: float = K1
    b: float = B
    weights: tuple[float, ...] = FIELD_WEIGHTS

    @property
    def trivial(self) -> bool:
        """True when this is the engine default, so callers can skip work."""
        return self.k1 == K1 and self.b == B and self.weights == FIELD_WEIGHTS


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


def derive_wlen(flen: list[int], scoring: Scoring = DEFAULT_SCORING) -> float:
    """The length normaliser, from committed per-field counts and live weights.

    **The one place this arithmetic exists.** Four callers need it — ingest's
    equality gate, the scan's corpus statistics, the accelerator's block bound,
    and the refer plane's passage rescore — and four copies of it is how they
    drift.
    """
    total = 0.0
    weights = scoring.weights
    for i, count in enumerate(flen):
        if count:
            total += weights[i] * count
    return total


def score_record(
    terms: dict[str, list[int]],
    flen: list[int] | int,
    query_hashes: list[str],
    df: dict[str, int],
    n: int,
    avg_wlen: float,
    scoring: Scoring = DEFAULT_SCORING,
) -> float:
    """Sum of each matched query term's weight-then-saturate contribution.

    `flen` is a per-field count list. An `int` is accepted and treated as an
    already-derived `wlen` — the accelerator hands one through after computing
    it once per document rather than once per term.
    """
    if n <= 0 or avg_wlen <= 0:
        return 0.0
    wlen = float(flen) if isinstance(flen, (int, float)) else derive_wlen(flen, scoring)
    k1, b = scoring.k1, scoring.b
    total = 0.0
    for h in query_hashes:
        tf = terms.get(h)
        if tf is None:
            continue
        wtf = weighted_tf(tf, scoring)
        if wtf == 0:
            continue
        denom = wtf + k1 * (1 - b + b * wlen / avg_wlen)
        total += idf(df.get(h, 0), n) * wtf * (k1 + 1) / denom
    return total
