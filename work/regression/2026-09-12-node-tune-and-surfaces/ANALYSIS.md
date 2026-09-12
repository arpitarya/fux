---
type: Analysis
name: node-tune-and-the-four-uncompared-surfaces-analysis
description: "What the run diagnoses, turned into specific improvements: what shipped in the same change, what is owed and to whom, and the one cause behind all five findings — an instrument aimed at one surface out of five."
timestamp: 2026-09-12T00:00:00Z
---

# Analysis — five findings, one cause

## The cause, stated once

**Every finding in [the report](report.md) is the same shape: a surface that
was transcribed and never compared.** Not one of them is a subtle arithmetic
divergence of the kind the differential law was built for. They are a missing
config read, three payloads with the wrong key names, a handler reading the
wrong argument, and a chunker running on the wrong bytes — the sort of thing
that is *obvious the moment two implementations are put side by side*, and
invisible for as long as they are not.

The previous run's find ([2026-09-12-node-arm-rungs](../2026-09-12-node-arm-rungs/report.md)
§3) was the special case: the arm's Python side called `scan.ask` while
`fux find` calls `run_query`, so **both readers were ignoring the same file**.
This run is the general case: the arm called two verbs out of nine.

**The lesson is not "write more tests".** It is that a differential harness
measures exactly the seam it is pointed at, and says nothing — while looking
green — about every seam it is not.

## Improvements — what shipped in this change

| # | improvement | where |
|---|---|---|
| 1 | The Node reader reads `.fux/tune.toml` and honours `--no-tune` | `node/src/config/{toml,tune}.mjs`, `node/src/query/{run,rerank}.mjs` |
| 2 | The Node reader reads `.fux/output.toml`, folded in once before dispatch | `node/src/config/output.mjs`, `node/fux.mjs` |
| 3 | The archived declaration is read LIVE from `.fux/sources/dirs`, not trusted to the record's stamped property | `node/src/ingest/{sourcelist,gitdir}.mjs` |
| 4 | `explain`/`graph`/`path` emit Python's payloads, PPR expansion and all | `node/src/graph/walk.mjs`, `node/src/verbs/graph.mjs` |
| 5 | The MCP handlers read the advertised argument names and return every key | `node/src/verbs/mcp.mjs` |
| 6 | `fux.api` ranks through `run_query`, band floors included | `src/fux/api.py` |
| 7 | Node declines to refer a document it cannot decode | `node/src/decode/registry.mjs`, `node/src/verbs/answer.mjs` |
| 8 | The arm compares five surfaces instead of one | `tools/differential/node_arm.py` |
| 9 | The transcribed CONSTANTS are held equal by test, because the arm structurally cannot | `tests/test_node_config_parity.py` |
| 10 | `pyRound` takes `ndigits` — `mcp.py` rounds to six and there was one rounding routine fixed at nine | `node/src/compat/pyfloat.mjs` |

## Improvements this run does NOT deliver, and who owns each

### A · 🔴 The arm still cannot run on a GitHub runner

`node-arm.yml`'s `ladder` job runs the manifest check always and the arm itself
only when `FUX_GOLDEN_CORPORA` points at a checkout that has the rungs. A
runner does not: the corpora are not committed, `rung-10000` is 120 MB, and the
builder hard-codes two absolute paths. **So PRE-REG-NODE-2 §4's per-push
cadence is met in fux-lab, on one OS.**

The routes out — a self-hosted runner, a committed small rung, a portable
builder — are each a decision and **none is taken**. Carried to Arpit as part
of W-107's close-out rather than chosen here.

```bash
# what a runner CAN do today, and does
uv run python tools/differential/ladder_check.py
```

### B · Node's latency is unmeasured, and there is no instrument

N4's p95 fence moved to `fux-benchmark` ([SETUP-BENCHMARK](../../setup/fux-benchmark.md)),
which is **unbuilt**. Nothing in this run times anything, and nothing should:
[L9](../../../docs/adr/0011_LAW-9-environments.md) puts benchmarks in
`fux-benchmark` and this ran in the repo and in fux-lab.

⚠ **The shape is not alarming and that is an argument, not a measurement.**
Node's scan is the same algorithm over the same shards; nothing in this change
adds a pass over the corpus — `tune.toml`, `output.toml` and `sources/dirs` are
three small file reads per query, and the reranker reads at most 20 documents
and only when `rerank_weight > 0`. **That is a structural claim and it does not
substitute for the fence.**

### C · `verify`, `--why`, `--receipt`, `--journal` have no Node twin

Out of scope by W-107 R6, so no arm covers them. Stated so that "five surfaces
compared" is not read as "every surface compared".

### D · The `find --under` semantics differ between `fux.api` and the CLI

`fux.api` applies a component boundary, the CLI a bare prefix. `fux.api` is
frozen ([ADR-API](../../../docs/adr/0156_api.md) decision 1), so **which one is
right is a ruling, not a cleanup** — recorded in decision 6 and left for Arpit.

```bash
# the divergence, in one command each
uv run python -c "import fux; print([r.loc for r in fux.open('.').find('adr', top=20, under='docs/adr')])"
uv run fux find adr --top 20 --under docs/adr --json
```

### E · Unresolved: whether the two API graph shapes should stay

`explain`/`graph`/`path` return one shape from the CLIs and another from the
two library surfaces. **The cause is known** — `api.py` grew its own helpers —
and the fix is not obvious: collapsing them changes a frozen surface. Stated as
unresolved rather than quietly aligned.

## What would have caught each finding earlier

| finding | the instrument that was missing |
|---|---|
| tune not read | an arm aimed at `run_query` rather than `scan.ask` — closed in the previous run |
| graph payloads | comparing whole payloads for the verbs that carry no score |
| MCP handlers | comparing two **servers**, not two description files |
| `api.py` tune | comparing the library surfaces at all |
| decoded documents | comparing `answer`, which no arm had ever run |

⚠ **Four of the five are "compare the thing".** That is worth saying plainly: no
new technique was needed, and no measurement was hard. The work was pointing an
instrument that already existed at the surfaces it had never been aimed at.
