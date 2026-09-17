# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This is the v0.30 rebuild's changelog — a fresh start. The v0.26 engine's
history is archived at [`archive/v0.26/CHANGELOG.md`](archive/v0.26/CHANGELOG.md).

## [Unreleased]

## [3.0.0-alpha.0] - 2026-09-17

**A major, and the two breaking changes are the reason.** `fux update` is gone —
`fux ingest` is the one verb over the corpus — and the committed index format is
`fux.index.v3`, which an existing index must be rebuilt into. Everything below
had accumulated unreleased since `2.0.1` on 2026-09-14; the four things a
consumer feels are:

- 🔴 **`fux update` is deleted** and a bare `fux ingest` now goes to the network.
  The offline form is `fux ingest --no-fetch`, and `fux hooks` must be re-run.
- 🔴 **`fux.index.v3`** — rebuild required, and the ingest summary says so.
- 🔴 **`[bm25f] b` defaults to `0.15`, not `0.75`** — the first ranking default
  here that is MEASURED rather than inherited, so **every score changes**.
- 🔴 **`confidence.answerable` is `false` for `weak` as well as `none`**, and
  `No confident matches.` moved to stderr.

Added since `2.0.1`: anchor text as a sixth BM25F field, link-following on
`fux ask`, `fux correct`, `fux inspect`, `fux lexical`, `fux graph --seed`, and
`fetch=` taking any fetcher name.

⚠ **This is an alpha and npm serves it under the `alpha` tag, not `latest`.**

### Removed — BREAKING, read this before upgrading a consumer

- 🔴 **`fux update` is deleted. `fux ingest` is the one verb over the corpus**
  ([W-177](work/open/W-177-ingest-absorbs-update.md); Arpit's ruling,
  2026-09-15). The first ingest and every re-ingest, for directories and URLs
  alike. **There is no deprecation alias** — `fux update` exits non-zero with
  argparse's *invalid choice*.

  | was | is |
  |---|---|
  | `fux update` | `fux ingest` |
  | `fux update --all` | `fux ingest --refetch-all` |
  | `fux update --check [--json]` | `fux ingest --check [--json]` |
  | `fux update --failed` | `fux ingest --failed` |
  | `fux update <entry>` | `fux ingest <entry>` |
  | `fux ingest --refresh-urls` *(hidden)* | *(deleted — it is the default now)* |

  - 🔴 **A bare `fux ingest` now GOES TO THE NETWORK.** It fetches the URLs
    known to be stale and says so on stderr. **The offline form is
    `fux ingest --no-fetch`** — the same flag, with the same meaning, that
    `fux add` already carries. CI and air-gapped clones want that one.
  - **`--all` is renamed because of where it lands.** On `update` it sat alone;
    on `ingest` it sits beside `--full`, and *all* and *full* read as synonyms
    while one selects **URLs** and the other re-extracts **documents**.
  - **Your git hooks change, and `fux hooks` rewrites them.** `post-merge` now
    runs `fux ingest --no-fetch`; `post-commit` is unchanged. **Split by
    caller:** the daemon fetches, a git hook never does. Re-run `fux hooks`
    after upgrading, or a merge will open sockets you did not ask for.
  - **`fux doctor`'s remediation strings name `fux ingest`.** The report shape
    is unchanged.
  - **`--check` and `--list-skipped` are two exit-early flags on one verb now.**
    Given both, **`--check` wins** — it is the one with a `--json` form and the
    one a pipeline gates on
    ([SR-INGEST](records/0106_ingest.md) decision 21b).
  - 🔴 **`fux update` exits `2`, not `1`, and your pipeline needs to know which.**
    `2` is argparse's usage-error code — an unknown verb, raised before fux's own
    error boundary exists — and it comes with argparse's usage message on stderr
    naming the valid verbs. **A `1` is fux failing; a `2` here is the verb being
    gone.** A job that treats anything non-`1` as *the runner broke* will read
    this upgrade as an outage. ([SR-CLI](records/0101_cli-surface.md) decision 5,
    amended 2026-09-16: fux produces `0`, `1`, `130`; argparse produces `2`. The
    old *"`2` is reserved and not produced"* is retired — it was a statement
    about `FuxError` that read as a statement about the process.)
  - ⚠ **What did NOT change:** which URLs a networked run goes out for (W-82
    ruling 3 — narrow by default), pinned `update=never` lines (never fetched,
    `--refetch-all` included), the transient-failure guarantee (a failed fetch
    keeps the prior record and exits `0`), and **law L4**, whose text says
    *paths*, plural, and never bounded how many
    ([SR-LAW-4](records/0006_LAW-4-offline-by-default.md)).

### Added

- **`fetch=` on a URL line takes ANY fetcher name** — a consumer drops
  `.fux/fetchers/glassbox.py` in, writes `fetch=glassbox`, and ingests; no
  engine change and no fux release ([W-178](work/open/W-178-consumer-planes-open-sets.md);
  Arpit's ruling, 2026-09-15).
  - **It is the pattern `.fux/decoders/` already shipped**, made symmetrical:
    **fetchers and decoders are one consumer-plane pattern**, and the `fetch=`
    validator reuses the decoder name regex rather than growing a second one.
  - **Shape only, never existence.** Lowercase letters, digits and underscores,
    no leading `_`, no `.py`, no directory part. Importing a fetcher to check a
    config line would run consumer code that may open a browser, so a
    **committed file would open a socket to decide whether a line is
    well-formed** — on a path L4 fences.
  - 🔴 **A typo parses now.** `fetch=glasbox` is a legal line naming a file
    nobody wrote, where the old enum refused it at read time. **`fux doctor`
    gains a `fetcher bindings` row** — the mirror of `decoder bindings` — so it
    surfaces before an ingest dies mid-run on somebody else's machine.
  - **`meta`, `keep`, `archived`, `enrich` and `update` stay enums**, and the
    attribute **key** set stays closed at seven. Open values, closed keys.
  - ⚠ **Every URL list valid today stays valid**, and `fux add --cdp` / `--http`
    are unchanged. There is deliberately **no `--fetch <name>` flag**: for a
    custom fetcher, `fux add <URL> --no-ingest`, edit the `fetch=` value, then
    `fux ingest <URL>`.
  - **Fixed on the way:** `.fux/sources/urls`' generated header printed
    `<duration>` for every typed attribute, so a fresh `fux setup` would have
    written `fetch=<duration>`. The placeholder is the attribute's now.

### Changed — RANKING, read this before upgrading a consumer

- 🔴 **`[bm25f] b` defaults to `0.15`, not `0.75`. Every score in the engine
  changes.** ([W-144](work/regression/2026-09-16-b-sweep-2/VERDICT.md); Arpit's
  ruling, 2026-09-16.) `b` is the strength of BM25's length normalisation, and
  **a table inflates a document's length with tokens that say nothing about the
  query** — so at `0.75` a document is punished for an appendix it did not ask
  to be measured on.
  - **Measured, under a rule frozen before the sweep**: the first value,
    descending `0.4 → 0.3 → 0.2 → 0.15`, that improves both benefit families
    with every control holding. `0.4` moves neither; `0.3` and `0.2` fix the
    rate-card case and leave the prose-with-appendix case where `0.75` does;
    **`0.15` moves both** — `+30` each, `p = 0.0000` against a required net
    of 12.
  - ⚠ **One synthetic corpus, and the run is `informed`.** 510 generated
    documents built so the mechanism can move. It says a lower `b` ranks better
    **on documents shaped like these**.
  - **No re-ingest is needed** — `b` is applied at query time.
  - 🔴 **`fux setup` writes `b` out in full**, so a repo set up before this
    upgrade keeps `0.75` in its committed `.fux/tune.toml` and **will not move**.
    Change the line, or delete it to take the new default. A fresh clone and a
    set-up repo now rank differently unless you do.

### Changed — read this before upgrading a consumer

- 🔴 **The committed index format is `fux.index.v3`, and an existing index must
  be rewritten: `fux ingest --full`.** There is no in-place migration and
  `store/reader.py` refuses a v2 shard rather than misreading one. ⚠ **Do NOT
  delete `.fux/index/` by hand** — `url:` records are the one thing in it no
  re-extraction can rebuild, and `--full` refuses rather than stranding them,
  naming each.
  - **What appeared:** a `ref` edge now carries `at` (anchor term hash → count,
    from the **link text the source document wrote**) and `al` (the token
    total). The `_format` bump is
    [SR-INDEX-LIFECYCLE](records/0108_index-lifecycle.md) decision 9.1 firing —
    *a property appeared, and a reader cannot know what it is missing.*
  - **`analyzer` and `tf_fields` are UNCHANGED**, so no term hash changes
    meaning and no `df` moves.
  - 🔴 **A vendored Node reader must be re-bundled with the same upgrade.**
    `.fux/node/fux.mjs` pins the schema string it was built with, so a
    re-ingested corpus and a stale bundle are a hard refusal. `fux setup`
    rewrites it.
  - **Nothing about ranking changes on upgrade** — see below.

### Added

- **Anchor text: what OTHER documents call this one, as a sixth BM25F field**
  ([W-168](work/open/W-168-search-improvements.md) step 1; Arpit's ruling,
  2026-09-15). Every other field is something a document says about itself.
  - **`[bm25f] anchor`, default `0.0` — OFF, and unmeasured.** `0.0` is not
    "weight zero": every anchor branch in the engine tests it and is skipped, so
    an unconfigured corpus scores **byte-identically** to the engine before the
    field existed. Measured: 5 536 byte-identical scan-vs-accelerator
    comparisons at the default, and 5 536 more at `anchor = 2.0`.
  - 🔴 **It is a RETRIEVAL change, not just a scoring one.** With it on, `fux
    ask` can return a document that contains **none** of the query's words —
    reached through what its linkers call it. That is the point; *a document is
    never a candidate for a word it does not contain* is the sentence it exists
    to stop being true.
  - **The words are committed on the SOURCE's edge**, never on the target's
    record, so editing one document never rewrites another's committed bytes.
    The per-target view ranking needs is folded at read time from
    `.fux/runtime/anchors/` — derived, gitignored, rebuilt by `fux build`.
  - **Terms, not text.** An anchor is stored as hashed terms, like every other
    posting: link text is content, and [L2](records/0004_LAW-2-content-never-durable.md)
    keeps content out of the index.
  - ⚠ **Turning it on is not recommended yet.** The frozen bar is
    [`2026-09-15-anchor-text`](work/regression/2026-09-15-anchor-text/PRE-REGISTRATION.md)
    and it has no verdict. **No claim about ranking quality is made.**

- 🔴 **`confidence.answerable` is now `false` for `weak` as well as `none`**
  (W-176 gate 1). It was `band != "none"`. **A consumer that branches on
  `band == "none"` is now wrong for half the refusals** and will answer from a
  ranking that could not separate its own top two hits.
  - **`weak` means the ranking could not choose.** SR-CONFIDENCE's band table
    has always said *do not answer* on that row; the payload beside it said
    `answerable: true`, and the field an agent branches on was the permissive
    one.
  - **This is why fux never abstained.** *Nothing scored above zero* is a state
    no real corpus produces, so the refusal was structurally unreachable. Four
    measured runs found the symptom — 20 of 20 blind unanswerable questions
    answered, twice; 0 abstentions of 124 across five golden rungs; 10 of 10
    planted unanswerables answered — and none could name the cause. It was one
    expression.
  - **`partial` is unchanged and stays answerable**, which is the whole
    distinction: its defect is *nameable*, so you answer and say what is
    missing. A `weak` has nothing to name.
  - **New `confidence.failed` key** naming which gate refused
    (`no_candidates`, `separation`); `[]` when nothing did. Always present.
  - ⚠ **`[confidence] separation_floor = 0.0` now disables abstention on
    separation entirely**, not just the `weak` label.
  - **Branch on `answerable`.** It is correct for both refusals and stays
    correct as W-176's remaining gates land.

### Added

- 🔴 **`fux ask` follows links: a boosted tier and a labelled `related` tier**
  (W-161). `ask` is now `lexical` → graph walk → split → confidence → refer.
  BM25F retrieves by shared vocabulary, so a document that never uses your
  words cannot be retrieved at any depth however central it is; the walk out of
  the top-k finds those.
  - **Tier A (boosted)** re-orders the documents BM25F retrieved by
    `RRF(lexical rank, PPR rank)`. **A row the walk moved carries its move** —
    `(graph #7 -> #2)` in text, `boosted` + `route` in `--json`.
  - **Tier B (`related`)** is a separate list of documents *no query word
    matched*, each with the route it was reached by (`#2 via ref`). **Never
    counted as an answer and never in the confidence band.** `fux answer` does
    fetch them and re-score on the bytes.
  - ⚠ **`results` may no longer be monotone in `score`.** The order is a rank
    fusion; the number is still BM25F. **A consumer re-sorting by `score` is
    re-deriving the lexical order** — which is a real thing to want, and
    `fux lexical` is the verb that returns it.
  - **New keys on every hit:** `boosted` (bool) and `route` (str | null), in
    `--json`, `fux.api` and the Node reader alike. Additive; `false`/`null` is
    the claim, never an absence.
  - **`fux_search` over MCP carries `related` unconditionally**, because a tool
    call cannot pass a flag.
  - **Off with:** `--no-related` per call; `[graph] ask_boost = false` /
    `ask_related = false` per repository; `--no-tune` turns the whole tier off
    with everything else. Six new `[graph]` keys — the two booleans are
    separate so either arm can be withdrawn without touching the other.
  - ⚠ **Unmeasured, and deliberately shipped that way.** Ratified on design;
    the two arms are frozen in
    [`work/regression/2026-09-14-graph-ask/`](work/regression/2026-09-14-graph-ask/PRE-REGISTRATION.md)
    and cannot be measured until the golden key carries link-dependent
    questions. **If either arm fails, that arm's default becomes `false`.**
  - **No new `.fux/output.toml` key**, so no existing config file breaks.
  - **`fux find` shares the boost and never gets `related`** — two
    ranked-document verbs must rank one corpus one way, but `find` pipes bare
    paths. **`fux lexical` is unchanged**, which is what it is for.
  - ⚠ **Node pays a full record parse per `ask`** while the tier is on: it
    rebuilds the graph plane in memory rather than requiring `fux build`. Its
    query latency is unmeasured.

### Changed

- 🔴 **`No confident matches.` goes to STDERR on `ask`, `find` and `answer`** —
  a **breaking change to a documented surface**, and the one thing in this entry
  to read before upgrading. `fux find` exists to be piped, and a line of prose on
  the stream that otherwise holds nothing but paths turns an empty result into
  one fake path. **stdout is now empty on the no-match path.**
  - **Unchanged:** exit code `0` (an honest decline is a successful run),
    `--json` (which never printed the sentence — the empty case is still
    `{"results": []}`), and the wording, so a consumer matching the text keeps
    matching it on the other stream.
  - **If you guard with `grep -qx "No confident matches."` before piping**, that
    guard is now unnecessary and still harmless.
  - **`fux graph` still prints it on stdout**, deliberately and in both readers.
  - Both readers moved in one change.
    [SR-FIND](records/0104_find.md) decision 6 · [SR-ASK](records/0103_ask.md)
    decision 7 · [SR-ANSWER](records/0105_answer.md) decision 7 ·
    [SR-CLI](records/0101_cli-surface.md) decision 6.
- **`fux remove` writes its exclusion to `.fux/.fuxignore`**, not as a `!` line
  in `.fux/sources/dirs`. The pattern is **anchored** (`/docs/a.md`), with a
  trailing `/` for a directory, because a bare name in that grammar means *at any
  depth*. `!` lines already in `dirs` **keep working and are left exactly alone**;
  `fux doctor`'s new `dirs exclusions migrated` row names each survivor with the
  one-line move. `fux add` refuses a path `.fux/.fuxignore` excludes, for the same
  reason it always refused a `!` line — there is no un-exclude by design.
  [SR-FUXIGNORE](records/0144_fuxignore.md) decisions 5a–5b ·
  [SR-DIR-LIST](records/0120_dir-list.md) decision 2d.

### Fixed

- 🔴 **Three ways a carried-forward record silently kept stale bytes.** Ingest
  reuses a document's extracted record when its source bytes are unchanged; two
  other inputs to extraction were not in that key, and one class of record was
  never re-processed at all. Each was already named in its record as *stated,
  not fixed*.

  **⚠ The first `fux ingest` after upgrading re-extracts every document, once.**
  That is the price of the new keys taking effect, it is paid on one run, and a
  no-op ingest after it re-extracts nothing — pinned by a test, because a digest
  scoped too coarsely would turn every future release into the same full pass.

  - **A decoder change now invalidates the documents it read.** Every built-in
    decoder declares `VERSION`; a consumer decoder in `.fux/decoders/` is
    digested by its file sha. **Keyed per extension**, so a `.pptx` fix
    re-extracts slides and leaves the markdown corpus alone.
    [SR-DECODE](records/0139_decode.md) decision 11a.
  - **An extraction-rule change now reaches unchanged documents.**
    `extract.RULES_VERSION` joins the `[index]` caps in the reuse key. Corpus-
    wide, because those rules run on every document.
    [SR-INGEST](records/0106_ingest.md) Consequences.
  - **A `url:` record is re-extracted from `.fux/acquired/`** when a PII,
    decoder or extraction-rule change lands — **offline**, from bytes already on
    disk. Before this, a `url:` record carried forward verbatim whenever the
    fetch did not happen, and under `update=never` that was permanent, `--full`
    included: a new redaction rule could not reach it, ever.
    [SR-PII](records/0148_pii.md).

  **A URL with no retained bytes is stranded, never dropped** — its record is
  left exactly as it is, the run warns, and `fux doctor`'s new
  `url redaction current` row names it. `keep=true` on the line is what lets the
  next policy change reach it offline.

  ⚠ **For maintainers of this repo:** `VERSION` and `RULES_VERSION` are bumped
  **by hand**, in the change that edits the module. Two tests fail a changed
  module whose constant did not move, so it is a recorded decision either way.

### Added

- **`fux correct "<question>" <doc>` — the words people ASK with, written onto
  the document that answers.** It appends one human-authored question to that
  document's existing `.fux/enrich/<sha>.md` and is indexed as the same `ctx`
  field as the model-written questions beside it: **same file, same field,
  different author.** doc2query's deterministic cousin; no new directory, no new
  ranking code.
  - **The marker is `corrections: N` in the frontmatter** — *the last N body
    lines are human* — so it sits in the half that is never indexed while the
    text sits in the half that is. `.fux/eval/corrections.tsv` (committed,
    sorted) is the durable record.
  - **`fux enrich --check` REPORTS a human line and never refuses it**, and the
    file stays indexed. A correction is by definition a question that failed
    retrieval. **Every human line is checked whatever its punctuation** — a
    correction with no `?` is checked too.
  - **A negative correction is refused** with the pointer: *"don't serve X"* is
    `supersedes` / `archived=`, corpus-wide. **A PII match is refused, not
    redacted** — `[PII:…]` as vocabulary retrieves nothing. **A refused command
    writes nothing.**
  - **No wall clock**: `generated:` derives from the document's committed
    `mtime`, so the bytes do not depend on when the command ran.
  - **`--pin`** forces one document to #1 for one exact question, **after** the
    ranking and after the reranker — `"pinned": true`, `[pinned]` in text, a
    `note:` on stderr, and the confidence band still computed from the pinned
    list so a weakly-supported pin still says `weak`. **Suspended when the
    document changes**, released only by `fux correct --reaffirm`, and named by
    `fux doctor`'s new `correction pins` row.
  - **`--why` says who wrote a `ctx` term**: `ctx_via` is `human`, `model`,
    `both` or `unattributed`.
  - **Both readers apply a pin.** `fux correct` is Python-only (the Node reader
    never writes), but the effect crosses.
  - Ships with the `fux-correct` guide skill on all four agent surfaces, whose
    first section is **propose the command, do not run it**.
    [SR-ENRICH](records/0137_enrich.md) decisions 19, 19a, 19b.

### Fixed (this release)

- 🔴 **`fux doctor`'s `pinned url bytes` row printed `[OK]`** beside *every
  citation from these will be `unverified`*. `cmd_doctor` takes the exit code
  from `ok` only for `level == "error"` rows, so a `warn` row's `ok=True` meant
  *print `[OK]`* — the row disclosed nothing. `ok=False, level="warn"` renders
  `[WARN]` and still exits 0, which is what *disclosed, never refused* meant.
  A test now asserts the **rendered line**.

- **`fux lexical` — the lexical core, named and frozen.** BM25F, then the
  proximity reranker, then RRF over any `-q` phrasings. **No graph stage,
  ever.** It takes every flag `ask` takes and returns `ask`'s exact output
  shape — **byte-identical today**, and held so by a test.
  - **It is not a better `ask` and not a faster one.** It is the baseline arm
    every ranking verdict needs, kept separate because `ask --scan` stops
    meaning *the words alone* the moment `ask` grows a stage.
  - **Frozen by contract:** a future component added to the lexical core
    becomes a new verb or a tunable, never a change to this one.
  - On the Node reader it is the **same function** as `ask`, so the freeze
    holds there by construction.
    [SR-CLI](records/0101_cli-surface.md) decision 12.
- **`fux graph --seed <id> [--seed <id>…]`** — the walk from documents you
  name, with no query in the way. Mass follows **argument order**, and
  `fux graph "<q>"` is now *defined* as `--seed` over the query's top-k, with a
  test asserting the two agree.
  - ⚠ **A hand-named seed reports `"score": null` and `"rank": n`.** There is
    no ranking behind it; the query form's seeds still carry their BM25F score.
  - A query and `--seed` together are refused, and so is neither; a seed that
    is not in the index is refused by name rather than walking from nowhere.
    [SR-GRAPH](records/0126_graph.md) decision 13.
- **Three graph-walk flags, `--kinds`, `--link-idf` and `--max-hops`, all OFF
  by default and inert at their defaults.** They exist so the mechanism the
  graph-composed `ask` needs can be driven and measured *before* `ask`
  composes it — landing both together would make one diff nobody could
  attribute a delta to. 🔴 **No measurement supports any setting of them yet.**
  [SR-GRAPH](records/0126_graph.md) decisions 14–15.

- **`fux inspect` — the index X-ray.** Six lenses over the committed index, all
  read-only: **boilerplate** (which words are on every document, with `df`, IDF,
  the Zipf slope and Heaps β), **findability** (documents no query can reach),
  **length and fields** (per-field totals and the vocabulary percentiles that
  killed index pruning here), **duplication and templates** (minhash pairs and
  identical heading sets), **analyzer coverage** (what never became a term), and
  **graph** (orphans, hubs, community sizes). `--json` for agents; a Markdown
  report and its JSON twin under the gitignored `.fux/runtime/inspect/`.
  - **Every finding names the lever that would change it and applies none** —
    stopwords, `.fuxignore`, `archived=`, `supersedes`, `fux enrich`, a decoder.
  - **Three checks carry a flag, and every floor prints the word *provisional*.**
    `fux inspect` **exits 0 whatever it finds**: a flag is attention, not a
    failure. There is no one-number index score.
  - **The words come from a gitignored, locally rebuilt hash → word dictionary**
    — the committed index holds term hashes, and still does. Nothing new is
    committed, nothing is fetched, and the report carries no timestamp, so it is
    byte-identical over an unchanged index.
  - Ships with the `fux-inspect` guide skill on all four agent surfaces.
    [SR-INSPECT](records/0156_inspect.md) ·
    [the floors run](work/regression/2026-09-14-inspect-floors/report.md).

- **The ingest summary counts deletions** — `…, N records deleted`, present only
  when `N > 0`. `write_index` writes the whole index, so a removal is an
  *absence*: every other number on that line could sit still while a document
  left the corpus, `0 shards written` included.
  [SR-INGEST](records/0106_ingest.md) Consequences.
- **`fux doctor`: `dirs exclusions migrated`** — a `warn` row listing the `!`
  lines left in `.fux/sources/dirs`. Distinct from the duplicate warning, which
  fires only when a pattern sits in both files; this one fires on every survivor.
  [SR-DOCTOR](records/0152_doctor.md).
- **`fux doctor`: `url redaction current`** — a `warn` row naming the `url:`
  documents a policy change could not reach for want of retained bytes. ⚠ It
  reads from derived state, so it does not travel with a cloned index.
  [SR-DOCTOR](records/0152_doctor.md).

## [2.0.1] - 2026-09-14

**Two shipped bugs, one in each of the two extension points a consumer
actually writes against.** Both had been live since the surfaces existed, and
both failed in the way that is hardest to notice: not with an error, but with
a plausible-looking result.

### Fixed

- **`[sources.url.config]` went VERBATIM to every fetcher, so a repo could
  configure at most ONE of the two shipped fetchers.** Each `configure()`
  raises on a key it does not know — deliberately — so `cdp_port` made
  `http.py` refuse the whole run, and the error named the innocent party.
  The table is now sliced **by shape, never by meaning**: a scalar at the top
  level is shared and reaches every fetcher, and a sub-table belongs to the
  fetcher whose name it carries. `[sources.url.config.cdp]` reaches `cdp.py`
  and nothing else; a sub-table naming a fetcher this run never loads is
  simply not read. **A flat table behaves exactly as before, so no existing
  repo changes.** [SR-FETCHER](records/0117_fetcher.md) decision 8.
- **An `.xlsx` row budget counted XML elements rather than records.** A
  worksheet carries a phantom blank `<row/>` for every row that was ever
  *styled*, and each one spent budget — so `max_table_rows = 10` delivered
  five data rows on a maintained tracker. The blanks were then dropped from
  the rendered table, leaving **no trace anywhere** that a fact had gone
  missing. `csv.py` never had this; it filters empty rows before applying the
  limit. [SR-TABULAR](records/0150_tabular.md) decision 7.
- **An `.xlsx` truncated at the row budget said nothing**, while `csv.py` has
  emitted `*(table truncated)*` the whole time. It now emits the same line,
  plus `*(columns past 40 dropped)*` for the column cap, which had no
  disclosure in either file. A sheet that exactly *fills* the budget says
  nothing — the notices are evidence of loss, so one row past the budget is
  what proves a tail exists.

### Changed

- **A `dict` at the top of `[sources.url.config]` is now read as a
  per-fetcher table** rather than handed to `configure()` as a value. Only
  the top level is namespaced. This is the one behaviour change in the patch
  and it is named here because a config table is a published surface.

## [2.0.0] - 2026-09-13

**The 2.0.0-alpha line, promoted — plus everything below, which had
accumulated unreleased since `2.0.0-alpha.7` on 2026-09-02.** Read the
`Added` / `Changed` / `Removed` / `Fixed` sections that follow for the detail;
this is what the major carries against `1.0.0`:

- **Record shape v2, tuning, `fux enrich`, MCP and reranking** (alpha.0), with
  the **dense lane removed** (alpha.1).
- **The URL freshness loop** (alpha.2), `ask --sections` and the `output.toml`
  fork closed (alpha.3), and three built-in decoders — jsonl, svg, images
  (alpha.4).
- **The acquired plane, declarative refusal detection, `ttl=`/`as-ingested`
  and PII redaction** (alpha.5) — a repository without `.fux/pii.toml` is
  refused rather than indexed.
- **Enrichment inside the PII boundary**, `fux enrich <TARGET>` and a cdp
  fetcher that survives concurrency (alpha.6); one enrichment-report path
  spelling on every platform (alpha.7).
- **The Node read plane** — `fux-engine` in both registries under one name,
  served as **one generated file** rather than 44 source modules
  ([L10](records/0011_LAW-10-bundled-output.md)).
- **The decision records moved to `records/` at the repo root** and were
  renumbered into three ranges; `ADR-<NAME>` is now `SR-<NAME>`. A
  documentation change, but it is what every citation in this changelog
  resolves against.

⚠ **Upgrading from `1.0.0` is not a drop-in:** the dense lane is gone, the
record shape is v2, and ingest refuses without `.fux/pii.toml`. Re-run
`fux ingest && fux build` after upgrading.

### Fixed — Windows, and three of these are shipped bugs rather than test defects

The full CI matrix ran green on Windows for the first time while cutting this
release, and it found what no developer machine here could:

- 🔴 **`fux`'s own stdout was the locale encoding.** `fux ask --json` piped to
  a file or to an agent emitted **cp1252 bytes** on Windows — an em dash in a
  document title arrived as `0x97`. `cli.main` and `fux-merge-index` now set
  UTF-8 before parsing an argument, which is the only legal encoding for JSON
  anyway (RFC 8259 §8.1). [SR-CLI-SURFACE](records/0101_cli-surface.md)
  decision 10a.
- 🔴 **The Node reader's `fux_passage` refused every path in the repository on
  Windows.** Its containment check compared against `base + "/"`, and the
  separator there is `\`. Python's twin was always correct; the differential
  arm caught the divergence the first time it ran on Windows.
- 🔴 **The engine read git's output with the platform code page** in
  `ingest/priors.py`, `maintain/runner.py` and `maintain/hooks.py` — and git
  prints *paths*, so one non-ASCII filename raised `UnicodeDecodeError` from
  inside the recency prior or silently lost that file's date.
- **A background re-index could strand work.** A commit landing between the
  runner's last check and its release had its own spawn refused, leaving
  `pending: 1` with nothing running. A runner now hands new ids to a successor.
  [SR-MAINTENANCE](records/0129_hooks.md).
- **`fux doctor`'s Node-shadowing row cannot fire on Windows** —
  `shutil.which` resolves through PATHEXT and npm writes `fux.cmd`. Named as
  unbuilt rather than left to look built; filed as W-159.


### Added

- **`.fux/output.toml`'s `journal` line now says what the key DOES.** It reads
  **`⚠ NOT a rendering key`** and names the file it appends to, instead of
  *"record each answer's receipt locally"* — which named the place and not the
  act ([SR-PROVENANCE](records/0142_provenance.md) decision 10, W-147).
  - **Both consent surfaces stay and both are explicit** (Arpit, 2026-09-13):
    `fux answer --journal` for one invocation, and a committed
    `[cli.answer] journal = true` for the repository — the second reviewable in
    git rather than by watching a terminal. **Default is `false` on both**;
    nothing records by accident.
  - **No behaviour changed** — both surfaces already worked. What is new is the
    disclosure, and a test binding all four states so neither surface can be
    tidied away by a reader who takes `output.toml` for a pure rendering config.

- **`mtime` on every `--json` hit** — `ask`, `find`, `fux.api`, the Node reader
  and both MCP servers ([SR-API](records/0154_api.md) decision 7, W-153). The
  document's committed **git commit timestamp, in whole UNIX seconds**.
  - **Every record already carried it and no caller could read it**, so you
    could not sort by recency, filter by age, or see how old an answer was.
  - 🔴 **Always present; `null` is a CLAIM**, not an absence — *this document
    carries no committed date*. A corpus copied **out** of its repository has no
    `mtime` anywhere, which `fux doctor`'s `recency prior` row reports.
  - ⚠ **Additive, and stated rather than assumed:** a consumer validating
    strictly against the previous `output.schema.json` will see a new key.
  - **It exposes a fact and orders nothing.** `mtime` reaches the sort only
    through the declared tie-break, at an equal score. **Prose output is
    unchanged.**

### Removed

- 🔴 **`.fux/tune.toml` `[ranking] archived_weight` and `recency_half_life_days`
  are REMOVED** (Arpit, 2026-09-13; [SR-TUNE](records/0135_tuning.md) decisions
  15a and 15b, W-152). With `superseded_weight` below, **all three document
  priors are gone** and `[ranking]` is `rerank_weight` and `expand_weight`.
  - **Nothing ranks differently.** `archived_weight` shipped at `1.0` and
    `recency_half_life_days` at `0.0` (off). Delete the lines; results are
    byte-identical.
  - **Why:** measured across 26 intent-split probes, every value that perfects
    *current-seeking* dismantles *history-seeking* one probe for one; at a
    half-life of a year or less, history-seeking drops to **0 of 13**. A
    per-document multiplier cannot carry a per-query distinction.
  - ⚠ **Both are refused BY NAME**, in the Python and Node readers alike.
  - **The facts are untouched and are what you branch on:** `archived: bool` on
    every JSON hit, `[archived]` in prose, and `mtime` on every record. At an
    **equal score** the declared tie-break still puts a live document above a
    retired one and a newer above an older.
  - 🔴 **The response note loses its `(demoted, weight N)` clause** — there is no
    demotion left to disclose.
  - **Also gone, because their only reader was the knob:**
    `fux.ingest.priors.recency_multiplier` (and its Node twin) and
    `newest_mtime` from the derived `.fux/runtime/stats.json`. The runtime plane
    is gitignored, so **no migration and no rebuild is required** — a stale
    `stats.json` that still carries the key is ignored.
  - `fux doctor`'s `ranking priors` row now covers one prior; its `recency prior`
    row now names what a missing `mtime` actually costs (no date reaches a
    caller; the tie-break's date key is inert).

- 🔴 **`.fux/tune.toml` `[ranking] superseded_weight` is REMOVED** (Arpit,
  2026-09-13; [SR-TUNE](records/0135_tuning.md) decision 15, W-151).
  Supersession is a **fact**, not a weight: no multiplier decides which document
  supersedes another, and the only band of values that ordered a corpus sensibly
  had its lower edge set by an **unrelated** document — so adding a document
  moved the correct value.
  - **Nothing ranks differently.** It shipped at `1.0`, which was already the
    identity. Delete the line and your results are byte-identical.
  - ⚠ **A committed `superseded_weight` is now an ERROR** — in the Python reader
    and the Node one — and the error **names the removal and its date** rather
    than reporting an unknown key. `fux setup` wrote this key into every
    `.fux/tune.toml` it created, so the generic message would have sent you
    hunting for a typo in a line fux typed for you.
  - **The fact is untouched:** `supersedes:` frontmatter, the `superseded`
    record property, the graph edge, `fux explain`, and the declared tie-break
    that still puts a live document above a retired one at an equal score.
  - `fux doctor`'s `ranking priors` row stops listing it.

### Changed

- 🔴 **BREAKING for npm consumers, and a smaller diff for everyone else: the
  Node reader ships as ONE generated file.**
  ([SR-LAW-10](records/0011_LAW-10-bundled-output.md),
  [SR-NODE-SEARCH](records/0153_node-search.md) decisions 13-16.)
  - **`.fux/node/` is four files instead of 47** — `fux.mjs` (generated),
    `package.json`, `mcp-tools.json`, `README.md`. It was fux's own `.mjs`
    module tree, committed into your repository, editable in place with nothing
    able to detect that it had been.
  - ⚠ **`fux setup` now DELETES the old tree** when it upgrades you. If you had
    edited anything under `.fux/node/src/`, that edit is gone — which is the
    point: a hand-edited ranker in a consumer's repo is a silent fork of the
    engine.
  - ⚠ **npm: `exports` is `./fux.mjs`** and the tarball no longer carries
    `src/`. `import { open } from 'fux-engine'` is unchanged; a **deep import**
    like `fux-engine/src/query/rank.mjs` was never supported and now cannot
    resolve.
  - **In a monorepo, `fux setup` detects the workspace and wires `.fux/node`
    into it** — one line added to your root `package.json` or
    `pnpm-workspace.yaml`, format-preserving, never twice, and it tells you
    which file it edited and which `install` to run. npm, pnpm, yarn 1, bun and
    Yarn Berry with `nodeLinker: node-modules` get this shape; Berry under PnP
    gets the offline bundle, because PnP has no `node_modules` for the shim to
    resolve from. `fux setup` says which it chose and why.
  - **`.fux/fux` is the command to use** — it resolves the reader in three
    rungs, because npm and Yarn hoist the `fux` binary to the workspace root and
    pnpm and bun do not. Do not hard-code `node .fux/node/fux.mjs` in a script.
  - **No build step on your machine.** The bundle is built when fux publishes
    and ships inside both the PyPI wheel and the npm tarball, from one build.
  - `fux doctor`'s `node reader` row now reports the shape, a stale `src/` tree,
    and a workspace manifest with nothing installed behind it.

- 🔴 **An unknown key in `fux.toml` is now REFUSED, not ignored**
  ([SR-CONFIG](records/0113_config.md) decision 14, W-122; the defect was
  W-140 row 8). A misspelled key used to parse and do nothing, so your setting
  was inert with nothing said. The error names the key and lists what is legal
  at that level. **This can break an existing `fux.toml`** that carries a key
  fux never read — which is the point: it was not in force either way.
  - `.fux/tune.toml` has behaved this way since it existed; `fux.toml` now matches.
- **`fux setup`'s `fux.toml` comments are pointers, not explanations.** Every
  key's meaning and default lives in SR-CONFIG; a comment describing a key can
  drift from the record while both look correct
  ([SR-LAW-0](records/0002_LAW-0-authority.md) decision 4). Your existing
  `fux.toml` is untouched — `setup` never rewrites a file that is there.


- **Codex and Copilot skills now install to `.agents/skills/`** — one shared
  folder, instead of `.codex/skills/` and `.github/skills/`
  ([SR-AGENT-POLICY](records/0132_agent-policy.md) decision 16, W-141).
  Codex's docs list `.agents/skills` as its only repository skill folder, so
  the old Codex copies may never have loaded. Copilot reads the same folder.
  - ⚠ **Already set up? Delete `.codex/skills/` and `.github/skills/` yourself**,
    then re-run `fux setup`. It never deletes files, so otherwise Copilot sees
    the old copies next to the new ones.

### Removed

- **`src/fux/config.schema.json`** — every field in it was a `doc:` string
  describing a `fux.toml` key, and nothing loaded or checked it, which is how it
  came to advertise a `[sources] types_file` key that did not exist
  ([SR-CONFIG](records/0113_config.md) decision 15). The five remaining
  schemas are all loaded at runtime or held equal to the code by a test.

### Added

- 🔴 **A second reader: `fux` in Node, with no Python and no dependencies**
  ([SR-NODE-SEARCH](records/0153_node-search.md)). `fux setup` vendors it
  into **`.fux/node/`** and writes a `.fux/fux` shim beside it, so a clone
  answers with nothing installed:

  ```console
  $ node .fux/node/fux.mjs find rollback
  $ .fux/fux find rollback
  $ npx fux-engine find rollback
  ```

  - **It only reads.** `ingest`, `build`, `add`, `remove`, `update`, `enrich`,
    `setup`, `doctor`, `hooks` and `daemon` are absent, and typing one prints
    the specific correction rather than `unknown command`.
  - **`--version` names the runtime** — `fux 2.0.0-alpha.7 (node 22.9.0)` —
    because Python fux installs a `fux` too and a bug report must say which
    one answered.
  - **No `dependencies` key at all and no build step**: a build step is a
    dependency (L1).
  - ⚠ **`.fux/node/` is committed and OVERWRITTEN on a version difference**,
    not write-if-missing — the fourth `.fux/` shape
    ([SR-DOTFUX](records/0102_fux-directory.md) decision 6a). Nobody edits a
    vendored reader, and a stale one against a bumped `_format` is a wrong
    answer rather than an old preference. `fux doctor` gains a `node reader`
    row that reports the drift.
  - ⚠ **It refuses without `.fux/pii.toml`, exactly as Python does.** A reader
    that answered where the CLI refuses would be a divergence in the product.
  - **Not on npm yet**, and no global `fux` bin in the first release.

- 🔴 **`from fux import open` — fux is importable, not only spawnable**
  ([SR-API](records/0154_api.md)).

  ```python
  from fux import open as fux_open

  ix = fux_open(".")
  ix.find("rollback", top=5)
  ix.ask("how do we roll back a release")
  ix.answer("what is the RTO")
  ```

  Same method names and return shapes as the Node reader, and every result's
  `as_dict()` is the `--json` payload — `query/output.schema.json` is now the
  contract for **three** surfaces rather than one. `.fux/README.md`'s *"the CLI
  is the contract; the modules are not"* is retired: **the CLI and `fux.api`
  are the contract**, and nothing that writes is in it.

- **Operating guides for every `fux` job, on Claude, Codex, Copilot and Kiro**
  ([SR-AGENT-POLICY](records/0132_agent-policy.md) decision 15). `fux setup`
  now writes **ten more skills** — `fux-search`, `fux-answer`, `fux-graph`,
  `fux-index`, `fux-maintain`, `fux-mcp`, `fux-sources`, `fux-config`,
  `fux-fetcher`, `fux-pii` — to all four skill surfaces, and `fux-usage` gains a
  *which skill next* router.
  - **Scoped pointers, three vendors:** short rules that load when an agent edits
    fux's own files (`.fux/sources/`, `.fux/decoders/`, `.fux/enrich/`,
    `.fux/fetchers/`, `.fux/pii.toml`, `fux.toml` and tune/output, `.fux/index/`)
    — Kiro `fileMatch` steering, Claude `.claude/rules/`, Copilot path-specific
    `instructions/`. Plus five Kiro `inclusion: auto` guides for the read-only jobs. Each is ≤ 1.2 KB,
    names its skill, and never carries a procedure.
  - 🔴 **On a Kiro CLI without inclusion-mode support, all twelve Kiro
    pointers load on every request** (~10 KB). Bounded by a test and announced;
    `[agents] install` without `kiro` opts out.
  - ⚠ **Existing repos get none of this automatically** — `fux setup` is
    write-if-missing, so re-run it to add the new files; your edited copies stay.

- **`update = auto|never` on a URL line** (W-113,
  [SR-URL-LIST](records/0116_url-list.md) decision 14). A line could say how
  to reach a document and how long a citation could go unchecked, and could not
  say whether to go back for it at all. `update=never` pins the document:
  `fux update` opens no socket for it and **does not even import your fetcher**
  on its account. Resolved through the same three layers as `keep`/`ttl`/`enrich`
  — built-in default, `[sources.url] update`, then the line — so a whole wiki
  pins in one line and a single page can exempt itself. `fux add <URL>
  --no-update` writes it; ⚠ that add still fetches **once**, which is what makes
  the line ingestable. Default `auto`: **a corpus that declares nothing is
  byte-identical to before.**
  - 🔴 **It buys bandwidth by giving up freshness, and it is NOT the ETag
    saving.** CDP intercepts at the response stage, so the body has already
    crossed the wire ([SR-CDP-FETCHER](records/0118_cdp-fetcher.md) decision
    12, now carrying the veto that re-costs request-stage interception).
  - ⚠ **`update=never` + `keep=false` is legal and lossy** — nothing retained
    and nothing fetched, so the document is frozen with nothing to verify a
    citation against. `fux doctor` counts the pinned lines and names those ones.
  - 🔴 **A pinned URL can never be re-redacted, `--full` included**
    ([SR-PII](records/0148_pii.md)). Its record is carried forward verbatim,
    so a new `.fux/pii.toml` rule cannot reach it. Documented, not fixed.
- **`fux doctor` gains `fux.toml loads`.** A config the loader refuses used to
  produce a **green doctor beside an exit-1 ingest** — every config-dependent
  check degraded to `skipped (no readable fux.toml)` at warn level, each
  correctly, and collectively they deleted the finding. The new row is an
  **error** and prints the loader's own message verbatim
  ([SR-DOCTOR](records/0152_doctor.md) decision 4).
- **`fux-decoder` and `fux-usage` now install for Copilot** (`.github/skills/` — now `.agents/skills/`, see *Changed*),
  so all three committed-write skills reach all four vendors (W-118,
  [SR-AGENT-POLICY](records/0132_agent-policy.md) decision 14a).

### Fixed

- **`fux.open()` was 20× slower than it needed to be.** Its PII gate did
  `from fux.ingest import pii`, which pulls in every decoder — **50.2 ms on a
  warm open, against 2.6 ms** once the gate became a stat with the import only
  on the path where it is about to raise. `fux.cli` has spelled the path inline
  for this reason since the gate shipped; `tests/test_api.py` now asserts on
  `sys.modules` rather than on a clock, and `tests/test_cli.py` holds all three
  copies of the path equal.
- **The MCP tool schema Node advertised contradicted itself.** `fux_search`'s
  `k` property is declared `"type": "integer"` and Node emitted
  `"default": "5"` — a string — because the `{{TOP}}` placeholder was
  substituted into serialized JSON without regard for the quotes around it.
  Python emitted `5`. Found by writing the equality check that now holds the
  two halves together ([SR-MCP](records/0136_mcp.md) decision 11).

- **`fux update --check --json`.** The verb whose purpose is being read by
  something else had no machine-readable output, and it exits 0 whether or not
  anything drifted — so the only way to act on the answer was to parse a table
  meant for a person. It emits `{drifted, fresh, unchecked_urls}` and still
  exits 0; gate CI on `drifted` being empty, never on the status
  ([SR-CLI](records/0101_cli-surface.md)).

- 🔴 **`fux verify --rerun` fetched.** SR-PROVENANCE decision 14 is a ruling
  that `fux verify` never goes to the network — one receipt must not verify
  differently on a laptop with a VPN and in CI. `--rerun` called the refer
  plane, which fetches every citation. It re-ranks from the committed index
  alone now, and a receipt from a `source: refer` answer reports
  `unverifiable` rather than being compared against bytes fetched on the spot;
  its fetched-byte verdicts were already recorded in the receipt. **An index
  receipt could also report `reproduced` against a different document** — its
  subject carries no digest, and two empty shas compared equal; citations
  compare as `(name, sha)` now.

- 🔴 **Every `ttl=` was dead at ask time, and `cached` was unreachable.**
  `fux answer` built its freshness policy with caching off, and a URL line's
  `ttl=` may only narrow the caller's policy, never widen it — so `min(0, …)`
  was always `0`. **`fux answer --cache-ttl 15m`** is how to ask; the default
  stays off, so nobody who did not ask can be served a cached byte
  ([SR-URL-FRESHNESS](records/0147_url-freshness.md)).

- **The background re-index rebuilds the accelerator.** Every CLI verb builds
  it where the shards are written, so `ask --fast` never pays for one; the
  detached runner skipped it, leaving the derived plane stale after every
  background pass. Best-effort and recorded in the run status — a disposable
  plane must not fail a correct re-index
  ([SR-MAINTENANCE](records/0129_hooks.md)).

- 🔴 **The answer-time fetch timeout bounded nothing.** `timeout_seconds` was
  validated, stamped into every answer bundle and printed by `--audit`, and no
  code read it — so a consumer fetcher that blocked forever hung `fux answer`
  behind a number that read as a guarantee. The fetch now runs in a worker and
  the query stops waiting at the deadline, degrading exactly as a failed fetch
  does ([SR-REFER](records/0127_refer-plane.md)).

- 🔴 **`fux add <URL>` wrote the engine's defaults over your `[sources.url]`.**
  Each generated line states every attribute, and the values came from the
  built-in defaults — so a repo configured with `ttl = "7d"`, `meta = "plain"`
  or a `cdp` fetcher got `ttl=24h meta=hashed fetch=http` written onto every
  line `fux add` produced. The line now states the resolved value: built-in,
  then `[sources.url]`, then an explicit flag
  ([SR-URL-LIST](records/0116_url-list.md)). Existing lines are unchanged —
  a line that already states an attribute has already spoken.

- 🔴 **The starter refusal rules refused real wiki pages.**
  `requested_suffix_not` means *this URL asked for a web page* and listed only
  `.html`/`.htm` — so `document-request-returned-a-web-page`, the file's
  highest-value rule, refused every `viewpage.action`, `Page.aspx`,
  `index.php` and `.jsp` document a corpus had. Both suffix rules now carry the
  server-page extensions ([SR-REFUSAL](records/0146_refusals.md)). The
  starter also promised that a short page "warns instead of indexing silently";
  **there is no warn level** and never was — every rule refuses, and the
  comment says so now. **Existing repos keep their `refusals.toml`**: add the
  suffixes by hand.

- **Four things `fux setup` shipped that were not true.** `.fux/.gitignore`
  carries `__pycache__/`, so the bytecode beside a consumer's committed decoder
  and fetcher stops showing as untracked. A re-run no longer re-prints the whole
  `AGENTS.md` snippet at the file fux itself wrote. The starter
  `.fux/sources/urls` header is generated from the list spec — it said *two
  attributes* while there were seven, and promised `fux update` re-fetches every
  line, which narrow-by-default ended. The starter `pii.toml` and `doctor` stop
  pointing at `tools/pii-probe/probe.py`, which ships in the repository and not
  in the wheel; both name the `fux-pii` skill, which carries the script.
  **Existing repos keep their files** — setup is write-if-missing.

- 🔴 **`fux hooks` installed nothing in a repo with `[cli.json] enabled = true`.**
  It read the resolved `--json` to choose between installing and reporting, and
  the output config fills that field — so the command whose job is to wire the
  hooks printed a true status report of an unwired repo instead. `--status`
  selects the mode now; `--json` only selects the rendering, and an explicit
  `fux hooks --json` still reports ([SR-MAINTENANCE](records/0129_hooks.md)).

- **A shard with merge conflict markers says so.** It reported *not a fux index
  shard, or the file is truncated* — corruption-shaped words for an unresolved
  merge — and the merge driver's own refusal told you to run `fux ingest`,
  which cannot read that file. Both now name the two commands that work:
  `git checkout --ours` (either side; a shard is derived), then `fux ingest`.

- **`fux path` refuses an end that is not in the index**, naming which
  (`… is not in the index (FROM)`, exit 1). It printed `No route from … within
  N hop(s)` and exited 0 — the same answer as for two real, unconnected
  documents, so a typo read as a finding. `fux explain` now refuses an unknown
  `tag:` too; neither verb checked tags at all
  ([SR-GRAPH](records/0126_graph.md)). An empty `paths` still exits 0 and
  still means what it says.

- **`fux doctor` gains a `tune.toml loads` row.** A tune file that did not parse
  left every row green — `fux ingest` reads only `[index]` from it, so the index
  stayed clean while `ask`, `find`, `answer`, `graph` and `path` all refused.
  The row quotes the loader's own refusal and fails as an **error**
  ([SR-DOCTOR](records/0152_doctor.md) decision 10).

- **`fux add <URL> --no-update` now fetches once**, as `--help` and the record
  always said. It wrote the line, fetched nothing and exited 1 — the pin filter
  ran above the fetch and did not know an add was in progress. Every run after
  the add is still pinned ([SR-URL-LIST](records/0116_url-list.md) decision
  14). ⚠ A pinned line written **by hand** into `.fux/sources/urls` is still
  never fetched and so has no record.

- **`fux update --failed` now narrows the fetch.** The flag was parsed and never
  read: it fell through to the ordinary narrow pass and fetched the *stale* set
  instead. It selects the URLs whose last run failed (`fail_streak > 0`) and
  wins over `--all`.

- 🔴 **A frontmatter `title:` was committed unredacted.** Only a document's body
  was redacted, and `title:` wins over every heading — so a document whose body
  read `[PII:email]` could carry the address in its committed title, and in the
  title field's terms on every record. The title is redacted in the same pass as
  the body now; **re-ingest to clean an index built before this**
  ([SR-PII](records/0148_pii.md) decision 19a).

- ⚠ **A document's PATH is never redacted, and ingest now says so.** `loc` is
  the address `fux answer` fetches with and `id` is the key the index is sorted
  on, so a redacted path addresses nothing. A run whose rules match a path
  prints a note naming those documents; renaming the file or ignoring it is the
  consumer's call ([SR-PII](records/0148_pii.md) decision 19b).

- 🔴 **No URL citation was ever verified live.** The refer plane's fetch step
  still required a fetcher to return a `str`, while the fetcher contract has
  returned `(bytes, content type)` since 2026-08-26. Every `url:` citation
  raised `fetcher returned tuple, expected str` internally and fell back to
  `as-ingested` or `unverified` — **never `current` or `stale`** — so the
  freshness feature reported itself as working with its network half never
  running. `fux answer` and `fux verify` now fetch and decode a URL through the
  same `_unpack` + `_decode_fetched` + `sanitize` pipeline ingest used, so the
  two shas are comparable; a response whose type no decoder claims is
  `unverified` with the decoder's own reason, and a pre-2026-08-26 fetcher that
  returns prose still verifies
  ([SR-URL-FRESHNESS](records/0147_url-freshness.md) decision 6a).

- 🔴 **`.jsonl` and `.json` documents lost their title.** Since 2026-09-06 a
  record-oriented decoder emitted `## Record 1` / `## Item 1` as its **first**
  heading and no document title, so `extract.py`'s shallowest-heading rule made
  *every* such document titled `Record 1` — in a heavily-weighted field.
  Measured over this repo: **96 documents** (86 `.jsonl`, 10 `.json`) lost a real
  title and **not one gained anything**
  ([the run](work/regression/2026-09-11-w116-chunking/report.md),
  [SR-DECODE](records/0139_decode.md) decision 11a). Both decoders now emit a
  `# <filename>` title with the records as siblings beneath it — which is what
  `DECODER-SKILL.md` told decoder authors to do all along.
  - ⚠ **Run `fux ingest --full` to pick this up.** Reuse is keyed on a
    document's content sha and a decoder change moves no bytes, so a plain
    `fux ingest` carries the old records forward.
- **The shipped `fux-decoder` skill was missing its chunking section.** Fux's own
  committed rendering had gained it and the **template had not**, so every
  `fux setup` since shipped a decoder guide with no explanation of how a
  decoder's headings become citable passages. `.github/agents/fux.agent.md` had
  drifted the other way, losing the command-resolution ladder. Both repaired, and
  a test now asserts every committed agent file still equals the template that
  ships ([SR-AGENT-POLICY](records/0132_agent-policy.md) decision 14b).

### Changed

- ⚠ **BREAKING — the types list is `.fux/formats.toml`** (W-130,
  [SR-TYPES](records/0128_types-list.md) decision 12). It was
  `.fux/sources/types`, a line-grammar file. The new file has two keys:
  `include` (globs that are already text) and `[decoders]` (`ext = "module"`,
  and a bound extension is a document). **Nothing in it subtracts** — `!`
  exclusions live in `.fux/.fuxignore`. A path-scoped binding and a repeated
  binding can no longer be written at all. **Upgrading:** a repo with the old
  file stops at `ingest`, `ask`, `doctor` and every `fux add/remove --types`
  with an error naming the fix — run `fux setup`, which writes
  `.fux/formats.toml` from the old file (moving its `!` lines to `.fuxignore`),
  then delete `.fux/sources/types`. Verified on this repo: the converted file
  re-ingests to a **byte-identical** index and `.fuxignore`.
- `[sources] types_file` in `fux.toml` is now refused by name.
  `config.schema.json` advertised it; nothing ever read it
  ([SR-CONFIG](records/0113_config.md)).

- ⚠ **BREAKING — `.fux/pii.toml` is required** (W-129,
  [SR-PII](records/0148_pii.md) decision 17). `fux setup` now writes the
  starter, and **every command except `setup`, `tune` and `output` stops with an
  error in a repo without it**; `fux doctor` runs and reports it as a failing
  row. A file with every rule commented out is legal and redacts nothing.
  **Upgrading:** run `fux setup` once per repo. That turns the starter's enabled
  rules on (email, JWT, AWS key, GitHub token, bearer token, PAN, US SSN, ITIN,
  Medicare MBI, Canadian SIN), and the next ingest re-extracts in full.

- **The PII starter covers US and Canadian identifiers** (W-131,
  [SR-PII](records/0148_pii.md) decision 12a). **On:** US SSN and ITIN/ATIN
  in their written shape, excluding numbers the SSA and IRS never issue; the
  Medicare MBI; the Canadian SIN with a Luhn check. **Off, commented with what
  each over-matches:** US EIN, Canadian postal code, NANP phone numbers.
  ⚠ Unseparated nine-digit SSNs and SINs are deliberately not caught. A repo
  that already has `.fux/pii.toml` keeps its file — copy the new sections in
  by hand if you want them.

- **`phrases` keeps up to 32 headings, and the cap is `.fux/tune.toml [index]
  max_phrases`** (Arpit, 2026-09-11). It was a hard-coded 12: on fux's own
  corpus 87 of 563 markdown documents lost 1 055 headings, and 262 of the slots
  that survived held template headings (`Context`, `Decision`). At 32, 98.2 %
  keep every heading for ~0.3 % more index. **Display only** — ranking already
  read every heading. [SR-EXTRACTED](records/0115_extracted-mode.md) decision 9.
- ⚠ **BREAKING: `fux.toml [decode]` is refused.** `max_table_rows` moved to
  `.fux/tune.toml [index]`, beside `max_phrases`. `[index]` is tune.toml's one
  declared exception to "nothing here changes the index": `fux ingest` reads it,
  `--no-tune` does not undo it, and changing it re-extracts.
  [SR-TUNE](records/0135_tuning.md) decision 13.
- **Fixed: a changed `max_table_rows` never reached an unchanged CSV on a delta
  ingest** (since 2026-09-06), so delta and `--full` disagreed. Ingest now keeps
  a digest of `[index]` in `.fux/runtime/` and re-extracts when it moves —
  recorded only after the index is written, so a stopped run cannot hide it.
  [SR-INGEST](records/0106_ingest.md) decision 15b. **The first ingest after
  upgrading re-extracts every document once.**

### Added

- **`.fux/pii.toml` rules can name a checksum — `validate = "luhn"` or
  `"verhoeff"`** (W-128, [SR-PII](records/0148_pii.md) decision 16). A match
  is redacted only when its digits pass, so a payment-card or Aadhaar rule stops
  eating order ids and timestamps. The set is closed and engine-owned — no
  consumer code runs inside ingest. ⚠ **A checksum is a 1-in-10 filter**, so the
  starter's `aadhaar` and `card` rules gain `validate` and **still ship
  commented out**. `tools/pii-probe/` now prints how many shape matches a
  checksum turned away. **An existing `pii.toml` keeps its digest**: upgrading
  forces no full re-extract.
  🔴 **Fixed on the way, in the starter:** with both rules enabled, `aadhaar`
  (which runs first) could take the first twelve digits of a spaced card number
  — one card in ten passes Verhoeff there. Its pattern now refuses a window
  inside a longer digit group.

- **`tests/test_open_work_is_not_stale.py` — the work queue now checks itself.**
  Five checks over `work/OPEN-WORK.md`'s *Blocked on Arpit* table: an age is
  arithmetic against `filed`; every link resolves; no tombstone sits in the
  inbox; a row's subject id has no `## W-nn` landing record in
  `IMPLEMENTATION.md`; and the header's overdue count matches the table beneath
  it. 🔴 **It catches the mechanical half of staleness and says so in its own
  docstring** — the two rows cleaned the same day were false *in their
  sentences*, with live links and correct ages, and nothing here would have
  caught them. Guessing at claim truth would pass on exactly those. ⚠ **The
  rules it enforces live in `CLAUDE.md` and `OPEN-WORK.md`'s footer and in no
  SR**, so the test is an unowned guard — filed to W-122 Phase 1.

- **SR-RS — a FIFTH way a prediction can end: `VOID`** (Arpit, 2026-09-06),
  for a bar that could not be applied at all. 🔴 **Distinct from
  `INCONCLUSIVE`, and conflating them destroys the finding:** INCONCLUSIVE is
  *the instrument could not discriminate*; VOID is *the measurement was fine
  and the bar was not a bar*. ⚠ It is **not a soft FAIL** — a bar that could
  not be applied did not rule against what it measured, and only the
  adjudication is withdrawn, never the controls. **Only Arpit may void a bar**,
  on the same rule that sends an ambiguous result to him. `tests/test_regression_runs.py`
  accepts the value.

- **SR-QUALITY decision 2a — a bar on `recall@k` names its `k`, or it is
  VOID** (Arpit ruled, 2026-09-06). `recall@k` is a curve, so a bar that omits
  `k` is four bars whose verdicts can disagree, and whoever supplies the
  missing `k` afterwards picks the verdict — a moving threshold wearing an
  omission instead of an edit. Such a bar has **not failed and has not
  passed**. A `k` justified by a ceiling effect must be justified **in the
  pre-registration**, against the clean-arm curve the record publishes.

### Changed

- 🔴 **W-110's gate is VOID, and `fux enrich`'s questions body is now recorded
  as BUILT AND UNPROVEN**
  ([`W110-DOC2QUERY`](work/regression/2026-09-05-doc2query/VERDICT.md)). Its
  bar — *net ≥ 6 on `recall@k`* — never named `k`: the run is **+7 at `k = 1`**
  and **+3 / +2 / +1** at `3 / 5 / 10`, because `recall@10` is already
  `0.9884` with no enrichment at all. **No behaviour changed** — the feature
  stays shipped on SR-ENRICH decision 15's own argument (prose measured
  `+1 / −1`; a question is a checkable object) — but the record no longer
  reads as *measured and passing*. ✅ **The placebo control is not voided with
  it**: 0 discordant queries at every `k`, so the gain is the content of the
  questions rather than more bytes or more files, and **no query regressed in
  any arm**. ⚠ The doc2query−− filter is **unproven, not disproven** — 2 of 98
  questions, a 2 % treatment.

- **SR-RANKING decision 8a — `round(score, 9)` is the cross-runtime contract
  for the score; the ORDER stays byte-equal** (Arpit ruled, 2026-09-06).
  Two runtimes reading one committed index agree on `round(score, 9)`, not
  necessarily on the score's last bit: `log` is the one transcendental in
  `score_record`, and two IEEE-conforming libms disagree by one ulp on ~7 % of
  the arguments fux can hand it. Measured on **darwin/arm64 and glibc 2.39 /
  x86-64**, with `idf`'s argument domain **enumerated rather than sampled** —
  all 10 939 arguments `df = 1..n` at `n ∈ {101, 838, 10 000}`, of which
  **841 (7.69 %) differ bit-for-bit and 0 differ at `round(9)`**
  ([the run](work/regression/2026-09-05-node-log-divergence/ADDENDUM-GLIBC.md)).
  **Nine places is not a tolerance invented to pass a test** — it is the
  resolution `rank.py`'s sort key already uses, seven orders of magnitude above
  the largest divergence measured. ⚠ **Nothing about the ORDER is licensed**: a
  discordant top-5 is a defect under this decision. No Python behaviour
  changed, no golden was re-derived, and no portable `log` was added.
  `work/benchmark/PRE-REGISTRATION-NODE.md` is now **frozen in full**
  (sha `0e3b4c8`), which unblocks **W-107 Phase 1**.

- 🔴 **L0 — SRs are the only source of truth, and the Law records outrank
  every other record** (Arpit, 2026-09-06).
  [SR-LAW-0](records/0002_LAW-0-authority.md). Two clauses: a rule is
  **stated in exactly one SR** and every other artifact links to it, never
  restates it; and the Law records `SR-LAW-0`…`SR-LAW-8` outrank every other
  SR, so **a record conflicting with a Law is void in the conflicting part**.
  **A Law changes only on Arpit's ruling, named in the record.**
  The record carries the test that makes the first clause followable —
  *describes* is forbidden, *implements* and *enforces* are not — and states
  plainly that precedence is **judgment, never a gate**.
  ⚠ **Supersedes [SR-LAWS](records/0001_LAWS.md) decision 1** (*"CLAUDE.md is
  the single normative home"*), accepted the same day. `CLAUDE.md` becomes a
  pointer; its process sections stay, because no record governs how an agent
  behaves in a session. Migration: **W-122**.
- **The nine law records are named `SR-LAW-n` and filed as `*_LAW-n-*.md`**
  (`0002_l1-zero-cost.md` → `0003_LAW-1-zero-cost.md`, and its seven
  siblings). Every citation swept across 13 files. **The prefix is the
  grouping key**, so `records/*_LAW-*.md` finds all nine wherever they sit —
  and **L0 sits at `0002`, first, because the law about laws precedes the laws** —
  `CLAUDE.md` has called this *"Law zero"* since August, so the number inherits a
  name the repo already used. Every record from the old `0002` to `0061` shifted
  down one and its frontmatter `(NNNN)` with it; **L1–L8 keep their identities**,
  which is what made a 62-file renumber safe where a law renumber would not have been. **The index they hang from is `0001_LAWS.md`**, in
  caps to match — 70 files repointed, including link-only repoints inside past
  `WORKLOG.md` entries, which is the repo-wide-mechanical-rename exception to
  the append-only rule and is said out loud here for that reason. **Two
  sentences in old entries that describe what a file was *called at the time*
  were restored** rather than rewritten: a link may be repointed, a statement
  about the past may not.

- **`fux doctor` gained four checks and one line — W-101, one pass at
  `doctor.py`.** Each closes something that was reachable only from inside a
  run that had already finished, or from nowhere at all:
  - 🔴 **`freshness verdicts` — the `as-ingested` share.** This is the **veto
    check of two accepted records** ([SR-ACQUIRED](records/0145_acquired-plane.md),
    [SR-URL-FRESHNESS](records/0147_url-freshness.md)); both say to run it
    with `fux doctor --json`, and until now neither veto could be run at all.
    The machine-readable form is the new `freshness` block.
    ⚠ **Over journalled answers only** — a verdict exists at answer time and
    only the opt-in receipt journal (`--journal`) persists one, so a repo that
    has never journalled reports **unknown**, never a zero share.
  - **`refusal rules`** — how many rules load, how many responses each has
    refused (cumulative, recorded by every networked run), and **the rules that
    have never fired**, which is what a typo'd condition looks like. The loud
    case is refusals recorded with **no `url:` document surviving**: a rule that
    matches everything empties the URL half of the corpus and leaves it looking
    like a corpus nobody has ingested.
  - **`decoder bindings`** — every `decoder=` binding resolves, plus the one
    fault no ingest can catch: a binding on an extension **no indexed document
    has**. Extending a decoder to a new extension is legal by design, so
    nothing errors and a typo indexes nothing forever.
  - 🔴 **`recency prior`** — whether any document carries an `mtime`. **A corpus
    copied out of its git repository loses every one of them**, so the whole
    recency prior switches off and nothing reported it; found 2026-09-05 on
    `fux-benchmark`'s 10 000-document corpus, where all 10 000 have none.
  - **Redaction counts on `pii rules`.** `redact()` returned per-rule hit
    counts from day one and `run()` summed them into a variable nothing ever
    read. Every ingest now records them
    ([SR-PII](records/0148_pii.md) decision 15), and `doctor` reports them
    with their denominator.
  - **Absent is never reported as zero.** *"No ingest has recorded counts"*,
    *"no networked run has recorded a refusal"* and *"no receipts journalled"*
    are each said in those words rather than shown as a `0` a reader would take
    for a finding.
  - ⚠ **A check that fires on a healthy repo is one people learn to skip.**
    `fux setup` writes the entire built-in binding table, so on a markdown
    corpus 27 of 36 bindings match no document — all correct. Only a binding
    that differs from the built-in default for its extension is reported.

- **The tie-break is DECLARED, and ties are marked** (W-111). Where two
  documents' rounded scores are equal the order is now
  `superseded -> recency -> priority -> id` — Arpit's ratified order — instead
  of a document's name alone. `ask`/`find --json` carry `tie: true|false` on
  every row and text `ask` prints `(tie)` after the score.
  - 🔴 **This turns no ranking prior on.** Every signal is already a
    `Weighting` multiplier shipping as a no-op; the key reads the same *facts*
    and reads them **only among equals**. No score moves and no document passes
    one that outscores it. `superseded_weight` stays Arpit's open call.
  - **`tie` is computed before truncation**, so the last row of a `--top 5` is
    marked even when the document it ties with is off the page — that row is
    the one most likely to have been a coin-toss.
  - ⚠ **`-priority` in the ratified order is unreachable**, and the code says
    so rather than implying otherwise: `[priority]` has no fact beside its
    weight — `priority_for` *is* the weight — so different priorities already
    produce different scores. The slot is kept and pinned by a test that fails
    if that ever changes.
  - ⚠ **Measured effect on the corpora available here: zero.** 0 of 2 450
    top-5 rows tie on the playground, 3 of 1 200 at 10 000 documents, and **no
    query's order differs from the old key** — because neither corpus carries
    the signals where a tie lands
    ([the run](work/regression/2026-09-05-declared-ties/report.md)).

- **`find --phrase "…"`, `find --under <prefix>`, `find --all`** — precision
  controls for a pipe. Each **removes** results the ranking already produced
  and retrieves nothing; raising `--top` is what widens the pool.
  - `--phrase` uses the index's own analyzer, so stopwords are dropped:
    `--phrase "roll back"` matches *"roll the back"*.
  - ⚠ **A `url:` document is kept by `--phrase`, never dropped** — offline
    there is no text to test, and dropping it would report *"this page does not
    contain the phrase"* on the strength of not having looked.
  - ⚠ **`band` describes the UNFILTERED ranking**, and a `[filter]` line on
    **stderr** says so whenever a filter removed anything. stdout stays a bare
    path list.


- **Enrichment is now QUESTIONS, not prose** (W-110). The `fux-enrich` skill
  asks for five to ten questions a searcher would type before they knew the
  document existed — one per line, no summary — because prose was measured at
  **+1 fixed / −1 broken** and the break was context prose carrying currency
  words into a superseded record. doc2query (Nogueira & Lin 2019).
  - **`fux enrich --check` now tests every question against the index** and
    refuses one that does not place its own document in the **top 3**
    (doc2query−−, arXiv 2301.03266). Scored with `title` **and** `ctx` zeroed:
    `title` so echoing the heading cannot pass, `ctx` because enrichment text
    is itself indexed as `ctx` and a question would otherwise retrieve its
    document *through itself* — passing on the second run what it failed on
    the first.
  - **`--check` reports; it never rewrites or deletes.** The filter is
    corpus-dependent: a question that passes today can be refused after an
    unrelated ingest moves the corpus statistics.
  - **Prose bodies written under the old skill stay valid** — the filter checks
    lines ending in `?`, and a body with none has nothing to check.
  - 🔴 **The gate is AMBIGUOUS and was handed to Arpit**, not adjudicated: the
    bar (`net >= 6` on `recall@k`) never fixed `k`, and it is met at
    `recall@1` (**net +7, nothing down**) and not at `@3`/`@5`/`@10`
    ([the run](work/regression/2026-09-05-doc2query/report.md)). The `placebo`
    control moved **nothing at any k**.

- **`superseded_by:` in an enrichment's frontmatter retires its document.** The
  declared path `supersedes:` cannot cover: that key is written by the
  *successor*, and a document retired years ago could not name one that did not
  exist yet. Declared, never inferred — the named successor must exist, never
  itself, and a malformed enrichment retires nothing.

### Fixed

- 🔴 **A newly written enrichment was never indexed on an incremental
  ingest.** Extraction reuse was keyed on the *document's* content sha alone,
  so a `.fux/enrich/` file could be written, pass `fux enrich --check`, be
  committed and reviewed — and its vocabulary never reached `.fux/index/` until
  the document itself changed or `fux ingest --full` ran. **It presented as a
  working feature**, and shipped that way from W-76 Phase 8 until a test
  written for something else caught it.
  - Reuse is now invalidated per document when its enrichment's content sha
    moves, **appears or disappears** — a deletion must remove its vocabulary
    too. An *unchanged* enrichment still forces no re-extraction, so the
    delta-ingest guarantee is intact.
  - ⚠ **Every prior enrichment measurement in this repo ran through this
    defect**, and whether any under-measured enrichment depends on whether its
    harness ingested from clean. Not audited here; filed.


- 🟢 **`--expand "<text>"` on `ask`, `find` and `answer`, and `expand` on the
  MCP `fux_search` tool** (W-109). Fux's remaining failures are **vocabulary
  gaps** — the document does not use the question's words — and no weighting
  reaches a term that is not there. Fux may never call a model (L3); its caller
  usually is one. The caller hands over the words it expects the document to
  use, analyzed by the same analyzer the index was built with and scored at
  `[ranking] expand_weight`.
  - **Measured, blind-authored, 16 fixed / 0 broken** on the 50 goldens —
    28/50 → 44/50, and **6 of the 9 hand-annotated vocabulary-gap failures now
    pass where 0 did before**
    ([the run](work/regression/2026-09-05-expand/report.md)). The expansions
    were written by a separate agent session given the corpus and the
    **stripped** questions only.
  - 🔴 **A document matching only supplied terms is never returned.** Enforced
    in `rank()`, before the score is kept, on both candidate paths — not in the
    printer, which would leave MCP returning them. It is the line between a
    citation and a fabrication.
  - ⚠ **`expand_weight` ships at `0.2`** (Query2doc's 1:5) and **no run has
    graded the value**; the run above measured the feature, not the number.
  - ⚠ **The finding's ceiling, stated:** the blind author read all ten corpus
    documents first. Nothing here says an agent can supply the vocabulary for a
    corpus it has *not* read.

- **`-q/--query` on `ask` and `find`, repeatable** — another phrasing of the
  same question. Each is ranked on its own and the lists are fused by
  **reciprocal rank** (Cormack et al. 2009, `k = 60`), never by score: the
  deleted dense lane fused scores, and a BM25F score and any other quantity are
  on unrelated scales.
  - ⚠ **A fused `score` is an RRF score**, and `--json` carries
    `"fused": true` so a consumer cannot read one as the other.
  - ⚠ **`--band` on a fused search describes the FIRST phrasing.**
    `separation_floor` is calibrated against BM25F; a perfect fused top-2
    differs by `~0.0003`, so scoring separation on reciprocal ranks would
    demote every fused query for the change of units. Stated rather than
    rescaled or dropped.
  - ⚠ **Not graded.** `-q` has unit tests and no measured run.
  - `answer` takes `--expand` and **not** `-q`: one answer to one question.

- **The receipt records `--expand` verbatim and `fux verify --rerun` replays
  it**; `--why` marks every matched term `expanded: true|false`.

### Fixed

- 🔴 **The accelerator's block bound now prices each term at that term's
  weight.** An unweighted ceiling over weighted scores is the W-73 class of
  defect — the accelerator returns a different answer from the scan, silently.
  A second half was found by measurement, not reasoning: **a candidate `rank()`
  will drop may not set `theta`**, or the accelerator skips blocks on the
  strength of a document nobody will be shown. The differential test diverged
  at every `expand_weight >= 0.5` at `top = 20` until both were fixed —
  including at `1.0`, where the weights change no arithmetic at all.

### Changed

- 🔴 **`fux answer` refers the top THREE documents, not one** (W-108). The verb
  still returns one answer; what changed is how many documents it reads to build
  it. `refer()` already looped candidates and `_rescore` already computed passage
  `df` across all of them, so the cross-document passage contest existed and was
  being handed a field of one.
  - **Measured, paired, 43 graded queries: 13 fixed / 0 broken**; mean answer
    recall `0.4341 -> 0.8256`
    ([the run](work/regression/2026-09-05-answer-top3/report.md)).
    **`ask` is byte-identical** — no ranking changed.
  - ⚠ **Answers cost more context**: mean assembled bytes `2 517 -> 6 467`, on
    every one of the 43. `[refer] budget` still bounds the whole rendered answer
    and is never exceeded; set it lower to buy the old cost back.
  - ⚠ **`fux answer --band` demotes 8 of 43 from `grounded` to `weak`.** At one
    result there was no runner-up, so `separation` was `1.0` on every answer
    fux has ever given. It is now computed. **No floor moved and nothing gates
    on the band.**
  - ⚠ **`answer`'s cited document may differ from `ask`'s first result** — on 18
    of the 43. `ask` ranks documents; `answer` ranks passages across `ask`'s top
    three.

- **`fux answer --json`: each entry of `answer.passages` now carries `id`, `loc`
  and `sha`.** Additive — nothing was removed or repurposed, and `citation`
  still names the winning passage's document. In text mode each passage prints
  under **its own** locator line.
  - ⚠ **This fixes a mis-citation that predates the top-3 change.** Every passage
    was printed above a single trailing locator naming the *first* passage's line
    range, whatever the later passages were.

- **`fux verify --rerun` retrieves three candidates too**, or it would report
  `drifted` on every multi-document answer.

### Fixed

- **A multi-document answer resolves each `url:` citation's OWN fetcher.**
  `refer()` takes one fetcher for the whole call; with three candidates behind
  different `.fux/sources/urls` lines, handing all of them the first one's module
  compares a rendered page against a shell and reports a **false staleness on
  every query**. `answer` now passes a URL-keyed dispatcher, connecting each
  module once. A fetcher that fails to load or connect costs **its own**
  documents their citations instead of taking the query down.


## [2.0.0-alpha.7] - 2026-09-02

**A Windows-only fix, caught by a Windows runner and by nothing else.**

### Fixed

- **`fux enrich --plan`/`--check` named the same file two different ways in one
  run on Windows.** The worklist built `.fux/enrich/<sha>.md` from a literal;
  the `malformed:` and `refused:` lines came from `str(Path)`, which is `\` on
  Windows. A consumer grepping their own log for a path found half of it.
  Every path in the report now uses the worklist's spelling.
  - ⚠ **No reviewer on Linux or macOS could have seen this** — `str(Path)` and
    `as_posix()` are the same string there. The `malformed:` half predates
    `2.0.0-alpha.6`; the `refused:` line, added in it, is what put two
    spellings in one report and made the mismatch visible.
  - Display only: nothing opens a file by that string, and no index byte moves.

## [2.0.0-alpha.6] - 2026-09-02

**Enrichment prose is inside the PII boundary, `fux enrich` takes one target,
and the cdp fetcher survives concurrency.** Four items written on 2026-09-01 in
a session whose shell never came up, verified here against a real one — two of
them against measured runs, because CI structurally cannot see either failure.

### Fixed

- 🔴 **A PII value in an *enrichment body* became a committed index term.**
  Redaction walked parsed document bodies; `_enrichment_for()` read
  `.fux/enrich/` further down and handed its text to extraction as `ctx`, so an
  address in enrichment prose was searchable on a document whose own body had
  just been redacted, with **no surface saying why**. Enrichment now gets its
  own pass. Reproduced through the real CLI in two arms before it was called
  fixed — [`2026-09-02-enrich-pii-leak`](work/regression/2026-09-02-enrich-pii-leak/report.md):
  `fux find` returned the document before and does not after, and a control
  proves enrichment vocabulary still ranks.
  - ⚠ **The sha is untouched.** Enrichment is keyed by the source document's
    content sha, which is also the file's name; re-shaing over redacted text
    would report every enriched document `stale` against its own unchanged
    source.
  - **The frontmatter is deliberately outside the pass** — it is stripped
    before indexing already, so a `model:` value never reaches a committed term.

- 🔴 **`cdp.py` shared protocol state and one browser tab across threads.** The
  file said the constraint was one WebSocket every `fetch()` reuses; that had
  not been true for some time. What was actually shared was the message-id
  counter, both message queues (**cleared at the top of every fetch**, so one
  thread wiped another's in-flight state) and the page target — which returned
  the **first** page, so two threads navigated one tab.
  - `_Conn` owns the socket, the counter and both queues per fetch; each worker
    opens and keeps **its own tab**; the launch is guarded by a lock; `close()`
    closes exactly the tabs this module opened and no others.
  - Measured against real Chrome —
    [`2026-09-02-cdp-parallel`](work/regression/2026-09-02-cdp-parallel/report.md):
    pre-fix, **seven 200-OK responses filed under the wrong URL** across
    parallel 2/4/6, plus cross-attributed ETags; after, 12/12 on both fetch and
    `validate()` at parallel 1, 2, 4 and 6, with no tab leaked in eight runs.
  - ⚠ **Behaviour change: fux no longer drives a tab you had open.** It opens
    its own — same Chrome, same profile, so a signed-in session is unaffected.
  - **`MAX_PARALLEL` still ships at `1`.** Both arms pass there, so the shipped
    number was never itself unsafe; the defect was the explanation beside it.

- **Two docstrings named `runner.lock`, a file renamed to `write.lock` on
  2026-08-26.** The code was correct throughout; the two files that *explain*
  the mechanism named something that does not exist. Found by a record that
  pastes a real `grep` of `src/` into itself rather than describing the check.

### Added

- **`fux enrich [TARGET]`** — an optional positional on `--plan` and `--check`
  that reports on **one** document or URL. Matching is **exact**: a selector
  that silently matches two documents is how a one-document request becomes a
  bulk run.
  - 🔴 **It filters; it never widens.** A document no `enrich=true` line
    reaches stays unenrichable, and naming it here does not change that.
  - Coverage arithmetic keeps the scope's denominator, so a single-target run
    cannot read as a scope being complete.
  - *not declared* and *not indexed* are **different messages**, because the
    fixes are different.

- **`fux enrich --check` refuses an enrichment body carrying PII**, names the
  rules that fired, and exits `1`. 🔴 **It reports; it never repairs** — the
  file is prose a human reviews in a diff, and a silent rewrite makes that diff
  lie. The message says to rewrite the sentence, **not** to add a `pii.toml`
  rule: a redacted enrichment body indexes `[PII:email]` as vocabulary.

- **`[sources.url.config] fetcher_max_parallel`** — the fetcher's safety
  ceiling, settable without forking a shipped file. **Both** shipped fetchers
  accept that one spelling, because the config table reaches every fetcher
  verbatim and a prefixed name would break any repo loading the other one.
  Distinct from `[sources.url] max_parallel`, which is politeness. Below `1` is
  **refused, not clamped**.

### Changed

- **The `fux-enrich` skill runs `--plan` itself** rather than telling a human
  to, enriches **one** named document when one is named, and **stops to ask**
  when a plan returns several. It re-runs `--plan <target>` immediately before
  writing each file, so the window between planning and writing is closed with
  no new field and no second digest.

- **[SR-LOCKS](records/0140_locks.md) is accepted**, and its veto captures are
  a 2026-09-02 re-run rather than a five-day-old one. All three checks: not
  fired.

### Upgrade note

⚠ **A repo with both enrichment and a firing `.fux/pii.toml` rule re-ingests
once on upgrade.** `.fux/runtime/pii-digest` does not cover this: the digest
fires when the **ruleset** moves, and here the ruleset did not move — its
**reach** did. One full pass, then it settles.

## [2.0.0-alpha.5] - 2026-09-01

**A URL behind a login is now ingestible, checkable offline, and redactable.**
Four phases of W-98 plus the PII plane; the `.fux/` directory gains three
committed files and one gitignored plane.

### Added

- **`.fux/acquired/` — the retained bytes a citation can be checked against**
  (SR-ACQUIRED). Ingest used to decode a fetched URL, keep the markdown and
  drop the bytes, so a `url:` record could only ever be verified by a *fresh
  fetch* — which needs the network, the session, and the source still existing.
  - **A third `.fux/` category**, beside committed and derived: gitignored like
    `runtime/` and **not rebuildable**, because a blob can only be
    re-*acquired*.
  - **`keep=` on a URL line, defaulting to `true`**, resolved through the same
    three layers as `meta` — built-in default, `[sources.url] keep`, the line.
    `fux add --no-keep` or `keep=false` opts out.
  - **Bounded by `[sources.url] acquired_max_bytes` (default 2 GiB)**, evicted
    by run counter — **never by `mtime`**, which would be a clock. ⚠ **A blob
    whose URL last failed is never evicted**: that is precisely the copy that
    cannot be re-acquired.
  - `fux doctor` reports blob count, total bytes and an 80%-of-cap warning;
    `fux remove <url>` drops the manifest entry and sweeps the blob.

- **`.fux/refusals.toml` — declarative refusal detection that fails closed**
  (SR-REFUSAL). A SharePoint share link returns a **sign-in page with HTTP
  200** that decodes perfectly well and lands a login page in the committed
  index. Six shipped rules, ORed in file order, first match wins; the check
  runs **after `_unpack` and before both retention and decode**, so a refusal
  is never stored and never indexed.
  - **A missing file is legitimate**; a malformed one **refuses to run**, once,
    before the first socket opens.
  - ⚠ **Conditions are pure over the bytes.** `status`, `final_url_host` and
    `final_url_contains` were specified and **cut**: they would have put HTTP
    facts inside the engine, which SR-FETCHER decision 13 forbids. Provider
    detection survives as `body_contains` over **form-field names**
    (`name="loginfmt"`, `name="SAMLRequest"`) — an API between a page and its
    own backend, which outlives the redesigns that rewrite every visible string.

- **`ttl=` on a URL line, and a sixth freshness verdict `as-ingested`**
  (SR-URL-FRESHNESS). When the source cannot be reached but the passage still
  matches the retained bytes the record was built from, that is a **real
  comparison** — no longer reported as `unverified`, which is
  indistinguishable from never having looked.
  - **`min(policy, declared)`:** a line may **narrow** the caller's policy and
    can never widen it, so `ttl`'s `24h` default cannot switch caching on for a
    caller who never opted in. `ttl=0` means *always go out for this one*.
  - ⚠ **Consumers switching on the freshness string must handle six values.**
    `output.schema.json` declares the wider enum on `verified`, on a citation's
    `freshness`, and per document in the provenance key. `ask` and `find` fetch
    nothing and still always report `unverified`.

- **`.fux/pii.toml` — redaction of the committed index, and nothing else**
  (SR-PII). The boundary is **committed vs local**, not *sensitive vs not*:
  acquired bytes, refer passages and `fux answer` quotes are untouched.
  - **The sha is taken BEFORE redaction**, so `refer` still verifies a citation
    against its unchanged source. An index storing the sha of redacted text
    would report every document with one PII hit as `stale` against its own
    source, forever — a defect that presents as a working feature.
  - **Editing the ruleset invalidates extraction reuse** (`.fux/runtime/pii-digest`);
    a missing digest reads as *moved*, which costs one full extraction and settles.
  - 🔴 **`.fux/enrich/` is committed and is NOT redacted.** Stated in SR-PII
    decision 1 and SR-ENRICH decision 11 rather than left to be discovered.
  - ⚠ A pathological regex can hang an ingest — Python's `re` has no timeout.
    Empty patterns are refused and `doctor` compiles the rest; beyond that a
    consumer's regex is a consumer's regex.

- **`.fux/sources/types` became the decoder map: `decoder=<module stem>`**
  (SR-TYPES decision 11/11a, SR-DECODE decision 13). *"Which decoder reads
  `.csv`"* was a property of the code on a machine — two clones with different
  `.fux/decoders/` could commit different indexes from the same sources with
  nothing in the repo recording which decoder ran. It is now a committed line,
  checked against the module.
  - **Extending and redirecting are separated.** An extension **no** decoder
    claims may be given to any decoder; one another decoder **does** claim may
    not be handed to a module that does not claim it. `EXTENSIONS` is a
    decoder's *default claim*, not a declaration of what it can read.

- **`fux enrich` covers `url:` documents** via `enrich=` on a URL line
  (SR-ENRICH decision 11), under one synthetic scope, `.fux/sources/urls`.
  Possible only because the acquired plane holds the bytes locally — before it,
  planning a URL's enrichment meant a network fetch inside an offline command.

- **`fux add --keep` / `--no-keep` / `--ttl D`**, and **`fux update --failed`**
  (fetch only URLs whose last run failed). A flag on the existing networked
  verb rather than a `fux retry`, per SR-CLI decision 1.

- **`[sources.url] acquired_max_bytes`, `keep`, `ttl` and `enrich`**
  (SR-CONFIG decision 12) — each a source-wide *layer* a line still overrides.

### Changed

- **`cdp.py` returns the resource instead of a rendering** (SR-CDP-FETCHER
  decisions 5, 10–13; W-98 Phase 1). The shipped browser fetcher now
  intercepts the response over CDP — `Fetch.enable` at
  `requestStage: "Response"` → `Page.navigate` → `Fetch.requestPaused` →
  `Fetch.getResponseBody` — and hands fux **the bytes the server sent with the
  server's own `Content-Type`**, rather than `document.documentElement.outerHTML`
  declared as `text/html`.
  - **Why it matters:** a rendered DOM carries nonces, timestamps and session
    ids, so its sha changed on every fetch; and a rendering cannot be a
    spreadsheet. A `.xlsx` behind a login is now ingestible.
  - **Why interception and not an in-page `fetch()`:** measured, not argued.
    CORS and CSP are page-level and CDP is not — the same cross-origin URL
    sending no `Access-Control-Allow-Origin` returned `TypeError` in-page and
    **8557 bytes** under interception. A cross-origin in-page fetch also cannot
    see `ETag` at all.
  - **New:** `validate(url)` returns the server's `ETag`. ⚠ It saves the decode
    and the shard comparison, **not the download** — interception is at the
    response stage, so the body has already transferred.
  - **`LAUNCH_CHROME` now defaults to `False`.** A browser fux launched is
    signed in to nothing, so every URL worth a browser came back as a login
    page.
  - **`CdpSession` gained an event pump.** The old `_call` discarded every
    message that was not its own id, so a CDP event arriving while a command
    was in flight was lost — under interception that is a paused request nobody
    resolves, which wedges the page until the timeout rather than raising.
  - The rendering implementation is kept at
    `archive/templates/cdp-rendering.py.txt`.

  ⚠ **`fux setup` is write-if-missing and never rewrites a consumer's fetcher.**
  A repo with a hand-edited `.fux/fetchers/cdp.py` gets none of this until the
  file is replaced by hand.

### Fixed

- 🔴 **`NameError` on every retaining fetch.** `urlsrc.fetch_all` read
  `source.acquired_max_bytes` with no `source` in scope, because
  SR-ACQUIRED named the key and `config.py` never parsed it. The key is now
  parsed, validated (a `bool` is rejected — it is an `int` subclass — and `< 1`
  refuses, pointing at `keep = false`) and passed in explicitly.
- 🔴 **`refer()` raised in a repo with no `fux.toml`.** Reading a URL line's
  declared `ttl` turned *opting into caching* into a new way for an answer to
  fail. An **unconfigured** repo now declares nothing; a `fux.toml` that exists
  and is wrong still refuses.
- **`fux doctor` crashed on a Windows console codepage** in two failure
  branches — two em-dashes in returned check details, on the `.fux/pii.toml`
  rows.

### Removed

- **`settle_ms` from `[sources.url.config]`** — there is no render step left to
  settle. ⚠ **Breaking for a repo that sets it:** `configure()` raises a message
  naming the retirement and pointing at `load_timeout_s`, rather than letting it
  read as a typo in the generic unknown-key list.

## [2.0.0-alpha.4] - 2026-08-29

### Added

- **Three new built-in decoders: `jsonldoc` (`.jsonl`), `svgdoc` (`.svg`),
  `imagedoc` (`.png`/`.jpg`/`.jpeg`/`.gif`)** (SR-DECODE decision 10a).
  Sixteen built-ins → nineteen.
  - `jsonldoc` walks JSON Lines the same way `jsondoc` walks JSON — keys
    become headings, ids/hashes/timestamps are dropped — one malformed line
    is skipped rather than failing the file.
  - `svgdoc` extracts `<title>`/`<desc>`/`<text>`/`<tspan>` labels only,
    never path/shape geometry.
  - `imagedoc` extracts embedded text metadata only — PNG
    `tEXt`/`zTXt`/`iTXt`, JPEG EXIF IFD0 ASCII tags + `COM`, GIF comment
    extensions — hand-rolled per L1 (no Pillow). A pure-pixel image or a
    geometry-only SVG decodes to `None` and is not indexed at all.

  ⚠ **This widens `DEFAULT_TYPES`** (SR-TYPES decision 1 unions every
  built-in's extensions in automatically), reversing the SVG half of
  SR-TYPES decision 5 for every fresh `fux setup`. Images and `.jsonl` were
  never named by that decision, so those are new admissions rather than a
  reversal. See [SR-TYPES](records/0128_types-list.md) decision 5 and
  [SR-DECODE](records/0139_decode.md) decision 10a for the reasoning.

## [2.0.0-alpha.3] - 2026-08-29

### Added

- **`fux ask` gained `--sections` / `--no-sections`, and a `[cli.ask]
  sections` key** (SR-OUTPUT decision 21, SR-ASK decision 8 reopened).
  W-84's matched `§ heading` lines were the one part of `ask`'s output nothing
  could turn off.

  ```toml
  [cli.ask]
  sections = false     # hide the § lines AND the --json `headings` field
  ```

  **One key, both renderings.** `sections = false` removes the `§` lines from
  stdout *and* omits `headings` from the `--json` payload — a machine reader
  who does not want them is asking the same question a human is.

  ⚠ **An absent `headings` key is not the W-48 trap.** `[]` still means
  *nothing matched*. Absent means **not asked for** — `confidence`-under-
  `--band`'s shape, and `output.schema.json` marks it
  `required: "sections_requested"` rather than saying so in prose.

  **The default did not move** (`sections = true`), so a repo that says
  nothing gets exactly what W-84 shipped. `find` and `[mcp]` deliberately do
  not get the key — `find`'s `§`-free stdout is a design decision, and MCP has
  no text rendering.

- **`fux doctor` gained an `output.toml present` row.** A **warning**, naming
  `fux output > .fux/output.toml`, for a repo that predates the file. This is
  SR-DOTFUX decision 6's sanctioned mechanism for reaching existing repos,
  modelled on `types list usable`.

- **The two confidence band floors are `.fux/tune.toml` keys**
  (SR-CONFIDENCE decision 13, SR-TUNE decision 5d). A sixth table:

  ```toml
  [confidence]
  separation_floor   = 0.1   # the `grounded`/`weak` cutoff
  doc_coverage_floor = 0.0   # 0.0 = the clause is OFF
  ```

  **This reverses SR-CONFIDENCE decision 7**, which had refused both as tune
  keys. Neither can move a score or an ordering — confidence is computed *from*
  `rank()`'s output and nothing feeds back — so `[confidence]` is the first
  table in `tune.toml` that changes no ranking at all.

- **The confidence block now publishes the floors it was judged under.**
  `separation_floor` and `doc_coverage_floor` are emitted in `--json`, in the
  `fux_search` MCP result, and declared in `output.schema.json`. **Additive —
  an existing consumer is unaffected.**

  🔴 **Read them before comparing two bands.** Once the floor is repo-local, a
  `grounded` judged at `0.02` is not the same claim as one judged at `0.10`,
  and this is the only thing that makes the difference visible.

  ⚠ **`separation_floor = 0.0` means no answer is ever `weak` again.** That is
  a legal setting and a loud one: it makes fux quieter about not knowing rather
  than better at knowing. The default `0.10` remains **provisional and
  unmeasured** (prediction R10) and a repo-local value is never a calibration.

- **Handbook: two new sections on confidence** — *The formulas*
  (`docs/handbook.html#s-conf-formula`: the shared `idf`, every signal written
  out, the five-clause band ladder, and the NQC / clarity-score grounding for
  `separation`) and *Tuning the floors* (`#s-conf-tune`).

### Fixed

- 🔴 **`fux ask`, `fux find` and `fux doctor` hard-failed in every repo without
  `.fux/output.toml`** (SR-OUTPUT decision 20 rules the fork decision 19
  opened). Decision 19 made a *missing* file a hard `FuxError` at load time.
  The file is **write-if-missing** (SR-DOTFUX decision 6), so it reaches new
  repos only — which made every pre-existing repo exit 1 on every query after
  upgrading, **`doctor` included**, the verb you would run to find out why.

  ```console
  $ fux find "oncall rota"
  error: .fux/output.toml is missing — run `fux setup` to create it
  exit=1
  ```

  **A missing file now resolves to the engine defaults.** Decision 19 is
  otherwise untouched: a file that **exists** and omits a key a verb resolves
  is still a hard error, which is the case it was written about. Decision 19's
  own wording — *"once it is in effect"* — is what survives; a file that does
  not exist is not in effect.

  ⚠ **If you rely on `fux ask` refusing to run when the file is absent, it no
  longer does.** Run `fux doctor` — the new `output.toml present` row is where
  that now shows up.

- **`test_the_receipt_shape_does_not_vary_by_config` had not run since
  SR-OUTPUT decision 19.** It imported `SCHEMA` from `output_config`, which
  decision 19 split into `CLI_VERBS` and `MCP_KEYS` — so the assertion was an
  `ImportError`, not a check. It now walks **both** key sets, including
  `[mcp]`, which is the surface SR-PROVENANCE decision 15 was written about.

- **SR-TUNE decision 4 described behaviour the code had not had since
  2026-08-27** — it said tune keys ship *commented* and carried a commented
  specimen; they have shipped as live lines since Arpit's ruling that day.
  Rewritten, with the setup-freeze cost it correctly predicted now recorded as
  paid.
- **`output.schema.json` said `doc_coverage` below `1.0` makes the band
  `partial`.** The gate was measured on 2026-08-28 and left **off**; the field
  reports and does not gate.
- **Handbook staleness:** *Fact vs guess* claimed SR-CONFIDENCE was *proposed*
  (accepted since 2026-08-27) and that the floor was deliberately not a tune
  key; *The five fields* counted five when `doc_coverage` made it six; the
  `--json` sample omitted three keys.

- **`fux ingest` writes the skip list into `.fux/.fuxignore`, and counts it in
  two numbers** (SR-FUXIGNORE decision 11, SR-INGEST decisions 4 and 15).
  `599 skipped` on this repo was 598 files a committed list rejected exactly as
  designed and **one** worth looking at, and the list itself sat in
  `.fux/runtime/skipped` — derived, gitignored, invisible to review.

  ```console
  ingested 632 docs (32 changed, 600 carried forward), 341 not indexed, 1 skipped, 31 shards written
  ```
  ```
  # .fux/.fuxignore
  # >>> fux: not indexed >>>
  # a committed list said not to index these. Rewritten by every `fux ingest`.
  archive/v0.1/fux/cli.py   # not an indexed file type
  # <<< fux: not indexed <<<

  # >>> fux: skipped >>>
  # fux opened these and could not read them.
  archive/v0.26/tests_e2e/corpus/docs/binary.md   # binary
  # <<< fux: skipped <<<
  ```

  **`not indexed`** is a committed list doing its job — `.fuxignore`, a `!`
  exclusion in `.fux/sources/dirs`, the type allowlist. **`skipped`** is a file
  fux opened and could not read. Printed lines use the summary's own two words,
  so a line and the total above it can never say different things about one
  event. **`.fux/runtime/skipped` is deleted on every run.**

  ⚠ **The blocks are written FIRST, above every hand-written line.** Last match
  wins in this file, so a block written last would silently beat a `!` you
  wrote. First means you always win, and `!<path>` is how you pull a file back
  out of a block.

  ⚠ **A generated line DECIDES, so it freezes the verdict that produced it.**
  Widen `.fux/sources/types` and the listed `.py` files stay out; write content
  into a file listed as `empty` and it stays out. That is what putting the list
  in `.fuxignore` means, and it is not undone — it is made **loud**: every run
  re-checks each line and warns on stderr when one has stopped being true,
  naming the edit that fixes it. Delete the line, or write a `!`.

  **A pattern you write suppresses the generated lines it covers.**
  `__pycache__/` and `*.py[cod]` in this repo keep 257 lines out of the block,
  leaving 342. That lever is deliberately a person's: fux writes exact paths and
  never infers a pattern, because an inferred pattern can over-reach onto a file
  the corpus does not have yet and the failure would be a document silently
  missing.

  **Nothing machine-readable moved.** `fux ingest --list-skipped` is still
  `path: reason`, sorted and unprefixed. ⚠ **W-88's report-once promise now
  covers files only** — a URL has no repo-relative path, so a URL skip has
  nowhere to be recorded and prints on every networked run; repeat URL failure
  is `.fux/runtime/url-state.json`'s job.

- **`.fux/.fuxignore` — one file for what is not indexed** (SR-FUXIGNORE).
  *"Why is my file not in the index?"* had four answers across three files plus
  the walker's source. Exclusion now has one home, in `.gitignore`'s grammar:
  last match wins, `!` re-includes, a trailing `/` means a directory, any `/`
  anchors at the repo root, `**` is the explicit any-depth form, and a file
  under an ignored directory cannot be re-included — git's rule, kept.

  **It is read first and decides in both directions.** A path it ignores is
  skipped whatever `.fux/sources/types` allows; a path it **explicitly**
  re-includes with `!` is indexed whatever `types` disallows. Every skip names
  the file, the line number and the pattern:
  `ignored by .fux/.fuxignore:12 \`*.log\` (docs/notes.log)`.

  ⚠ **`!` means the opposite of what it means next door.** It subtracts in
  `.fux/sources/dirs` and `.fux/sources/types`; it re-includes here. Deliberate
  — a `.fuxignore` that did not behave like a `.gitignore` would be worse than
  none. `fux ingest`, `fux ingest --list-skipped` and `fux doctor` warn when the
  same pattern is written in both places, naming the `sources/` line to delete.

  ⚠ **A `!` line can now index a format with no decoder, as raw bytes.**
  `!*.py` really does index Python. That is the shape SR-TYPES was opened
  about; it costs one explicit line a human wrote, in one committed file.

  ⚠ **One deliberate divergence from git:** a `#` after whitespace begins a
  comment, so `*.log  # noisy` is a pattern plus a note. Git reads that whole
  line as a pattern matching nothing.

  Absent, empty or all-comments means nothing is ignored — safe here, unlike
  `sources/types`, because this file only ever subtracts by default. `fux setup`
  writes the header and no patterns, write-if-missing.

### Changed

- **SR-TYPES decision 7 is narrower.** The three walk conditions were *"a
  conjunction, deliberately not a priority order"*. They are now a conjunction
  with exactly one thing above them. SR-DIR-LIST decision 3a is unchanged and
  its argument is restated: `fux add` still may not outrank the allowlist,
  because a verb leaves nothing behind for a reader to find and a committed
  `.fuxignore` line does.
- **`!` lines in `.fux/sources/dirs` and `.fux/sources/types` are the
  deprecated spelling for an exclusion.** They still parse and still work —
  `fux remove` still writes one — and `.fuxignore` is the home.
- **A `.fux/output.toml` that EXISTS is now the sole source of every output
  default it is asked for** (SR-OUTPUT decision 19). Earlier, a key the file
  did not set fell through silently to the engine's built-in value; now
  resolving an unset key on a present file is a `FuxError` naming the key and
  where to add it. `fux setup` / `fux output` already write every key
  **live**, so a repo that has run either never sees this — it reaches only a
  `.fux/output.toml` that predates a key this version added, or one edited by
  hand with a line deleted. `--no-output-config` (or running outside a fux
  repo) still bypasses the file entirely and resolves the engine defaults, and
  now reaches `doctor`, `hooks`, `daemon`, `explain`, `graph` and `path` as
  well — it was previously wired only to `ask`/`find`/`answer`/`mcp`, which
  left `doctor` unable to be bisected from the very file it might exist to
  diagnose.
- 🔴 **Fixed same-day: a MISSING `.fux/output.toml` no longer hard-errors**
  (SR-OUTPUT decision 20). Decision 19, above, briefly made a missing file
  raise too — and since the file is write-if-missing (SR-DOTFUX decision 6,
  reaching new repos only), that meant `fux ask` / `fux find` / `fux doctor`
  all exited 1, after upgrading, in every repo that predates this release.
  **Fixed before it reached anyone**: a missing file now resolves to the same
  engine defaults as `--no-output-config`; a file that *exists* and omits a
  key is unchanged and still a hard error. `fux doctor` gains an
  `output.toml present` row — a warning naming `fux output > .fux/output.toml`
  — since a loader refusal was already ruled out as the fix for a missing
  file (SR-DOTFUX decision 6 forbids reaching an existing repo by rewrite).
- **`.fux/output.toml`'s three roots (`[cli]`/`[cli.json]`/`[mcp]`) are now
  fully built**, closing a one-day gap where SR-OUTPUT's record described
  them and the code still ran the original one-root layout. `[mcp] top`
  (`fux mcp`'s only knob) is loaded once at server start-up instead of once
  per search, and the `fux_search` tool schema now advertises the *resolved*
  `top`, not a hardcoded literal — a repo-configured `[mcp] top` used to
  change the server's behaviour while `tools/list` kept announcing the
  built-in number.
- **`ask` gains `sections` / `--no-sections`** (SR-OUTPUT decision 21). The
  matched-heading `§` lines W-84 added under each `ask` hit shipped
  unconditional, with no way to turn them off; `sections = false` in
  `[cli.ask]` (or the flag) removes them from stdout **and** omits `headings`
  from the `--json` payload — one key answers the question for both
  renderings. The omitted key means *"not asked for"*, same shape as
  `confidence` under `--band`; `[]` still means *nothing matched*, unchanged.

## [2.0.0-alpha.2] - 2026-08-26

### Added

- **URL freshness closes its loop** (W-82 §3.2). The refer plane already fetched
  every cited URL and already computed whether its sha still matched the index —
  then **threw the fact away**. It now records that `url:` doc id in the dirty
  list, where `ingest.run(only_urls=...)` consumes it.

  **This buys recall, not correctness.** A changed document could never be
  *mis-answered* — the verdict beside every citation is what stops that — it
  could only fail to surface, because ranking runs on the terms the index
  recorded. Prioritisation comes out **usage-weighted for free**: documents
  people actually retrieve get verified constantly, because they are cited.

- **`fux doctor` reports URL health** (W-82 §3.1). How many `url:` records
  exist, how many the last networked run confirmed, how many have never been
  re-fetched since first ingest, and how many are failing — naming any that have
  failed five runs in a row.

  **Report, never auto-delete.** SR-URL-INGEST decision 4 forbids treating a
  failed fetch as a deletion, and the cost of that rule is that a permanently
  dead URL lives in the index forever. This makes the cost legible instead of
  invisible. ⚠ **The counters are runs, not clocks** — wall clock lives in the
  TTL store and nowhere else.

- **Parallel URL fetching, by declared capability** (W-82 §3.3). A fetcher
  module may declare `MAX_PARALLEL = n`; **absent the declaration it is 1**, so
  behaviour is byte-for-byte what shipped before. `[sources.url] max_parallel`
  caps it from the consumer side: `min(declared, configured)`.

  Two values, two kinds of refusal — the module's declaration is **capability**
  and exceeding it clamps down loudly; the config value is **policy** and a
  large one is honoured with a warning that states the cost; `< 1` refuses.

  ⚠ **A blanket pool would have been silently wrong.** The shipped `cdp.py`
  holds one WebSocket in a module global, and two threads on it produce
  *plausible documents attributed to the wrong URLs* — which passes every
  determinism check. **Sequential fetching was never what made the index
  deterministic; the trailing sort is.** First threading in `src/fux/`; stdlib
  only, so L1 is untouched.

- **`fux answer` says whether anything changed since you last asked** (W-82
  §3.4). ⚠ **A report, not a memo** — no answer is stored and nothing is
  replayed; only the previous answer's `(loc, sha)` pairs are remembered. On
  **stderr in both text and JSON mode**, so stdout stays byte-identical.

- **A `fux-usage` agent skill, and an invocation ladder** (W-82 §3.6), closing a
  live silent defect: the shipped agent rendering told an agent to fall back to
  ordinary search when `fux` was not found, so **any repo whose fux lived in an
  unactivated `.venv/` had agents quietly using grep** while the engine and the
  committed index sat right there.

  The ladder is `fux` -> `uv run fux` -> `./.venv/bin/fux`
  (`.venv\Scripts\fux.exe` on Windows) -> `python -m fux.cli`, probed with
  `--version` and cached per session. **No rendering may tell an agent to
  activate a virtualenv, modify `PATH`, or install anything** — gated by a test,
  because that is the fix a well-meaning edit reaches for.

  It ships to Claude and Kiro from **one template at two paths**, because Kiro
  implements the same open Agent Skills standard — agreement by construction
  rather than by conformance test.

### Changed

- `[sources.url]` gains `max_parallel`. Absent means *whatever the fetcher
  declares*, which is `1` unless the module says otherwise.


### Removed

- **Breaking: the bundled embedding model and the entire dense lane are gone**
  (Arpit, 2026-08-25). `src/fux/embed/` — `model.py`, `fuxvec.py`,
  `chunkvec.py` and the 7.9 MB `model.bin` — plus `query/dense.py`,
  `derive/dense.py`, `.fux/runtime/codes.jsonl`, the committed per-chunk
  `vectors` field, the `[dense]` tune table and **`ask --hybrid`**.

  **Why:** [DENSE-CHUNK](work/regression/2026-08-24-dense-lane-gate/VERDICT.md)
  measured **0 fixed / 2 broken at every setting that fires**, against a bar of
  `>= 3-fixed / 0-broken`. The bundled model mean-pools static token vectors, so
  the lane was **as order-blind as BM25F** — it duplicated the lexical lane's
  blind spot at far higher cost.

  **What it cost, measured A/B on the same corpus**
  ([run](work/regression/2026-08-25-model-removal/report.md)):

  | | before | after | |
  |---|---|---|---|
  | wheel | 6.84 MB | **233 KB** | **30.1x smaller** — the download was 97 % model |
  | committed index | 6 528 570 B | 5 052 388 B | **-22.6 %** |
  | full ingest | 33–36 s | ~4.9 s | **~6.8x faster** |

  **Ranking does not move.** `[dense] mode` defaulted to `off` and the gate
  returned before any dense work, so anyone who never typed `--hybrid` sees
  byte-identical results. The differential law still holds.

  **Migration:** delete `[dense]` from `.fux/tune.toml` (and from `fux.toml` if
  it predates 2026-08-24) — both now raise an error naming the removal rather
  than a generic "unknown table". Drop `--hybrid` from any script; it is now an
  argparse error rather than a silent no-op. `RUNTIME_SCHEMA` moves
  `fux.runtime.v4` -> `v5`, so `.fux/runtime/` is refused and rebuilt once;
  nothing committed needs regenerating, though a re-ingest is what drops the
  `vectors` field from existing records.

- **Breaking: `[fuse]` is gone from `.fux/tune.toml`'s key set.** `rrf_k` and
  `dense_width` were validated and threaded but had no CLI reader — their only
  consumer, `src/fux/query/hybrid.py`'s `hybrid_ask`, was already off the live
  path. Anyone who set either key now gets a loud "unknown key" error instead
  of a silent no-op. `--hybrid` is unaffected: it fuses through
  `query/dense.py`'s gated lane, which never read these keys.
- **Breaking: `explain --no-tune` is removed.** `cmd_explain` never read a
  tunable, so the flag parsed and did nothing. `--no-tune` now applies to
  `ask`, `find`, `answer`, `graph` and `path` — five verbs, not six.
- `src/fux/query/hybrid.py` — the module-level RRF fusion, dead since W-76
  Phase 7 gave `--hybrid` a lane through `query/dense.py`. Its only caller,
  `tools/differential/playground_grade.py`, now grades `--hybrid` through
  `fux.query.run_query`, the same path the CLI takes.
  [SR-TUNE](records/0135_tuning.md), [SR-CLI](records/0101_cli-surface.md),
  [SR-ASK](records/0103_ask.md) — filed as
  [W-79](archive/open/W-79-remove-the-dead-fusion-code.md).

## [2.0.0-alpha.1] - 2026-08-24

**SR-TUNE is built.** The knobs that decide what you read first have a home.

### Added

- **`.fux/tune.toml` — the tunables file.** Committed, written once by
  `fux setup`, and **never rewritten by fux**. Absent, empty, or every key
  commented out means every default, so `$0` stays `$0`. Seven tables:
  `[bm25f]` (`k1`, `b`, five field weights), `[ranking]`, `[dense]`,
  `[fuse]`, `[graph]`, `[refer]`, and `[priority]`.
  [SR-TUNE](records/0135_tuning.md).
- **Per-source priority, in either direction.** A multiplicative weight keyed
  by a source entry exactly as it appears in `.fux/sources/`. Anything
  unlisted is `1.0`; when two entries match, the **longer** one wins. Fux
  states the cost and refuses exactly two values: a negative weight (it
  inverts the ordering) and zero (that is exclusion, and the `!` prefix in
  `.fux/sources/` already owns it).
- **`--no-tune`** on the read verbs — the *is it me or the config?* switch. It
  does not read the file at all, so a malformed tune file does not stop it.
- **`fux tune`** — prints the tunables file for you to paste. It never writes;
  there is no TOML writer anywhere in fux, which is what keeps the
  never-rewritten promise cheap to hold.

### Changed

- **Breaking: `[ranking]` and `[dense]` are retired from `fux.toml`.** They
  moved to `.fux/tune.toml` whole. The old tables now raise an error naming
  the new home rather than being silently ignored — a key that is quietly
  not read is worse than one that errors, because you believe your setting is
  in force. Same shape as the `middleware` -> `fetcher` rename.
- **`RUNTIME_SCHEMA` -> `fux.runtime.v4`.** `.fux/runtime/stats.json` stores
  `total_flen`, the five **raw** per-field token-count totals, where it used
  to store a pre-weighted `total_wlen`. Run `fux build` once; nothing
  committed changed and the runtime plane is disposable. An older plane is
  refused with a message that says so rather than a `KeyError`.
- `k1`, `b` and the five field weights are carried as one `Scoring` object
  through the scorer and the accelerator's pruning bound. They appear on both
  sides of one fraction, and passing them separately is what makes it possible
  to reweight a numerator against a denominator computed at the old weights.

### Fixed

- **`fux doctor` warned about files fux itself writes.** `.fux/` had no
  category for a committed *file* — only directories — so `tune.toml` (and
  `enrich/`) reported as undeclared entries. Found by checking the claim
  instead of asserting it.

### Notes

- **The four new records still ship `status: proposed`.** Built is not
  ratified, and the register carries two columns for exactly that reason.
- Two `[fuse]` keys are validated but no CLI path reads them today, and
  `explain --no-tune` is inert. Both are stated in SR-TUNE rather than left
  to be discovered.


## [2.0.0-alpha.0] - 2026-08-24

**A pre-release.** The record shape and analyzer changed, so this ships
ahead of a stable `2.0.0` to give the migration a soak before it is called
final — every new SR here (`SR-TUNE`, `SR-MCP`, `SR-ENRICH`, `SR-RERANK`)
is still `status: proposed`.

### Changed

- **Breaking: the committed record shape moves to `fux.index.v2`.** BM25F
  goes from two fields to five (`body, heading, title, path, ctx`), body
  first — measured **-36.7%** on tf-vector bytes while adding three fields.
  `flen` replaces `wlen`, so field weights are tunable without touching a
  committed byte. The `code` field is dropped (it was 91% of every ingest
  for 0.4% of the index). `fux ingest --full` is required to move an
  existing `.fux/index/` off `v1`; this repo's own corpus is migrated in
  this release (434 records, delta run byte-identical to the full run).
  [SR-INDEX-LIFECYCLE](records/0108_index-lifecycle.md),
  [SR-RECORD](records/0109_index-record.md).
- **The analyzer moves to `v2`** — Porter stemming (75/75 published vectors)
  and identifier splitting, `query/analyzer.py` + `query/stem.py`.

### Fixed

- **[W-73] The accelerator's differential law held only at `archived_weight
  == 1.0`.** `ask --fast` and `ask --scan` could silently disagree at any
  other configured weight, in both directions. `rank.Weighting` now carries
  the query-time weights into the pruning bound itself (`derive/accel.py`),
  so the law holds at every weight — verified by an adversarial fixture
  that fails at `w = 500` without the fix. A second, smaller divergence
  found on the way: the derived doc table didn't carry the `archived` flag,
  so the two paths could disagree on that marker even at the default
  weight; fixed in the same change (`RUNTIME_SCHEMA` -> `fux.runtime.v3`).
  This closes the known limitation recorded in `1.0.0`.
- **`fux ingest --full` could not perform the migration this release
  requires.** It read the existing index *before* checking `--full`, so the one
  command that exists to replace an outdated index **refused to run against
  one** — leaving `rm -rf .fux/index/` as the only apparent way forward, which
  silently destroys every `url:` record, the one thing in the index that cannot
  be rebuilt offline. `--full` now discards an unreadable index when nothing
  would be lost, and refuses **by name** when `url:` records would be. Present
  in `1.0.0`. [SR-INDEX-LIFECYCLE](records/0108_index-lifecycle.md)
  decision 10.
- **`fux enrich --plan` printed a sha that could not be used.** It showed the
  first 12 characters while validation compared the whole value, so enrichment
  written by correctly following the documented procedure came back `STALE` —
  under a message rendering two identical-looking shas. Both the command and
  the skill's own worked example are corrected.
  [SR-ENRICH](records/0137_enrich.md) decision 11.

### Added

- **`.fux/tune.toml`** — a committed, write-if-missing ranking file for
  BM25F field weights, fuse/graph/refer constants and per-source query-time
  priority (longest-directory-match, multiplicative, both directions
  allowed — fux states the cost rather than picking a side).
  [SR-TUNE](records/0135_tuning.md).
- **`fux enrich`** — a separate, opt-in command that writes model-assisted
  enrichment into `.fux/enrich/` for a named scope; never runs inside
  `fux ingest`, so the maintenance path stays model-free (L3).
  [SR-ENRICH](records/0137_enrich.md).
- **`fux mcp`** — serves the index to coding agents over stdio JSON-RPC,
  stdlib-only, as three tools rather than the full CLI surface (no
  `answer` — the agent is the answerer). [SR-MCP](records/0136_mcp.md).
- **Proximity reranking**, in stdlib arithmetic — a specified cross-encoder
  pass was refused because `onnxruntime` is not byte-identical across
  x86-64/arm64. Measured on 50 new playground goldens: 28 -> 32 (4 fixed,
  0 broken), +8ms p95 against a 150ms bar at 10 000 documents, 240
  differential comparisons green. [SR-RERANK](records/0138_rerank.md).
- **Per-chunk committed `int8` vectors**, with a derived Hamming-prefix
  prefilter over them replacing the old whole-document sign codes.
- **Priors** — `supersedes:` frontmatter edges and git commit recency,
  folded into ranking through the same `Weighting` the accelerator bounds
  on, rather than as an unbounded side channel.

### Known limitation

- **Enrichment measured in this release's regression run
  ([`2026-08-24-rerank-and-goldens`](work/regression/2026-08-24-rerank-and-goldens/))
  was authored by someone who had already seen the failing queries** — its
  28/50 -> 38/50-41/50 numbers are an upper bound, not a clean measurement.
  A re-grade against blind enrichment is the named follow-up.

## [1.0.0] - 2026-08-22

**The first major release of the v0.30 index-and-refer rebuild.** M2 through
M5 are shipped: the derived accelerator (`ask --fast`, byte-identical to the
reference scan under the differential law), the graph lane (`explain` /
`graph` / `path`, unseeded communities, lazy PPR — both acceptance gaps
closed 2026-08-22), the refer plane (`answer` fetches, verifies and re-scores
cited documents live), and the maintenance hooks (post-commit/post-merge
re-ingest, a conflict-refusing merge driver for `.fux/index/*.jsonl`).
Archived content is signalled without moving the ranking; the corpus is
maintained with `fux add` / `remove` / `update` over directories, single
documents and URLs alike.

No `src/` behaviour changed in this release beyond the version string — it
marks the milestone `v0.37.1` already reached, not new code.

### Added

- Every SR gains a `References` bibliography, generated from the citations
  already in its own body — 465 links, nothing invented.
- Two research proposals on ranking/pruning tuning, filed but not built:
  a committed `.fux/tune.toml` and per-source query-time priority.

### Known limitation

- **[W-73](https://github.com/arpitarya/fux/blob/main/archive/open/W-73-weighted-scores-vs-pruning-bound.md):**
  the accelerator's differential law — `ask --fast` and `ask --scan` return
  identical results — holds only at the `archived_weight` default (`1.0`).
  The pruning bound is computed unweighted; a configured weight can make the
  two paths disagree. Default behaviour is unaffected; tracked openly rather
  than fixed silently before this release.

## [0.37.1] - 2026-08-22

### Changed

- **Docs only, no code change.** `README.md`'s status block was two releases
  stale (still read `0.36.0` and described the graph lane's two acceptance
  gaps as open after both closed); rewritten against ground truth and given
  an archived-content-signalling paragraph. `records/TEMPLATE.md` gains an
  optional worked-output block per §2 section, retrofitted to
  SR-ARCHIVED-CONTENT, SR-REFER and SR-GRAPH where real output existed.
  The committed `.fux/index/` shards were re-derived from the corpus these
  doc edits touched.

## [0.37.0] - 2026-08-22

### Added

- **Archived documents now say so, in every verb.** A document from a source
  declared `archived=true` carries `archived: true` on its record, `ask` prefixes
  its title with `[archived]` in text output, both `ask` and `find` carry the
  flag in `--json`, and a response-level note goes to **stderr** whenever any
  archived document is returned. **The ranking does not move**: the demotion
  weight stays at its `1.0` default and a test asserts scores and order are
  byte-identical with the marker present.
  [SR-ARCHIVED-CONTENT](records/0134_archived-content.md) decisions 1, 3 and 7.

  Measured before shipping, on a frozen 45-query instrument:
  **[W44-SIGNAL](work/regression/2026-08-22-archived-signal/VERDICT.md) —
  WARRANTED**. On this repo's own corpus, 32.00 % of the top-5 for a
  present-tense question about the current engine was retired material, against
  a pre-registered 25-point bar, while archived documents stayed findable when
  actually wanted (93.33 % recall). `fux ask "what commands does the fux command
  line have"` returned five retired documents and no current one.

  **`fux find`'s stdout is unchanged** — bare paths, so it still pipes; the flag
  is in `--json` and the note on stderr.

### Fixed

- **`fux answer` no longer discards half its byte budget.** The refer plane's
  per-document cap applied even when there was only one candidate document —
  which is every `fux answer` call, since `refer()` is passed exactly one. The
  cap exists to stop one document dominating a field of several; with a field of
  one it only truncated the answer. On a real query the assembled answer goes
  from **3 passages / 3 492 bytes to 6 passages / 6 991 bytes** against the same
  8 000-byte budget. Found by
  [the budget sweep](work/regression/2026-08-22-budget-sweep/report.md), fixed
  as W-72; the cap still binds the moment a second document competes, with a
  test for each direction.
  [SR-REFER](records/0127_refer-plane.md) veto condition 2.

## [0.36.0] - 2026-08-22

**Committing stops waiting for a re-index, and fux now ships the policy its
readers need to read it correctly.**

The headline is a latency change you will feel on every commit in a large
repository, and a scaffolding change you should read before upgrading: `fux
setup` writes outside `.fux/` for the first time, into directories GitHub, AWS
and Anthropic own. It announces every one of them and both ways to turn them
off.

[SR-MAINTENANCE](records/0129_hooks.md) 1a–1d ·
[SR-AGENT-POLICY](records/0132_agent-policy.md) ·
[SR-DIR-LIST](records/0120_dir-list.md) 11. Measured evidence:
[R6 re-run](work/regression/2026-08-22-r6-rerun/VERDICT.md) (PASS) ·
[R9](work/regression/2026-08-22-r9-t2-at-10k/VERDICT.md) (PASS).

### Added

- **`fux setup` now installs agent policy — and writes outside `.fux/` for the
  first time.** Fux marks retired documents `archived` and states no
  conclusion; these files teach your agents how to read that mark, which is the
  difference between an agent citing a deleted design confidently and one that
  tells you it is retired. Four files, three vendors:

  | vendor | file |
  |---|---|
  | Claude | `.claude/skills/fux-archived-results/SKILL.md` |
  | Copilot | `.github/agents/fux.agent.md` |
  | Copilot | `.github/instructions/fux-archived-results.instructions.md` |
  | Kiro | `.kiro/steering/fux-archived-results.md` |

  **They install by default, and `setup` tells you it did** — naming every path
  and how to turn it off. **`fux setup --no-agents`** skips them for one run;
  `[agents] install = []` in `fux.toml` is the durable form, and you can name a
  subset. The default is written into your `fux.toml` in full, so it is
  something you can read and edit rather than something buried in the engine.

  ⚠ **Two of the four are ambient** — Copilot's `applyTo: "**"` and Kiro's
  `inclusion: always` enter *every* request in the repository, for every
  developer, whether or not they are using fux. That is a real cost and it is
  why `setup` announces them. They are ~2 KB each and a test keeps them that
  way.

  Write-if-missing like everything else `setup` writes: edit any of them and
  fux will never rewrite it. [SR-AGENT-POLICY](records/0132_agent-policy.md).

- **`post-commit` no longer waits for a re-index.** It records what changed and
  spawns a **detached one-shot** background run, so committing costs what git
  costs regardless of corpus size. The re-index still happens; nobody watches
  it. [SR-MAINTENANCE](records/0129_hooks.md) 1a–1d (W-66).
  - **`fux ingest` takes over** from a background run, and **`fux ingest
    --stop`** halts one without running — exiting **0** when nothing was
    running, so scripts can call it defensively.
  - **`fux doctor` reports the background runner** — live/idle and its pid, how
    many documents are pending, whether a lock is held or stale, and whether
    the last run failed. It **names the command to clear a stale lock and never
    clears it itself**.
  - **`fux doctor --json`** — `doctor` had no machine-readable form.
  - Stopping is **cooperative**: a background run is only ever interrupted
    between units of work and never mid-write, so a stopped run leaves the
    index byte-clean and nothing pending is lost.

- **`[ranking] archived_weight`** (`fux.toml`, default `1.0`) — a score
  multiplier for documents under a directory declared `archived=true`.
  Byte-identical at the default; demotes an archived document only once a
  weight is configured. [SR-DIR-LIST](records/0120_dir-list.md) decision 11
  (W-44). The marker and the response-level disclaimer (decisions 5/7/12)
  stay gated on a pre-registered query set.
- **`fux ask` says when the index is behind.** Since the hook defers, the
  committed index can lag by more than one commit, so `ask` states how many
  documents are pending — on **stderr**, so `--json` and every pipe produce
  exactly the bytes they did before. It is a declaration, never a gate: `ask`
  does not refuse to answer and does not re-index on your latency.
  [SR-MAINTENANCE](records/0129_hooks.md) decision 1b (W-66).
- **A dirty list** (`.fux/runtime/dirty`, gitignored) records which documents
  each commit touched. **It is advisory only** — `fux ingest` produces the same
  index whether the list is right, stale, empty or missing, which is asserted
  rather than reasoned about. It exists so the background run can report what
  is pending, and so a future incremental re-index has something to consume.

## [0.35.0] - 2026-08-21

The corpus becomes a first-class verb, and two defects that made removing a
document harder than adding one are fixed.
[SR-CLI](records/0101_cli-surface.md) 1a–1e ·
[SR-INGEST](records/0106_ingest.md) 9–10 ·
[SR-DIR-LIST](records/0120_dir-list.md) 2d–2e, 3a. Surface captured
verbatim in [`work/regression/2026-08-21-source-verbs/`](work/regression/2026-08-21-source-verbs/report.md).

### Added

- **`fux add` / `fux remove` / `fux update` — the corpus is a first-class
  verb now.** They work over `.fux/sources/dirs`, `urls` and `types` alike,
  dispatching on the entry: anything with a `scheme://` is a URL, `--types`
  says type pattern, everything else is a path — and a path may be a directory
  **or a single document**, which the list always accepted and no command ever
  wrote.

  - **`add` records and then does the work.** It ingests by default
    (`--no-ingest` opts out), and for a URL it **fetches that one URL**
    (`--no-fetch` opts out), announcing on stderr that it went to the network.
  - **`remove` has two branches and says which it took.** An entry with its own
    line loses the line; a path held only by a listed ancestor is subtracted
    with `!`, leaving the ancestor listed. It reports what left the index and
    how many inbound graph edges went with it.
  - **`update` re-reads what is listed and never writes a line.** With no
    entry it re-reads everything; with one it re-reads that. `--check` is
    read-only and offline for files.
  - `--dry-run` on `add`/`remove` prints the line and the plan and writes
    nothing.

### Changed

- **A de-listed URL now leaves the index on an *offline* run.** Removing a URL
  from `.fux/sources/urls` used to have no effect until someone ran
  `--refresh-urls` — so **deleting a document required the network**, which it
  never needed. Reconciliation reads a committed file; only *fetching* is
  fenced. A URL that is still listed and whose fetch fails still keeps its
  prior record, unchanged: that guarantee is about the fetch, not the list.
- **A carried-forward record no longer keeps edges to documents that are
  gone.** `url:` records are reused whole on an offline run, edges included,
  and those edges were resolved against a previous run's corpus — so a removed
  document could survive as an edge target in the derived graph. Every carried
  record's edges are now re-checked against the run's own id set.
- **`fux explain` distinguishes "no relationships" from "not in the index".**
  It answered the same way for both, and exited 0 for a document the corpus
  does not hold.
- **`fux add '<pattern>' --types` extends the built-in file-type allowlist
  instead of replacing it.** `.fux/sources/types` *replaces* the default when
  it exists, so creating it with one pattern silently un-indexed every
  markdown document. `add` now seeds the defaults when it creates the file.

### Fixed

- **`fux add` no longer crashes on a Windows console.** The explanation it
  prints when the type allowlist rejects a file used an arrow (`→`), which is
  outside `cp1252` — so `print()` raised `UnicodeEncodeError` and the command
  exited non-zero instead of rendering badly. It is ASCII now, and a check
  (`tests/test_windows_console_safe.py`) refuses any non-`cp1252` character in
  anything the CLI prints. Second occurrence of this class; `fux doctor`'s
  checkmarks did it at 0.30.0.

### Removed

- **`fux url` is gone.** Use `fux add <URL>` and `fux remove <URL>`. It is
  deleted rather than deprecated: it shipped four days ago, this is pre-1.0,
  and the replacement is a rename plus a fetch. `--cdp`, `--http`, `--plain`
  and `--hashed` mean exactly what they meant.
- **`fux ingest --refresh-urls` is retired into `fux update`** and hidden from
  `--help`. **It still parses for one release** — it is a flag rather than a
  verb and more likely to be in a pipeline. `fux update` differs in one way,
  and it is a fix: a repo with no `[sources.url]` is not an error there.

- **`fux ingest` and `fux build` show progress.** A bar on **stderr**, painted
  only when stderr is a terminal, reporting **counts and no clock** — no
  elapsed, no ETA, no rate. It engages per phase once that phase has more than
  ~200 items, so a run where everything carries forward stays quiet.
  `--no-progress` and `--progress` force it off and on; `FUX_NO_PROGRESS=1`
  disables it from the environment. The installed git hooks turn it **on**
  explicitly, because a slow commit is where silence is most alarming.

  **Your pipelines are unaffected, by construction.** stdout is byte-identical
  with the bar on or off — `--json`, `| tee`, and every captured transcript
  produce exactly the bytes they did before. That is asserted per verb in the
  test suite, not merely intended.

  Motivated by a measured 44.4 s of total silence when re-indexing 100 000
  documents on the commit path
  ([R5](work/regression/2026-08-20-r5-hook-latency/VERDICT.md)).
  Surface captured verbatim at
  [`2026-08-21-progress-plane`](work/regression/2026-08-21-progress-plane/report.md).

### Changed

- **`ask`/`find`/`answer`/`graph` scan by default; `--fast` opts into the
  accelerator** (Arpit, 2026-08-21). Previously the reverse: the accelerator
  answered whenever a fresh build existed, and `--scan` forced the reference
  path. `--scan` is unchanged in behaviour and now redundant with the
  default — kept because it is what a bug report reproduces against
  explicitly. `--fast` and `--scan` are mutually exclusive. The differential
  law (SR-ASK) makes this a pure speed choice: results are byte-identical
  either way. See [SR-CLI](records/0101_cli-surface.md) and
  [SR-ASK](records/0103_ask.md).

## [0.34.0] - 2026-08-21

**Four milestones in one release — the graph lane, the refer plane, the
maintenance plane, and delta ingest — plus the prediction series that
measures three of them against pre-registered thresholds.**

M3 makes the edges ingest already extracts answerable: `explain`, `graph`,
`path`, and deterministic seedless community detection. M4 builds the refer
plane — fetch a citation from the system that owns it, verify it still says
what the index thinks, re-score on the fetched bytes — and P6 wires it into
`answer` by default, making it load-bearing for the first time
([SR-REFER](records/0127_refer-plane.md) accepted,
[R4 PASS](work/regression/2026-08-20-refer-plane-r4/VERDICT.md)). M5 adds
`fux hooks` and a merge driver for the committed index, but
[R5 FAIL](work/regression/2026-08-20-r5-hook-latency/VERDICT.md) (44.4 s at
100 000 documents against a 1 s bound) and
[R6 INCONCLUSIVE](work/regression/2026-08-20-r6-merge-driver/VERDICT.md) mean
[SR-MAINTENANCE](records/0129_hooks.md) stays **proposed, not accepted** —
the hook ships, its accept gate has not cleared. Delta ingest reuses
extraction for byte-unchanged documents (22.7×–26.4× measured, byte-identical
to a full run). Only prose files are indexed by default now — a 14 % non-prose
slice this repo carried silently is excluded
([SR-TYPES](records/0128_types-list.md)) — and L5's hashed-meta rule moved
from ingest to `write_index`, so it can no longer be skipped by a caller that
bypasses ingest.

**Three breaking changes**, each with a stated migration below: `answer
--json`'s `"source"` key now branches on refer vs index; a non-git record with
no stated `meta` is refused at write time instead of defaulted; and the
prose-only filter changes `df` for every surviving document, so rankings
shift (`fux ingest` to migrate; not claimed to improve, and unmeasured either
way).

### Added

- **`hashed` records now show a real title when their source's bytes are
  reachable, and a labelled hash — never a bare, indistinguishable-from-
  working one — when they are not** (PRIORITY.md P5, 2026-08-21,
  `meta-privacy.compare.md` reopened). Ingest already holds a non-git
  document's bytes before writing its record, so it now also writes the
  title to a new local, gitignored, content-addressed cache
  (`.fux/runtime/display-cache/`) before the record is allowed to commit —
  `store/writer.py` refuses a `hashed` record with no cache entry for its
  `sha`. `ask`/`find`/`answer` (text and `--json`) resolve through it. The
  committed record is unchanged — still `title_h` only — and so is ranking:
  the differential law is untouched, since `rank()` never consults the
  cache. Two of the row's three sub-questions were also decided: term-hash
  salting was researched and **not built** (a committed salt is not a salt);
  `code` (the dense embedding) **stays** on hashed records despite a
  demonstrated inversion risk, traded against `--hybrid`'s ranking quality,
  documented rather than closed. The third (`loc`/`id`) turned out to need
  no decision — the refer plane fetches through `loc` directly, and it is
  already committed in plaintext via the separate URL source list, so
  hashing it would cost function for no privacy gained.
- **The `PreToolUse` write lock is per-asset, not repo-wide.** Two Claude
  sessions editing different files now run in parallel; only a genuine
  same-file conflict is denied (`.claude/hooks/session-lock.sh`).
- **The prediction series is measured again** — R4, R5 and R6 all ran on
  2026-08-20, against thresholds frozen and committed first.
  **[R4 PASS](work/regression/2026-08-20-refer-plane-r4/VERDICT.md)** ·
  **[R5 FAIL](work/regression/2026-08-20-r5-hook-latency/VERDICT.md)** ·
  **[R6 INCONCLUSIVE](work/regression/2026-08-20-r6-merge-driver/VERDICT.md)**.
- **`fux hooks` has a measured ceiling.** A 20-document commit re-indexes in
  **0.651 s at 1 000 documents** and **44.4 s at 100 000** — the hook is
  automatic on a small repository and not on a large one. Nothing was changed
  to make that number better; what changed is that it is now written down, with
  an attribution showing two O(corpus) passes are the whole cost.
- **`tools/refer-bench/` and `tools/maintenance-bench/attribute.py`** — the R4
  harness (a real loopback HTTP server behind the *shipped* consumer fetcher)
  and the cost attribution that turns "it is slow" into "here is where."

- **Delta ingest — unchanged documents keep their extraction** (SR-INGEST
  decision 1b). A filed [cost profile](work/regression/2026-08-20-ingest-cost-profile/report.md)
  put **92 % of a full ingest inside the dense embedding**, so a document whose
  content `sha` is unchanged now keeps its `title`, `phrases`, `terms`, `wlen`
  and `code`. **Edges still re-resolve on every run** — they are corpus-wide,
  and skipping them would leave a link dangling forever with nothing to notice.
  Measured **22.7× at 1 000 documents and 26.4× at 5 000, byte-identical** to a
  full run.
- **`fux ingest --full`** — re-extract every document regardless. It is the
  complete term-hash collision check, and the way to retro-fit `code` after an
  embedding bundle becomes available; both are consequences of the reuse and
  are recorded in SR-INGEST rather than left to be discovered.
- The ingest summary now reports what was carried forward:
  `ingested 3 docs (1 changed, 2 carried forward), 2 skipped, 1 shards written`.

- **A TTL-bounded local fetch cache for the refer plane** (W-60,
  [SR-REFER](records/0127_refer-plane.md) 5a-5c). `cache_ttl_seconds`
  (**default 0 — off**) and `no_cache` on the freshness policy; entries live in
  the gitignored `.fux/runtime/fetch-cache/`. Motivated by rate limits rather
  than latency: an agent asking ten questions about one runbook must not fetch
  it ten times, because at enterprise scale that is throttling, not slowness.
- **A fourth freshness verdict, `cached`**, carrying `age_seconds`. It is
  **never folded into `current`** — "we looked recently" is a different claim
  from "we just looked", and it still records whether the cached bytes matched
  the index.

- **`fux hooks` — the maintenance plane** (M5,
  [SR-MAINTENANCE](records/0129_hooks.md), **proposed, not accepted**).
  Installs `post-commit` / `post-merge` / `post-checkout` and registers a merge
  driver for `.fux/index/*.jsonl`. Every hook is best-effort and **cannot block
  a commit**; installation **refuses rather than overwrites** a hook fux did
  not write, and `--uninstall` removes only what it wrote.
- **`fux-merge-index` — a line-wise merge driver for the committed index.**
  Two people working at once no longer get a textual conflict in a
  machine-written file: it resolves last-writer-wins on `(ver, sha)`, sorts its
  output by id so two machines merge to the same bytes, and **refuses** on the
  four cases it cannot resolve — writing ordinary conflict markers that keep
  both sides and naming the fix. It never picks a side.
  A separate console script rather than a `fux` verb, because git invokes a
  merge driver as a bare command with positional arguments.

### Fixed

- **Six reproduced defects** (PRIORITY.md P4, 2026-08-21), each with a
  regression test:
  - The merge driver's modify/modify branch relied solely on `ver`, so a
    document whose `ver` was not bumped on the changed side read as an
    unresolvable conflict even when the other side provably touched nothing.
    Now checks each side against the ancestor first, matching the delete
    branch's existing logic.
  - `ingest/parse.py` decoded content as plain `"utf-8"`, leaving a leading
    BOM as a literal `U+FEFF` character instead of stripping it. Now decodes
    `"utf-8-sig"`.
  - `ingest/gitdir.py` built `rel_path` from the filesystem with no Unicode
    normalization — a path can come back NFD even when committed as NFC.
    Now NFC-normalized, matching `parse.py`'s existing content normalization.
  - `query/scan.py`'s `df` count was inflated by a 16-hex term hash quoted
    outside `terms` (a title, id, or sha) — the substring prefilter that
    finds candidate lines is deliberately imprecise, but `df` leaked that
    imprecision. Now counted from the parsed record's actual `terms` keys.
  - `mergedriver.py`, `sources.py` and `graph/plane.py` all used
    `write_text`'s platform-default newline translation, which would commit
    CRLF on Windows and LF everywhere else. All three now write with
    `newline="\n"` explicitly.
  - `refer/fetchcache.py`'s TTL cache was unbounded on disk — an entry only
    stopped counting toward `get()` once its TTL passed, and nothing ever
    deleted the file. Now size-capped (`max_bytes`, default 500 MB) with
    oldest-first eviction.

### Changed — **breaking**

- **`answer` fetches, verifies and re-scores by default now** (PRIORITY.md
  P6, 2026-08-21, SR-REFER **accepted** — R4 passed, and the plane is now
  load-bearing in a shipped verb; SR-ANSWER **accepted**). A citation whose
  source can be reached returns a verbatim passage re-scored on the fetched
  bytes, cited with a fresh `sha` and a freshness verdict — `"source":
  "refer"` in `--json`. `--no-refer` keeps the exact M2 shape
  (`"source": "index"`, `{title, phrases}`). **Breaking for a caller that
  assumed `--json`'s `"source"` was always `"index"`, or that `"answer"`
  was always `{title, phrases}`** — W-48 (2026-08-20) put `"source"` on
  every branch specifically so this could be detected, not silently missed.
  `ask`/`find` and ranking are untouched — only `answer`, and only how its
  winning citation is produced.
- **L5 is enforced when a record is written, not when it is ingested.** The
  hashed-meta rule for non-git sources moved from `ingest/run.py` — one caller
  — into `write_index`, the only way bytes reach a committed shard. A non-git
  record must now **state** `meta` (a missing value is refused rather than
  defaulted), and a `hashed` record carrying `title` or `phrases` is rejected.
  **Breaking only for a caller writing records directly**; every record this
  repo already holds complied, so nothing changed on disk.

- **Only prose files are indexed now** ([SR-TYPES](records/0128_types-list.md),
  W-55 verdict G). The git-dir walker had **no file-type filter at all**:
  anything UTF-8-decodable was a document, which on this repo meant 21 of 150
  records (14 %, and 15 % of the tokens) were `.json`, `.svg`, `.sh`, `.py` or
  `.mermaid`. A compiled-in allowlist — `*.md`, `*.markdown`, `*.txt`, `*.rst`,
  `*.adoc`, `*.org` — now applies, replaceable by committing
  `.fux/sources/types`. **Absent means the default**, never "index everything"
  and never "index nothing".
  **Migration:** re-run `fux ingest`. Records for non-prose files disappear and
  `df` moves for every surviving document, so **this changes rankings** — it is
  not claimed to improve them, and nothing has measured it.
- **`.fux/sources/dirs` accepts `!` exclusions**
  ([SR-DIR-LIST](records/0120_dir-list.md), W-45 verdict E).
  `!work/regression/*/evidence` removes matching paths, and everything beneath
  them, from every included root. Order-independent, no un-exclude, no
  attributes. `*` does not cross a `/`; `**` is the any-depth form.
  Not breaking on its own — a file with no `!` line behaves exactly as before.
- **`fux ingest --list-skipped` names the reason for every rejection** —
  `not an indexed file type`, or `excluded by !<pattern>` with the pattern that
  did it. A filter nobody can see is what both of these items were opened
  about.
- **`fux setup` writes `.fux/sources/types`** with the default spelled out in
  comments, so a consumer can see what fux considers a document without reading
  its source.

### Added

- **The refer plane's core — `fux.refer`** (M4,
  [SR-REFER](records/0127_refer-plane.md), **proposed, not accepted**).
  Fetches a cited document from the system that owns it, verifies it still says
  what the index thinks, cuts it into heading-delimited passages, re-scores
  those against the query, and assembles as much as fits a **byte** budget.
  **No verb exposes it yet** — its gate has not run, and wiring an unmeasured
  plane into the default surface is how it becomes load-bearing before anyone
  knows whether it works.
- **Fux still does not fetch.** The plane reuses the consumer-owned fetcher
  contract ([SR-FETCHER](records/0117_fetcher.md)) rather than adding a
  second fetch mechanism; the callable is injected, never imported, and an AST
  test asserts no network import anywhere in the plane.
- **Freshness is verified by content, not by age.** `never` (the default,
  offline) and `always`, plus a timeout — and a three-state verdict
  `current`/`stale`/`unverified`, so nothing can collapse "we did not look"
  into "we looked and it was fine". **`max_age_seconds` was deliberately not
  built**: the committed record carries no ingest time, so the bound could not
  have been honoured, and a knob that silently does nothing is worse than a
  missing one.
- **ARC content cache**, keyed `(loc, sha)` and byte-budgeted. The content
  address is in the key, so a hit is byte-identical to what a fetch would have
  returned — asserted by a differential test.

- **The graph lane — `fux explain`, `fux graph`, `fux path`** (M3,
  [SR-GRAPH](records/0126_graph.md)). The `ref`/`tag`/`code` edges
  ingest has extracted since M1 become answerable. `explain` lists a
  document's outbound edges and its community; `graph` returns the
  neighbourhood around a query's best answers, PPR-expanded; `path` returns
  every simple directed route between two documents with a reliability that
  decays per hop. Flat verbs, as ever — `fux graph path` would have been the
  first subcommand tree on this surface.
- **Communities, assigned deterministically and without a seed.** Label
  propagation with sorted visit order, ties broken on the smallest label, and
  a fixed sweep cap — there is no `random` import in the module and a test
  parses its AST to keep it that way. A fixed seed would have been the weaker
  guarantee. Labels are canonicalised (`c0`, `c1`, …) by size, so adding one
  document cannot rename a partition that did not change.
- **`.fux/runtime/graph.json`** — the derived graph plane, written by
  `fux build`, gitignored, and part of the byte-identity assertion. Communities
  are derived rather than committed because a community label is *global*:
  committing it would turn a one-file commit into a corpus-wide diff.

### Changed

- **`ask` is untouched, and now asserted so from the graph fixture too.** The
  graph plane is built by the same `fux build` as the accelerator, so a leak
  into the lexical path is a live possibility rather than a theoretical one.

### Fixed

- **`fux ask --hybrid` no longer crashes on a source install.** `get_model()`
  returns `None` when the embedding bundle is not shipped, and `None.embed(...)`
  raised an `AttributeError` that the guard written for exactly this case did
  not list — so a documented, supported state printed a traceback instead of
  falling back. It now returns the lexical answer at exit 0. Fixed with an
  explicit `None` check rather than a wider `except`, so a real bug inside
  `embed()` still propagates; both halves are asserted
  ([SR-CLI](records/0101_cli-surface.md)).

### Changed

- **`ask --json --explain` now carries `"path"`** — `"accelerator"`, `"scan"`
  or `"hybrid"`. `--explain` was text-only, so the one fact worth logging about
  a slow query was the one a caller could not read. The key appears only when
  `--explain` is passed, so the default payload is unchanged
  ([SR-ASK](records/0103_ask.md)).
- **`answer --json` now carries `"source"` on the no-match branch too.**
  [SR-ANSWER](records/0105_answer.md) tells callers to key on `"source"` to
  detect the M4 upgrade, so its absence on one branch was a trap. The payload
  is now `{"answer": null, "citation": null, "source": "index"}`.

## [0.33.0] - 2026-08-19

**The sources rewrite — what fux indexes becomes two committed files, and the
URL path works for the first time.**

Five defects closed. Every one of them was **latent**: this repo does not use
URL ingest, so nothing in its own corpus reached four of the five, and a green
test suite said nothing about them. They were fixed anyway, because the first
consumer hits all five on day one, on the documented default. The evidence is
[`work/regression/2026-08-19-w54/`](work/regression/2026-08-19-w54/report.md),
a fixture that builds a repo from nothing and runs the whole path offline.

**Two breaking changes**, both retired config keys, both a stopped run with the
migration in the message. Both are cheapest now.

**The honest limits.** Nothing here exercises real HTTP — `http.py`'s transport
is covered by reading it, and the first consumer to point `fetch=http` at a
real server is its first real exercise. The `archived=` declaration parses and
is deliberately **not read**: changing what a verb says about a document needs
an instrument, and that instrument does not exist yet. And seven documents
measures nothing about speed, so this release reports no new timing.

### Added

- **`fux setup`** — writes the files you own into your repo, **write-if-missing**:
  `fux.toml`, `.fux/sources/dirs`, `.fux/sources/urls`, and both fetchers
  ([SR-DOTFUX](records/0102_fux-directory.md) decision 6). Optional, explicit,
  once per repo, and a second run is a no-op that never clobbers an edit. It is
  the only verb that may run before a repo root exists — it is what creates one.
- **Two fetchers ship in the wheel**, `http.py` and `cdp.py`
  ([SR-HTTP-FETCHER](records/0119_http-fetcher.md),
  [SR-CDP-FETCHER](records/0118_cdp-fetcher.md)). They travel as **package
  data with an extension Python cannot import**, so fux copies them and never
  imports them — the adapter cap is structural, not remembered. `http.py` is a
  plain stdlib GET and is what a URL with no `fetch=` attribute gets; it never
  escalates to the browser on its own.
- **`fux url`** — records a URL in the committed list, writing **every**
  attribute explicitly ([SR-URL-LIST](records/0116_url-list.md) decisions 12
  and 13). Flags, not a subcommand tree: `--cdp`/`--http`, `--plain`/`--hashed`,
  `--remove`; no argument lists what the loader sees. **It never fetches** —
  `fux ingest --refresh-urls` remains the only networked path in the engine.
- **Per-URL attributes in `.fux/sources/urls`** — `fetch=http|cdp` routes to a
  file under `.fux/fetchers/`, `meta=plain|hashed` decides whether the index may
  hold readable display text for that one document. A line beats the source-wide
  `[sources.url]` setting, which beats the built-in default. `meta` only ever
  *loosens* per line: there is deliberately no way to make one URL stricter.
- **`.fux/sources/dirs`** — the committed directory list, on the same grammar
  ([SR-DIR-LIST](records/0120_dir-list.md)). A line may declare
  `archived=true`; it is parsed and validated today and **not yet read** — the
  marker in results is gated on a pre-registered query set.

### Changed

**Two breaking changes, both retired keys, both a stopped run with
instructions.** A retired key that silently does nothing is worse than one that
stops the run — here "silently does nothing" would mean indexing the wrong
corpus or fetching through the wrong file.

- **BREAKING — `[sources] dirs` is retired.** The corpus moves to
  `.fux/sources/dirs`, one entry per line, so a 5 000-entry list diffs and
  merges line by line instead of colliding in a single TOML array.

  ```diff
  # fux.toml
   [sources]
  -dirs = ["docs", "work", "README.md", "archive/v0.26-docs"]

  # .fux/sources/dirs
  +docs
  +work
  +README.md
  +archive/v0.26-docs        archived=true
  ```

  `[sources] dirs_file` points elsewhere if you want. **The key errors whatever
  its value** — `dirs = []` stops the run exactly as a populated list does.

- **BREAKING — `[sources.url] middleware` is retired, renamed `fetcher`**, and
  `.fux/middleware/` is `.fux/fetchers/`
  ([SR-FETCHER](records/0117_fetcher.md)). Middleware names a pattern whose
  defining property is composition, and nothing here composes: one file, one
  `fetch(url)`, exactly one running per URL.

  ```diff
   [sources.url]
  -middleware = ".fux/middleware/cdp.py"
  +fetcher    = ".fux/fetchers/cdp.py"
  ```

  ```console
  $ git mv .fux/middleware .fux/fetchers
  ```

- **`[sources.url] fetcher` defaults to `.fux/fetchers/http.py`** (was
  `cdp.py`), because a URL line with no `fetch=` means `fetch=http`. The key
  now carries two things: the file an unattributed line uses, **and** the
  directory a `fetch=<name>` resolves in.
- **`fux.toml` has no required keys.** It holds policy; the source lists hold
  the corpus.
- **SR-DOTFUX, SR-URL-INGEST and SR-CONFIG are ratified** (Arpit,
  2026-08-19), closing W-31. Their `⏳ proposed` qualifiers in the `0.32.0`
  entry below are stale as of that date; the register
  ([`records/README.md`](records/README.md)) is the live statement of every
  record's status, and released entries are left as written.

### Fixed

- **`meta = "hashed"` produced an index no `fux build` would accept** — and it
  is the default, and an L5 safety default. A bare 16-hex `title_h` is a quoted
  16-hex token outside `terms`, which the build refuses because the scan would
  count it toward that term's `df` and the accelerator would not. Any corpus
  with one hashed URL record was stuck on the reference scan permanently: 27.2 ms
  becomes 4 248.8 ms at RFC scale. **Fixed in the field's shape, not the check** —
  `title_h` is now `"h:" + <hash>` and the two paths agree by construction.
  **Migration: re-run `fux ingest --refresh-urls`.** No `_format` or `analyzer`
  bump ([SR-INDEX-LIFECYCLE](records/0108_index-lifecycle.md) decision 9), and
  the build's refusal names the migration.
- **A URL fragment was silently truncated.** `#` began a comment anywhere on a
  line, so `https://x/page#section` loaded as `https://x/page`, two URLs
  differing only by fragment collapsed into one, and **a document disappeared
  with no error**. `#` now begins a comment only at the start of a line or after
  whitespace.
- **`[sources.url] fetcher`'s default named a file that did not exist.** Nothing
  in fux wrote it and nothing shipped it, so a consumer following the documented
  default got *"fetcher not found"*. `fux setup` writes it.
- **Two docstrings claimed fux shipped a fetcher when it did not.** Now true.

## [0.32.0] - 2026-08-12

**M2 — the query engine gets fast without changing a single answer.**

Warm `ask` is measured at a **worst-case p95 of 27.2 ms on 8 870 RFC
documents**, against a pre-registered 150 ms bar, where the reference scan
takes 4 248.8 ms (prediction **R3 PASS**). The speed comes from a *derived*
index that is never committed, and it is bound by a **differential law**: its
results are byte-identical to the scan's, asserted over 6 088 comparisons on
two corpora, every one of the playground's 50 graded goldens, and the shipped
CLI itself.

Also in this release: the `.fux/` directory becomes a declared layout, URL
ingestion arrives through consumer-owned fetcher, the demo corpus moves to
a graded sibling repo, and **R2 closes at 3/3**.

Versions 0.31.x were never published; their work ships here.

### Added

- **The derived T1 accelerator — M2** ([SR-T1-ACCELERATOR](archive/adr/0005_derived-accelerator.md),
  ⏳ proposed). Term-major blocked postings and a fixed-width binary offset
  table under `.fux/runtime/` (derived, gitignored, `CACHEDIR.TAG`-tagged),
  rebuilt from the committed shards alone. **Prediction R3 PASS:** warm `ask`
  worst-case p95 **27.2 ms** against a 150 ms bar on 8 870 RFC documents,
  where the reference scan takes 4 248.8 ms.
  - **The differential law.** Accelerator results are **byte-identical** to
    the reference scan — asserted over 5 536 generated comparisons and every
    one of the playground's 50 graded goldens, in both skipping modes, at four
    `top` values. `ask --scan` forces the reference path.
  - Block skipping is **loss-free by construction**: terms open rarest-first
    and unopened blocks are skipped only when their combined upper bound
    provably cannot reach the k-th best score. Never by dropping postings —
    pruning stays forbidden (P1-RERUN).
- **`fux build`** — rebuild the derived accelerator from the committed index.
  `fux ingest` now builds it too; `--no-accelerator` opts out.
- **`fux find`** (ranked locations, one per line) and **`fux answer`** (the
  single best answer the index can give). `answer` is deliberately bounded to
  the index's own structure and says so — passage-level answers arrive with
  the refer plane at M4, upgrading the verb rather than adding one.
- **`fux doctor`** reports the accelerator: missing or stale is a **warning**
  (it is disposable and `ask` is correct without it); tracked-by-git is an
  error.
- **The dense lane and RRF fusion (k=60), behind `ask --hybrid`, OFF by
  default.** Int-cached Hamming over the FuxVec `code` property M1 has been
  writing; RRF ported from `archive/v0.26/` with its tests. The default is a
  measurement, not caution: on the playground's graded goldens hybrid closes
  three named gaps and breaks nine passing queries — **net −6**, including
  every no-answer query. Flipping it needs new evidence and a separate
  sign-off.

### Fixed

- `fux doctor` could crash on Windows consoles (`cp1252`) when a check
  **failed** — two failure-branch messages carried em-dashes. The existing
  ASCII guard only ever exercised the healthy path; a new test drives every
  branch.

### Changed

- **The frozen v0.19–0.26 documentation set is now an indexed source.**
  `archive/v0.26-docs` joined `fux.toml`'s `[sources].dirs` (W-42). No engine
  code changed. This closes **prediction R2 at 3/3 PASS** — the third frozen
  question's citation target had never been reachable from configured
  sources. Frozen means never *edited*; it does not mean unindexed.
  - The committed index grows **+45.1 %** (942,479 → 1,367,888 raw bytes;
    416,899 → 602,825 zlib) for +34 documents. Determinism holds: double
    ingest is byte-identical.
  - **Known consequence:** retired v0.26 documents now rank for questions
    about the *current* engine — *"what is the ingest cache"* returns five
    archived results describing a deleted subsystem. Measured post-hoc,
    filed as [W-44](work/open/W-44-archived-content-signalling.md), and
    deliberately **not** fixed here; the mechanism is Arpit's call.
    Full run: [`work/regression/2026-08-12-r2-close/`](work/regression/2026-08-12-r2-close/report.md).

### Removed

- **`examples/` is gone** ([SETUP-PLAYGROUND](work/setup/fux-playground.md)).
  The 20-document AcmePay fixture that shipped inside this repository was
  deleted. It contaminated the engine's own dogfood corpus, it entered the
  sdist by accident of layout rather than by decision, and — having no
  expected answers — it could not notice a ranking regression.

### Added

- **A graded corpus, in a sibling repository** (`fux-playground`,
  [SETUP-PLAYGROUND](work/setup/fux-playground.md)). Ten
  internal-developer-platform documents, **fifty golden queries asserting
  ranks** across seven hazard classes (supersession, near-duplicate,
  attractor, collision, precision, edges, no-answer), and ten URLs that
  exercise the CDP fetcher. Its committed index holds **file documents
  only**, and a staleness guard re-ingests and asserts `git diff --exit-code`
  on every run — the byte-determinism law, checked continuously. Goldens are
  hand-written from the corpus and never derived from engine output; there is
  no `--update-goldens` flag. Standing status: 41 pass, 9 named engine gaps.
  README reading-order item 5 now points there.
- **The `.fux/` directory is a declared layout**
  ([SR-DOTFUX](archive/adr/0011_fux-dir-layout.md), ⏳ proposed): every child is
  committed (`index/`, `sources/`, `fetchers/`) or derived (`runtime/`,
  `cache/`). Ingest writes a self-describing `.fux/README.md` and a narrow
  `.fux/.gitignore` — derived names only, **never `*`** — both
  write-if-missing so consumer edits survive. `derived_dir()` drops a
  spec-exact `CACHEDIR.TAG` for M2/M4 to use. `fux doctor` gains two checks:
  the committed index must not be git-ignored (error), and undeclared
  top-level `.fux/` entries are reported (warning).
- **URL source via consumer-owned fetcher**
  ([SR-URL-INGEST](archive/adr/0010_url-source-consumer-middleware.md), ⏳ proposed):
  `fux.toml [sources.url]` names a consumer-editable Python file
  (`fetcher`, `urls_file`, `meta`); `fux ingest --refresh-urls` — the only
  networked ingest path — calls its `fetch(url) -> str` and indexes the
  result as `src:"url"`. Hashed meta by default (`title_h`, the non-git
  law's first exercise); plain ingest stays offline and carries `url:`
  records forward byte-identically; a failed fetch keeps the prior record.
  Absolute http(s) links now resolve to in-corpus `url:` docs as `ref`
  edges. Core gains no network code and no dependencies.
- `.fux/fetchers/cdp.py` — the shipped, consumer-owned template: Chrome
  DevTools Protocol capture over a hand-rolled RFC 6455 WebSocket +
  deterministic HTML→markdown, pure stdlib, ported from the archived
  v0.26 `render = "cdp"` path (never bundles a browser). Its constants are
  defaults, overridable from `fux.toml` via the new optional
  `configure(config)` hook.

### Changed

- The URL list moved out of `fux.toml` into **`.fux/sources/urls`** — one URL
  per line, `#` comments allowed, deduped and sorted before fetching, with
  line-numbered errors on a bad scheme. An inline `urls = [...]` key is now a
  hard error pointing at the file. The fetcher moved from the repo root to
  `.fux/fetchers/cdp.py`. Both are breaking changes against an unreleased,
  hours-old surface, so no shims exist ([SR-DOTFUX](archive/adr/0011_fux-dir-layout.md)).
- Fetcher tunables now live in an optional **`[sources.url.config]`** table
  passed verbatim to `configure(config)`. Fux validates only that it is a
  table and never reads a key inside it — the PEP 518 `[tool.*]` discipline,
  which keeps one fetcher's vocabulary out of fux's config schema.
- The repo's own `.gitignore` no longer blanket-ignores `.fux/*`; the narrow
  `.fux/.gitignore` carries the derived names instead.

## [0.30.0] - 2026-08-11

M0 scaffold + M1 T0 slice — the first real code of the v0.30 rebuild.
[SR-RECORD](archive/adr/0004_index-format.md); R1 PASS, R2 2/3 PASS.

### Added

- `src/fux/` package scaffold: `store/`, `derive/` (M2 stub), `query/`,
  `ingest/`, `refer/` (M4 stub), `cli.py`, `errors.py`, `config.py`,
  `doctor.py`.
- `fux --version`, `fux doctor` (python version, repo root, `.fux/` writable).
- Canonical committed store (`store/`): sharded doc-major JSONL under
  `.fux/index/`, exactly per [`work/compare/index-format.compare.md`](work/compare/index-format.compare.md) §5/§7.
- Git-dir ingest adapter and `extracted`-mode extractors (tokenizer, heading
  phrases, `ref`/`tag`/`code` edges, FuxVec `code`); `fux ingest` is
  incremental by sha.
- `fux ask`: bytes-level prefilter scan over shards + ported BM25F, with
  citations.
- [`work/adr/0004_index-format.md`](archive/adr/0004_index-format.md) — the
  schema, canonical rules, unicode policy, and analyzer version frozen.
