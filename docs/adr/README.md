# ADRs — the decision records

**How to use this file.** This is the register: the naming convention, the
record shape, the ownership table, and the rules every record obeys. Read it
before writing an ADR, before citing one, and before adding a module to `src/`.

One ADR per completed feature or ruled measurement. Every ADR carries a
reference. **Every record is cited by NAME in prose, never by number.**

## Two directories, two states

**This file is the register for both.** A record's directory *is* its state:

| state | directory | may back a live claim? |
|---|---|---|
| **live** | `docs/adr/` (here) | yes |
| **superseded or retired** | [`archive/adr/`](../../archive/adr/README.md) | **no** — archive is not evidence |

A record moves from `docs/adr/` to `archive/adr/` **in the same change that
accepts its successor** — never before, so no claim is ever left ungrounded. A
record whose *subject ceased to exist* moves there too, and its row says plainly
that it has **no successor**. New records are written here, from
[`TEMPLATE.md`](TEMPLATE.md).

The v0.26 engine's records are frozen at
[`archive/v0.26-docs/adr/`](../../archive/v0.26-docs/adr/) and are always cited
as **"archived ADR-NNNN"** with that path — a bare `ADR-<NAME>` in any live doc
means this directory.

---

## The convention

**Path.** `docs/adr/000N_<short-name>.md`, numbered sequentially. The number is
a filename ordinal, **not an identity** — it is scoped to its directory and its
generation, and it restarts when a record set is replaced. Nothing identifies a
record by number.

**Cite by NAME, never by number.** In prose, always `ADR-RECORD`, never
"ADR-0004". Numbers exist so the archive can map a retired record to its
successor. **A live doc that says "ADR-0004" is a defect; fix it on contact.**

### Frontmatter is the metadata, and the body never restates it

**Ten keys, in this order** — `type` · `name` · `title` · `description` ·
`status` · `date` · `feature` · `owns` · `laws` · `timestamp`. Two more are
optional and appear only where they are true: `supersedes` and `ratifies`.

| key | value |
|---|---|
| `type` | always `ADR` |
| `name` | `ADR-<NAME>` — cite this everywhere |
| `title` | `ADR-<NAME> (NNNN) — <short decision title>`; carries both name and number |
| `description` | one sentence; what the record decides |
| `status` | `proposed` · `accepted` · `superseded` |
| `date` | `YYYY-MM-DD` — when the decision was taken |
| `feature` | the one feature this record belongs to |
| `owns` | inline list of `src/`/`tools/` paths, `[]` when none — **must match the ownership table below** |
| `laws` | inline list of ADR-LAWS numbers (`[L1, L3]`), `[]` when none. Never restate a law |
| `timestamp` | ISO-8601, for OKF consumers |

**Any value containing `: ` must be quoted** — `fux`'s parser is permissive and
will read it, but strict YAML refuses the whole block, **which makes the
record's metadata invisible to GitHub, editors and every generator.**

⚠ **The body opens at §1 and restates none of it.** Every record used to carry
both a frontmatter block and a `- **Name:** …` bullet list, written by hand at
different times, and **they drifted**.
[`tests/test_adr_frontmatter.py`](../../tests/test_adr_frontmatter.py) forbids
the second copy, checks the key set and its order, checks the quoting, and
checks the title carries both the name and the number.

### A record states what is true now. It carries no history.

⚠ **There are no `Amended` sections, and the word does not appear as a
heading.** When a decision changes, **rewrite the sentence it changed** — in
place, in the same commit. **A record is read top-down by an agent that will act
on the first answer it finds, so a correction appended below a false sentence is
a false sentence with a footnote.**

**What a record holds:** what fux does today, and what it is committed to doing.
**What it does not hold:** what it used to do, what a superseded amendment said,
what a number was before it was corrected, or which work item corrected it. Git
holds all of that, and git is where it belongs.

**The one exception is an argument that still binds.** A rejected alternative
belongs in *Alternatives considered* — not because it is history, but because
**it is the reason the current shape is the current shape**, and leaving it out
invites the argument back. The same goes for a defect a decision exists to
prevent: **the failure is the argument, the date it happened is not.**

### Two sections and a bibliography

- **§1 — For humans.** One screen, maximum. Includes a diagram: a Mermaid block
  **and** a hand-paired ASCII twin, **updated together whenever either
  changes**. The twin is collapsed inside a `<details>` block, with a blank line
  after `</summary>` or the fence will not render.

  §1 may also carry **Examples** — real, capture-copied, two or three at most —
  and **Charts**, whose default is *none*. Both are deleted, not left empty,
  when they do not apply.
- **§2 — For agents.** Context · decision · consequences · alternatives
  considered · reference · veto condition. Decisions are numbered, so another
  record can cite `decision 3` rather than quoting.
- **References.** The last section: every source the record cites, gathered —
  **Records · Code · Measured evidence · Project docs · Papers and
  specifications**, empty groups deleted. It is an index, not an argument:
  **nothing appears there that is not cited in the body**, and **an archived
  document is never listed there.**

**The reference is grounded.** A paper, a live doc, code, or measured evidence
under [`work/regression/`](../../work/regression/README.md). **Never an archived
doc** — nothing guarantees an archived file was not overwritten after the fact.
An archived doc may be *named* in a record; it may not *back* a live claim.

**The veto condition is a condition, not an event.** Write what would have to
become **true** for the decision to reopen, phrased so someone can check it
today with a command or a look at the code. **A veto written as an event to
await never fires, because nobody is waiting** — and a veto keyed to a filename
goes stale when the file is renamed, where one keyed to a committed value does
not.

**A record that restates a cross-cutting principle is a bug.** The project's
foundational rules live in exactly one place — **ADR-LAWS**. Every other record
names the law's number in its `laws:` key and moves on. **The paraphrase is what
drifts.**

### Records are kept current by a check, not by good intentions

`CLAUDE.md` §Law zero is the rule; these are where it is enforced:

| where | what it does |
|---|---|
| [`tests/test_adr_freshness.py`](../../tests/test_adr_freshness.py) | runs in CI with `fetch-depth: 0`. Fails any commit since the rule landed that changed an ADR-owned component without touching **that component's owning record specifically** — touching some other record does not count |
| [`tests/test_adr_register_status.py`](../../tests/test_adr_register_status.py) | fails when a status cell below disagrees with the record's own frontmatter, or when a record on disk is missing from the table. **The record is the truth; this table indexes it** |
| [`tests/test_adr_owns_consistency.py`](../../tests/test_adr_owns_consistency.py) | fails when a record's `owns:` key and the ownership table disagree — **in either direction** |
| [`tests/test_adr_frontmatter.py`](../../tests/test_adr_frontmatter.py) | the ten keys, their order, the quoting, the title, and the two things a body may not contain |
| [`tests/test_adr_ownership.py`](../../tests/test_adr_ownership.py) | every component claimed exactly once, every owner resolvable, every number unique within a directory |
| [`scripts/adr-guard.sh`](../../scripts/adr-guard.sh) | the freshness check as a `commit-msg` hook: `ln -sf ../../scripts/adr-guard.sh .git/hooks/commit-msg` |

**The escape hatch is a line reading exactly `no ADR affected` in the commit
message**, on its own line. **It is not a silent skip — it is a claim, in git
history, under your name**, that you checked and there was nothing to update.

⚠ **What none of these prove.** The freshness gate checks that a record was
**touched**, never that it is **coherent**. A record can be edited into
self-contradiction in the same commit and every mechanical check passes. **That
has happened, and the code implemented the wrong sentence.**

**The baseline is self-bootstrapping**: the freshness check applies from the
commit that added it, never retroactively. After a bulk review the baseline can
move forward by writing a commit sha into
[`docs/adr/RULE-SINCE`](RULE-SINCE) — ⚠ at the cost that the commits it skips
past are **no longer re-auditable by the gate.**

Start from [`TEMPLATE.md`](TEMPLATE.md).

---

## The register

| # | name | title | status | built |
|---|------|-------|--------|-------|
| [0001](0001_laws.md) | **ADR-LAWS** | The non-negotiable constraints have exactly one home, and records cite it | accepted | yes |
| [0002](0002_cli-surface.md) | **ADR-CLI** | The command-line surface — flat verbs in seven groups, one error boundary, three output modes, every command captured verbatim | accepted | yes |
| [0003](0003_fux-directory.md) | **ADR-DOTFUX** | The `.fux/` directory — every child declared committed or derived; the ignore rule asserted against git itself | accepted | yes |
| [0004](0004_ask.md) | **ADR-ASK** | The `ask` verb — one scorer, one sort; the path that answers can never change the answer | accepted | yes |
| [0005](0005_find.md) | **ADR-FIND** | The `find` verb — one line per hit, for pipes; a projection of `ask`, not a second strategy | accepted | yes |
| [0006](0006_answer.md) | **ADR-ANSWER** | The `answer` verb — a fetched, re-scored passage with a fresh sha, its footing stated every time, and no model on the path | accepted | yes |
| [0007](0007_ingest.md) | **ADR-INGEST** | How ingest works — carry unchanged extraction forward, re-resolve every edge, write only shards whose bytes changed | accepted | yes |
| [0008](0008_url-ingest.md) | **ADR-URL-INGEST** | URL ingestion behaviour — fetching only inside a named fenced path, a failed fetch is a skip not a deletion, de-listing needs no network | accepted | yes |
| [0009](0009_index-lifecycle.md) | **ADR-INDEX-LIFECYCLE** | Index generation and update — one canonical encoder, write-if-different, a derived plane that refuses to diverge | accepted | yes |
| [0010](0010_index-record.md) | **ADR-RECORD** | One line of the committed index, property by property — including the ones that are conditional | accepted | yes |
| [0011](0011_accelerator.md) | **ADR-T1-ACCELERATOR** | The derived T1 accelerator — disposable, term-major, and forbidden from changing an answer | accepted | yes |
| [0012](0012_ranking.md) | **ADR-RANKING** | How documents are scored and ordered — BM25F, weight-then-saturate once, one scorer and one rounded sort | accepted | yes |
| [0013](0013_postings.md) | **ADR-POSTINGS** | The postings in two shapes — doc-major in git for diffs, term-major in the runtime plane for queries | accepted | yes |
| [0014](0014_config.md) | **ADR-CONFIG** | `fux.toml` and every property in it — three tables read, two refused by name, one passed through unread | accepted | yes |
| [0015](0015_port-list.md) | **ADR-PORT-LIST** | Port, don't rewrite — a closed list, each module with its tests, and a port earns its place by having a caller | accepted | partial |
| [0016](0016_extracted-mode.md) | **ADR-EXTRACTED** | The `extracted` ingest mode — everything taken from the document, nothing invented; the mode every guarantee is stated for | accepted | yes |
| [0018](0018_url-list.md) | **ADR-URL-LIST** | The committed URL list — one per line so it merges at scale; loader-sorted so config order can never change committed bytes; one grammar for all three lists | accepted | yes |
| [0019](0019_fetcher.md) | **ADR-FETCHER** | The consumer-owned fetcher — fux never fetches; one fetcher per URL, declared not detected, returning bytes and a content type, and nothing composes | accepted | yes |
| [0020](0020_cdp-fetcher.md) | **ADR-CDP-FETCHER** | The browser fetcher — drives your existing Chrome over CDP on a hand-rolled stdlib WebSocket; never escalated to | accepted | yes |
| [0021](0021_http-fetcher.md) | **ADR-HTTP-FETCHER** | The default fetcher — a plain stdlib GET written into your repo by `fux setup`, so core keeps zero network lines; and it never escalates | accepted | yes |
| [0022](0022_dir-list.md) | **ADR-DIR-LIST** | The committed directory list — `!` subtracts, and `archived=true` is a declaration never derived from a path | accepted | yes |
| [0023](0023_cachedir-tag.md) | **ADR-CACHEDIR-TAG** | CACHEDIR.TAG marks a derived `.fux/` directory disposable, so backup and archive tools skip it for free | accepted | yes |
| [0024](0024_docs-table.md) | **ADR-DOCS-TABLE** | `docs.jsonl` — the docidx-ordered doc table every other derived structure joins against; nothing in it is derived, only carried | accepted | yes |
| [0026](0026_runtime-manifest.md) | **ADR-RUNTIME-MANIFEST** | `manifest.json` — the per-shard content-sha fingerprint, plus the doc-table field set that a version string could not be trusted to carry | accepted | yes |
| [0027](0027_runtime-stamp.md) | **ADR-RUNTIME-STAMP** | `stamp.json` — the cheap, non-reproducible size/mtime pre-check ahead of the manifest's real one | accepted | yes |
| [0028](0028_runtime-stats.md) | **ADR-RUNTIME-STATS** | `stats.json` — the corpus-wide numbers BM25F reads, stored RAW so a field weight cannot bake into the plane | accepted | yes |
| [0029](0029_graph.md) | **ADR-GRAPH** | The graph lane — `explain`/`graph`/`path`, unseeded label-propagation communities in a derived plane, and PPR-lite with a **lazy** walk | accepted | yes |
| [0030](0030_refer-plane.md) | **ADR-REFER** | Fetch through the *consumer's* fetcher, verify by content sha, assemble under a **byte** budget with a floor, and record the staleness discovered | accepted | yes |
| [0031](0031_types-list.md) | **ADR-TYPES** | Which files are documents — prose plus every format a built-in decoder reads; absent means the default, never "everything" | accepted | yes |
| [0032](0032_hooks.md) | **ADR-MAINTENANCE** | The hooks that keep a committed index in step — `post-commit` **defers**, no hook touches the network, one write lock, and a resident daemon for the URL tail | accepted | yes |
| [0033](0033_merge-driver.md) | **ADR-MERGE-DRIVER** | The committed index merges line by line, last-writer-wins on `(ver, sha)`, and refuses rather than guesses | accepted | yes |
| [0034](0034_cache.md) | **ADR-CACHE** | Two caches, two different proofs — ARC keyed `(loc, sha)` cannot change an answer; the TTL store is opt-in, disk-bounded, and answers `cached`, never `current` | accepted | yes |
| [0035](0035_agent-policy.md) | **ADR-AGENT-POLICY** | Fux ships the policy its consumers need to read it correctly — one canonical policy carried as a **verbatim block** into each vendor's native format, from a declaration and never from detection | accepted | yes |
| [0036](0036_predictions.md) | **ADR-RS** | The R predictions — a claim frozen before measurement, four ways one can end (**FAIL is a success of the method**), and the blind/informed split on the runs that measure them | accepted | partial |
| [0037](0037_archived-content.md) | **ADR-ARCHIVED-CONTENT** | What a document declared `archived=true` does once indexed — a record property, a marker, a disclaimer that states the fact and refuses to interpret it, and a demotion nobody takes by default | accepted | yes |
| [0038](0038_tuning.md) | **ADR-TUNE** | `.fux/tune.toml` — every knob that changes ordering and none that changes the index, decided by one mechanical test; plus per-source priority in either direction | accepted | yes |
| [0039](0039_mcp.md) | **ADR-MCP** | `fux mcp` — the stdio JSON-RPC server for coding agents. Three tools rather than the whole verb surface, stdlib-only, and **`answer` is deliberately absent** | accepted | yes |
| [0040](0040_enrich.md) | **ADR-ENRICH** | Enrichment as an **agent skill, not an API call** — fux plans and validates, a coding agent generates, and partial coverage is the steady state | accepted | yes |
| [0041](0041_rerank.md) | **ADR-RERANK** | Proximity reranking over the refer plane's own passages — and the cross-encoder refused on cross-machine determinism, not on cost | accepted | yes |
| [0042](0042_decode.md) | **ADR-DECODE** | The decoder plane — bytes become Markdown in one place, and a consumer may bring a dependency fux may not | accepted | yes |
| [0043](0043_locks.md) | **ADR-LOCKS** | The one mutex fux owns over the committed index, and the three sibling files that are constantly mistaken for locks | ⏳ proposed | yes |
| [0044](0044_quality-contract.md) | **ADR-QUALITY** | What *"good"* means — a four-gate funnel with `recall@k` as the headline, a declared and versioned query mix, unanswerable queries inside the gate, and the cost of an error published before any score exists | accepted | **no** |
| [0045](0045_confidence.md) | **ADR-CONFIDENCE** | How much the index believes its own answer — four deterministic signals and one band, so an agent can tell a grounded result from the closest thing in a corpus that never discusses the question. ⚠ **Amended 2026-08-27 (decision 11): `--band` gates the CLI, the MCP result is always on** — the block is always computed, only its emission is gated | accepted | **partial** |
| [0046](0046_provenance.md) | **ADR-PROVENANCE** | Fux does not keep an audit trail; it makes one derivable — a derivation on `ask --why`, a re-runnable receipt on `answer --receipt`, and `fux verify`'s four-state verdict | accepted | yes |
| [0047](0047_output-defaults.md) | **ADR-OUTPUT** | Output defaults are configurable in a third file, `.fux/output.toml` — a third boundary: not what is indexed, not which documents come back, but **how they are shown**. The one surface it exists for is **MCP**, which has no flags at all | accepted | yes |
| [0048](0048_fuxignore.md) | **ADR-FUXIGNORE** | `.fux/.fuxignore` — one file for what is not indexed, in `.gitignore`'s grammar; read first, and the only thing that outranks the type allowlist in both directions | accepted | yes |
| [0049](0049_ownership.md) | **ADR-OWNERSHIP** | `owns` and `describes` — the record-to-component model itself, which two tests enforced and no record decided. Exactly one owner per component; any number of describers, and the freshness gate demands all of them | accepted | **no** |

> ## The number line has holes, on purpose — `0017` and `0025` are burned
>
> **`0001`–`0049`, with two gaps that are never filled.** The gaps are the rule
> working, not a mess to tidy:
>
> - **A vacated ordinal is burned and never reused** (W-82 ruling 7). `0025`
>   went when `ADR-CODES-TABLE` was archived with no successor — its subject,
>   the dense lane, was deleted rather than replaced. `0017` went on 2026-08-27
>   when `ADR-ENRICHED` was superseded by [ADR-ENRICH](0040_enrich.md).
> - ⚠ **A note here claimed the opposite until 2026-08-27** — that `0026`
>   upward had been "renumbered down by one" so `0025` was no longer a hole. It
>   never happened, and it must not: it names the exact failure ruling 7 exists
>   to prevent, and the same ruling records that a previous compaction put **two
>   records on `0022`**. The note pointed at `0025_runtime-manifest.md` and
>   `0042_locks.md`, neither of which has ever existed
>   ([ADR-RUNTIME-MANIFEST](0026_runtime-manifest.md) is `0026`,
>   [ADR-LOCKS](0043_locks.md) is `0043`).
> - **`ADR-CONFIDENCE` briefly existed at two paths** — `0043_confidence.md` and
>   `0045_confidence.md`, same `name:`, while `0043` was also
>   [ADR-LOCKS](0043_locks.md). Ruled 2026-08-27: **keep the later file**, on a
>   substantive ground rather than its date — its decision 6 binds
>   `SEPARATION_FLOOR` to [ADR-QUALITY](0044_quality-contract.md)'s frozen
>   `t = 0.75`, where the discarded one still picked its own abstention
>   threshold. The duplicate is deleted.
> - **This is why the cite-by-name rule exists.** A hole costs nothing when
>   every citation is a name; closing one costs every citation in the repo.
>
> ⚠ **So a number in a document older than 2026-08-27 may name a different
> record than it does today**, and [`work/WORKLOG.md`](../../work/WORKLOG.md) is
> append-only, so some of those sentences cannot be corrected and were left
> standing. **This is the cost that the cite-by-name rule below exists to avoid
> paying twice** — a name survives a renumber and a number does not. Read a bare
> number in an old document as *an ordinal at the time of writing*, and resolve
> it through [`archive/adr/README.md`](../../archive/adr/README.md).

**`status` and `built` are two different questions, and conflating them is a
mistake this project has already paid for.** `status: accepted` means **the
decision is ratified**. `built` means **the engine does it**. A record can be
accepted and unbuilt — that is a decision made ahead of the code, which is
legitimate and is how [ADR-ENRICH](0040_enrich.md) and
[ADR-QUALITY](0044_quality-contract.md) exist today. **What is not legitimate is
a reader having to open the record to find out.**

**A row with `built: no` or `partial` names work somebody has to do**, and
belongs to an item in [`work/OPEN-WORK.md`](../../work/OPEN-WORK.md) — otherwise
it is a decision nobody is going to act on, which is a wish.

---

## Ownership — which record owns which component

**This table is the answer, not a judgement call.** Every component in `src/`
and `tools/` appears here exactly once, and
[`tests/test_adr_ownership.py`](../../tests/test_adr_ownership.py) fails on one
that does not.

**Most specific wins.** A record may carve a single file out of another's
directory-level claim — `store/fuxdir.py` out of `store/`, `query/rank.py` out
of `query/`, `maintain/mergedriver.py` out of `maintain/`. **A carve-out is
justified when the file carries a *different decision*, not merely a different
concern**: the reranker is separate because it is the one thing under `query/`
that reads the **working tree**; the merge driver because its failure mode and
its gate are its own.

**A record may own nothing, and there are two honest reasons for it.** Some
records specify one file another record already generates — the runtime-plane
companions. Others state a mechanism spread across components each already
claimed by the record carrying its decisions, as [ADR-LOCKS](0043_locks.md)
does. ⚠ **In both cases the freshness gate cannot demand that record**, so
nothing mechanical will catch it going stale.

⚠ **Directory-level ownership lets a change be discharged against the wrong
record.** The freshness gate demands the *owning* record for a changed
component, so editing a file can be satisfied by touching whichever record owns
its directory — **while the record whose subject *is* that file need never be
opened.** A record that describes a component it does not own has no mechanical
protection at all. **Open both.**

**A component that genuinely has no decision yet is claimed by an open work
item** (`W-nn`) instead. The test resolves that id against
[`work/OPEN-WORK.md`](../../work/OPEN-WORK.md); a `W-nn` that has closed fails
the check, so **a component cannot stay unowned by accident.**

**Both change together.** A record's `owns:` key and this table are asserted
equal **in both directions** by
[`tests/test_adr_owns_consistency.py`](../../tests/test_adr_owns_consistency.py)
— a path here that its owner does not declare fails as loudly as a claim this
table does not grant.

<!-- OWNERSHIP-TABLE-START -->

| component | owner | note |
|---|---|---|
| `src/fux/__init__.py` | ADR-LAWS | package identity and version. Every release bump opens that record, which is correct rather than annoying |
| `src/fux/errors.py` | ADR-LAWS | the single flat `FuxError` — CLAUDE.md §Error contract |
| `src/fux/schema.py` | ADR-LAWS | the **one** schema mechanism every plane's declared shape loads through. Here for the same reason `errors.py` is: it is cross-cutting, and ADR-LAWS is the one record that legitimately spans planes. **The schema FILES are not here** — each lives beside the code it describes, so its ownership is correct by construction |
| `src/fux/frontmatter.py` | ADR-LAWS | hand-rolled parser — L1, `$0` stdlib-only |
| `src/fux/cli.py` | ADR-CLI | the flat verb surface, the boundary error contract, and the `--json` shape |
| `src/fux/__main__.py` | ADR-CLI | `python -m fux` — the invocation ladder's last rung, and the spelling a human guesses |
| `src/fux/sources.py` | ADR-CLI | `add`/`remove`/`update` — the writer for **all three** source lists, and the verbs over them |
| `src/fux/progress.py` | ADR-CLI | the progress plane — stderr-only, TTY-gated, counts not clocks |
| `src/fux/config.py` | ADR-CONFIG | `fux.toml`'s schema, the opaque `[sources.url.config]` table, and the tables refused by name rather than ignored |
| `src/fux/tune.py` | ADR-TUNE | `.fux/tune.toml` — the loader, the closed key set, the two refusals, and the `[priority]` data. **The priority RESOLUTION is not here**: it lives on `query/rank.py::Weighting`, next to the bound that has to agree with it |
| `src/fux/doctor.py` | ADR-DOTFUX | the committed-vs-derived assertions, the URL section, the runner check and the **fetcher-capability notice** — all read-only, all offline. The notice is decision 6's own named mechanism (*a `doctor` check, never a rewrite*) applied to [ADR-FETCHER](0019_fetcher.md) decisions 12–13; it reads the consumer's fetcher **as text and never imports it** |
| `src/fux/setup.py` | ADR-DOTFUX | the second scaffolding moment — the consumer-owned files, write-if-missing |
| `src/fux/store/` | ADR-INDEX-LIFECYCLE | canonical bytes, shard addressing, writer/reader, collisions, and the declared record shape |
| `src/fux/store/fuxdir.py` | ADR-DOTFUX | the `.fux/` layout generator |
| `src/fux/ingest/` | ADR-INGEST | git-dir walk, parse, edges — writes the committed plane |
| `src/fux/ingest/priors.py` | ADR-INGEST | ⚠ **covered by the directory claim, and described by no record's decisions.** It computes the supersession and recency priors and writes `mtime` and `superseded` into the committed record; ADR-RECORD documents the properties and ADR-TUNE the weights, but the module's own behaviour is unrecorded |
| `src/fux/ingest/extract.py` | ADR-EXTRACTED | what extraction *promises* — title, phrases, terms and per-field lengths, taken from the bytes and nothing else |
| `src/fux/ingest/sourcelist.py` | ADR-URL-LIST | the one grammar all three committed source lists are parsed by |
| `src/fux/ingest/fuxignore.py` | ADR-FUXIGNORE | `.fux/.fuxignore` — the `.gitignore` grammar, the last-match-wins resolution, and the duplicate-pattern warning. **Carved out of ADR-INGEST's directory claim for a different DECISION, not a different concern**: everything else under `ingest/` is a step in the walk, and this is a *precedence rule* over it — the one thing that outranks the type allowlist |
| `src/fux/ingest/urlsrc.py` | ADR-FETCHER | fux's half of the fetch contract — load, configure, bound, call, normalize |
| `src/fux/decode/` | ADR-DECODE | bytes → Markdown, in one place: the built-in decoders, the registry, the override precedence and the `.fux/decoders/` consumer seam. Separate from ADR-INGEST's claim because the record it carries is a **boundary** — where consumer-supplied dependencies become legal — not a step in the walk |
| `src/fux/derive/` | ADR-T1-ACCELERATOR | T1 build, block maxima, skipping, and the declared runtime shapes |
| `src/fux/query/` | ADR-ASK | the scan, unification, and the display-only resolution after it — bound by the differential law |
| `src/fux/query/rank.py` | ADR-RANKING | the one scorer and the one sort, and `Weighting`, which is where every document multiplier must travel to reach the pruning bound |
| `src/fux/query/bm25f.py` | ADR-RANKING | BM25F, `Scoring`, and `derive_wlen` — the one place the weighting arithmetic exists |
| `src/fux/query/analyzer.py` | ADR-RANKING | split, lowercase, stopword, stem, hash — in that order, shared by ingest and query |
| `src/fux/query/stem.py` | ADR-RANKING | the Porter implementation, checked against the published test vectors |
| `src/fux/query/tokenize.py` | ADR-RANKING | the shim both `ingest/` and `query/` import, which is what makes the two sides agree **by construction** rather than by review |
| `src/fux/query/rerank.py` | ADR-RERANK | proximity reranking — carved out because it is the one thing under `query/` that reads the **working tree** rather than the committed index, and because the decision it carries is a *refusal* |
| `src/fux/query/confidence.py` | ADR-CONFIDENCE | the four signals and the band, computed from what ranking already produced |
| `src/fux/query/provenance.py` | ADR-PROVENANCE | the derivation, the receipt, the journal and `verify`'s four-state verdict. **Carved out of `query/` for a different DECISION, not a different concern**: everything else under `query/` answers a question, and this answers *how the answer was reached* — and it is the one module in the tree that may write a plaintext use record (L8, as reverted) |
| `src/fux/output_config.py` | ADR-OUTPUT | `.fux/output.toml` — the loader, the closed per-verb key set, and the one precedence chain (flag -> `[verb]` -> `[defaults]` -> built-in). **Top-level, beside `tune.py`, because it is a peer of it**: same shape, different boundary — `tune.py` changes which documents come back, this changes how they are shown |
| `src/fux/enrich.py` | ADR-ENRICH | `fux enrich --plan/--check` — the deterministic halves |
| `src/fux/mcp.py` | ADR-MCP | the stdio JSON-RPC server — three tools, stdlib-only, warm across calls. **`answer` is deliberately absent**: the agent is the answerer |
| `src/fux/graph/` | ADR-GRAPH | edges lifted into adjacency, unseeded label-propagation communities, PPR-lite, and the three relational verbs. Owns `.fux/runtime/graph.json` |
| `src/fux/maintain/` | ADR-MAINTENANCE | the git hooks and their installer, the deferring runner, the write lock, the daemon and the local state files. **L5's write-time check is deliberately NOT here** — it lives in `store/writer.py`, because a check beside the thing it guards cannot be skipped |
| `src/fux/maintain/mergedriver.py` | ADR-MERGE-DRIVER | the merge driver itself — carved out because its failure mode and its gate are its own |
| `src/fux/refer/` | ADR-REFER | source · freshness · chunk · rescore · assemble. **Imports no transport**: the consumer's fetcher is injected |
| `src/fux/refer/arc.py` | ADR-CACHE | the content cache, keyed `(loc, sha)` so a hit cannot change an answer |
| `src/fux/refer/fetchcache.py` | ADR-CACHE | the TTL fetch store — the only place in the engine that reads a wall clock |
| `src/fux/templates/` | ADR-FETCHER | the two shipped fetchers as package data; **bytes, never imported** |
| `src/fux/templates/agents/` | ADR-AGENT-POLICY | the canonical agent policy and its per-vendor renderings, shipped as wheel package data (`setup.py` itself stays with ADR-DOTFUX — one component, one owner) |
| `src/fux/templates/agents/ENRICH-SKILL.md` | ADR-ENRICH | the generation half — a skill rather than code, because a model call may not live under `src/` |
| `src/fux/templates/agents/DECODER-SKILL.md` | ADR-DECODE | how to write or edit a decoder — a **build procedure for one plane**, not a rendering of the archived-results policy |
| `tests/test_regression_runs.py` | ADR-RS | the per-run contract for a conformance run. **The harnesses are not claimed here**: a harness belongs to the feature it measures, the discipline belongs to the record |
| `tools/pruning-eval/` | ADR-POSTINGS | the gate harness and its frozen pre-registrations, held by the record that owns the pruning decision and carries its standing law |
| `tools/maintenance-bench/` | ADR-MAINTENANCE | the hook-latency and merge-driver harness. **One file runs both, and a component is owned once** |
| `tools/refer-bench/` | ADR-REFER | the latency harness and its frozen pre-registration — a real `http.server` behind the **consumer's own generated fetcher**, so the measured path is the shipped one |
| `tools/refer-budget-sweep/` | ADR-REFER | the assembler-vs-greedy budget sweep and its frozen pre-registration |
| `tools/differential/` | ADR-T1-ACCELERATOR | the differential-law harness and its bench. ⚠ **No test imports it**, so it can break silently — and has |
| `tools/quality-controls/` | ADR-RS | the two controls **decision 15 is owed** — a content-free matched-length placebo and a decoy query set. Owned by the record that demands them, not by ADR-CONFIDENCE whose behaviour they test: a control belongs to the measurement discipline, so changing what a control IS updates the rule rather than the feature. ⚠ **The third, the sealed subset, is NOT built** and decision 15 keeps its `NOT BUILT` marker |
| `tools/archived-signal-eval/` | ADR-ARCHIVED-CONTENT | the live-vs-archived contamination instrument, its frozen pre-registration and its query set. Owned by the record whose claim it tests, because this measures a **feature gate** and takes no `R` id |
| `tools/graph-bench/` | ADR-GRAPH | cost-attribution profiler for the graph lane — not a gate |
| `tools/quality/` | ADR-QUALITY | the frozen quality contract — the declared query mix and the published cost of an error — **and `goldens.py`, the schema that keeps the rank contract and the relevance set apart** (decision 12). The mix and the cost are a **frozen instrument, not a harness**; `goldens.py` is the one executable thing here, and it exists because decision 12's rules are mechanical: an undeclared relevance list, or a `doc` outside its own relevance set, is refused rather than trusted |
| `tools/t2-eval/` | ADR-RS | a harness whose feature record was retired, held here by ADR-RS decision 10's fallback. **A retired record cannot own anything, and a proposal is not a valid owner** |

<!-- OWNERSHIP-TABLE-END -->

---

## Describes — which record's subject REACHES INTO a component it does not own

**A second, additive relation** ([ADR-OWNERSHIP](0049_ownership.md)). Ownership
stays exactly one record per component; **describes is any number**, and the
freshness gate demands the owner **and every describer**.

⚠ **This exists because the gate was narrower than it read.** `src/fux/query/`
is owned by ADR-ASK, so rewriting the scorer satisfied the check by touching
ADR-ASK — while **ADR-RANKING, whose entire subject is that scorer, rotted
silently** and was never opened. It passed through all of W-76 that way, sixteen
records deep.

**`describes` never substitutes for `owns`.** A component with no owner fails
whatever describes it, and a record listed as describing something it also owns
is a defect (veto 2). **Every row states its reason** — a bare pair is
unauditable, and an unauditable table stops being trusted.

⚠ **Seeded small and first-hand.** Four rows, each verified against a change
actually made, rather than a sweep guessing at intent — a bulk fill would make
the relation *look* enforced while asserting things nobody checked.

<!-- DESCRIBES-TABLE-START -->

| component | record | why it reaches in |
|---|---|---|
| `src/fux/cli.py` | ADR-OUTPUT | decision 10 binds **every gated flag** in this file to `default=None`. Owned by ADR-CLI, constrained here — and the constraint failing silently is precisely how six flags shipped at `default=False` |
| `src/fux/query/__init__.py` | ADR-CONFIDENCE | the confidence block is assembled and emitted here (`confidence_out`, `_fill_confidence`), while ADR-ASK owns the module for the scan and unification |
| `src/fux/query/__init__.py` | ADR-OUTPUT | the emission gate (`_show_band`, `_gated`) lives here — where a rendering decision reaches into a file whose subject is the query itself |
| `src/fux/derive/accel.py` | ADR-CONFIDENCE | `stats_out` is passed through here so the accelerator and the scan agree about `df`/`n`. **The differential law is what makes this load-bearing**: if only one path carried it, the two would disagree about how confident fux is |
| `src/fux/query/rank.py` | ADR-TUNE | `[priority]` is DATA in ADR-TUNE and RESOLUTION on `rank.py::Weighting` — the register's own ownership note already says so, which is what made this row checkable rather than asserted |

<!-- DESCRIBES-TABLE-END -->

