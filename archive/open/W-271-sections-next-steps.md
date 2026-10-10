---
type: Handoff
name: W-271
description: "Arpit's ask (2026-10-10, Cowork): the next steps for section records after W-236 (B2, FAIL) and W-269 (gain-only, FAIL on the zero-loss clause, net +7 at λ 2.0). This item holds the RULINGS — the 8× record-format size question owed before W-270 freezes its bar, the two branches, the close-out on a FAIL — plus a post-hoc review of past verdicts under L13. Test data is W-272, the build W-273, the measurement W-270."
item: W-271
filed: 2026-10-10
ball: arpit
---

# W-271 — section records: what comes next

**Status: CLOSED 2026-10-10 — ruled.** **RULED 2026-10-10 (Arpit, Cowork): *"Go with the recommendation."***

- **Size (step 1): option (b)** — no section records for decoded record formats
  (`.jsonl`, `.csv`, `.json`); prose only, ≈ 1.9× on this repository. Built by
  W-273 phase 1, which amends SR-SECTIONS decision 2 first.
- **Branches (step 2):** `w236-sections` may be deleted once W-270 starts; the
  W-269 branch stays as W-273's base until W-270 rules.
- **On a W-270 FAIL (step 4):** SR-SECTIONS stays `proposed` with both FAILs
  on it, not archived, so a `b > 0.5` re-try can reopen it. Carried in W-270.
- **On a W-270 INCONCLUSIVE (step 5):** Arpit rules, per L13. Carried in W-270.

**Arpit, 2026-10-10 (Cowork):** *"create a work item for sections on what are
the next step. Sections being W269 or W236 or maybe both."* Same exchange:
law [L13](../../records/0015_LAW-13-the-standing-bar.md) was ratified, and he
asked for a review of *"all the previous work items which had failed just
because of these bar"* (§Review below).

## Where section records stand

| | mechanism | result | branch |
|---|---|---|---|
| W-236 | B2 — `S_doc + λ · best section` | **FAIL (drift)**: hit@1 45 → 39 at λ 1.0, the target pool got worse (23 → 28 misses) | `w236-sections` (`f2a139fd`) |
| W-269 | gain-only — `S_doc + λ · max(0, best section − document as one unit)` | **FAIL (drift)** on zero-loss: hit@1 45 → 52 at λ 2.0 (12 wins, 5 losses), pool 23 → 13 | `claude/gracious-galileo-aqrg8b` (`03fbf782`) |
| W-270 | gain-only at λ 2.0, decided arm, fresh `set-6-claude` | 🔴 Arpit runs prompt 14 | the W-269 build |

[`ANALYSIS.md` of W-236](../regression/2026-10-10-section-records/ANALYSIS.md)
and [W-269's VERDICT](../regression/2026-10-10-section-gain-only/VERDICT.md)
carry the evidence.

## Steps

1. 🔴 **Arpit rules the record-format size question — before W-270's DoD 3**,
   so the build W-270 measures is the build that would ship.
   On this repository the section plane is **8.0×** the document plane
   (337.5 MB against 42.1 MB): `.jsonl` 75.6 %, `.md` 23.0 %, `.json` 1.2 %
   ([W-236 ANALYSIS](../regression/2026-10-10-section-records/ANALYSIS.md) §2).

   | | option | effect on this repo's section plane |
   |---|---|---|
   | **(b) rec.** | no section records for decoded **record** formats (`.jsonl`, `.csv`, `.json`); prose only | ≈ 78 MB, about **1.9×** the document plane (`.md` 77.7 MB + the rest 0.6 MB). The golden ladder holds none of these formats, so W-270's ranking numbers are unchanged |
   | (a) | accept it | 42 → about 380 MB, in git history for good |
   | (c) | a fixed per-document section cap | a constant whose value is a guess (SR-TUNE d6 keeps a tunable out of committed bytes) |

   (b) is an SR-SECTIONS decision 2 amendment plus a small build change —
   [W-273](W-273-section-records-implementation.md) phase 1.
2. **The two branches.** `w236-sections` holds only the failed B2 term and is
   superseded by the W-269 branch, which merged it. Keeping or deleting it is
   Arpit's (both FAIL verdicts give him the branch). The W-269 branch is the
   base of [W-273](W-273-section-records-implementation.md)'s build and stays
   until W-270 rules.
3. **On a W-270 PASS** — the ship path is
   [W-273](W-273-section-records-implementation.md) phase 2.
4. **On a W-270 FAIL** — step 10 closes as measured on two sets. SR-SECTIONS
   either stays `proposed` with both FAILs on it, or is retired and archived
   under [L1](../../records/0003_LAW-1-retired-records-archived.md): Arpit's
   call. Both branches go with it.
5. **On a W-270 INCONCLUSIVE** — Arpit rules, per L13 decision 4.

**The work items, after the 2026-10-10 split:** this item (rulings) ·
[W-272](W-272-section-test-data-gen5.md) (test data) ·
[W-273](W-273-section-records-implementation.md) (implementation) ·
[W-270](W-270-section-retest-set-6.md) (the measurement).

## Review — past verdicts read under L13 (post-hoc, decides nothing)

L13 decision 1: a frozen run keeps its bar, and reading it under L13 is
post-hoc. Read from each VERDICT's filed counts. **Only one run failed on the
bar alone.**

| run | filed verdict | read under L13 | why |
|---|---|---|---|
| W-269 gain-only, λ 2.0 (2026-10-10) | FAIL drift | **INCONCLUSIVE** | C1 ✅ (pool 10 / 0), C3 ✅ (+7), C2 ❌ by 1 (non-pool 2 wins / 5 losses) → W-270 |
| W-269, λ 0.5 and 1.0 | FAIL drift | FAIL guardrail | pool net +2 / +4 is positive but below the floor, C2 −1 and C3 > 0 — but the `grounded` band fell 44 → 41 / 40, past the −2 guardrail |
| W-236 B2 (2026-10-10) | FAIL drift | FAIL | C3 fails (hit@1 down at every λ) and the pool got worse |
| RM3 (2026-09-23) · RM3 boosted (2026-09-25) | FAIL | FAIL | tagged nets −1 to +3 against a floor of 7–10, and 6–13 rank-1 losses |
| authority prior (2026-09-28) | FAIL | FAIL | nets +1 to +3 against 7–12, losses 2–10 |
| RM3 grounded-only (2026-09-30) | FAIL no gain | FAIL | no positive net |
| enriched rung, doc2query (2026-10-10) | FAIL | FAIL | net +2 where 8 was needed |
| identifier analyzer (2026-09-21) | INCONCLUSIVE | FAIL no gain or INCONCLUSIVE | nets within ±5, no floor cleared |
| proximity rerank b2 (2026-09-16) | FAIL | FAIL | net −40 |
| `b` sweep 1 (2026-09-15) | FAIL | FAIL | nothing moved; sweep 2 shipped 0.15 |
| supersession prior (2026-08-25) · four priors W-143 (2026-09-12) | FAIL | FAIL | 2 fixed / 2 broken; no gain on the probes |
| dense lane (2026-08-24) | FAIL | FAIL | 0 fixed |

Not ranking changes, so outside L13: the pruning gate, hook latency, merge
driver, separation floor, the doc-coverage abstention floor, the ingest split
and the Node graph speed runs.

## Records this will touch

SR-SECTIONS — its status on a W-270 FAIL (step 4). The build's record changes
are [W-273](W-273-section-records-implementation.md)'s.

**Model:** the rulings are Arpit's.
