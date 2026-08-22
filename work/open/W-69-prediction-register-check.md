# W-69 — the prediction register check: ADR-RS's acceptance gate

**Status:** **STARTABLE** · **Filed:** 2026-08-22.

**Spec:** this file.
**Closes with:** the check exists and passes, and
[ADR-RS](../../docs/adr/0036_predictions.md) moves `proposed` → `accepted`.
**Blocked by:** nothing.
**Model:** **Sonnet** — the design is decided and the invariant is assertable.

> **Filed late, and that is itself the finding.** This item existed as a row in
> `OPEN-WORK.md` with **no detail file** from the moment it was created until
> 2026-08-22, which breaks [`open/README.md`](README.md)'s contract — *an item's
> file is created with its index row and deleted with it.* Caught by a review of
> the queue rather than by anything automatic. **W-68 was filed the same way and
> closed before anyone noticed**, so the gap is a pattern, not a one-off.

## Why this exists

[ADR-RS](../../docs/adr/0036_predictions.md) decision 3 says the prediction
table in [`IMPLEMENTATION.md`](../IMPLEMENTATION.md) **claims to be complete**.
Nothing verifies that claim.

**It was already false once.** **R9** ran on 2026-08-22, passed, and was cited
in six documents while having no row in the register. Nothing was wrong with the
measurement; what was missing was anything positioned to notice. A register that
claims completeness and is not checked is worse than one that claims nothing,
because readers trust it.

**This is ADR-RS's acceptance gate.** That record stays `proposed` until this
exists — accepting a record whose central claim is *"the register is complete"*
while nothing verifies completeness is the same class of error as an unmeasured
gate, which is precisely what ADR-RS was written to forbid.

## What lands

A test — `tests/test_prediction_register.py` — that:

1. Walks `work/regression/*/VERDICT.md`.
2. Reads each one's `prediction:` frontmatter id.
3. Asserts a row for that id exists in `IMPLEMENTATION.md`'s prediction table.

**The direction is the whole design, and getting it backwards breaks the
queue.** Assert **every filed verdict has a row** — *not* every row has a
verdict. A **RETIRED** id (R7, R8) has no verdict and never will; a row with no
verdict is normal and must pass.

## Definition of done

- [ ] Every `VERDICT.md`'s `prediction:` id has a register row. **Fails loudly,
      naming the id and the file**, not just "mismatch".
- [ ] **A RETIRED row with no verdict passes** — asserted with R7 or R8 as the
      live fixture, so the direction cannot silently invert later.
- [ ] **A verdict with no row fails** — asserted by construction (a temp fixture
      or a monkeypatched table), because the check that never fails is the one
      nobody notices is broken. This is the box that would have caught R9.
- [ ] Runs with no network and no fixtures beyond the repo, like the other
      doc-law tests.
- [ ] **[ADR-RS](../../docs/adr/0036_predictions.md) flips to `accepted`** in
      the same change, and its veto 4 stops saying UNBUILT.
- [ ] The ADR register's status cell for ADR-RS updated in the same change —
      `tests/test_adr_register_status.py` will fail otherwise.

## Hazards

- **Do not parse the table with a fragile regex that silently matches nothing.**
  A check that passes because it found zero verdicts is the failure mode this
  item exists to prevent, one level up. Assert the walk found a plausible number
  of verdicts before asserting anything about them.
- **Ids appear in prose all over the repo.** Read the `prediction:` frontmatter
  key, never a grep for `R[0-9]`.
- **This check owns no threshold and is not a prediction.** It is a doc law like
  `test_doc_registry.py`, and it belongs with them.

## Reference

- [ADR-RS](../../docs/adr/0036_predictions.md) — decision 3 (the register
  claims completeness) and veto 4 (this check).
- The register itself — the prediction table in
  [`IMPLEMENTATION.md`](../IMPLEMENTATION.md).
- The precedent for a doc law asserted as a test —
  [`tests/test_doc_registry.py`](../../tests/test_doc_registry.py) and
  [`tests/test_adr_register_status.py`](../../tests/test_adr_register_status.py),
  the latter written after register-vs-record drift hit twice.
- The failure that motivated it — R9's row, added by hand on 2026-08-22 after
  it had been missing since the run.
