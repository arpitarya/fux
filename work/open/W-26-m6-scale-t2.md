# W-26 — M6: scale and the T2 tier

**Status:** **STARTABLE, 2026-08-20.** R4, R5 and R6 have all run and carry
verdicts; **R7 is this milestone's own measurement**, not a precondition for
it, which is what the DoD box means by *"a measured value or an honest failure
record"*. Two of the three verdicts are not passes, and both are recorded
rather than pending.

> **What M6 inherits from R5's failure.** A 20-document commit costs **44 s at
> 100 000 documents** ([R5-HOOK](../regression/2026-08-20-r5-hook-latency/VERDICT.md)),
> and the attribution puts **47.6 % of it in `fux build`** — the derived plane
> M6 is about to add a *third* tier to. T2 is not only a query-speed feature;
> it lands on the maintenance path this milestone's sibling gate just failed.
> Measure the rebuild cost of any tier before choosing its default.

> **The one thing that does not relax.** Tier-auto must flip **by measurement,
> not by a hardcoded threshold**. Picking it by hand and then looking for
> evidence is the inversion the pre-registration rule exists to stop.

**Blocked by:** nothing. (Was: the held prediction runs — lifted 2026-08-20.)
**Spec:** this file — see §Scope below (migrated from the retired `PLAN.md`, 2026-08-18)
**Closes with:** **`ADR-T2-SEGMENTS`** (reserved) · prediction **R7**. **Reserved by NAME, never by number** — a number is a filename ordinal assigned when the record is written (Arpit, 2026-08-19, closing W-33).
**Model:** **Sonnet** for the bench harness · **Opus** for the analysis and
the paper rewrite — interpreting a scaling measurement is exactly the
"confidently wrong" failure mode.

## Goal

Prove the architecture at the scale it was designed for, and **replace the
paper's projections with measurements**.

## What lands

- `tpack` writer/reader — the same records, one property swaps.
- mmap byte-aligned segments as the **T2** accelerator.
- Partial-clone deployment doc; external-shards-only committing.
- Bench at 100k synthetic + the RFC corpus + 1M synthetic if feasible.
  (Prior finding: the 1k→10k scaling behaviour is recorded in the lab
  notes — read them before designing the sweep.)

## Definition of done

- [ ] **R7**: committed index at 100k target density ≤ **250 MB**
      git-packed; tier-auto flips by measurement, not by a hardcoded
      threshold.
- [ ] **Every R prediction has a measured value or an honest failure ADR.**
      No prediction may end the build as "UNMEASURED".
- [ ] **The paper's §4 (keyspace) and §5–§6 (size, latency) are rewritten
      from projection to measurement.** They have been knowingly stale
      since 2026-08-09; this is where that debt is paid, and it is a DoD
      box, not a nice-to-have.
- [ ] `ADR-T2-SEGMENTS` written and accepted.

## Hazards

- The BIC codec lives **inside T2 only**. It is superseded for the
  committed plane and must not leak back out.
- Shard churn at high edit rates measured fine at 138 MB; shard count
  (256 → 1024) is the knob if real usage disagrees. Changing it is an ADR,
  not a tweak.
- A pre-registered threshold may never move. If R7 lands between clearly
  passing and clearly failing, write it up as **ambiguous and hand it to
  Arpit** — do not adjudicate it.

## Lab

New runs are **new directories inside** `~/my_programs/fux-lab`. The lab is
never deleted or rebuilt. Run the tiers in the cloud, not the device VM.

---

## Scope — M6 — scale and T2

*Migrated verbatim from `PLAN.md` §M6 on 2026-08-18, when
that document was archived. **This file is now the spec**; there is no other.*

`tpack` writer/reader (same records, one property swaps); mmap byte-aligned
segments as the T2 accelerator; partial-clone deployment doc;
external-shards-only committing; bench at 100k synthetic + RFC + 1M synthetic
if feasible. **The paper's §4 (keyspace) and §5–§6 (size, latency) are
rewritten from projection to measurement here.**

**DoD:** R7; tier-auto flips by measurement; every R has a measured value or
an honest failure record.
