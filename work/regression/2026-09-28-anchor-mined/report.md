---
type: Report
description: "W-232, the shipped pair anchor 1.0 + mined 0.5: three arms captured on set-4-claude at a copy of the generation-3 rung-01000 (b73348d5), engine 641ee38a. The bar's STOP fired. am-B (mined off) ranks all 125 questions identically to am-A, because no set-4-claude question carries any of the rung's 9 mined forms. Not scored, and no verdict: a data defect under SR-RS d23b, handed to Arpit."
run: 2026-09-28-anchor-mined
item: W-232
classification: informed
filed: 2026-09-28
pre_registration: work/regression/2026-09-28-anchor-mined/PRE-REGISTRATION.md
---

# Report: the shipped pair on `set-4-claude`, `rung-01000` copy

🔴 **STOP by the bar's precondition. Nothing is scored, and nothing may be decided.**
`am-A` vs `am-B` changes **no** question's order. By the
[pre-registration](PRE-REGISTRATION.md) §Precondition, a null from it would be a
data defect ([SR-RS](../../../records/0133_predictions.md) d23b), not a pass. The
next step is Arpit's (§4).

## 1 · What ran

| | |
|---|---|
| sequence | pre-registration `641ee38a` (bar + `decide.py`, frozen by hash) → capture at the same commit, 2026-09-28 15:13–15:16 |
| engine | a detached worktree at `641ee38a` with its own venv, passed to the harness as `--fux` |
| source rung | `fux-lab/corpora/golden/rung-01000` at `b73348d5`. **Not written to** |
| base copy | `fux-lab/arms/runs/am-base/rung-01000`. **No re-ingest**: the engine read the rung's index as it stands |
| `doctor --fix` on the copy | template values only: `tune.toml` +28 lines, `formats.toml`, `output.toml`, `refusals.toml`, and a new `inspect.toml`. `anchor = 1.0` and `mined_weight = 0.5` were untouched. Diff: [`evidence/doctor-fix.diff`](evidence/doctor-fix.diff) |
| arms | `am-{A,B,C}/rung-01000`, each a `cp -a` of the base. `diff -r` against `am-A` shows exactly one line: `mined_weight = 0.0` (B), `anchor = 0.0` (C). Base = A byte-for-byte |
| harness | `golden_run.py --sets 4-claude --arm am-<X> --engine-commit 641ee38a --fux <pinned>`: 125/125 rows per arm, gates on all 125 |

## 2 · Build check and precondition ([`evidence/describe.py`](evidence/describe.py) → `describe.json`)

| vs `am-A` | rank 1 changed | order changed | membership changed | median `ask` ms | bands (grounded / partial / weak) |
|---|---:|---:|---:|---:|---|
| `am-A` | — | — | — | 169 | 69 / 24 / 32 |
| `am-B` (mined off) | **0** | **0** | **0** | 163 | 69 / 24 / 32 |
| `am-C` (anchor off) | 0 | 13 | 5 | 166 | 69 / 24 / 32 |

- ✅ **`am-A` equals the 2026-09-27 capture**: 125/125 ranked lists and 125/125 bands.
- 🔴 **STOP: `am-B`.** Turning the mined fold off moves nothing.
- `am-C` moves 13 orders and no rank-1 document. A `hit@1` comparison of A and C
  would therefore have zero discordant pairs.

## 3 · Why `am-B` is inert: diagnosed, not scored

**The fold is live.** On hand-written probes run from the arm copies, `mined_weight`
changes scores and ranking. *"how is MKT calculated"*: top score 11.70 (A) vs
7.04 (B). *"Door Open Minutes limit"*: rank 1 differs between A and B. So neither
the index nor the engine is the defect.

**The set cannot reach it.** The step-4 pattern over the rung's `seed/` and `ext/`
text yields **9** `Term (ABBR)` forms (MKT, QDL, DOM, WCP, LRS, CCT, SBR, SCT, …).
**None of the 125 set-4-claude questions contains any of them**, neither the short
form as a token nor the long form as a phrase. The fold adds terms only when a
question holds one side of a pair, so on this set it adds nothing, ever.

⚠ **This also means step 4's shipped effect on set-4-claude is nil.** The
2026-09-27 baseline and every step-9 arm ran a pair whose second half did
nothing on this set. Step 4's PASS stands on `set-3-u`'s 22 tagged questions,
which were counted on the generation-2 rung.

## 4 · What Arpit decides

The measurement needs questions that carry a mined form, on a rung that holds the
pair's documents. The options, none of them taken here:

1. **Re-run the three arms on `set-3-u`**, the set step 4 was measured on (22
   `expansion_form` questions), at a copy of **its** rung (generation 2,
   `9cdde333`). This needs a **new pre-registration**, because the frozen bar
   names set-4-claude. It is cheapest, and closest to what W-232 asked.
2. **Author mined-form questions into the next generation** (a seed/question
   change, which rebuilds the ladder, like W-228's misfits). The slowest option.
3. **Close W-232 as unmeasurable on the current set**, with the warning moved
   from *"unmeasured"* to *"inert on set-4-claude; the interaction is unmeasured
   where it acts"*.

## 5 · Reproduce

```bash
git worktree add --detach <eng> 641ee38a && (cd <eng> && uv sync --extra dev)
cp -a ~/my_programs/fux-lab/corpora/golden/rung-01000 ~/my_programs/fux-lab/arms/runs/am-base/rung-01000
(cd ~/my_programs/fux-lab/arms/runs/am-base/rung-01000 && <eng>/.venv/bin/fux doctor --fix)
# am-A = cp -a base; am-B: mined_weight = 0.0; am-C: anchor = 0.0. Then, from <eng>:
python tools/quality-controls/golden_run.py --rung rung-01000 \
    --tree ~/my_programs/fux-lab/arms/runs/am-<X>/rung-01000 \
    --evidence work/regression/2026-09-28-anchor-mined/evidence/am-<X>/rung-01000 \
    --sets 4-claude --arm am-<X> --engine-commit 641ee38a --fux <eng>/.venv/bin/fux
python3 work/regression/2026-09-28-anchor-mined/evidence/describe.py
```

## Authorship

**`classification: informed`, permanently**: set-4-claude is Claude-authored and
was scored before. This session wrote the bar and captured the arms, so it may
not decide them. It read `work/golden/questions/set-4-claude.jsonl` (ids and text)
and the ladder manifest, and **no other path under `work/golden/`**. It opened no
key and no score file.

## Headroom (SR-RS d22), added 2026-09-28 by the deciding session

**Not measurable, because the run was never scored.** The STOP came before
scoring, so neither **improvement** nor **regression** headroom exists for any
arm. The precondition's own count stands in for both: `am-B` changes **0** of 125
rankings, so no question could move in either direction on the mined switch.
That is the STOP. The second bar ([`2026-09-28-anchor-mined-set3`](../2026-09-28-anchor-mined-set3/VERDICT.md))
is where W-232 was decided.
