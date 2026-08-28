---
type: Report
title: The ±2-query resolution floor is far too loose — a net of 6 to 16 is needed
description: "The placeholder every 'no detected change' ruling rests on says ±2 queries. A paired exact test says a net of 6-16 depending on how many queries flipped. At net 2 the p-value is never below 0.68."
classification: informed
timestamp: 2026-08-28T00:00:00Z
---

# The resolution floor, computed

**Replaces a placeholder that says it is one.** `CLAUDE.md` §Conformance runs:
*"provisionally — and this is a placeholder for a measurement, not a measurement
— nothing under ±2 queries (4 pp) on a 50-query set counts."*

> **This is arithmetic, not a run.** Two arms graded on the **same** queries is a
> **paired** comparison, so queries both arms agree on carry no information —
> only the ones that **flip** do. That is McNemar's test, and for a binary
> outcome it is an exact binomial on the discordant pairs. **No corpus, no
> engine, no model, no network** — the answer does not depend on who authored
> anything.

## The result

Smallest **net** difference `|b − c|` whose two-sided exact p clears `α = 0.05`:

| queries that flipped | net difference needed |
|---:|---:|
| 2 · 4 | **impossible** — no split clears α |
| 6 · 8 · 10 · 12 | **8** (6 at exactly 6 flips) |
| 15 | **9** |
| 20 | **10** |
| 30 | **12** |
| 50 | **16** |

## 🔴 What the placeholder allows

**At a net of 2 — the current bar — the p-value is never below 0.68.**

| flips | the placeholder's net 2 | p |
|---:|---:|---:|
| 6 | b=4, c=2 | **0.688** |
| 10 | b=6, c=4 | **0.754** |
| 20 | b=11, c=9 | **0.824** |
| 30 | b=16, c=14 | **0.856** |

**A delta of 2 queries is indistinguishable from a coin flip at every set size
this project uses.** The placeholder is not slightly loose; it admits results
that carry no evidence at all.

## ⚠ The rule of thumb is also the wrong SHAPE

**The floor is a function of the flips, not of the set size.** *"±2 on 50"*
implies a fixed bar; the real bar moves with how many queries disagreed. At 4
flips **nothing** is detectable; at 50 flips you need a net of 16.

**So a run must report its discordant count**, and no run this project has filed
does.

## What this does NOT do

- ⚠ **It re-adjudicates nothing.** Filed verdicts stand as measured, and
  **nothing supersedes a measurement except a better measurement**. This is a
  statement about a *rule*, and what to do about the rulings that leaned on it
  is a call for Arpit — see [`ANALYSIS.md`](ANALYSIS.md) §2.
- **It does not make any delta generalise.** Clearing a detectability floor says
  a result is unlikely to be chance. 50 queries over 10 documents is three orders
  of magnitude below the design point, and `CLAUDE.md` §Litmus governs that
  separately.
- **It does not choose α.** `0.05` is conventional and is stated, not derived.
  The script takes it as an argument.

## Authorship

| artifact | author | could reach |
|---|---|---|
| the derivation, the script, this report | Claude Code (Opus 5), 2026-08-28 | the goldens and prior scores — **and none of it is an input**: the result is a property of the binomial distribution |

`informed` by the classification rule, and the label is close to meaningless
here: **there is no corpus in this measurement to have been contaminated by.**
Stated rather than argued away.

## Reproduce

```bash
python3 tools/quality-controls/resolution.py        # alpha = 0.05
python3 tools/quality-controls/resolution.py 0.01
```
