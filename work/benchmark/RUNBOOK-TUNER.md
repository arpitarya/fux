---
type: Runbook
name: RUNBOOK-TUNER
title: RUNBOOK-TUNER — how an agent executes the knob sweep, step by step
description: "The operating procedure for PRE-REGISTRATION-TUNER: one engine, one index per corpus, one query pass per knob value, the playground veto, the cost fence, the candidate table handed over without a recommendation. Restates no bar."
timestamp: 2026-08-28T00:00:00Z
---

# RUNBOOK-TUNER — the knob sweep, executed by an agent

**Model: Sonnet** for §1–§6 — every step has a mechanical gate. **Opus** for
§7 (`ANALYSIS.md`, the verdicts, the candidate table's wording) and for the
moment T2's veto returns anything other than what was predicted: that is a
judgement, and the wrong model returns a confident, plausible, wrong one.
**Say the model out loud on handover.**

> **Bars live in [`PRE-REGISTRATION-TUNER.md`](PRE-REGISTRATION-TUNER.md).**
> Every *"rule against Tn"* below means: open that section and rule against it
> as written. If this runbook and the pre-registration disagree, the
> pre-registration wins and this file is fixed in the same change.
> [`RUNBOOK-BENCHMARK.md`](RUNBOOK-BENCHMARK.md) §1, §2 and §8 apply unchanged
> and are not repeated here.

---

## 0. What is different about a sweep — read before the first command

| version benchmark | knob sweep |
|---|---|
| two engines, two indexes | **one engine, one index per corpus** |
| the arm is the variable | **one key in `.fux/tune.toml` is the variable**; the index must not move (T0.b) |
| a null is a finding | a null on a generated suite is *expected*; the **veto** is the finding |
| `informed` is a limitation | `informed` is the **nature** of a tuner — selection reads scores. It is filed so, and it states no default |
| the output is a delta | the output is a **candidate table** with three legs per knob, handed over **without a recommendation** |

🔴 **The three legs are not optional and not interchangeable.** Gain on the
generated suite, veto on the hand-graded playground, cost on one machine. A
candidate with two green legs is not a candidate.

---

## 1. Preconditions — beyond RUNBOOK-BENCHMARK §1

```bash
# 1.1 the playground is at its committed state, and green at defaults
cd ~/my_programs/fux-playground && git status --short          # expect: empty
python check.py                                                 # expect: 41 pass · 9 xfail · 0 unexplained (or the current committed state)
python check.py --index-guard                                   # a fresh ingest reproduces the committed index

# 1.2 the playground grades the working tree, not a wheel
grep -A2 'tool.uv.sources' pyproject.toml                       # fux-engine = { path = "../fux", editable = true }
cd ~/my_programs/fux && git rev-parse HEAD                      # must equal the sha in the pre-registration §1

# 1.3 the harness has the sweep switch and the playground adapter (pre-registration §8)
cd ~/my_programs/fux-benchmark && python3 bin/bench.py --help | grep -E 'tune|playground'
```

| gate | on failure |
|---|---|
| playground dirty, or red at defaults | stop. A sweep against a red baseline attributes the wrong thing to the knob |
| playground grades a wheel, not `../fux` | fix `pyproject.toml`; the candidate must be measured on the sha the pre-registration froze |
| `bench.py` lacks `--tune` / the playground adapter | **build them first** (Sonnet, specified in the pre-registration §8). ⚠ The playground harness emits totals only; without rows the run cannot be filed |
| `fux tune` prints a value that differs from `tune.py`'s default | the file and the constant have drifted — W-83's class of defect. Halt, fix at the source |

**Where it runs:** §2–§5 in the cloud or on the laptop (deterministic). **§6 on
the laptop only.** ⚠ The playground repo lives on the laptop; if §4 runs in the
cloud the playground must be cloned there at the same commit, and the report
says so.

---

## 2. Freeze and corpora

```bash
# 2.1 freeze — the sha goes into the pre-registration §1, committed, before anything below
cd ~/my_programs/fux && git rev-parse HEAD
shasum -a 256 work/benchmark/PRE-REGISTRATION-TUNER.md

# 2.2 regenerate the three corpora BYTE-IDENTICAL to the filed runs
cd ~/my_programs/fux-benchmark && python3 shared/generate/make_corpus.py --selftest
python3 shared/generate/make_corpus.py --out corpora/t1200  --docs 1200 --seed 12 --bench \
        --pairs 120 --chains 20 --decoys 30 --unanswerable 20 --contested 120 --heading 40 --path 60 --cluster 4
python3 shared/generate/make_corpus.py --out corpora/t1200b --docs 1200 --seed 13 --bench \
        --pairs 120 --chains 20 --decoys 30 --unanswerable 20 --contested 120 --heading 40 --path 60 --cluster 4
python3 shared/generate/make_corpus.py --out corpora/t1000  --docs 1000 --seed 12 --bench \
        --pairs 240 --chains 40 --decoys 50 --unanswerable 20
for t in t1200 t1200b t1000; do (cd corpora/$t && find . -type f | sort | xargs shasum -a 256 | shasum -a 256); done
```

| gate | on failure |
|---|---|
| a hash differs from the one filed under `work/regression/2026-08-28-benchmark-*/evidence/` | the generator is no longer additive. Halt; nothing this run measures is comparable to what those runs filed |

---

## 3. T0 — gates and baselines (rule against T0)

```bash
# 3.1 one index per corpus, built ONCE at defaults — the sweep never re-ingests
for t in t1200 t1200b t1000; do python3 bin/bench.py prepare --run T --arm B --tier $t; done
for t in t1200 t1200b t1000; do (cd work/B-$t/.fux/index && find . -type f | sort | xargs shasum -a 256 | shasum -a 256) | tee runs/T/index-$t.sha; done

# 3.2 T0.a — same-corpus repeat at defaults
python3 bin/bench.py quality --run T --arm B --tier t1200 --label base-rep1
python3 bin/bench.py quality --run T --arm B --tier t1200 --label base-rep2
diff runs/T/rows/base-rep1-t1200.jsonl runs/T/rows/base-rep2-t1200.jsonl && echo IDENTICAL

# 3.3 T0.c — baselines, filed before any knob pass
python3 bin/bench.py quality --run T --arm B --tier t1200b --label base
python3 bin/bench.py quality --run T --arm B --tier t1000  --label base
python3 bin/bench.py playground --run T --label base            # per-golden rows: pass | xfail | XPASS
(cd ~/my_programs/fux-playground/.fux/index && find . -type f | sort | xargs shasum -a 256 | shasum -a 256) | tee runs/T/index-playground.sha
```

| gate | on failure |
|---|---|
| T0.a rows differ | 🔴 halt. The engine is nondeterministic on near-identical candidates; every number is void |
| the playground baseline is not `41 · 9` (or its committed state) | stop; the working tree has moved. Re-freeze or re-check the sha |

**Write down, from the baseline rows, the headroom line per endpoint** — *score
· could change* — before the first knob pass. This is T5's first row and the
reason a later "no change" can be read.

---

## 4. T1 and T2 — the grids (rule against T1, T2)

The sweep switch writes one key into the work directory's `.fux/tune.toml`,
runs the pass, restores the file, and **hashes the index before and after**.

```bash
# 4.1 T1.a — rerank_weight grid on seed 12. G_r is FROZEN in the pre-registration; do not extend it.
for v in 0.1 0.25 0.5 1.0 2.0; do
  python3 bin/bench.py quality --run T --arm B --tier t1200 --label rerank-$v \
          --tune 'ranking.rerank_weight' --value $v
  (cd work/B-t1200/.fux/index && find . -type f | sort | xargs shasum -a 256 | shasum -a 256) | diff - runs/T/index-t1200.sha || echo "T0.b VIOLATED at rerank=$v"
done

# 4.2 T1.b — select the candidate by the FROZEN rule (smallest value ≥ 0.95 × max target_first)
python3 bin/bench.py select --run T --knob rerank --rule 'smallest>=0.95max' --suite contested --kind proximity --key target_first

# 4.3 T1.c — gain on the fresh seed, candidate vs baseline
python3 bin/bench.py quality --run T --arm B --tier t1200b --label rerank-cand --tune 'ranking.rerank_weight' --value <cand>
python3 bin/bench.py mcnemar --a runs/T/rows/base-t1200b.jsonl --b runs/T/rows/rerank-cand-t1200b.jsonl \
        --suite contested --kind proximity --key target_first

# 4.4 T1.d — the veto: playground at the candidate, rows per golden, restore the file, check the index
python3 bin/bench.py playground --run T --label rerank-cand --tune 'ranking.rerank_weight' --value <cand>
(cd ~/my_programs/fux-playground && git status --short)        # expect: empty — tune.toml restored
python3 bin/bench.py veto --run T --base playground-base.jsonl --cand playground-rerank-cand.jsonl   # prints broken / fixed / XPASS by qid
```

```bash
# 4.5 T2 — superseded_weight, same shape; G_s FROZEN; selection is LARGEST value ≥ 0.95 × max fixed
for v in 0.9 0.75 0.5 0.25; do
  python3 bin/bench.py quality --run T --arm B --tier t1000 --label sup-$v --tune 'ranking.superseded_weight' --value $v
  (cd work/B-t1000/.fux/index && find . -type f | sort | xargs shasum -a 256 | shasum -a 256) | diff - runs/T/index-t1000.sha || echo "T0.b VIOLATED at sup=$v"
done
python3 bin/bench.py select --run T --knob sup --rule 'largest>=0.95max' --suite chains --key current_first
python3 bin/bench.py quality --run T --arm B --tier t1200b --label sup-cand --tune 'ranking.superseded_weight' --value <cand>
python3 bin/bench.py mcnemar --a runs/T/rows/base-t1200b.jsonl --b runs/T/rows/sup-cand-t1200b.jsonl --suite chains --key current_first
python3 bin/bench.py playground --run T --label sup-cand --tune 'ranking.superseded_weight' --value <cand>
python3 bin/bench.py veto --run T --base playground-base.jsonl --cand playground-sup-cand.jsonl
```

| gate | on failure |
|---|---|
| T0.b violated at any value | that knob's passes are **void**; the run says the knob is not a tune knob and files it as a defect against ADR-TUNE |
| no value beats baseline by more than net 6 on the isolating suite | no candidate; the knob's verdict is `INCONCLUSIVE` |
| the veto prints `broken > 0` | the knob's verdict is **`FAIL`** at that candidate. 🔴 **Do not try the next grid value to find one that passes** — the candidate is selected once, by the frozen rule. If Arpit wants the mildest value that passes the veto measured, that is a new pre-registration |
| `q022` / `q033` break at the T2 candidate | as predicted; file it. If they **do not**, hand the result to Arpit unadjudicated — the pre-registration says this is its one real question |
| the playground `git status` is not empty after a pass | the restore failed; `git checkout -- .fux/tune.toml` and re-run T0.b on the playground index |

⚠ **Never edit `src/fux/tune.py` or `bm25f.py` during the run.** The sweep is
entirely through `.fux/tune.toml`; a constant changed in source would move the
baseline under every pass.

---

## 5. T3 — the joint set (only if both T1 and T2 produced a candidate)

```bash
python3 bin/bench.py quality --run T --arm B --tier t1200b --label joint \
        --tune 'ranking.rerank_weight' --value <c1> --tune 'ranking.superseded_weight' --value <c2>
python3 bin/bench.py playground --run T --label joint --tune 'ranking.rerank_weight' --value <c1> --tune 'ranking.superseded_weight' --value <c2>
python3 bin/bench.py veto --run T --base playground-base.jsonl --cand playground-joint.jsonl
```

Rule against T3: playground broken = 0, and each instrument's `c` no larger
than its single-knob `c`. **If T3 does not run, the report says `not run` and
why** — it is the predicted outcome.

---

## 6. T4 — the cost fence, laptop, one session (rule against T4)

```bash
# 6.1 differential law AT THE CANDIDATE, before any --fast number
python3 bin/bench.py difflaw --run T --tier t1200 --tune 'ranking.rerank_weight' --value <cand>      # --fast ≡ --scan, byte-identical, all queries
# 6.2 latency, interleaved baseline / candidate
python3 bin/latency.py --run T --tier t10000 --queries 240 --repeats 5 --arms base,rerank-cand
```

| gate | on failure |
|---|---|
| the law fails at the candidate | the candidate is **`FAIL`** on cost — a `--fast` path that returns different results at a shipped default is a correctness defect, not a tuning result. File it against W-73's law |
| p95 > 1.2 × baseline | `FAIL` on cost; the reranker's top-k cost is the first suspect, and that is a code finding |
| the laptop half slips | T4 filed **`not measured`**; T1/T2 verdicts become **`INCONCLUSIVE`** on the cost leg, never `PASS` |

---

## 7. Filing — RUNBOOK-BENCHMARK §8, plus what a sweep adds

- [ ] `work/regression/<date>-benchmark-tuner/` with `classification: informed`
      (a tuner is informed by nature — say so, and say why in `## Authorship`).
- [ ] `evidence/rows/` — one file per pass: `base-*`, `rerank-<v>-*`,
      `sup-<v>-*`, `playground-*`; `evidence/index-*.sha` for every T0.b
      assertion; `ARMS.toml`; the pre-registration's `sha256`.
- [ ] `VERDICT-T1.md`, `VERDICT-T2.md`, and `VERDICT-T3.md` / `VERDICT-T4.md`
      where ruled — predicted vs measured in each.
- [ ] **The candidate table**, in the report, one row per knob:
      *knob · default · candidate · gain (b / c / p, fresh seed) · veto (broken
      / fixed / XPASS, by qid) · cost (p95 ratio, law) · verdict*. **No
      recommendation column.** The last line of the report is the handoff to
      Arpit, and it names ADR-TUNE as where a change would be recorded.
- [ ] T5's headroom table, every endpoint, every grid value.
- [ ] Post-hoc observations (a grid value that "would have passed") **labelled
      post-hoc, outside every verdict**.
- [ ] The deck (README rule 4): the three-leg diagram, one dose–response chart
      per knob with the candidate marked, the veto by qid, the cost bar.
- [ ] `W-97`: row deleted from `OPEN-WORK.md`, file to `archive/open/`; a new
      `arpit`-lane row for each candidate that passed, pointing at the run and
      at ADR-TUNE.
- [ ] Tests green: `python -m pytest -q tests/test_regression_runs.py tests/test_doc_registry.py tests/test_doc_links.py`.

---

## 8. Hazards particular to a sweep

| hazard | looks like | the check |
|---|---|---|
| the generated suite flatters the knob | `c = 0`, 100 % at every positive value | the veto leg; and the report says *"the suite rewards exactly what the knob does"* |
| grid extended after seeing numbers | "we also tried 0.35" | the grid is frozen; anything else is post-hoc and in no verdict |
| a knob that moves the index | quality changes that survive `--no-tune` | T0.b hash per pass |
| tune.toml left in the playground | a later playground run grades a tuned engine | `git status --short` empty after every pass |
| source constant edited mid-run | baseline shifts between passes | `git -C ~/my_programs/fux status --short` empty; sha unchanged |
| selecting the veto's survivor | trying values until `q022` stops breaking | selection happens once, by the frozen rule, before the veto runs |
| `fixed` on the playground reported as a win | "+3 goldens" | `N = 50`: reported, never tested, never claimed |
| a recommendation in the report | "we suggest shipping 0.25" | the table has no recommendation column; the change is Arpit's ADR-TUNE amendment |
