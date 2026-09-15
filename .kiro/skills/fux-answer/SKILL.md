---
name: fux-answer
description: Get cited answers with `fux answer` and check them with `fux verify` — line-range locators, freshness verdicts (current, stale, as-ingested, cached, unverified), --no-refer, --audit, --receipt, and verify's reproduced/drifted/unverifiable verdicts. Use when asked to "answer from the docs with citations", "give me the exact lines", "is this still current", "prove or reproduce this answer" or "verify this receipt".
---

# Answering with `fux answer`, checking with `fux verify`

`answer` ranks exactly as `ask` does, takes the **top three** documents, reads
each one **from its source right now**, re-scores every passage against your
question, and returns verbatim spans with the sha of the bytes it read. No model
touches the text. Resolve the `fux` command first — see the `fux-usage` skill
(`fux` → `uv run fux` → `./.venv/bin/fux`, on Windows `.venv\Scripts\fux.exe` → `python -m fux`).

## 1 · Pick the invocation

| the ask | run |
|---|---|
| an answer with citations | `fux answer "<q>" --json --band` |
| the exact lines | the same; read `answer.passages[].loc` |
| "is this still current?" | `fux answer "<q>" --json --band --audit` — read the verdicts |
| do not touch any source | `fux answer "<q>" --no-refer --json` |
| something to re-check later | `fux answer "<q>" --json --receipt > receipt.json` |
| "verify this receipt" | `fux verify receipt.json --rerun --json` |
| a list of candidates, not one answer | `fux ask` — see `fux-search` |

## 2 · Flags, verified

| `fux answer` flag | effect |
|---|---|
| `--json` | the payload in section 4; **prefer it** |
| `--band` | add the `confidence` block (JSON) or a `confidence:` line (stderr) |
| `--expand TEXT` | extra terms the document probably uses, scored at a discount. **You write this text — fux never generates it** (see `fux-search` §5a); it is recorded in the receipt and replayed by `fux verify` |
| `--no-refer` | read nothing; answer from the index's title and headings |
| `--audit` | add `audit`: every document looked at, both shas, the budget spent |
| `--receipt` | add `receipt`: a re-runnable record for `fux verify` |
| `--journal` | also append the receipt to `.fux/runtime/provenance.jsonl` (gitignored) |
| `--fast` / `--scan`, `--no-tune`, `--no-output-config` | as on `ask` |

⚠ **`answer` has no `--top`, no `-q` and no `--why`.** Passing one is a usage
error (exit 2). Three candidates is fixed, not configurable.

| `fux verify` | effect |
|---|---|
| `fux verify <file>` | check the receipt's inputs against this tree |
| `--rerun` | also re-answer the question and compare the cited bytes |
| `--json` | `{verdict, note, expected, actual}` |

## 3 · What one answer does

1. **Rank** like `ask`, keep the top 3.
2. **Read each source.** A `file:` document is read from the **working tree** —
   no network, works offline, sees uncommitted edits. A `url:` document goes
   through **the fetcher its line in `.fux/sources/urls` names** — network,
   that fetcher's auth and timeouts.
3. **Compare** the sha of what was read with the sha that was indexed.
4. **Chunk and re-score** all three documents' passages in one contest. ⚠ **The
   winning passage can come from the second or third document**, so `answer`
   and `ask` may disagree about which document is first.
5. **Assemble** under `[refer] budget` in `.fux/tune.toml` (default 8000 bytes
   for the whole rendered answer). The best passage is seated first.
6. **Fall back.** If no candidate yields a passage, the answer comes from the
   index alone and says so (`source: index`).

It writes only gitignored state under `.fux/runtime/`, and prints a stderr note
such as `note: nothing has changed since you last asked this.`

## 4 · Read the JSON

```json
{"answer": {"passages": [{"id": "file:docs/mesh.md", "loc": "docs/mesh.md:L10-L13",
                          "sha": "516bef06…", "heading": "Rollback procedure",
                          "text": "Drain the sidecar and fail open.", "score": 2.689}]},
 "citation": {"id": "file:docs/mesh.md", "loc": "docs/mesh.md:L10-L13",
              "sha": "516bef06…", "freshness": "current"},
 "source": "refer"}
```

**Switch on `source` first.** It is present on every branch.

| `source` | `answer` | `citation` |
|---|---|---|
| `refer` | `{passages: [{id, loc, sha, heading, text, score}]}` | `{id, loc, sha, freshness}` of the **winning passage's** document |
| `index` | `{title, phrases}` — headings, **not quoted text** | `{id, loc, score}` — document-level, no sha, no freshness |
| `index`, no match | `null` | `null` — exit 0 |

⚠ **Passages may come from different documents.** Cite each passage by its own
`loc` and `sha`; never list them all under `citation`.

`text` is verbatim from the fetched bytes — frontmatter and table pipes included.

## 4a · 🔴 `answer` can cite a document no query word matched

`fux answer` reads `fux ask`, and since W-161 `ask` returns two tiers. **Both
are fetched and re-scored on the fetched bytes**, so the winner can be a
document the words never retrieved — one the ranked results merely **link to**.

That is deliberate and it is usually right: the tier exists because BM25F
retrieves by shared vocabulary, and the record a runbook points at often uses
none of the runbook's words. The refer plane reads the **document**, not the
index, so a linked document with nothing in it loses on its own bytes.

**What it means for how you report:**

- **The passage is still real and still verified** — same fetch, same sha, same
  freshness verdict. Nothing about the citation is weaker.
- ⚠ **But the confidence band describes the lexical tier only.** A `grounded`
  band beside a citation that came from a link is not a claim about that link.
  If the answer matters, say which document it came from and let the reader see
  that the question's own words are not in it.
- To rule the tier out entirely, `fux ask --no-related` first and answer from
  that, or set `[graph] ask_related = false`.

## 5 · Locators

| form | when | how to use it |
|---|---|---|
| `docs/x.md:L12-L40` | a file fux reads as plain text (Markdown, `.txt`) | 1-based, inclusive lines of the file **as it is now** |
| `docs/x.html#p7` | a format a decoder converts (HTML, PDF, DOCX, CSV, XLSX, YAML, JSON…) | **not a line.** Use `heading` and search for the quoted `text` |
| `https://host/page:L3-L9` | a `url:` document | lines of fux's text copy of the page, not of the rendered page — search for `text` |

## 6 · Freshness verdicts

`citation.freshness` covers the winning document; `--audit` gives one verdict
per document in `audit.documents[]` (`freshness`, `indexed_sha`, `fetched_sha`,
`strategy` = `git`|`url`, `note`).

| verdict | what happened | how to cite it |
|---|---|---|
| `current` | read now; matches what was indexed | cite plainly with `loc` |
| `stale` | read now; **changed since indexing** | quote it — it is the **current** text — and say the index is behind (a stale winner drops the band to `partial`) |
| `as-ingested` | source unreachable **or not consulted**; compared against the bytes kept in `.fux/acquired/` at ingest (retained unless the URL line says `keep=false`) | "as of the last ingest" — say *could not be reached* only if a fetch was actually tried |
| `cached` | served from the local fetch cache — **only when you pass `--cache-ttl`** | "checked recently, not just now" |
| `unverified` | not read — no fetcher, fetch failed, or file gone from the working tree | that document supplied **no passage**; never call it confirmed |

- **An `as-ingested` note saying *"the index disagrees with the bytes it was
  built from"*** is an index defect, not a changed source. Say so.
- **`answer` goes out for every citation unless you ask otherwise.**
  `--cache-ttl 15m` serves a copy fetched within the window instead; a URL
  line's own `ttl=` can only **narrow** that, never widen it, so without the
  flag no line's `ttl=` applies and `cached` never appears. ⚠ **`update=never`
  is update-time and does NOT keep `answer` offline** — that is by design
  (SR-URL-FRESHNESS decision 15), not a defect. Read `citation.freshness` (or
  `--audit`) rather than assuming what was fetched.
- ⚠ **`[sources.url] fetch_at_answer = false` makes `as-ingested` the NORMAL
  verdict, not a degradation.** The repo has said *never open a socket when
  answering*; no fetch was attempted, so **do not report the source as
  unreachable** — it was never asked. Check `fux.toml` before writing that
  sentence, or read `--audit`'s recorded policy, where `mode` is `never`.
  **This is not `--no-refer`**: the passage was still re-scored on real bytes
  and the line range is real.
- ⚠ **A `note` naming the fetcher** — it raised, returned no bytes, or returned
  a type no decoder claims — means the live fetch was not used: the verdict is
  `as-ingested` (kept bytes) or `unverified`, never `current`. The note says
  which; retrying changes nothing until the fetcher or the decoder does.
- A `stale` `url:` document is recorded for the next URL refresh — see `fux-sources`.

## 7 · Cite honestly — band first, then verdict

| `--band` says | do |
|---|---|
| `none` (`answerable: false`) | abstain: "the index has nothing on this" |
| `weak` | **abstain** (`answerable: false`) — *the documents don't say*; show the passages as candidates and name what was searched, never a conclusion |
| `partial` | answer, and name `missing` terms or the `stale` source |
| `grounded` | answer, citing each passage's `loc` and its verdict |

On `source: index`, say the answer is **from the index's structure only** — a
title and headings, nothing read from the source. Point at the document, not at
lines.

## 8 · Receipts and `fux verify`

`--receipt` adds an **unsigned in-toto Statement**, with no timestamp:
`subject[]` (`name`, `digest.sha256`, `annotations["fux.dev/loc"]`) and
`predicate` (`engine.version`, `engine.path`, `inputs.index`, `inputs.tune`,
`inputs.query`, `inputs.expand` when used, `confidence`, `verdicts`). Text mode
prints only `[receipt] <digest>` on stderr. ⚠ `digest.sha256` holds fux's own
40-hex content sha — do not check it with `sha256sum`.

```bash
fux answer "how do we roll back the gateway" --json --receipt > receipt.json
fux verify receipt.json --rerun --json
```

`verify` accepts the whole answer payload or the bare receipt. It checks the
format, then engine and tune, then the index, then the re-run; the first
failure decides:

| verdict | exit | means |
|---|---|---|
| `drifted:config` | 1 | engine version differs, or `.fux/tune.toml` differs (or appeared) |
| `drifted:corpus` | 1 | the committed index differs, or `--rerun` cited a different document |
| `unverifiable` | 1 | not a fux receipt, an older format, no index here, `--rerun` was not passed — **or the receipt came from a `refer` answer** |
| `reproduced` | 0 | `--rerun` cited the same documents, in the same order |

- 🔴 **`fux verify` NEVER FETCHES**, by ruling (SR-PROVENANCE decision 14). So
  a **`source: refer` receipt is `unverifiable`** with `--rerun`: its answer was
  assembled from bytes fetched at answer time, and reproducing that would mean
  going out again — which would make one receipt verify differently on a laptop
  and in CI. **The fetched-byte verdicts you want are already in the receipt's
  own `verdicts`**, recorded when the answer was given.
- ⚠ **Without `--rerun` the best possible verdict is `unverifiable`** (*"inputs
  match; the answer was not re-run"*). That is not a pass.
- **`--rerun` re-ranks from the committed index only**, so it is deterministic
  on any machine. A local file edited since the receipt changes the index
  digest and shows as `drifted:corpus`.
- **Upgrading fux makes every older receipt `drifted:config`.**

**`--journal` stores the question in plaintext** in a local, gitignored file,
keeping the newest 1000 receipts. Use it only when asked. `.fux/output.toml`
can switch it on (`[cli.answer] journal`), as it can `no_refer`; neither has an
off flag, so use `--no-output-config` to bypass.

## 9 · Budget and exit codes

- **`audit.budget`** is `{bytes, used, dropped}`. `dropped` passages scored but
  did not fit. A bigger answer is a `[refer] budget` change in `.fux/tune.toml`
  (see `fux-config`), not a retry.
- **`answer` exits 0** on success, on no match and on the index fallback; `1` on a
  fux error (outside a repo, bad config, missing `.fux/pii.toml`); `2` on a usage
  error. **`verify` exits 0 only for `reproduced`**, and 1 for an unreadable file.

`answer` carries no `archived` flag. If a cited document may be retired, run `fux ask --json` for the same question and follow the `fux-archived-results` policy.

## Don't

- **Don't put every passage under `citation`** — each passage names its own document.
- **Don't say "current"** for `stale`, `as-ingested`, `cached`, `unverified` or any `source: index` answer.
- **Don't open a `#pN` locator as a line number.**
- **Don't report `fux verify` without `--rerun` as proof** of anything.
- **Don't use `ask` or `find` for line ranges**, and don't pass `--top` or `-q` to `answer`.
- **Don't enable `--journal` unasked** — it records questions in plaintext.
- **Don't run `fux correct` because the answer was wrong** — say which document
  should have answered and **propose** the command (`fux-correct`). It writes
  committed files and records a claim under somebody's name.
- **Don't loop on an unreachable URL**; report it as unverified.

Related skills: fux-usage, fux-search, fux-graph, fux-sources, fux-index, fux-maintain, fux-config, fux-mcp, fux-fetcher, fux-pii, fux-decoder, fux-enrich, fux-archived-results.
