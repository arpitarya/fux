---
type: OpenItem
id: W-188
title: "W-188 — the Node reader becomes a column in every capture, not only in CAP-6"
description: "Arpit, 2026-09-15: Node search versus Python search on ranked lists, what moved, hit@k, the answer layer and speed. The harness already returns Node's ranked results per query and throws them away after timing them. Node vs Python is a PARITY check — any difference is a defect — and it is captured and reported, not gated."
status: open
lane: agent
timestamp: 2026-09-15T00:00:00Z
filed: 2026-09-15
ball: agent
---

# W-188 — Node as a column in CAP-1, CAP-2, CAP-3 and CAP-4

✅ **THE HARNESS AND THE REPORT ARE BUILT (2026-09-15). The RUN is what is
left.** `bench.py` gained `answer_node`, `--node-arms` on `hits` and `answers`,
`RANK_PAIRS` with the `version`/`reader`/`tier` split, and `parity.jsonl`;
`report.py` gained the parity fill and `TEMPLATE.html` a reader-parity slide.
Exercised end to end on a **synthetic fixture** — four arms through CAP-1,
CAP-3, CAP-4 and the parity table, with both callout branches. 🔴 **No filed
number exists yet**, because the measurement runs on Arpit's machine
(`fux-benchmark`, node, the corpora ladder) and **cannot run from a Cowork
bridge shell** — no interpreter here can import `fux` and the arm venvs are not
reachable. This file is the spec; the run is Claude Code's.

**Model: Sonnet** to execute the run; **Opus** for the parity verdict if the
discordant count comes back non-zero.

## What is left, exactly

```bash
bin/bench.py latency --run <r> --corpus docs-00100 --node-arms B-node
bin/bench.py hits    --run <r> --corpus docs-00100 --node-arms B-node
bin/bench.py answers --run <r> --corpus docs-00100 --node-arms B-node
bin/bench.py rankdiff --run <r>          # writes parity.jsonl as well
bin/bench.py file    --run <r> --dest <fux>/work/regression/<r>
bin/bench.py report  --dest <fux>/work/regression/<r>
```

⚠ **`answer_node` has never been executed.** The Node reader accepts `--band`
(`node/fux.mjs`), but whether its payload carries the same `confidence` shape
Python's does is exactly what nobody has checked — if the block is absent every
Node row will read `answered` and the column will look like a fabrication
machine. **Check one question by hand before the sweep.**

## The ruling

> **Arpit, 2026-09-15:** *"in benchmark I want few more numbers — this is for
> node search versus Python search … ranked list, what moved, hit@k, answer
> layer and speed."*

Two forks he settled in the same exchange:

- **Every run, as a column** — `B-node` joins CAP-1, CAP-2, CAP-3 and CAP-4,
  exactly as decision 12 put it in CAP-6. Not a separate parity run.
- 🔴 **`B-node-nograph` is NOT an arm** (Arpit, later the same day): a benchmark
  measures what ships and the graph tier ships on. **The arms are `A` · `B` ·
  `B-node`.** Decision 16a.
- **A reported capture, not a gate** — a disagreement is shown (discordant
  count, first differing rank, max score delta) and a person reads it. A
  benchmark rules no threshold (decision 6).

Stated once in [SR-WORK-BENCHMARK](../../records/0053_WORK-benchmark.md)
**decision 16**. This file restates none of it.

## Why it is nearly free, and where the cost actually is

🔴 **The harness already has the results and throws them away.**
`fux-benchmark/bin/bench.py::ask_node` runs `node fux.mjs ask --json` and
returns `(ms, results)` — the ranked list is in hand at the moment it is timed,
and only `ms` is kept. CAP-1 and CAP-3 for the Node column are a *retention*
change, not a new measurement.

⚠ **CAP-4 is the one that costs a pass.** `answer` is a different verb; the
Node reader has it (`node/README.md` line 102) and claims *"same ids, same
order, same locators, same band"*. Nobody has ever checked that claim with an
instrument.

## Definition of done

1. **CAP-1** — `B-node` rows in `ranked-lists.jsonl`, same schema as the Python
   arms.
2. **CAP-2** — the movement table gains one **reader pair**: `B` vs `B-node`. ⚠ **Read the other way round from an A/B
   pair**: 0 discordant is the expected result, and a non-zero one is a defect
   report rather than a finding.
3. **CAP-3** — hit@k for both Node arms against the same planted key. Identical
   to `B`'s, or one reader is wrong.
4. **CAP-4** — the answer layer on Node: answered/declined/fabricated **and**
   `band`, `answerable`, `missing`, and the **cited line ranges**. The README's
   parity claim is about locators too, so a column that compares only the
   verdict tests less than the claim.
5. **CAP-5 and ingest/build have NO Node column, by construction** — the Node
   reader writes no index. The slides say that rather than showing a blank.
6. **A parity block on the report**: exact-list agreement rate, first differing
   rank, and **max |Δscore|** against a stated tolerance — the float question
   `PRE-REGISTRATION-NODE`'s `log()` cell left open and that the retired N0–N4
   table never measured.

## The extra numbers worth taking while the harness is open

Not ruled; proposed here so the decision is Arpit's and the list is in one place.

| number | why it is worth the pass |
|---|---|
| **cold start, separated** | today's Node p50 is **one process per query**, so it carries `node` boot. A warm-process pass beside it splits the reader's work from its startup — otherwise the column silently measures Node booting |
| **peak RSS per query** | W-161's graph tier rebuilds in memory (~2.4 s at 10 000). Time is half the price; **memory is the half nobody has** |
| ~~the tier's effect on ranking~~ | 🔴 **STRUCK by decision 16a** — not a benchmark column. The question is real and is W-161's, with its own run |
| **failure parity** | same refusal, same exit code on a stale index (`fux.index.v2`), a missing `pii.toml`, a retired config key. W-186 showed three refusals in a row; whether Node refuses identically is unknown |
| **the 10 000 tier for both readers** | the column exists at 100 and 1 000. The design point is 10 000 (SR-WORK-SCALE) and that is where the tier's cost explodes |

## Out of scope

- **Making any of it a gate.** Ruled: reported, not gated (decision 4 keeps
  gates in `tests/`).
- **Node's own unit suite.** `node --test node/test/*.test.mjs` is not a
  benchmark.
- **Changing what the Python arms capture.** The seven captures are unchanged.

## Hazards

- 🔴 **A non-zero discordant count between readers is a DEFECT, and the report
  must not read like a quality delta.** Same table shape as A-vs-B, opposite
  meaning — say so on the slide, every run.
- ⚠ **One Node arm in four more captures adds a pass per capture.** Interleave
  inside the repeat, as decision 12a's run already does, or the columns measure
  different machines.
- ⚠ **`B` is an editable install of the working tree** (decision 12a's warning).
  Two runs of "arm B" are not necessarily the same engine, and that now applies
  to the parity numbers too.
