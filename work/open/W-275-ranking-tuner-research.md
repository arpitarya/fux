---
type: Handoff
name: W-275
description: "Research item (Arpit, 2026-10-11): is there a tool that can tune fux's ranking knobs (b, k1, the field weights, section_weight), or can one be built? Survey what exists, what fux already has, and propose a tuner that trains on the retired open sets and ships nothing except through law L13 on a fresh sealed set. No code."
item: W-275
filed: 2026-10-11
ball: agent
---

# W-275 — research: a tuning tool for the ranking knobs

**Status: filed 2026-10-11, not started.** Research and a proposal only; **no
code, no knob moves, no record change.**

**Arpit, 2026-10-11 (Cowork),** after asking whether long documents are
penalised today (they are, lightly: `b = 0.15`): *"Is there a tool which can
help with tuning these parameters? Or can it be built? Create a work item,
research work item for this."*

**Model:** **Cowork**, Opus, with web research — a `research` item, never
Claude Code ([SR-WORK-OPEN-QUEUE](../../records/0051_WORK-open-queue.md) rule 37a).

## Why now

- **Every knob so far was tuned by hand, one pre-registered run at a time.**
  `b` went 0.75 → 0.15 through two hand sweeps
  ([W-144](../regression/2026-09-16-b-sweep-2/VERDICT.md)); `section_weight`
  took three full runs (W-236, W-269, W-270) to learn it does not pay.
- **Most of `.fux/tune.toml` is still unmeasured.** Its own comments say
  `heading`, `title`, `path` and `ctx` are *"defensible starting points, not
  measured optima"*. `k1 = 1.2` is inherited. No `b` below 0.15 was tried.
- **The 2026-08-22 note already argued the shape.**
  [`work/proposals/ranking-tuning.md`](../proposals/ranking-tuning.md)
  (graduated 2026-10-03): build the *instrument*, not the optimiser; k1/b
  tuning usually buys ~nothing (Anserini Robust04: 5-fold CV recovers the
  default); judgment supply is the binding constraint. The instrument now
  exists (the golden ladder, `golden_run.py`, `tools/golden-score`, the
  PRE-REGISTRATION/VERDICT discipline). **The optimiser was never built.**
- **The judgment supply changed.** Sets 1–3 are retired into
  `work/golden/retired/` — **374 questions with committed expected answers**,
  open to any session (L11), which clears the note's 73-topic bar.

## What the research must cover

1. **What exists outside fux.** Anserini/Pyserini grid regressions, RankLib
   coordinate ascent, `ir_measures` / `ranx` / `trec_eval`, Optuna (the note
   rejected it on cost regime — re-check), OpenSearch Search Relevance
   Workbench, Vespa's match-phase evaluator. For each: licence (L2: OSI, by
   SPDX), and whether it can sit in `tools/` as lab tooling without becoming a
   runtime dependency.
2. **What fux already has that a tuner would reuse:** `golden_run.py` arms,
   the W-144 sweep harness, `decide.py`'s paired-flip rule, `fux tune` (prints
   the file — the verb name is spent), `fux serve`'s Words tab.
3. 🔴 **Data and custody — the binding constraint.**
   - **Train on the retired sets only.** A tuner never touches a sealed set,
     never runs `score.py` (L11: Arpit's hand only), and a set it tuned on may
     **report** a knob, never **decide** it (L13).
   - **Decide on a fresh sealed set**, one arm named before any number, under
     L13 — the tuner's output is a *candidate*, never a shipped value (L12: it
     proposes a `tune.toml` line; it does not write one).
   - Do the retired sets' expected documents still exist in the generation-5
     ladder? If not, what a re-mapping costs.
4. **Speed — which knobs need no re-ingest.** `k1`, `b`, the field weights,
   `anchor` and the `[ranking]` rerank knobs are query-time (`Scoring`), so a
   tuner can **freeze each query's candidate set once and rescore it** —
   thousands of evaluations in seconds. `section_records` needs a re-ingest.
   Estimate evaluations per second at `rung-01000` and `rung-10000`.
5. **Guards against tuning noise** (the note's §5): cross-validation across
   sets, the plateau fraction, the 1-SE tie-break toward the current value, a
   sample-size sentence, and paired flips against
   [SR-RS](../../records/0133_predictions.md) decision 19's floor.
   **"No setting beat the current one" must be the designed, common outcome.**
6. **Report every endpoint, never one number:** `hit@1` (L13's endpoint),
   `hit@5` / `hit@10` (what the refer plane re-scores), `primary@1`, MRR, and
   **per pool** — `step10_section` vs `other`, because sections showed a gain in
   one pool is paid for in the other.
7. **A length diagnostic.** `hit@1` by document-length bucket — the direct
   answer to *"are long documents penalised?"* — so a `b` change shows whom it
   moves.
8. **Which knobs first**, ranked by expected value (the note's §6, updated):
   field weights (unmeasured), `b` below 0.15, `k1`, then the graph and rerank
   knobs.
9. **The tool's shape:** a lab tool in `tools/` only (nothing shipped, L10
   untouched) versus a consumer verb (needs a new name; SR-CLI). Where its runs
   are filed (SR-RS decision 10a).

## Definition of done

1. `work/proposals/ranking-tuner.md`, recommendation first, every claim cited
   (record line, code path or paper). It builds on, and does not restate,
   `ranking-tuning.md`.
2. A compare doc if more than one shape survives.
3. A pre-registration **outline** for the first sweep (not frozen).
4. One 🔴 inbox row: Arpit picks. Build items filed after, in `fux build`.

## Records

**No SR affected by this item** (rule 38). A build it leads to would touch
[SR-TUNE](../../records/0135_tuning.md), [SR-RANKING](../../records/0111_ranking.md),
[SR-RS](../../records/0133_predictions.md),
[SR-WORK-GOLDEN](../../records/0066_WORK-golden.md) (a tool reading retired
sets), and [SR-CLI](../../records/0101_cli-surface.md) only if it becomes a verb.
Laws in play: L2, L4, L11, L12, L13.

## Reference

- [`work/proposals/ranking-tuning.md`](../proposals/ranking-tuning.md) — the 2026-08-22 note.
- [W-144 b-sweep VERDICT](../regression/2026-09-16-b-sweep-2/VERDICT.md).
- The section sweeps, for the per-arm `hit@1/5/10` this tool would automate:
  [W-236](../regression/2026-10-10-section-records/report.md) ·
  [W-269](../regression/2026-10-10-section-gain-only/report.md) ·
  [W-270](../regression/2026-10-11-section-retest-set-6/report.md).
