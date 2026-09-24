---
type: OpenItem
id: W-220
title: "W-220 — the index X-ray: one engine, four zoom levels, judged by what a person types"
description: "Arpit asked (2026-09-23) to see how one document is ingested and indexed, and then how that works for the whole index. Two design samples were built from real runs. They found that inspect's findable share reads 100 % while 21 of 120 title probes miss their own top 10, and that 526 of 1 672 documents share a title. The design extends SR-INSPECT and W-210's rungs 3–4. Fully ruled 2026-09-23: inspect computes it, and fux serve computes it on demand when a tab is opened — no separate command. Not built."
status: closed
closed: 2026-09-24
lane: build
timestamp: 2026-09-23T00:00:00Z
filed: 2026-09-23
ball: none
---

# W-220 — the index X-ray

## ✅ CLOSED 2026-09-24 (Claude Code, Opus) — all four rungs built

**Built:**
- **R1** · `inspect/facts.py`: pass A, cached in `.fux/runtime/inspect/facts.json`
  per document.
- **R2** · `inspect/probes.py`: titles and headings; data files on both bars.
  `title-probe reach` is now the headline row.
- **R3** · `fux serve` has Ask · Documents · Index tabs. It calls `fux.inspect`
  in-process, lazily and cached, with probes streamed behind the fast lenses.
- **R4** · `inspect/diff.py`: `--diff A B`. A lost edge is always an alert.

The fold (identity, segments, chunks, triage) and the one-document X-ray are in
`inspect/xray.py`.

**Records:**
- SR-INSPECT decisions 17–22, plus five levers;
- SR-SERVE decisions 4 and 5 amended, 15 new;
- SR-CLI decision 11;
- SR-DOTFUX `runtime/inspect/`;
- six co-owners of `fuxdir.py`, re-read and noted.

**Tests:** both suites green. The new ones are
`tests/test_inspect_xray.py` (19), `tests/serve/test_xray_routes.py` (10) and
`tests_e2e/test_inspect_xray_verb.py` (2). The e2e test plants an html decoder
that strips hrefs.

**What it found on this repository, live via `fux serve`** (descriptive, 1 672
documents, a 50-document probe sample):

| finding | value |
|---|---|
| documents sharing a title | **526 in 99 groups** — the same figure the design sample filed |
| data files identifiable by title | 141 of 559 |
| passages cut between two words | **16 202** of 144 500 |
| title-probe reach (sample) | 82 % |
| data files in the sample | 4 of 13 identifiable, 7 of 13 reachable |
| heading probes in the top 10 | 129 of 246 |

**Cost, on a loaded machine** (orders of magnitude, not a benchmark):
- Index tab: 278 s cold, 6 s warm;
- probe job: ≈ 1.3 s per query;
- a reopened tab: instant.

⚠ **One design change the spec did not name.** The probe cache key is the shards
**plus the `tune.toml` bytes**, not the index root alone, because a probe cached
under one `[bm25f]` and read under another would report a ranking nobody ran
(SR-INSPECT decision 19).

⚠ **Self-retrieval moved off the Index tab's fast path.** It is one real query
per document too, so the tab's first render skips both sampled halves and the
probe job runs them through one shared cache (SR-SERVE decision 15).

**Out of scope, still:** every lever, since findings 2–7 each become their own
item measured on golden data first; `ask --html`; the Node reader.

**Model: Opus** for the rulings' follow-through and SR-INSPECT's amendment (a new
headline metric and a new cache); **Sonnet** for rungs 1, 3 and 4 once ruled.

✅ **Fully ruled 2026-09-23 — NOT built.** Nothing in `src/`, `node/` or `tests/`
moved.

## The ask

- *"I want a view of a sample document, how that gets ingested, what all things
  get indexed, how it gets indexed … how it would be useful for debugging and how
  it can be used to improve the decoders as well as chunking."* (2026-09-23)
- *"create a design how it is going to work for the whole index"* (2026-09-23)
- Standing frame: the Google-style top-10 test (2026-09-22). A per-token dump was
  rejected **as a front page** on W-210, so the top-10 view leads and the token
  view is the drill-down.

## What exists already, and what this adds

| piece | state | this item |
|---|---|---|
| [SR-INSPECT](../../records/0156_inspect.md) — six lenses, three checks, a local dictionary | built | adds a facts pass, three lenses and a probe lens; reuses the dictionary |
| W-210 rung 3 — `fux trace <doc> --html` | filed inside the closed W-210, not built, no open item | picked up here as the L3 drill-down |
| W-210 rung 4 — `fux serve /docs` | same | picked up here as the L0–L2 view |
| `inspect --diff` | nothing | new: corpus diff for any decoder, rules or analyzer bump |

## The design, in one screen

- **Three passes, each cached on its own key**
  - **A · per-document facts:** decode → fields → analyze → chunk, using the
    engine's own helpers (SR-INSPECT d5). Key = sha + decoder digest +
    `RULES_VERSION` + analyzer + `[refer]` bounds. An unchanged document is never
    recomputed.
  - **B · corpus fold, at read time:** shared titles, segments by
    decoder × folder × archived, plus inspect's six lenses. Nothing corpus-wide is
    stored per document (the edges.py invariant).
  - **C · probes:** one real `ask` per probe (the title by default). An evenly
    spaced sample, labelled an estimate (SR-INSPECT d7), with `--all` to exhaust.
    Key = index root hash + probe text.
- **Four zoom levels:** L0 corpus (top-10 headline by class, no single score) →
  L1 segments (decoder × folder report card) → L2 triage queue (one row per
  document, worst first) → L3 document (the per-doc X-ray).
- **Diff mode:** two `report.json` files → terms, edges, flen, passages,
  identity and probe ranks per document. **Edge loss is always an alert.**
- **Contract:** nothing committed (L2, L8) · no timestamp (L3, SR-INSPECT d14) ·
  full counts beside capped lists (d13) · levers named, none applied (d12) · never
  fetches (L4) · the walk honours `.fux/sources/dirs`, and any recursive walk
  skips `work/golden/` (L11) · probe numbers are never claims about engine quality
  (SR-RS, SR-WORK-ENVIRONMENTS) · nothing promised above 10 000 documents
  (SR-WORK-SCALE).

## What the samples found

Descriptive only, not `blind` and not a golden run. Per-doc = one invented HTML
runbook in a 6-doc scratch repo. Corpus = this repository's index, 1 672
documents, `work/golden/` excluded.

| # | finding | evidence | lever (a later item, measured on golden first) | record |
|---|---|---|---|---|
| 1 | **Self-retrieval can't see misses** | inspect `findable share` = 100 %. Title probes: 99/120 in own top 10, **21 miss** | probe lens replaces it as the headline (its floor is already dropped, d9a) | SR-INSPECT |
| 2 | **Identity collisions** | **526 documents share 99 titles** (`predictions-set-1.jsonl` ×35 …). The json decoder titles 124 documents by their **first key** (`rows` ×22). json: 9 of 13 sampled miss | data decoders claim a path-derived title via META_FIELDS | SR-DECODE, SR-INGEST |
| 3 | **jsonl cut mid-word** | 15 884 of 76 683 jsonl passages (21 %) cut between words; prose has 0 | jsonl emits one record per paragraph (the table-row rule) | SR-DECODE, SR-REFER |
| 4 | **Page chrome indexed** | sample: 24/222 body tokens, and boilerplate queries return it (band `weak`). This repo: 3 documents | add `nav header aside footer` to html `_SKIP` | SR-DECODE |
| 5 | **Link targets tokenised** | 2.7 % of prose body tokens. `md` on 1 429/1 672 docs | strip in `extract.py`, **not** the decoder: a decoder strip deleted all 3 edges | SR-EXTRACTED |
| 6 | **Plural-acronym junk terms** | 4 020 tokens in 357 docs: `DCs`→`cs` ×2 040, `URLs`→`ur`/`ls` | analyzer v4 | own record |
| 7 | **Section mislabel and chrome passages** | the sample's warning cited under §Thresholds. A nav-only passage is cited 3rd | decoder honours `<section>` depth; #4 fixes the rest | SR-REFER, SR-DECODE |
| 8 | **Owner outranked via the graph** | "drain the retry queue": lexical #2 → #1 via graph over the owner | not a decoder lever | W-168 |

Also from `fux inspect` on this repo: near-duplicate share 23.7 % (flagged
*attention*), 638 of 1 071 graph nodes orphaned, json/jsonl/csv carry 0 edges.

Cost, measured once on the bridge VM with another session active (orders of
magnitude, not a benchmark):

- pass A: 162 s cold for 1 672 documents
- inspect: 35 s with a warm dictionary
- pass C: ≈2.5 s per probe

## Rulings

**Ruled by Arpit, 2026-09-23:**

- **Data files are held to BOTH bars.** *"both of them if it is about
  inspecting it i want both the options."* Every data document (json, jsonl,
  csv, toml, yaml) is reported against:
  - **identifiable:** no other document shares its title.
  - **reachable:** it's in the top 10 for its own probe, the same bar as prose.

  The two are reported side by side and never averaged into one number.
- **It lives inside `fux inspect`.** *"should all this live inside fux inspect
  yes it should."* No new verb. SR-INSPECT d1 stands, and rungs 1, 2 and 4 are
  inspect's.

**Also ruled by Arpit, 2026-09-23** (the first three said in chat earlier the
same day and not filed until now, because the bridge dropped mid-session):

- **One page, with tabs — no `/docs` route.** `fux serve` opens one page:
  **Ask** (the explorer as today), **Documents**, **Index**. Switching is a tab
  in the page, not a new URL to remember.
- **Documents come from the REGISTER, and open one at a time.** The tab lists
  every document from `.fux/index/REGISTER`. **Clicking one** shows that
  document's X-ray — what was ingested, what was indexed, and how it links to
  other documents. ⚠ **No trace runs for every document up front.**
- **Probes use titles AND headings.** Accepted cost: ≈7.8× the probes per prose
  document.
- 🔴 **Everything is computed ON THE FLY by `fux serve` — never a separate
  command first.** *"I don't want to … run some command and then … do a serve
  … I just want to do fux serve and the application itself should run the
  commands, get whatever details need to be fetched so it can be displayed on
  the UI for analysis."*

**What that ruling means for the build, stated so it cannot be misread:**

- **One command:** `fux serve`. Nobody runs `fux inspect` first. `fux inspect`
  stays as the CLI for CI, scripts and `--diff`, and both call **the same
  library functions** — one engine, two front doors.
- **In-process, never a subprocess.** The server imports `fux.inspect` and calls
  it; it does not shell out to the CLI.
- **Lazy, per tab:** nothing is computed at start-up. Opening **Index** runs the
  corpus pass; clicking a document runs **that document's** facts pass only.
- **Cached, so the second look is instant.** Pass A is keyed on sha + decoder
  digest + `RULES_VERSION` + analyzer + refer bounds; probes on index root hash
  + probe text; the cache lives under gitignored `.fux/runtime/inspect/`.
  Re-opening a tab on an unchanged index recomputes nothing.
- **The slow part is visible, never silent.** The fast lenses render first. The
  probe lens (real `ask` calls, titles and headings) runs behind them with a
  progress line. **By default it probes an evenly spaced sample, labelled an
  estimate** (SR-INSPECT d7, a rule already in force), with a **"probe every
  document"** button.
- ⚠ **SR-SERVE decision 5 must be amended, not broken.** It says the page
  computes nothing. After this, **the browser still computes nothing** — no
  score, no band, no rank in JavaScript — but **the server calls inspect's
  library**, exactly as it already calls `ask` for the Ask tab. The amendment
  states that line; it does not delete the rule.
- **Read-only still.** No route writes a committed byte; the only writes are
  the runtime cache (L2, L8). No fetch (L4).

## Definition of done — per rung, after the rulings

- **R1 · facts pass + decoder / chunk / identity lenses in `fux inspect`.**
  - `report.json` gains the per-document rows and segment tables.
  - The facts cache sits under `.fux/runtime/inspect/`.
  - SR-INSPECT amended first.
- **R2 · probe lens.**
  - Sampled title probes, classed as question-bearing vs data.
  - Data documents are reported on both bars: identifiable and reachable (ruled 2026-09-23).
  - Replaces self-retrieval as the findability headline.
  - SR-INSPECT amended.
- **R3 · the tabs in `fux serve`, computed on the fly.**
  - One page: **Ask · Documents · Index**. No `/docs` route.
  - **Documents:** the REGISTER list; click one → its X-ray (ingested, indexed,
    links in and out), computed for that document on the click and cached.
  - **Index:** L0 headline → L1 segments → L2 worst-first triage, computed when
    the tab opens; probes stream in behind the fast lenses, sampled by default,
    with a button to probe every document.
  - Server calls `fux.inspect` in-process; the browser computes nothing.
  - SR-SERVE amended (decision 5's line, the two new tabs); SR-INSPECT names
    serve as its second caller.
- **R4 · `fux inspect --diff A B`.**
  - Descriptive, with edge loss always an alert.
  - The review artifact for any decoder `VERSION`, `RULES_VERSION` or analyzer
    bump.
- **Every rung:**
  - both suites green
  - WORKLOG, IMPLEMENTATION, OPEN-WORK and registry updated in the same change

## In / out of scope

- **In:** the four rungs above.
- **Out:**
  - Applying any lever. Findings 2–7 each become their own item, measured on
    golden data first.
  - W-210 rung 2 (`ask --html`).
  - The Node reader (SR-INSPECT d16).
  - A single index score (d11).

## Key files

- `src/fux/inspect/` — `__init__.py`, `_scan.py`, `lenses.py`, `checks.py`,
  `dictionary.py`
- `src/fux/serve/`
- imported, not copied: `ingest/extract.py`, `ingest/parse.py`,
  `refer/_chunk.py`, `decode/__init__.py`

## Records to amend

- **SR-INSPECT:** lenses, probe lens, facts cache, `--diff`
- **SR-SERVE:** the `/docs` route and rung 3
- **SR-CLI:** new flags
- **SR-DOTFUX:** the runtime cache path. `.fux/runtime/trace/` is already
  reserved.

## Tests

- Report byte-identical on an unchanged index.
- No timestamp.
- Full count beside every capped list.
- A recursive walk never enters `work/golden/` (plant a file there and assert
  it's absent).
- The facts cache invalidates on a decoder `VERSION` or `RULES_VERSION` bump,
  and only for the bound documents.
- `--diff` flags edge loss: fixture = an html decoder that strips hrefs.
- The probe sample is evenly spaced and labelled an estimate.
- `git status` is clean after a run.

## Hazards

- **Probe cost:** full probing is an overnight job at 10 000 documents. The
  sample is the default for that reason.
- **Probe numbers are this corpus describing itself.** A quality claim still
  needs fux-lab and the golden sets.
- **Words on disk:** everything names words and titles, so it stays in
  `.fux/runtime/`.
- **Title probes favour documents whose title is also in their body.** Say so
  on the page.

## Evidence — runtime only, gitignored, never committed

`.fux/runtime/trace/` on Arpit's machine:

- `payment-retry.ingest-xray.html` — the per-doc design
- `index-xray.design.html` — the whole-index design
- the JSON captures beside them

Like W-210's samples, **they are a design reference, not part of the repo**. The
builder regenerates them from this spec.
