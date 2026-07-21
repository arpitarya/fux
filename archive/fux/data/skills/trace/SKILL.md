---
name: fux-trace
description: "walk the merged graph to explain how a feature spans modules — graph-query value delivered as a workflow ($0)"
trigger: /fux trace
---

# /fux trace — explain how a feature spans modules

Graph-query value delivered as a workflow. Pure graph
traversal → effectively `$0` (no LLM required for the traversal itself).

## Inputs

`/fux trace "<feature or concept>"` — e.g. `/fux trace "day P&L"`.

## Procedure

1. Ensure the engine + project and a current graph: `fux build`.
2. **Anchor.** Find the entry points: `fux recall "<feature>"` to get governing
   rules, and grep the graph for matching node labels in `.fux/out/graph.json`.
3. **Traverse.** From each anchor node, walk edges in `graph.json`:
   - `governs` (rule → code) to reach the implementing files,
   - `contains` (file → function/class) to reach the symbols,
   - `calls` (symbol → symbol) to follow the data/control flow across modules,
   - `related` / `depends-on` (rule → rule) to pull in adjacent knowledge.
4. **Explain.** Narrate the path module-by-module, citing each hop as
   `path:line` and each governing rule as `fux why <id>`. Distinguish what the
   graph *extracted* (real call edges) from what you *inferred*.
5. **Capture (optional).** If the trace surfaced an undocumented cross-module
   rule, author it (`fux new rule <id>`) so the next trace is cheaper — the
   substrate gets smarter each time it is queried.

## Why through the graph, not grep

Grep finds string matches; the graph encodes *relationships* — which rule governs
which file, which function calls which, which decision constrains which module.
Tracing the graph answers "how does X relate to Y" by traversal, not by
re-scanning files every time the question comes up.
