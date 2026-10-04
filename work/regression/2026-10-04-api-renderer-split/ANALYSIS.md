---
type: Analysis
description: "W-247 analysis: what the byte-equality result licenses (the split may land) and what it does not (nothing about ranking, journalling, URL fetches, mcp or serve)."
run: 2026-10-04-api-renderer-split
item: W-247
---

# Analysis: what 537 identical invocations license

**Result.** [`report.md`](report.md): stdout, stderr and exit code identical on
537 of 537 invocations, the library's results identical on 93 calls, Node
differential 0 of 225.

## The change this licenses

`query.build_ask`, `build_find` and `build_answer` are the one place a payload
is built. `cmd_ask`/`cmd_lexical`/`cmd_find`/`cmd_answer` render them, and
`fux.api.Index.find/ask/answer` read them. Repro: the command block in the
report.

## Where the builders deliberately differ from a pure split

- `build_ask` and `build_find` print nothing and the stderr declarations stay in
  the `cmd_*` functions; the library never printed them.
- `build_answer` does print the declarations that precede the answer (floor
  note, missing accelerator, a pin, "since you last asked"), because the library
  has always reached them through `cmd_answer` and moving them would have changed
  what it prints. Unresolved by design: whether the library should print them at
  all is a ruling, not a refactor.
- `Index.answer` round-trips the payload through JSON, so tuples become lists as
  they did when the CLI's stdout was parsed back.

## What it does not license

Nothing about ranking quality, `--journal`, a live URL fetch, or the `mcp` and
`serve` verbs (which call `run_query` directly). The `lab` corpus is a v7
re-ingest of the rung's documents, not the rung's own v5 index.
