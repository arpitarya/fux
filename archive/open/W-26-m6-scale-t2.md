# W-26 — M6: scale and the T2 tier

> **CLOSED 2026-08-22 · ARCHIVED.** The milestone's first question was answered
> by measurement: **T2 is not built** ([R9](../../work/regression/2026-08-22-r9-t2-at-10k/VERDICT.md)
> passed at 12.46 ms against R3's own 150 ms bar), recorded in
> [ADR-T2-SEGMENTS](../../docs/adr/0037_t2-segments.md). Its last open box —
> R7's budget — **dissolved when Arpit retired R7** rather than being met.
> Outcome in [IMPLEMENTATION.md](../../work/IMPLEMENTATION.md).
> **Archive is not evidence** — may be named, never cited.

> ## RE-SCOPED TO 10 000 DOCUMENTS — Arpit, 2026-08-21
>
> The design point moved from 10⁵–10⁶ to **10 000 documents** (CLAUDE.md
> §Litmus). **50 000 is the next target and 100 000 the one after; 1 000 000
> leaves this milestone entirely.**
>
> **⚠ AMENDED 2026-08-22 — those later targets are now CLOSED TO MEASUREMENT.**
> Arpit: *"no testing should go beyond ten thousand documents"* until the tool
> is built out. So *next target* means **next in intent, not next in queue** —
> no session runs a 50 000-document bench, and the harness staying
> size-parameterised is **readiness, not permission**. Reopening them is
> Arpit's, deliberately. This item is not cancelled and not parked:
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

**Status:** **MOSTLY DONE 2026-08-22 — the tier question is answered and T2 is
not built.** [R9-T2-AT-10K](../regression/2026-08-22-r9-t2-at-10k/VERDICT.md)
PASSED at 12.46 ms against R3's 150 ms bar, closing
[ADR-T2-SEGMENTS](../../docs/adr/0037_t2-segments.md) as a decision *not* to
build; the paper's §5–§6 are rewritten to measured. **Two boxes remain and both
are Arpit's**: R7's budget re-derivation (`work/BLOCKED.json`) and whether §4's
*architectural* staleness is in scope. The row stays until he has read those.

**Previously: STARTABLE, 2026-08-20; re-scoped 2026-08-21.** R4, R5 and R6 have all run and carry
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

- [~] ~~**R7 re-derived at 10 000 documents.**~~ **DISSOLVED 2026-08-22 — the
      requirement was removed, not met.** Arpit retired R7 outright: *"remove
      that promise, it's not needed."* There is no committed-size budget and no
      successor is owed. **Marked dissolved rather than ticked**, because a box
      that was deleted is not a box that was satisfied, and a later reader must
      be able to tell those apart. The size is still measured by ADR-POSTINGS'
      and ADR-INDEX-LIFECYCLE's checks — as information, never as a gate.
- [x] **Every R prediction has a measured value or an honest failure ADR.**
      R4 ✅ · R5 ❌ · **R6 ✅ (re-run 2026-08-22, W-67)** · R7 CLOSED unmeasured,
      re-derivation blocked above · **R9 ✅ (new, this milestone)**.
- [x] **The paper's §5–§6 (size, latency) are rewritten from projection to
      measurement at 10 000 documents**, with the 10⁶ figures **relabelled as
      deferred-target projections, not deleted**. Also corrected while there:
      the abstract, §1.3's `~250 B/doc` contribution, §1.3's P1 claim, and
      §8's P2/P3 rows (both retired with plan revision 1 and still presented as
      live gates).
      ⚠ **§4 (keyspace) was NOT rewritten, and this file contradicts itself
      about whether it should be.** The re-scope box says *"§4 (keyspace) is
      unaffected by size"*; this DoD box said §4 is rewritten *"from projection
      to measurement"*. §4 contains **no numbers**, so there is nothing to
      measure — its staleness is *architectural*: it describes an MST keyspace
      with a bit-packed wire format, which `index-format.compare.md` superseded
      on 2026-08-09 in favour of sharded canonical JSONL. **That is a paper
      rewrite, not a measurement**, it is larger than this milestone, and
      guessing at it would be an agent re-deciding an architecture. Left for
      Arpit.
- [x] **A decision on whether T2 earns its place at 10 000 documents**,
      taken before it is built. **Answered by measurement:**
      [R9-T2-AT-10K](../regression/2026-08-22-r9-t2-at-10k/VERDICT.md) — worst-case
      warm p95 **12.46 ms against R3's own 150 ms bar**, 12× inside.
      ⚠ **The bar is R3's, reused verbatim, not a new number** — picking a
      fresh one having already seen R3's 27.2 ms is the inversion the
      pre-registration rule exists to stop.
      ⚠ **R3's 27.2 ms could not be used as evidence**: its corpus was lost
      with the lab (W-56), so this is a **new baseline**, not a confirmation.
- [x] `ADR-T2-SEGMENTS` written and accepted — as **the record of the decision
      not to need one yet**, which this file named in advance as legitimate.
      [ADR-T2-SEGMENTS](../../docs/adr/0037_t2-segments.md), accepted
      2026-08-22, owning `tools/t2-eval/` and nothing in `src/`.

## What this milestone did **not** build, and why that is the outcome

`tpack` writer/reader, mmap byte-aligned segments, the partial-clone
deployment doc and external-shards-only committing — **all of §What lands** —
are not built. That is not scope being dropped: it is the answer to the
question the re-scope box put first, and it is recorded in an accepted ADR
with a reopen condition that is a **number rather than a size**, so nobody has
to remember to revisit it at 50 000.

**Two things surfaced that this file did not anticipate:**

1. **`R8` is claimed by two documents.** This file's DoD referred to *"whatever
   bar R8 sets"* for T2, while
   [`graph-plane-format.compare.md`](../compare/graph-plane-format.compare.md)
   §6 had already named R8 for *"a graph verb answers in under X s at 100 000
   documents"*. **The T2 measurement was registered as R9** and R8 left where
   it was described first and in most detail. Confirming or swapping that is a
   one-line call and is in `work/BLOCKED.json`.
2. **`[index] tier = t0|t1|t2|auto` does not exist in the code** — `fux.toml`'s
   `[index]` table holds only `shards`. *"Tier-auto flips by measurement, never
   by hand"* has been governing an unbuilt mechanism the whole time. The knob
   is deliberately **still** not created (ADR-T2-SEGMENTS decision 3): it ships
   with the tier, or it is surface with no capability behind it.

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
