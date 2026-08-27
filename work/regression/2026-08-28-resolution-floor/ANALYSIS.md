---
type: Analysis
title: What a too-loose floor costs, and which filed claims it puts in question
description: The bar admits coin flips. Two filed uplifts sit under the real threshold, and re-judging them is Arpit's call, not this run's.
timestamp: 2026-08-28T00:00:00Z
---

# Analysis — the resolution floor

## 1 · The defect, stated plainly

**A net of 2 queries has a p-value of 0.68 to 0.86.** The placeholder does not
merely under-protect; **it admits results that are indistinguishable from
chance**, at every set size this project uses.

**Repro:** `evidence/resolution.py`.

## 2 · 🔴 Which filed claims this puts in question

**Named, not re-judged.** *Nothing supersedes a measurement except a better
measurement*, and this is arithmetic about a rule.

- **The reranker's `28 → 32` uplift** (2026-08-24) is a net of **4**. Under the
  real test that clears α only if **exactly 4 queries flipped and all 4 went the
  same way**. The run does not report its discordant count, so **it cannot be
  checked from what was filed.**
- **Enrichment's `+9` and the blind `+1 / −1`** (W-78) are in the same position,
  and the `+9` already had its own standing correction.
- **Every "no detected change" ruling** used a bar 3–8× too permissive — but in
  the *safe* direction: calling something undetectable under a loose bar stays
  true under a stricter one. **The losses are one-sided, and they are on the
  claims of improvement.**

⚠ **The single cheapest fix for future runs is a reporting change, not a
threshold change: report the discordant count.** Without it a paired result
cannot be tested at all, and no run this project has filed reports one.

## 3 · Why the rule of thumb was the wrong shape, not just the wrong number

*"±2 on a 50-query set"* implies the bar depends on the set size. **It depends on
how many queries flipped** — 4 flips make *nothing* detectable, 50 flips need a
net of 16. A fixed number cannot express that, so replacing `2` with `8` would
be a better wrong answer.

## 4 · Unresolved

- **Whether to adopt this as the rule**, and what to do about §2's claims.
  Arpit's — it changes how filed results read.
- **α is conventional, not derived.** `0.05` is stated as a choice.
- **Detectability is not generalisation.** A cleared floor still says nothing
  about 10 000 documents.
