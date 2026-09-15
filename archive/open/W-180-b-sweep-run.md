---
type: OpenItem
id: W-180
title: "W-180 — run the frozen b-sweep on the golden ladder"
description: "W-144 was ruled (d) on 2026-09-14 — sweep b over the three measured families and ship the first value positive on all with controls holding. The pre-registration was frozen 2026-09-15. What is left is the run. Filed 2026-09-15 under SR-WORK-OPEN-QUEUE 23a because W-144 was 🟡 on a run with no item behind it."
status: open
lane: agent
timestamp: 2026-09-15T00:00:00Z
filed: 2026-09-15
ball: agent
---

# W-180 — the `b`-sweep run

**Model: Opus** — it reads a measurement against a frozen bar and calls a gate.

**Why this exists.** [W-144](W-144-structure-aware-extraction.md) is fully ruled
and fully specified: Arpit took **(d) lower `b`** on 2026-09-14, and the
pre-registration was frozen on 2026-09-15 at
[`regression/2026-09-15-b-sweep/PRE-REGISTRATION.md`](../regression/2026-09-15-b-sweep/PRE-REGISTRATION.md).
Step 1 is done. Steps 2–4 are a run, and nothing in the queue was going to
produce one — W-144 sat 🟡 on *"a `fux-lab` run"*.

## Definition of done

1. Run the frozen sweep — `b ∈ {0.75, 0.6, 0.5, 0.4}`, families `dump` ·
   `content` · `main` + `inverse` · `placebo` — on the **golden ladder** in
   `fux-lab` (the verdict), and on fux's own docs tree (reopen-trigger evidence
   only, never the verdict).
2. ⚠ **The threshold may not move.** The decision rule — *first value netting
   positive on all three with controls holding* — and the
   [SR-RS](../../records/0133_predictions.md) d19 floor at the pair count
   actually run are both frozen. An ambiguous result goes to Arpit with
   per-query rows, never to whoever ran it.
3. File the verdict under `work/regression/`.
4. **On PASS:** ship the winning `b` as the `tune.toml [bm25f]` default, amend
   [SR-TUNE](../../records/0135_tuning.md) and
   [SR-RANKING](../../records/0111_ranking.md) in the same change, L3 check,
   two-reader byte equality. **On FAIL: a null closes W-144, and that is a
   success** — the proposal's own text says a ranking change here needs a
   verdict and never an argument.

## Environment

`fux-lab` — every measurement, ≤ 10 000 documents, **agents and Arpit both**
([SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md)). Agent work on
the Mac; the Cowork bridge cannot run it
(Linux/py3.10 against a macOS `.venv`).

## Closes

[W-144](W-144-structure-aware-extraction.md), either way.
