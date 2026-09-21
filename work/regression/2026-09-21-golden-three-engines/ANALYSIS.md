---
type: Analysis
run: 2026-09-21-golden-three-engines
description: "Three diagnoses: what capture 2's near-total churn actually measures, why capture 6 is not a benchmark and what it would cost to make it one, and the two asymmetries that make v1 a different product rather than an older engine."
filed: 2026-09-21
---

# ANALYSIS — three engines that are not three versions of one thing

## 1 · Capture 2 measures *the engines disagree*, and cannot measure more

**Diagnosis.** `v2 → HEAD` moves the whole ranked list on **125 of 125** queries
at every rung. That looks like the headline and it is not a finding: `b` went
`0.75 → 0.15` between those releases (W-144, measured), and length normalisation
is a term in every document's score. **A knob that enters every score reorders
every list**; the only surprise would have been if it had not.

**Change, specific:** the report states the cause in the same paragraph as the
number, and [`evidence/ARMS.md`](evidence/ARMS.md) prints each arm's own `b`
before any A-vs-B row is quoted.

```bash
grep -hE "^b\s*=" ~/my_programs/fux-lab/arms/runs/v2/rung-01000/.fux/tune.toml \
                  ~/my_programs/fux-lab/corpora/golden/rung-01000/.fux/tune.toml
```

**Unresolved, and unresolvable here:** *which* ordering is better. Capture 2
counts movement; **movement has no direction without a key**, and inventing one
is exactly what phase D exists to prevent. ⚠ **A reader who takes 125-of-125 as
evidence of improvement has read a diff as a verdict.**

## 2 · Capture 6 is not a benchmark, and saying so costs less than pretending

**Diagnosis.** [SR-WORK-BENCHMARK](../../../records/0053_WORK-benchmark.md)
capture 6 wants the arms **interleaved** on one machine, per L9. This run did
not interleave: it built and ran v1 across eight rungs, then v2 across eight,
over roughly two hours, while other work shared the box.

**Change, specific:** the numbers are filed and labelled **descriptive**, and
the report says they may not be cited against capture 6. **What it would take to
make them a benchmark measurement** is an `A B A B` interleave per rung — the
shape the 2026-08-28 run used for B5 — which is a different driver and roughly
the same wall clock.

⚠ **The one comparison that survives the caveat is the SHAPE**: all three arms
grow sub-linearly in corpus size and none of them changes order of magnitude
across a 357× range. That is worth knowing and it is not a p50.

🔴 **And v1 is fastest while doing less** — four fewer documents, no confidence
band, no anchor branch. **Faster is not better when the arms are not doing the
same work**, which is the same sentence capture 2 needs and for the same reason.

## 3 · v1 is a different product, not an older engine

**Diagnosis.** Two facts, both measured before the run and both structural:

- **v1 indexes `.md` and `.txt` only.** 4 of 28 seed documents are invisible to
  it, on all eight builds. `02-sensor-thresholds.yaml` alone is the primary
  target of **8 of the 43 id-queries**.
- **v1 has no `tune.toml`** — no `b`, no field weights, no knobs at all.

**Change, specific:** every `v1 → *` claim in the report is worded end-to-end,
and the phrase *"v2 ranks better than v1"* is named as wrong on its face.

⚠ **This is the clause the pre-registration's §7 exists for**, and it was
classified **before** any row: the adaptation is *part of the arm*, not a defect
to patch. Forcing v1 to read `.yaml` would measure an engine nobody shipped.

🔴 **The consequence for phase D, and it is the reason this section exists:**
when the key opens, **a v1 `hit@k` will be structurally depressed** by every
question whose answer lives in one of those four documents. **That is not v1
ranking badly.** Phase D must either report v1's `hit@k` beside the count of
structurally-unreachable questions, or restrict the v1 pair to questions whose
`relevant` set excludes them — and **which of those it does is a choice to make
before the number exists**, not after.

## 4 · The null control is the only thing here that could have failed

**0 of 374.** It is reported as a pass in one line, and it deserves more than
one: it is the sole assertion in this run with a stated way to be wrong.
Everything else is a count.

⚠ **What it does NOT cover:** it ran on `rung-00500` with v1 only. A
nondeterminism that appears only at 10 000 documents, or only in v2's confidence
band, would not have been caught. **Cheap enough that nobody skips it** was the
pre-registration's reason for that rung, and the gap is the price.

## 5 · The `mtime` asymmetry, still live and still declared

`arm_corpus.py` commits every document at **one stamp**; the frozen rungs date
each file. `mtime` is a **tie-break** in v2 and HEAD (`superseded → recency →
priority → id`), so a flat-`mtime` corpus collapses the recency tie-break into
the `id` tie-break.

- **`v1 → v2` is unaffected** — both flat, symmetric.
- 🔴 **`v2 → HEAD` and `v1 → HEAD` carry it**, because HEAD's rows come from the
  dated frozen rung.

**With `b` moving between v2 and HEAD, the tie-break is a second-order effect
here** — ties are rare and `b` reorders far more than ties do. **It is recorded
rather than dismissed** because phase D computes `hit@k` from these same rows,
and a `hit@1` decided by a tie is decided by this.

**The remedy, named:** re-run HEAD through `arm_corpus.py` (5 984 calls) so all
three arms share a flat-`mtime` corpus. Not taken, because HEAD's rows already
exist at the frozen sha and phase A is the run that owns them.
