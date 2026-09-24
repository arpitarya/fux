---
type: Report
description: "The five anchor arms of W-168 step 1 — `[bm25f] anchor ∈ {0.0, 0.5, 1.0, 2.0, 3.0}` — captured on `set-3-u` at `rung-01000`, one pinned engine (`2dbe870f`), one index. Hand-offs only: no score and no verdict exist. The anchor field changes the rank-1 document on 9 to 18 of 80 questions, every one of them tagged `anchor_dependent`."
run: 2026-09-15-anchor-text
item: W-168
classification: informed
filed: 2026-09-24
pre_registration: work/regression/2026-09-15-anchor-text/PRE-REGISTRATION.md
---

# REPORT — anchor arms captured, `set-3-u`, `rung-01000`

🔴 **Captured, not scored, and not decided.** No key reached this session.
*Changed* below means **the ranking moved**, never *improved*. The verdict comes
from [`evidence/decide.py`](evidence/decide.py) (frozen in `cfca651a`, before
any arm existed), run on Arpit's scores by a session that **did not** capture
these arms (pre-registration §What this run may NOT do, item 4).

## 1 · What ran

| | |
|---|---|
| pre-registration | amended 2026-09-24 and committed at `cfca651a` **before the first call** |
| engine | `2dbe870f66a87ec65a6483078fc64899ee10b72c` in a pinned worktree: the rung's own stamp, so no re-ingest |
| arm copies | `~/my_programs/fux-lab/arms/runs/anchor-<w>/rung-01000`, `cp -a` of the frozen rung. Each `tune.toml` differs from the rung's **only** on the `anchor` line; `.fux/index/` is byte-identical across them (`diff -rq`) |
| stop check | ✅ **`anchor-0.0` ranks exactly what the [generation-2 capture](../2026-09-24-golden-gen2-rung-01000/report.md) ranked, 80 of 80 rows** |
| harness | `golden_run.py --sets 3-u`, `ask --json --band --why --top 10` + `answer --json` |
| questions | 80 per arm; funnel gates captured on 80 of 80 in every arm |

## 2 · What each arm did — descriptive, `k = 10`

From [`evidence/describe.py`](evidence/describe.py) → `describe.json`. *Tagged*
means `anchor_dependent` (27 of 80).

| arm | rank-1 changed | of which tagged | order changed (tagged) | membership changed | hub first | hub in top 10 | hub rose | median `ask` ms | bands (grounded / partial / weak) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `anchor-0.0` | — | — | — | — | 5 | 44 | — | 142 | 22 / 48 / 10 |
| `anchor-0.5` | 9 | 9 | 31 (25) | 20 | 5 | 44 | 1 | 144 | 23 / 48 / 9 |
| `anchor-1.0` | 14 | 14 | 35 (25) | 23 | 5 | 43 | 2 | 144 | 25 / 48 / 7 |
| `anchor-2.0` | 17 | 17 | 39 (25) | 24 | 5 | 43 | 3 | 145 | 26 / 48 / 6 |
| `anchor-3.0` | 18 | 18 | 44 (25) | 30 | 4 | 43 | 3 | 144 | 26 / 48 / 6 |

- **The mechanism fires on this set.** The 2026-09-15 probe measured 0 of 124
  flips because the ladder had no link text. Here rank 1 moves on 9 questions at
  `0.5`.
- **Every rank-1 change is on a tagged question, at every weight.** The
  anchor field acts only where a linker's word appears in the question. Lower in
  the list it also reorders 6–19 untagged questions, but **never their rank 1**,
  so clause 2 cannot move at `hit@1` ([ANALYSIS §1](ANALYSIS.md)).
- **The hub barely moves:** first on 5 → 4 questions, and its rank rises on 1–3.
  Whether those rises are on questions it answers is the scorer's to say.
  Clause 3 reads them.
- **Bands shift toward `grounded`** (22 → 26). The band gates nothing here.
- **Cost:** none measurable. The median `ask` is within 3 ms across arms on a
  shared machine.

## 3 · Headroom (SR-RS d22), per direction

`decide.py` restates both from the **baseline arm** (d22f). Because `anchor-0.0`
equals the generation-2 capture row for row, the scored gen-2 figures already
are the baseline's:

| direction | on `set-3-u`, `hit@1` | what it counts |
|---|---:|---|
| **improvement** headroom | **14** tagged (13 in the returned ten) | tagged, answerable, missing rank 1: the pool the ruling was made on |
| **regression** headroom | **41** (11 of them tagged) | every baseline rank-1 hit, which a treatment could lose |

## 4 · What Arpit picks up

```bash
just golden-score work/regression/2026-09-15-anchor-text
```

In his own shell. It finds five hand-offs (`evidence/anchor-<w>/rung-01000/`,
checked with `handoffs.py`) and writes
`scores/anchor-<w>/rung-01000/set-3-u.json`. **No unlock is needed**: the
scoring carve-out reads the key in the LOCKED state. Then a session that did
**not** capture these arms runs `decide.py`.

## Authorship

**`classification: informed`, permanently.**

| artifact | authored by | could reach |
|---|---|---|
| `set-3-u`'s questions **and answers** | **Claude**, the designated set-3 session under L11's per-set carve-out | `work/golden/seed/` only |
| `step_pools.py` and the pool of 14 | **Claude Code**, the 2026-09-24 gen-2 scoring session | question text, `seed/`, and Arpit's score rows (ids, ranks, flags) |
| the amendment, the tags, `decide.py`, these captures, `describe.py`, this report | **Claude Code**, this session | questions, `seed/`, corpus, hand-offs, and the gen-2 **pool counts** (aggregates). **No answer, and no score row for any anchor arm** |

🔴 **The set's author and its runner are the same model family, and the
endpoint was ruled after the pools were seen.** Nothing here changes that.

## 5 · May not claim

Whether any change is right; any keyed metric; *the best weight*; the word
*blind*.

## 6 · Reproduce

```bash
git worktree add <tmp>/engine-pin 2dbe870f66a87ec65a6483078fc64899ee10b72c --detach
cd <tmp>/engine-pin && uv venv .venv && uv pip install --python .venv/bin/python -e .
# each arm: copy the frozen rung, set `anchor = <w>` under [bm25f], then
.venv/bin/python tools/quality-controls/golden_run.py --rung rung-01000 --sets 3-u \
    --tree ~/my_programs/fux-lab/arms/runs/anchor-<w>/rung-01000 \
    --evidence work/regression/2026-09-15-anchor-text/evidence/anchor-<w>/rung-01000 \
    --fux <tmp>/engine-pin/.venv/bin/fux \
    --engine-commit 2dbe870f66a87ec65a6483078fc64899ee10b72c --arm anchor-<w>
.venv/bin/python work/regression/2026-09-15-anchor-text/evidence/describe.py
```
