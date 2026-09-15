---
name: fux-index
description: Bootstrap, diagnose and rebuild a Fux index — `fux setup`, `fux doctor` (every check row, --json, exit codes), `fux ingest`, `fux build`, what to commit from .fux/, and how CI proves the index is current. Use for "set up fux in this repo", "fux doctor says", "rebuild the index", "ingest failed", "what should I commit from .fux", or when a fux verb refuses to run. doctor is read-only; setup writes committed files, only when asked.
---

# Building and diagnosing the Fux index

Fux keeps a **committed index** in `.fux/index/` and a **disposable
accelerator** in `.fux/runtime/`. This skill is the build side: scaffold once,
diagnose with `doctor`, write the index with `ingest`, speed it up with `build`.

Resolve the `fux` command first — see the `fux-usage` skill (`fux` → `uv run fux` → `./.venv/bin/fux`, on Windows `.venv\Scripts\fux.exe` → `python -m fux`).

---

## 1 · Pick the job

| the ask | what to do |
|---|---|
| "set up fux in this repo" | §2 `fux setup`, then list sources (`fux-sources`), then §4 `fux ingest` |
| "fux doctor says …" / a verb refuses | §3 — run `fux doctor --json` and branch on the failing row |
| "rebuild the index" / "the index is stale" | §4 `fux ingest`; `--full` only for the cases in §4 |
| queries are slow, or `graph`/`explain`/`path` refuse | §5 `fux build` |
| "what should I commit from .fux" | §6 |
| "make CI check the index" | §7 |

**Every verb except `setup`, `doctor`, `tune` and `output` stops when
`.fux/pii.toml` is missing.** See §8 and `fux-pii`.

---

## 2 · `fux setup` — scaffold once

**Write-if-missing, always.** Each path prints `wrote <path>` or
`kept <path> (yours; never rewritten)`. A consumer's edit is never overwritten,
so a newer template never reaches a file that already exists.

| writes | what it is |
|---|---|
| `fux.toml` | policy: `[sources]`, `[sources.url]` (`max_parallel` is **required**), `[index]`, `[agents] install` |
| `.fux/sources/dirs` · `.fux/sources/urls` | what is indexed; `dirs` is seeded with `README.md` and `docs` when they exist |
| `.fux/formats.toml` · `.fux/.fuxignore` | which files are documents · what is excluded |
| `.fux/pii.toml` · `.fux/refusals.toml` | redaction rules (required) · what a sign-in wall looks like |
| `.fux/tune.toml` · `.fux/output.toml` | ranking knobs · output defaults — the engine defaults spelled out |
| `.fux/fetchers/*.py` · `.fux/decoders/*.py` | consumer-owned code; **the copies in `.fux/` are what run** |
| `.fux/README.md` · `.fux/.gitignore` | the layout table · ignores `runtime/` and `acquired/` by name |

**It also writes agent files OUTSIDE `.fux/`** — under `.claude/{skills,rules}/`,
`.agents/skills/`, `.github/{agents,instructions}/`, `.kiro/{steering,skills}/`
and a repo-root `AGENTS.md`. Setup prints them under
`note: N of those are OUTSIDE .fux/`. **Relay that list to the user** — some of
them load into every request in the repo (Kiro steering on a Kiro CLI without
inclusion-mode support loads all of `.kiro/steering/`).

| to control agent files | use |
|---|---|
| skip them this once | `fux setup --no-agents` |
| skip them for good | `[agents] install = []` in `fux.toml` |
| only some vendors | `[agents] install = ["claude"]` (known: `claude`, `codex`, `copilot`, `kiro`) |

`AGENTS.md` is written only when all four vendors install, or `codex` does.

⚠ **An existing `AGENTS.md` is kept and setup prints a snippet to paste — on
every re-run, even when fux wrote that file itself.** Check for the
`# Working with fux in this repo` block before pasting; never paste it twice.

A repo still holding `.fux/sources/types` gets it **converted** into
`.fux/formats.toml`; delete the old file afterwards — fux refuses while both exist.

---

## 3 · `fux doctor` — diagnose before touching anything

**Read-only, offline, never repairs.** Each failing row's `detail` names the fix.

```bash
fux doctor --json
```

| field | meaning |
|---|---|
| `ok` | `true` when no **error**-level row failed. Same as exit code `0`; otherwise exit `1` |
| `checks[]` | `{name, ok, level, detail}` — `level` is `"error"` or `"warn"` |
| `runner` | `{running, pid, lock, lock_path, pending, last_run}` — `lock` is `free`, `held` or `stale` |
| `freshness` | verdict counts from journalled answers; `{}` means unknown, not zero |

**Branch on `ok`, then on `name`/`ok`/`level`. Never parse `detail`.**
**A warning is not a failure:** `ok:false, level:"warn"` leaves exit 0. Text
mode prints `[OK]`, `[WARN]` or `[FAIL]` per row.

| row | fails as | what it means |
|---|---|---|
| `python version` · `repo root` · `.fux/ writable` | error | wrong interpreter · no `fux.toml`/`.git` above cwd · `.fux/` not writable |
| `fux.toml loads` | error (warn if absent) | the loader's own message, verbatim — fix the key it names |
| `index not gitignored` | error | an ignore rule (usually `.fux/*`) drops `.fux/index` out of git |
| `types list usable` | error | `.fux/formats.toml` will not load, admits nothing, or old `sources/types` remains |
| `fuxignore usable` | error on parse · warn on duplicates | a pattern in both `.fuxignore` and `sources/dirs` |
| `pii rules` | error when missing/invalid · warn when empty | ingest refuses without the file |
| `refusal rules` · `decoder bindings` | error when the file/binding will not load · else warn | a hand-written binding matching no indexed document is a warn |
| `acquired plane` | **error if not gitignored** · warn near cap | fetched source bytes visible to git |
| `.fux/ layout declared` · `output.toml present` | warn | undeclared entry under `.fux/` · no output defaults file |
| `accelerator` | warn | not built, stale, or tracked by git — §5 |
| `background runner` · `url daemon` | warn | stale lock, failed last run, pending paths — see `fux-maintain` |
| `url sources` · `fetcher optional functions` · `freshness verdicts` | warn | URL health and fetcher capability — see `fux-sources` |
| `recency prior` · `ranking priors` | warn | a disclosure; **do not "fix" it by choosing values** — see `fux-config` |

---

## 4 · `fux ingest` — write the committed index

**Offline. Walks `.fux/sources/dirs`, carries URL records forward, rewrites
`.fux/index/*.jsonl`, then builds the accelerator.** No `--json`: judge it by
exit code (`0` ok, `1` error, `130` interrupted), then `fux doctor --json`.

| flag | effect |
|---|---|
| *(none)* | delta run: unchanged documents are carried forward by content sha — same bytes as a full run |
| `--full` | re-extract everything: after a fux upgrade, for the complete term-collision check, or to migrate an index written by another fux version |
| `--no-accelerator` | skip the derived build; results are unaffected |
| `--list-skipped` | print every skipped path as `path: reason`, then exit; writes nothing |
| `--stop` | stop a background re-index and do not run (exit 0 if none was running; clears a stale lock) |
| `--no-progress` · `--progress` | never / always paint the stderr progress bar |

**One writer at a time.** Ingest holds `.fux/runtime/write.lock`. If a
background re-index holds it, ingest asks it to stop, waits, then runs.
Editing `.fux/pii.toml` or `[index]` in `tune.toml` invalidates carry-forward automatically.

The summary line is
`ingested N docs (C changed, R carried forward), X not indexed, Y skipped, S shards written`.

- **`not indexed`** — a committed list excluded it. **`skipped`** — fux opened
  it and could not read it (empty, undecodable); worth a look.
- **Each skip prints once**, then is recorded in `.fux/.fuxignore` between
  `# >>> fux: not indexed >>>` / `# >>> fux: skipped >>>` markers.
  ⚠ **A recorded path stays ignored** after the file is fixed — delete its line.
- A document no decoder can read (an image, a scanned PDF) is queued in
  `.fux/enrich/queue.tsv` for `fux-enrich`.

---

## 5 · `fux build` — the derived accelerator

**Rebuilds `.fux/runtime/` from the committed shards only** — no source walk,
no network. `ingest` already does this unless given `--no-accelerator`.

- **`ask` and `find` return identical results with or without it**; `ask`
  scans by default and `--fast` opts into the accelerator.
- ⚠ **`explain`, `graph` and `path` refuse without it:**
  `the graph lane needs the derived plane - run fux build first`.
- Run it after a fresh clone or a background re-index, or when doctor says
  `stale`. It takes the write lock but **never takes over**: another writer → exit 1.

---

## 6 · What to commit from `.fux/`

| commit | never commit |
|---|---|
| `fux.toml`, `.fux/index/*.jsonl` | `.fux/runtime/` — derived, rebuildable |
| `.fux/sources/`, `.fux/formats.toml`, `.fux/.fuxignore` | `.fux/acquired/` — **fetched source bytes**, not rebuildable |
| `.fux/pii.toml`, `.fux/refusals.toml`, `.fux/tune.toml`, `.fux/output.toml` | `__pycache__/` under `.fux/decoders/` or `.fux/fetchers/` — **`.fux/.gitignore` does not list these** |
| `.fux/fetchers/*.py`, `.fux/decoders/*.py`, `.fux/enrich/` | |
| `.fux/README.md`, `.fux/.gitignore`, and the agent files if the team wants them | |

⚠ **Never ignore `.fux/` or `.fux/*` wholesale.** The index silently leaves git;
doctor's `index not gitignored` row exists for exactly this.
**Ingest rewrites `.fux/.fuxignore`**, so commit it with the index.

---

## 7 · Byte-identical everywhere — and checking it in CI

**Same sources plus the same git history give byte-identical shards** —
sorted, canonical JSON, no clock. Two consequences:

1. **Record `mtime` comes from git commit times.** A shallow clone rewrites
   every record, so CI needs full history.
2. **An index ingested before the content commit is one commit behind.** Commit
   the documents, *then* ingest and commit `.fux/` — the order the hooks in
   `fux-maintain` produce.

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0            # full history: mtimes come from git
# install the fux-engine package the way this repo installs its other tools
- run: fux doctor             # exit 1 = some verb will refuse this repo
- run: fux ingest --no-accelerator --no-progress
- run: test -z "$(git status --porcelain -- .fux/index .fux/.fuxignore .fux/enrich)"
```

`git status --porcelain`, not `git diff`: a new document can add an untracked
shard. ⚠ **`fux ingest --check` is not this gate** — its exit code is always 0.
`fux ingest --check --json` gives you `drifted`, which you can gate on; it is
still blind to files that were never indexed, which is what this gate catches.

---

## 8 · Common failures

| message contains | fix |
|---|---|
| `.fux/pii.toml is missing, and fux will not run without it` | **tell the human.** `fux setup` writes the starter but also every other missing committed file and the agent files — run it only when asked, then relay its `wrote` lines. See `fux-pii` |
| `.fux/sources/types … moved to .fux/formats.toml` | `fux setup` converts it; then delete `.fux/sources/types` |
| `lists no file types` (ingest) · `admits nothing` (doctor) | delete `.fux/formats.toml` to take the built-in default |
| `another fux process is writing this index (lock: …)` | wait. If none is running, `fux ingest --stop` clears the stale lock |
| `did not stop when asked` | a live writer is mid-run; wait, then re-run |
| `….jsonl:1: not valid JSON` | merge conflict markers in a shard — `fux-maintain` §6 |
| `declares _format …` or `written by analyzer …` | `fux ingest --full`. ⚠ Do not delete `.fux/index/` in a repo with URL sources — those records cannot be rebuilt offline |
| a file is missing from results | `fux ingest --list-skipped`, then check `.fux/.fuxignore` |
| `no fux.toml or .git found` | run from inside the repository |

---

## Don't

- **Don't hand-edit `.fux/index/*.jsonl`.** Change the source and re-ingest.
- **Don't run `fux setup` unasked**, and don't paste its `AGENTS.md` snippet twice.
- **Don't read a `[WARN]` as a failure.** Exit code and `ok` decide.
- **Don't commit `.fux/runtime/` or `.fux/acquired/`**, or ignore `.fux/` wholesale.
- **Don't delete `write.lock` while a fux process is running** — two writers corrupt the index.
- **Don't delete `.fux/index/` to clear an error** when URL sources exist.
- **Don't gate CI on `fux ingest --check`'s exit code** (gate on `--json`'s
  `drifted`), or ingest in a shallow clone.

Related skills: fux-usage, fux-search, fux-answer, fux-graph, fux-sources, fux-maintain, fux-config, fux-mcp, fux-fetcher, fux-pii, fux-decoder, fux-enrich, fux-archived-results.
