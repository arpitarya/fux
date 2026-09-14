---
name: fux-search
description: Search the Fux index in depth with `fux ask` and `fux find` — flags, the --json fields, the confidence band (band, answerable, missing), --why, -q fusion, --expand for vocabulary gaps, and find's folder and phrase filters. Use when asked to "search the docs", "find where X is documented", "why did this rank", "fux ask returned nothing" or "narrow results to a folder". Read-only and offline; for exact line ranges use fux-answer.
---

# Searching with `fux ask` and `fux find`

Both verbs rank **documents** from the committed index. Neither fetches, neither
writes, and neither needs the network. Resolve the `fux` command first — see the
`fux-usage` skill (`fux` → `uv run fux` → `./.venv/bin/fux`, on Windows `.venv\Scripts\fux.exe` → `python -m fux`).

## 1 · Pick the invocation

| the ask | run |
|---|---|
| candidates you will judge yourself | `fux ask "<q>" --json --band` |
| paths to pipe into another tool | `fux find "<q>"` |
| only results under one folder | `fux find "<q>" --under docs/runbooks/ --top 20` |
| only documents containing an exact phrase | `fux find "<q>" --phrase "blue green deploy"` |
| "why did this rank" / "why is X above Y" | `fux ask "<q>" --why --json` |
| two ways of saying the same thing | `fux ask "<q>" -q "<other phrasing>" --json --band` |
| the corpus probably uses different words | `fux ask "<q>" --expand "<a passage YOU write — section 5a>" --json --band` |
| is my result caused by repo config? | re-run with `--no-tune`, then with `--no-output-config` |
| the exact lines that answer it | not here — `fux answer` (see `fux-answer`) |

**Always pass `--band` when you will act on the result.** Without it the
confidence block is not printed at all.

## 2 · Flags, verified

| flag | `ask` | `find` | effect |
|---|:-:|:-:|---|
| `--json` | ✓ | ✓ | machine-readable payload; **prefer it** |
| `--top N` | ✓ | ✓ | max results (engine default 5; `.fux/output.toml` may change it) |
| `--band` | ✓ | ✓ | emit the `confidence` block (JSON) or a `confidence:` line (stderr) |
| `-q TEXT` / `--query TEXT` | ✓ | ✓ | another phrasing; repeatable; rankings fused by RRF |
| `--expand TEXT` | ✓ | ✓ | extra terms scored at a discount (`[ranking] expand_weight` in `.fux/tune.toml`) |
| `--explain` | ✓ | — | which path answered: `[scan]` / `[accelerator]` line, or `"path"` in JSON |
| `--why` | ✓ | — | the ranking derivation (section 7) |
| `--sections` / `--no-sections` | ✓ | — | show or hide matched `§ heading` lines **and** the JSON `headings` field |
| `--phrase TEXT` | — | ✓ | keep docs whose local text has these words adjacent, in order |
| `--under PREFIX` | — | ✓ | keep docs whose `loc` starts with PREFIX (plain string prefix) |
| `--all` | — | ✓ | keep docs carrying every term of the positional query |
| `--fast` / `--scan` | ✓ | ✓ | accelerator vs reference scan — **identical results**, speed only |
| `--no-tune` | ✓ | ✓ | ignore `.fux/tune.toml` |
| `--no-output-config` | ✓ | ✓ | ignore `.fux/output.toml` |

⚠ **There is no `--no-json`, `--no-band` or `--no-explain`.** If `.fux/output.toml`
turns one of those on, the only way back is `--no-output-config`.

## 3 · Read the JSON, branch on fields

```json
{"results": [{"id": "file:docs/mesh.md", "title": "Service mesh", "loc": "docs/mesh.md",
              "score": 5.9021, "archived": false, "tie": false,
              "headings": ["Rollback procedure"]}],
 "confidence": {"band": "partial", "answerable": true, "missing": ["mtls"], "...": "..."},
 "fused": true, "path": "scan", "derivation": {"...": "..."}}
```

| key | present when | means |
|---|---|---|
| `results[]` | always (`[]` on no match) | ranked documents |
| `loc` | always | a path or a URL — **never a line range** |
| `headings` | `ask` unless `--no-sections`; `find` always | up to 3 committed headings matching the query; `[]` = none matched |
| `tie` | always | `true`: this row's rounded score equals another candidate's, so its position came from the tie-break, not the ranking |
| `archived` | always | retired source — follow the `fux-archived-results` policy |
| `confidence` | only with `--band` | section 4 |
| `fused` | only with more than one phrasing | `score` is an RRF score |
| `path` / `derivation` | only with `--explain` / `--why` | diagnostics |

⚠ **An absent key means "not asked for", never a claim.** A missing `confidence`
is not band `none`; re-run with `--band`.

**`headings` is your section pointer.** It is the finest unit `ask` can honestly
give. Open the document and go to that heading, or use `fux answer` for lines.

## 4 · The confidence block

Checked top to bottom; the first true row wins.

| `band` | condition | what you do |
|---|---|---|
| `none` | nothing scored (`answerable: false`) | **abstain.** Say the index has nothing on it |
| `partial` | a query term appears nowhere in the corpus (`missing` non-empty), or `doc_coverage` is below a non-zero `doc_coverage_floor` | answer, and **name the missing terms** — or retry (section 6) |
| `weak` | `separation < separation_floor` — top two are near-tied | do not conclude; report the top candidates, or sharpen the query |
| `grounded` | otherwise | use it and cite it |

- **`missing`** holds your own words, as typed, that no document contains. It is
  the field to surface to a human.
- **`coverage`** is corpus-wide. **`doc_coverage`** is the same measure inside the
  top document. A low `doc_coverage` beside `grounded` means your terms are
  scattered across documents that individually answer none of it.
- **`separation_floor` / `doc_coverage_floor`** are the cutoffs this band was
  judged under. They are repo-configurable, so **bands are not comparable across
  repos** without them.
- **`verified` is always `unverified` on `ask`/`find`** — they never look at the
  source. Freshness comes only from `fux answer`.
- **`support`** counts results above zero **within `--top`**, not corpus-wide.
- Text mode prints one `confidence: …` line on **stderr**.

## 5 · What a score is

- **Single query:** a BM25F score. Compare it only against other rows of **the
  same result list** — never across queries, repos or tune files.
- **Fused (`-q`):** `1/(60+rank)` summed across phrasings; values sit around
  `0.01–0.05`. `--json` carries `"fused": true`. ⚠ **On a fused list the band
  describes the FIRST phrasing only**, and `tie` is inherited from the arm that
  ranked the document best, so do not read it as a fused tie.
- **Each phrasing is retrieved at `--top` and no deeper.** Raise `--top` for a
  deeper fusion.
- **`--expand`:** expansion terms score below your own words, and a document that
  matches **only** expansion terms is dropped. `missing` still describes your
  question, not the expansion. **You write the text — section 5a.**

## 5a · `--expand` — YOU are the author, and what to write

🔴 **Fux never writes the expansion. It cannot.** No fux path may call a model,
so there is no `--auto-expand` and there never will be. **You are the model in
this loop**: you write the text, fux scores it deterministically, and the
receipt replays it. If you skip this, `--expand` does nothing.

**Write a short passage that answers the question in the words the document
would use — not a list of synonyms.** Two or three sentences, as if you were
the document. Guessing wrong is cheap; a document matching only your words is
dropped, so the floor is "no change", never a wrong citation.

```console
# the question uses "outage"; the document is titled
# "checkout unavailable for 47 minutes" and never says "outage"

fux ask "what caused the outage" --json --band \
  --expand "Checkout was unavailable for 47 minutes. The payment service
            returned 503 after a config rollout. Recovery was a rollback."
```

**Do it in this order:**

1. Ask plainly first. Read `confidence.missing` — those are the words the
   corpus does **not** have.
2. Only if the band is `none` or `partial`, write the passage using what you
   know of the corpus's own vocabulary (headings you have seen, `fux find`
   output, the folder's house terms).
3. Re-ask **once** with `--expand`. If it is still thin, report honestly — do
   not keep rewriting the passage.

⚠ **`-q` is a different tool and they do not combine into one mechanism.** Use
`-q` when you know two real *phrasings* of the question (their rankings are
fused by RRF); use `--expand` when you are guessing at the *document's*
vocabulary (one ranking, extra terms at a discount).
- **Results are deterministic** for the same index, tune file and working tree
  (with `[ranking] rerank_weight` above 0, the reranker reads local files).
  Retrying an identical command is wasted time.

## 6 · Empty or thin results — the retry ladder

**Fux ranks the words in the documents.** Most misses are vocabulary gaps, and
there is no fuzzy or prefix matching (`rollbak` never matches; `rollbacks` does
match `rollback`, via stemming).

| signal | next move |
|---|---|
| `No confident matches.` on **stderr** / band `none`, every term in `missing` | the corpus does not use these words — re-ask with the corpus's words, or add `--expand` |
| band `partial`, some terms in `missing` | replace or drop the missing term; keep the rest |
| band `weak` | add the distinguishing term, or add a `-q` phrasing; if still `weak`, report the top 2–3 |
| right area, wrong folder | `fux find "<q>" --under <prefix> --top 20` |
| the document you expect is not listed | raise `--top` — **filters never add results** |
| `grounded` but low `doc_coverage` | check `headings`; the answer may need two documents |

**Stop after about three reformulations** and report what you searched. An
honest *"the index has nothing on this"* beats a guessed citation.

## 7 · `--why` — how the ranking got here

Text goes to **stderr**; stdout is unchanged:

```text
[why] reachable 959 -> window 20 -> placed 3 -> answered 1 (cut at 7.6178)
       #2 docs/deploy.md 10.1143  matched rollback,deploy  absent canary  rerank 3->2  untuned #3
```

In `--json`, `derivation` holds `gates` (`reachable` = documents in the index,
`in_window`, `placed`, `answered`, `cut_score`) and one entry per **returned**
document: `score`, `rank` (0-based), `matched[]` (`term`, `analyzed`, `df`,
`fields` as counts in `body, heading, title, path, ctx` order with trailing zeros
trimmed — index it defensively — and `expanded`),
`missing`, `archived`, `multiplier`, and — only when measured —
`rank_before_rerank` and `rank_untuned`.

| you see | it means |
|---|---|
| `absent` / `missing` lists a key term | the doc lacks that word — a vocabulary issue, not a ranking bug |
| `rank_before_rerank` differs from `rank` | the proximity reranker moved it |
| `rank_untuned` differs from `rank` | `.fux/tune.toml` moved it — confirm with `--no-tune` |
| matches land in `heading`/`title` counts | by default those fields outweigh `body` |

⚠ **`--why` only describes returned documents.** To ask "why not X", raise
`--top` until X appears, then compare. The score is quoted, never recomputed.
With a tune file present, `--why` runs a second, untuned query.

## 8 · `find` in a pipe

- **stdout is bare locations**, one per line. Every note goes to stderr.
- ✅ **`No confident matches.` goes to STDERR, exit 0** (since 2.1.0). stdout is
  **empty** on the no-match path, so a pipe sees zero lines and needs no guard.
  ⚠ **It was on stdout before that**, which is why older notes tell you to
  `grep -qx` it out first; that guard is harmless and no longer needed.
- **`url:` documents appear as URLs**; a pipe may receive both kinds.
- Filters run **after** ranking, on the top `--top` results. A `[filter] … removed
  N` line on stderr says what went; the band still describes the unfiltered list.
- `--phrase` uses the index's analyzer (stopwords dropped, stemmed), reads local
  files, and **keeps** `url:` documents it cannot read offline.

```bash
# stdout is paths or nothing, so `xargs` on an empty file is a no-op.
fux find "retry policy" --under services/ --top 20 > hits.txt
xargs grep -n "max_retries" < hits.txt
```

## 9 · Defaults, paths, notes and exit codes

- **Scan is the default.** `--fast` uses the accelerator when present and fresh.
  The stderr note *"no fresh accelerator"* is advice, not an error; building one
  is the `fux-index` skill's job.
- **`.fux/output.toml` sets defaults:** `[cli] band`, `top`; `[cli.ask]
  explain`, `sections`; `[cli.json] enabled`; per-verb tables such as
  `[cli.find]`. A present file that lacks a key a verb needs is an error;
  see `fux-config`.
- **stderr notes, never parse them:** changed paths pending re-index, the
  archived-results note, `[filter]`, `[why]`, `confidence:`.

| exit | when |
|---|---|
| `0` | success — **including no matches** |
| `1` | fux error: not inside a fux repo, malformed `.fux/tune.toml` or `.fux/output.toml`, missing `.fux/pii.toml` |
| `2` | usage error — a flag the verb does not take (e.g. `fux find "<q>" --why`) |
| `130` | interrupted |

If a result carries `"archived": true`, follow the `fux-archived-results` policy.

## Don't

- **Don't report line numbers from `ask`/`find`**, or claim fux cannot give them — that is `fux answer`.
- **Don't read a missing `confidence` key as `none`.** You forgot `--band`.
- **Don't compare fused scores with single-query scores**, or any scores across queries or repos.
- **Don't expect `--under`, `--phrase` or `--all` to surface more** — raise `--top`.
- **Don't parse stderr.** The no-match line lives there now, with every other note.
- **Don't answer from `weak` or `none`** and cite the returned files as if they said it.
- **Don't re-run an identical query** hoping for a different ranking.

Related skills: fux-usage, fux-answer, fux-graph, fux-sources, fux-index, fux-maintain, fux-config, fux-mcp, fux-fetcher, fux-pii, fux-decoder, fux-enrich, fux-archived-results.
