---
type: OpenItem
id: W-210
title: "W-210 — `fux serve`: the ask explorer — a local page that shows the ten links, why each ranked, and the one lever that would change it"
description: "Arpit, 2026-09-22 (Cowork): fux is 'like Google' — if the ten documents an agent is handed are the right ten, the answer is mostly right. So the inspection tool is a QUESTION-first page: ask, see the ranked list, see per document which words won, which links helped, how sure fux is, and the lever. Three sample pages were built in the session and ratified as the reference design; this item ships the real verb over the real engine. Also carries the per-document findability card and the corpus reachability table as later rungs."
status: open
lane: agent
timestamp: 2026-09-22T00:00:00Z
filed: 2026-09-22
ball: agent
ruled: 2026-09-22
---

# W-210 — `fux serve`: ask, see why, see the lever

**Model: Opus** — a new verb across CLI, query and a served page, with an
HTML contract that a test must bind; the design is ratified but the data
contract between `ask --json` and the page has to be derived from the engine,
not guessed.

## ✅ RUNG 1 SHIPPED 2026-09-22 (Claude Code, Opus) — the verb, the page, the routes

**All eleven definition-of-done items met.** [SR-SERVE](../../records/0158_serve.md)
filed and accepted; `fux serve [--port N] [--open]` on `127.0.0.1` with **no
`--host`**; the four routes; one self-contained `src/fux/serve/page.html`; the
source gate that holds the page to computing nothing; `tests/serve/` (45) and
`tests_e2e/test_serve_verb.py` (4); the `fux-serve` skill on all four surfaces;
`.fux/runtime/trace/` reserved in SR-DOTFUX for rungs 2–3.

🔴 **The `--why` hazard was real, and it was worse than the item predicted.**
The item warned that `--why` might not carry per-term contributions. It did not —
and [SR-PROVENANCE](../../records/0142_provenance.md) **had refused to on
purpose**, in prose, as a standing decision: *"the scorer is not instrumented, no
per-term contribution is threaded through the hot path."* So the fix was not a
missing field, it was a decision to re-read. The resolution is decision 17: the
attribution runs in the **derivation pass**, over the documents that were
*shown*, which is Lucene's `explain` discipline that record already cites — *a
second query against one document, never a tax on the first.* The hot path is
untouched.

🔴 **And a second field had to come with it, which nothing anticipated.** The
printed score is `BM25F × proximity uplift × archived multiplier` — on this
repository the uplift is routinely **1.3** — so per-term contributions shown
beside the score leave a **23 % gap**. A page could close it only by dividing
two rounded numbers, which is exactly the *plausible number that disagrees with
the real one* `provenance.py` is written around. `rerank_uplift` is now a field,
and `tests_e2e` asserts the identity reconciles to 1e-9.

⚠ **Two DoD items were met in a different shape than written, and both are
stated rather than quietly adjusted:**

1. **DoD 6 — *"the stepper reads `ms` from the JSON"*.** `ask --json` carries no
   `ms` fields at all, and [L3](../../records/0005_LAW-3-deterministic.md) forbids
   wall-clock output in what fux writes. So the stepper shows stage
   **completion**, not duration, and the page reads no clock anywhere — which the
   gate asserts. Inventing durations to satisfy the sentence would have printed a
   number no verb produced.
2. **DoD 10 — *"a `docs/` page for the verb"*.** `docs/` is the OKF bundle root
   and carries no per-verb pages for any of the other nineteen verbs; a new one
   would restate SR-SERVE, which [L0](../../records/0002_LAW-0-authority.md)
   forbids. Met instead by the record, the `fux-serve` skill, the `.fux/README.md`
   verb table (all three copies) and a **glossary** entry.

**Rungs 2–4 are NOT built** — `fux ask --html`, `fux trace <doc> --html`, and
`/docs` — and neither are the two findings the samples produced (a law record at
#4 behind an archived proposal; 58 of 150 top-10 slots archived). Those are about
**this repository's corpus**, not about the tool, and they are recorded in
SR-SERVE §Context so the next person does not rediscover them.

---

## ✅ RULED 2026-09-22 (Arpit, Cowork) — what this is and is not

**The framing, in his words:** *"the way I'm thinking about fux is something
like Google. If a question gets asked, if you have the best 10 documents, the
answer the agent gives is going to be mostly correct."* Every inspection tool
in fux is judged by that test, and the first one built in the session — a
per-token X-ray of one document's ingest — **failed it** ("do you believe people
will go through this big document?"). What replaced it, and what he ratified in
three iterations (explorer → playful → modern), is **question-first**: type a
question, get the ranked list with the hood open.

**Ratified reference design** — three sample pages, built in the session over
the real analyzer, real graph edges and a BM25 replay, on his machine under
`.fux/runtime/trace/` (gitignored — they embed words and content, and stay
uncommitted by SR-POSTINGS decision 2 and L2):

| file | what it is | status |
|---|---|---|
| `ask.sample.html` | the **modern dark** explorer — the reference design for this item | ✅ ratified as the design |
| `ask-librarian.sample.html` | the playful variant (podium, sticky notes, constellation) — superseded by the above, kept for the constellation and the empty-state copy | reference only |
| `ask-explorer.sample.html` | the plain first version — tables; superseded | history |
| `0008_LAW-6-say-index.findability.html` | the **per-document** card — 15 probe questions, rank of this doc for each, who beat it, the lever | ✅ ratified as rung 3 |
| `0008_LAW-6-say-index.sample.html` | the per-token ingest X-ray | ❌ rejected as a front page; survives as a collapsed panel on the findability card |

⚠ **Those files are not in this repository and never will be.** The builder
regenerates them from this spec; the sample HTML is a design reference, not a
source file to copy. The one thing worth lifting verbatim is the **CSS design
language** below.

## Why a served page and not a written one

- `fux ask "…" --html` (one file per question) was the first rung proposed.
  Arpit's ask on 2026-09-22 was *"an HTML document which will have the whole
  index and you can ask a question"* — a page you leave open and type into.
- The page cannot hold 1 669 documents' postings in a browser and stay honest
  (the 3-document sample already embeds 96 KB of stems), and it cannot run
  fux's own ranker in JS without a second implementation of BM25F, the walk and
  the band — a **restatement in the L0 sense**: two rankers that could disagree
  while both looking correct.
- So the page is a **thin renderer** over the engine: `fux serve` starts a
  stdlib `http.server` on localhost, serves one bundled HTML page, and answers
  `GET /ask?q=…` with exactly what `fux ask --json --why` prints. **One ranker,
  one JSON, one page.** Nothing in the page computes a score.

## The page — panel by panel (the ratified design)

Every panel below exists in `ask.sample.html`; the builder ports the layout,
not the logic. Order on the page is the order here.

1. **Command bar.** One input, `/` focuses it from anywhere, Enter asks.
   Example chips beneath it come from `.fux/enrich/` questions and `fux
   correct` markers when present, else from the document titles — never
   hard-coded.
2. **Stepper — `lexical → graph → split → confidence`.** The four stages
   [SR-ASK](../../records/0103_ask.md) names, lit in sequence as the response
   arrives; `refer` shown dimmed as the fifth, since the page never fetches.
   The stage timings come from the JSON's `ms` fields, not from the page's
   own clock (L3 — no wall-clock output in anything fux writes; the page may
   animate, it may not measure).
3. **What the analyzer heard.** The query's tokens as pills: kept (stem
   shown), stopword (struck through, dimmed), unknown to the corpus (red).
   Source: the `--why` block's query terms; the page does not re-tokenise.
4. **Confidence ring.** The band as [SR-CONFIDENCE](../../records/0141_confidence.md)
   prints it — `band`, `answerable`, `separation` — drawn as an arc. The label
   is fux's word (`high` / `low` / `none`), never a percentage the page
   invented. ⚠ The sample shows *"#1 leads #2 by N%"* — that is the sample's
   own stand-in and **must not ship**; the ring shows `separation` against the
   floor the record names.
5. **Ranked list.** One row per result in **the order `ask` printed**, score as
   printed (BM25F, not a fused number — SR-ASK's non-monotone rule), rank
   badge, animated bar relative to #1, and the two badges the JSON already
   carries: `boosted` + `route` (*"↑ #3 -> #1 via graph"*) and *walk agrees*
   when boosted without moving. Archived results carry the archived badge and
   the reading stance [SR-ARCHIVED-CONTENT](../../records/0134_archived-content.md)-style: a history question vs a build task.
6. **Per-result detail (click a row).**
   - **Score by word** — one stacked bar, a segment per query term with its
     contribution from `--why`'s per-term rows; orange when the term's df/N is
     above the boilerplate line `fux inspect` uses, gold outline when the
     match is in the title field; missing terms as dashed red pills.
   - **Why #k is above** — a butterfly chart of the same terms against the row
     above: purple (above) vs cyan (this), Δ printed. Pure arithmetic on two
     `--why` blocks; no new numbers.
   - **The passage the agent would see** — the heading/snippet `ask` prints,
     hits highlighted. Not a re-scan of the document.
   - **Actions** — see §Levers. Each is a card with an icon and a **lever
     tag** naming the command or config key; never prose alone.
7. **The link walk.** The graph tier as a constellation: seeds = the lexical
   window (gold, sized by walk mass), `related` (cyan, pulsing), reached-with-
   query-words (grey), hubs (dim, with the link-IDF factor on hover). Edges
   are the `ref` edges the walk was allowed to follow — `kinds` from tune —
   drawn from `fux graph --seed <window> --json`. Below it, the `related`
   list as action cards with `route` and `mass`.
8. **Empty state.** When `answerable` is false and the list is empty: an
   abstain card, the unknown words named, one action (`fux correct` / enrich).
   **This is the page's most important state** — the band exists so an agent
   is not handed ten wrong links, and the page must make abstaining look like
   a correct outcome, not an error.

## Levers — the rule table

Each action card is produced by one rule over the JSON; the page carries no
free text about ranking. Rules, in the order they are tested per result:

| condition (from `ask --json --why`) | card | lever tag |
|---|---|---|
| rank 1 and `separation` below the floor | Coin flip with #2 — pin the intended answer | `fux correct --pin` |
| a query term absent from this document | Never says X — teach it the phrasing | `fux enrich` · `fux correct` |
| a matched term with df/N above the boilerplate line carrying score | Boilerplate carrying N pts — stopword candidate | `[index] stopwords` |
| a matched term in the title field | Title match — the cheapest, strongest lever | `title` |
| `boosted` and moved up | The walk lifted this past the words — knob is the graph | `[graph] ask_boost` · `ask_kinds` |
| rank > 1, score within 15 % of #1, no missing terms | Near-tie on the same words — duplication smell | `supersedes` · `archived=` |
| `related` entry is archived | A live page links to retired material — repoint | the linking document |
| `related` present at all | Reached by link, not by words — vocabulary gap | `fux correct` on that document |
| a hub above the in-degree line still in `related` | Hub crowding | `[graph] ask_link_idf` |
| none of the above | Clear winner — nothing to do | — |

⚠ Two of these thresholds — the boilerplate line and the 15 % near-tie — are
**provisional** in exactly the sense SR-INSPECT uses the word, and the page
prints it. They are not tuned to this repository.

## The three rungs

**Rung 1 — `fux serve` (this item's core).** The verb, the page, the JSON
route, the stepper, the ranked list, per-result detail, the walk, the empty
state. Definition of done below.

**Rung 2 — `fux ask --html <file>`.** The same page with one question's JSON
inlined, written under `.fux/runtime/trace/` — for sharing one result without
a server. Same renderer; a flag, not a second page.

**Rung 3 — the per-document findability card** (`fux trace <doc> --html`,
ratified from `…findability.html`). For one document: probe questions from its
title, its `fux correct` markers, its enrichment questions and a `--questions`
file — each run through the real `ask` — and for each: rank, who is above,
the lever. Header verdict REACHABLE / AT RISK / UNREACHABLE by top-10 share on
the questions it **owns**; a question another document should win is marked
*not owed*, never a miss. The per-token X-ray survives here only as a collapsed
panel. ⚠ The 2026-09-22 sample surfaced two real findings the builder should
expect to reproduce: a law record at #4 behind an **archived** proposal, and
**58 of 150 top-10 slots taken by archived documents** across 15 probes —
archived crowding is the largest lever in this repository, ahead of any
analyzer change.

**Rung 4 — corpus reachability** (`fux serve` route `/docs`, later). One row
per document, reachable share, worst-first. The view people would actually
leave open. Filed here so the page's routes are designed for it; **not** in
this item's DoD.

## Definition of done (rung 1)

1. **SR-SERVE** filed and accepted — the verb, the routes, the page contract,
   the rule table above, the runtime-only rule for anything the page writes,
   and the L4 fence (localhost only, no outbound request from the server or
   the page). SR-CLI gains the verb; SR-ASK, SR-CONFIDENCE and SR-GRAPH are
   cited, not restated. `records/README.md` register row and ownership.
2. **`fux serve [--port N] [--open]`** — stdlib `http.server`, binds
   `127.0.0.1` only, refuses any other bind address, prints the URL, exits 0
   on Ctrl-C. No dependency (L1 is amended, but none is needed here).
3. **Routes:** `GET /` → the page; `GET /ask?q=…` → the byte-identical
   output of `fux ask --json --why` for that query; `GET /graph?seed=…` →
   `fux graph --seed … --json`; `GET /health` → version + index schema id.
   **No route writes anything.** L8: the server keeps no log of queries unless
   the existing provenance journal consent (flag + output TOML) is on, in
   which case it is that journal and nothing else.
4. **One bundled page** — `src/fux/serve/page.html`, inline CSS and JS, no
   external host (L4; the page must render with the network unplugged).
   L10: what ships is the built artefact; the authored source may be split
   during development but one file is what the package carries.
5. **The page computes no score, no band, no rank.** A test loads the page's
   JS in Node and asserts the absence of any arithmetic over `score` fields
   beyond percentage-of-#1 for bar widths and the Δ of two printed numbers.
6. **The stepper reads `ms` from the JSON.** No `Date.now()` in the served
   page except for animation timing that never reaches the DOM as a number.
7. **Empty state** rendered from `answerable: false`, tested with a query no
   document matches.
8. **Archived results** carry the badge and the stance line.
9. **Tests:** `tests/serve/` — routes, bind refusal, byte-equality of `/ask`
   with the CLI, page snapshot bound by a golden-file test the way
   `test_claude_md_laws.py` binds the generated law block; `tests_e2e` starts
   the server as a user would and fetches `/ask`.
10. **Docs:** `docs/` page for the verb, `fux-serve` skill under
    `.claude/skills/` (read-only verb; when to open it; what a lever tag means;
    *never apply a lever it printed unasked* — same discipline as
    `fux-inspect`), CHANGELOG, IMPLEMENTATION.md, DOC-REGISTRY, WORKLOG.
11. `.fux/runtime/trace/` added to the runtime layout in SR-FUX-DIRECTORY for
    rungs 2–3.

## Design language (port verbatim from `ask.sample.html`)

- Dark: `--bg #0a0c12`, cards `rgba(255,255,255,.035)` with 1 px
  `rgba(255,255,255,.08)` borders, 18 px radius, backdrop blur.
- Accent gradient `#7c5cff → #3ec6ff`; ok `#22d3a6`, warn `#f5a524`, bad
  `#ff5c7a`, gold `#ffd166` (title match, seeds).
- System font stack only (`Inter, -apple-system, SF Pro Text, Segoe UI`);
  mono for every number; `font-variant-numeric: tabular-nums`.
- Entry animation: staggered 500 ms fade-up; bars, arcs and segments grow on
  the second animation frame; the command bar's border is a slow 6 s gradient
  sweep. Motion is decoration only — see DoD 6.
- Icons are inline SVG line icons; **no emoji** in the shipped page (the
  playful variant used them; the modern one does not).

## Hazards

- 🔴 **Restating the ranker in the page.** The 2026-09-22 samples *did* — a
  BM25 replay and a JS port of `walk.ppr()` — because there was no server. The
  shipped page inherits none of that code. If a number on the page cannot be
  pointed at in `ask --json --why`, it does not go on the page.
- 🔴 **Words on disk.** Rungs 2–3 write HTML that names words and quotes
  passages; that is runtime-only and gitignored, and the page must say so in
  its footer. A served page writes nothing.
- ⚠ **`--why` may not yet carry per-term contributions in the shape the
  stacked bar needs.** If it does not, the change is to `--why` (SR-PROVENANCE
  / SR-ASK), with the record amended — not a parallel computation in the page.
- ⚠ **The stance line for archived results** is
  [`fux-archived-results`](../../.claude/skills/fux-archived-results/SKILL.md)'s
  rule; link it, do not rewrite it.
- ⚠ `fux mcp` and `fux serve` are different surfaces (SR-MCP owns the former);
  do not make one a mode of the other.

## Out of scope

- Editing anything from the page — no "apply lever" buttons. Every lever is a
  committed change made by a human or a session that was asked; the page
  proposes.
- A hosted or shared deployment; `127.0.0.1` is the contract.
- Rung 4.

## Decisions taken by default — Arpit reverses any by a ruling

- The verb is `fux serve` (not `fux ui`, `fux web`, `fux explorer`).
- Port default `7337`; `--open` launches the browser, off by default.
- The boilerplate line and the near-tie threshold are the provisional values
  above until a golden rung says otherwise.
- The page ships dark only; a light theme is a later item if asked.
