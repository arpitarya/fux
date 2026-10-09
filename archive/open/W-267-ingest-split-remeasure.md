---
type: Handoff
name: W-267
description: "Re-time W-256 §8's no-change delta ingest at rung-10000 on the fixed engine (redact memoised, W-264 DoD 1), under a new freeze and the SAME pre-registered 5 s bar, so Arpit can rule B-002. Filed 2026-10-09 from his W-264 ruling."
item: W-267
filed: 2026-10-09
ball: agent
---

# W-267 — re-time the no-change ingest, so B-002 can be ruled

✅ **CLOSED 2026-10-10 — Arpit (Cowork):** *"For the time being, close this work
item and let's do some research and put a proposal."* B-002 closes on the frozen
rule's close branch (N = 4.902 s < 5 s): the dirty list stays advisory and
option D is not needed **at the 5 s bar**. Arpit's new goal — ingest of 10 000
documents in **under one second**, any language — is a separate research item,
[W-268](../../work/open/W-268-ingest-under-one-second.md). He considered a parse
cache first and dropped it: it cannot reach one second (parse is 1.42 s of
4.90 s).

**Status 2026-10-09: DoD 1–3 and 5 DONE (Claude Code, Opus 5.5). 🔴 Waiting on Arpit for DoD 4: rule B-002.**
[The run](../regression/2026-10-09-ingest-split-remeasure/report.md) gives
**N = 4.902 s** (4.894 / 4.908 / 4.902) at gen-4 rung-10000, under the 5 s bar
with no straddle. Identical root sha on all seven runs; redact 0.96 s; full/delta
1.92×. **The frozen rule's close branch** ([VERDICT](../regression/2026-10-09-ingest-split-remeasure/VERDICT.md)):
the dirty list stays advisory and option D is not needed at 10 000 documents.
SR-MAINTENANCE 1a-3 and SR-INGEST §1 are rewritten on the number and
restamped. ⚠ The margin is 0.092 s on one machine.
**The question for Arpit:** close B-002 on this number? Recommended: **yes**.
The frozen rule says close, and the margin caveat is now in both records.

**Arpit, 2026-10-09 (Cowork), on W-264:** *"go with the recommendation"* —
retire the redaction cache **and** re-measure on the fixed engine. Ratified, not
built.

**Why.** W-256 §8 pre-registered the rule for B-002: if a delta ingest of an
unchanged rung-10000 spends **< 5 s in its non-extract phases**, B-002 closes
(the dirty list stays advisory; option D is not needed at the design point); if
**≥ 5 s** and walk+parse dominate, a runtime parse cache becomes its own item.
That run measured an engine carrying W-255's `redact` regression (~6 s). After
the fix, `redact` is 1.03–1.09 s and the whole unchanged delta 5.16 s median
([ANALYSIS addendum](../regression/2026-10-04-ingest-split/ANALYSIS.md)). **The
rule's quantity is the non-extract phases, not the whole delta**, and no run has
measured it on the fixed engine under a freeze.

**Model:** Claude Code, **Sonnet** — a measurement on an existing harness.

**Records it updates:** SR-MAINTENANCE (decision 1a-3) and SR-INGEST (§1).

## Definition of done

1. A new run under `work/regression/` with a PRE-REGISTRATION committed alone
   before any number. **The bar is W-256 §8's, copied verbatim and unmoved**
   (SR-RS decision 10b): non-extract phases < 5 s at rung-10000 → B-002 closes;
   ≥ 5 s → the walk+parse share decides whether a parse-cache item is filed.
2. The 2026-10-04 harness (that run's `evidence/phase_times.py`) on the fixed
   engine: unchanged rung-10000, delta, ≥ 3 interleaved repeats, identical root
   sha; the per-phase split.
3. Report and VERDICT, `informed`. The sentences it decides — SR-MAINTENANCE
   1a-3 and SR-INGEST §1 — rewritten on the number and restamped.
4. 🔴 **Then to Arpit:** B-002 on the number — closed, or promoted to a
   parse-cache item. Inbox row filed in the same change.
5. `BACKLOG.md` B-002 row updated; WORKLOG; both suites whole.

## Out of scope

- Any redaction cache (W-264 retired it). Moving the 5 s bar.

## Hazards

- ⚠ Measure in `fux-lab`, never `fux-playground` (L9), with no other session
  loading the machine while timing (SR-WORK-SESSION decision 12).
- ⚠ Wall clock is machine-specific: compare only with runs on the same machine.
