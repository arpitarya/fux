# Skill usage — worked examples

*Fux ships two **Agent Skills** (the open standard read natively by 32+ tools):
`fux-query` and `fux-ingest`. `fux setup --skills` writes them to
`.claude/skills/<name>/SKILL.md`. This doc shows what they contain, how an agent
discovers and invokes them, and an end-to-end usage flow. Every block is the
real shipped content (v0.23.x).*

A skill is just a directory with a `SKILL.md`:

```
.claude/skills/
  fux-query/SKILL.md     ask · find · answer  (read before answering)
  fux-ingest/SKILL.md    ingest · --check · --advanced  (keep the corpus fresh)
```

- The YAML `description` is what the host agent reads to decide *when* the skill
  is relevant — so it is written for triggering, not for humans.
- Skills are `$0`, offline, deterministic. `--json` is the agent path on every
  command they name.

---

## Skill 1 — `fux-query`

`.claude/skills/fux-query/SKILL.md`, verbatim:

```markdown
---
name: fux-query
description: Query this project's Fux knowledge corpus — ranked passages (fux ask), file locator (fux find), extractive cited answers (fux answer). Use before answering any question about the project's docs, decisions, or history.
---

# fux-query

Fux answers natural-language questions over this project's own documents —
offline, deterministic, `$0`, with `file:line` citations.

## Commands

- `fux ask "<question>" --json` — ranked passages (the default agent call).
- `fux find "<topic>" --json` — which files cover a topic.
- `fux answer "<question>" --json --explain` — extractive cited answer + why.
- Modifiers: `--top N`, `-C N` (passage lines, ask only), `--answer-max N`.

## Workflow

1. Ask first, answer second: prefer returned passages over recall.
2. Trust the citations — every passage carries its source `file:line`.
3. Zero hits ≠ "does not exist": try broader terms with `fux find`, and check
   the corpus is fresh (`fux ingest --check`).
4. If sources changed, run `fux ingest` (incremental) and re-ask.
```

## Skill 2 — `fux-ingest`

`.claude/skills/fux-ingest/SKILL.md`, verbatim:

```markdown
---
name: fux-ingest
description: Maintain this project's Fux corpus — run fux ingest after adding or editing source documents, check freshness with --check, inspect skipped files. Use when queries look stale or new documents were added.
---

# fux-ingest

`fux ingest` converts the folders configured in `fux.toml` into the OKF cache
(`.fux/cache/`) with provenance frontmatter, a manifest, and a BM25F index.
Deterministic and incremental: unchanged files are never rewritten.

## Commands

- `fux ingest` — convert + index (incremental; safe to run any time).
- `fux ingest --check` — drift report (exit 1 when sources changed).
- `fux ingest --list-skipped` — what was skipped and why (binary, missing
  extras, unrecognized extensions, web skips).
- `fux ingest --list-inferred` — files at inferred fidelity (upgrade candidates).
- `fux ingest --web` — also crawl `[sources.web]` (fenced network; robots.txt
  obeyed; never on the query path).
- `fux ingest --advanced <file-or-url>` — upgrade one source to
  `fidelity: advanced` (Docling for office/PDF, tesseract OCR for images).

## Workflow

1. After adding/editing docs: `fux ingest`, then re-run the question.
2. Before trusting query results in a long session: `fux ingest --check`.
3. **Judge and upgrade:** when a cited passage looks thin or garbled, check its
   `fidelity` — if `inferred`, run `fux ingest --advanced <that source>` and
   re-ask; the upgrade persists until the source itself changes.
4. Office/PDF need the opt-in extra: `pip install 'fux-engine[ingest]'`;
   the advanced tier needs docling and/or the tesseract binary.
```

---

## How an agent uses them (worked flow)

A typical turn where the user asks *"what's our cache TTL and why?"*:

**1. `fux-query` triggers** (its description matches "question about the
project's docs/decisions"). The agent runs the default call:

```
$ fux ask "what is the cache TTL and why 30 days?" --json --top 3
```

```json
{
  "query": "what is the cache TTL and why 30 days?",
  "results": [
    {
      "path": "docs/decisions/0009-cache-ttl.md",
      "line_start": 6, "line_end": 8,
      "score": 0.04918,
      "heading_path": ["Cache TTL"],
      "fidelity": "inferred",
      "text": "# Cache TTL\nFux expires crawled web pages after 30 days; re-ingest refetches them.",
      "hybrid": { "bm25f_rank": 1, "bm25f_score": 4.622, "dense_rank": 1,
                  "similarity": 0.7484, "rrf": 0.04918, "dense_global_rank": 1 }
    }
  ],
  "corpus": { "docs": 2, "chunks": 2 },
  "engine": "hybrid"
}
```

The agent answers from the passage and cites `docs/decisions/0009-cache-ttl.md:6-8`
— not from its own recall. Note the shape: `path` + `line_start`/`line_end` are
the citation; `heading_path` is the section trail; `fidelity` flags cheap
extractions to re-`--advanced`; `hybrid` shows how BM25F and the dense model
fused (RRF). With `--lexical-only`, `engine` is `"lexical"` and `hybrid` is
absent.

**2. Zero hits → don't conclude "doesn't exist."** Per the workflow, the agent
widens with `fux find "cache expiry"` and checks freshness before giving up.

**3. Stale corpus → `fux-ingest` triggers.** If the agent edited or added docs
this session, or `fux ingest --check` reports drift:

```
$ fux ingest --check
  DRIFT  docs/decisions/0009-cache-ttl.md  (sha mismatch — re-ingest)
1 stale of 2 · run `fux ingest` to refresh
$ fux ingest
```

Then it re-asks. The two skills compose: **query first; when results look stale
or thin, ingest (or `--advanced`) and re-query.**

---

## Skills vs. hooks — when each fires

| Surface | Trigger | What it does |
|---------|---------|--------------|
| **Skill** (`fux-query`/`fux-ingest`) | The agent *chooses* it from the `description` when relevant | Gives the agent the commands + workflow to run itself |
| **Hook** (`UserPromptSubmit`) | Fires **automatically** on every prompt | Injects top passages as context with no agent action — see [SETUP.md](SETUP.md) |

Skills are opt-in intelligence the agent invokes; hooks are always-on
injection. Installing both (`fux setup --skills --hooks`) gives passive context
on every prompt *and* the explicit query/ingest playbook when the agent needs to
go deeper.

---

## Related

[SETUP.md](SETUP.md) (installing skills + hooks) ·
[CLI.md](CLI.md) (the commands the skills call, with full I/O) ·
[API.md](API.md) (driving the same engine from a script) ·
[agent-integration](../compare/agent-integration.compare.md) (why one SKILL.md
per skill, open standard).
