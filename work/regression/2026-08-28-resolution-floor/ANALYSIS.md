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

- **The reranker's `28 → 32` uplift** (2026-08-24) is a net of **4**.
  ⚠ **CORRECTED 2026-08-28.** This bullet first read *"clears α only if exactly
  4 queries flipped and all 4 went the same way"*, and that is **wrong** — four
  flips all one way gives **p = 0.125**. **A net of 4 cannot clear α at any
  discordant count**; nets of 1–5 are all impossible, with best achievable
  p-values of `1.00`, `0.50`, `0.25`, `0.125`, `0.0625` (every split to `n = 50`
  exhausted). ⚠ **The error was in the GENEROUS direction** — it left the claim
  alive as *"unverifiable from what was filed"* when the arithmetic settles it
  without the missing count. `evidence/table.txt` in this same run already said
  `4 → impossible`; **the prose disagreed with the evidence sitting beside it**,
  which is the failure mode this project files evidence to prevent.
- **Enrichment's `+9` and the blind `+1 / −1`** (W-78) are in the same position,
  and the `+9` already had its own standing correction.
- **Every "no detected change" ruling** used a bar 3–8× too permissive — but in
  the *safe* direction: calling something undetectable under a loose bar stays
  true under a stricter one. **The losses are one-sided, and they are on the
  claims of improvement.**

⚠ **The single cheapest fix for future runs is a reporting change, not a
threshold change: report the discordant count.** Without it a paired result
cannot be tested at all, and no run this project has filed reports one.

🔴 **RULED 2026-08-28, and Arpit went further:** *"adopt it and next time record
all the questions so we can check in detail."* The obligation is **per-query
results under `evidence/`** — one row per query per arm — not a discordant
count. Strictly stronger and no harder to produce: `b`, `c`, the discordant
count and any later test all fall out of per-query rows, and out of nothing
else. Carried as a numbered rule in `CLAUDE.md` §Conformance runs.

## 3 · Why the rule of thumb was the wrong shape, not just the wrong number

*"±2 on a 50-query set"* implies the bar depends on the set size. **It depends on
how many queries flipped** — 4 flips make *nothing* detectable, 50 flips need a
net of 16. A fixed number cannot express that, so replacing `2` with `8` would
be a better wrong answer.

## 4 · Unresolved

- ✅ ~~**Whether to adopt this as the rule**, and what to do about §2's claims.~~
  **RULED 2026-08-28 (Arpit): adopted, plus per-query recording. §2's claims are
  MARKED, not re-judged** — they were filed under a bar since shown to admit
  chance, and their claims of improvement are not supported by what was filed.
  None can be re-run: W-78's corpora went in the 2026-08-20 lab wipe with their
  generator.
- **α is conventional, not derived.** `0.05` is stated as a choice.
- **Detectability is not generalisation.** A cleared floor still says nothing
  about 10 000 documents.
