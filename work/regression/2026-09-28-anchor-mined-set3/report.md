---
type: Report
description: "W-232 second bar: three arms (A anchor 1.0 + mined 0.5, B 1.0 + 0.0, C 0.0 + 0.5) captured on set-3-claude at a copy of step 4's mx-base (gen-2 rung-01000, 9cdde333, v5), engine d30783c5. Precondition holds (B moves 20 orders, C 35). am3-C reproduces step 4's mx-0.5 arm 80/80. Hand-offs only: no score and no verdict exist yet."
run: 2026-09-28-anchor-mined-set3
item: W-232
classification: informed
filed: 2026-09-28
pre_registration: work/regression/2026-09-28-anchor-mined-set3/PRE-REGISTRATION.md
---

# Report: the shipped pair on `set-3-claude`, gen-2 `rung-01000` copy

✅ **Decided 2026-09-28: [PASS](VERDICT.md)** by the frozen table. A beats B 6/0
and C 7/0 at rank 1, with 0 losses. The capture text below is left as it was
filed.

**Captured, not scored, not decided.** Below, *changed* means **the ranking
moved**, never that it *improved*.

- **Who scores:** Arpit, with `just golden-score work/regression/2026-09-28-anchor-mined-set3`,
  in his own shell. **No unlock is needed.**
- **Who decides:** a session that did **not** capture these arms runs
  [`evidence/decide.py`](evidence/decide.py) (sha256 `7fb7ab4d…f83c5abc`, frozen
  in the [bar](PRE-REGISTRATION.md)). It writes `decision.json` and
  `per-query.jsonl`.

## 1 · What ran

| | |
|---|---|
| sequence | first bar `641ee38a` → STOP on set-4-claude (`d3139fdb`, [report](../2026-09-28-anchor-mined/report.md)) → Arpit: *re-run on set-3-u* → this bar `d30783c5` → capture at the same commit, 2026-09-28 19:59–20:01 |
| engine | a detached worktree at `d30783c5` with its own venv. `src/` and `node/` equal `641ee38a` |
| source | `fux-lab/arms/runs/mx-base/rung-01000` (gen-2 `9cdde333`, step 4's v5 re-ingest). **Not written to** |
| base copy | `arms/runs/am3-base/rung-01000`. **No re-ingest**: `.fux/index` is `diff -r` identical to `mx-base`'s |
| `doctor --fix` on the copy | template values only: `fux.toml [index] git_timeout_s`, two `refusals.toml [scan]` keys, the missing `tune.toml` keys (among them `mined_weight = 0.5` and `intent_weight = 0.0`), and a new `inspect.toml`. [`evidence/doctor-fix.diff`](evidence/doctor-fix.diff) |
| arms | `am3-{A,B,C}/rung-01000`, each a `cp -a` of the base, with **both** keys written. `diff -r` against A: one line each (`mined_weight = 0.0` in B, `anchor = 0.0` in C) |
| harness | `golden_run.py --sets 3-claude --arm am3-<X> --engine-commit d30783c5 --fux <pinned>`: 80/80 rows per arm, gates on all 80 |

## 2 · Build check and precondition ([`evidence/describe.py`](evidence/describe.py) → `describe.json`)

| vs `am3-A` | rank 1 changed | order changed | membership changed | median `ask` ms | bands (grounded / partial / weak) |
|---|---:|---:|---:|---:|---|
| `am3-A` (1.0 + 0.5) | — | — | — | 172 | 24 / 48 / 8 |
| `am3-B` (1.0 + 0.0) | 7 | 20 | 10 | 163 | 25 / 48 / 7 |
| `am3-C` (0.0 + 0.5) | 14 | 35 | 24 | 171 | 22 / 48 / 10 |

- ✅ **Precondition holds.** Both switches move rankings, so the headroom will be
  **proven** (d22c(a)) once it is scored.
- ✅ **`am3-C` equals step 4's `mx-0.5` arm**: 80/80 ranked lists and 80/80
  bands. That is the same pair of values on the same index, a day and several
  engine commits apart. The build did not drift, and the keys `doctor --fix`
  added moved nothing.
- ⚠ **A rank-1 change is not a loss.** Seven questions have a different rank-1
  document with the mined fold off. Only the score can say which arm is right.
- Latency is flat (163–172 ms median) on a shared machine.

## 3 · Headroom ([SR-RS](../../../records/0133_predictions.md) d22)

Read from each **comparator** arm once scored (d22f). `decide.py` writes it into
`decision.json`. This report claims no figure.

**Filled 2026-09-28, after scoring** (from [`decision.json`](evidence/decision.json),
by the session that decided, not the one that captured):

| endpoint `hit@1` | shipped A | comparator | improvement headroom (comparator in top 10, not at rank 1) | regression headroom (comparator at rank 1) |
|---|---:|---:|---:|---:|
| vs `am3-B` | 54 | 48 | 23 | 48 |
| vs `am3-C` | 54 | 47 | 23 | 47 |

Neither direction is near zero, so the 0 losses are a real null and not a
saturated endpoint.

## 4 · Reproduce

```bash
git worktree add --detach <eng> d30783c5 && (cd <eng> && uv sync --extra dev)
cp -a ~/my_programs/fux-lab/arms/runs/mx-base/rung-01000 ~/my_programs/fux-lab/arms/runs/am3-base/rung-01000
(cd ~/my_programs/fux-lab/arms/runs/am3-base/rung-01000 && <eng>/.venv/bin/fux doctor --fix)
# each arm: cp -a the base; write anchor / mined_weight per the bar. Then, from <eng>:
python tools/quality-controls/golden_run.py --rung rung-01000 \
    --tree ~/my_programs/fux-lab/arms/runs/am3-<X>/rung-01000 \
    --evidence work/regression/2026-09-28-anchor-mined-set3/evidence/am3-<X>/rung-01000 \
    --sets 3-claude --arm am3-<X> --engine-commit d30783c5 --fux <eng>/.venv/bin/fux
python3 work/regression/2026-09-28-anchor-mined-set3/evidence/describe.py
```

## Authorship

**`classification: informed`, permanently**: set-3-claude is Claude-authored,
it was scored before, and step 4 was tuned on it. **This session wrote both bars
and captured every arm**, so it may not decide them. It read
`work/golden/questions/` (ids and text), the `README` there and the directory
listing of `work/golden/retired/`, and **no other path under `work/golden/`**. It
opened no key and no score file.
