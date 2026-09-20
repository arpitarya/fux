---
type: Proposal
title: Knowledge diff & time-travel — what changed in what we know
description: fux log / fux diff over the git-versioned corpus; checkout an old commit and ask questions of past knowledge.
status: proposed
timestamp: 2026-07-21T00:00:00Z
tags: [git, corpus, history]
---

# Knowledge diff & time-travel

## Signal

Because the corpus lives in git (the accepted long-term design), history comes free —
no other local doc-QA tool (semtools, rlama, qmd) treats the knowledge base as a
*versioned* artifact. "What changed in what we know since last sprint?" and "what did
we believe in March?" are questions only a git-native corpus can answer.

## Sketch

- `fux diff [rev]` — semantic changelog: which documents entered/left/changed,
  summarized at the heading level (extractive, deterministic — no LLM).
- `fux log <question>` — when did the answer to this question last change?
- Time-travel: `git checkout <rev> && fux ask "…"` already works by construction
  (index rebuilds from the cache deterministically); document it as a first-class
  workflow, maybe sugar it as `fux ask --at <rev>`.

## Why parked

Pure additive UX over v1's deterministic cache + index; needs zero new engine
concepts. Graduates when: the Anton corpus has enough git history that "what
changed?" becomes a real question Arpit asks.

# Citations

[1] [Knowledge as Code](https://knowledge-as-code.com/) — git-native knowledge with history/attribution/diffs as core properties (accessed 2026-07-21).
[2] [qmd — local search engine for agents](https://github.com/qntx-labs/qmd) — nearest competitor; no versioned-corpus concept (accessed 2026-07-21).
