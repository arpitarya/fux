---
type: Proposal
title: Code pattern recognition — a committed structural index for code, beside fux, not inside it
description: The code half of Arpit's 2026-09-27 pattern-recognition ask — what "how code looks" would mean as a fux-shaped tool, why it is not a fux lens, what already exists (ast-grep, clone detectors, tree-sitter knowledge graphs served over MCP), and the one trigger on which building anything is worth it.
status: proposed
timestamp: 2026-09-27T18:30:00Z
---

# Code pattern recognition — beside fux, not inside it

**The ask, Arpit, 2026-09-27 (Cowork):**

> *"Pattern recognition from how it is, how a code looks like, or how one
> document looks like, or how a bunch of documents look like … similar to how
> fux works, that … there's a CLI that is available, which can be ingested by
> Claude Code, and can give meaningful answers."*

The **document** half is [W-228](../open/W-228-document-families.md), a lens in
`fux inspect`. This file is the **code** half, and it is parked because the
honest answer to *"shall we build a separate tool?"* is *"the field has, and
the part that is fux-shaped is small."*

⚠ **Nothing here is built, and nothing here is a fux feature.** Fux is
document-only ([the positioning](../../archive/proposals/positioning-documents-not-code.md)
shipped as *"a search index for your written knowledge"*); no AST layer exists
and the rules-bound-to-code vision is on hold. A code index in `src/fux/` would
need an SR, Arpit's sign-off, and a reason this file does not find.

---

## 1. What "how code looks" decomposes into

Three different questions, three different existing answers:

| question | what answers it today | fux-shaped? |
|---|---|---|
| *find this shape in the code* (a pattern, an anti-pattern, a migration target) | [ast-grep](https://ast-grep.github.io/advanced/tool-comparison.html) (tree-sitter, JSON out, MIT), [semgrep](https://github.com/semgrep/semgrep) (LGPL engine, deeper semantics, slower) | no — a query tool with no index to commit |
| *which parts of the code look alike* (clones, near-miss copies, template families) | [SourcererCC](https://arxiv.org/pdf/1603.01661) (token-bag, scales to big code), PMD CPD, the [2026 tool roundup](https://dev.to/rahulxsingh/13-best-duplicate-code-checker-tools-in-2026-1cnk) | partly — a **committed clone map** is index-and-refer-shaped |
| *how is this codebase structured, and what depends on what* (hubs, call chains, dead code) | [Codebase-Memory](https://arxiv.org/html/2603.27277v1) — tree-sitter → SQLite graph → 14 MCP tools, 66 languages, 83 % answer quality at 10× fewer tokens; also [tree-sitter-analyzer](https://github.com/aimasteracc/tree-sitter-analyzer), [coderlm](https://github.com/JaredStewart/coderlm) | **this is exactly the CLI/MCP-for-Claude-Code shape asked for — already built, by several people** |

**Reading the table:** the first row is grep with a parser; the third row is a
crowded 2025–26 space; only the second row has a fux-shaped gap.

## 2. The fux-shaped gap, stated once

What none of the third-row tools do, and what fux does for documents:

- **commit the index, not the content** — a small, diffable structural
  summary in git that every clone shares, instead of a per-machine SQLite that
  each agent rebuilds;
- **verify at answer time** — cite a symbol at a sha and say whether the
  source still matches;
- **byte-identical from the same tree** (L4) — Codebase-Memory's own paper
  concedes a heuristic resolution cascade that is *reproducible, not
  deterministic*.

That gap is real and it is **narrow**: it is a git-committed, deterministic
**clone-and-shape map** (row 2 plus a symbol skeleton), not a call graph, not
a type resolver, not a query language. Everything past that line is row 3, and
row 3 is a buy.

## 3. Sketch — if the trigger fires

A separate distribution (working name only: `fux-code`; **not** a verb of
`fux`), sharing fux's laws by adoption rather than by import:

1. **Extract**: tree-sitter grammars vendored per L2 (all MIT/Apache; check
   each SPDX id before naming it), one deterministic pass → per-file
   **shape**: symbol skeleton (defs, their kinds, their order), import set,
   token-bag minhash. Same masking discipline as W-228's heading skeleton.
2. **Commit**: one content-addressed plane beside `.fux/index/` — shapes and
   the clone map, never source text (L3 by analogy; a token *bag* is
   statistics, a token *sequence* is content and stays out).
3. **Answer**: `families` (which files share a shape), `clones` (near-miss
   pairs with exact Jaccard, the W-228 pattern), `misfits` (a file in a folder
   whose shape it does not share), each `--json`; served over MCP the way
   [SR-MCP](../../records/0136_mcp.md) serves `fux_search` — its own server,
   not new tools on fux's.
4. **Verify**: every cited symbol carries the file sha it was extracted at.

**Out of the sketch, deliberately:** call graphs, dataflow, taint, type
resolution — Codebase-Memory and semgrep own these and fux would be a worse
third.

## 4. Why not a lens in `fux inspect`

- `inspect` reads the **document index**; code files are not ingested and the
  analyzer is a text analyzer. A code shape needs a parser per language, which
  is a dependency decision (L2 permits; a record must decide) and a scope
  decision the positioning already made the other way.
- The document lens is judged by the **top-10 test**. A code lens has no
  `ask` to serve — its consumer is a different agent question.
- Mixing them puts a tree-sitter build in every consumer's `fux` install for
  a feature most corpora never use; L2's *dependencies ship packaged* makes
  that cost everyone's.

## 5. Graduation trigger

**Graduates when a consumer of fux asks a code-shape question that the third-row
tools cannot answer *because the answer must be committed* — a review, a CI
gate, or an audit that needs the clone map at a sha, reproducible on another
machine.** One such ask is a use case; the second is a shape, and this
graduates into a compare doc on *separate distribution vs. row-3 wrapper*.

Until then the recommendation for anyone who wants row 1 or row 3 today is a
**skill**, not a build: `ast-grep` for shape queries, one clone detector for
row 2, and one of the tree-sitter graph servers for row 3, each wrapped so
Claude Code reaches it the way it reaches `fux`. That costs a SKILL.md, not a
distribution.

## 6. Reference

- [ast-grep — comparison with semgrep, comby, grep](https://ast-grep.github.io/advanced/tool-comparison.html)
- [semgrep](https://github.com/semgrep/semgrep)
- Sajnani et al., [SourcererCC and SourcererCC-I](https://arxiv.org/pdf/1603.01661), ICSE 2016
- [Codebase-Memory: tree-sitter-based knowledge graphs for LLM code agents](https://arxiv.org/html/2603.27277v1), 2026
- [tree-sitter-analyzer](https://github.com/aimasteracc/tree-sitter-analyzer) · [coderlm](https://github.com/JaredStewart/coderlm)
- [13 duplicate-code checkers, 2026](https://dev.to/rahulxsingh/13-best-duplicate-code-checker-tools-in-2026-1cnk)
- [W-228](../open/W-228-document-families.md) — the document half, and the
  shape/minhash/misfit pattern this sketch reuses
