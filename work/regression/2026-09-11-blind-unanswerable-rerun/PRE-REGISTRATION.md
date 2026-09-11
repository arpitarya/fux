---
type: Pre-Registration
name: PRE-REGISTRATION-BLIND-UNANSWERABLE-RERUN
title: "Pre-registration — does the engine still abstain 0 of 20 on the blind unanswerable set?"
description: "Frozen before the first number. Re-runs the 2026-08-28 blind unanswerable measurement on today's engine. Descriptive: no threshold, no gating verdict, R10 untouched."
status: frozen
date: 2026-09-11
timestamp: 2026-09-11T00:00:00Z
---

# Pre-registration — the blind `unanswerable` re-run

**Written and committed before any number from this run exists.** That is the
whole point of the file ([`CLAUDE.md`](../../../CLAUDE.md) §"A pre-registered
threshold may never move").

## The ask

**Arpit, 2026-09-11:** run the 2026-08-28 blind unanswerable measurement again
on today's engine and report whether the finding still holds.

**The claim under test.** On 20 questions authored blind and independently ruled
unanswerable by a second blind session, the engine reported `answerable: true` on
**20 of 20** ([the 2026-08-28 run](../2026-08-28-blind-unanswerable/report.md)).

## 🔴 No threshold, and no gating verdict

**This run proposes no floor, moves no floor, and adjudicates no prediction.**

- **R10 is untouched.** It is unmeasured, and a floor fitted to the same 20
  numbers that exposed the problem is the moving-threshold failure wearing a
  different costume.
- **No `[confidence]` key is tuned** — not `separation_floor`, not the
  `doc_coverage` gate ADR-CONFIDENCE ruled off on 2026-08-28.
- **No `VERDICT.md` is filed.** There is no prediction to adjudicate. The output
  is a number and a sentence saying whether the earlier finding still holds.

## The measurement

**Command**, reused verbatim from the 2026-08-28 report's *Reproduce* block:

```
fux ask "<query>" --json --band --top 5
```

read for `confidence.answerable`, `confidence.band`, `confidence.separation`.

**Primary metric** — *count of `answerable: true`, out of 20.*
**Secondary** — the per-band counts (`grounded` / `partial` / `weak`), and the
count agreeing with ground truth (`answerable: false`).

**Pairing.** The **same 20 ids** against the 2026-08-28 values, which are frozen
in that run's `evidence/per-query.csv`. Both arms are the same queries and the
same ground truth, so this is a **paired** comparison and only the ids that
**flip** carry information ([ADR-RS](../../../docs/adr/0133_predictions.md)
decision 19).

**How a difference is read, decided now rather than after:**

- A paired net **below 6 is "no detected change"**, in either direction. Decision
  19: nets of 1–5 cannot clear α = 0.05 at any discordant count.
- The primary metric is a **single-arm count** — *is it still 20?* — and that
  question is answered by the count itself, not by a significance test. The
  paired reading above governs only the claim *"the engine got better/worse."*

## Headroom, declared in advance

[ADR-RS](../../../docs/adr/0133_predictions.md) decision 22, ratified
2026-09-11. Both directions are computable from the frozen 2026-08-28 rows
before this run produces anything:

| direction | definition | value, from the frozen arm |
|---|---|---:|
| **improvement** (more abstentions) | queries not right in both arms — here, every query the 2026-08-28 arm got wrong | **20** |
| **regression** (fewer abstentions) | queries not wrong in both arms — here, every query that arm got right | **0** |

- **Improvement headroom is 20 and is PROVEN**, by construction rather than by a
  control arm: the frozen arm answered `true` on all 20 against a ground truth of
  all `false`, so every single query has room to move in that direction.
- 🔴 **Regression headroom is 0, so a null in the regression direction is
  INCONCLUSIVE, not "no detected change"** (decision 22d). The engine cannot get
  worse on this set; it is already at the floor. **The report must say this
  rather than report a regression null as a result.**

## The environment, recorded before the run

| | |
|---|---|
| engine | `fux-engine` 2.0.0-alpha.7 at fux `94d7a76` |
| corpus | a **copy** of `fux-playground` `fece5a3`, `docs/` only — ten documents |
| queries | `2026-08-28-blind-unanswerable/evidence/unanswerable.jsonl`, **reused, never edited** |
| ground truth | `…/evidence/ground_truth.jsonl`, **reused, never edited** |
| python | 3.14.3 |
| os | Darwin arm64 |

⚠ **The corpus question is answered in the report, not assumed here.** The 20
queries are byte-identical between the frozen evidence and the playground's
`goldens/unanswerable.jsonl` (verified 2026-09-11). Whether the ten **documents**
are the same bytes the 2026-08-28 run read is a separate question and the report
states what could and could not be established.

🔴 **`fux-playground` itself is never edited by this run.** W-134 owns its index.
The run works in a copy under `~/my_programs/fux-lab`, which persists.

## Classification

**`blind`**, on the artifacts that decide anything:

| artifact | author | could reach |
|---|---|---|
| the 20 queries | a fresh session, 2026-08-28 | the ten documents and the blind-author brief — nothing else |
| the ground-truth ruling | a second fresh session, 2026-08-28 | the documents and the queries — no engine output |
| the harness, this file, the report | Claude Code (Opus), 2026-09-11 | **everything**, including the 2026-08-28 per-query values |

⚠ **The orchestrating session is informed and authors no evaluation material.**
It reuses both blind artifacts verbatim. That is the same posture the 2026-08-28
run declared, and the same limitation applies: the brief's own author was not
blind, and publication rather than trust is the mitigation.

## What this run may never be used to say

- That any threshold passed or failed. There is none.
- That R10 is measured, or that the `doc_coverage` gate should move.
- That the engine regressed on this set. **Regression headroom is 0.**
- That the goldens' relevance sets are settled — a different finding, from a
  different artifact, in the 2026-08-28 run.
