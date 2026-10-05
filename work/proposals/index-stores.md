---
type: Proposal
title: Index stores — the index may live in git or in a database; one store boundary, a writer and a reader
description: Arpit's ask (2026-10-04, clarified 2026-10-05) — today the index is committed to a repository; in future it may live in a database outside any repository, with fux's writer and reader as separate modules against it, and both kinds of index existing in parallel. Proposes lifting the existing store/reader + store/writer seam into one store boundary with two implementations (`git` = today's JSONL shards, `sql` = SQLite first, Postgres second), one writer publishing generations, readers syncing a generation into the local derived plane so `fux ask` stays a local, offline process. Reader and writer ship as separate packages over a shared core — the writer Python only, the reader Python and Node (ruled 2026-10-05) — while `fux-engine` stays the all-in-one distribution exactly as today, and the generation carries the ranking knobs so a repo-less reader ranks identically. Database research: SQLite is the format (a generation file at a path or on object storage/static HTTPS), PostgreSQL the one hosted server. Nothing committed changes shape. Seven forks are Arpit's; F4 (a Node writer) is ruled no.
status: proposed
timestamp: 2026-10-05T00:30:00Z
---

# Index stores — git today, a database tomorrow, the same index either way

**Arpit, 2026-10-04 (Cowork):** *"Right now fux writes everything in JSONL
files. I want a feature where it can write the data in a vector DB or an SQL
DB as well … the configuration can write it either into a DB or into a JSONL
file."*

**Arpit, 2026-10-05, clarifying the first draft:** *"I don't want SQLite to be
git-committed. The way I was thinking about it: right now the index is present
in git, but in future the index can be present in a DB, not in a repository.
Fux can have a writer and a reader, two separate modules, and everybody can use
it. Both can exist in parallel."*

**Status: proposed, not ruled, not built.** Research and a recommendation
only — no code, no record change. Cowork ratifies; Claude Code builds.
*(The first draft of this file, 2026-10-04, proposed a derived "sink" plane
beside the git index. That reading was wrong and is kept only as shape C
below, because one piece of it survives as the bridge between the two stores.)*

## Recommendation, first

1. **Name the seam that already exists and make it the boundary.** Every
   Python read of the committed index goes through one function,
   [`store/reader.py::read_index(root)`](../../src/fux/store/reader.py) (19
   call sites: query, graph, mcp, serve, doctor, enrich, correct, sources),
   and every write through one,
   [`store/writer.py::write_index(root, records)`](../../src/fux/store/writer.py)
   (ingest, maintain). Node mirrors it in
   [`node/src/store/reader.mjs`](../../node/src/store/reader.mjs). **The
   writer and the reader Arpit asked for are already two modules** — what they
   lack is a second implementation and a config key that picks one. This is
   Lucene's `Directory` move: the engine talks to an abstract store; where the
   bytes live is the implementation's business.
2. **Two stores, same records.** `store = "git"` is today's `.fux/index/*.jsonl`,
   byte for byte, no change. `store = "sql"` is the index held in a database
   **outside any repository** — a SQLite file at any path (zero dependencies in
   both runtimes), or a Postgres database by DSN (a dependency each side,
   allowed since L2's 2026-09-06 amendment). The *record* is identical in both:
   the canonical JSON object SR-INDEX-RECORD already defines. A sql store holds
   the same `id · loc · sha · terms · edges …` — hashes, never content (L3) —
   and nothing a git store could not.
3. **One writer, many readers, by generation.** The writer (`fux ingest` on
   CI, or one person's machine) writes a complete record set under a new
   **generation** in one transaction, then flips the store's `current` pointer
   — the database form of today's tmp-file-and-rename. Readers only ever see
   `current`. A second writer that finds `current` moved since it read refuses
   and says so (optimistic; the merge driver's *higher `ver` wins* stays the
   per-record rule). In sql mode the generation **replaces** `write.lock`
   (SR-LOCKS) — the transaction is the mutex.
4. **The reader syncs, it does not query the server.** `fux ask` stays *"a
   local process reading local files"* (`.fux/README.md`): a reader fetches
   the current generation once into its derived plane (`.fux/runtime/`, or
   `~/.cache/fux/<index>/` when there is no repo) and builds the accelerator
   from those records exactly as it builds it from shards today. The sync is
   the **third fenced, opt-in networked path** under L5 (after URL ingest and
   `answer`'s refer), announced on stderr like the other two. Ranking, the
   band, the graph — all still arithmetic over local bytes, in two languages,
   byte-equal. **This is the design choice that keeps L4, L5 and L9 intact at
   once** (§3 says how), and it is **F1** if Arpit wants the other model.
5. **"Both in parallel" is true at two levels.** Across repos: some run
   `git`, some `sql`, same engine, same verbs, same `--json`. Within one repo:
   a `git` index may be **published** into a `sql` store (`fux publish`, the
   surviving half of the sink draft — shape C) so a team server mirrors what
   the repo commits; the repo stays the source of truth. The reverse (a sql
   index written back into a repo) is not offered: it would make `git` a
   cache of a server, which inverts what fux is.
6. **Deterministic at the record level, stated once.** L4 today reads as
   *same sources → byte-identical shards*. The property that actually
   carries the engine is *same sources → byte-identical canonical record set
   and root digest*; the git store makes that into file bytes, the sql store
   keeps it as a digest column. `fux ingest --check` compares digests on
   either store. One clarifying sentence in SR-INDEX-LIFECYCLE, no change to
   the law text — **F6**.

7. **Reader and writer ship as separate packages** (`fux-reader`,
   `fux-writer`, over a shared `fux-core`; **the writer is Python only, the
   reader Python and Node** — ruled 2026-10-05) **and `fux-engine` stays
   everything combined, exactly as today** — same name, same install, same
   verbs on PyPI and npm; the split adds two smaller doors, it closes none — a chat agent's backend installs only the reader, a git hook
   only the writer. The generation **carries the ranking knobs** so a reader
   with no repo ranks exactly as every other reader of that generation. §8.
8. **SQLite is the format, Postgres is the server.** The default `sql` store
   is a SQLite generation file at a path, on a shared volume, or on object
   storage / static HTTPS (no database server at all); PostgreSQL is the one
   hosted database supported when a consumer wants ACLs, several writers and
   `NOTIFY`. §9 has the table.

## §1 — What a database index is for (the cases that are not "a bigger repo")

| case | why git cannot be the store | what the sql store gives |
|---|---|---|
| **A knowledge base with no repo** — a wiki, a Confluence space, a shared drive, read by agents | there is no tree to commit into; the "repo" would exist only to hold `.fux/` | one index, one DSN, every agent and MCP server reads it; the writer is a scheduled `fux ingest` |
| **Org-wide, many repos, one question** | each repo holds its own index; nothing asks across them | one store, many indexes (`index_id`), or one index whose `loc` carries a source prefix — **F3** |
| **Scale** — this repo is 2 177 documents / 40 MB of shards; at 100 000 documents the committed plane is ~2 GB of JSONL in every clone | SR-INDEX-LIFECYCLE: *"committed index size is measured, never gated"* — honest, and a ceiling | the clone carries `.fux/` config only; the reader syncs one generation (a 40 MB download, once, not a 2 GB history forever) |
| **Readers who are not developers** — a support team's agent, a dashboard | they do not clone repos | a DSN and the Node bundle |
| **Access control on the index itself** | git grants the whole tree | the database grants the index; the sources keep their own ACLs (L3 unchanged) |

What it does **not** give: content, meaning, or ranking inside the database.
The store holds what the shards hold. A vector column is not a record (§4).

## §2 — The store boundary, sketched

**The protocol (Python; the Node twin mirrors the read half).**

```
class IndexStore(Protocol):
    def header(self) -> dict | None              # _format, analyzer, identifiers digest
    def read_index(self) -> dict[str, dict]      # {id: record}, current generation
    def generation(self) -> str                  # root digest of the current record set
    def write_index(self, records, *, ids_digest) -> Generation   # whole set, atomic
    def register_rows(self) -> list[Row]         # W-266's file in git; a view in sql
```

`git` implements it with today's code moved, not rewritten — `iter_shard_paths`,
`read_shard`, the merge-marker refusal, `_atomic_write`. `sql` implements it
over the standard library's `sqlite3`, and over `psycopg` when the URL says
`postgres://`.

**The sql schema — the record, flattened, plus the generation.**

```
generations (gen TEXT PRIMARY KEY, root_sha TEXT, analyzer TEXT, identifiers TEXT, _format TEXT, written_at TEXT)
current     (one row: gen)                                -- flipped last, in the same transaction
documents   (gen, id, loc, sha, src, mode, archived, mtime, ver, decoder, fetcher, record JSON)
terms       (gen, id, term_hash, field, tf)              -- indexed on (gen, term_hash) for the sync's postings
edges       (gen, id, dst, kind, grade, al)
```

`documents.record` holds the **canonical JSON of the whole record** — the
same bytes a shard line would hold — so the reader rebuilds records
byte-identically and the root digest is computable without trusting the
flattened columns. The flattened columns exist for SQL consumers and for
`fux doctor`; `terms`/`edges` exist so a future direct-query reader (shape B)
has something to query without a redesign. `written_at` is on `generations`,
never on a record: a wall clock is a fact about a run (the W-199 `outcome`
lesson), and a generation is a run.

**Configuration (template, every key required — L12).**

```toml
[index]
store   = "git"                        # "git" | "sql"
shards  = 256                          # git only
git_timeout_s = 120                    # git only

# Present only when store = "sql". The index then lives HERE and .fux/index/ is absent.
# [index.sql]
# url      = "env:FUX_INDEX_URL"       # sqlite:///abs/path/index.sqlite  |  postgres://host/db
# index_id = "acme-knowledge"          # one database may hold many indexes
# sync_dir = ".fux/runtime"            # where a reader keeps the synced generation; "~/.cache/fux" when no repo
```

**`env:` is how a secret satisfies L12**: the key is present and names where
the value is; fux refuses a missing variable by name, exactly as it refuses a
missing key. A DSN with a password is never a committed literal.

**What the verbs do in sql mode.**

| verb | git store (today) | sql store |
|---|---|---|
| `fux ingest` | writes shards, REGISTER, then builds | writes one generation, flips `current`, then syncs + builds locally |
| `fux ingest --check` | re-derives, compares shard bytes | re-derives, compares root digest to `current` |
| `fux build` | derives runtime from shards | **syncs** `current` if the local generation differs, then derives — the one networked step, fenced and announced |
| `fux ask/find/answer/explain/graph/path`, `fux mcp`, `fux serve` | local | **local** — same code, same bytes, after one `build` |
| `fux doctor` | shard health, register drift | reachability, `current` vs local generation, who wrote it, how stale |
| `fux hooks` / merge driver | yes | **not applicable** — doctor says so instead of installing them |
| `fux publish` *(new, shape C, F5)* | — | push a git store's current record set into a sql store as a generation |

**What stays in the repository when the index does not.** All of `.fux/`
except `index/`: `fux.toml`, `sources/`, `decoders/`, `fetchers/`,
`observers/`, `enrich/`, `pii.toml`, `tune.toml`, the agent guides. The
consumer-owned code and the policy are still the repo's; only the derived
statistics moved. SR-DOTFUX's table gains one word on the `index/` row:
*committed — when `[index] store = "git"`*.

**Node.** The Node bundle today reads shards (`reader.mjs`) and, after W-242
Tier 2, builds the runtime. For a sql store it needs the read half of the
boundary: `node:sqlite` (unflagged since 22.13.0 — L8's floor is 22) for a
SQLite URL; `pg` (MIT) for Postgres — a dependency the bundle would carry.
**There is no Node writer — ruled** (Arpit, 2026-10-05: *"the writer will
always be Python, but the reader will be Python as well as Node"*). Node never
writes an index or a generation; W-242's Node *build* of the derived runtime
is a reader-side derivation and is untouched by this. F4 is closed.

## §3 — The laws, one by one

- **L4 — deterministic.** Same sources, same canonical record set, same root
  digest, on either store; the git store additionally makes it file bytes.
  No model, no clock on a record. The reader rebuilds the accelerator from
  the synced records with the same code → Python and Node stay byte-equal.
- **L5 — offline by default.** The read verbs never open a socket; **only the
  sync inside `fux build`** does, fenced, opt-in by `[index.sql]`'s presence,
  announced on stderr. A reader that has synced once works on a plane.
- **L9 — a use record is never committed.** This is the strongest reason for
  the sync model over direct querying: a database server **logs statements**.
  A reader that ran its postings lookups against a shared Postgres would
  leave every term hash of every question in the server's log — a use record
  on a shared host, outside anyone's repo and outside fux's control. A sync
  fetches a generation and never sends a query. Shape B cannot pass this.
- **L3 — content never durable.** Unchanged: the store holds hashes, paths,
  display headings — what the shards hold. A sql store is more exposed than a
  repo only in who can reach it, which is the database's ACL, not fux's.
- **L6 — say "index", not "db".** Kept, and sharper: the index *lives in* a
  database; it is not one. The key is `store`, the values are `git` and `sql`;
  no flag says `db`. SR-LAW-6's "so where's the data?" still has the answer
  *there isn't any*.
- **L2 — $0, FOSS.** SQLite: public domain, in both stdlibs. Postgres: its own
  licence. `psycopg` LGPL, `pg` MIT — dependencies, permitted since 2026-09-06,
  **and the first ones on the read path**, which L2's amendment should be read
  against before F2 is ruled. **Refused on L2 as much as on L4:** `pg_search` /
  ParadeDB — BM25 inside Postgres — is **AGPL-3.0**, and would put a second
  scorer where fux has one.
- **L10 — bundled output.** Store implementations are engine code, bundled;
  nothing readable lands on the consumer's machine. No new exemption — unlike
  the first draft.
- **L12 — values in config.** Every key above is in the template; `env:` names
  a variable rather than inlining a secret.

## §4 — Why a vector database is still not a store

A store holds fux's records; an embedding is not a record — it is a model's
output (L4), usually fetched (L5), never free in the sense L2 means. So
`store = "vector"` does not exist in this proposal, and nothing in fux computes
an embedding. **What a Postgres store does give the consumer for free** is a
place: pgvector or `sqlite-vec` tables **beside** the generation, written by
the consumer's own job (which re-reads the source by `loc`, exactly as the
refer plane does), read by the consumer's own application, and **never opened
by `fux ask`**. A hybrid-ranking arm, if ever wanted, is a separate proposal
measured on the golden ladder — not a column.

## §5 — Shapes compared

| shape | one line | L4 | L5 | L9 | L2 | verdict |
|---|---|---|---|---|---|---|
| **A** store boundary; `git` + `sql`; reader **syncs** a generation, queries locally | this proposal | ✓ | ✓ one fenced step | ✓ | ✓ (SQLite) · deps for Postgres | **recommended** |
| **B** `sql` store queried **directly** — postings, or BM25, computed by the server | fewer local files; a server per question | ✗ a second scorer / server-side arithmetic | ✗ socket per `ask` | ✗ server logs hold term hashes | ✗ pg_search AGPL | **refused for v1**; the schema leaves the door open |
| **C** `git` store + `fux publish` into a `sql` store | the first draft's sink, as a bridge | ✓ | ✓ | ✓ | ✓ | **kept as the within-one-repo "parallel"** — F5 |
| **D** object store (S3-style) as a third store | same boundary, blob per generation | ✓ | ✓ | ✓ | ✓ | later; nothing in A blocks it |
| **E** SQLite file **committed** in the repo | the first draft's misreading | ✗ bytes | ✓ | ✓ | ✓ | **refused** — SR-INDEX-LIFECYCLE already did, and Arpit confirmed 2026-10-05 |

**Why the sync model and not direct query, in one line each:** `fux ask`
stays offline (L5); no question leaves the machine (L9); one scorer, two
languages, byte-equal (L4); a dead server degrades to *stale*, not *down*
(`fux doctor` names the generation age) — the `answer` verb's `cached` verdict
already taught readers what that word means.

**Prior art, each cited for one point.** Lucene's `Directory` — the engine
never knows where bytes live; `FSDirectory` is one implementation among
several. SQLite's *How To Corrupt* — a database file on a network filesystem
with more than one writer is unsafe, hence the **one-writer** rule and the
Postgres backend for shared writing. `node:sqlite` — the zero-dependency Node
read half exists from 22.13. `pg_search` — BM25-in-the-database exists, is
AGPL, and is the thing shape B would become.

## §6 — Forks for Arpit

- **F1 — reader model.** Sync-then-local (recommended) vs direct query (shape
  B). The schema serves both; the laws serve one.
- **F2 — first backend.** SQLite-at-a-path only in v1 (zero dependencies; one
  writer; a shared volume or a server-mounted file), with Postgres in v2 —
  or both at once, accepting `psycopg`/`pg` as the first read-path
  dependencies.
- **F3 — index identity across sources.** One store, many `index_id`s (one per
  repo or space), or one org index whose `loc` carries a source prefix
  (`repo-a/docs/…`, `confluence/SPACE/…`). The first is cheaper and keeps
  `loc` as it is; the second is what "one question across everything" needs.
- ~~**F4 — the Node writer.**~~ **Ruled 2026-10-05: no.** The writer is Python only;
  the reader is Python and Node. (W-242's Node build of the derived runtime is
  not an index write and stands.)
- **F5 — `fux publish`.** Whether the git→sql bridge ships (shape C), and as a
  verb or a `fux build` flag.
- **F7 — a reader in the browser.** Not v1; the SPA's backend is the reader.
  Reachable later from a SQLite generation on static HTTPS (§8, §9).
- **F8 — the package split.** Three distributions (`fux-core`, `fux-reader`,
  `fux-writer`) beside `fux-engine`, which stays the combined one, in the same change as the store boundary
  or as a second step after it. §8 recommends the same change: the boundary is
  what makes the split cut cleanly.
- **F6 — the L4 sentence.** Add to SR-INDEX-LIFECYCLE: *byte-identity is a
  property of the canonical record set and its root digest; the git store
  makes it file bytes.* His word, since it touches a law's rationale.

## §7 — What building it would touch (for the W-nn this graduates into)

- `src/fux/store/` — `boundary.py` (the protocol), `git/` (today's
  `reader.py`, `writer.py`, `format.py`, `resident.py` moved), `sql/`
  (`sqlite.py`, `postgres.py`, `schema.sql`, `sync.py`); `store/__init__.py`
  picks by `[index] store`. The 19 `read_index` call sites change one import.
- `src/fux/derive/_build.py` — sync before derive in sql mode.
- `src/fux/maintain/` — `write.lock` bypassed in sql mode; hooks and the merge
  driver refuse with a message.
- `src/fux/config.py`, `fux.toml` template, `constants.toml` — `[index] store`,
  `[index.sql]`, `env:` resolution.
- `src/fux/doctor.py` — reachability, generation age, writer identity.
- `node/src/store/` — `reader.mjs` behind the same boundary; `sqlite.mjs` via
  `node:sqlite`.
- Records amended in the same change: [SR-INDEX-LIFECYCLE](../../records/0108_index-lifecycle.md)
  (the boundary, F6's sentence, `--check` by digest), [SR-DOTFUX](../../records/0102_fux-directory.md)
  (`index/` conditional), [SR-LOCKS](../../records/0140_locks.md) (generation in sql mode),
  [SR-CONFIG](../../records/0113_config.md), [SR-ACCELERATOR](../../records/0110_accelerator.md)
  (built from records, not from shards), [SR-LAW-5](../../records/0007_LAW-5-offline-by-default.md)
  (the third fenced path — his word), [SR-MERGE-DRIVER](../../records/0130_merge-driver.md)
  and [SR-HOOKS](../../records/0129_hooks.md) (git-only), [SR-NODE-SEARCH](../../records/0153_node-search.md),
  [SR-DOCTOR](../../records/0152_doctor.md), `.fux/README.md` (`index/` row; the *What fux is* paragraph gains *"or in a store you run"*).
- Packaging (§8, F8): `pyproject.toml` → a `uv` workspace with `fux-core`, `fux-reader`, `fux-writer` and `fux-engine` (the combined one, unchanged for its users); `node/` → one reader bundle, core inlined (no Node writer — ruled); `hatch_build.py` per distribution; [SR-CLI](../../records/0101_cli-surface.md) and [SR-API](../../records/0154_api.md) name which package owns each verb and the library surface.
- Tests: the same record set written to `git` and to `sql` yields the same
  root digest and the same `fux ask --json` on both; a reader with a synced
  generation answers with the network fenced off; a second writer against a
  moved `current` exits 1 naming both generations; `fux doctor` reports
  generation age; the import-fence test lists `store/sql/sync.py` as the third
  networked module and nothing else.

## §8 — Reader and writer as separate packages (Arpit's second clarification)

**Arpit, 2026-10-05, 00:25:** *"If you are hosting a DB and you want to build
a separate chat agent in a single-page application, you don't need a writer —
you just need a reader. If you're updating the DB through hooks, you just need
a writer — you don't need a reader. How can the package be structured?"*

**Finding: the split already exists in the module tree; only the distribution
hides it.** `src/fux/` is one wheel (`fux-engine`, `dependencies = []`) and
`node/` is one bundle (`fux-engine`, `fux.mjs`). Inside, the modules sort
cleanly:

| package | holds today's | verbs | installs for |
|---|---|---|---|
| **`fux-core`** · Python + Node | `store/format.py`, `canonical.py`, `recordschema.py`, `schema.py`, `constants.py` + `constants.toml`, `schemas/`, `query/tokenize.py` (the analyzer), `config.py`, `errors.py` — pure functions, **no I/O, no socket** | none | everyone, transitively |
| **`fux-reader`** · **Python + Node** | the store boundary's **read** half (`git`, `sqlite`; `[postgres]` extra), `query/`, `graph/`, `refer/`, `serve/`, `mcp.py`, `api.py`, `observe.py`, `doctor`'s read checks | `ask` `find` `answer` `lexical` `explain` `graph` `path` `serve` `mcp` `verify` | the SPA's backend, an MCP server, any agent host — **no decoders, no fetchers, no CDP, no PII engine, no git** |
| **`fux-writer`** · **Python only** (ruled) | the store boundary's **write** half, `ingest/`, `decode/`, `derive/` (build), `maintain/` (hooks, daemon, merge driver), `enrich.py`, `correct.py`, `identifiers_cmd.py`, `setup.py` + `templates/`, `sources.py`, `tune.py`, `output_config.py` | `setup` `ingest` `build` `add` `remove` `enrich` `correct` `identifiers` `hooks` `daemon` `tune` `output` | CI, a git hook, the one machine that writes — **no ranking, no serve, no MCP** |
| **`fux-engine`** — **everything combined, exactly as today** (Arpit, 2026-10-05) | the CLI; depends on core + reader + writer, or keeps shipping as the single wheel / single bundle it is now | all | what a developer installs today — same name on PyPI and npm, same verbs, same `--json`; nothing changes for them |

**Mechanism (Python).** One repository, one `uv` workspace, three
distributions sharing the `fux` import namespace as PEP 420 packages
(`fux.core`, `fux.reader`, `fux.writer`); **`fux-engine` stays the
all-in-one distribution** — it depends on all three and owns `cli.py`, so
`pip install fux-engine` installs what it installs today, and a consumer who
never hears the words *reader* or *writer* loses nothing. `pip install fux-reader[postgres]` is the SPA
backend's whole install. **Mechanism (Node, L10).** **Node is reader-only — ruled**
(Arpit, 2026-10-05). One bundle, `@fux/reader`, with core inlined so it stays
ONE artefact; **no `@fux/writer` ever**. **`fux-engine` on npm stays what it
is today — the one combined bundle, which on Node *is* the reader** (its own
description already says *"Read a fux index from Node"*). The Python side
alone carries `fux-writer`.

**Doctor splits too.** `fux-reader` ships the read checks (store reachable,
generation age, runtime matches generation); `fux-writer` the write checks
(sources, decoders, PII rules, register drift). The CLI's `doctor` runs both.

**The one thing a repo-less reader needs that it does not have today: the
ranking knobs.** `tune.toml`, `output.toml`, the identifier digest and the
analyzer version live in the repo's `.fux/` — an SPA backend has no repo.
**So the writer publishes them with the generation**: the `generations` row
carries `tune`, `output`, `identifiers`, `analyzer`, `_format` as columns, and
a sql-store reader takes its knobs **from the generation, never from a local
file**. Two readers of one generation therefore rank identically — which is
L4's promise restated for a store with many readers — and a tuning change is
a new generation, visible as such. In git mode nothing moves: the files beside
the index are the generation.

**The SPA, concretely.** Browser → the SPA's Node (or Python) backend →
`import { ask } from '@fux/reader'` → the backend synced a generation from the
sql store at start and on `NOTIFY`/poll → ranks locally → returns `--json`'s
shape (SR-API: *one schema for three readers*). The backend holds the DSN; the
browser never does. **A reader in the browser itself is F7**: the ranking code
is already pure JS, and a SQLite generation on static HTTPS is readable
page-by-page with `Range` requests (sql.js-httpvfs's pattern) — so a
zero-backend SPA is reachable later without a redesign, but it is a new build
target and not v1.

**The hook, concretely.** `pip install fux-writer`; `fux hooks` installs
post-commit → `fux ingest` → one generation → `current` flipped. The hook
machine needs the DSN and nothing else; it never ranks. On CI the same two
commands, no hook.

## §9 — Which database (the research)

**The criteria, from the laws and from §8's two consumers:**

1. FOSS, $0 to run (L2); drivers in **both** runtimes with as near zero
   dependencies as exists (L7, L8).
2. One writer, many readers; an **atomic generation flip**; readers can pull
   one whole generation cheaply (the sync model, F1).
3. Works with **no server at all** when the consumer wants none, and with a
   server when they want ACLs and many writers.
4. Reachable from an SPA's backend over an ordinary network; eventually from a
   browser (F7).
5. Lets the consumer put *their* tables beside the index (vectors, joins) —
   without fux ever reading them (§4).
6. Operational burden proportional to the consumer's size.

| candidate | licence | Py / Node driver | no-server mode | atomic generation | shared writers | SPA / browser | verdict |
|---|---|---|---|---|---|---|---|
| **SQLite file** (path, shared volume, object storage) | public domain | stdlib / `node:sqlite` ≥ 22.13 — **zero deps** | ✓ this *is* the no-server mode | ✓ write `gen-<sha>.sqlite`, rename/flip `current` | ✗ one writer (network FS unsafe — *How To Corrupt*) | backend ✓; browser ✓ via `Range` on static hosting | **the default `sql` store** |
| **PostgreSQL** | PostgreSQL licence | `psycopg` (LGPL) / `pg` (MIT) — one dep each | ✗ | ✓ one transaction + `current` row; `LISTEN/NOTIFY` tells readers a generation landed | ✓ advisory lock or `current` compare-and-set; **row-level security** per `index_id` | backend ✓; browser ✗ (never expose a DSN) | **the one hosted DB to support** |
| libSQL / `sqld` (Turso) | MIT | JS `@libsql/client`; Python **experimental** | ✓ (it is SQLite) | ✓ | ✓ via server; *embedded replicas* = §2's sync model built in | backend ✓ | **attractive fit, not now**: server last tagged Feb 2025, company's focus moved to the Rust "Turso Database", Python driver experimental — the §2 sync gives the same shape on plain SQLite |
| DuckDB | MIT | `duckdb` / `@duckdb/node-api` — native deps | ✓ | ✓ | ✗ single process | DuckDB-WASM reads over HTTP | analytical columnar; strong for term scans, but a native dependency in both runtimes for no capability SQLite lacks here |
| LanceDB / Lance | Apache-2.0 | native deps both | ✓ (files, or S3) | ✓ dataset **versions** — generations as a first-class feature | ✗ | — | vector-first; its BM25 is tantivy's — a **second scorer** (L4); native deps; its versioning is the one idea worth borrowing (we have it: generations) |
| MySQL / MariaDB | GPL | deps | ✗ | ✓ | ✓ | backend | nothing Postgres lacks; weaker JSON, no RLS story, no pgvector-beside |
| MongoDB | SSPL (not OSI) | deps | ✗ | ✓ | ✓ | backend | **fails L2's FOSS clause outright**; not SQL, which the ask named |
| Hosted vector DBs (Pinecone, Qdrant Cloud, …) | varies / paid | SDKs | ✗ | — | — | — | **not a store** (§4): an embedding is a model's output; fails L4 before L2 |

**Recommendation: SQLite is the format; Postgres is the server.**

- **Default `sql` store = a SQLite generation file.** `url = "sqlite:///…"`
  may be a local path, a shared volume, or — the hooks-writer / SPA-reader
  case with no server — an **object-storage or static-HTTPS URL**: the writer
  uploads `gen-<root_sha>.sqlite` and then a tiny `current` file; a reader
  fetches `current`, then the generation it names, once. One writer by rule,
  many readers by construction, no database server anywhere, zero
  dependencies in both runtimes, and F7's browser reader falls out of the same
  file. This is the shape that matches fux's own philosophy — *a local process
  reading local files* — extended by one fetch.
- **Hosted store = PostgreSQL**, when a consumer wants a server: several
  writers (advisory lock + `current` compare-and-set), ACL per `index_id`
  (row-level security), `LISTEN/NOTIFY` so an SPA backend learns of a new
  generation without polling, JSONB for the canonical record, and pgvector
  *beside* for the consumer's own embeddings. Cost: `psycopg` / `pg` as the
  first read-path dependencies (L2's 2026-09-06 amendment allows it; F2 says
  when).
- **Not two formats in one database.** In Postgres the generation is rows,
  not a SQLite blob — the ask said *SQL DB*, and a blob column would make
  Postgres a file server with a licence. The reader's sync (`SELECT … WHERE
  gen = current`) rebuilds the same canonical records either way; the root
  digest proves it.
- **Refused:** MongoDB (SSPL), hosted vector stores (§4), BM25-in-the-database
  of any brand (`pg_search` AGPL; LanceDB/tantivy) — one scorer, in fux, in two
  languages, byte-equal.
- **Watch, don't adopt:** libSQL embedded replicas — if Turso's Rust database
  ships a stable Python driver and a maintained server, it is the §2 sync model
  as a product; the store boundary makes adding it a third implementation, not
  a redesign.

**One sentence on cost for the two consumers Arpit named.** The SPA team
installs `fux-reader`, points it at a DSN or a static URL, and never learns
what a decoder is. The hooks machine installs `fux-writer`, gets a DSN or a
bucket credential, and never ranks anything.

## Graduation trigger

Arpit rules **F1** and **F2**, and names the first index that will live
outside a repository — a team space or wiki something of his will actually
query. Then this file graduates into one `W-nn` with §7 as its key files, and
W-266 (the register's shape) notes which half of it applies to the sql store.

## References

- [`src/fux/store/reader.py`](../../src/fux/store/reader.py), [`writer.py`](../../src/fux/store/writer.py), [`node/src/store/reader.mjs`](../../node/src/store/reader.mjs) — the seam that becomes the boundary.
- [SR-INDEX-LIFECYCLE](../../records/0108_index-lifecycle.md) §Alternatives — SQLite *as the committed plane* refused; this proposal does not reopen it.
- [SR-LOCKS](../../records/0140_locks.md) — the one mutex a generation replaces.
- [SR-LAW-5](../../records/0007_LAW-5-offline-by-default.md) — *"paths, plural"*: the sync is the third.
- [SR-LAW-9](../../records/0011_LAW-9-use-record.md) — why readers sync rather than query a shared server.
- [SR-LAW-2](../../records/0004_LAW-2-zero-cost.md) — the 2026-09-06 amendment that permits `psycopg`/`pg`.
- Lucene `Directory` / `FSDirectory` — the storage-boundary pattern ([lucene.apache.org](https://lucene.apache.org/core/10_3_1/core/org/apache/lucene/store/Directory.html)).
- SQLite, *How To Corrupt An SQLite Database File* — network filesystems and multiple writers ([sqlite.org](https://www.sqlite.org/howtocorrupt.html)).
- Node.js `node:sqlite` history — added 22.5.0, unflagged 23.4.0 / **22.13.0**, release candidate 25.7.0 ([nodejs.org](https://nodejs.org/api/sqlite.html)).
- ParadeDB `pg_search` — BM25 inside Postgres, **AGPL-3.0** ([github.com/paradedb](https://github.com/paradedb/paradedb)).
- sql.js-httpvfs — a read-only SQLite file on static hosting, read page-by-page with HTTP `Range` requests ([phiresky.github.io](https://phiresky.github.io/blog/2021/hosting-sqlite-databases-on-github-pages/)) — F7's browser reader.
- libSQL / Turso — MIT; `sqld` self-hostable; *embedded replicas* are the sync model as a product; server last tagged Feb 2025, Python driver experimental ([layerbase.com](https://layerbase.com/blog/libsql-vs-turso)).
- `sqlite-vec` — MIT/Apache-2.0, vectors supplied by the caller ([alexgarcia.xyz](https://alexgarcia.xyz/blog/2024/sqlite-vec-stable-release/index.html)) — §4's "beside, never inside".
