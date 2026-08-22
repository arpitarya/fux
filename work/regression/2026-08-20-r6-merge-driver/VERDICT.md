---
type: Verdict
name: R6-MERGE
title: R6-MERGE — the three-tier merge harness — INCONCLUSIVE
description: "All three tiers matched their expected outcome and the driver is demonstrably doing the work on tiers 2 and 3, but tier 1 merged cleanly with the driver removed as well — so it proves nothing, and the frozen verdict table does not cover 'some but not all tiers informative'. The substance of R6 holds; the arithmetic is Arpit's call."
verdict: INCONCLUSIVE
adjudication: "PASS — Arpit, 2026-08-22, ruling that §3.1 governs. The measured verdict below is unchanged and unedited; the adjudication is an addendum."
prediction: R6
pre_registration: tools/maintenance-bench/PRE-REGISTRATION.md
timestamp: 2026-08-20T00:00:00Z
---

# R6-MERGE — the three-tier merge harness: **INCONCLUSIVE**

> **This is a verdict, not a decision record.** It is the ruling of a
> pre-registered measurement against its frozen threshold, and nothing
> supersedes it except a better measurement — which would be a new run with its
> own verdict. It is **cited**, never replaced, and lives with its evidence.

- **Name:** `R6-MERGE` — cite this by name
- **Verdict:** **INCONCLUSIVE**, and the reason is the frozen table's shape
  rather than the engine's behaviour
- **Prediction under test:** **R6** — machine planes conflict-free, human
  conflicts preserved
- **Date:** 2026-08-20
- **Pre-registration (frozen before the first number):**
  [`../../../tools/maintenance-bench/PRE-REGISTRATION.md`](../../../tools/maintenance-bench/PRE-REGISTRATION.md)
  (commit `d98874d`)
- **Evidence:** [`report.md`](report.md) · [`evidence/`](evidence/)
- **The harness:** [`tools/maintenance-bench/`](../../../tools/maintenance-bench/run.py)
  — owned by [ADR-MAINTENANCE](../../../docs/adr/0033_hooks.md)
- **What depends on this verdict:** ADR-MAINTENANCE's status and its veto
  condition 2

---

## Headline

**Every judged tier matched its expected outcome. The engine did what R6 says
it does.** The verdict is not PASS because tier 1 also matched *without the
merge driver installed*, and the pre-registration requires tiers 1 and 2 to be
informative — to conflict in the control arm and merge cleanly in the
treatment arm — before the pass may be claimed.

| tier | expected | treatment | control | informative | matched |
|---|---|---|---|---|---|
| 1 · disjoint adds | no conflict | clean | **clean** | **no** | ✅ |
| 2 · one shard, two lines | no conflict | clean | **conflict** | ✅ | ✅ |
| 3 · same document, both sides | conflict preserved | conflict, both sides kept | conflict | n/a | ✅ |

The frozen table (§3.2) defines PASS as *all tiers match **and** tiers 1 and 2
are informative*, and INCONCLUSIVE as *all tiers match but **neither** is
informative*. **This result — all match, one of two informative — falls between
those rows.** CLAUDE.md says a result between the defined outcomes is written
up and handed to Arpit rather than adjudicated by whoever ran it, so that is
what this is.

## Why tier 1 was uninformative, and why that is a finding rather than a fault

Two documents added on two branches hash into **two different shard files**, so
git is merging two files that each changed on one side only. It has always been
able to do that. The tier was constructed to describe the everyday case, and
the everyday case turns out not to need the feature.

**The control arm is the only reason anyone knows that.** Without it, tier 1
reads as a pass and is evidence for nothing at all — the driver could have been
uninstalled and the number identical. §3.1 was written to prevent exactly that,
and it fired on the very first run.

**Post-hoc, tier 1b settles the underlying question**: with the two added
documents *selected by hashing* to share a shard, the control conflicts and the
treatment merges cleanly. Concurrent adds are handled. That arm is labelled
post-hoc, sits outside this verdict, and does not turn it into a PASS —
it was built after seeing the result it then fixed.

## What is not in doubt

- **The machine plane does not conflict on adjacency** (tier 2, informative).
- **The driver refuses rather than picking** (tier 3): same `ver`, different
  bytes, ordinary conflict markers, both sides' bytes intact — asserted, not
  inferred.
- **Human prose conflicts exactly as it always did** (tier 3), which is the
  asymmetry the whole design rests on.

## The call in front of Arpit

Two readings, and the pre-registration supports both, which is the defect:

1. **PASS.** §3.1 says an uninformative tier *"does not count toward the
   pass"* — i.e. the remaining tiers carry it, and tiers 2 and 3 both do,
   informatively.
2. **Not yet.** §3.2's table requires tiers 1 **and** 2 informative, full stop.

**The honest fix, whichever way it goes, is to the instrument, not the
threshold**: tier 1 should be re-specified so that its two added documents
share a shard — which is what 1b already does — and re-run clean. That is a new
measurement with its own verdict, not an edit to this one.

---

## Adjudication — Arpit, 2026-08-22

> **Nothing above this line was edited.** A filed verdict is a measurement, and
> nothing supersedes a measurement except a better measurement. What follows is
> the answer to the section directly above it — *"The call in front of Arpit"* —
> recorded where the question was asked.

**Ruling: PASS, under §3.1's reading.** An uninformative tier *"does not count
toward the pass"*, so tier 1 is dropped from the tally and R6 is judged on the
tiers that do count — **tiers 2 and 3, both informative, both matched**.
[ADR-MERGE-DRIVER](../../../docs/adr/0034_merge-driver.md) moves to `accepted`
on that basis.

**Why the runner could not have taken this call.** §3.2's PASS row requires
tiers 1 **and** 2 informative; its INCONCLUSIVE row requires **neither**. This
result — all tiers matching, one of two informative — fits no row in the frozen
table. CLAUDE.md's rule is that a result between the defined outcomes is written
up and handed to Arpit rather than adjudicated by whoever ran it. That is what
happened, and this is the other half of it.

**What this ruling is honestly resting on.** §3.1's clause and §3.2's table
disagree, and the ruling picks the former. That is a defensible reading — §3.1
is where informativeness is *defined* and where its consequence is *stated*,
while §3.2 is a summary table — but it is a reading, not a derivation. **Two
obligations follow, and both are W-67:**

1. **Repair the instrument, in a change separate from any verdict.** §3.1 and
   §3.2 are made to agree. The threshold itself is not touched — a
   pre-registered threshold may never move.
2. **Re-specify tier 1 and re-run.** Its two added documents must be selected
   by hashing to share a shard, which is what the post-hoc tier 1b already
   does. That is a **new** pre-registration and a **new** verdict, never an
   edit to this one. [ADR-MERGE-DRIVER](../../../docs/adr/0034_merge-driver.md)
   veto condition 2 is the tripwire if it comes back FAIL.

**What the ruling does not do.** It does not turn tier 1 into evidence, it does
not promote the post-hoc tier 1b into this verdict, and it does not make the
frozen table any less contradictory than it was on 2026-08-20.
