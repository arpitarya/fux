# Fux

**Deterministic knowledge retrieval for AI-assisted codebases — rank from a
small git-carried index, fetch content from the systems that own it, verify
at answer time.**

> **Status (2026-08-09): rebuild in progress.** The v0.26 engine and its
> docs are archived under [`archive/v0.26/`](archive/v0.26/) and
> [`docs/archive/v0.26-docs/`](docs/archive/v0.26-docs/), reference-only.
> The new architecture is specified in
> [`docs/paper/the-fux-index-paper.md`](docs/paper/the-fux-index-paper.md)
> and built against [`docs/PLAN.md`](docs/PLAN.md). Nothing on `main` is
> usable until milestone M4 of that plan.

## The idea

- **Sources own content.** Repo docs stay in git; Confluence pages stay in
  Confluence. Fux never keeps a durable copy (except explicit per-source
  `snapshot` policy).
- **Git carries only the index** — pruned per-document term statistics,
  dense binary codes, an extracted link graph, and a source ledger, in one
  content-addressed keyspace (~250 MB at a million documents).
- **Answers verify themselves.** Rank in the index, fetch the cited
  documents live (through a version-keyed cache), re-score passages on the
  fetched bytes, cite the fresh sha.
- **Laws:** $0 default · stdlib-only · byte-deterministic · offline by
  default · one ADR per feature, every rule referenced.

## Reading order

1. [`docs/paper/the-fux-index-paper.md`](docs/paper/the-fux-index-paper.md) — architecture + falsifiable predictions
2. [`docs/architecture-components.svg`](docs/architecture-components.svg) — the component map
3. [`docs/PLAN.md`](docs/PLAN.md) — milestones M0–M8
4. [`docs/WORKLOG.md`](docs/WORKLOG.md) — the running build log

License: MIT.
