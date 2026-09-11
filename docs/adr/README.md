# ADRs — the decision records

**How to use this file.** This is the register: the naming convention, the
record shape, the ownership table, and the rules every record obeys. Read it
before writing an ADR, before citing one, and before adding a module to `src/`.

One ADR per completed feature or ruled measurement. Every ADR carries a
reference. **Every record is cited by NAME in prose, never by number.**

## One directory, one state

**`docs/adr/` is the only home a decision record has** (Arpit, 2026-09-06). The
archive tier is gone: the retired records were **deleted**, not filed, and
nothing outside this directory is a record. A citation therefore resolves here
or it does not resolve at all.

- **There is no "superseded" location.** A record that is superseded is
  **rewritten or deleted in the change that supersedes it**, and the successor
  states plainly what it replaced — in prose, by name. There is no second file
  left behind to be found and mistaken for current.
- **A record whose subject ceased to exist is deleted**, and the decision that
  killed the subject says so.
- **Nothing in this repo may cite an archived record**, by path or by name, as
  backing for a live claim. A name may appear in a sentence about history; a
  link to one may not, because the file is not there.

New records are written here, from [`TEMPLATE.md`](TEMPLATE.md).

---

## The convention

**Path.** `docs/adr/NNNN_<short-name>.md`, on **two ranges** (Arpit, 2026-09-11):

| range | holds | a new record takes |
|---|---|---|
| `0001`–`0100` | the **Law** records only — `0001` ADR-LAWS, `0002`–`0010` ADR-LAW-0 … ADR-LAW-8 | the next free number **from `0011`** |
| `0101`– | **every other record**, sequentially | the next free number **after the highest** |

**`0011`–`0100` are reserved and EMPTY — there are no placeholder files.** A
gap in that range is the reservation, not a missing record; nothing scans for
one and nothing should create one to fill it. **If the laws ever pass 100,
renumber again** — Arpit's words, and deliberately not a pre-built rule.

The number is a filename ordinal, **not an identity** — it is scoped to its
directory and its generation, and it restarts when a record set is replaced.
Nothing identifies a record by number.

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
| [0001](0001_LAWS.md) | **ADR-LAWS** | The non-negotiable constraints have exactly one home, and records cite it | accepted | yes |
| [0003](0003_LAW-1-zero-cost.md) | **ADR-LAW-1** | **L1** — `$0`, FOSS-only: OSI-approved licences only, with source-available (BSL/SSPL/Elastic v2) named as failing it. Why fux is never a purchase order; and the 2026-09-06 amendment that withdrew the zero-dependency guarantee while hardening the money clause | accepted | yes |
| [0004](0004_LAW-2-content-never-durable.md) | **ADR-LAW-2** | **L2** — content is never durable outside its source system. The law the architecture rests on, its three declared exceptions, and why a summary of a confidential document is one | accepted | yes |
| [0005](0005_LAW-3-deterministic.md) | **ADR-LAW-3** | **L3** — deterministic; no model in the maintenance path. Byte-identical index and root hash, the enrichment boundary that keeps it true, and the pin problem L1's amendment created | accepted | yes |
| [0006](0006_LAW-4-offline-by-default.md) | **ADR-LAW-4** | **L4** — offline by default. Fenced opt-in paths, *plural*; the narrowing that already happened once across nine records; and the use-record gap this law does not close | accepted | yes |
| [0007](0007_LAW-5-hashed-meta.md) | **ADR-LAW-5** | **L5** — hashed meta for non-git sources, enforced at write time. The ACL-mismatch leak it closes, and the channel it reduces rather than closes | accepted | yes |
| [0008](0008_LAW-6-say-index.md) | **ADR-LAW-6** | **L6** — say "index", not "db". Load-bearing vocabulary: the noun governs the inferences, and every *"why not cache the bodies"* conversation starts with the wrong one | accepted | yes |
| [0009](0009_LAW-7-python-311.md) | **ADR-LAW-7** | **L7** — Python ≥ 3.11. The floor that made refusing dependencies affordable, and the justification that narrowed on 2026-09-06 without the floor moving | accepted | yes |
| [0010](0010_LAW-8-use-record.md) | **ADR-LAW-8** | **L8** — a use record is never committed. Written, reverted and re-narrowed in one day; gitignored is the test, not `.fux/`; and the transmission clause that did not survive | accepted | yes |
| [0101](0101_cli-surface.md) | **ADR-CLI** | The command-line surface — flat verbs in seven groups, one error boundary, three output modes, every command captured verbatim | accepted | yes |
| [0102](0102_fux-directory.md) | **ADR-DOTFUX** | The `.fux/` directory — every child declared committed or derived; the ignore rule asserted against git itself | accepted | yes |
| [0103](0103_ask.md) | **ADR-ASK** | The `ask` verb — one scorer, one sort; the path that answers can never change the answer | accepted | yes |
| [0104](0104_find.md) | **ADR-FIND** | The `find` verb — one line per hit, for pipes; a projection of `ask`, not a second strategy | accepted | yes |
| [0105](0105_answer.md) | **ADR-ANSWER** | The `answer` verb — a fetched, re-scored passage with a fresh sha, its footing stated every time, and no model on the path | accepted | yes |
| [0106](0106_ingest.md) | **ADR-INGEST** | How ingest works — carry unchanged extraction forward, re-resolve every edge, write only shards whose bytes changed | accepted | yes |
| [0107](0107_url-ingest.md) | **ADR-URL-INGEST** | URL ingestion behaviour — fetching only inside a named fenced path, a failed fetch is a skip not a deletion, de-listing needs no network | accepted | yes |
| [0108](0108_index-lifecycle.md) | **ADR-INDEX-LIFECYCLE** | Index generation and update — one canonical encoder, write-if-different, a derived plane that refuses to diverge | accepted | yes |
| [0109](0109_index-record.md) | **ADR-RECORD** | One line of the committed index, property by property — including the ones that are conditional | accepted | yes |
| [0110](0110_accelerator.md) | **ADR-T1-ACCELERATOR** | The derived T1 accelerator — disposable, term-major, and forbidden from changing an answer | accepted | yes |
| [0111](0111_ranking.md) | **ADR-RANKING** | How documents are scored and ordered — BM25F, weight-then-saturate once, one scorer and one rounded sort | accepted | yes |
| [0112](0112_postings.md) | **ADR-POSTINGS** | The postings in two shapes — doc-major in git for diffs, term-major in the runtime plane for queries | accepted | yes |
| [0113](0113_config.md) | **ADR-CONFIG** | `fux.toml` and every property in it — three tables read, three refused by name, one passed through unread | accepted | yes |
| [0114](0114_port-list.md) | **ADR-PORT-LIST** | Port, don't rewrite — a closed list, each module with its tests, and a port earns its place by having a caller | accepted | partial |
| [0115](0115_extracted-mode.md) | **ADR-EXTRACTED** | The `extracted` ingest mode — everything taken from the document, nothing invented; the mode every guarantee is stated for | accepted | yes |
| [0116](0116_url-list.md) | **ADR-URL-LIST** | The committed URL list — one per line so it merges at scale; loader-sorted so config order can never change committed bytes; one grammar for the `urls` and `dirs` lists (`types` left it for TOML on 2026-09-11) | accepted | yes |
| [0117](0117_fetcher.md) | **ADR-FETCHER** | The consumer-owned fetcher — fux never fetches; one fetcher per URL, declared not detected, returning bytes and a content type, and nothing composes | accepted | yes |
| [0118](0118_cdp-fetcher.md) | **ADR-CDP-FETCHER** | The browser fetcher — borrows your signed-in Chrome over CDP and **intercepts the response**, returning the server's bytes rather than a rendering; never escalated to | accepted | yes |
| [0119](0119_http-fetcher.md) | **ADR-HTTP-FETCHER** | The default fetcher — a plain stdlib GET written into your repo by `fux setup`, so core keeps zero network lines; and it never escalates | accepted | yes |
| [0120](0120_dir-list.md) | **ADR-DIR-LIST** | The committed directory list — `!` subtracts, and `archived=true` is a declaration never derived from a path | accepted | yes |
| [0121](0121_cachedir-tag.md) | **ADR-CACHEDIR-TAG** | CACHEDIR.TAG marks a derived `.fux/` directory disposable, so backup and archive tools skip it for free | accepted | yes |
| [0122](0122_docs-table.md) | **ADR-DOCS-TABLE** | `docs.jsonl` — the docidx-ordered doc table every other derived structure joins against; nothing in it is derived, only carried | accepted | yes |
| [0123](0123_runtime-manifest.md) | **ADR-RUNTIME-MANIFEST** | `manifest.json` — the per-shard content-sha fingerprint, plus the doc-table field set that a version string could not be trusted to carry | accepted | yes |
| [0124](0124_runtime-stamp.md) | **ADR-RUNTIME-STAMP** | `stamp.json` — the cheap, non-reproducible size/mtime pre-check ahead of the manifest's real one | accepted | yes |
| [0125](0125_runtime-stats.md) | **ADR-RUNTIME-STATS** | `stats.json` — the corpus-wide numbers BM25F reads, stored RAW so a field weight cannot bake into the plane | accepted | yes |
| [0126](0126_graph.md) | **ADR-GRAPH** | The graph lane — `explain`/`graph`/`path`, unseeded label-propagation communities in a derived plane, and PPR-lite with a **lazy** walk | accepted | yes |
| [0127](0127_refer-plane.md) | **ADR-REFER** | Fetch through the *consumer's* fetcher, verify by content sha, assemble under a **byte** budget with a floor, and record the staleness discovered | accepted | yes |
| [0128](0128_types-list.md) | **ADR-TYPES** | Which files are documents — prose plus every format a built-in decoder reads; absent means the default, never "everything"; `.fux/formats.toml` (`include` + `[decoders]`) replaces it, and the old `.fux/sources/types` is refused and converted | accepted | yes |
| [0129](0129_hooks.md) | **ADR-MAINTENANCE** | The hooks that keep a committed index in step — `post-commit` **defers**, no hook touches the network, one write lock, and a resident daemon for the URL tail | accepted | yes |
| [0130](0130_merge-driver.md) | **ADR-MERGE-DRIVER** | The committed index merges line by line, last-writer-wins on `(ver, sha)`, and refuses rather than guesses | accepted | yes |
| [0131](0131_cache.md) | **ADR-CACHE** | Two caches, two different proofs — ARC keyed `(loc, sha)` cannot change an answer; the TTL store is opt-in, disk-bounded, and answers `cached`, never `current` | accepted | yes |
| [0132](0132_agent-policy.md) | **ADR-AGENT-POLICY** | Fux ships the policy its consumers need to read it correctly — one canonical policy carried as a **verbatim block** into each vendor's native format, from a declaration and never from detection | accepted | yes |
| [0133](0133_predictions.md) | **ADR-RS** | The R predictions — a claim frozen before measurement, four ways one can end (**FAIL is a success of the method**), and the blind/informed split on the runs that measure them | accepted | partial |
| [0134](0134_archived-content.md) | **ADR-ARCHIVED-CONTENT** | What a document declared `archived=true` does once indexed — a record property, a marker, a disclaimer that states the fact and refuses to interpret it, and a demotion nobody takes by default | accepted | yes |
| [0135](0135_tuning.md) | **ADR-TUNE** | `.fux/tune.toml` — every knob that changes ordering, decided by one mechanical test, plus `[index]` (`max_phrases`, `max_table_rows`), the declared exception that changes the index; plus per-source priority in either direction | accepted | yes |
| [0136](0136_mcp.md) | **ADR-MCP** | `fux mcp` — the stdio JSON-RPC server for coding agents. Three tools rather than the whole verb surface, stdlib-only, and **`answer` is deliberately absent** | accepted | yes |
| [0137](0137_enrich.md) | **ADR-ENRICH** | Enrichment as an **agent skill, not an API call** — fux plans and validates, a coding agent generates, and partial coverage is the steady state | accepted | yes |
| [0138](0138_rerank.md) | **ADR-RERANK** | Proximity reranking over the refer plane's own passages — and the cross-encoder refused on cross-machine determinism, not on cost | accepted | yes |
| [0139](0139_decode.md) | **ADR-DECODE** | The decoder plane — bytes become Markdown in one place, and a consumer may bring a dependency fux may not | accepted | yes |
| [0140](0140_locks.md) | **ADR-LOCKS** | The one mutex fux owns over the committed index, and the three sibling files that are constantly mistaken for locks | accepted | yes |
| [0141](0141_quality-contract.md) | **ADR-QUALITY** | What *"good"* means — a four-gate funnel with `recall@k` as the headline, a declared and versioned query mix, unanswerable queries inside the gate, and the cost of an error published before any score exists | accepted | **no** |
| [0142](0142_confidence.md) | **ADR-CONFIDENCE** | How much the index believes its own answer — four deterministic signals and one band, so an agent can tell a grounded result from the closest thing in a corpus that never discusses the question. ⚠ **Amended 2026-08-27 (decision 11): `--band` gates the CLI, the MCP result is always on** — the block is always computed, only its emission is gated | accepted | **partial** |
| [0143](0143_provenance.md) | **ADR-PROVENANCE** | Fux does not keep an audit trail; it makes one derivable — a derivation on `ask --why`, a re-runnable receipt on `answer --receipt`, and `fux verify`'s four-state verdict | accepted | yes |
| [0144](0144_output-defaults.md) | **ADR-OUTPUT** | Output defaults are configurable in a third file, `.fux/output.toml` — a third boundary: not what is indexed, not which documents come back, but **how they are shown**. The one surface it exists for is **MCP**, which has no flags at all | accepted | yes |
| [0145](0145_fuxignore.md) | **ADR-FUXIGNORE** | `.fux/.fuxignore` — one file for what is not indexed, in `.gitignore`'s grammar; read first, and the only thing that outranks the type allowlist in both directions | accepted | yes |
| [0146](0146_ownership.md) | **ADR-OWNERSHIP** | `owns` and `describes` — the record-to-component model itself, which two tests enforced and no record decided. Exactly one owner per component; any number of describers, and the freshness gate demands all of them | accepted | **no** |
| [0147](0147_acquired-plane.md) | **ADR-ACQUIRED** | Fetched source bytes are retained in `.fux/acquired/` — a **third** category beside committed and derived: gitignored like derived, but **not rebuildable**, only re-acquirable, and only while the source exists and the session holds. Clock-free: eviction orders by `run_seq`, never by an mtime | accepted | **no** |
| [0148](0148_refusals.md) | **ADR-REFUSAL** | The response a server sends **instead** of the document — a sign-in wall, a paywall, an Office viewer shell. A declarative `.fux/refusals.toml`, **every condition pure over the bytes** (ADR-FETCHER decision 13 held rather than amended), under an always-on magic-byte floor no consumer can switch off | accepted | **no** |
| [0149](0149_url-freshness.md) | **ADR-URL-FRESHNESS** | Six verdicts that never collapse into each other — `as-ingested` is a real comparison against retained bytes, and is neither `current` nor `unverified`. Plus `ttl=` as a per-URL bound that **narrows** the caller's policy and can never widen it | accepted | **no** |
| [0150](0150_pii.md) | **ADR-PII** | **Redact what gets committed; leave alone what stays local.** A consumer-owned `.fux/pii.toml` redacts the index and nothing else — acquired bytes, refer passages and `fux answer` quotes stay as they are. The sha is taken **before** redaction, or every redacted document verifies as `stale` against its own unchanged source. **No built-in floor**, unlike ADR-REFUSAL: a format signature is a fact, a PII definition is a policy. **The file is required** — `fux setup` writes the starter and every command but `setup`, `tune` and `output` stops without it; `doctor` fails the row. A rule may name a closed-set checksum, `luhn` or `verhoeff` | accepted | **no** |
| [0151](0151_expand.md) | **ADR-EXPAND** | The caller supplies the vocabulary (`--expand`, scored at `expand_weight`) and fuses its own phrasings (`-q`, RRF in rank space); a document matching only supplied terms is never returned | accepted | yes |
| [0152](0152_tabular.md) | **ADR-TABULAR** | Tabular documents — one passage per row, `max_table_rows` (500 -> 20 000; `.fux/tune.toml [index]` since 2026-09-11), and the two silent data losses that hid behind both | accepted | yes |
| [0153](0153_chunking.md) | **ADR-CHUNKING** | A chunk does three jobs and one span cannot do all three — the one fold rule that derives every unit from heading depth with nothing declared, the boundary ladder that makes every document quotable, and why small-to-big was rejected | accepted | yes |
| [0154](0154_doctor.md) | **ADR-DOCTOR** | The health command — fifteen checks, one owner. `warn` is the default and `error` is reserved for a repo a verb will refuse; a check that degrades to `skipped` must name the row that does fail; `fux doctor` never repairs. Carved out of ADR-DOTFUX so a change to one check stops demanding eight records | accepted | yes |
| [0002](0002_LAW-0-authority.md) | **ADR-LAW-0** | L0 — a rule is stated in exactly one ADR and every other artifact links to it; the Law records outrank every other record and a conflicting record is void in the conflicting part; a Law changes only on Arpit's ruling | accepted | yes |

> ## Renumbered again on 2026-09-11 — the laws were given their own range
>
> **Every non-law record moved up by 90**, in its existing order: `0011`
> ADR-CLI → `0101`, through `0064` ADR-DOCTOR → `0154`. The nine law records
> did not move. Ruled by Arpit, 2026-09-11, executed by
> `scripts/renumber-adrs.py` in one commit and deleted with it.
>
> **Why.** A law and an ordinary record sat interleaved on one number line, so
> **accepting a new law pushed nothing and accepting a new record pushed
> nothing — until a tenth law had nowhere to go but `0065`**, next to the
> newest ordinary record and nowhere near the other nine. The range makes the
> law set contiguous permanently, at the price of one mechanical rename.
>
> ⚠ **The first new law will take `0011`, which was ADR-CLI's ordinal until
> today.** That is exactly the vacated-ordinal hazard W-82 ruling 7 named, and
> it is being accepted a second time rather than avoided: the alternative is
> reserving from `0065` and leaving the laws non-contiguous, which is the
> problem. **A frozen document citing `0011` means ADR-CLI; a document written
> after 2026-09-11 citing `0011` means a law.** The only thing that separates
> them is the date on the document and the name beside the number.
>
> ⚠ **What could NOT be corrected, again.**
> [`work/WORKLOG.md`](../../work/WORKLOG.md) is append-only, so **every bare
> number in it older than 2026-09-11 names a different record than it does
> today** — a second layer on top of the 2026-09-06 pass. Resolve any bare
> number through the **name** written beside it, and never through the number
> alone. Bare numbers in prose were deliberately **not** rewritten: guessing
> which four digits in a sentence mean a record is how a renumber lies.
>
> - **What was rewritten:** 1 772 exact `NNNN_slug.md` path tokens across 136
>   files, every one naming a record that exists and moves. Unresolved ADR
>   links were **437 before and 437 after** — the renumber added none, and the
>   437 pre-existing broken links were left broken on purpose, so the diff
>   stays reviewable.
> - **What was skipped:** `.fux/index/` and `.fux/runtime/` (content-addressed
>   — re-ingested instead, never sed'd) and `archive/v0.26*/`, a different and
>   frozen numbering.
> - **This is the third renumber.** The first put two records on `0022`. Each
>   one is a further reason the cite-by-name rule exists.

> ## The number line was renumbered on 2026-09-06, and W-82 ruling 7 was overridden
>
> **`0001`–`0064`, contiguous, no holes.** `0001` is the router
> [ADR-LAWS](0001_LAWS.md); `0002`–`0009` are the eight law records; `0010`
> upward is every other record, in its previous order.
>
> ⚠ **This reverses a standing rule, and the reversal is Arpit's.** W-82 ruling
> 7 said **a vacated ordinal is burned and never reused**, and this register
> carried two burned ones — `0017` (`ADR-ENRICHED`, superseded) and `0025`
> (`ADR-CODES-TABLE`, archived with no successor). **Both holes are gone**: the
> renumber closed them along with everything else.
>
> ⚠ **The rule was right and the cost it named was real.** *"A hole costs
> nothing when every citation is a name; closing one costs every citation in
> the repo."* Closing them cost **996 path links across 52 records**, rewritten
> mechanically in one pass with every link verified to resolve. That was
> affordable **only** because it was scripted and verified; it is not a
> precedent for doing it by hand, and a future compaction is still the failure
> ruling 7 exists to prevent — a previous one put **two records on `0022`**.
>
> ⚠ **What could NOT be corrected.** [`work/WORKLOG.md`](../../work/WORKLOG.md)
> is append-only and 810 KB. **Every bare number in it older than 2026-09-06
> now names a different record**, and those sentences may not be rewritten.
> The same was already true of some of them from the 2026-08-27 pass. **Read a
> bare number in any document older than 2026-09-06 as an ordinal at the time
> of writing**, resolve it through the name beside it, and never trust it
> alone.
>
> - **This is why the cite-by-name rule exists**, and this renumber is the
>   second time the project has paid for the times it was not followed.
> - **`ADR-CONFIDENCE` once existed at two paths** — `0043_confidence.md` and
>   `0045_confidence.md`, same `name:` — while `0043` was also `ADR-LOCKS`.
>   Ruled 2026-08-27: keep the later file, on the substantive ground that its
>   decision 6 binds `SEPARATION_FLOOR` to
>   [ADR-QUALITY](0141_quality-contract.md)'s frozen `t = 0.75`. The duplicate
>   was deleted, and the survivor is now [0051](0142_confidence.md).
> - **A note here once claimed a renumber had already happened** and pointed at
>   `0025_runtime-manifest.md` and `0042_locks.md`, neither of which ever
>   existed. It was false when written. It is retained as the reason nobody
>   should trust a number in an old document.

**`status` and `built` are two different questions, and conflating them is a
mistake this project has already paid for.** `status: accepted` means **the
decision is ratified**. `built` means **the engine does it**. A record can be
accepted and unbuilt — that is a decision made ahead of the code, which is
legitimate and is how [ADR-ENRICH](0137_enrich.md) and
[ADR-QUALITY](0141_quality-contract.md) exist today. **What is not legitimate is
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
claimed by the record carrying its decisions, as [ADR-LOCKS](0140_locks.md)
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
| `src/fux/sources.py` | ADR-CLI | `add`/`remove`/`update` — the writer for **all three** source lists, and the verbs over them. The types list's edits go through `ingest/typesfile.py` (ADR-TYPES decision 12) |
| `src/fux/progress.py` | ADR-CLI | the progress plane — stderr-only, TTY-gated, counts not clocks |
| `src/fux/config.py` | ADR-CONFIG | `fux.toml`'s schema, the opaque `[sources.url.config]` table, and the tables refused by name rather than ignored |
| `src/fux/tune.py` | ADR-TUNE | `.fux/tune.toml` — the loader, the closed key set, the two refusals, and the `[priority]` data. **The priority RESOLUTION is not here**: it lives on `query/rank.py::Weighting`, next to the bound that has to agree with it |
| `src/fux/doctor.py` | ADR-DOCTOR | every check, its level, and the register naming whose subject each one reports on. **Carved out of ADR-DOTFUX for a different DECISION, not a different concern** (Arpit, 2026-09-11): the layout assertions are still ADR-DOTFUX's subject, but this file's subject is the health command itself — and seven records describing one file made the freshness gate demand all eight for any change to any check |
| `src/fux/setup.py` | ADR-DOTFUX | the second scaffolding moment — the consumer-owned files, write-if-missing |
| `src/fux/store/` | ADR-INDEX-LIFECYCLE | canonical bytes, shard addressing, writer/reader, collisions, and the declared record shape |
| `src/fux/store/fuxdir.py` | ADR-DOTFUX | the `.fux/` layout generator — and the **three** kind declarations (`COMMITTED`, `DERIVED`, `ACQUIRED`) the generated README table is built from |
| `src/fux/store/acquired.py` | ADR-ACQUIRED | the retained-bytes plane — content-addressed blobs, the advisory manifest, `sweep` and `evict`. **Carved out of `store/`'s claim for a different DECISION, not a different concern**: everything else under `store/` is the committed index, and this is the one plane that is neither committed nor rebuildable |
| `src/fux/ingest/` | ADR-INGEST | git-dir walk, parse, edges — writes the committed plane |
| `src/fux/ingest/priors.py` | ADR-INGEST | ⚠ **covered by the directory claim, and described by no record's decisions.** It computes the supersession and recency priors and writes `mtime` and `superseded` into the committed record; ADR-RECORD documents the properties and ADR-TUNE the weights, but the module's own behaviour is unrecorded |
| `src/fux/ingest/extract.py` | ADR-EXTRACTED | what extraction *promises* — title, phrases, terms and per-field lengths, taken from the bytes and nothing else |
| `src/fux/ingest/sourcelist.py` | ADR-URL-LIST | the one line grammar `.fux/sources/dirs` and `.fux/sources/urls` are parsed by — and the `TYPES` entry vocabulary, which `fux source --types` checks against and `fux setup` reads the old `.fux/sources/types` with |
| `src/fux/ingest/fuxignore.py` | ADR-FUXIGNORE | `.fux/.fuxignore` — the `.gitignore` grammar, the last-match-wins resolution, and the duplicate-pattern warning. **Carved out of ADR-INGEST's directory claim for a different DECISION, not a different concern**: everything else under `ingest/` is a step in the walk, and this is a *precedence rule* over it — the one thing that outranks the type allowlist |
| `src/fux/ingest/typesfile.py` | ADR-TYPES | `.fux/formats.toml` — the closed two-key shape, the one-line editors that refuse a layout they did not write, the refusal of the old `.fux/sources/types`, and its conversion. **Carved out of ADR-INGEST's directory claim on `fuxignore.py`'s precedent**: a *policy over* the walk — what counts as a document — not a step in it |
| `src/fux/ingest/urlsrc.py` | ADR-FETCHER | fux's half of the fetch contract — load, configure, bound, call, normalize |
| `src/fux/ingest/pii.py` | ADR-PII | the redaction matcher, the ruleset digest, and the plane table stating that redaction reaches the committed index and nothing else. Carved out of ADR-INGEST's directory claim on `fuxignore.py`'s precedent — a *policy over* the walk, not a step in it |
| `src/fux/ingest/refusals.py` | ADR-REFUSAL | the refusal matcher — six byte-pure conditions and the always-on magic-byte floor. **Carved out of ADR-INGEST's directory claim on `fuxignore.py`'s precedent**: everything else under `ingest/` is a step in the walk, and this is a *refusal rule* over it |
| `src/fux/decode/` | ADR-DECODE | bytes → Markdown, in one place: the built-in decoders, the registry, the override precedence and the `.fux/decoders/` consumer seam. Separate from ADR-INGEST's claim because the record it carries is a **boundary** — where consumer-supplied dependencies become legal — not a step in the walk |
| `src/fux/decode/csv.py` | ADR-TABULAR | how much of a `.csv`/`.tsv` is read — `.fux/tune.toml [index] max_table_rows`. Carved out of ADR-DECODE's directory claim on `freshness.py`'s precedent: the record is about **tabular documents**, which reaches past `decode/` into how `refer` cites them |
| `src/fux/decode/xlsx.py` | ADR-TABULAR | the same limit, applied per SHEET — a sheet is the workbook's own division, so truncating the fifth because the first four were long would be arbitrary |
| `src/fux/decode/_limits.py` | ADR-TABULAR | the `ContextVar` seam that lets a two-name decoder read committed config without the protocol growing a third parameter (decision 5) |
| `src/fux/derive/` | ADR-T1-ACCELERATOR | T1 build, block maxima, skipping, and the declared runtime shapes |
| `src/fux/query/` | ADR-ASK | the scan, unification, and the display-only resolution after it — bound by the differential law |
| `src/fux/query/rank.py` | ADR-RANKING | the one scorer and the one sort, and `Weighting`, which is where every document multiplier must travel to reach the pruning bound |
| `src/fux/query/bm25f.py` | ADR-RANKING | BM25F, `Scoring`, and `derive_wlen` — the one place the weighting arithmetic exists |
| `src/fux/query/analyzer.py` | ADR-RANKING | split, lowercase, stopword, stem, hash — in that order, shared by ingest and query |
| `src/fux/query/stem.py` | ADR-RANKING | the Porter implementation, checked against the published test vectors |
| `src/fux/query/tokenize.py` | ADR-RANKING | the shim both `ingest/` and `query/` import, which is what makes the two sides agree **by construction** rather than by review |
| `src/fux/query/rerank.py` | ADR-RERANK | proximity reranking — carved out because it is the one thing under `query/` that reads the **working tree** rather than the committed index, and because the decision it carries is a *refusal* |
| `src/fux/query/confidence.py` | ADR-CONFIDENCE | the four signals and the band, computed from what ranking already produced |
| `src/fux/query/expand.py` | ADR-EXPAND | the `Expansion` object — what to score, what the user actually asked, and at what weight. Carved out of `query/` because the decision it carries is a **refusal**: a document matching no original term is not ranked low, it is not returned |
| `src/fux/query/fuse.py` | ADR-EXPAND | reciprocal rank fusion for `-q`. **A revival, not a restoration** — the deleted module fused SCORES; this one fuses ranks, which is why it comes back under a record rather than off the port list |
| `src/fux/query/provenance.py` | ADR-PROVENANCE | the derivation, the receipt, the journal and `verify`'s four-state verdict. **Carved out of `query/` for a different DECISION, not a different concern**: everything else under `query/` answers a question, and this answers *how the answer was reached* — and it is the one module in the tree that may write a plaintext use record (L8, as reverted) |
| `src/fux/output_config.py` | ADR-OUTPUT | `.fux/output.toml` — three roots (`[cli]`, `[cli.json]`, `[mcp]`), the two closed key sets (`CLI_VERBS`, `MCP_KEYS`), and the precedence chain (flag -> `[cli.json.<verb>]` -> `[cli.json]` -> `[cli.<verb>]` -> `[cli]` -> bypass -> `FuxError`). **Since 2026-08-28 the file, once in effect, is the sole source of truth** — an unset key errors rather than falling back to `BUILT_IN`. **Top-level, beside `tune.py`, because it is a peer of it**: same shape, different boundary — `tune.py` changes which documents come back, this changes how they are shown |
| `src/fux/enrich.py` | ADR-ENRICH | `fux enrich --plan/--check` — the deterministic halves |
| `src/fux/mcp.py` | ADR-MCP | the stdio JSON-RPC server — three tools, stdlib-only, warm across calls. **`answer` is deliberately absent**: the agent is the answerer |
| `src/fux/graph/` | ADR-GRAPH | edges lifted into adjacency, unseeded label-propagation communities, PPR-lite, and the three relational verbs. Owns `.fux/runtime/graph.json` |
| `src/fux/maintain/` | ADR-MAINTENANCE | the git hooks and their installer, the deferring runner, the write lock, the daemon and the local state files. **L5's write-time check is deliberately NOT here** — it lives in `store/writer.py`, because a check beside the thing it guards cannot be skipped |
| `src/fux/maintain/mergedriver.py` | ADR-MERGE-DRIVER | the merge driver itself — carved out because its failure mode and its gate are its own |
| `src/fux/refer/` | ADR-REFER | source · freshness · chunk · rescore · assemble. **Imports no transport**: the consumer's fetcher is injected |
| `src/fux/refer/_chunk.py` | ADR-CHUNKING | what a passage IS — the fold rule that derives row/unit/section/file from heading depth, the universal table rule and the paragraph→line→word ladder. Carved out of ADR-REFER's directory claim on `freshness.py`'s precedent: the subject reaches past `refer/` into what decoders EMIT |
| `src/fux/refer/freshness.py` | ADR-URL-FRESHNESS | the six verdicts and the policy object — the **claim-strength vocabulary**, which now reaches past `refer/` into the output schema and `fux verify`. Carved out of ADR-REFER's directory claim on `arc.py`'s precedent |
| `src/fux/refer/arc.py` | ADR-CACHE | the content cache, keyed `(loc, sha)` so a hit cannot change an answer |
| `src/fux/refer/fetchcache.py` | ADR-CACHE | the TTL fetch store — the only place in the engine that reads a wall clock |
| `src/fux/templates/` | ADR-FETCHER | the two shipped fetchers as package data; **bytes, never imported** |
| `src/fux/templates/pii.toml.txt` | ADR-PII | the shipped starter rules, written into every repo by `fux setup` — the safe ones enabled (credentials, email, PAN, US SSN/ITIN/MBI, Canadian SIN), the risky ones commented out with what each still over-matches (decisions 12 and 12a) |
| `src/fux/templates/refusals.toml.txt` | ADR-REFUSAL | the six shipped starter rules. Carved out of ADR-FETCHER's `templates/` claim on `ENRICH-SKILL.md`'s precedent — it is data a consumer edits, not a fetcher |
| `src/fux/templates/agents/` | ADR-AGENT-POLICY | the canonical agent policy and its per-vendor renderings, shipped as wheel package data (`setup.py` itself stays with ADR-DOTFUX — one component, one owner) |
| `src/fux/templates/agents/ENRICH-SKILL.md` | ADR-ENRICH | the generation half — a skill rather than code, because a model call may not live under `src/` |
| `src/fux/templates/agents/DECODER-SKILL.md` | ADR-DECODE | how to write or edit a decoder — a **build procedure for one plane**, not a rendering of the archived-results policy |
| `tests/test_regression_runs.py` | ADR-RS | the per-run contract for a conformance run. **The harnesses are not claimed here**: a harness belongs to the feature it measures, the discipline belongs to the record |
| `tools/pruning-eval/` | ADR-POSTINGS | the gate harness and its frozen pre-registrations, held by the record that owns the pruning decision and carries its standing law |
| `tools/maintenance-bench/` | ADR-MAINTENANCE | the hook-latency and merge-driver harness. **One file runs both, and a component is owned once** |
| `tools/pii-probe/` | ADR-PII | what a rule would remove from a real corpus. The only thing that can see an over-broad rule — `doctor` compiles patterns and structurally cannot |
| `tools/refusal-probe/` | ADR-REFUSAL | the shipped rules against real captured responses, and the runnable form of this record's veto condition. Owned by the record whose claim it tests |
| `tools/refer-bench/` | ADR-REFER | the latency harness and its frozen pre-registration — a real `http.server` behind the **consumer's own generated fetcher**, so the measured path is the shipped one |
| `tools/refer-budget-sweep/` | ADR-REFER | the assembler-vs-greedy budget sweep and its frozen pre-registration |
| `tools/differential/` | ADR-T1-ACCELERATOR | the differential-law harness and its bench. ⚠ **No test imports it**, so it can break silently — and has |
| `tools/quality-controls/` | ADR-RS | the two controls **decision 15 is owed** — a content-free matched-length placebo and a decoy query set. Owned by the record that demands them, not by ADR-CONFIDENCE whose behaviour they test: a control belongs to the measurement discipline, so changing what a control IS updates the rule rather than the feature. ⚠ **The third, the sealed subset, is NOT built** and decision 15 keeps its `NOT BUILT` marker |
| `tools/archived-signal-eval/` | ADR-ARCHIVED-CONTENT | the live-vs-archived contamination instrument, its frozen pre-registration and its query set. Owned by the record whose claim it tests, because this measures a **feature gate** and takes no `R` id |
| `tools/graph-bench/` | ADR-GRAPH | cost-attribution profiler for the graph lane — not a gate |
| `tools/quality/` | ADR-QUALITY | the frozen quality contract — the declared query mix and the published cost of an error — **and `goldens.py`, the schema that keeps the rank contract and the relevance set apart** (decision 12). The mix and the cost are a **frozen instrument, not a harness**; `goldens.py` is the one executable thing here, and it exists because decision 12's rules are mechanical: an undeclared relevance list, or a `doc` outside its own relevance set, is refused rather than trusted |
| `tools/vector-gate/` | ADR-RS | W-106's instrument — does a **contextual** embedder fused by RRF reach DENSE-CHUNK's frozen bar, and **do two implementations of one model produce the same vector**. ⚠ Held here by **decision 10's fallback**, the `tools/t2-eval/` precedent: the record it belongs to (`ADR-VECTORS`) **does not exist** — W-112 is blocked on this instrument's own result, and a proposal is not a valid owner. It moves to `ADR-VECTORS` if and when that record is accepted |
| `tools/t2-eval/` | ADR-RS | a harness whose feature record was retired, held here by ADR-RS decision 10's fallback. **A retired record cannot own anything, and a proposal is not a valid owner** |

<!-- OWNERSHIP-TABLE-END -->

---

## Describes — which record's subject REACHES INTO a component it does not own

**A second, additive relation** ([ADR-OWNERSHIP](0146_ownership.md)). Ownership
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
| `src/fux/ingest/run.py` | ADR-PII | the redaction pass, and its position between `content_sha` and `extract_fields` — decision 3, which is the whole record. Also `_pii_ruleset_moved`, the reuse invalidation. Owned by ADR-INGEST for the walk |
| `src/fux/enrich.py` | ADR-PII | `enrich=` for `url:` documents — `_document_text` reading the retained blob, and the single synthetic `.fux/sources/urls` scope. Owned by ADR-ENRICH for enrichment itself |
| `src/fux/ingest/sourcelist.py` | ADR-PII | `enrich` on the URL list, resolved through the same three layers as `keep` and `ttl` |
| `src/fux/config.py` | ADR-PII | `[sources.url] enrich` — the source-wide layer |
| `src/fux/cli.py` | ADR-PII | `_require_pii_rules` and `PII_EXEMPT` — decision 17's refusal, placed before dispatch so a verb added later is gated without knowing it. Owned by ADR-CLI for the verb surface; the rule and its exemptions are this record's |
| `src/fux/setup.py` | ADR-PII | writes `.fux/pii.toml` from the starter, write-if-missing — the half of decision 17 that makes the refusal fixable. Owned by ADR-DOTFUX for scaffolding |
| `src/fux/store/fuxdir.py` | ADR-PII | `pii.toml`'s row in `COMMITTED_FILES` — **the ruleset is committed, and that is the decision** (decision 1): a redaction rule that lived on a gitignored path would redact one clone and not the next, so the file has to sit in the category `fux doctor` audits. Owned by ADR-DOTFUX for the layout |
| `src/fux/ingest/urlsrc.py` | ADR-ACQUIRED | retention lives in `fetch_all()` and **never inside a fetcher** (decision 5) — W-86 P8's precedent, so every fetcher gains it with no line changed in any of them. Owned by ADR-FETCHER for the contract itself |
| `src/fux/ingest/urlsrc.py` | ADR-REFUSAL | the refusal check sits in `fetch_all()`, **after `_unpack` and before persist and decode** (decision 1) — the ordering is the decision, and it lives in a file this record does not own |
| `src/fux/ingest/urlsrc.py` | ADR-URL-FRESHNESS | `UrlEntry.ttl`, and `resolve_urls` applying the same three layers to it as to `keep` — a per-URL freshness bound resolved inside the ingest module |
| `src/fux/ingest/sourcelist.py` | ADR-URL-FRESHNESS | `ttl` is the **first typed attribute** in the grammar: `Attribute` grew an optional `validate` callable because a duration cannot be a closed enum. Owned by ADR-URL-LIST for the grammar itself, constrained here |
| `src/fux/ingest/sourcelist.py` | ADR-ACQUIRED | `keep`, and its default flipping to `true` (decision 4) — a value in a file this record does not own |
| `src/fux/config.py` | ADR-ACQUIRED | `[sources.url] keep` and `acquired_max_bytes` — the source-wide layer and the store's bound |
| `src/fux/config.py` | ADR-URL-FRESHNESS | `[sources.url] ttl`, validated by the source list's **own** duration grammar rather than a second copy, so `--ttl 1x` and a hand-written `ttl=1x` fail identically |
| `src/fux/refer/__init__.py` | ADR-URL-FRESHNESS | both `as-ingested` fallback points in `_obtain`, and `min(policy, declared)` — decision 11's arithmetic, which is where a per-URL value is prevented from widening a caller's policy |
| `src/fux/refer/source.py` | ADR-URL-FRESHNESS | `from_acquired`, and decision 6's rule that it **imports** `_decode_fetched` and `sanitize` rather than reimplementing them — the property the whole fallback rests on |
| `src/fux/store/fuxdir.py` | ADR-ACQUIRED | the `ACQUIRED` declaration and its `.gitignore` line. Owned by ADR-DOTFUX for the layout; this is the record that added the third kind |
| `src/fux/mcp.py` | ADR-OUTPUT | decisions 11, 16 and 17 reach in directly: `[mcp]`'s closed key set (`top` only, `band` refused by name), `tools/list` advertising the RESOLVED `top` rather than a literal (the W-83-class defect this decision exists to prevent), and `[mcp]` being loaded once at `serve()` start rather than per search. Owned by ADR-MCP for the protocol itself; this is a rendering decision reaching into the module that serves it |

| `src/fux/query/__init__.py` | ADR-ANSWER | `cmd_answer` and both printers live here — `ANSWER_TOP`, the refer/index fork, `_freshness_of`. ⚠ **Added 2026-09-05 because this record owned NOTHING and therefore could never be opened by the gate**: W-108 rewrote the `answer` verb and the freshness check demanded ADR-ASK, ADR-CONFIDENCE, ADR-OUTPUT, ADR-REFER and ADR-URL-FRESHNESS — every record except the one whose entire subject is the verb. Owned by ADR-ASK for the scan and unification |
| `src/fux/query/refer_answer.py` | ADR-ANSWER | the seam between `cmd_answer` and `refer()` — the candidate list, and `_load_fetchers`' per-URL dispatch. Owned by ADR-ASK under its `src/fux/query/` claim |
| `src/fux/refer/_rescore.py` | ADR-RERANK | `passage_boost` and the bounded multiplicative uplift reach in here (decision 9) — the same constant that reorders documents scores their passages. Owned by ADR-REFER under its `src/fux/refer/` claim |
| `src/fux/maintain/urlstate.py` | ADR-REFUSAL | `refused` and `record_refusals` — the counter's storage, in the file ADR-MAINTENANCE owns, on `rate_limited`'s shape with the key turned from host to rule |
| `src/fux/ingest/urlsrc.py` | ADR-URL-FRESHNESS | `_record_refusals` in `fetch_all()` — see ADR-REFUSAL decision 11; the counting sits beside the refusal check the row above places |
| `src/fux/ingest/sourcelist.py` | ADR-ARCHIVED-CONTENT | `archived` on both lists — `dirs` since 2026-08-22 and `urls` since 2026-09-11 (decision 1a), the same name, values and default on each. ⚠ **Added because this record OWNED NOTHING in `src/` and could therefore never be opened by the freshness gate** — the [ADR-ANSWER](0105_answer.md) precedent above, exactly: W-126 amended this record and the gate demanded seven others instead |
| `src/fux/ingest/urlsrc.py` | ADR-ARCHIVED-CONTENT | `UrlEntry.archived`, and `resolve_urls` applying **two** layers to it where `keep` and `ttl` take three — the absence of a source-wide layer is decision 1a's call, not an omission |
| `src/fux/ingest/run.py` | ADR-ARCHIVED-CONTENT | `_archived_url_ids` and `_with_archived` — the declaration reaching a record, including a CARRIED one, which is the half that makes a retired page declarable at all. Owned by ADR-INGEST for the walk |
<!-- DESCRIBES-TABLE-END -->

