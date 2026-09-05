---
type: Run Report
run: 2026-09-05-node-log-divergence
classification: blind
date: 2026-09-05
---

# W-107 Phase 0 — how far apart are Python and Node, and does it flip an order?

**The question Arpit's `log()` decision turns on.** W-107 offers **(a)** one
portable `log` in both runtimes — a Python-wide ranking change — or **(b)** the
Node arm compares scores at `round(9)`. This is the measurement he picks from.

## Authorship — classification `blind`

| artifact | author | could reach |
|---|---|---|
| the probe, the dump, the Node scorer, the comparator | Claude Code, 2026-09-05 | the corpora and the code; **no evaluation judgments exist for this question** |
| the query sets | pre-existing (playground goldens, `fux-benchmark` `pairs.jsonl`) | — |
| this report | Claude Code | everything |

**`blind` on its own terms.** There is no relevance judgment, no golden and no
prior score to be exposed to: the measured quantity is *do two runtimes compute
the same double*, and the answer is a property of the two libms, not of any
ranking anyone graded. The corpora were not selected on any prior result.

## What was measured, and on what

| | |
|---|---|
| Python | CPython **3.14.2**, macOS 26.3.1, arm64 (Apple libm) |
| Node | **v24.13.0**, V8 13.6.233.17, darwin/arm64 (fdlibm port) |
| corpora | `fux-playground` **re-derived**, 10 documents, its 50 goldens · `fux-benchmark` **`t10000`**, **10 000 documents**, its 240 `pairs.jsonl` queries |

**One script, two runtimes.** `evidence/dump.py` pulls the scoring inputs out of
`query/scan.py`'s own candidate pass — the same `df`, `n` and `avg_wlen` the
shipped scan derives — and writes Python's score beside each.
`evidence/score.mjs` reads that file and writes Node's. The JS is a
**transcription** of `bm25f.score_record`: same loop order, same accumulation
order, same expression shape, because float addition is not associative and a
tidier `reduce` would add a second source of divergence on top of the one under
test. Doubles cross the boundary as **hex**, never decimal.

## Result 1 — `log` DOES diverge on this machine, by one ulp, and never at `round(9)`

`evidence/logprobe-output.txt`:

| population | differ | max relative | differ after `round(9)` |
|---|---|---|---|
| **`idf`** — every distinct `(n - df + 0.5)/(df + 0.5) + 1` the two corpora produce | **0 / 13** | 0 | 0 |
| **`wide`** — 100 000 seeded doubles, log-uniform over `[1e-6, 1e6]` | **655 / 100 000 (0.655 %)** | **2.211e-16** | **0** |

- **The hazard is real.** 0.655 % on darwin/arm64 is the same order as the
  1 095 / 100 000 W-107 cites for V8-vs-glibc 2.39. Two libms, two answers.
- **Every difference is one ulp.** `2.211e-16` relative is the last bit of a
  double, and **not one of the 655 survives `round(9)`** — seven orders of
  magnitude below what that rounding can see.

🔴 **The `idf` population is 13 distinct values, and that is a fact about these
two corpora, not about fux.** `idf` is a function of `(df, n)`, and both corpora
have narrow `df` distributions — the playground has ten documents, and
`t10000`'s queries are synthetic and near-unique. **A corpus with a wide `df`
spread samples far more of the argument space, and a zero here is not proof
that byte identity holds in general.** It is why result 2 is reported as a
count and not as a guarantee.

## Result 2 — 0 discordant scores, 0 discordant top-5, on 197 233 scored documents

`evidence/compare-playground.txt`, `evidence/compare-t10000.txt`:

| corpus | queries | documents scored | scores differing bit-for-bit | at `round(9)` | queries with a different top-5 |
|---|---|---|---|---|---|
| playground (10 docs) | 50 | 433 | **0** | 0 | **0** |
| `t10000` (**10 000 docs**) | 240 | 196 800 | **0** | 0 | **0** |

The top-5 comparison was run twice per query — once on `rank.py`'s real sort key
`(-round(score, 9), id)` and once on an **exact** `(-score, id)` key, so a flip
hidden by the rounding would still show. Neither found one.

Per-query rows: `evidence/per-query-playground.csv`,
`evidence/per-query-t10000.csv` — 290 rows, one per query, with each query's
candidate count and how many of its scores differed.

## Result 3 — the bar Node has to clear: Python's own scan p95 at 10 000 documents

`evidence/latency.py`, in-process, scan path, no accelerator (Node has no
derived plane in Phase 1), warm, 240 queries:

| n | mean | p50 | **p95** | p99 | max |
|---|---|---|---|---|---|
| 240 | 48.2 ms | 48.1 ms | **50.2 ms** | 52.3 ms | 58.2 ms |

## 🔴 The limit of this run, stated rather than discovered

**One platform pair was measured: CPython 3.14.2 on Apple libm against Node
24 / V8 on darwin/arm64.** W-107's hazard note cites **glibc 2.39**, and this
machine has no Linux. That pairing — the one CI would run — **was not
re-measured here and is not claimed.** Node 20 and 22, the versions the CI
matrix names, were not run either; only 24 is installed.

**What that means for the decision:** the finding *"one ulp, never at
`round(9)`"* is a property of two well-behaved libms and is very likely to hold
for glibc as well, **but this run cannot say so**, and W-107 Phase 1 must not
proceed on the assumption. Re-running `evidence/logprobe.py` +
`evidence/logprobe.mjs` on a Linux runner is one command and settles it.

## Reproduce

```bash
# the 10 000-document corpus
cp -R ~/my_programs/fux-benchmark/corpora/t10000/repo /tmp/t10000
cd /tmp/t10000 && printf '[sources]\n' > fux.toml \
  && mkdir -p .fux/sources && printf 'docs\n' > .fux/sources/dirs && fux ingest

E=work/regression/2026-09-05-node-log-divergence/evidence
python $E/dump.py /tmp/t10000 ~/my_programs/fux-benchmark/corpora/t10000/eval/pairs.jsonl /tmp/t10k.json
node   $E/score.mjs /tmp/t10k.json /tmp/t10k-scored.json
python $E/compare.py /tmp/t10k-scored.json /tmp/per-query.csv

# the log probe itself
python $E/logprobe.py /tmp/t10k.json /tmp/logargs.json
node   $E/logprobe.mjs /tmp/logargs.json

# the latency bar
python $E/latency.py /tmp/t10000 ~/my_programs/fux-benchmark/corpora/t10000/eval/pairs.jsonl
```

## Nothing is claimed above 10 000 documents

The larger corpus **is** 10 000 documents — the design point exactly, not above
it. No threshold, budget or bound at 50 000 or 100 000 is stated or implied.
