# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This is the v0.30 rebuild's changelog — a fresh start. The v0.26 engine's
history is archived at [`archive/v0.26/CHANGELOG.md`](archive/v0.26/CHANGELOG.md).

## [Unreleased]

## [2.0.0-alpha.1] - 2026-08-24

**ADR-TUNE is built.** The knobs that decide what you read first have a home.

### Added

- **`.fux/tune.toml` — the tunables file.** Committed, written once by
  `fux setup`, and **never rewritten by fux**. Absent, empty, or every key
  commented out means every default, so `$0` stays `$0`. Seven tables:
  `[bm25f]` (`k1`, `b`, five field weights), `[ranking]`, `[dense]`,
  `[fuse]`, `[graph]`, `[refer]`, and `[priority]`.
  [ADR-TUNE](docs/adr/0038_tuning.md).
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
  `explain --no-tune` is inert. Both are stated in ADR-TUNE rather than left
  to be discovered.


## [2.0.0-alpha.0] - 2026-08-24

**A pre-release.** The record shape and analyzer changed, so this ships
ahead of a stable `2.0.0` to give the migration a soak before it is called
final — every new ADR here (`ADR-TUNE`, `ADR-MCP`, `ADR-ENRICH`, `ADR-RERANK`)
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
  [ADR-INDEX-LIFECYCLE](docs/adr/0009_index-lifecycle.md),
  [ADR-RECORD](docs/adr/0010_index-record.md).
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
  in `1.0.0`. [ADR-INDEX-LIFECYCLE](docs/adr/0009_index-lifecycle.md)
  decision 10.
- **`fux enrich --plan` printed a sha that could not be used.** It showed the
  first 12 characters while validation compared the whole value, so enrichment
  written by correctly following the documented procedure came back `STALE` —
  under a message rendering two identical-looking shas. Both the command and
  the skill's own worked example are corrected.
  [ADR-ENRICH](docs/adr/0040_enrich.md) decision 11.

### Added

- **`.fux/tune.toml`** — a committed, write-if-missing ranking file for
  BM25F field weights, fuse/graph/refer constants and per-source query-time
  priority (longest-directory-match, multiplicative, both directions
  allowed — fux states the cost rather than picking a side).
  [ADR-TUNE](docs/adr/0038_tuning.md).
- **`fux enrich`** — a separate, opt-in command that writes model-assisted
  enrichment into `.fux/enrich/` for a named scope; never runs inside
  `fux ingest`, so the maintenance path stays model-free (L3).
  [ADR-ENRICH](docs/adr/0040_enrich.md).
- **`fux mcp`** — serves the index to coding agents over stdio JSON-RPC,
  stdlib-only, as three tools rather than the full CLI surface (no
  `answer` — the agent is the answerer). [ADR-MCP](docs/adr/0039_mcp.md).
- **Proximity reranking**, in stdlib arithmetic — a specified cross-encoder
  pass was refused because `onnxruntime` is not byte-identical across
  x86-64/arm64. Measured on 50 new playground goldens: 28 -> 32 (4 fixed,
  0 broken), +8ms p95 against a 150ms bar at 10 000 documents, 240
  differential comparisons green. [ADR-RERANK](docs/adr/0041_rerank.md).
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

- Every ADR gains a `References` bibliography, generated from the citations
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
  an archived-content-signalling paragraph. `docs/adr/TEMPLATE.md` gains an
  optional worked-output block per §2 section, retrofitted to
  ADR-ARCHIVED-CONTENT, ADR-REFER and ADR-GRAPH where real output existed.
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
  [ADR-ARCHIVED-CONTENT](docs/adr/0037_archived-content.md) decisions 1, 3 and 7.

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
  [ADR-REFER](docs/adr/0030_refer-plane.md) veto condition 2.

## [0.36.0] - 2026-08-22

**Committing stops waiting for a re-index, and fux now ships the policy its
readers need to read it correctly.**

The headline is a latency change you will feel on every commit in a large
repository, and a scaffolding change you should read before upgrading: `fux
setup` writes outside `.fux/` for the first time, into directories GitHub, AWS
and Anthropic own. It announces every one of them and both ways to turn them
off.

[ADR-MAINTENANCE](docs/adr/0032_hooks.md) 1a–1d ·
[ADR-AGENT-POLICY](docs/adr/0035_agent-policy.md) ·
[ADR-DIR-LIST](docs/adr/0022_dir-list.md) 11. Measured evidence:
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
  fux will never rewrite it. [ADR-AGENT-POLICY](docs/adr/0035_agent-policy.md).

- **`post-commit` no longer waits for a re-index.** It records what changed and
  spawns a **detached one-shot** background run, so committing costs what git
  costs regardless of corpus size. The re-index still happens; nobody watches
  it. [ADR-MAINTENANCE](docs/adr/0032_hooks.md) 1a–1d (W-66).
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
  weight is configured. [ADR-DIR-LIST](docs/adr/0022_dir-list.md) decision 11
  (W-44). The marker and the response-level disclaimer (decisions 5/7/12)
  stay gated on a pre-registered query set.
- **`fux ask` says when the index is behind.** Since the hook defers, the
  committed index can lag by more than one commit, so `ask` states how many
  documents are pending — on **stderr**, so `--json` and every pipe produce
  exactly the bytes they did before. It is a declaration, never a gate: `ask`
  does not refuse to answer and does not re-index on your latency.
  [ADR-MAINTENANCE](docs/adr/0032_hooks.md) decision 1b (W-66).
- **A dirty list** (`.fux/runtime/dirty`, gitignored) records which documents
  each commit touched. **It is advisory only** — `fux ingest` produces the same
  index whether the list is right, stale, empty or missing, which is asserted
  rather than reasoned about. It exists so the background run can report what
  is pending, and so a future incremental re-index has something to consume.

## [0.35.0] - 2026-08-21

The corpus becomes a first-class verb, and two defects that made removing a
document harder than adding one are fixed.
[ADR-CLI](docs/adr/0002_cli-surface.md) 1a–1e ·
[ADR-INGEST](docs/adr/0007_ingest.md) 9–10 ·
[ADR-DIR-LIST](docs/adr/0022_dir-list.md) 2d–2e, 3a. Surface captured
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
  law (ADR-ASK) makes this a pure speed choice: results are byte-identical
  either way. See [ADR-CLI](docs/adr/0002_cli-surface.md) and
  [ADR-ASK](docs/adr/0004_ask.md).

## [0.34.0] - 2026-08-21

**Four milestones in one release — the graph lane, the refer plane, the
maintenance plane, and delta ingest — plus the prediction series that
measures three of them against pre-registered thresholds.**

M3 makes the edges ingest already extracts answerable: `explain`, `graph`,
`path`, and deterministic seedless community detection. M4 builds the refer
plane — fetch a citation from the system that owns it, verify it still says
what the index thinks, re-score on the fetched bytes — and P6 wires it into
`answer` by default, making it load-bearing for the first time
([ADR-REFER](docs/adr/0030_refer-plane.md) accepted,
[R4 PASS](work/regression/2026-08-20-refer-plane-r4/VERDICT.md)). M5 adds
`fux hooks` and a merge driver for the committed index, but
[R5 FAIL](work/regression/2026-08-20-r5-hook-latency/VERDICT.md) (44.4 s at
100 000 documents against a 1 s bound) and
[R6 INCONCLUSIVE](work/regression/2026-08-20-r6-merge-driver/VERDICT.md) mean
[ADR-MAINTENANCE](docs/adr/0032_hooks.md) stays **proposed, not accepted** —
the hook ships, its accept gate has not cleared. Delta ingest reuses
extraction for byte-unchanged documents (22.7×–26.4× measured, byte-identical
to a full run). Only prose files are indexed by default now — a 14 % non-prose
slice this repo carried silently is excluded
([ADR-TYPES](docs/adr/0031_types-list.md)) — and L5's hashed-meta rule moved
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

- **Delta ingest — unchanged documents keep their extraction** (ADR-INGEST
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
  are recorded in ADR-INGEST rather than left to be discovered.
- The ingest summary now reports what was carried forward:
  `ingested 3 docs (1 changed, 2 carried forward), 2 skipped, 1 shards written`.

- **A TTL-bounded local fetch cache for the refer plane** (W-60,
  [ADR-REFER](docs/adr/0030_refer-plane.md) 5a-5c). `cache_ttl_seconds`
  (**default 0 — off**) and `no_cache` on the freshness policy; entries live in
  the gitignored `.fux/runtime/fetch-cache/`. Motivated by rate limits rather
  than latency: an agent asking ten questions about one runbook must not fetch
  it ten times, because at enterprise scale that is throttling, not slowness.
- **A fourth freshness verdict, `cached`**, carrying `age_seconds`. It is
  **never folded into `current`** — "we looked recently" is a different claim
  from "we just looked", and it still records whether the cached bytes matched
  the index.

- **`fux hooks` — the maintenance plane** (M5,
  [ADR-MAINTENANCE](docs/adr/0032_hooks.md), **proposed, not accepted**).
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
  P6, 2026-08-21, ADR-REFER **accepted** — R4 passed, and the plane is now
  load-bearing in a shipped verb; ADR-ANSWER **accepted**). A citation whose
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

- **Only prose files are indexed now** ([ADR-TYPES](docs/adr/0031_types-list.md),
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
  ([ADR-DIR-LIST](docs/adr/0022_dir-list.md), W-45 verdict E).
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
  [ADR-REFER](docs/adr/0030_refer-plane.md), **proposed, not accepted**).
  Fetches a cited document from the system that owns it, verifies it still says
  what the index thinks, cuts it into heading-delimited passages, re-scores
  those against the query, and assembles as much as fits a **byte** budget.
  **No verb exposes it yet** — its gate has not run, and wiring an unmeasured
  plane into the default surface is how it becomes load-bearing before anyone
  knows whether it works.
- **Fux still does not fetch.** The plane reuses the consumer-owned fetcher
  contract ([ADR-FETCHER](docs/adr/0019_fetcher.md)) rather than adding a
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
  [ADR-GRAPH](docs/adr/0029_graph.md)). The `ref`/`tag`/`code` edges
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
  ([ADR-CLI](docs/adr/0002_cli-surface.md)).

### Changed

- **`ask --json --explain` now carries `"path"`** — `"accelerator"`, `"scan"`
  or `"hybrid"`. `--explain` was text-only, so the one fact worth logging about
  a slow query was the one a caller could not read. The key appears only when
  `--explain` is passed, so the default payload is unchanged
  ([ADR-ASK](docs/adr/0004_ask.md)).
- **`answer --json` now carries `"source"` on the no-match branch too.**
  [ADR-ANSWER](docs/adr/0006_answer.md) tells callers to key on `"source"` to
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
  ([ADR-DOTFUX](docs/adr/0003_fux-directory.md) decision 6). Optional, explicit,
  once per repo, and a second run is a no-op that never clobbers an edit. It is
  the only verb that may run before a repo root exists — it is what creates one.
- **Two fetchers ship in the wheel**, `http.py` and `cdp.py`
  ([ADR-HTTP-FETCHER](docs/adr/0021_http-fetcher.md),
  [ADR-CDP-FETCHER](docs/adr/0020_cdp-fetcher.md)). They travel as **package
  data with an extension Python cannot import**, so fux copies them and never
  imports them — the adapter cap is structural, not remembered. `http.py` is a
  plain stdlib GET and is what a URL with no `fetch=` attribute gets; it never
  escalates to the browser on its own.
- **`fux url`** — records a URL in the committed list, writing **every**
  attribute explicitly ([ADR-URL-LIST](docs/adr/0018_url-list.md) decisions 12
  and 13). Flags, not a subcommand tree: `--cdp`/`--http`, `--plain`/`--hashed`,
  `--remove`; no argument lists what the loader sees. **It never fetches** —
  `fux ingest --refresh-urls` remains the only networked path in the engine.
- **Per-URL attributes in `.fux/sources/urls`** — `fetch=http|cdp` routes to a
  file under `.fux/fetchers/`, `meta=plain|hashed` decides whether the index may
  hold readable display text for that one document. A line beats the source-wide
  `[sources.url]` setting, which beats the built-in default. `meta` only ever
  *loosens* per line: there is deliberately no way to make one URL stricter.
- **`.fux/sources/dirs`** — the committed directory list, on the same grammar
  ([ADR-DIR-LIST](docs/adr/0022_dir-list.md)). A line may declare
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
  ([ADR-FETCHER](docs/adr/0019_fetcher.md)). Middleware names a pattern whose
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
- **ADR-DOTFUX, ADR-URL-INGEST and ADR-CONFIG are ratified** (Arpit,
  2026-08-19), closing W-31. Their `⏳ proposed` qualifiers in the `0.32.0`
  entry below are stale as of that date; the register
  ([`docs/adr/README.md`](docs/adr/README.md)) is the live statement of every
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
  bump ([ADR-INDEX-LIFECYCLE](docs/adr/0009_index-lifecycle.md) decision 9), and
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

- **The derived T1 accelerator — M2** ([ADR-T1-ACCELERATOR](archive/adr/0005_derived-accelerator.md),
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
  ([ADR-DOTFUX](archive/adr/0011_fux-dir-layout.md), ⏳ proposed): every child is
  committed (`index/`, `sources/`, `fetchers/`) or derived (`runtime/`,
  `cache/`). Ingest writes a self-describing `.fux/README.md` and a narrow
  `.fux/.gitignore` — derived names only, **never `*`** — both
  write-if-missing so consumer edits survive. `derived_dir()` drops a
  spec-exact `CACHEDIR.TAG` for M2/M4 to use. `fux doctor` gains two checks:
  the committed index must not be git-ignored (error), and undeclared
  top-level `.fux/` entries are reported (warning).
- **URL source via consumer-owned fetcher**
  ([ADR-URL-INGEST](archive/adr/0010_url-source-consumer-middleware.md), ⏳ proposed):
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
  hours-old surface, so no shims exist ([ADR-DOTFUX](archive/adr/0011_fux-dir-layout.md)).
- Fetcher tunables now live in an optional **`[sources.url.config]`** table
  passed verbatim to `configure(config)`. Fux validates only that it is a
  table and never reads a key inside it — the PEP 518 `[tool.*]` discipline,
  which keeps one fetcher's vocabulary out of fux's config schema.
- The repo's own `.gitignore` no longer blanket-ignores `.fux/*`; the narrow
  `.fux/.gitignore` carries the derived names instead.

## [0.30.0] - 2026-08-11

M0 scaffold + M1 T0 slice — the first real code of the v0.30 rebuild.
[ADR-RECORD](archive/adr/0004_index-format.md); R1 PASS, R2 2/3 PASS.

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
