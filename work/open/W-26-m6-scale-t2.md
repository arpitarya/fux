# W-26 — M6: scale and the T2 tier

> ## RE-SCOPED TO 10 000 DOCUMENTS — Arpit, 2026-08-21
>
> The design point moved from 10⁵–10⁶ to **10 000 documents** (CLAUDE.md
> §Litmus). **50 000 is the next target and 100 000 the one after; 1 000 000
> leaves this milestone entirely.** This item is not cancelled and not parked:
> **`tpack` and the mmap T2 segments still land**, judged at 10k.
>
> **What changes:**
> - **The bench is 10k synthetic + the RFC corpus.** The 100k and 1M sweeps
>   are struck. Keep the harness parameterised by size — re-running it at 50k
>   must be an argument, not a rewrite.
> - **R7's budget must be re-derived and pre-registered at 10 000 before
>   anything is measured.** The old threshold (≤ 250 MB packed @100k) was
>   frozen against the old design point and **is not simply divided by ten**.
>   A naive linear read gives ~25 MB @10k, and the
>   [preliminary analysis](../regression/2026-08-21-r7-preliminary-analysis/ANALYSIS.md)
>   puts the current engine ~2× over the old budget on real data — so the
>   honest expectation is that a 10k budget is **also** missed until
>   `ADR-POSTINGS`'s compact encoding lands. **Do not pick the number to fit
>   the engine.** If the re-derivation is not obvious, it is Arpit's call, not
>   the runner's.
> - **The paper's §5–§6 are rewritten to 10k measurements**, and the 10⁶
>   projections are marked as projections for a deferred target rather than
>   deleted. §4 (keyspace) is unaffected by size.
> - **T2's justification needs re-checking, not assuming.** Byte-aligned mmap
>   segments were motivated by query latency at 10⁵–10⁶. **At 10k the T1
>   accelerator may already be enough** — R3 measured worst-case p95 27.2 ms
>   on 8 870 RFCs, which is the design point almost exactly. **The first
>   question this milestone now asks is whether T2 earns its place at 10k**,
>   and "no" is a legitimate answer that closes it with an ADR instead of a
>   build.
>
> **What does not change:** tier-auto still flips by measurement, never by
> hand; the pre-registration discipline is unchanged; and no frozen threshold
> or filed verdict is edited to fit the new scope.

**Status:** **STARTABLE, 2026-08-20; re-scoped 2026-08-21.** R4, R5 and R6 have all run and carry
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
- Bench at **10k synthetic + the RFC corpus**. (Prior finding: the 1k→10k
  scaling behaviour is recorded in the lab notes — read them before designing
  the sweep.) **100k and 1M struck 2026-08-21** — keep the harness
  size-parameterised so 50k is a flag, not a rewrite.

## Definition of done

- [ ] **R7 re-derived at 10 000 documents.** A new pre-registration, frozen
      before the first number, naming the packed-size budget at 10k. The old
      row (≤ 250 MB packed @100k) is **history, not a divisor**. Tier-auto
      still flips by measurement, never by a hardcoded threshold.
- [ ] **Every R prediction has a measured value or an honest failure ADR.**
      No prediction may end the build as "UNMEASURED".
- [ ] **The paper's §4 (keyspace) and §5–§6 (size, latency) are rewritten
      from projection to measurement at 10 000 documents.** They have been
      knowingly stale since 2026-08-09; this is where that debt is paid, and
      it is a DoD box, not a nice-to-have. **The 10⁶ projections are relabelled
      as projections for a deferred target — not deleted**, because they are
      the argument for the roadmap even when they are not the gate.
- [ ] **A decision on whether T2 earns its place at 10 000 documents**,
      taken before it is built. R3's 27.2 ms p95 on 8 870 RFCs is the design
      point almost exactly; if T1 already clears whatever bar R8 sets, the
      honest close is `ADR-T2-SEGMENTS` recording **why T2 was not built**.
- [ ] `ADR-T2-SEGMENTS` written and accepted — either as the record of the
      segment format, or as the record of the decision not to need one yet.

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

> **The paragraph above is the migrated 2026-08-18 text and is kept verbatim
> as the record of what M6 was.** It is superseded by the re-scope box at the
> head of this file: the bench is 10k + RFC, 1M is out of scope, R7 is
> re-derived at 10k, and T2 must first justify itself at that size. Where the
> two disagree, **the box wins.**
