---
type: PreRegistration
name: PRE-REG-BENCH-V1-V2-HEAD
description: "W-204 phase B, frozen before any number existed. Three engines — fux-engine 1.0.0, 2.0.1 and the frozen HEAD — on the same eight golden rungs and the same three question sets, end to end from ingest. Descriptive per set; it files no score, because the key is not open."
timestamp: 2026-09-21T00:00:00Z
item: W-204
status: frozen
---

# Benchmark — `1.0.0` vs `2.0.1` vs `HEAD`, on the golden ladder. Frozen before the run.

**Asked by Arpit, 2026-09-20 (Cowork):** *"a benchmark between version one,
version two and the latest head."* This is
[W-204](../regression/2026-09-22-golden-final-score/FINAL-SCORE.md) phase B.

**It cites [PRE-REG-BENCH-V1-VS-HEAD](PRE-REGISTRATION-V1-VS-HEAD.md) (2026-08-28)
and does not edit it.** That document froze one sha and two arms against a
generated 240-query corpus; this is three arms, a different corpus and a
different question set, so it is **a new id space**. What is carried forward
verbatim is its §0 power table and its §1.1 asymmetry rule, both cited below.

---

## 0 · What this run can and cannot conclude — decided before the first command

🔴 **The key is not open, so phase B produces NO correctness number.** What it
produces is **what each engine ranked, answered and declined**, per query, per
rung, per arm — the rows phase D scores in one pass once Arpit pastes prompt 9.
Phase B's own claims are confined to §5.

🔴 **The two sets are never pooled to reach 240, and this run is therefore
descriptive per set.** Set 1 has 125 questions, set 2 has 124 and set 3 has 125;
the 2026-08-28 table puts `N = 100–150` at power **0.17–0.60** for the effects a
version bump produces. So:

| `N` | `pb`.06 / `pc`.02 | `pb`.10 / `pc`.03 | `pb`.15 / `pc`.05 |
|---:|---:|---:|---:|
| 100 | 0.17 | 0.40 | 0.55 |
| **125** | **~0.23** | **~0.50** | **~0.67** |
| 150 | 0.30 | 0.60 | 0.75 |
| 240 | 0.52 | 0.83 | 0.93 |

**A pair that does not clear [SR-RS](../../records/0133_predictions.md) decision
19's paired floor — a net of 6 flips — is reported as *not distinguishable at
this N*, and NEVER as *no difference*.** The floor is applied **per set**, and it
tracks the flips, not the set size.

⚠ **Three sets are three measurements, not a bigger one.** The temptation this
clause exists to refuse is pooling 374 questions to buy power; that would erase
the authorship gap the sets were commissioned to expose and would put a number on
a mixture nobody can name.

## 1 · The arms

| arm | what it is | install | index format it writes |
|---|---|---|---|
| **v1** | `fux-engine==1.0.0`, tag `v1.0.0`, 2026-08-22 | `uv pip install fux-engine==1.0.0` into `fux-lab/arms/v1` (Python 3.11.15) | `fux.index.v1` |
| **v2** | `fux-engine==2.0.1`, the release on PyPI | `uv pip install fux-engine==2.0.1` into `fux-lab/arms/v2` (Python 3.11.15) | `fux.index.v2` |
| **HEAD** | the frozen sha below, from this working tree | the repo's own `.venv` | `fux.index.v4` |
| **v1′** | arm v1, run twice on the same rung | the null control (§4) | — |

```
HEAD = 7a88a1657a183157a1cd842e5d392d55f65823f2   # frozen 2026-09-21, before the first command ran
```

🔴 **HEAD's rows are phase A's rows, not a second pass.** They were produced at
this same sha by
[`2026-09-21-golden-ladder-outputs-set-3`](../regression/2026-09-21-golden-ladder-outputs-set-3/report.md).
Re-running HEAD would spend 6 000 calls to reproduce a file that already exists
and would introduce a second engine state to reconcile.

⚠ **`uv` rather than `pip`, and Python 3.11 rather than the system one, and
both are recorded because both were forced.** macOS `python3` here is **3.9.6**,
below fux's floor of 3.11 ([L7](../../records/0008_LAW-7-python-311.md)), so
`python3 -m venv` + `pip install fux-engine==1.0.0` fails with *"No matching
distribution found"* — a message that reads exactly like *the version was never
published*. It was published; the interpreter was too old.

## 1.1 · Three engines, three indexes, no shared bytes

**Carried forward verbatim from
[PRE-REG-BENCH-V1-VS-HEAD §1.1](PRE-REGISTRATION-V1-VS-HEAD.md):** each arm
**ingests the same rung bytes into its own copy** of the rung directory, so the
comparison is **end to end** — ingest → index → rank → answer — and every claim
is worded that way. An arm never reads another arm's index.

🔴 **Nothing writes into `~/my_programs/fux-lab/corpora/golden/rung-*/.fux/`.**
Those are the frozen rungs; the arms work on throwaway copies under
`~/my_programs/fux-lab/arms/runs/<arm>/<rung>/`, and the runbook deletes and
recreates a copy rather than re-using one.

⚠ **`corpora/` is kept, not scratch** (Arpit, 2026-09-12). A 2026-08-20 wipe
already cost a filed item its evidence. The copies live under `arms/`, which is
this run's and is disposable by construction.

## 2 · The arms cannot share a `fux.toml`, and that is stated before it is discovered

🔴 **Phase A found the mirror image of this and it stopped the run cold.** Every
rung's `fux.toml` carried `[sources.url] meta = "hashed"`, which HEAD **refuses
by name** after W-194 — so no rung loaded at HEAD until the line was deleted.
**v1 and v2 are the other half of that trap:** they were released while the key
existed, and v1 predates keys HEAD requires.

**So the config is per arm, and the arms manifest records the exact bytes each
one ran with.** Concretely, and decided now rather than mid-run:

- Each arm's copy is set up **by its own `fux setup`**, so every default in
  `fux.toml` and `.fux/tune.toml` is the one that arm ships.
- 🔴 **`[bm25f] b` differs between arms and that IS the arm**, not a knob to
  equalise — W-204 phase B's own words. The manifest prints each arm's `b`.
- **The `.fux/sources/dirs` declarations are identical across arms** — `seed`,
  `seed/archive archived=true`, `ext`, `ext/archive archived=true` — because
  *what is in the corpus* is not the variable under test. If an arm cannot parse
  that file, the adaptation is recorded and §7 decides whether it is part of the
  arm.
- **`pii.toml`**: HEAD refuses to run without one; v1.0.0 has no such concept.
  An empty `.fux/pii.toml` is written for every arm that tolerates it, and the
  runbook records which did.

## 3 · What is run, and the per-arm invocation

**Eight rungs × three question sets × two verbs, per arm.**

| rung | documents |
|---|---:|
| `rung-seed` | 28 |
| `rung-00100` | 100 |
| `rung-00200` | 200 |
| `rung-00500` | 500 |
| `rung-01000` | 1 000 |
| `rung-02000` | 2 000 |
| `rung-05000` | 5 000 |
| `rung-10000` | 10 000 |

🔴 **The invocation differs per arm, and the difference is measured, not hidden:**

| | v1.0.0 | v2.0.1 | HEAD |
|---|---|---|---|
| `ask` | `ask "<q>" --json --top 10` | `ask "<q>" --json --band --top 10` | same as v2 |
| `answer` | `answer "<q>" --json` | `answer "<q>" --json` | same |
| ingest | `ingest --full` | `ingest --full` | `ingest --full --no-fetch` |

⚠ **`--band` does not exist in v1.0.0.** Its `ask` parser has `--json`,
`--fast`/`--scan`, `--top`, `--explain` and `--hybrid`, and argparse exits **2**
on an unknown flag — so a harness that hardcoded `--band` would record 3 000
empty results for arm v1 and they would read as a catastrophic ranking
regression. **Capture 2's band column therefore exists for two arms of three**,
and any statement about the confidence band in this benchmark is a `v2 → HEAD`
statement only.

**374 questions × 2 verbs × 8 rungs × 2 new arms = 11 968 calls**, plus HEAD's
5 984 already filed by phase A.

## 4 · 🔴 The null control runs FIRST, and nothing else runs until it passes

**`v1` against `v1′` on `rung-00500`, both sets, same throwaway copy recipe, two
independent ingests.** The endpoint is **zero moved rows**.

**If any row moves, the harness is wrong and no A-vs-B number is taken.** This is
not a formality: an engine with an unseeded iteration order, a wall-clock field
or a path-dependent tie-break produces differences between *identical* arms, and
every one of them would be attributed to the version bump. The control's output
is filed whether it passes or fails.

⚠ **`rung-00500` rather than `rung-seed`**, because a 28-document corpus has too
few ties to expose an unstable sort, and rather than `rung-10000`, because the
control must be cheap enough that nobody is tempted to skip it.

## 5 · What phase B may claim, and what it may not

**Captures 1, 2, 5 and 6 of [SR-WORK-BENCHMARK](../../records/0053_WORK-benchmark.md)
are filled NOW. Captures 3, 4 and 7 are left EMPTY until phase D**, because each
of them needs the key:

| # | capture | phase B | why |
|---|---|---|---|
| 1 | ranked lists, per query, per arm | ✅ **now** | no key needed |
| 2 | what moved between arms | ✅ **now** | a diff of two ranked lists; ⚠ band column, v2→HEAD only |
| 3 | `hit@k` at 1/5/10/20/50 | ⬜ **phase D** | needs `relevant` |
| 4 | the answer layer against the planted unanswerables | ⬜ **phase D** | needs `answerable` |
| 5 | committed index bytes per rung per arm | ✅ **now** | a byte count |
| 6 | speed, arms interleaved on one machine | ✅ **now** | see the caveat below |
| 7 | the HTML report, one slide per capture | ⬜ **phase D** | it reports 3, 4 and 7's numbers |

🔴 **What phase B may NOT claim:** that any arm is better, worse, more accurate
or more useful than another; any `hit@k`, `recall@k` or correctness figure; any
statement about a pair that does not clear the d19 floor other than *not
distinguishable at this N*; and any pooled figure across sets.

⚠ **Capture 6 is timing on a SHARED machine.** L9 requires the arms to be
interleaved rather than run in blocks, and they are; even so, a concurrent
session on this machine produces *"a clean, localised anomaly that reads like a
finding"* ([LESSONS](../LESSONS.md)). Every latency number here is reported with
the machine's concurrent load stated beside it, and **no latency claim is
reported as a regression without a second interleaved run**.

## 6 · The arms manifest — written before any A-vs-B row

`work/regression/<date>-golden-three-engines/evidence/ARMS.md`, holding per arm:
the venv path, the resolved interpreter, `uv pip freeze`, the wheel's sha256 (or
the git sha for HEAD), the exact command line for setup, ingest, `ask` and
`answer`, and the arm's `b`, `k1` and field weights as that arm's own `fux setup`
wrote them.

**No row is taken before that file exists**, for the reason the 2026-08-28
document gives: an arm nobody can rebuild is an anecdote with three decimal
places.

## 7 · Adaptations — how one is recorded, decided now

An arm may refuse to ingest a rung as the rung is laid out (types allowlist,
`.fux/sources` shape, a missing or forbidden config key). When that happens:

1. The runbook records **what was changed, for which arm, and the exact bytes**.
2. 🔴 **The adaptation is declared as part of the arm or as a defect of the
   comparison, and which one is decided BEFORE the arm's first row.** An
   adaptation chosen after the numbers are visible is a moved threshold wearing a
   different hat.
3. An arm that cannot be made to ingest a rung at all is filed as
   **`unmeasurable` for that rung**, with the error, and is never reported as a
   zero.

## 8 · Classification

**`informed`**, on [SR-RS](../../records/0133_predictions.md) decision 11 — sets
2 and 3 share an author with the runner, set 1's blindness ended with the
2026-09-17 breach, and these rows feed a scored run. **No arm of this benchmark
is `blind` and none may be labelled so.**
