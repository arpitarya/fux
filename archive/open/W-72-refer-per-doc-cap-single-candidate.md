# W-72 — the per-document cap wastes budget when there is one candidate document

**Status:** OPEN · **Filed:** 2026-08-22, from
[the budget sweep's finding](../regression/2026-08-22-budget-sweep/report.md)
(closing [W-59](../../archive/open/W-59-refer-plane-measurement.md))
**Blocked by:** — nothing
**Closes with:** a code change to `src/fux/refer/assemble.py`, its own
before/after on `fux answer --json`'s shipped output, and tests.
**Model:** **Sonnet** — well-specified, a measured finding with a named fix,
tests to verify it.

## Why this exists

The refer-plane budget sweep (W-59, 2026-08-22) measured the greedy
assembler against plain top-k truncation at six budgets, in the exact call
shape `fux answer` ships (`query/refer_answer.py` passes `refer()` **exactly
one** candidate document). **The greedy assembler never won**: it tied at
generous budgets and lost by up to 35.5% at realistic ones (500–2000 bytes).

**Root cause, not this item's to re-derive — already found:** `PER_DOC_FRACTION
= 0.5` in `assemble()` caps how much of any *one* document's passages can
enter the budget, to stop one document dominating when several compete for
the same space. With a single candidate, there is nothing else to protect
against — the cap simply discards up to half the budget for no reason. Once a
budget is large enough that the capped half already holds every relevant
passage (≥4000 bytes on the measured corpus), the cap stops binding and
GREEDY/NAIVE converge exactly — evidence the packing logic itself is sound
and the cap is the specific problem.

## What is NOT in question

The score-per-byte resort and the best-answer floor are not implicated —
every budget where the cap didn't bind showed byte-identical value-mass
between the greedy and naive arms. This is a scoped fix to one mechanism,
not a re-litigation of the assembler's design.

## Definition of done

- [ ] `assemble()` does not apply `PER_DOC_FRACTION` when the candidate set
      spans exactly one document (`len({s.doc_id for s in scored}) <= 1`), or
      an equivalent fix that removes the wasted-budget effect without
      reintroducing single-document dominance when it *is* a real risk (e.g.
      a caller passing many chunks of one huge document as if it were
      trustworthy in full).
- [ ] `tests/refer/test_assemble.py` gains a case for the single-candidate
      shape, asserting the fixed behaviour against the sweep's own numbers
      (or a fresh, smaller repro) — not just "no regression."
- [ ] `fux answer --json`'s output on at least one real query is captured
      before/after, since this changes what ships by default.
- [ ] `CHANGELOG.md` under `[Unreleased] → Fixed`.
- [ ] ADR-REFER's veto condition 2 note updated from "recommendation, not
      acted on" to "fixed, see W-72" in the same change.

## Reference

- [`work/regression/2026-08-22-budget-sweep/`](../regression/2026-08-22-budget-sweep/report.md)
  and its `ANALYSIS.md` — the measurement and the recommendation this item
  executes.
- [ADR-REFER](../../docs/adr/0030_refer-plane.md) veto condition 2 — the
  decision this closes out.
- `src/fux/refer/assemble.py` — `PER_DOC_FRACTION`, the cap logic in
  `assemble()`.
