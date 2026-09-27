---
type: Handoff
name: W-229
description: "Everything `fux inspect` reports is visible in the fux explorer — every lens the report carries gets a panel on the Index tab, `--diff` gets a route, and a test binds the page to the report's keys so the two cannot drift. Ratified 2026-09-28, NOT built."
item: W-229
filed: 2026-09-28
ball: agent
---

# W-229 — inspect ⇄ explorer parity: everything in `inspect` is visible in `serve`

**Status: BUILT and closed 2026-09-28 (Claude Code, Opus).** All seven DoD
items: one card per lens on the Index tab in the prose report's order, each with
its own lever; document names open the Documents tab and terms the Words tab;
`/inspect/diff` compares the last `fux inspect` report with the Index tab's by
`diff.compare`; `tests/test_serve_renders_every_lens.py` binds the page to the
report's keys; SR-SERVE decision 16; both skills; CHANGELOG; IMPLEMENTATION.
Verified by rendering the Index tab in Node from this repo's real report: 13
cards, no `undefined`, no `NaN`.

**Model:** Claude Code, Sonnet — rendering and one test; no ranking, no
config, no new law.

## §1 — The ruling

Arpit, 2026-09-28 (Cowork): *"W-228 and everything in inspect should be
present in `serve` so that we can see visually."*

It stands on two earlier rulings: the explorer is the one page with tabs and
computes nothing (W-220, SR-SERVE d3–d5 as amended), and the whole X-ray lives
in `inspect` with no separate command. **The rule this item makes true: a
lens that `fux inspect` reports and the explorer does not show is a defect.**

## §2 — The gap, measured 2026-09-28

`inspect.as_dict()` carries these top-level sections; the Index tab
(`page.html` `renderIndex`) renders the ticked ones only:

| section | rendered today | what is missing on the page |
|---|---|---|
| `corpus`, `checks` | ✅ L0 card | — |
| `probes` | ✅ probes card, sample + probe-all | — |
| `segments` | ✅ L1 card | — |
| `triage`, `triage_count` | ✅ L2 card | — |
| `identity` | ✅ shared-titles card | — |
| `boilerplate` | ✗ (the Words tab shows the *vocabulary*, not the lens) | the named high-df offenders, hapax share, Zipf/Heaps fit, boilerplate share of postings |
| `findability` | ✗ | the unreachable documents, findable share, the fingerprint that failed |
| `lengths` | ✗ | per-field token distribution, `no_headings`, the shortest and longest documents |
| `duplication` | ✗ | near-duplicate pairs with their exact Jaccard; heading-set families |
| `coverage` | ✗ | kept/dropped share, zero-token documents, the enrich queue |
| `graph` | ✗ | orphans, hubs by in-degree, community sizes |
| `chunks` | ✗ | word-cut passages per decoder |
| `levers`, `lever` | partly (identity only) | one lever line per finding, from `LEVERS`, on every card |
| `--diff` | ✗ no route | two cached reports compared: findings gained and lost |

## §3 — Definition of done

1. **One card per section.** Every top-level key of `inspect.as_dict()` that
   is a lens has a card on the Index tab, in the order `inspect`'s prose
   report prints them; each card carries the lens's numbers, its named
   offenders (top lists as the report caps them), and **its lever from
   `LEVERS`** — never a lever the page invents.
2. **Every document name is a link** into the Documents tab (the `opendoc`
   pattern already on the page); every term name is a link into the Words tab.
3. **Nothing is computed on the page** (SR-SERVE d5). Every number comes from
   the `/inspect/index` and `/inspect/probes` responses as they are; a lens
   the server already returns needs no new route.
4. **`/inspect/diff`** — a GET route taking two cached report ids from
   `.fux/runtime/inspect/` (the ids the cache already keys on: shard content
   shas) and returning what `fux inspect --diff` prints, as JSON; the Index tab
   gets a *compare with the previous report* control when a second cached
   report exists. Read-only; it writes nothing.
5. **The parity test.** `tests/test_serve_renders_every_lens.py`: for every
   top-level key of a fixture report's `as_dict()` (excluding the non-lens keys
   the test names — `corpus`, `levers`, `triage_count`), `page.html` contains
   a renderer that references that key. A new lens without a card fails here,
   which is the whole point: **W-228's `families` lens lands against this test
   and cannot ship invisible.**
6. **Fast lenses render before probes**, as today; the new cards are on the
   fast path and add no wait.
7. **Records and skills**: SR-SERVE gains a decision stating the parity rule
   in one sentence and naming the test; `fux-serve` and `fux-inspect` skills
   say the Index tab shows every lens; `CHANGELOG.md`; `IMPLEMENTATION.md`.

## §4 — Not in scope

- No lens changes; no thresholds; nothing in `src/fux/inspect/` beyond a
  `diff` entry point if `--diff`'s logic is not already importable.
- No new tab. Everything lands on **Index**; Documents and Words are untouched.
- Charts. Tables and numbers, like every other card; a chart is a separate
  ask.

## §5 — Hazards

- 🔴 `src/fux/inspect/` may be held by another session (`NOW.md`); this item
  needs only `serve/` and the test, and should stay there.
- `page.html` is one file with no build step (L10 reads the other way here:
  it *is* the served artefact). Keep the cards in the same `renderIndex`
  style; do not introduce a framework.
- The Words tab already shows a boilerplate *class* per term. The boilerplate
  *card* is the lens's corpus-level numbers and named offenders — link the two,
  do not duplicate the vocabulary table.

## §6 — Related

- [W-228](W-228-document-families.md) — the `families` lens; its DoD 7 is
  satisfied by this item's parity test, and it lands after this one.
- W-220 (archived) — the X-ray tabs and the on-the-fly ruling this extends.
