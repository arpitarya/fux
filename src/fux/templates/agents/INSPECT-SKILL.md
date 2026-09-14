---
name: fux-inspect
description: Read the shape of a Fux index with `fux inspect` — words on every document, documents no query can reach, near-duplicates and template families, what the analyzer never saw, graph orphans and hubs, and three flagged checks with provisional floors. Use for "is this index any good", "why can't fux find this document", "what is the corpus like", "find duplicate docs", or before proposing a stopword or an ignore rule. Read-only and offline; it applies no lever.
---

# The shape of a Fux index — `fux inspect`

`fux doctor` says whether the **machine** is set up. `fux inspect` says whether
the **index** is any good. Both are read-only; the difference is the remedy —
`doctor`'s is a command or a config edit, `inspect`'s is a change to the corpus.

Resolve the `fux` command first — see the `fux-usage` skill (`fux` → `uv run fux` → `./.venv/bin/fux`, on Windows `.venv\Scripts\fux.exe` → `python -m fux`).

## 1 · When this is the right verb

| the ask | what to do |
|---|---|
| "is our index good or bad?" | `fux inspect --json` — read the `checks` array first |
| "which words are on everything?" | the `boilerplate.top` rows, with `share` and `idf` |
| "why can't fux find this document?" | `findability.unfindable`, then `lengths.shortest` |
| "do we have duplicate docs?" | `duplication.near_duplicates` and `duplication.families` |
| "what did fux fail to read?" | `coverage.undecodable`, `coverage.unreadable`, `coverage.no_content` |
| "which docs are isolated?" | `graph.orphans`; `graph.hubs` for the opposite |
| "why did THIS document rank here?" | not this verb — `fux ask --why` (`fux-search`) |
| "is the repo set up correctly?" | not this verb — `fux doctor` (`fux-index`) |

**Run it read-only and say so.** `inspect` writes only
`.fux/runtime/inspect/` — gitignored, rebuildable — and never edits a
committed byte.

## 2 · Read `checks` before anything else

Four numbers. **Three carry a flag; the fourth is descriptive and says so.**

| check | direction | what it means |
|---|---|---|
| `unreachable share` | lower is better | documents with **no distinctive term at all** — no query can select them. EXHAUSTIVE: every document is checked |
| `boilerplate share` | lower is better | share of **postings** whose term is on half the corpus or more |
| `near-duplicate share` | lower is better | share of documents that are one half of a pair at Jaccard ≥ 0.80 |
| `findable share` | — | share of sampled documents returned in the top 3 for their own most distinctive words. **No floor, on purpose** |

- **`status` is one of `ok`, `attention`, `descriptive`, `n/a`.** They are four
  different statements. `descriptive` means *there is a number and no floor
  could separate a healthy corpus from a bad one*. `n/a` means *there is no
  number*, which is **never** a pass.
- **Every floor is `provisional` and the JSON says so** (`checks[].floor.provisional`).
  Report a flag as *worth looking at*, never as a failure.
- ⚠ **`fux inspect` exits 0 whatever it finds.** A non-zero exit means it could
  not produce a report at all — almost always no committed index yet. **Do not
  read exit 0 as "the index is fine."**
- ⚠ **`findable share` is near 1.0 on almost every corpus, including bad
  ones**, because a fingerprint is built from a document's own rarest terms and
  its file path is part of its indexed vocabulary. Do not quote it as evidence
  that retrieval is healthy. `unreachable share` is the one that fires.

## 3 · Every finding names a lever. Never apply one unasked.

The report prints the lever beside the finding, and `levers` in `--json` is the
whole table. **Propose the command; do not run it.** Each lever writes a
committed file and changes what is indexed or how it ranks — which is somebody's
decision, not a tidy-up.

| finding | the lever it prints |
|---|---|
| boilerplate term | `[index]` stopwords, or an analyzer amendment |
| template family · near-duplicate pair | `.fuxignore`, `archived=`, or `supersedes` on the one that is current |
| unfindable document | `fux enrich`, `fux correct`, or fix the source |
| document known only by its file name | a decoder (`fux-decoder`), or leave it in `.fux/enrich/queue.tsv` |
| unreadable document | re-ingest, or `keep = true` on the url line |
| orphan · hub | nothing today — the graph-composed `ask` is unbuilt |

The skills that own those levers: `fux-config` (stopwords and `fux.toml`),
`fux-sources` (`.fuxignore`, `archived=`), `fux-enrich`, `fux-decoder`,
`fux-fetcher`.

## 4 · Flags

| flag | what it does |
|---|---|
| `--json` | the machine-readable report. **Prefer it**; the Markdown is for a human |
| `--top N` | rows per named list (default 20). **The counts beside them are never truncated** |
| `--retrieval-sample N` | documents tested by retrieval. `0` means every one of them — one full query each, so it is slow on a large corpus |
| `--rebuild-dictionary` | re-tokenise the sources even when the cached dictionary is current |

## 5 · A truncated list is not a total

⚠ **Every named list is capped at `--top`; every count beside it is not.** Read
`duplication.pair_count`, `graph.orphan_count`,
`findability.unfindable_count` and `coverage.total_terms` — never
`len(near_duplicates)` or `len(orphans)`. On the fux repository itself the
orphan list showed 20 and the count was **341**.

## 6 · Where the words come from, and what that limits

The committed index holds **term hashes, not words**. `inspect` re-tokenises the
sources on this disk into a gitignored dictionary and joins it in.

- **`coverage.dictionary_coverage` is how much of the index it could name.**
  Below 1.0 means some document's bytes are not on this machine — not that the
  terms do not exist.
- **A `url:` document is read from `.fux/acquired/` or skipped.** `inspect`
  **never fetches**. A URL indexed with `keep = false` has no retained bytes, so
  its words cannot be named; it appears in `coverage.unreadable`.
- **An unnamed hash prints as the hash.** That is a real state, not a blank.
- **The words are stems.** The report shows the most frequent spelling a human
  wrote for each, so `mTLS` prints as `mTLS` rather than as `mtl`.

## 7 · Reading the vocabulary numbers

- `boilerplate.zipf_slope` — about −1 on ordinary prose. Far from it means the
  corpus is not shaped like text.
- `boilerplate.heaps_beta` — typically 0.4–0.6. **Low means each new document
  brings few new words**: a corpus of near-copies.
- `lengths.distinct_terms` percentiles — the number that killed index pruning
  here: documents with a 30-term vocabulary cannot match much, and an average
  hides them. **Quote the percentiles, never the mean.**
- `boilerplate.hapax_share` — terms on exactly one document. High is normal.

## 8 · Preconditions

- **A committed index must exist.** No index → exit 1 naming `fux ingest`.
- **`fux build` is not required**, but the retrieval half is much faster with a
  fresh accelerator.
- **Offline and deterministic.** The same index produces a byte-identical
  report twice; there is no timestamp in it.
- **Python only.** There is no `npx fux inspect`.

## Don't

- **Don't apply a lever it printed** unless you were asked to. Propose it.
- **Don't read exit 0 as a clean bill of health** — it always exits 0.
- **Don't quote a capped list as a total** — read the count beside it.
- **Don't quote `findable share` as evidence retrieval works** — it is ~1.0 on
  a corpus of forty identical documents.
- **Don't call a provisional floor a failure**, or drop the word *provisional*
  when reporting one.
- **Don't treat a boilerplate term as safe to add as a stopword** on this
  report alone — it changes ranking for every query and needs its own decision.
- **Don't confuse `no_content` with empty**: those documents are indexed, by
  their file name alone.
- **Don't run it to answer a question about one document** — that is
  `fux ask --why` or `fux explain`.

Related skills: fux-usage, fux-index, fux-search, fux-sources, fux-config, fux-enrich, fux-decoder, fux-graph, fux-archived-results.
