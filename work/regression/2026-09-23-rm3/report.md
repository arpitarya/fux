---
type: Report
description: "The five RM3 arms of W-168 step 5 — `rm3_weight ∈ {0.0, 0.1, 0.2, 0.3, 0.5}` — captured on `set-2-u` at `rung-01000`, one engine commit (`36c913c7`), one index root (`17fe414e…`). Hand-offs only: no score and no verdict exist yet. RM3 changes the rank-1 document on 17 to 48 of 125 questions, rising with the weight."
run: 2026-09-23-rm3
item: W-168
classification: informed
filed: 2026-09-23
pre_registration: work/regression/2026-09-23-rm3/PRE-REGISTRATION.md
---

# REPORT — RM3 arms captured, `set-2-u`, `rung-01000`

🔴 **Captured, not scored, and not decided.** No key reached this session.
*Changed* below means **the ranking moved**, never *improved*. The verdict comes
from [`evidence/decide.py`](evidence/decide.py), run on Arpit's scores by a
session that **did not** run these arms (pre-registration §What this run may
NOT do, item 5).

## 1 · What ran

| | |
|---|---|
| engine | `36c913c7` — the build, one commit for every arm |
| index root | `17fe414e52d2…` on every arm copy, checked before the first call |
| engine re-ingest check | a throwaway copy re-ingested at `36c913c7`: **0 shards written, same root**, so this engine produces the index the arms queried |
| arm copies | `~/my_programs/fux-lab/arms/runs/rm3-<w>/rung-01000`, `cp -a` of the frozen rung; each `tune.toml` differs from the rung's **only** by `rm3_weight` |
| harness | `golden_run.py --sets 2-u`, `ask --json --band --why --top 10` + `answer --json`, no `--expand` |
| questions | 125 per arm; funnel gates captured on 125 of 125 in every arm |

## 2 · What each arm did — descriptive, `k = 10`

From [`evidence/describe.py`](evidence/describe.py) → `describe.json`:

| arm | rank-1 changed | of which tagged | order changed | membership changed | median `ask` ms | bands (grounded / partial / weak) |
|---|---:|---:|---:|---:|---:|---|
| `rm3-0.0` | — | — | — | — | 156 | 42 / 59 / 24 |
| `rm3-0.1` | 17 | 10 | 121 | 102 | 184 | 44 / 59 / 22 |
| `rm3-0.2` | 28 | 18 | 125 | 115 | 212 | 44 / 59 / 22 |
| `rm3-0.3` | 37 | 25 | 125 | 119 | 228 | 38 / 59 / 28 |
| `rm3-0.5` | 48 | 33 | 125 | 122 | 219 | 30 / 59 / 36 |

- **The mechanism fires on this set.** It is not the anchor field's
  `0 of 124 flips`: rank 1 moves on 17 questions even at `0.1`.
- **It moves untagged questions too** (7 at `0.1`, 15 at `0.5`). RM3 runs on
  every query; the tag narrows the **claim**, not the mechanism. So the drift
  bound, clause 2, covers the whole set.
- **Membership changes almost everywhere**: feedback terms pull documents the
  first pass never returned into the top 10. The pre-registration reports
  `hit@10` beside every arm for this reason.
- ⚠ **At `0.3` and `0.5` the band shifts toward `weak`** (24 → 36). The band is
  built on the original query, so a borrowed-vocabulary #1 reports lower
  coverage. It is reported here and gates nothing.
- **Cost:** about +30 to +70 ms median per `ask`, one extra ranking pass.

## 3 · Headroom (SR-RS d22)

Restated from the **baseline arm** once it is scored (d22f): `decide.py` writes
`headroom` into `decision.json`. The 2026-09-22 capture's figures (improvement
39, regression 51) are from a different engine and are not quoted as this run's.

## 4 · What Arpit picked up — scored 2026-09-23, 01:03

```bash
just golden-score work/regression/2026-09-23-rm3
```

In his own shell. It finds five hand-offs (`evidence/rm3-<w>/rung-01000/`) and
writes `scores/rm3-<w>/rung-01000/set-2-u.json`. **No unlock is needed**: the
scoring carve-out reads the key in the LOCKED state.

## 5 · Reproduce

```bash
# each arm: copy the frozen rung, add `rm3_weight = <w>` under [ranking], then
python3 tools/quality-controls/golden_run.py --rung rung-01000 \
    --tree ~/my_programs/fux-lab/arms/runs/rm3-<w>/rung-01000 \
    --evidence work/regression/2026-09-23-rm3/evidence/rm3-<w>/rung-01000 \
    --sets 2-u --arm rm3-<w>
python3 work/regression/2026-09-23-rm3/evidence/describe.py
```

## Authorship

**`classification: informed` — permanently.**

| artifact | authored by | could reach |
|---|---|---|
| `set-2-u`'s questions **and answers** | **Claude**, a prior designated session under L11's per-set carve-out | `work/golden/seed/` only |
| the pre-registration, the tags, `pool.py` | **Claude Code**, the 2026-09-23 pre-registration session | the question text; two score rows, declared there |
| the build, these captures, `decide.py`, `describe.py`, this report | **Claude Code**, this session | questions, corpus, hand-offs. **No answer, and no score for any arm** |

🔴 **The set's author and its runner are the same model family.** Nothing here
changes that.
