---
type: OpenItem
id: W-133
title: "W-133 — re-run the blind unanswerable set: does the engine still abstain 0 of 20?"
description: "Arpit, 2026-09-11: re-run the 2026-08-28 blind-unanswerable measurement on today's engine and report whether 0 abstentions out of 20 is still true. Descriptive only — no threshold, no gating verdict."
status: open
lane: agent
timestamp: 2026-09-11T00:00:00Z
---

# W-133 — re-run the blind `unanswerable` set

**Model: Opus** — close call. Running it is mechanical; explaining what moved
since 2026-08-28 and classifying authorship without adjudicating a gate is not.

## The ask

- **Arpit, 2026-09-11:** run it again and tell us whether it is true or not.
- **The claim under test:** on 20 blind-authored questions that a second blind
  session ruled unanswerable, the engine reported `answerable: true` on **20 of 20**
  ([2026-08-28 report](../regression/2026-08-28-blind-unanswerable/report.md)).

## What is frozen — reuse, never edit

- `regression/2026-08-28-blind-unanswerable/evidence/unanswerable.jsonl` — the 20 queries.
- `…/evidence/ground_truth.jsonl` — the blind answerability ruling.
- The command in that report's *Reproduce* block: `fux ask "<q>" --json --band --top 5`.
- 🔴 **No threshold is proposed and R10 is untouched, deliberately.** A floor fitted to
  the numbers that exposed the problem is the moving-threshold failure. Do not tune
  `separation_floor` or any `[confidence]` key.

## Definition of done

1. **Pre-register before the first number:** `work/regression/<date>-blind-unanswerable-rerun/PRE-REGISTRATION.md`
   — the command, the metric (*count of `answerable: true` of 20*, per-band counts),
   the pairing (same 20 ids vs 2026-08-28), and the sentence *"no threshold; no gating verdict"*.
   Commit it first.
2. **Environment in `~/my_programs/fux-lab`** (the lab persists — never delete or rebuild it):
   - a **copy** of the `fux-playground` tree; 🔴 **never edit `fux-playground`
     itself** — [W-134](W-134-playground-index-and-rows.md) owns its index;
   - the engine at fux `HEAD`; `fux ingest --full` in the copy, over `docs/` only.
   - Record: fux sha, a content hash of the corpus copy, Python, OS.
   - ⚠ **State whether the corpus is the one the 2026-08-28 run read.** `goldens/unanswerable.jsonl` in the playground is byte-identical to the frozen evidence. If that
     cannot be established, say so plainly — do not assume.
3. **Run** the 20 queries. `evidence/per-query.csv`: one row per query —
   `id, query, answerable, band, separation, top5_doc_ids`, plus the 2026-08-28 values beside them.
4. **`report.md`** (frontmatter `classification: blind`, authorship table: queries and
   ground truth reused from the blind sessions; harness and report `informed`):
   - 🟢 **The one-line answer first:** *"Still 0 abstentions of 20: TRUE / FALSE —
     N of 20 `answerable: true`."*
   - band table, then/now; which ids flipped, and the discordant count.
   - A paired net below [ADR-RS](../../docs/adr/0043_predictions.md) decision 19's floor
     (net 6) is **"no detected change"**, whatever direction it points.
   - What changed in the engine since 2026-08-28 that could move this (W-108, W-109,
     W-111, W-115, `[index]`) — **post-hoc, labelled, out of the answer**.
5. `ANALYSIS.md`, a row in `regression/README.md`, DOC-REGISTRY bump.
6. **Close-out:** delete the W-133 row from `OPEN-WORK.md`; **add an inbox row** —
   *"Whether the abstention result gates anything"*, `filed: 2026-08-28`, carrying the
   one-line answer and a link to the run. `IMPLEMENTATION.md` + `WORKLOG` entries; move
   this file to `archive/open/`.

## Hazards

- **Do not edit the 2026-08-28 run directory.** A re-run is a new directory.
- **Do not re-author or re-rule the queries.** A new blind set is a different run.
- ⚠ Not runnable from Cowork's bridge (Linux / py3.10 / no egress; the `.venv` is macOS-built).
- Commit only your own paths. Do not push.

## Prompt

```
Execute work/open/W-133-unanswerable-rerun.md exactly.
Read CLAUDE.md §Conformance runs and §A pre-registered threshold may never move,
then that file. Commit the PRE-REGISTRATION before producing any number.
Never edit fux-playground or the 2026-08-28 run. Lead the report with the
one-line TRUE/FALSE answer. Propose no threshold. Commit only your own paths;
do not push. Finish with the close-out list.
```
