---
type: Pre-registration
description: "W-232's second bar: the same three arms (A anchor 1.0 + mined 0.5, B 1.0 + 0.0, C 0.0 + 0.5) on set-3-claude (was set-3-u, the set step 4 was measured on, with 22 expansion_form questions), at a copy of step 4's own mx-base (the generation-2 rung-01000 at 9cdde333, re-ingested v5). The first bar STOPped because set-4-claude cannot reach the mined fold. Endpoint hit@1 on all 80, keep-rule significance, as Arpit ruled 2026-09-28. Written before any arm on this set exists."
run: 2026-09-28-anchor-mined-set3
item: W-232
filed: 2026-09-28
measured: "not yet"
classification: informed
status: frozen
---

# Pre-registration: the shipped pair on `set-3-claude`, W-232 (second bar)

## Why a second bar

[The first bar](../2026-09-28-anchor-mined/PRE-REGISTRATION.md) named
`set-4-claude` and **STOPped at its precondition**. `am-B` equals `am-A` on all
125 questions, because no question in that set carries a mined `Term (ABBR)`
form ([report](../2026-09-28-anchor-mined/report.md) §3). **Arpit, 2026-09-28:**
*re-run on set-3-u*, the set step 4 was measured on. That bar is closed, not
moved: this file is new, and every clause of the first bar that is not named
below carries over **verbatim**.

## What changes from the first bar, and nothing else

| | first bar | this bar |
|---|---|---|
| question set | `set-4-claude`, 125 | **`set-3-claude`** (renamed from `set-3-u` on 2026-09-27; ids `s3u-…` unchanged), **80** questions, sha256 `851b3550aff47c621f617fb12c5b5227bf4045dfae18ac08a7e45826e745fba9`. This is the hash step 4's bar froze |
| corpus | copy of gen-3 `rung-01000` at `b73348d5` | **copy of `fux-lab/arms/runs/mx-base/rung-01000`**: the gen-2 `rung-01000` at `9cdde333`, re-ingested `--full` at `f8b21bd5` by step 4's build (`fux.index.v5`, index hash `3b82fb39…`). `9cdde333` no longer exists in the rung's own history, because the gen-3 rebuild replaced it. `mx-base` is the only copy of it left, so it is **copied with `cp -a` and never written to** |
| arm values | both keys edited from the rung's shipped pair | the copy's tune pins `anchor = 0.0`, and carries **no** `mined_weight` line. **Every arm writes both keys explicitly**, after `doctor --fix` |
| decider | `evidence/decide.py` | the same file, with only `SET` and two docstring lines changed ([`evidence/decide.py`](evidence/decide.py), hash at §Freeze) |

The arms, the endpoint, the keep-rule table, the headroom reading, the two
directions and §What this run may NOT do are the first bar's, verbatim.
In short:

| arm | `anchor` | `mined_weight` |
|---|---:|---:|
| **`am-A`** | **1.0** | **0.5** |
| `am-B` | 1.0 | 0.0 |
| `am-C` | 0.0 | 0.5 |

**Per comparator `X` ∈ {B, C}, on `hit@1` over all 80:** **FAIL** if
`verdict.rule` finds `X` better at the observed discordant count. **INCONCLUSIVE**
if losses > wins below the floor, or if `X` has no rank-1 hit. **PASS** if
losses ≤ wins, 0 / 0 included. The run is PASS if both comparisons pass, FAIL
(to Arpit) if either fails, and INCONCLUSIVE (to Arpit) otherwise.

**Held for every arm:** the index, every other key `doctor --fix` leaves on the
copy (including the copy's graph tier and `intent_weight` at the template
value), **no `[doctype]` table**, the corpus, the questions and one engine
commit: **the commit that freezes this file**, from a detached worktree.
If that engine refuses `mx-base`'s v5 index, the base copy is re-ingested
`--full` **once**, before the arms fork, and the report says so.

## Precondition, as the first bar

`am-A` vs each comparator must change **some** question's top-10 order.
🔴 **STOP otherwise**, and a STOP is a data defect, not a pass.

**Beside it, gating nothing:** the wins and losses restricted to step 4's 22
`expansion_form` questions, read from step 4's frozen tag file
(`2026-09-27-mined-expansion/evidence/tags-set-3-u.jsonl`, sha256
`d025cb6e…083f45bf7b`) and never re-tagged.

⚠ **Declared:** this session has seen the first bar's capture (rankings only,
no score) and step 4's filed verdict. It has seen no ranking of any arm on
`set-3-claude` at `anchor = 1.0`.

## Freeze, filled before the commit that freezes this file

| | |
|---|---|
| `set-3-claude.jsonl` sha256 | `851b3550aff47c621f617fb12c5b5227bf4045dfae18ac08a7e45826e745fba9` |
| `evidence/decide.py` sha256 | `7fb7ab4d55f80e14d2cba491dd53b563a442d25606127c614ccc37d3f83c5abc` |
| source copy | `arms/runs/mx-base/rung-01000`, git head `9cdde33`, with step 4's `--full` re-ingest in its working tree |
| step 4's tag file sha256 | `d025cb6ea9e72e1bc1b10cc8a99d25edbe94d6e05fe54e6668de0f083f45bf7b` |
