---
type: Report
run: 2026-09-16-node-column
item: W-188
classification: surface capture
description: "The Node column in CAP-1/2/3/4, run for the first time. Reader parity is EXACT: 60 of 60 ranked lists identical with max |Δscore| 0.000000, hit@k identical at every k, and 0 of 52 answer-layer rows differing in verdict, band or citation. `answer_node` executed for the first time and the confidence block the item warned might be missing is present and identical."
filed: 2026-09-16
---

# REPORT — the Node column, measured

**W-188's harness was built on 2026-09-15 and exercised only on a synthetic
fixture. This is the run.** [SR-WORK-BENCHMARK](../../../records/0053_WORK-benchmark.md)
decision 6 — *a benchmark rules no threshold* — so this is a **surface capture**
and files no verdict.

**Reproduce** (from `~/my_programs/fux-benchmark`):

```bash
python3 bin/bench.py prepare  --run 2026-09-16-node-column --corpus docs-00100
python3 bin/bench.py latency  --run 2026-09-16-node-column --corpus docs-00100 --node-arms B-node
python3 bin/bench.py hits     --run 2026-09-16-node-column --corpus docs-00100 --node-arms B-node
python3 bin/bench.py answers  --run 2026-09-16-node-column --corpus docs-00100 --node-arms B-node
python3 bin/bench.py rankdiff --run 2026-09-16-node-column
python3 bin/bench.py file     --run 2026-09-16-node-column --dest <fux>/work/regression/2026-09-16-node-column
~/my_programs/fux/.venv/bin/python bin/bench.py report --dest <fux>/work/regression/2026-09-16-node-column
```

⚠ **The last line needs a different interpreter, and that is a real trap.**
`python3` on this machine is **3.9.6**; `report` imports `tomllib`, which is
3.11+. Every other subcommand runs fine on 3.9, so the failure lands at the very
end of a long run. Filed in [`work/MACHINE.md`](../../MACHINE.md).

**Three arms and a pseudo-arm**, `docs-00100`, 60 timing queries, 42 judged
questions, 52 answer-layer questions (10 planted unanswerable):

| arm | what it is |
|---|---|
| `A` | `fux-engine` 1.0.0 |
| `B` | `fux-engine` 2.0.1 |
| `B-node` | **the vendored Node reader over `B`'s index** — a column, never a run of its own |

---

## 🔴 The headline: reader parity is EXACT

**Three pair kinds, three readings** (decision 16). `B|B-node` is a **parity**
pair — 0 discordant is expected and **any difference is a defect in one reader**:

| pair | kind | identical | discordant | max &#124;Δscore&#124; |
|---|---|---:|---:|---:|
| `A`&#124;`B` | **version** — the finding | 31 / 60 | 29 | 0.754260 |
| **`B`&#124;`B-node`** | **reader** — a difference is a bug | **60 / 60** | **0** | **0.000000** |

**`max |Δscore| = 0.000000`** is the number
`PRE-REGISTRATION-NODE`'s `log()` cell left unmeasured. Not *small* — **zero**,
across every query, at every rank compared.

### CAP-3 — hit@k, identical at every k

| arm | hit@1 | hit@5 | hit@10 | hit@20 | hit@50 |
|---|---:|---:|---:|---:|---:|
| `A` 1.0.0 | 0.833 | 0.952 | 1.000 | 1.000 | 1.000 |
| `B` 2.0.1 | 0.833 | **0.976** | 1.000 | 1.000 | 1.000 |
| **`B-node`** | 0.833 | **0.976** | 1.000 | 1.000 | 1.000 |

### CAP-4 — the answer layer, and the hazard that did not materialise

🔴 **`answer_node` had never been executed.** W-188 warned: *"if the block is
absent every Node row will read `answered` and the column will look like a
fabrication machine. Check one question by hand before the sweep."*

**Checked by hand first, then measured.** The Node reader's `--band` payload
carries the full `confidence` block — `band`, `answerable`, `failed`,
`coverage`, `separation`, `separation_floor`, `doc_coverage`, `support`,
`verified`, `missing` — and Python's differs only in JSON float rendering
(`0` against `0.0`).

| arm | answered | declined | fabricated |
|---|---:|---:|---:|
| `A` 1.0.0 | 42 | **0** | 10 |
| `B` 2.0.1 | 24 | 18 | 10 |
| **`B-node`** | **24** | **18** | **10** |

**0 of 52 questions differ between `B` and `B-node`** in verdict, band **or**
citation, and `coverage` is identical on all 52. Both readers emit the same
three bands (`grounded`, `partial`, `weak`).

### CAP-2 — latency

Median of medians, `n = 10` after 3 warm-ups, interleaved:

| arm | median | p95 of medians |
|---|---:|---:|
| `A` 1.0.0 | 52.4 ms | 53.7 ms |
| `B` 2.0.1 | 78.4 ms | 80.0 ms |
| `B-node` | **63.7 ms** | 64.7 ms |

⚠ **This is one tier and one machine, and it does not restate
[W-179's result](../2026-09-15-node-column/report.md).** That run's finding —
the Node reader is **flat in corpus size** and the graph tier is the whole of its
growth — needed three tiers. This is `docs-00100` only.

## ⚠ Two things worth stating rather than smoothing

**`B-node` has 600 non-warmup latency rows where `A` and `B` have 602.** Chased
rather than assumed: the two extra rows per arm are `class: ingest` and
`class: build`, with an empty `query_id`. **The Node reader writes no index**, so
it has neither by construction — CAP-5 and ingest get no Node column for the
same reason (decision 16).

**All three arms fabricate on 10 of 10 planted unanswerables.** That is the
known abstention shape, **fourth recorded occurrence**, and it is not this run's
finding — `A` is worse (0 declines to `B`'s 18) but neither declines on a
planted unanswerable. It is [W-176](../../open/W-176-abstention-gates.md)'s.

## What this does NOT establish

- **No threshold is ruled.** A benchmark rules none (decision 6).
- **Nothing about the graph tier's worth.** The tier-off arm was retired from the
  benchmark by decision 16a; what the tier is *worth* stays
  [W-161](../../open/W-161-graph-composed-ask.md)'s and is unmeasured.
- **One tier.** `docs-01000` and `docs-10000` are not run here.
- ⚠ **Arm `B` is an editable install** reporting `2.0.1`, and is not the
  published `2.0.1`.

## Authorship

| what | who |
|---|---|
| corpora, queries, judged key | `fux-benchmark`'s generators, deterministic and seeded |
| the harness and this run | this session |

**A surface capture** — no arms compared against a threshold, no judgement
authored for this run, so no `blind`/`informed` classification
([`README`](../README.md) §Per-run contract row 7 exempts one).
