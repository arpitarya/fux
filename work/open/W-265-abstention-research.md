---
type: Handoff
name: W-265
description: "Research item (Arpit, 2026-10-04, W-260 line 1): doc_coverage_floor came back INCONCLUSIVE (0.80 catches 12 of 21 unanswerables, p = 0.35). Deep research on how fux can better tell an unanswerable question from an answerable one — mechanisms, what the literature does, what data it needs — ending in a proposal. doc_coverage_floor stays 0.0 meanwhile."
item: W-265
filed: 2026-10-04
ball: agent
---

# W-265 — deep research: refusing unanswerable questions better

**Status: filed 2026-10-04, not started.** Research and a proposal only; **no
code, no threshold moves.**

**Arpit, 2026-10-04 (Cowork), on [W-260](../../archive/open/W-260-w256-results-to-rule.md)
line 1:** *"for the first one create a work item to do a deep research on how it
can be improved."* Meanwhile `doc_coverage_floor` stays `0.0`
([SR-CONFIDENCE](../../records/0141_confidence.md) d12's *off*), and the
[INCONCLUSIVE run](../regression/2026-10-04-doc-coverage-replay/VERDICT.md) is
recorded as the measured reason.

**His standing direction (2026-09-13):** *"if a question is not answerable it
should not be answered."*

**Model:** **Cowork**, Opus, with web research — a `research` item, never Claude Code (SR-WORK-OPEN-QUEUE rule 37a).

## What the research must cover

1. **Why `doc_coverage` alone failed:** AUC 0.60 on 374 rows; the 21 reachable
   unanswerables — what do the misses and the 61 wrongly-demoted answers have
   in common (by shape, not by reading the sealed key — use the retired open
   sets only, L11).
2. **Candidate signals**, each with how fux could compute it deterministically
   (L4: no model at query time): score gap between rank 1 and 2; the
   identifier test (an id in the question that no document holds — the
   `PROJ-126` case); term-level coverage weighted by idf; agreement between
   lexical and fielded rankings; `missing` terms the band already reports;
   combinations of these. Revisit the nine mechanisms already listed for the
   confidence band (2026-09-13) and the W-176 abstention gates.
3. **What the literature does** — query performance prediction (pre- and
   post-retrieval predictors: clarity, WIG, NQC, SCQ), unanswerability in QA
   (e.g. SQuAD 2.0-style no-answer), selective prediction / abstention — and
   which predictors are deterministic and cheap enough for fux.
4. **The data problem:** the replay had 21 reachable unanswerables against a
   20-row headroom bar. What a set needs (≥ 60 reachable unanswerables?) and
   how it is authored under SR-WORK-TESTDATA (T9 near-misses, A1 blind author)
   — the next generation, or W-257's rung.
5. **Shapes**, compared in a compare doc if more than one survives.

## Definition of done

1. `work/proposals/abstention-v2.md`, recommendation first, every claim cited
   (record line, code path, or paper).
2. A compare doc if there are several shapes; a pre-registration *outline* for
   the first measurement (not frozen — that waits on the data).
3. One 🔴 inbox row: Arpit picks. B-rows or W-items for the data it needs.
