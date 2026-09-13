---
type: Report
name: node-tune-and-the-four-uncompared-surfaces
description: "Closing ADR-NODE-SEARCH decision 8 — the Node reader now reads .fux/tune.toml and .fux/output.toml, and this repo goes 90 of 174 discordant to 0 of 199. Then the more general version of the same defect: the arm compared `find` and `ask` and nothing else, so four more surfaces had been transcribed and never checked. Each was wrong, and one of them had shipped to npm."
classification: blind
timestamp: 2026-09-12T00:00:00Z
---

# Node's tune file, and the four surfaces nobody was comparing — W-107

## 0 · Classification — `blind`

### Authorship

Per [ADR-RS](../../../docs/adr/0133_predictions.md) decisions 11–15.

| artifact | author | could reach |
|---|---|---|
| the corpora (`rung-00100`, `rung-10000`) | built 2026-09-12 by `build_golden_rung.py`, W-136 phase 2 | none of this run's queries — the rungs predate it |
| this repo's own index | fux's own `.fux/index/`, ingested from its own documents | — |
| the query set | **derived from each corpus's own vocabulary** by `queryset.py`'s fixed rule, capped by position; the repo arm uses the hand-written `REPO_QUERIES` set, unchanged from the previous run | the corpus. **no** golden questions, **no** judgments, **no** prior scores |
| the code under test | this session | the queries, which are its own harness's |
| the analysis | this session | everything above |

⚠ **Blind is a claim about exposure, not about care.** The code and the
analysis are the same session's, so the honest statement is: *the query sets
were fixed before the code changed, and no answer key was opened.* The golden
answer key was not read, by any tool, at any point.

⚠ **This is a two-reader agreement measurement, not a quality one.** Nothing
here says fux ranks well. It says two implementations of fux rank identically,
which is the only thing the differential law claims.

## 1 · What was measured

**Two arms, per [PRE-REG-NODE-2](../../benchmark/PRE-REGISTRATION-NODE-2.md) §3
and the harness's own split:**

| arm | what a discordance means |
|---|---|
| **contract** (`--python-tune on`) | what `fux find` answers on this corpus, tune and all. The two readers disagree, whatever the cause |
| **transcription** (`--no-tune`, **both sides**) | the engine's own answer. A discordance is a Node transcription defect and nothing else |

## 2 · The headline — decision 8 closed

`.fux/tune.toml` on this repo sets `rerank_weight = 0.3` and nothing else.

| | before | after |
|---|---|---|
| **contract arm** | **90 of 174 discordant** | **0 of 199** |
| **transcription arm** | 0 of 174 | **0 of 199** |

**The before numbers are [the previous run's](../2026-09-12-node-arm-rungs/report.md)
§3**, measured the same day with the same harness on the same index.

The golden ladder, both ends, manifest-verified before a byte was read:

| rung | comparisons | discordant |
|---|---|---|
| `rung-00100` | **775** | **0** |
| `rung-10000` | **775** | **0** |

⚠ **Every golden rung's tune is all-defaults**, so the ladder runs say nothing
about the tune fix — which is exactly why they did not surface it. They say the
three newly-compared surfaces agree at 100 and at 10 000 documents.

Per-query rows for all four runs are under [`evidence/`](evidence/), one JSONL
object per comparison, `_condition` first.

### Headroom, both directions — [ADR-RS](../../../docs/adr/0133_predictions.md) decision 22

**A paired run with an unusual shape: there is no better arm.** The endpoint is
a discordance count, so *improvement* is not defined, and the only question
decision 22 can ask is whether a zero is a real zero or a saturated instrument.

| direction | headroom | why |
|---|---|---|
| **improvement headroom** | **0 of 199** on the repo after the fix; **90 of 174 before it** | the comparisons wrong in both arms — already discordant and therefore fixable. Before the change there were 90; after it there are none, which is the whole claim |
| **regression headroom** | **199 of 199** on the repo, **775 of 775** per rung | the comparisons right in both arms, every one of which could have gone discordant. Nothing is structurally forced to agree, and the hazard pins plus the `df == 1` singletons are shapes chosen to break a reader |
| **observed** | **0 discordant**, all four runs | |
| **positive control** | 🔴 **the instrument fires, and it fired five times in this run** | the tune gap (90 of 174), three payload-shape divergences, and a wrong-bytes citation. A null from a harness that had just produced five real findings is a null about the readers, not about the instrument |

🔴 **The previous run predicted this, in writing, and was right.** Its report
closed with: *"a divergence living only in a shape neither the pins nor those
bands touch — `answer`'s passage locators, `explain`, `path`, an `--expand`
query — would return 0 here and be no less real."* Three of the four surfaces
named there turned out to be diverging at the time that sentence was written.
**A stated coverage limit is not a hedge; it is a prediction, and this one paid
out within a day.**

⚠ **What this run's zero does NOT clear, in the same spirit.** `--expand` is
still uncompared, and so are `verify`, `--why`, `--receipt` and `--journal` —
the last four because they have no Node twin at all. A divergence living only
there would return 0 here and be no less real.

## 3 · The four surfaces that had never been compared

The arm compared `find` and `ask`. **Every other surface was transcribed and
never checked**, and each was found wrong on the first run after the arm
reached it.

### 3.1 · `explain` · `graph` · `path` — different key names in all three

| | Python CLI | Node CLI (before) |
|---|---|---|
| `explain` | `{doc, edges, community}` | `{id, community, members, edges}` |
| `graph` | `{nodes: [{path, id, role, score}]}` | `{seeds, hops, nodes: [{id, distance, community}]}` |
| `path` | `{from, to, paths: [{hops, reliability}]}` | `{from, to, hops, route, weight}` |

Node's `graph` ran **its own breadth-first walk** where Python runs a PPR-lite
expansion — so the two verbs did not merely print differently, they answered a
different question. `node/src/graph/walk.mjs` is the port that closed it, lazy
walk and all.

⚠ **The Node verbs were not arbitrary — they were `api.py`'s shapes.** The
Python *library* surface grew its own simpler graph helpers, and Node's CLI had
been written against those rather than against Python's CLI. That is now
explicit: the CLIs agree with each other, the two APIs agree with each other,
and [ADR-API](../../../docs/adr/0156_api.md) decision 6 states that the two
pairs differ.

### 3.2 · `mcp` — a shipped defect, in a package on npm

| tool | advertised in `mcp-tools.json` | what Node's handler read |
|---|---|---|
| `fux_passage` | `path`, `line_start`, `line_end` | **`args.id`** |
| `fux_related` | `path` | **`args.id`** |

Every conformant client got an **empty result reported as success**.
`fux_search` additionally returned five of the nine keys Python returns and
**none of `confidence`** — the one key
[ADR-CONFIDENCE](../../../docs/adr/0141_confidence.md) decision 11 makes
unconditional on MCP, precisely because a tool call cannot pass a flag.

`[mcp] top` was hard-coded to `5`, so `.fux/output.toml` did not reach the
surface ADR-OUTPUT decisions 16–17 are about.

### 3.3 · `fux.api` — the Python library was ranking without its own tune file

Not a Node defect at all. `api.find`/`api.ask` called `query.scan.ask`
directly:

| query | `fux.api` | `fux find` |
|---|---|---|
| `graph plane` | 6.392573 | **8.310345** |
| `getUserName` | 13.792954 | **17.930840** |

**The same defect as decision 8, in the third of the three surfaces W-107 R3
names.** The band was also being built at the engine's default floors while the
ranking beside it used the repository's.

### 3.4 · 🔴 `answer` cited line numbers into text the index never held

The worst of the four, because it produces a **confident wrong citation**
rather than an absence.

Python's refer plane runs a cited document's bytes back through the decoder
plane before chunking, so a `.csv` is re-scored as the Markdown table ingest
indexed. Node has no decoders and was chunking the **raw bytes** — emitting
`path:L20-L28` locators into a file whose text the index never contained.

Found by comparing the two library surfaces: `answer("rollback")` returned a
different document, a different passage and a different locator in each
runtime.

**Node now declines rather than guessing** — the same shape the never-fetch
rule takes for an unreachable URL
([ADR-NODE-SEARCH](../../../docs/adr/0155_node-search.md) decision 11).

## 4 · Two differences that are NOT defects, excluded by name

| | why |
|---|---|
| `ranked_by` — `"accelerator"` vs `"scan"` | Python's MCP surface opts into the accelerator and Node has none. The differential law asserts the two paths return the same documents in the same order, so the label is the only difference and each side's label is true of itself |
| `answer` equality, where Python cited a decoded document | Once Node skips a candidate, the two rescore over **different passage populations** — `df` is computed across the candidate set — so every score downstream legitimately differs. **The invariant is asserted instead, on every answer: nothing Node cites is a decoded document** |

Neither is a loosened comparison. Both are named keys and named conditions.

## 5 · What this run does NOT establish

- 🔴 **It is not an N5–N8 result.** PRE-REG-NODE-2 §4 requires the OS/Node
  matrix; this is one machine on Node 24. §2 makes the arm **standing rather
  than a gate**, and a green arm is filed, not announced.
- **Node's latency is still unmeasured.** N4's fence moved to `fux-benchmark`,
  which is unbuilt.
- **`verify`, `--why`, `--receipt` and `--journal` have no Node twin at all**
  (W-107 R6), so no arm covers them and none pretends to.
- **The golden questions were not opened**, and the arm has no reason to want
  them: it compares two readers against each other, never against an answer key.

## Reproduce

```bash
# the repo arm, both halves
uv run python tools/differential/node_arm.py . --python-tune on
uv run python tools/differential/node_arm.py . --python-tune off

# the ladder, both ends (needs fux-lab's corpora; manifests are verified first)
uv run python tools/differential/node_arm.py --rung rung-00100
uv run python tools/differential/node_arm.py --rung rung-10000

# the constants the arm structurally cannot compare
uv run pytest -q tests/test_node_config_parity.py tests/test_node_twins.py
cd node && node --test
```

⚠ **The graph lane needs `fux build` on the corpus**, because Python's graph
verbs refuse without the derived plane and Node's do not. The harness says so
and skips rather than filing the refusal as a discordance.
