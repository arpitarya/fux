# ADRs — the decision records

**How to use this file.** This is the register: the naming convention, the
ownership table, and the rules every record obeys. Read it before writing an
ADR, before citing one, and before adding a module to `src/`.

One ADR per completed feature or ruled measurement. Every ADR carries a
reference. Every record is **cited by name** in prose.

## Two directories, two states

**This file is the register for both.** A record's directory *is* its state:

| state | directory | may back a live claim? |
|---|---|---|
| **live** | `docs/adr/` (here) | yes |
| **superseded** | [`archive/adr/`](../../archive/adr/README.md) | **no** — archive is not evidence |

**The v0.30 set finished migrating into `docs/adr/` on 2026-08-18–19** — every
live record is here now, and `work/adr/` (the transient superseded-pending tier
the migration passed through) no longer exists. A record moves straight from
`docs/adr/` to `archive/adr/` **in the same change that accepts its
successor** — never before, so no claim is ever left ungrounded. New records
are written here, from [`TEMPLATE.md`](TEMPLATE.md).

---

## The convention

**Path.** `docs/adr/000N_<short-name>.md`, numbered sequentially. The number is
a filename ordinal, not an identity — **it is scoped to its directory and its
generation**, and it restarts when a record set is replaced. Two records can
carry `0001` at the same time and nothing breaks, because nothing identifies a
record by number.

**Frontmatter is a fixed six-key block**, and it is checked. `type` · `name` ·
`title` · `description` · `status` · `timestamp`, in that order; **any value
containing `: ` must be quoted**, `name`/`status` must match the body's
`**Name:**` and `**Status:**` lines, and the title must carry both the name and
the file number. `tests/test_adr_frontmatter.py` enforces every one of those —
it exists because frontmatter broke twice on 2026-08-18, once from an unquoted
colon that only strict YAML rejected, and once when a global rename substituted
a name for the number inside eight titles.

**Cite by NAME, never by number.** In prose, always `ADR-RECORD`, never
"ADR-0004". Numbers are for the historical record only — once a record is
superseded and moves to [`archive/adr/`](../../archive/adr/README.md),
its number is how the archive maps it to its successor. A live doc that says
"ADR-0004" is a defect; fix it on contact.

**Two sections, and they are for different readers.**

- **§1 — For humans.** One screen, maximum. Includes a diagram: a Mermaid
  block **and** a hand-paired ASCII twin. **Both are updated together whenever
  either changes** — a Mermaid block that has drifted from its ASCII twin is
  the same defect as a stale diagram.

  §1 may also carry two optional sections, in this order after the diagram:
  **Examples** — real, capture-copied, two or three at most — and **Charts**,
  whose default is *none*. Add a chart only when a shape argues better than a
  sentence; one measure per chart, every number measured or computed, and the
  same both-formats rule as the diagram. Both sections are deleted, not left
  empty, when they do not apply.

  **The ASCII twin is collapsed**, inside a `<details>` block with a
  `<summary>` naming it. The Mermaid renders on GitHub and is what a human
  sees; the twin is there for terminals, diffs, and any reader without a
  renderer, and it should not cost a screen to scroll past. Collapsing it is
  what keeps §1 to one screen while keeping the twin mandatory. Copy the shape
  from [`TEMPLATE.md`](TEMPLATE.md) — a blank line after `</summary>` is
  required, or the fenced block will not render.
- **§2 — For agents.** Context · decision · consequences · alternatives
  considered · reference · veto condition.

**The reference is grounded.** A paper, a live doc, code, or measured evidence
under [`work/regression/`](../../work/regression/README.md). **Never an archived
doc** — nothing guarantees an archived file was not overwritten after the fact
(see [`archive/README.md`](../../archive/README.md)). An archived doc
may be *named* in a record; it may not *back* a live claim.

**The veto condition is a condition, not an event.** Write what would have to
become **true** for the decision to reopen, phrased so someone can check it
today with a command or a look at the code. "Revisit when we hit scale" is not
a veto condition; "reopen if p95 on a ≥100k-doc corpus exceeds 150 ms" is.
A veto written as an event to await never fires, because nobody is waiting.

**A record that restates a cross-cutting principle is a bug.** The project's
foundational rules live in exactly one place — **ADR-LAWS**. Every other record
references it by name and cites the law's number. Do not paraphrase a law into
a record; the paraphrase is what drifts.

**Records are kept current by a check, not by good intentions.** `CLAUDE.md`
§Law zero is the rule; these are the two places it is enforced:

| where | what it does |
|---|---|
| `tests/test_adr_freshness.py` | runs in CI (`pytest -q tests`, with `fetch-depth: 0` so the runner can see the history it audits). Fails any commit since the rule landed that changed an ADR-owned component without touching **that component's owning record specifically** — touching some other record does not count — and fails a working tree that is mid-violation |
| [`scripts/adr-guard.sh`](../../scripts/adr-guard.sh) | the same check as a `commit-msg` hook (not `pre-commit` — it has to read the message, which does not exist yet at `pre-commit` time): `ln -sf ../../scripts/adr-guard.sh .git/hooks/commit-msg` |

**The escape hatch is a line reading exactly `no ADR affected` in the commit
message** (or `[no-adr]`), on its own line. It is not a silent skip — it is a
claim, in git history, under your name, that you checked and there was nothing
to update. That is exactly what the rule asks for.

**The baseline is self-bootstrapping**: the check applies from the commit that
added it, never retroactively. After a bulk review you can move the baseline
forward by writing a commit sha into `docs/adr/RULE-SINCE`.

**Superseding.** A superseded record moves to `archive/adr/`, and
`archive/adr/README.md` maps its old number to its live successor. The
archive-is-not-evidence rule applies to it from that moment.

Start from [`TEMPLATE.md`](TEMPLATE.md).

---

## The register — the new set (`docs/adr/`)

**Numbering restarted at 0001** with ADR-LAWS (2026-08-18), because the v0.30
set is being replaced wholesale. This is the third restart: the v0.26 line ran
0001–0015, the v0.30 line restarted at 0001 on 2026-08-09, and this one starts
again here.

| # | name | title | status | built |
|---|------|-------|--------|-------|
| [0001](0001_laws.md) | **ADR-LAWS** | The non-negotiable constraints have exactly one home, and records cite it | accepted | yes |
| [0002](0002_cli-surface.md) | **ADR-CLI** | The command-line surface — six verbs, one boundary, three output modes; every command captured verbatim | accepted | yes |
| [0003](0003_fux-directory.md) | **ADR-DOTFUX** | The `.fux/` directory — every child declared committed or derived; the ignore rule asserted against git | accepted | yes |
| [0004](0004_ask.md) | **ADR-ASK** | The `ask` verb — one scorer, one sort; the path that answers can never change the answer | accepted | yes |
| [0005](0005_find.md) | **ADR-FIND** | The `find` verb — one line per hit, for pipes; a projection of `ask`, not a second strategy | ⏳ proposed | yes |
| [0006](0006_answer.md) | **ADR-ANSWER** | The `answer` verb — the single best answer the index can give, with its ceiling stated in every response | ⏳ proposed | yes |
| [0007](0007_ingest.md) | **ADR-INGEST** | How ingest works — re-extract everything, re-resolve every edge, write only shards whose bytes changed | accepted | yes |
| [0008](0008_url-ingest.md) | **ADR-URL-INGEST** | URL ingestion behaviour — fetching only inside a named fenced path, a failed fetch is a skip not a deletion, de-listing needs no network, and what comes back is normalized | accepted | yes |
| [0009](0009_index-lifecycle.md) | **ADR-INDEX-LIFECYCLE** | Index generation and update — one canonical encoder, write-if-different, a derived plane that refuses to diverge | accepted | yes |
| [0010](0010_index-record.md) | **ADR-RECORD** | One line of the committed index, property by property — including the two that are conditional on privacy | accepted | yes |
| [0011](0011_accelerator.md) | **ADR-T1-ACCELERATOR** | The derived T1 accelerator — disposable, term-major, and forbidden from changing an answer | accepted | yes |
| [0012](0012_ranking.md) | **ADR-RANKING** | How documents are scored and ordered — BM25F, weight-then-saturate once, one scorer and one rounded sort | ⏳ proposed | yes |
| [0013](0013_postings.md) | **ADR-POSTINGS** | The postings in two shapes — doc-major in git for diffs, term-major in the runtime plane for queries | ⏳ proposed | yes |
| [0014](0014_config.md) | **ADR-CONFIG** | `fux.toml` and every property in it — including the one table fux passes through unread | accepted | yes |
| [0015](0015_port-list.md) | **ADR-PORT-LIST** | Port, don't rewrite — nine named modules from the archived engine, each with its tests, and the list is closed | ⏳ proposed | partial |
| [0016](0016_extracted-mode.md) | **ADR-EXTRACTED** | The `extracted` ingest mode — everything taken from the document, nothing invented; the mode every guarantee is stated for | accepted | yes |
| [0017](0017_enriched-mode.md) | **ADR-ENRICHED** | The `enriched` ingest mode — a coding agent as a source, never a step; pinned, graded, and fenced out of the maintenance path | accepted | **no** |
| [0018](0018_url-list.md) | **ADR-URL-LIST** | The committed URL list — one per line so it merges at scale; loader-sorted so config order can never change committed bytes; one grammar, shared with `dirs` | accepted | yes |
| [0019](0019_fetcher.md) | **ADR-FETCHER** | The consumer-owned fetcher — fux never fetches; one fetcher per URL, declared not detected, and nothing composes | accepted | yes |
| [0020](0020_cdp-fetcher.md) | **ADR-CDP-FETCHER** | The browser fetcher — drives your existing Chrome over CDP on a hand-rolled stdlib WebSocket; never escalated to | accepted | yes |
| [0021](0021_http-fetcher.md) | **ADR-HTTP-FETCHER** | The default fetcher — a plain stdlib GET, written into your repo by `fux setup` so core keeps zero network lines and zero network imports | accepted | yes |
| [0023](0023_dir-list.md) | **ADR-DIR-LIST** | The committed directory list — source dirs leave `fux.toml`; a directory may be declared `archived=true`. **The file and the declaration are built; the *signal* is gated on W-44's instrument** (decision 10) | accepted | partial |
| [0024](0024_cachedir-tag.md) | **ADR-CACHEDIR-TAG** | CACHEDIR.TAG marks a derived `.fux/` directory disposable, so backup and archive tools skip it for free | ⏳ proposed | yes |
| [0025](0025_docs-table.md) | **ADR-DOCS-TABLE** | `docs.jsonl` — the docidx-ordered doc table every other derived structure joins against | ⏳ proposed | yes |
| [0026](0026_codes-table.md) | **ADR-CODES-TABLE** | `codes.jsonl` — the dense lane's per-document FuxVec codes, decoded once per process | ⏳ proposed | yes |
| [0027](0027_runtime-manifest.md) | **ADR-RUNTIME-MANIFEST** | `manifest.json` — the per-shard content-sha fingerprint that detects a stale accelerator | ⏳ proposed | yes |
| [0028](0028_runtime-stamp.md) | **ADR-RUNTIME-STAMP** | `stamp.json` — the cheap, non-reproducible size/mtime pre-check ahead of the manifest's real one | ⏳ proposed | yes |
| [0029](0029_runtime-stats.md) | **ADR-RUNTIME-STATS** | `stats.json` — the corpus-wide `n` and `total_wlen` that BM25F length normalization reads | ⏳ proposed | yes |
| [0030](0030_graph.md) | **ADR-GRAPH** | M3 — `explain`/`graph`/`path`, unseeded label-propagation communities in a derived plane, and PPR-lite with a **lazy** walk | ✅ accepted | yes |
| [0033](0033_hooks.md) | **ADR-MAINTENANCE** | M5 — `post-commit` (never `pre-commit`), the installer that registers the merge driver, and L5 moved into `write_index` where nothing can skip it | ⏳ proposed | partial |
| [0034](0034_merge-driver.md) | **ADR-MERGE-DRIVER** | The committed index merges line by line, last-writer-wins on `(ver, sha)`, refuses rather than guesses — carved out of ADR-MAINTENANCE 2026-08-21 | ⏳ proposed | yes |
| [0032](0032_types-list.md) | **ADR-TYPES** | which files are documents — a compiled-in prose allowlist, replaced (not extended) by `.fux/sources/types`; absent means the default, never "everything" | ✅ accepted | yes |
| [0031](0031_refer-plane.md) | **ADR-REFER** | M4 core — fetch through the *consumer's* fetcher, verify by content sha (there is no recorded ingest time), ARC keyed `(loc, sha)`, and a **byte** budget with a floor | ⏳ proposed | partial |
| [0035](0035_cache.md) | **ADR-CACHE** | The refer plane's two caches — ARC keyed `(loc, sha)` cannot change an answer; the TTL fetch store is opt-in, disk-bounded, and answers `cached`, never `current`. Carved out of ADR-REFER 2026-08-21 | ⏳ proposed | yes |
| 0030+ | — | unwritten | planned | — |

**`status` and `built` are two different questions, and conflating them is how
the `CLAUDE.md` PROPOSED header survived ten days.** `status: accepted` means
**Arpit ratified the decision**. `built` means **the engine does it**. A record
can be accepted and unbuilt — that is a decision made ahead of the code, which
is legitimate and is how ADR-ENRICHED, ADR-HTTP-FETCHER and ADR-DIR-LIST exist
today. What is *not* legitimate is a reader having to open the record to find
out.

**A row with `built: no` or `partial` must be claimed by an open item in
[`work/OPEN-WORK.md`](../../work/OPEN-WORK.md)** — otherwise it is a decision
nobody is going to act on, which is a wish. Today: ADR-ENRICHED → W-38 ·
ADR-URL-LIST, ADR-HTTP-FETCHER, ADR-DIR-LIST → W-54 · ADR-PORT-LIST → W-23/W-24
(its M3 and M4 rows).

**Eight of these are successors, and none has retired its predecessor yet.**
ADR-DOTFUX, ADR-ASK, ADR-INGEST, ADR-URL-INGEST, ADR-INDEX-LIFECYCLE,
ADR-RECORD, ADR-T1-ACCELERATOR and ADR-CONFIG each name what they supersede
(ADR-FIND, ADR-ANSWER, ADR-RANKING and ADR-POSTINGS supersede nothing — those
subjects never had a record), and each is now **accepted** (2026-08-18). **Retirement happens in the change
that accepts them.** One predecessor decision remains unratified —
[W-31](../../work/IMPLEMENTATION.md) *(ratified 2026-08-19)*, the `.fux/` layout and the
URL fetcher; **W-30 closed on 2026-08-19** when Arpit ratified the
ingest-mode naming, which now has its own two records,
[ADR-EXTRACTED](0016_extracted-mode.md) and [ADR-ENRICHED](0017_enriched-mode.md),
both accepted.

**Numbers collide across the two directories, and that is fine.** `0001` here
is ADR-LAWS; `0001` in `work/adr/` is ADR-INGEST, retiring. Nothing reads
a number to identify a record — that is exactly why the cite-by-name rule
exists, and why this restart costs nothing. `tests/test_adr_ownership.py`
enforces uniqueness **within** each directory, not across them.

## The v0.30 set is retired

**All five remaining records were archived on 2026-08-18**, in one change, on
Arpit's instruction — `work/adr/` no longer exists. Their map, with a named
successor for each, is [`archive/adr/README.md`](../../archive/adr/README.md).

Two consequences, recorded rather than left to be discovered:

- **The successors are the records in force.** They hold the components their
  predecessors used to own, and their status moved from ⏳ *proposed* to
  **accepted** — a record cannot own the engine and be a proposal at the same
  time.
- **The ratification items survive.** W-30 and W-31 were never about *which
  record* holds a decision; they are Arpit's calls on the decisions themselves.
  **W-30 closed 2026-08-19** — the ingest-mode naming is ratified and now has
  its own pair of records. **W-31 is still open**: the `.fux/` layout and the
  URL fetcher.

Records that supersede nothing — ADR-FIND, ADR-ANSWER, ADR-RANKING,
ADR-POSTINGS, ADR-PORT-LIST, and the six single-file companion records added
2026-08-19 (ADR-CACHEDIR-TAG, ADR-DOCS-TABLE, ADR-CODES-TABLE,
ADR-RUNTIME-MANIFEST, ADR-RUNTIME-STAMP, ADR-RUNTIME-STATS) — **stay ⏳
proposed**. Nothing forced their hand.

**One accepted record owns nothing, on purpose.** ADR-ENRICHED decides a
contract for a mode that is not built: the name, the boundary that keeps it
outside the maintenance path, and the record shape. Acceptance is not
permission to build it — [W-38](../../work/open/W-38-m8-deferred.md)'s M8 gate
is, and it has not been given.

The v0.26 engine's ADRs 0001–0015 are frozen at
[`archive/v0.26-docs/adr/`](../../archive/v0.26-docs/adr/) and are always cited
as **"archived ADR-NNNN"** with that path — a bare `ADR-<NAME>` in any live doc
means this directory.

---

## Ownership — which record owns which component

**This table is the answer, not a judgement call.** Every component in `src/`
and `tools/` appears here exactly once. A component owned by no record is a
defect, and `tests/test_adr_ownership.py` fails on it.

**Superseded-pending records still own things.** Eight of the owners below live
in `work/adr/`, and they keep their components until a successor takes them —
that transfer happens in the same change that accepts the successor.

**Proposed records declare `Owns (on acceptance)` instead**, and several are
deliberately more specific than a sibling's claim: ADR-RANKING takes
`query/rank.py`, `bm25f.py` and `tokenize.py` out of ADR-ASK's claim on
`src/fux/query/`, and ADR-CONFIG takes `config.py` out of ADR-DOTFUX's. Most
specific wins, exactly as the table already resolves `store/fuxdir.py` against
`store/`. **Nothing changes in the table below until acceptance.**

**Two live carve-outs, both 2026-08-21.** ADR-CACHE takes
`src/fux/refer/arc.py` and `src/fux/refer/fetchcache.py` out of ADR-REFER's
claim on `src/fux/refer/`; `tools/refer-bench/` is deliberately **not** split,
because one harness runs R4 for the whole plane and a component is owned once.
And ADR-MERGE-DRIVER takes
`src/fux/maintain/mergedriver.py` out of ADR-MAINTENANCE's claim on
`src/fux/maintain/`. Unlike the six companion records below, this one **is** in
the table: it is a genuine ownership claim, and the freshness gate has to be
able to name one owner for that file. Its harness is deliberately **not**
split — `tools/maintenance-bench/` runs R5 and R6 from one file, and a
component is owned once.

**Six 2026-08-19 records own nothing at all, on purpose.**
ADR-CACHEDIR-TAG, ADR-DOCS-TABLE, ADR-CODES-TABLE, ADR-RUNTIME-MANIFEST,
ADR-RUNTIME-STAMP and ADR-RUNTIME-STATS each specify one file
[ADR-T1-ACCELERATOR](0011_accelerator.md) already generates from
`src/fux/derive/`. They do not appear in the table below, and never will —
`src/fux/derive/` stays claimed exactly once, by ADR-T1-ACCELERATOR, the same
"most specific wins" rule notwithstanding, because these six are not more
specific ownership claims, they are companion records documenting one file
each of an already-owned component.

**Both change together.** When this table changes, edit
[`../../tests/test_adr_ownership.py`](../../tests/test_adr_ownership.py) in the
same change. They drift silently otherwise — that is the entire reason the
check exists.

A component that genuinely has no decision yet is claimed by an **open work
item** (`W-nn`) instead. The test resolves that id against
[`work/OPEN-WORK.md`](../../work/OPEN-WORK.md); a `W-nn` that has closed fails
the check, so a component cannot stay unowned by accident.

<!-- OWNERSHIP-TABLE-START -->

| component | owner | note |
|---|---|---|
| `src/fux/__init__.py` | ADR-LAWS | package identity and version |
| `src/fux/errors.py` | ADR-LAWS | the single flat `FuxError` — CLAUDE.md §Error contract |
| `src/fux/frontmatter.py` | ADR-LAWS | hand-rolled parser — law L1, `$0` stdlib-only |
| `src/fux/config.py` | ADR-CONFIG | `fux.toml` schema; the opaque `[sources.url.config]` table |
| `src/fux/doctor.py` | ADR-DOTFUX | the committed-vs-derived assertions, incl. `git check-ignore` |
| `src/fux/setup.py` | ADR-DOTFUX | the second scaffolding moment — the consumer-owned files, write-if-missing |
| `src/fux/templates/` | ADR-FETCHER | the two shipped fetchers as package data; **bytes, never imported** |
| `src/fux/sources.py` | ADR-CLI | `add`/`remove`/`update` — the writer for **all three** source lists, and the verbs over them (W-63, 2026-08-21; was ADR-URL-LIST while it was `fux url` alone) |
| `src/fux/cli.py` | ADR-CLI | the flat verb surface, the boundary error contract, and the `--json` shape |
| `src/fux/progress.py` | ADR-CLI | the progress plane on `ingest.run()`/`derive.build()` — stderr-only, TTY-gated, counts not clocks (W-64, 2026-08-21) |
| `src/fux/store/` | ADR-INDEX-LIFECYCLE | canonical bytes, shard addressing, writer/reader, collisions |
| `src/fux/store/fuxdir.py` | ADR-DOTFUX | the `.fux/` layout generator |
| `src/fux/ingest/` | ADR-INGEST | git-dir walk, parse, edges — writes the committed plane |
| `src/fux/ingest/extract.py` | ADR-EXTRACTED | what extraction *promises* — title, phrases, terms, wlen, taken from the bytes and nothing else |
| `src/fux/ingest/sourcelist.py` | ADR-URL-LIST | the one grammar both committed source lists are parsed by |
| `src/fux/ingest/urlsrc.py` | ADR-FETCHER | fux's half of the fetch contract — load, configure, call, normalize |
| `src/fux/derive/` | ADR-T1-ACCELERATOR | T1 build, block maxima, skipping, dense lane |
| `src/fux/query/` | ADR-ASK | BM25F, scan, rank, fusion — bound by the differential law |
| `src/fux/embed/` | ADR-T1-ACCELERATOR | `fuxvec` codes; ships default-off on measured evidence |
| `src/fux/graph/` | ADR-GRAPH | the M3 lane — edges lifted into adjacency, unseeded label-propagation communities, PPR-lite, and the `explain`/`graph`/`path` verbs. Owns `.fux/runtime/graph.json` |
| `src/fux/maintain/` | ADR-MAINTENANCE | the git hooks and their installer. **L5's write-time check is deliberately NOT here** — it lives in `store/writer.py`, because a check beside the thing it guards cannot be skipped |
| `src/fux/maintain/mergedriver.py` | ADR-MERGE-DRIVER | the merge driver itself — carved out of ADR-MAINTENANCE's directory-level claim 2026-08-21, most specific wins |
| `src/fux/refer/` | ADR-REFER | M4's core — source · freshness · ARC · chunk · rescore · assemble. **Imports no transport**: the consumer's fetcher is injected |
| `src/fux/refer/arc.py` | ADR-CACHE | the content cache — carved out of ADR-REFER's directory-level claim 2026-08-21, most specific wins |
| `src/fux/refer/fetchcache.py` | ADR-CACHE | the TTL fetch store — the only place in the engine that reads a wall clock |
| `tools/pruning-eval/` | W-38 | the gate harness and its frozen pre-registrations. **Owned by an open item, not a record** — the verdicts that used it ([P1-GATE](../../work/regression/2026-08-09-pruning-eval/VERDICT.md) · [P1-RERUN](../../work/regression/2026-08-09-pruning-rerun/VERDICT.md)) are no longer ADRs, and W-38 is the only live item permitted to touch pruning work |
| `tools/maintenance-bench/` | ADR-MAINTENANCE | the R5 and R6 harness. **Both ran 2026-08-20** — [R5-HOOK](../../work/regression/2026-08-20-r5-hook-latency/VERDICT.md) FAIL, [R6-MERGE](../../work/regression/2026-08-20-r6-merge-driver/VERDICT.md) INCONCLUSIVE (W-61). **R6's verdict belongs to ADR-MERGE-DRIVER; the harness does not** — one file runs both, and a component is owned once |
| `tools/refer-bench/` | ADR-REFER | the R4 harness and its frozen pre-registration — a real `http.server` behind the **consumer's own generated fetcher**, so the measured path is the shipped one |
| `tools/differential/` | ADR-T1-ACCELERATOR | the differential-law harness and the R3 bench |
| `tools/graph-bench/` | ADR-GRAPH | cost-attribution profiler for the M3 lane — not a gate; feeds `graph-plane-format.compare.md` |

<!-- OWNERSHIP-TABLE-END -->

---

## Path note (2026-08-18)

The `work/` move renamed several directories that older records cite:
`docs/conformance/` → `work/regression/`, `docs/compare/` → `work/compare/`,
`docs/open|proposals|archive/` → `work/…`, and `docs/{WORKLOG,INTERVIEW,
OPEN-WORK,DOC-REGISTRY}.md` → `work/…`. ADR filenames also went from
`000N-name.md` to `000N_name.md`.

A second move the same day took `docs/paper/`, `docs/handoff/` and the two
architecture SVGs into `work/`, and the eight v0.30 records into `work/adr/` as
superseded-pending. **As of that day**, `docs/` held only `GLOSSARY.md`,
`index.md`, and this register with `TEMPLATE.md` and ADR-LAWS — the v0.30
records finished migrating into `docs/adr/` over the following day, and
`work/adr/` no longer exists (see "Two directories, two states" above).

**ADR-LAWS was renumbered `0013` → `0001`** in the same change, opening the new
sequence. Anything written before 2026-08-18 that says "0013" means ADR-LAWS.

**Re-indexed again, later the same day**, to seat the three query verbs at
0004–0006 on Arpit's instruction: `0004_ingest` → **`0007_ingest`**,
`0005_url-ingest` → **`0008_url-ingest`**, `0006_index-lifecycle` →
**`0009_index-lifecycle`**. Nothing else changed — which is the cite-by-name
rule paying for itself twice in one day: a renumber costs three `git mv`s and a
sweep, and no prose moves.

Live references were rewritten in that same change. **Frozen artifacts were
not** — the pre-registrations under `tools/pruning-eval/` and the run reports
under `work/regression/<date>-*/` still carry pre-move paths, by the same rule
that keeps their pre-renumbering ADR ids: a frozen document is never edited.
Where a record quotes a *measured* path (ADR-RECORD's R2 results), the
path was repointed but the measurement is unchanged.

## Renumbering note (2026-08-09)

These files previously carried numbers 0016–0018 continuing the v0.26 sequence;
all live references were rewritten in the same change. Frozen artifacts
intentionally retain the old numbers — their "ADR-0017/0018" means today's
P1-GATE / P1-RERUN.
