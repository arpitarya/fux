---
type: Verdict
name: "W-169 floors — the keep/remove call on fux inspect's three flagged checks"
verdict: PASS
description: "The keep/remove call W-169 pre-registered for its three flagged checks. Two bounds are admissible and ship provisional. `findable share` has no admissible bound — 1.000 on every golden rung AND on forty copies of one runbook — and ships descriptive, which is the pre-registered rule firing rather than a threshold being missed."
run: 2026-09-14-inspect-floors
item: W-169
prediction: W-169-FLOORS
pre_registration: work/regression/2026-09-14-inspect-floors/PRE-REGISTRATION.md
filed: 2026-09-14
---

# VERDICT — two floors ship, one number goes descriptive

⚠ **`verdict: PASS` means the CRITERION was decidable on all four numbers and
was applied without being loosened. It does not mean four checks passed.** One
of them — `findable share` — **lost its flag**, which is the rule's own stated
outcome for a number no bound can floor (*"this is the rule passing, not the
run failing"*). A reader scanning the frontmatter should read *the call was
made*, never *everything is fine*.

**The call this adjudicates** is `W-169` DoD 5 and
[`work/proposals/fux-inspect.md`](../../proposals/fux-inspect.md) §5b: *a floor
separates the planted-bad corpus from every golden rung; a floor that flags a
healthy rung is dropped to descriptive — the number prints, the flag does not.*

⚠ **Read [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md) §1 before this.** The
criterion predates the numbers and is in git at two named commits; the
`PRE-REGISTRATION.md` **file** does not and is a restatement. An earlier draft
of this run claimed otherwise and is corrected there.

## The ruling

| number | verdict | bound | the numbers it rests on |
|---|---|---|---|
| **unreachable share** | ✅ **ships, provisional** | `<= 0.01` | 0.0000 on all seven rungs; **0.0370** on `planted-lenses`, which carries one document with no distinctive term out of 27 |
| **near-duplicate share** | ✅ **ships, provisional** | `<= 0.20` | 0.0000 on all seven rungs; **1.0000** on `planted-bad` |
| **boilerplate share** | ⚠ **ships, provisional — and weak, disclosed** | `<= 0.60` | 0.4713–0.4750 on all seven rungs; **0.9848** on `planted-bad`; 0.0721 on this repository |
| **findable share** | 🔴 **DESCRIPTIVE — no admissible bound exists** | none | **1.000 on every rung AND 1.000 on `planted-bad`** |

## Why `findable share` could not be floored, and why that is the rule working

Self-retrieval was this verb's intended headline check. It **cannot separate a
healthy corpus from a pathological one**, and the cause is structural rather
than a badly chosen threshold:

> A fingerprint is built from the document's own rarest terms, and a document's
> **path is part of its indexed vocabulary and is unique by construction**.

`planted-bad` is one runbook copied forty times, differing only by a two-digit
service number — and every one of the forty retrieves itself. There is no bound
between 1.000 and 1.000.

**The flag moved to the exhaustive half.** *No distinctive term at all* costs no
queries, is computed for every document rather than a sample, and fires on
exactly the shape it names.

**This is a successful outcome, not a failed task.** A pre-registered rule was
written, a number was measured against it, and the number lost its flag. The
alternative — keeping a flag that reads `ok` on every corpus anyone will ever
run it on — is a check that can only ever produce false reassurance.

## What this verdict does NOT rule

- **It does not rule on ranking.** `fux inspect` changes none, and this run
  states no delta between arms (`not a paired run`).
- **It does not judge the golden ladder.** §4 of the
  [report](report.md) measures that the ladder is one vocabulary spread over
  more documents — 100× the documents for 2.1× the vocabulary, Heaps β 0.599 →
  0.20. **That is filed as evidence for
  [W-156](../../open/W-156-prevalence-outside-golden.md) and is Arpit's call**,
  not this run's. Nothing here changes a threshold, a default or the ladder.
- **It does not settle the boilerplate bound for good.** 0.60 is provisional
  and admissible; it is also the weakest of the three, and the report says so
  in as many words. A ladder with an ordinary boilerplate share would allow a
  much tighter one.

## Reproduce

The command is in [`report.md`](report.md) §7. The per-corpus rows this verdict
reads are [`evidence/corpora.jsonl`](evidence/corpora.jsonl); the complete
`fux inspect --json` for each corpus is beside them.
