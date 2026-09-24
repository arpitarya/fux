---
type: Standing Record
kind: component
name: SR-SERVE
title: "SR-SERVE (0158) — `fux serve`, the ask explorer: a local page that renders `ask --json --why` and computes nothing"
description: "Arpit's framing, 2026-09-22 — fux is like Google: if the ten documents an agent is handed are the right ten, the answer is mostly right. So the inspection surface is question-first. `fux serve` starts a stdlib server bound to 127.0.0.1 with no --host, serves one self-contained page, and answers GET /ask with the byte-identical stdout of `fux ask --json --why --band`. The page is a RENDERER: it computes no score, no band and no rank, because a second ranker in a browser is a restatement in the L0 sense. Every lever it prints is a proposal; no route writes a committed byte. Since W-220 (2026-09-23) the page has three tabs — Ask, Documents, Index — and the server calls fux.inspect in-process for the last two, on demand and cached under .fux/runtime/inspect/; the browser still computes nothing."
status: accepted
date: 2026-09-22
feature: the ask explorer — a local page over the real ask
owns: [src/fux/serve@045449d1c10f]
laws: [L1, L2, L4, L6, L8, L10]
timestamp: 2026-09-22T00:00:00Z
content_sha: 8062288b5facbc5cfaed864d306916b85e016a660d2f81a66ee1823b1d26afa0
ratifies: "Arpit, 2026-09-22 (Cowork, W-210) — three sample pages built on his machine, the per-token ingest X-ray REJECTED as a front page ('do you believe people will go through this big document?') and the question-first explorer ratified in its modern-dark form: 'the way I'm thinking about fux is something like Google. If a question gets asked, if you have the best 10 documents, the answer the agent gives is going to be mostly correct.'"
---

<!-- COMPONENTS-START — GENERATED from records/README.md's OWNERSHIP and DESCRIBES tables by scripts/gen-components.py. Do not edit by hand: change the table, then run `python scripts/gen-components.py --write`. -->

**Owns** — the components this record decides:

- [`src/fux/serve/`](../src/fux/serve) · dir

<!-- COMPONENTS-END -->

# SR-SERVE — ask, see why, see the lever

## §1 — For humans

**`fux inspect` tells you whether the index is any good. `fux serve` tells you
why *this question* got *those ten documents*.** They are different questions:
`inspect` walks the corpus and reports its shape, and `serve` starts from a
question a person typed and opens the hood on one ranking.

**The framing is Arpit's and it decides the design.** *"The way I'm thinking
about fux is something like Google. If a question gets asked, if you have the
best 10 documents, the answer the agent gives is going to be mostly correct."*
Every inspection tool in fux is judged by that test — and the first one built
while this was being designed, a per-token X-ray of one document's ingest,
**failed it**: *"do you believe people will go through this big document?"* What
replaced it is question-first.

🔴 **The page is a renderer and nothing else.** It computes no score, no band
and no rank. That is not modesty about effort; it is the only shape this feature
can legally take. A browser cannot hold a corpus's postings and stay honest —
the three-document sample already embedded 96 KB of stems — and re-implementing
BM25F, the walk and the band in JavaScript would be **two rankers that could
disagree while both looked correct**, which is the restatement
[SR-LAW-0](0002_LAW-0-authority.md) decision 1 forbids by its own test.

**So there is a server, and the server runs `ask`.** Not *the same code path* —
**the same command**, in-process, with its stdout handed back. The byte-equality
is then not a property somebody has to maintain; it is the implementation.

| question | answered by |
|---|---|
| is the machine set up? | `fux doctor` |
| is the index any good? | `fux inspect` |
| **why did this question get these ten documents?** | **`fux serve`** |
| what links to what? | `fux explain` · `fux graph` · `fux path` |
| what does the agent get over a protocol? | `fux mcp` |

⚠ **`fux serve` and `fux mcp` are different surfaces and neither is a mode of
the other.** `mcp` hands an agent results over a protocol;
[SR-MCP](0136_mcp.md) owns it. `serve` shows a **person** why those results are
what they are. Making one a flag on the other would put a human inspection page
behind a machine transport, or a machine transport behind an HTML renderer.

## §2 — For agents

### Context

**W-210, filed 2026-09-22 from five sample pages built in a Cowork session** on
Arpit's machine, under `.fux/runtime/trace/` — gitignored, never committed,
because they embed words and quoted passages ([L2](0004_LAW-2-content-never-durable.md)
and [SR-POSTINGS](0112_postings.md) decision 2). Two of the five were rejected
and three ratified; the design below is the modern-dark explorer.

🔴 **Those samples restated the ranker, and that is why this record exists.**
They carried a BM25 replay and a JS port of `walk.ppr()`, because there was no
server to ask — and they were *convincing*, which is the problem. A page that
computes plausible numbers is indistinguishable from one that reports true ones
until somebody checks. **The shipped page inherits none of that code.**

**Two findings the samples produced on this repository**, recorded because they
are about the corpus rather than about the tool: a law record ranked **#4 behind
an archived proposal** on its own question, and **58 of 150 top-10 slots across
15 probes were archived documents**. Archived crowding is this repository's
largest ranking lever, ahead of any analyzer change.

### Decision

**1. The verb is `fux serve`, it does not return, and it is in the `serve`
group** beside `mcp` and `daemon` ([SR-CLI](0101_cli-surface.md) §1). Flat, like
every other verb: `--port` and `--open`, no subcommand tree.

**2. 🔴 It binds `127.0.0.1` and there is no `--host`.** Not a default — a
contract. The page shows a corpus's vocabulary, its passages, and the questions
somebody typed; [L4](0006_LAW-4-offline-by-default.md) is offline-by-default and
a page on `0.0.0.0` is that content offered to a network.
`serve._bind_address` is a **function** so the refusal has a name, an error
message and a test, and so that a future `--host` has to *delete* a refusal
rather than pass through one.

**3. 🔴 `GET /ask` returns the byte-identical stdout of
`fux ask --json --why --band`**, and it gets those bytes by running that
command in this process. **Not an equivalent payload — the same one.** A second
builder would be a second contract, free to drift one key at a time with nothing
to notice, and the page would quietly begin describing a ranking fux did not do.
⚠ **The cost is an argparse parse and an output-config read per request**, on a
localhost tool a person types into. The alternative buys microseconds and sells
the one property the page exists to have.
`tests/serve/test_routes.py::test_ask_is_byte_identical_to_the_cli` pins it,
including on a query that matches nothing — the shape a page is likeliest to
special-case.

**4. Every route is `GET`, and none of them writes a committed byte.**

| route | answers with |
|---|---|
| `/` | the one bundled page |
| `/ask?q=…&top=N` | `fux ask --json --why --band` |
| `/graph?seed=…` | `fux graph --seed … --json` |
| `/health` | version, index schema id, analyzer version, bind address |
| `/inspect/documents` | the rows of `.fux/index/REGISTER` (decision 15) |
| `/inspect/document?loc=…` | one document's X-ray — [SR-INSPECT](0156_inspect.md) decision 20 |
| `/inspect/document/probes?loc=…` | that document's own probes — SR-INSPECT decision 19 |
| `/inspect/index` | the corpus report **without** probes, as a job with progress |
| `/inspect/probes[?all=1]` | the corpus report **with** probes, sampled or every document |

⚠ **Amended 2026-09-23 (W-220): the five `/inspect/` routes write the
GITIGNORED runtime cache** — `.fux/runtime/inspect/`'s facts, probes and
dictionary, exactly what `fux inspect` writes for the same index. Nothing else,
and never a committed byte ([L2](0004_LAW-2-content-never-durable.md),
[L8](0001_LAWS.md)). A GET that fills a cache is a read that remembers; a route
that changed what is indexed would be an apply button, which decision 10
refuses.

🔴 **`POST`, `PUT`, `PATCH` and `DELETE` are 405 with a sentence**, not a
missing handler. The refusal is what tells the next person that read-only is a
decision rather than an omission somebody should helpfully fill in.

**5. 🔴 The page computes no score, no band and no rank**, and a source gate
holds it: `tests/serve/test_page_computes_nothing.py`. ⚠ **Amended 2026-09-23
(W-220), and narrowed rather than deleted:** the *browser* still computes
nothing — no score, no band, no rank, no order — but the **server** now calls
`fux.inspect`'s library for the Documents and Index tabs, exactly as it already
runs `ask` for the Ask tab. Every number those tabs show is a field of what
`fux inspect --json` would print; the triage order is the one the engine
returned, and the page never re-sorts it. The arithmetic it may do
is presentation only — a percentage of #1 for a bar width, a difference of two
**printed** numbers, a share of the printed per-term contributions for a stacked
segment. **If a number cannot be pointed at in `ask --json --why`, it does not
go on the page**; the change is to `--why` and its record, never a computation
in the browser.

⚠ **A source gate is crude, and it is the only kind available.** A behavioural
test would need a second ranker to compare against, which is the thing being
forbidden; reading the file is the one check that cannot be satisfied by making
the second ranker agree.

**6. One self-contained file, no external host.** `src/fux/serve/page.html`,
inline CSS and JS: it must render with the network unplugged, which is
[L4](0006_LAW-4-offline-by-default.md) and also simply what an offline tool
owes. ⚠ **[L10](0011_LAW-10-bundled-output.md) is satisfied trivially here** —
for one self-contained HTML file the authored form and the built form are the
same bytes, so there is nothing to bundle. **A page that grows a second file
gains a build step in the same change**, or it has stopped being one artefact.

**7. Stdlib only.** `http.server` is enough for one person on one machine.
[L1](0003_LAW-1-zero-cost.md) permits a dependency and a record still has to
decide one; none is decided here, and none is needed.

**8. 🔴 No route logs anything, and `log_message` is silenced deliberately.**
`BaseHTTPRequestHandler` writes an access line per request naming the full query
string — which is the question somebody typed.
[L8](0001_LAWS.md) decision 8 puts every durable trace of use on a gitignored
path; the one surface that exists for it is the provenance journal, which is
opt-in ([SR-PROVENANCE](0142_provenance.md) decision 10) and is not this.

**9. The lever table is a rule per condition over the JSON**, and the page
carries no free prose about ranking. Each card names the command or config key —
never prose alone.

| condition, from `ask --json --why` | lever tag |
|---|---|
| rank 1 and `separation` below `separation_floor` | `fux correct --pin` |
| a query term in this document's `missing` | `fux enrich` · `fux correct` |
| a matched term with `df/n` above the boilerplate line, carrying score | `[index] stopwords` |
| a matched term with a `title`-field count | `title` |
| `boosted` and the `route` shows movement | `[graph] ask_boost` · `ask_kinds` |
| rank > 1 and within the near-tie width of #1, nothing missing | `supersedes` · `archived=` |
| the result is archived | `archived=` |
| `related` is non-empty on the top result | `fux correct` |
| none of the above | — |

⚠ **Two thresholds are PROVISIONAL in exactly the sense
[SR-INSPECT](0156_inspect.md) uses the word** — the boilerplate line and the
near-tie width — and **the page prints that word to the reader**, not only to
the reader of its source. They are tuned to no corpus. A lever phrased on an
untuned threshold and presented without the caveat would be a guess passed off
as a measurement, which is the one thing an inspection tool must never do.

**10. 🔴 The page proposes and never acts.** No *apply this lever* button, no
write route, no edit. Every lever is a committed change made by a person or by a
session that was asked — the discipline `fux inspect` already carries, and the
reason the `fux-serve` skill says *never apply a lever it printed unasked*.

**11. The empty state is the page's most important state.** When `answerable` is
false and the list is empty, the page renders an **abstain card** that says
declining is a correct outcome, names the unknown words, and offers one action.
The band exists so an agent is not handed ten wrong links; a page that rendered
that as an error would be arguing with the feature it is displaying.

**12. Archived results carry the badge and the reading stance.** The rule is
[`fux-archived-results`](../.claude/skills/fux-archived-results/SKILL.md)'s and
[SR-ARCHIVED-CONTENT](0134_archived-content.md)'s — *authoritative for a history
question, misleading for an architecture question, dangerous for a build task* —
and this page **links it rather than rewriting it.**

**13. The stepper shows stage COMPLETION, not stage duration, because there are
no timings to show.** `ask --json` carries no `ms` fields.
[L3](0005_LAW-3-deterministic.md) forbids wall-clock output in what fux writes,
so a page that invented durations would be printing a number no verb produced.
⚠ **W-210's definition of done asked for *"the stepper reads `ms` from the
JSON"*, and the honest version of that requirement is this one** — if `--why`
ever gains `ms`, the stepper reads it. `tests/serve/test_page_computes_nothing.py`
holds that no clock is read either way.

**14. Rungs 2–4 were not this record's when it was written.** Rungs 3 and 4 are
now decision 15's tabs; **rung 2 (`fux ask --html`) is still unbuilt and out of
W-220's scope.** `fux ask --html <file>` (the same
renderer, one question inlined), `fux trace <doc> --html` (the per-document
findability card) and `/docs` (corpus reachability) are filed in W-210 and land
with their own decisions. What is reserved for them here is
**`.fux/runtime/trace/`** — gitignored, runtime-only, because anything those
rungs write names words and quotes passages.

**15. One page, three tabs — Ask · Documents · Index — and no `/docs` route**
(Arpit, 2026-09-23, W-220). Switching is a tab in the page, never a URL to
remember.

- **Documents** lists every row of `.fux/index/REGISTER`. **Clicking one**
  computes that document's X-ray and nothing else, then asks for its probes.
- **Index** computes the corpus report **when the tab is opened** — the
  exhaustive lenses first, with **both sampled halves skipped** (self-retrieval
  and the probes each cost one real `ask` per query) — and then streams them in
  behind, through one shared query cache, with a progress
  line (a phase, a count and a total; no clock is read). It probes an **evenly
  spaced sample labelled an estimate**, with a *probe every document* button.
- 🔴 **Everything is computed ON THE FLY by `fux serve`** — *"I just want to do
  fux serve and the application itself should run the commands"*. Nobody runs
  `fux inspect` first. The server imports `fux.inspect` and calls it
  **in-process, never through a subprocess**; one engine, two front doors
  ([SR-INSPECT](0156_inspect.md) decision 22).
- **Lazy and cached.** Nothing is computed at start-up. The server keeps one
  `IndexView`, re-read when the committed shards change, and one job per
  (tab, shards) — reopening a tab on an unchanged index recomputes nothing.

### Consequences

- ⚠ **W-214 (2026-09-22) moved the page's colour and its note, and decision 11
  survives narrowed.** `answerable` is `band != none`
  ([SR-CONFIDENCE](0141_confidence.md) decision 3a, Arpit's ruling), so the
  **empty state now fires on `none` alone** — which is what decision 11 always
  described, since that state has no results to render either way. Two things
  had to move with it: the ring is coloured **by band, not by `answerable`**,
  because otherwise a near-tie would be painted the same green as a clear
  winner; and the note beside a rendered list now fires on `band === "weak"`
  and says *open both and judge* rather than *fux would not stand behind this*.
  🔴 **The old note's argument — that ten wrong links produce a confident wrong
  answer — is the premise W-213 measured against**, so leaving it on the page
  would have been the page arguing with the engine it displays.

- **A new surface a consumer can point at their own corpus**, at `$0`, offline,
  with no dependency and no build step.
- 🔴 **One more place a ranking can be misread.** Every number on the page is
  fux's, but the page chooses what to put next to what — and adjacency is an
  argument. The provisional-threshold caveat is printed for exactly this reason.
- ⚠ **`/ask` costs an argparse parse and a config read per request.** Accepted
  in decision 3; the alternative is the drift this record exists to prevent.
- ⚠ **The attribution the page draws did not exist before this feature.**
  `--why` gained `matched[].contribution` and `rerank_uplift`
  ([SR-PROVENANCE](0142_provenance.md) decision 14) so the page would not have
  to compute them. **That is the shape every future panel takes**: add the field
  to the engine's own output, or do not show the number.

### Alternatives considered

| | why not |
|---|---|
| **`fux ask --html`, one file per question** | the first rung proposed, and Arpit asked for *"an HTML document which will have the whole index and you can ask a question"* — a page you leave open and type into. It survives as rung 2, which is a flag on the same renderer rather than a second page |
| **Ship the postings to the browser and rank in JS** | 96 KB of stems for three documents, and a second BM25F, walk and band — a restatement in the L0 sense, and the one this feature was closest to shipping |
| **A mode of `fux mcp`** | a human inspection page behind a machine transport. Different audiences, different shapes; SR-MCP owns one and this owns the other |
| **Bind `0.0.0.0` behind a `--host` flag** | it makes the fence a preference. A person who needs this off-machine needs a different tool with a different record |
| **An *apply this lever* button** | every lever is a committed change. A page that edits is no longer an inspection tool, and the one-click version of `fux correct --pin` is the version nobody reviews |
| **A one-number *page quality score*** | SR-INSPECT refused the same thing for the same reason: it becomes the figure everybody quotes and nobody can act on |

### Reference (required)

- **Lucene's `explain` API** — a *second query against one document*, never
  instrumentation of the first. The per-term attribution decision 5 depends on
  follows that discipline exactly; see
  [SR-PROVENANCE](0142_provenance.md) decision 14.
  https://www.elastic.co/search-labs/blog/elasticsearch-scoring-and-explain-api
- **Arpit, 2026-09-22 (Cowork)** — the ratification quoted in `ratifies`, and
  the rejection of the per-token ingest X-ray as a front page.
- [`archive/open/W-210-fux-serve-ask-explorer.md`](../archive/open/W-210-fux-serve-ask-explorer.md)
  — the item, the panel-by-panel design and the hazards.

### Veto condition

🔴 **Reopen if the page is ever found computing a score, a band or a rank** —
including "just for the bar" or "only to sort ties". The source gate is the
tripwire, and a change that adds a number the JSON does not carry is the change
this record exists to refuse.

**Reopen if `/ask` stops being the CLI's own stdout.** The moment the route
builds its own payload, decision 3's guarantee is prose rather than mechanism,
and the page's honesty becomes something somebody has to maintain.

**Reopen if a bind address other than `127.0.0.1` is ever accepted**, by a flag,
an environment variable or a config key. That is not a change to this verb; it
is a different tool.

## References

- [SR-CLI](0101_cli-surface.md) — the verb surface and the `serve` group
- [SR-ASK](0103_ask.md) — the stages the page names, and the non-monotone rule
- [SR-CONFIDENCE](0141_confidence.md) — the band, `separation` and its floor
- [SR-PROVENANCE](0142_provenance.md) — `--why`, and decision 14's attribution
- [SR-GRAPH](0126_graph.md) — the walk the `/graph` route renders
- [SR-INSPECT](0156_inspect.md) — the sibling verb, and the word *provisional*
- [SR-ARCHIVED-CONTENT](0134_archived-content.md) — the stance an archived row carries
- [SR-MCP](0136_mcp.md) — the other non-returning surface, and not this one
