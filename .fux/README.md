# `.fux/`

Fux's directory in your repo. Every child is declared below, in one
of THREE kinds:

- **committed** - belongs in git. This is the product.
- **derived** - rebuildable from the committed bytes by `fux build`.
  Ignored, tagged with [`CACHEDIR.TAG`](https://bford.info/cachedir/),
  and safe to delete at any time.
- **acquired** - the bytes a fetch returned. Ignored and tagged like
  derived, but NOT rebuildable: deleting it loses the only local copy,
  and getting it back means re-fetching from a source that must still
  exist and a session that must still hold.

| entry | kind | what it is |
|---|---|---|
| `README.md` | committed | this file: written once by fux, yours to annotate |
| `.gitignore` | committed | lists the ignored directories BY NAME, never `*` |
| `index/` | committed | the wire-format index (ADR-RECORD) |
| `sources/` | committed | the committed source lists (`dirs`, `urls`), one entry per line |
| `fetchers/` | committed | consumer-owned code (`cdp.py`, `http.py`), edit freely |
| `decoders/` | committed | consumer-owned code, one module per format. THESE COPIES ARE WHAT RUN, not the ones inside the installed package (ADR-DECODE) |
| `enrich/` | committed | pinned enrichment text, one file per source content sha, plus `queue.tsv` (W-86 P6: what fux could NOT read and a model must). Committed, because a backlog is a team fact |
| `node/` | committed | the vendored Node read plane (`fux-engine`), engine-owned and REWRITTEN on a version change -- not write-if-missing, because nobody edits it and a stale copy is a wrong answer (ADR-NODE-SEARCH) |
| `tune.toml` | committed | the tunables: HOW results are ordered, never what is indexed (ADR-TUNE) |
| `output.toml` | committed | the output defaults: HOW a result is SHOWN, never which documents come back (ADR-OUTPUT) |
| `formats.toml` | committed | which files are documents (`include`) and which decoder reads each extension (`[decoders]`). Optional - absent means the built-in default. Replaced .fux/sources/types on 2026-09-11 (ADR-TYPES) |
| `.fuxignore` | committed | what is NOT indexed, in .gitignore's grammar. The one place exclusions belong, read before the source lists (ADR-FUXIGNORE) |
| `pii.toml` | committed | REQUIRED - every command refuses without it. What is REDACTED from the committed index - and ONLY from it. The acquired bytes, the refer plane and every answer quote still see the document as it is (ADR-PII) |
| `refusals.toml` | committed | what a REFUSAL looks like here - the sign-in walls, paywalls and error shells a server returns INSTEAD of the document. Consumer-owned; fux ships no vendor knowledge (ADR-REFUSAL) |
| `fux` | committed | a 3-line shim: `.fux/fux find rollback` in a clone with nothing installed. Runs `node .fux/node/fux.mjs` (ADR-NODE-SEARCH) |
| `runtime/` | derived | M2 accelerator segments, M4's fetch cache at `runtime/fetch-cache/`, the write lock, and `enrich-progress.tsv` (W-86 P6: which queued documents THIS machine has handled - local by design, so two people's progress cannot conflict on a pull); carries `CACHEDIR.TAG` |
| `acquired/` | acquired | the bytes a fetch actually returned, for URLs whose line says keep=true. Gitignored and NOT rebuildable - re-acquirable only, and only while the source is still reachable; carries CACHEDIR.TAG |

## The fetchers are yours

`fetchers/http.py` and `fetchers/cdp.py` are **your** code, committed
to **your** repo. `fux setup` writes them once if they are missing;
`fux ingest` never writes a fetcher at all. Fux loads one by path
under `fux add <URL>` or `fux update`, and never rewrites it. Change the
port, the transport, the extraction, anything.

One consequence of living in a dotdir: linters that skip hidden
directories by default (ruff does) will not lint it. That is fine, it
is consumer code, not a CI target.

## Rules

- Anything here that is not in the table above is undeclared; `fux
  doctor` warns about it.
- Derived directories can be deleted at any time. Committed ones
  cannot be rebuilt from anything but their source systems.
- `acquired/` sits between the two: deleting it costs you the local
  copy of bytes you already fetched, and a re-fetch is the only way
  back. `fux doctor` reports its size.
- Fux writes `README.md` and `.gitignore` **only if missing**. Your
  edits survive every ingest.

---

# What fux is

A search index for your written knowledge - decisions, runbooks,
specs, wiki pages - committed to git and read by agents.

- **The index is committed; the content is not.** `index/` holds
  statistics about your documents, never the documents. That is why
  it diffs like code and why no second copy of anything exists.
- **Ranking is arithmetic.** BM25F, one scorer, one sort. The same
  sources build the same index, byte for byte, on any machine.
- **No server, no vector database, no API key, and no model anywhere
  on the path.** `fux ask` is a local process reading local files.
- **It does not read your code.** No parser runs over source files,
  and no source extension is on the default type list. Fux is about
  what you wrote down, not what you compiled.
- **Answers are re-read before they are quoted.** `fux answer` fetches
  the cited lines from the source and tells you whether they still
  say what the index thinks they say.

# The commands

Flat verbs, no subcommand tree. `fux <verb> --help` for any of them.

| group | verbs | what the group does |
|---|---|---|
| lifecycle | `setup` `doctor` | set the repo up, then check it |
| write | `ingest` `build` | `ingest` writes the committed index; `build` derives the local accelerator from it |
| sources | `add` `remove` `update` `enrich` | maintain what is indexed. `add`/`remove` write lines; `update` re-fetches and writes none; `enrich` writes no committed byte at all |
| read | `ask` `find` `answer` | the same question, differing only in how much each commits to |
| graph | `explain` `graph` `path` | answer with relationships the documents stated, never with a ranking |
| serve | `mcp` `daemon` | the only verbs that do not return |
| maintenance | `hooks` `tune` `output` `verify` | wire git to keep the index in step; print or set the tunables; re-run a receipt |

**The three read verbs differ in how much they commit to.** `find`
gives locations and stays out of the way. `ask` gives a ranked list
with scores, which is what you want when judging the engine. `answer`
commits to one passage with a line range and a freshness verdict,
which is what an agent wants when it needs a value and not a menu.

```console
$ fux setup                 # write the consumer-owned files here
$ fux add docs/             # index a directory
$ fux add https://wiki/...  # index a URL through a fetcher you own
$ fux ingest                # walk the sources into the committed index
$ fux doctor                # is this repo healthy, and why not

$ fux find rollback                       # one line per hit, for pipes
$ fux ask 'how do we roll back a release' # ranked, with scores
$ fux answer 'what is the RTO' --band     # one passage, cited and checked
```

# Calling fux from a script, in any language

**There is no SDK, and that is the design.** Fux is a normal
command-line program: it reads files, writes to stdout, and exits with
a status. Anything that can start a process can drive it, which is why
there is no binding to install, version, or wait for.

**Three things are the whole contract:**

1. **`--json` on every read verb.** `ask`, `find`, `answer`, `explain`,
   `graph`, `path`, `doctor`, `update`. Never parse the prose output -
   it is for humans and it is allowed to change.
2. **Exit codes.** `0` ok - `1` error - `2` blocking (strict mode) -
   `130` interrupted. Errors go to stderr as `error: <message>`.
3. **It is offline and deterministic.** No network on a read path, so a
   call is fast enough to make inline and safe to make in a loop.

**The JSON shape you will actually use:**

```json
{ "results": [ { "id": "docs/runbook.md",
                 "title": "Release runbook",
                 "score": 12.41,
                 "headings": ["Rollback"] } ],
  "confidence": { "band": "high", "answerable": true, "missing": [] } }
```

`confidence` is present only when you pass `--band`. **Absent means
not asked for; it is never a claim about the answer.**

## Shell

```bash
fux ask 'retention policy' --json | jq -r '.results[0].id'

# exit code first, output second
if ! fux doctor --json > health.json; then
  echo "index unhealthy" >&2; exit 1
fi
```

## Python

```python
import json, subprocess

def ask(question, top=5):
    p = subprocess.run(
        ["fux", "ask", question, "--json", "--top", str(top), "--band"],
        capture_output=True, text=True,
    )
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip())
    return json.loads(p.stdout)

hits = ask("how do we roll back a release")
if hits.get("confidence", {}).get("answerable"):
    print(hits["results"][0]["id"])
```

Import `fux` as a library only if you accept that the Python API is
not a supported surface. **The CLI is the contract; the modules are
not.**

## Node / TypeScript

```js
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const run = promisify(execFile);

export async function ask(question, top = 5) {
  const { stdout } = await run('fux',
    ['ask', question, '--json', '--top', String(top), '--band']);
  return JSON.parse(stdout);
}
```

A non-zero exit rejects the promise and carries `stderr`, so the error
path needs no special handling.

## Go, Ruby, Rust, anything else

Same three steps every time, because there is nothing language-
specific to learn:

1. Spawn `fux` with the verb, the query, and `--json`.
2. Check the exit status; read `stderr` when it is non-zero.
3. Parse `stdout` as JSON.

```go
out, err := exec.Command("fux", "ask", q, "--json").Output()
// err is *exec.ExitError on a non-zero status; out is the payload
```

## For an AI agent

Two ways in, and they differ in who owns the loop:

- **`fux mcp`** - serves the index over the Model Context Protocol
  (`fux_search`, `fux_passage`, `fux_related`). The client calls the
  tools; you configure the server once and write no glue.
- **A skill or instruction file** - `fux setup` installs guides for
  Claude Code, Codex, Copilot and Kiro that tell the agent to query
  the index rather than grep. The agent shells out to the CLI.

Use MCP when the client speaks it. Use the CLI everywhere else; it is
the same engine either way.

## One rule for every caller

**`fux answer` re-reads the source before it quotes.** Its verdict
field says `current`, `stale`, `as-ingested`, `cached` or `unverified`
- and a script that ignores that field has thrown away the only thing
separating fux from a stale cache with good manners.
