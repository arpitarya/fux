---
type: Compare Doc
title: Query Output
description: Ranked passages default; --files locator; --answer extractive synthesis via the bundled model — never generative.
status: accepted
timestamp: 2026-07-21T00:00:00Z
---

# Query Output — Comparison (with worked examples)

> **Verdict:** **Ranked passages by default; matching-files behind `--files`; and an
> `--answer` mode that synthesizes *extractively* — no external LLM.** The `--answer`
> mode stitches the source's own most-relevant sentences into a short, cited answer
> using the bundled ≤10 MB embedding model + TextRank (see
> [`packaged-model.compare.md`](packaged-model.compare.md)). It selects and orders
> existing sentences; it does not generate new prose.
> **Status:** ✅ Accepted (Arpit, 2026-07-20) · **Confidence:** Medium-High
> **Honest caveat:** an extractive answer reads slightly less fluent than an LLM's,
> but it's deterministic, fully traceable, and hallucination-free — the deliberate
> trade for offline `$0` with no external model.

## Context

Given a folder of documents and a question, what does the CLI print? Three formats
trade *effort-to-read* vs *verifiability* vs *capability*. Arpit picked **ranked
passages** as the base and asked whether option 3 ("synthesize an answer") can be done
**without an external LLM** — using a model *built into the package*. Answer: yes, as
**extractive** synthesis. This doc fixes the default and the flags, and shows all three
on one example.

**Running example.** Folder `~/notes/anton/`, file `decisions/db-indexing.md`:

> ## 2026-05 — Indexing the trades table
> We chose a composite index on `(symbol, ts)` over per-column indexes because every
> hot query filters by symbol then range-scans time. Partial index on `status='open'`
> to keep the working set small. Rejected a covering index — write amplification on the
> tick ingest path was too high.

**Question:** `fux ask "why did we pick a composite index for trades?"`

## Options (shown on the example)

### Option 1 — Matching files  `--files`
```
$ fux ask --files "why did we pick a composite index for trades?"
1.  0.82  notes/anton/decisions/db-indexing.md
2.  0.32  notes/anton/schema/trades.md
```
Lightest; a locator. Deterministic; works with any engine.

### Option 2 — Ranked passages  *(default)*
```
$ fux ask "why did we pick a composite index for trades?"

notes/anton/decisions/db-indexing.md:12  (score 0.82)
  We chose a composite index on (symbol, ts) over per-column indexes because
  every hot query filters by symbol then range-scans time. Rejected a covering
  index — write amplification on the tick ingest path was too high.
```
Shows the evidence with `file:line`; best trust-to-effort ratio; deterministic;
engine-agnostic. **The default.**

### Option 3 — Extractive answer + citations  `--answer`  *(bundled model, no LLM)*
```
$ fux ask --answer "why did we pick a composite index for trades?"

Answer (extractive — source sentences, ordered):
  We chose a composite index on (symbol, ts) because every hot query filters by
  symbol then range-scans time. [1] A covering index was rejected — write
  amplification on the tick ingest path was too high. [2]

Sources:
  [1] notes/anton/decisions/db-indexing.md:12
  [2] notes/anton/decisions/db-indexing.md:14
```
- **How:** retrieve → sentence-split → score each sentence by semantic similarity to
  the question (bundled embeddings) + centrality (TextRank) → select/order the top few,
  each cited. No text is invented.
- **Pros:** reads like an answer; multi-sentence; deterministic; every clause is
  verbatim-traceable; no external model, no network, no hallucination.
- **Cons:** it can't paraphrase or fuse ideas into new wording like an LLM; if the
  source never states the answer in one place, extractive can't manufacture it (it will
  surface the closest real sentences instead).

## Comparison matrix

| Criterion (weight) | 1: Files | 2: Passages | 3: Extractive answer |
|--------------------|----------|-------------|----------------------|
| Effort to get the answer (H) | High | Low | Lowest |
| Verifiability / trust (H) | Med | High | High (verbatim + cited) |
| No external model (H, hard) | ✓ | ✓ | ✓ (bundled only) |
| Cost / offline (H) | $0 | $0 | $0 |
| Determinism (M) | Full | Full | Full |
| Multi-source synthesis (M) | No | Manual | Yes (selects across passages) |
| Fluency of answer (M) | — | — | Good, not LLM-smooth |
| **Fit** | Locator | **Default** | Opt-in, no-LLM |

## Proposed shape

One command, three intents: `fux ask` → passages (default); `--files` → locator;
`--answer` → extractive cited answer via the bundled model. An agent (engine v3) can
call `--answer --explain` to also get why each sentence was chosen and decide whether to
trigger an advanced ingest pass on a thin source.

## References

- Internal: [`packaged-model.compare.md`](packaged-model.compare.md) — the bundled embedding model + TextRank that power `--answer`; [`query-engine.compare.md`](query-engine.compare.md) — supplies the retrieved passages.
- Internal: [`../../CLAUDE.md`](../../CLAUDE.md) — the determinism / no-external-model defaults that make extractive the right synthesis choice.
- External: [Erkan & Radev, 2004 — LexRank](http://www.cs.cmu.edu/afs/cs/project/jair/pub/volume22/erkan04a-html/erkan04a.html) — graph-centrality sentence selection (accessed 2026-07-20).
- External: [Extractive vs Abstractive Summarization — experimental review](https://www.mdpi.com/2076-3417/13/13/7620) — extractive stays faithful/traceable without generation (accessed 2026-07-20).
- External: [ripgrep output conventions](https://github.com/BurntSushi/ripgrep) — the `path:line: context` format option 2 mirrors (accessed 2026-07-20).

## Additional things to look into

- **Snippet/sentence windowing:** how much context per passage, and sentence-splitting
  quality on Markdown (headings, lists, code fences).
- **`--json` mode:** machine-readable output for the agent path (passages, scores,
  citations, explanation).
- **Answer length control:** cap sentences (e.g. `--answer-max 3`) to keep it tight.
- **"No confident answer" behavior:** when top scores are low, say so and fall back to
  passages rather than forcing a weak extractive answer — and let the agent trigger an
  advanced ingest pass.
