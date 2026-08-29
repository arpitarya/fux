---
type: OpenItem
id: W-97
title: "W-97 — the knob sweep: which .fux/tune.toml defaults are defensible, measured"
description: "Two 2026-08-28 runs found every ranking prior HEAD added ships as a no-op and correctly refused to recommend a default from a generated corpus. This item is the instrument that can carry the question one step: a pre-registered sweep where the generated suite selects a candidate, the hand-graded playground vetoes it, and a latency fence prices it. Output is a candidate table with no recommendation; the default change stays Arpit's ADR-TUNE amendment."
status: open
lane: agent
timestamp: 2026-08-28T00:00:00Z
---

# W-97 — the knob sweep over `.fux/tune.toml`

**Model: Sonnet** for the harness additions and every grid pass — specified
work with a mechanical gate at each step. **Opus** for `ANALYSIS.md`, the
verdicts, and the moment T2's veto returns anything other than what was
predicted.

## The spec this implements

**[`../benchmark/PRE-REGISTRATION-TUNER.md`](../benchmark/PRE-REGISTRATION-TUNER.md)**
— frozen, `type: PreRegistration`, ids **T0–T5**. The procedure is
[`../benchmark/RUNBOOK-TUNER.md`](../benchmark/RUNBOOK-TUNER.md). Nothing in
this file restates a bar.

## Goal

For `rerank_weight` and `superseded_weight`: is there a value with **three
green legs** — gain on the suite that isolates it (fresh seed, `p < 0.05`,
`b > c`), **zero broken hand-graded goldens**, and an affordable cost — and
what is it? Hand Arpit that table. **Do not recommend.**

## Definition of done

- [ ] `bench.py` gains `--tune <table.key> --value <v>` (write, run, restore,
      hash the index before and after), a `playground` pass that emits one row
      per golden, `select` (the frozen rule), `veto` (broken / fixed / XPASS by
      qid), `difflaw`.
- [ ] Pre-registration §1 carries the frozen sha; committed before the first pass.
- [ ] T0 gates pass; baselines filed before any knob pass.
- [ ] T1, T2 grids run as frozen; candidates selected once by the frozen rule.
- [ ] T4 on the laptop or filed `not measured`.
- [ ] `work/regression/<date>-benchmark-tuner/` filed under the per-run
      contract, `classification: informed`, `VERDICT-T1.md`, `VERDICT-T2.md`,
      the candidate table, the deck.
- [ ] Post-run: this row deleted, file to `archive/open/`; one `arpit`-lane
      row per passing candidate, pointing at ADR-TUNE.

## Blockers

- **Per-query rows from the playground** — `check.py` emits totals; the filing
  gate needs rows. Same emitter gap as OPEN-WORK's *Measurement plumbing*.
- The `--tune` switch and index-hash assertion do not exist in `bench.py`.

## Hazards (the ones that decide the run)

- 🔴 The generated suites reward exactly what the knobs do; `c = 0` there is a
  property of the generator. **The playground veto is the finding.**
- 🔴 `q022` / `q033` are the named breakers for `superseded_weight`. Selection
  happens once, by the frozen rule, **before** the veto — never by trying
  values until they stop breaking.
- `archived_weight` is never in the sweep (W-73's law). `[confidence]` floors
  are not ranking knobs and are out of scope.
- `k1`, `b`, field weights and recency have **no instrument with headroom**;
  §6 of the pre-registration lists the generator kinds owed before a `T6+`
  document can exist.

## Out of scope

Changing any default. Editing `tune.py`. Anything in pre-registration §6.
