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

**Headroom (ADR-RS decision 22, ratified 2026-09-11).** This run's report states,
per endpoint and **per direction**, how many queries could have changed, labelled
observed / proven / unproven. **0 headroom in a direction is Inconclusive, not
*no detected change*.** Written under the rule, not retrofitted to it.

## Definition of done

- [x] **`bench.py quality --tune TABLE.KEY=VALUE`, repeatable — landed
      2026-09-05.** One flag rather than the two the spec asked for: `--tune`
      plus a separate `--value` cannot express two keys at once, which T3's
      joint candidate set needs. Written **before the warm-up**, so no query in
      a row file was asked under a different setting; **refuses to score if the
      committed index moved** (T0.b, enforced per pass); omitting it **deletes**
      `tune.toml` rather than writing an empty one; every row carries `tune`
      and `index_sha`. Smoke on `t100`, 240 paired queries, rows deleted —
      **no number from it is a result.**
- [ ] `bench.py` still owes: a `playground` pass emitting one row per golden,
      `select` (the frozen rule), `veto` (broken / fixed / XPASS by qid),
      `difflaw`.
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

- 🔴 **Per-query rows from the playground** — `check.py`'s `grade()` already
  returns `{id, state, detail}` per golden and writes none of it, so this is a
  `--rows <path>` writer and nothing more. **It is not written, and the reason
  is not difficulty:** that repo has 74 files staged with its index staged as
  deletions and no commit since 2026-08-20, and adding a change to a pending
  commit that is Arpit's (R-11) is not a session's call. **Unblocks the moment
  he commits or restores it.**
- ~~The `--tune` switch and index-hash assertion do not exist in `bench.py`.~~
  **Landed 2026-09-05** — see the definition of done above.
- ⚠ **`rerank_weight` moves two mechanisms since W-108**, and T1 now says so:
  T1.a/T1.c read `ask` rows and do not fetch, so **T1.d is the exposed leg** and
  its verdict owes the sentence. Re-derived in code, written before any pass.

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

## From OPEN-WORK (moved 2026-09-11)

*Moved here verbatim when OPEN-WORK became one-to-two-line rows (Arpit, 2026-09-11). Links are rewritten for this directory.*

*This is what the queue said at the move. Re-derive it before believing it (OPEN-WORK rule 4).*

- **W-97** · `agent`, blocked on W-136 · *(record: [ADR-TUNE](../../docs/adr/0135_tuning.md) ·
  [ADR-RS](../../docs/adr/0133_predictions.md))* · **the knob sweep — which
  `.fux/tune.toml` defaults are defensible, measured rather than argued.**
  Pre-registered as [`benchmark/PRE-REGISTRATION-TUNER.md`](../benchmark/PRE-REGISTRATION-TUNER.md)
  (ids **T0–T5**, a third id space), procedure in
  [`benchmark/RUNBOOK-TUNER.md`](../benchmark/RUNBOOK-TUNER.md). Three legs per
  knob — the generated suite **selects**, the hand-graded playground **vetoes**
  (bar: 0 broken; `q022`/`q033` named in advance for `superseded_weight`), a
  latency fence **prices**. Output is a **candidate table with no
  recommendation**; the change stays an ADR-TUNE amendment Arpit ratifies.
  Scope is `rerank_weight` and `superseded_weight` only — `k1`/`b`, field
  weights and recency have no instrument with headroom (§6 lists the generator
  kinds owed).

  🔴 **Under [L9](../../docs/adr/0011_LAW-9-environments.md), nothing here is runnable today.** T1's 13/37 headroom was
  measured on the playground, which is no longer an instrument, and the generated
  selection suite is not golden test data. **Every leg moves to fux-lab golden data
  (W-136) under a new pre-registration that supersedes the frozen one** — the
  latency fence may run in fux-benchmark, which is its job. The tooling
  (`bench.py quality --tune`, per-query rows) carries over.

  🔴 **T2 (`superseded_weight`) cannot run**: the knob moves **0 of 50** goldens
  at every value on that corpus, because it declares no `supersedes:` key
  ([the run](../regression/2026-09-11-four-priors-headroom/report.md)). **The named
  veto queries `q022`/`q033` cannot be broken by a knob that reaches neither.**
  T2 waits on the golden data's superseding pairs — [prompt 1](../golden/prompts/1-codex-seed.md) part A §3, which absorbed prompt 1b on 2026-09-12 (Arpit ruled **(b)**, 2026-09-11).

  ⚠ **`rerank_weight` moves TWO mechanisms, not one** — since W-108 it also
  scales the refer plane's passage proximity, which this sweep's design assumed
  it did not. T1.a/T1.c read `ask` rows and do not fetch, so **T1.d's veto is the
  exposed leg**; the bar is unchanged and the verdict owes that sentence.
  ⚠ **`expand_weight` ships at `0.2` (Query2doc's 1:5) and is untested** —
  [W-109's gate](../regression/2026-09-05-expand/report.md) ran every arm at that one
  value. It is in §1's defaults table and §6's out-of-scope table, and **it cannot
  join this sweep: no suite here passes `--expand`**, so no query can move it. —
  — [detail](W-97-tuner-knob-sweep.md) `filed: 2026-08-28`

## Unblocked 2026-09-12 — and the endpoint now has to be named

The golden ladder is built to rung 1 000. Before sweeping `superseded_weight`,
read [the run's analysis](../regression/2026-09-12-golden-ladder/ANALYSIS.md) §2:
**the document plane inverts a declared supersession about half the time while
`fux answer` recovers it on the same question.** A sweep that does not name its
endpoint measures two different things and averages them.

The inversion count is **key-free**, so that arm is not contaminated by
[W-145](W-145-codex-regenerates-the-key.md). Anything scored against the key is.

## ✅ SWEPT 2026-09-12 — the candidate table, with no recommendation

Both in-scope knobs were swept on golden data under a new pre-registration that
**supersedes the frozen `PRE-REGISTRATION-TUNER.md` (T0–T5)** for them, exactly
as this file said should happen once L9 removed the playground as an instrument:
[the run](../regression/2026-09-12-priors-and-tables/report.md) §1, [the verdict](../regression/2026-09-12-priors-and-tables/VERDICT-W143.md).

| knob | result |
|---|---|
| `superseded_weight` | **No value clears `0 broken`.** `0.9` clears on `rung-00100` and breaks on `rung-seed` (`p07`) and `rung-01000` (`p15`); net +1 |
| `rerank_weight` | Net **+1** at `rung-01000`, **no effect at any value** on `rung-00100`, breaks one probe on `rung-seed`. The same evidential position the hold already rests on |

- ✅ **The endpoint is named, as this file's 2026-09-12 note required.** The
  document plane and the passage plane disagree on supersession, so the sweep
  states that it measures the **document plane** — `fux ask`'s ranked list —
  and nothing else.
- ✅ **The playground per-query-rows blocker is moot.** It was blocked on Arpit
  committing that repo; the measurement moved to golden data and does not need it.
- 🔴 **Output is a candidate table with NO recommendation**, as the goal states.
  **Lane is now `arpit`**: a default change is an
  [ADR-TUNE](../../docs/adr/0135_tuning.md) amendment he ratifies.

⚠ **T3's joint candidate set and T4's latency fence did not run.** Neither is
answerable while no single candidate survives its own knob, and the latency
fence belongs in fux-benchmark ([W-139](W-139-benchmark-per-l9.md)) under L9.
