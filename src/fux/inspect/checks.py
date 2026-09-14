"""The three checks — and the reason there are only three.

`fux inspect` is **descriptive by default**. Every lens prints distributions and
named lists; exactly three numbers carry a *pass / attention* flag:

1. **unreachable share** — the share of documents that carry no distinctive
   term at all, so no query can select them.
2. **boilerplate share of postings** — the share of the index's postings whose
   term is on half the corpus or more.
3. **near-duplicate share** — the share of documents that are one half of a
   near-duplicate pair.

⚠ **Their floors are PROVISIONAL and the report says so on every line.** They
were measured on the golden ladder
([`work/regression/2026-09-14-inspect-floors/`](../../../work/regression/2026-09-14-inspect-floors/report.md)),
never tuned to any one repository, and the rule a floor has to satisfy was
pre-registered: **a floor that flags a healthy golden rung is dropped to
descriptive** — the number still prints, the flag does not. A wall of red on an
unmeasured floor is how a diagnostic tool gets ignored, and then the one real
finding in it is ignored too.

🔴 **`findable share` IS a dropped floor, and this is the measured reason.**
The plan was for self-retrieval — *does a document come back in the top 3 for
its own most distinctive words* — to be the headline check. It measures almost
nothing, and the rule caught it: the share is **1.000 on every golden rung and
1.000 on the deliberately terrible planted-bad corpus**, whose 40 documents are
one runbook copied forty times. The cause is structural rather than a bad
threshold. A fingerprint is built from the document's own rarest terms, and a
document's **path is part of its indexed vocabulary and is unique by
construction** — so a document with any rare term at all, its own file name
included, retrieves itself. A check that cannot separate a healthy corpus from
a pathological one is not a check. The number still prints, under the
findability lens, because *"can the engine return this document at all"* is
worth answering; the flag went to the **exhaustive** half, which is the one
that fires on the shape it names.

**No flag here fails the command.** `fux inspect` exits 0 on a corpus it has
things to say about, because *"your index has boilerplate"* is not an error —
it is the report. It exits non-zero only when it cannot produce a report at
all, which the CLI boundary already owns.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Check", "FLOORS", "Floor", "run_checks"]


@dataclass(frozen=True)
class Floor:
    """One provisional floor: the bound, its direction, and where it came from.

    `provisional` is a field rather than a comment because the report prints
    it. A floor whose status is only in a docstring reads, in a terminal, as a
    settled threshold.
    """

    name: str
    bound: float
    #: `"min"` — attention below the bound. `"max"` — attention above it.
    direction: str
    provisional: bool
    source: str

    def flags(self, value: float) -> bool:
        return value < self.bound if self.direction == "min" else value > self.bound

    def describe(self) -> str:
        comparison = ">=" if self.direction == "min" else "<="
        return f"{comparison} {self.bound:.2f}"


_SOURCE = "work/regression/2026-09-14-inspect-floors/"

#: ⚠ **Measured, not chosen.** The rule every bound here satisfies: it does not
#: flag any golden rung, and it does flag a corpus that is bad in that bound's
#: own dimension. A bound that cannot do both is not a floor, and its number
#: ships as description alone — `findable share` is the one that failed it.
FLOORS: dict[str, Floor] = {
    "unreachable share": Floor(
        name="unreachable share",
        bound=0.01,
        direction="max",
        provisional=True,
        source=_SOURCE,
    ),
    "boilerplate share": Floor(
        name="boilerplate share",
        #: ⚠ **0.60, and the gap to it is the finding.** Every golden rung sits
        #: at **0.47** — they are generated from one template, so half of every
        #: posting is a term on half the corpus — while this repository sits at
        #: **0.072**. A bound anywhere near the honest-looking 0.25 would flag
        #: all seven rungs, which the pre-registered rule forbids, so the bound
        #: sits above them and catches only the pathological case (planted-bad:
        #: 0.985). **That makes this the weakest of the three and it says so.**
        bound=0.60,
        direction="max",
        provisional=True,
        source=_SOURCE,
    ),
    "near-duplicate share": Floor(
        name="near-duplicate share",
        #: The cleanest separation of the three: every golden rung is 0.000 and
        #: planted-bad is 1.000.
        bound=0.20,
        direction="max",
        provisional=True,
        source=_SOURCE,
    ),
}


@dataclass
class Check:
    """One reported number. `floor is None` means **descriptive**, not broken.

    The three states are deliberately distinct, because collapsing any two of
    them tells a reader something false:

    - `ok` / `attention` — there is a number and a measured floor.
    - `descriptive` — there is a number and **no floor that could separate a
      healthy corpus from a bad one**. The number is still the answer to its
      question.
    - `n/a` — there is no number at all. **Never a pass**: treating an absent
      number as a pass is how a broken instrument reads as a healthy corpus.
    """

    name: str
    value: float | None
    floor: Floor | None
    detail: str

    @property
    def flagged(self) -> bool:
        if self.value is None or self.floor is None:
            return False
        return self.floor.flags(self.value)

    @property
    def status(self) -> str:
        if self.value is None:
            return "n/a"
        if self.floor is None:
            return "descriptive"
        return "attention" if self.flagged else "ok"


def run_checks(boilerplate, findability, duplication, *, documents: int) -> list[Check]:
    """The four numbers the report leads with — three floored, one descriptive."""
    share = findability.findable_share
    if share is None:
        findable_detail = "no documents were sampled for retrieval"
    else:
        findable_detail = (
            f"{findability.retrieved} of {findability.sampled} documents are returned in the top 3 "
            f"for their own most distinctive words"
            + (
                " (every document)"
                if findability.sample_is_whole_corpus
                else " (an evenly spaced SAMPLE - the share is an estimate)"
            )
        )
    unreachable = len(findability.unfindable) / documents if documents else None
    return [
        Check(
            name="unreachable share",
            value=unreachable,
            floor=FLOORS["unreachable share"],
            detail=(
                f"{len(findability.unfindable)} of {documents} documents carry no distinctive term "
                f"at all, so no query can select them (EXHAUSTIVE - every document was checked)"
            ),
        ),
        Check(
            name="boilerplate share",
            value=boilerplate.boilerplate_share,
            floor=FLOORS["boilerplate share"],
            detail=(
                f"{boilerplate.boilerplate_postings} of {boilerplate.postings} postings carry one of "
                f"{boilerplate.boilerplate_terms} term(s) on half the corpus or more"
            ),
        ),
        Check(
            name="near-duplicate share",
            value=duplication.near_duplicate_share,
            floor=FLOORS["near-duplicate share"],
            detail=(
                f"{duplication.documents_in_a_pair} of {duplication.docs} documents are one half of a "
                f"near-duplicate pair (Jaccard >= 0.80); {duplication.pair_count} pair(s)"
            ),
        ),
        # ⚠ **Descriptive, deliberately — `floor=None` is the measured verdict**
        # and not an omission. See the module docstring: 1.000 on every golden
        # rung and 1.000 on planted-bad.
        Check(
            name="findable share",
            value=share,
            floor=None,
            detail=findable_detail,
        ),
    ]
