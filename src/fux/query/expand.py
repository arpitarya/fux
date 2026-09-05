"""`--expand` — an agent-written expansion, scored at a lower weight. W-109.

## Why fux takes an expansion instead of writing one

18 of the 18 surviving golden failures are **vocabulary gaps**: the document
does not use the query's words. `q006` is the shape — the question asks about
the *"outage"*, the document is titled *"checkout unavailable for 47 minutes"*
and the word never appears. No amount of BM25F tuning reaches it, because the
term is not there to weight.

Query2doc (arXiv 2303.07678) lifts BM25 by 3-15 % by appending a model-written
pseudo-passage to the query. **Fux may never call a model** (L3), and it does
not have to: its caller usually *is* one. `--expand` is the slot where the
caller hands over the words it thinks the document will use, and fux ranks the
combination deterministically, records it in the receipt, and can replay it.

## The one object, and why it is one

Three values have to travel together into `rank()`:

- `hashes` — everything to score, original terms first;
- `required` — the **original** query's hashes;
- `weights` — the multiplier per hash.

A caller that passes the weights and forgets `required` returns documents that
match **nothing the user asked for**, scored entirely on words a model made up.
That is a hallucinated citation with a sha attached — the failure this whole
architecture exists to prevent. Three parameters make it possible at every call
site; one frozen object makes it unrepresentable, which is the argument
[ADR-TUNE](../../docs/adr/0038_tuning.md) decision 6 already made for
`Scoring`.

## `none()` is the byte-identity guarantee

With no expansion, `weights` is empty and `required` is the whole hash set, so
`score_record` performs **no multiply at all** and the drop test is vacuous. An
unexpanded query takes exactly the arithmetic it took before this module
existed — asserted, not assumed, by
`tests/query/test_expand.py::test_no_expansion_is_byte_identical`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["Expansion", "build"]


@dataclass(frozen=True)
class Expansion:
    """What to score, what the user actually asked for, and at what weight."""

    #: Every hash to score, **original terms first**, de-duplicated. This is
    #: what `scan_candidates`/`accel_candidates` collect on and what
    #: `score_record` sums over.
    hashes: tuple[str, ...]

    #: The hashes of the **original query**. A candidate matching none of these
    #: is dropped by `rank()` before its score is kept.
    required: frozenset[str]

    #: `hash -> multiplier`, for expansion-only hashes. **Empty when there is
    #: no expansion**, and the emptiness is load-bearing: `score_record` skips
    #: the multiply entirely rather than multiplying by 1.0, so no float
    #: operation is added to the unexpanded path.
    weights: dict[str, float] = field(default_factory=dict)

    @property
    def trivial(self) -> bool:
        """True when this changes nothing — the `Scoring.trivial` precedent."""
        return not self.weights

    @classmethod
    def none(cls, query_hashes: list[str]) -> "Expansion":
        """The identity: every hash required, nothing weighted."""
        hashes = tuple(query_hashes)
        return cls(hashes=hashes, required=frozenset(hashes), weights={})

    def matches(self, terms) -> bool:
        """Does this record match at least one term the **user** asked for?

        🔴 **The hallucinated-citation guard.** A record that matches only
        expansion terms is not a weak answer to be ranked low — it is an answer
        to a question nobody asked, and `rank()` drops it outright.

        `terms` is the record's own `terms` mapping, so this is a membership
        test and not a second scoring pass.
        """
        return any(h in terms for h in self.required)

    def weight_of(self, term_hash: str) -> float:
        """The multiplier for one hash. `1.0` for anything not weighted."""
        return self.weights.get(term_hash, 1.0)


def build(query_hashes: list[str], expansion_hashes: list[str], weight: float) -> Expansion:
    """Combine the query's hashes with an expansion's, at `weight`.

    **A hash the original query already carries stays at 1.0**, even when the
    expansion repeats it. The expansion is a *supplement*, and letting it
    re-weight a term the user typed would mean the caller could quietly demote
    their own query by mentioning one of its words.

    `weight <= 0` returns `none()` — off is off, and the unexpanded path must
    be reachable by configuration as well as by omission
    ([ADR-TUNE](../../docs/adr/0038_tuning.md)'s rule for every knob).
    """
    if weight <= 0 or not expansion_hashes:
        return Expansion.none(query_hashes)

    original = list(dict.fromkeys(query_hashes))
    required = frozenset(original)
    extra = [h for h in dict.fromkeys(expansion_hashes) if h not in required]
    if not extra:
        # Every expansion term was already in the query: nothing to add, and
        # nothing to weight. Returning `none()` rather than an object with an
        # empty `weights` keeps `trivial` meaningful for callers that branch.
        return Expansion.none(original)

    return Expansion(
        hashes=tuple(original + extra),
        required=required,
        weights={h: weight for h in extra},
    )
