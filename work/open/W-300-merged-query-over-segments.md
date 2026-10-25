---
type: Handoff
name: W-300
description: "W-298 step 3, ruled 2026-10-25: one `fux_search` ranks the repo's index plus every pinned package segment — the query hashed once per distinct identifiers digest, `df` / `n` / `total_flen` summed across segments, one `rank()` call, a foreign segment refused by name; an optional `scope` = repo|packages|all (default all) on the MCP tool. Python and Node, held equal by the differential law."
item: W-300
filed: 2026-10-25
filed_by: "Arpit (Cowork, Fable 5.1)"
updated: 2026-10-25
updated_by: "Arpit (Cowork, Fable 5.1)"
ball: agent
---

# W-300 — one query over many segments, statistics merged

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | The query is hashed **once per distinct `identifiers` digest** — the consumer's `identifiers.toml` for the repo, each segment's shipped `identifiers.toml` for that segment. Term keys are unsalted `blake2b(term)`, so equal tokens meet | identifier-family tokens match inside a package built under other rules; nothing silently misses | ⏳ |
| 2 | Per segment: candidates + per-segment `df`, `n`, `total_flen` (the B2 scan or the runtime postings, as today). Then **sum**: `df = Σ df`, `n = Σ n`, `total_flen = Σ`; one `avg_wlen`; **one `rank()` call** over the union | one yardstick, shared idf, deterministic for a pinned set (L4) | ⏳ |
| 3 | A segment whose `_format` / `analyzer` / `tf_fields` differ from the reader's is **refused by name** before the scan — never scored, never skipped silently | lockstep, as ruled | ⏳ |
| 4 | `fux_search` gains optional `scope`: `repo` · `packages` · `all` (default). `fux ask --scope` mirrors it. Still three MCP tools | the lever against a large package filling the top-k | ⏳ |
| 5 | Node: the same four steps in `node/src/query/`; one differential test over repo + fixture segment | the same answer on every machine | ⏳ |
| 6 | Pre-register and run the merged-vs-repo-only comparison under L13's standing bar on the fixture corpus; file under `work/regression/` | a ranking change ships only through the bar | ⏳ |

**Arpit, 2026-10-25 (Cowork):** *"Yes, all three as recommended"* — `scope` =
repo|packages|all default all; wire compat lockstep; the 10 000 ceiling counts the
merged corpus. Design accepted in chat: *"This looks good to me."*

**Model:** Claude Code, **Opus** — the ranking arithmetic and the differential law.
**Ratified, not built.**

## Why

- `rank()` already takes `df`, `n`, `avg_wlen` as inputs, and all three are
  additive. The merge is arithmetic at the seam, not a new ranker.
- Shared idf is the **correct** behaviour: a word common in the package is
  common in the corpus the query runs over. "A big package drowns the repo" is
  answered by `scope`, not by a hidden per-segment prior.
- Hashing the query per identifiers digest is the one thing the engine does not
  do today, and without it a package's `RF-{n}`-style identifiers never match.

## What to build

- `src/fux/query/scan.py` / `derive/accel.py` — a `Segment` seam: each returns
  `(candidates, df, Corpus)`; a new `merge_corpora()` sums them. `anchor_tf`
  folds **within** a segment only — a package's edges never point into the repo.
- `src/fux/query/rank.py` — unchanged arithmetic; called once over the union.
- `src/fux/query/scan.py::query_term_hashes` — called per distinct digest; a
  `dict[digest, list[hash]]` carried to the scan.
- `src/fux/mcp.py`, `src/fux/cli.py` — `scope`; `src/fux/constants.toml` — the
  default and the three values (L12).
- `node/src/query/{scan,run,rank}.mjs` twins; `node/src/verbs/` for `--scope`.
- `tests/test_differential_*.py` — the law extended to a two-segment fixture.

## Records amended in the same change

- **SR-PKG-INDEX** — the merged query (its §Decision; W-299 writes the record,
  this item fills the query section).
- **SR-NODE-SEARCH** — the merged query in Node; d24's runtime reading per segment.
- **SR-MCP** — `scope` on `fux_search` (gated tool description; still no fourth tool).
- **SR-QUERY** / the record owning `scan.py` — the per-digest hashing and the seam.
- **SR-LAW-13** citation in the pre-registration, never a restatement.

## Tests

- two segments with disjoint `identifiers` digests: a family identifier in the
  package matches only when hashed under the package's rules.
- `df`/`n`/`total_flen` of the merged corpus equal the sums; `avg_wlen` derived once.
- a segment with `analyzer: v2` → `FuxError` naming the package; the query does not run.
- `scope=repo` returns exactly today's result (byte-equal to the pre-W-300 engine on
  the repo alone — the regression anchor); `scope=packages` returns no `file:`/`url:` ids.
- Node differential: same hits, same scores to the last bit, over the fixture.

## Definition of done

1. One `fux_search` call returns hits from the repo and the fixture segment, ranked
   on merged statistics; `scope` filters as specified; Python ≡ Node.
2. A foreign segment is refused by name; nothing is scored.
3. The L13 pre-registration and run filed under `work/regression/`, verdict stated.
4. Both suites green; docs per SR-WORK-DOCS d9–13.

## Out of scope

- A per-segment prior or weight — a ranking change with no evidence yet; only
  through L13 if step 1 of W-298 or a later measurement shows the need.
- Score fusion across segments (`fuse.py`): scores from separate corpora are not
  comparable; refused as the design.
- Anchor text across segments (a package linking into the repo, or back).

## Hazards

- 🟡 **Waits on W-299** (the pin and the inflated segment). W-298 step 1 passed
  2026-10-25.
- `anchor_on` folds in-edges by regex over shard lines; running it over a package
  segment is correct only if targets are resolved **within** that segment.
- The ceiling: `fux doctor` (W-299) reports the merged `n`; a query over more
  than 10 000 merged documents is outside what may be measured or promised
  (SR-WORK-SCALE, as amended).
