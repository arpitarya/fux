---
type: Handoff
name: W-284
description: "Arpit asked on 2026-10-19 for llms.txt and llms-full.txt rendered from the index (`fux llms`), and this repository's own pair at the root."
item: W-284
filed: 2026-10-19
filed_by: "Arpit (Claude Code, Opus 5.5)"
updated: 2026-10-19
updated_by: "Claude (Claude Code, Opus 5.5)"
ball: agent
closed: 2026-10-19
---

# W-284 — `fux llms`: an llms.txt and an llms-full.txt from the index

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | Add `fux llms`: the indexed documents as an llms.txt — title, link, the document's own description | any fux repo can hand an LLM a map of its docs in one command | ✅ |
| 2 | `--full` adds each document's text, read off disk, to stdout | the llms-full.txt convention, without fux writing a copy anywhere (L3) | ✅ |
| 3 | Generate this repository's own `llms.txt` / `llms-full.txt` with `just llms`, held current by a test | fux's own docs are LLM-readable from the repo root and from raw GitHub | ✅ |

**Arpit, 2026-10-19 (Claude Code):** *"create llms-full.txt and llms.txt files as well as mcp and lsp for vscode research and build it out create work items then implement it and close them then commit push and publish a new version"*

**Model:** Sonnet: the shape is ruled in the compare doc (F1) and every check is mechanical.

## Goal

A reader-layer verb that renders [llms.txt](https://llmstxt.org/) from the committed index: H1, blockquote, one H2 per top-level folder, archived documents under `## Optional`. `--full` appends the text of every `file:` document, read from the working tree; URL documents are listed, never fetched (L5).

## Definition of done

- `fux llms [--in PREFIX ...] [--full] [--title T] [--summary S] [--base-url U]` in `src/fux/llms.py`, reader layer, stdlib, deterministic (sorted by loc).
- Fixed format strings in `constants.toml [llms]` (L12).
- This repo's `llms.txt` and `llms-full.txt` at the root, `just llms` regenerates them, a test holds them equal to the verb's output.
- Unit tests and an e2e test; SR-LLMS written; README, CHANGELOG, GLOSSARY.

## Outcome

**Done, 2026-10-19** — shipped in fux 4.1.0. Live successor: [SR-LLMS](../../records/0162_llms.md).

## Blockers

None.

## Record affected

**SR-LLMS** (new) · SR-CLI (the verb list).

## Hazards

- **L3**: fux writes to stdout only; the committed pair is a copy inside the repository that owns the source.
- The committed index lags a commit by one post-commit ingest; the test reads the committed index, so regenerate after re-ingest.

## Reference

[compare doc](../../work/compare/editor-and-llms-surfaces.compare.md) Fork 4 · [llmstxt.org](https://llmstxt.org/).
