---
type: Handoff
name: W-282
description: "Arpit's ask (2026-10-18): build the package split from index-stores §8 — fux-core, fux-reader (Python + Node), fux-writer (Python only), with fux-engine still the all-in-one. Researched in Cowork the same day: the split does NOT exist in the module tree yet (~125 cross imports). Ruled 2026-10-18: F1 (L2 amended for role packages), F2 (the reader's `answer` is exactly today's, refer included) and F4 (npm scope `@fux-engine`, first package `@fux-engine/reader`; `@fux` belongs to another npm user). F3 ruled too: the split goes before the database store. Nothing blocks Steps 1–2; Arpit creates the `@fux-engine` npm org before Step 3 (release)."
item: W-282
filed: 2026-10-18
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-18
updated_by: "Claude Code (Opus 5.5)"
ball: agent
---

# W-282 — split fux into a reader, a writer and a shared core

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 0a | The one-install law now allows a reader-only and a writer-only package | the split is lawful | ✅ done |
| 0b | The Node reader is published as `@fux-engine/reader`, under the `@fux-engine` scope | one home for every future fux npm package | ✅ decided — Arpit creates the free npm org before the first release |
| 0c | The reader gives full answers, re-checked against the source — exactly as `fux answer` works today | one meaning of `answer` on every install | ✅ decided |
| 0d | The split goes first; the database work comes after it, and its proposal is updated then | a clear order of work | ✅ decided |
| 1 | Untangle the code so reading and writing stop importing each other (about 125 cross imports today) | a clean line between reader and writer, held by a test | ✅ done 2026-10-18 — uncommitted |
| 2 | Package it as fux-core, fux-reader and fux-writer — fux-engine still installs everything | smaller installs for machines that only read or only write | ✅ done 2026-10-18 |
| 3 | Release all four together, on one version | the split live on PyPI, and on npm per the name call | ✅ 4.0.0 and 4.0.1 on all six names (2026-10-18) |

**The packages and what each install pulls in:** [`architecture-packages.svg`](../architecture-packages.svg) — four on PyPI, two on npm, no third-party package anywhere in the tree.

**Arpit, 2026-10-18 (Cowork):** *"Put this in work item. Research and put this
in work item. We are going to build it out."* — said of the package split in
[`index-stores.md` §8](../proposals/index-stores.md) (B-272).

**Ratified as a direction, not built.** The rulings it stands on are his, from
2026-10-05 and quoted in the proposal: **the writer is Python only; the reader
is Python and Node; `fux-engine` keeps shipping everything combined, exactly as
today** — same name, same install, same verbs, same `--json`.

**Scope: the package split only.** The database store — B-272's F1, F2, F3,
F5, F6: the `sql` store, generations, sync, `fux publish` — stays parked in
[B-272](../BACKLOG.md). The split stands on its own, because what makes it hard
is in `query/`, `refer/` and `derive/`, not in `store/` (Research §2).

## Research (Cowork, 2026-10-18)

### 1. The proposal's central finding is wrong

§8 says *"the split already exists in the module tree; only the distribution
hides it."* An AST walk of `src/fux/` (140 modules), each placed by §8's own
table, finds the opposite. Counts are import edges, one per (importer, target)
module pair:

| edge | count | biggest targets |
|---|---|---|
| reader → writer | **86** | `derive` + `.format` + `.accel` 15 · `tune` 9 · `ingest` 8 · `ingest.extract`/`.parse` 8 · `ingest.pii` 4 · `ingest.urlsrc` 4 · `decode` 4 · `correct` 3 · `output_config` 3 · `maintain.dirty`/`.lastcited` 3 |
| writer → reader | **36** | `query` 7 · `query.identifiers` 6 · `query.bm25f`/`.mined`/`.scan`/`.rank` 6 · `refer` (+`._chunk`, `.freshness`, `.source`) 6 · `graph` (+`.walk`, `.plane`) 4 · `store.reader` 1 |
| core → writer | 3 | `config` → `ingest`, `ingest.routes`, `ingest.sourcelist` |
| core → reader | 2 | `query.tokenize` → `query.analyzer`, `query.identifiers` |
| not placed by §8 | 10 modules | `store/` (`__init__`, `acquired`, `cachedir`, `collisions`, `fuxdir`, `resident`, `nodebundle`), `frontmatter`, `progress`, `schemas` |

**So the split is an untangling first and a packaging change second.** Built
today, `fux-reader` alone would fail at its first import.

### 2. Three of §8's placements cannot stand

- **`derive/` (the runtime build) belongs to the reader, not the writer.**
  `query`, `query.sections`, `graph.plane`, `refer.fetchcache` and `observe` all
  import it, and the derived plane is gitignored and built per machine. A
  machine that only writes never ranks, so it never needs a runtime. →
  `fux build` moves to the reader; the writer's `ingest` stops once the index is
  written; `fux-engine`'s `ingest` still builds afterwards, as today.
- **`fux answer` needs decoders, fetchers and the PII engine.** The refer plane
  re-fetches each cited document from its source (`refer`, `refer.source`,
  `query.refer_answer` → `ingest.urlsrc`), decodes it (`refer` → `decode`,
  `refer._chunk` → `decode._markdown`) and redacts it (`api`, `refer_answer` →
  `ingest.pii`). §8's *"no decoders, no fetchers, no CDP, no PII engine"* is
  true of `ask` and `find`, false of `answer`. → **F2.**
- **Shared pieces move into core**, or reader and writer cannot be independent:
  the analyzer and identifiers (`query.tokenize`, `.analyzer`, `.identifiers` —
  used by `ingest.extract` and `ingest.edges`), the chunker (`refer._chunk` —
  used by `ingest.extract` and `enrich`), `frontmatter`, the source-list
  readers `config` imports, and the **read halves** of `tune`, `output_config`,
  `correct`, `enrich` and `maintain.dirty`/`.lastcited` that `query` reads.
  Engineering, not a fork: Step 1 decides it and a test holds it.

### 3. §8's one-namespace mechanism does not work as written

§8 has three distributions share `fux` as **PEP 420** namespace packages. PEP
420 needs every distribution to ship **no** `fux/__init__.py`. Today
`src/fux/__init__.py` carries `__version__` (hatch reads the version there) and
`from .api import open`, the frozen read API (SR-API). So either `fux-core`
alone ships `fux/__init__.py`, with `open` imported lazily, and the other two
install sub-packages under it (works with pip; editable installs need a
check), or the version and `open` move. Step 1 picks one; SR-API states it.

### 4. The laws

- **L2 — needs his word (F1).** L2: *"Fux is one install with everything it
  needs — no optional extras … no capability that works on one machine and not
  another because of what somebody chose at install time."* A machine with only
  `fux-reader` cannot `ingest`; one with only `fux-writer` cannot `ask`. That is
  that sentence, word for word. A law changes only on his ruling (SR-LAW-0 d3).
  - Same clause, for B-272 and not this item: §8's `fux-reader[postgres]` is an
    **optional extra**, refused as L2 reads today. Named so nobody copies it.
- **L10 — no conflict.** SR-LAW-10 decision 7 puts the Python distribution
  outside its reach; on npm, one bundle per package is still one artefact.
- **L12 — no conflict** if `constants.toml` ships in `fux-core`, which every
  package depends on.
- **L4, L5 — untouched.** No new network path, no new arithmetic. The import
  fence lists networked modules by path, so it moves with them.
- **[W-268](W-268-ingest-under-one-second.md) fits.** A Rust ingest core would
  live in `fux-writer` alone: platform wheels for one package, `fux-reader`
  stays pure Python.

### 5. Names (checked against the registries, 2026-10-18)

- **PyPI:** `fux-core`, `fux-reader`, `fux-writer` are all free (404). A name
  is first come, first served — reserve them early.
- **npm:** §8's `@fux/reader` is **not available as written** — the `@fux`
  scope belongs to an existing npm account named `fux` (no public packages).
  Unscoped `fux-reader` is free. → **F4** (ruled: `@fux-engine/reader`).
- **npm `fux-engine` already is the reader** — its description is *"Read a fux
  index from Node"*, and `node/src/` carries `derive/`, `query/`, `refer/`,
  `graph/` and the `ask`/`answer`/`find`/`graph`/`mcp` verbs, and no writer.

## Package names — final (Arpit, 2026-10-18)

*"Let's go with whatever we had. Four PyPI packages, two npm packages."*

| registry | package | role | today |
|---|---|---|---|
| PyPI | `fux-engine` | everything, exactly as today | published (3.0.1) |
| PyPI | `fux-core` | shared, pure; no verbs | name free |
| PyPI | `fux-reader` | search and answers, refer included | name free |
| PyPI | `fux-writer` | ingest and upkeep, Python only | name free |
| npm | `fux-engine` | unchanged; already the reader bundle | published |
| npm | `@fux-engine/reader` | the Node reader, one file | org to create |

- **PyPI has no scopes**, so the PyPI names stay flat and hyphenated; import
  names (`fux`, `fux.core`, `fux.reader`, `fux.writer`) are unaffected.
  `fux-engine-core/-reader/-writer` was offered and declined.
- **Prefix reservation, later:** [PEP 752](https://peps.python.org/pep-0752/)
  (accepted 2026-06-29) lets a PyPI organization reserve a prefix; reserving
  `fux` would cover `fux` and every `fux-*` name, `fux-engine` included. Not
  confirmed live on PyPI on 2026-10-18; `fux` itself was free that day. When
  PyPI offers it, Arpit reserves `fux` — his hands, not a blocker.
- **Until published, the three new PyPI names can be taken by anyone.**
  Diagram: [`architecture-packages.svg`](../architecture-packages.svg).

## Rulings and open calls

- ✅ **F1 — L2. RULED 2026-10-18.** Arpit: *"For first one, go with the
  recommendation."* SR-LAW-2 now says: *"`fux-engine` is the one install;
  `fux-reader` and `fux-writer` are role packages — each complete for its role,
  none with optional extras."* CLAUDE.md regenerated.
- ✅ **F2 — `fux answer` comes with the reader, unchanged. RULED 2026-10-18, option (a).**
  Arpit: *"in reader can answer read the whole document again can it be a full
  copy exactly how it works today"*. So the reader's `answer` is today's
  `answer`: same code, same refer plane (re-read the whole document from its
  source, decode, redact, re-score, quote the best passage with a fresh sha and
  verdict), same output. Nothing is stored — the document is re-read each time
  (L3), with the existing `.fux/acquired/` and `--cache-ttl` paths unchanged.
  DoD 10 now checks it. The detail he was shown before ruling:
  - **What `answer` does today.** It ranks from the index, then *refers*: it
    re-reads the winning document from its source (a file in the repo, or a URL
    through `.fux/fetchers/`), decodes it (`decode/`, `.fux/decoders/`),
    redacts it (`.fux/pii.toml`), re-scores its passages and quotes the best
    one with a fresh sha and a freshness verdict (`current` / `stale` /
    `unverified` / `cached`). SR-ANSWER decision 1; SR-REFER.
  - **Why "index only" is thinner than it sounds.** The index holds statistics,
    never content (L3). With no refer, `answer` has **no text to quote**. It
    returns the title, heading phrases and the citation, marked *"from the
    index's own structure"* — SR-ANSWER's own `--no-refer` example. That is a
    pointer, not an answer.
  - **What (a) costs.** No new dependencies: `decode/`, `refer/`, `pii` and the
    `http` fetcher are standard library only. The cost is code size, network
    use (refer is already a fenced L5 path, not a new one), and the reader needs
    the consumer's `.fux/` (decoders, fetchers, `pii.toml`) and access to the
    sources. The signed-in-Chrome `cdp` fetcher cannot run on a server, so those
    URLs fall back to `cached` or index-only — the same as today when Chrome is
    closed.
  - **Example.** A support chat-agent backend asks *"what is our refund
    window?"* (a) returns the paragraph from today's policy page: *"Refunds are
    accepted within 30 days…"*, `current`, sha `9f2c…`. (b) returns *"Refund
    policy — Eligibility · Time limits — docs/policy/refunds.md"*, and the agent
    has to open the page itself.
  - **Options.** (a) the reader carries refer — **recommended**: `answer` keeps
    meaning the same thing on every install, and nothing new is downloaded.
    (b) the reader is index-only and `answer` there always behaves like
    `--no-refer`; full answers need `fux-engine`. (c) the reader carries refer
    for repo files only (no fetchers, no URLs) — smaller, but URL sources then
    answer differently on a reader than on the engine, which is the kind of
    install-dependent behaviour the amended L2 forbids inside a package.
- ✅ **F3 — the split goes first. RULED 2026-10-18 (option a).** Parked earlier
  the same day (*"add it as a blocker … keep it in the backlog"*), then ruled:
  *"we will split the packages before the DB work is done and later on update
  the DB proposal."* The store stays in [B-272](../BACKLOG.md); once this item
  lands, `index-stores.md` is rewritten against the split packages (its §8
  corrections included) before B-272 graduates.
- ✅ **F4 — the Node name. RULED 2026-10-18, then re-ruled the same day.**
  - **First ruling:** *"can we have it as @fux/fux-reader, and @fux becomes
    scope for any future packages as well."*
  - **Why it moved:** checked in Arpit's browser, signed in as `aarya11`:
    `npmjs.com/~fux` is another person's **user** account (0 packages, 0
    organizations). npm users and organizations share one namespace, so `@fux`
    cannot be created while that user exists. Arpit: *"I do not have a second
    login."*
  - **Final ruling:** *"Let's go with the first one, @fux-engine/reader, rather
    than fux-reader."* So the Node reader publishes as
    **`@fux-engine/reader`**, and every future fux npm package lives under
    **`@fux-engine`** — the same name as the existing `fux-engine` on PyPI and
    npm. `fux-engine` on npm stays as it is.
  - 🔴 **By Arpit's hand, before Step 3 (release):** create the `@fux-engine`
    organization at `npmjs.com/org/create` (free for public packages; free on
    the registry on 2026-10-18). Steps 1–2 do not wait on it. Asking npm
    support for `@fux` stays open to him and changes nothing here.

## Definition of done

**Step 0 — rulings.**
1. F1–F4 ruled and quoted in this file. ✅ F1 (SR-LAW-2 amended, CLAUDE.md
   regenerated), ✅ F2, ✅ F3 and ✅ F4 done 2026-10-18 — **Step 0 is done.**
   One hand-step stays for Step 3 only: Arpit creates the `@fux-engine` npm org
   before the first release; if it is not there when Step 3 is next, file it as
   its own 🔴 `arpit` item then.

**Step 1 — untangle (no packaging yet).** ✅ **Done 2026-10-18 (Claude Code,
Opus 5.5), in the working tree, uncommitted** — see *Step 1 — what landed*.
2. ✅ A layer map: every module under `src/fux/` placed in `core`, `reader`,
   `writer` or `engine` (`cli.py`, `__main__.py`), stated in
   `records/README.md` §Ownership.
3. ✅ Moves until the graph is layered: `core` imports only `core`; `reader`
   imports `core` and `reader`; `writer` imports `core` and `writer`; only
   `engine` imports both.
4. ✅ **A gate:** `tests/test_package_layers.py`, an AST walk that fails on any
   import crossing the map, so the split cannot rot back.
5. ✅ Both suites green, whole, and `--json` byte-identical before and after on
   this repository's own index (`ask`, `find`, `answer`, `graph`, a fixed query
   set).

**Step 2 — package.** ✅ **Done 2026-10-18 (Claude Code, Opus 5.5)** — see *Step 2 — what landed*, which names the two places it departs from the wording below.
6. ✅ A `uv` workspace with `fux-core`, `fux-reader`, `fux-writer`, `fux-engine`.
   `fux-engine` depends on the three, owns `cli.py` and both console scripts,
   and `pip install fux-engine` installs what it installs today.
7. ✅ `fux-reader` and `fux-writer` each expose only their verbs (SR-CLI says
   which); a reader-only install asked for `ingest` names the package that has
   it.
8. ✅ `fux doctor` splits: read checks in the reader, write checks in the writer,
   both in `fux-engine` (index-stores §8).
9. ✅ The wheel's Node-bundle payload (`hatch_build.py`) travels with the package
   that owns `fux setup` (the writer) and with `fux-engine`.
10. ✅ **e2e:** each wheel installed alone in a clean venv runs its own verbs on a
    fixture repo; a reader-only venv has no `fux.ingest`, a writer-only one no
    `fux.query`. A reader-only `fux answer --json` is byte-identical to
    `fux-engine`'s on the same query set (F2).

**Step 3 — release.** ✅ **Done 2026-10-18** — Arpit ruled a major, 4.0.0; 4.0.1 was the first release the workflow published to all six names (W-283 carried the registry steps).
11. ✅ SR-WORK-RELEASE: four PyPI distributions and `@fux-engine/reader` on npm,
    one version on all of them, held equal by the version test.

## Step 1 — what landed (2026-10-18, Claude Code)

| | |
|---|---|
| the map | [`records/README.md` §The layer map](../../records/README.md) — 37 rows; one layer per sub-package, root modules one by one |
| the gate | `tests/test_package_layers.py` reads the map from the record; it fails on an unplaced file, a mixed package, a crossing import (package `__init__` counted), and a guarded row that no longer matches. A planted `query → ingest` import fails it |
| new core packages | `text/` — analyzer, identifiers, stem, tokenize, mined, chunk (was `query/`, `refer/_chunk.py`) · `acquire/` — sourcelist, dirlist, typesfile, fuxignore, routes, gitdir, decoderdigest, ingestlog, refusals, urlsrc, urlstate, source, freshness, pii (was `ingest/`, `refer/`, `maintain/`) |
| into `store/` | `dirty.py`, `lastcited.py`, `lock.py` (was `maintain/`) · `corrections.py`, `enrichfile.py` — the read halves of `correct.py` and `enrich.py`, re-imported there |
| root | `inspect_config.py` (was `inspect/config.py`) · `stdio.py` (the UTF-8 helper, was `cli._stdio_utf8`) |
| definitions moved | `Scoring`, `Proximity` → `tune.py` (re-imported by `bm25f`, `rerank`) · `FLOOR_OFF_NOTE` → `query/confidence.py` · `runtime_dir` → `store/cachedir.py` · `fux build` → `derive.cmd_build` · graph reads `[graph]` constants instead of importing `ingest.edges` |
| guarded imports (3) | `fux.open` is lazy (PEP 562) · `ingest.build_runtime` builds the reader's accelerator after ingest, or returns `None` without a reader · `enrich --check` ranks, or refuses naming fux-reader |
| byte-identity | 50/50 `ask` / `find` / `answer` / `lexical` / `graph --json` identical on this repo's index, 10 fixed queries — the final code run against the baseline's documents in a worktree. `register` differs only in the decoder digest of this repo's own `.fux/decoders/` copies, whose docstrings now name the moved paths |
| suites | units 7 164 passed (one red: the Node-twin working-tree check, which reads `git diff HEAD` and clears at commit) · e2e 176 · Node 241 · bundle builds |

**Carried into Step 2 — found by Step 1, not decided by it:**

- **The writer relaunches the engine's CLI.** `maintain/runner.py` and
  `maintain/daemon.py` start `python -m fux.cli`; an import walk cannot see it
  (named in the record). A writer-only install needs its own entry point.
- **Some verbs sit elsewhere than the diagram draws them.** `serve` imports
  `inspect` and `cli`, so it is **engine**, not reader; `doctor`,
  `inspect` and `identifiers` are engine until DoD 8 splits doctor. `build`
  is the reader's, as the research said.
- **Decoders, fetchers and PII are core, not reader.** F2 holds — the reader
  carries them — but `fux ingest` needs them just as much, so they ship in
  `fux-core`, which is therefore larger than "record format, analyzer,
  config". [`architecture-packages.svg`](../architecture-packages.svg) should
  be redrawn from the map.
- **`store/` is core whole**, the shard serializer (`store/writer.py`)
  included, because `store/__init__` re-exports it. Moving it to the writer
  means callers stop importing it from `fux.store`.
- **Writer-only behaviour of the three guarded imports** is what SR-CLI should
  state when it names each package's verbs.
- **This repo's index will re-extract 958 documents** on the next ingest: the
  `.fux/decoders/` copies changed (docstrings only), and a consumer decoder's
  digest is its file sha. Deterministic; the post-commit hook absorbs it.

## Step 2 — what landed (2026-10-18, Claude Code)

| | |
|---|---|
| distributions | `packages/fux-core`, `packages/fux-reader`, `packages/fux-writer` + the root as `fux-engine`, one uv workspace; every wheel's files chosen by `packages/layer_hook.py` from the layer map — no `pyproject.toml` lists a file |
| the CLI | `cli.py` is **core**: it runs each verb through `VERBS` (verb → module → layer); a verb whose layer is absent is left out of `--help` and refused by name. The gate holds every row to the map |
| doctor | split by layer: `health.py` (core rows, the one row order `ROWS`, the run and render), `query/health.py` (reader rows + a reader doctor), `ingest/health.py` (writer rows + a writer doctor, the one that can `--fix`), `doctor.py` (the engine: every row, re-exporting all) |
| release plumbing | seven version-parity sites (the pins between distributions included, with a drift test); CI builds all four; `publish.yml` builds four, uploads to PyPI, and publishes the bundle as `fux-engine` and `@fux-engine/reader` (`scripts/npm-scoped.py`) |
| byte-identity | in a worktree at the Step-1 commit, HEAD's code and the new code on the same documents: 50 query `--json` outputs, `--help` for all 25 verbs, `tune`, `--version` and `doctor` identical — `doctor` up to its `pii timing` row, which reports measured milliseconds |
| e2e | `tests_e2e/test_role_packages.py`: each wheel installed alone, offline, in a clean venv; writer-only ingests and has no `fux.query`; reader-only answers, has no `fux.ingest`, and its `ask`/`find`/`answer --json` equal the engine's (F2); each refuses the other's verbs by name; no file in two wheels |
| suites | units 7 174 · e2e 183 · Node 241 — all green |

**Where it departs from the DoD's wording, and why:**

- **DoD 6 said `fux-engine` owns `cli.py` and both console scripts.** It owns
  neither: `fux` ships in **fux-core** and `fux-merge-index` in
  **fux-writer**. A script file owned by several distributions is deleted when
  any one of them is uninstalled, and core is the one package every install
  has — which is also what lets a reader-only or writer-only machine have a
  `fux` at all. `pip install fux-engine` still yields both scripts.
- **DoD 9 said the Node bundle travels with the writer *and* fux-engine.** It
  is in the writer's wheel only; fux-engine has it through its dependency.
  Two wheels carrying one file is the same uninstall hazard.

**What the Step-1 "Carried into Step 2" list became:** the `-m fux.cli`
relaunches stay inside a writer-only install now that `cli.py` is core;
SR-CLI decision 16 names each package's verbs, writer-only behaviour of the
guarded imports included; the diagram is redrawn; `store/writer.py` stays core
(moving it is not needed for any install to work, and would break
`from fux.store import write_index` for nothing).

## Out of scope

- The `sql` store, generations, sync, `fux publish`, Postgres — B-272.
- A reader in the browser (index-stores F7).
- Any change to ranking, to records, or to the committed index format.

## Key files

`pyproject.toml` (→ the workspace root) and one `pyproject.toml` per
distribution · `hatch_build.py` · `src/fux/__init__.py` · `cli.py` ·
`config.py` · `api.py` · `doctor.py` · `tune.py` · `output_config.py` ·
`query/{tokenize,analyzer,identifiers}.py` · `refer/_chunk.py` · `derive/` ·
`node/package.json` (a second, scoped package) · the release jobs in `.github/workflows/`.

## Records it will update

SR-LAW-2 (F1, his ruling) · SR-CLI (which package owns each verb) · SR-API
(`from fux import open`, where `__version__` lives) · SR-WORK-RELEASE (four
distributions, version equality) · SR-DOCTOR (the doctor split) ·
SR-NODE-SEARCH (the `@fux-engine/reader` package) · `records/README.md` §Ownership (the layer map) ·
`CHANGELOG.md` and the README's install section.

## Hazards

- **Byte-identity across the move.** Moving a module must not move a byte of
  output; DoD 5 is the check.
- **Editable installs.** One import name across several distributions behaves
  differently under `uv sync` / `pip install -e`; test the dev loop, not only
  built wheels.
- **It touches most of `src/fux/`.** Nothing else should be in flight in `src/`
  while Step 1 runs (SR-WORK-SESSION decision 10).

**Model:** **Opus** for Step 1 (the layer map and the moves); **Sonnet** for
Steps 2–3 once the map is fixed and gated.
