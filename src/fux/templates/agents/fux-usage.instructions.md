---
applyTo: "**"
---

# Running Fux

Apply this before running any `fux` command, whenever `fux` is reported as
not found, and whenever a fux command fails and you are about to fall back
to grep or ripgrep.

Fux is a committed BM25F index of this repository's documentation. It ships
**inside the repo**, so if the repo is here the index is here. Your job is to
query it rather than guess about this codebase's history or design.

## 1. Resolve the command FIRST - this is the step that gets skipped

**`fux` is a console script.** It exists only where the installing
environment's `bin/` is on `PATH`. A repo whose fux lives in an unactivated
`.venv/` has a working engine and a committed index, and a bare `fux` still
answers `command not found`.

**Do not read that as fux being absent.** Walk this ladder and stop at the
first rung that answers:

| # | try | when this is the one |
|---|---|---|
| 1 | `fux --version` | a venv is active, or fux is installed globally (pipx, uv tool, system) |
| 2 | `uv run fux --version` | a uv-managed repo - resolves without anyone having activated anything |
| 3 | `./.venv/bin/fux --version` | the venv exists and is NOT active |
| 4 | `python -m fux --version` | the package is importable but no script was installed |

**On Windows, rung 3 is `.venv\Scripts\fux.exe --version`.** Different path, not
a footnote.

Three rules that make the ladder safe rather than clever:

- **Probe with `--version`, and cache the winner for the whole session.** Never
  `which fux` - that answers *is there a file*, not *does it run*, and a stale
  shim from a deleted venv passes it. Never `fux doctor` as the probe either:
  it is the heaviest verb, it can legitimately exit non-zero on a healthy
  install, and it needs a repo root the probe must not presuppose.
- **NEVER activate anything and NEVER install anything.** Do not activate the
  virtualenv, do not modify the `PATH` variable, do not install or reinstall the
  package. Call the absolute path from rung 3 instead. Mutating the user's shell
  so a read-only query can run is a side effect nobody agreed to - and in a
  non-interactive subshell it usually does not even persist to the next command.
- **If every rung fails, say which ones you tried.** The sentence is
  *"fux could not be invoked - tried `fux`, `uv run fux`, `./.venv/bin/fux`,
  `python -m fux`"* - never a claim that the package is absent. Then fall
  back to ordinary search, and **say that you fell back**. A silent fallback is
  indistinguishable from an honest answer, which is the failure this whole
  section exists to prevent.

## 2. Pick the verb

| verb | gives you | reach for it when |
|---|---|---|
| `fux ask "<q>" --json` | ranked results with `score`, `loc`, `archived` | you want candidates and will judge them yourself |
| `fux find "<q>"` | bare paths | you are piping into another command |
| `fux answer "<q>"` | one cited answer, fetched and re-scored on the source's current bytes | you want the answer, with a freshness verdict |
| `fux explain <loc>` | the edges into and out of one document | you are asking what a document depends on |
| `fux graph "<q>"` | the neighbourhood around a query's best answers | you are orienting in an unfamiliar area |
| `fux path <a> <b>` | how two documents connect | you suspect a relationship and want the chain |

**Prefer `--json` everywhere it is offered.** It gives you `score`, `loc` and
`archived` as fields rather than as prose you have to parse. **Branch on the
fields, never on the wording** - the wording is not a contract.

### Line ranges come from `answer`, never from `ask`

**`ask` and `find` return DOCUMENTS. Only `answer` returns a SPAN.**

| verb | `loc` looks like | network |
|---|---|---|
| `fux ask` / `fux find` | `docs/mesh.md` | none - index only |
| `fux answer` | `docs/mesh.md:L10-L13` | fetches each cited source |

**If you need a line range, use `answer`.** Running `ask` and reporting that
fux "does not give line numbers" is wrong, and it is the most common way to be
wrong about this tool.

**This is law L4 showing through the surface, not an omission.** A line range
can only be computed by chunking the *fetched* bytes; the index holds
statistics, not text, so it has nothing to count lines in. Giving `ask` line
numbers would mean making it fetch, and `ask` is offline by default.

### When a search comes back thin, RETRY with the corpus's own words

**Fux ranks the words that are actually in the documents.** The most common
reason a search misses is a **vocabulary gap** - you asked about an *outage*
and the document is titled *"checkout unavailable for 47 minutes"*.

**The signal:** `confidence.band` is `partial` and `confidence.missing` is
non-empty. `missing` names the terms of your question that appear **nowhere in
this corpus**.

**The retry:** re-ask with the word the corpus would use, or keep the question
and add `--expand` - a handful of words you expect the document to use:

```bash
fux ask "what happened during the checkout outage" \
    --expand "checkout unavailable 47 minutes incident timeline"
```

Expansion terms score **below** your own words, and a document matching *only*
your expansion is never returned - so a wrong guess costs nothing.

Repeatable `-q` asks the same question a second way and fuses the rankings;
`--json` then carries `"fused": true` and `score` is a fusion score, not
comparable with a single-question one.

**Fux will never write the expansion for you.** No model runs inside fux.

## 3. Read the freshness verdict on `answer`

`answer` fetches each cited source and compares it against what was indexed:

- **`current`** - the source still matches the index. Cite it plainly.
- **`stale`** - the source changed since ingest. **The quoted passage is from
  the CURRENT bytes**, so the answer is right and the index is behind; say so.
- **`unverified`** - the source could not be reached. Do not present it as
  confirmed.
- **`cached`** - served from a TTL cache. It means *we looked recently*, which
  is not the same as *we looked just now*.

## 4. When there is no index

`fux ingest && fux build` builds one. **Say that you did it**, and never invent
a citation because a query came back empty. An honest *"the index has nothing on
this"* is a useful answer; a fabricated path is not.

## 5. Archived results

Fux indexes retired documents deliberately and marks them rather than hiding
them, because the same document is authoritative for a history question and
dangerous for a build task. If a result carries `"archived": true`, follow the
`fux-archived-results` skill. **When the stance is ambiguous, treat it as
building** - that is the ordering with the worst downside if you guess wrong.

## 6. If you are running as a Kiro custom agent

**Custom agents load neither skills nor steering by default.** If you are one
and you can see this file, someone already wired it. If a teammate reports that
fux guidance never activates, their agent config needs:

```json
{"resources": ["skill://.kiro/skills/*/SKILL.md", "file://.kiro/steering/**/*.md"]}
```

Fux cannot write that config, which is why it is written here instead.
