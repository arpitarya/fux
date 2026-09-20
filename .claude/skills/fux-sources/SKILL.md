---
name: fux-sources
description: Manage what is in a Fux corpus with `fux add`, `fux remove` and `fux ingest` — the ONE verb for the first ingest and every re-ingest, since `fux update` was deleted in 3.0. Directories, files, file types and URLs, archived=, keep, ttl, update=, and why a file is not indexed. Use ONLY when explicitly asked to change the corpus ("index this folder", "add this URL", "stop indexing X", "refresh the URLs"), or to answer "why isn't file X indexed". Edits committed files in .fux/.
---

# Managing a Fux corpus

What Fux indexes is decided by **committed lists in `.fux/`**, not by a scan of
the repo. `fux add`, `fux remove` and `fux ingest` are the editors for those
lists, and each one ends in an ingest.

> ⚠ **These verbs change committed files and the committed index.** Run one only
> when a human asked for that change. Diagnosing (§6) and listing (`fux add`
> with no entry) are read-only and always safe.

Resolve the `fux` command first — see the `fux-usage` skill (`fux` → `uv run fux` → `./.venv/bin/fux`, on Windows `.venv\Scripts\fux.exe` → `python -m fux`).

## 1 · Pick the job

| the ask | what to do |
|---|---|
| "what is indexed?" | `fux add` with no entry — prints every list as the loader sees it |
| "index this folder / this file" | `fux add docs/runbooks` · `fux add docs/onboarding.md` |
| "re-index / bring the index up to date" | `fux ingest` — the same verb as the first time, for dirs and URLs alike |
| "add this page / Confluence URL" | `fux add https://…` — fetches **that URL only**, then ingests |
| "index our `.srt` files" | `fux add '*.srt' --types` — a format with no decoder also needs the `fux-decoder` skill |
| "stop indexing X" | `fux remove X --dry-run`, read the branch, then `fux remove X` |
| "mark these docs archived" | `fux add old/2023-platform --archived` (a URL line takes `--archived` too) |
| "refresh the URLs" | `fux ingest` — add `--refetch-all` to fetch every URL |
| "why isn't X indexed?" | §6. Change nothing until you know the reason |
| the page comes back as a login page | the `fux-fetcher` skill — that is a fetcher problem, not a list problem |

**`add` and `remove` write lines; `ingest` never writes one.** Changing an
attribute is another `fux add` on the same entry — it is an upsert.

> 🔴 **`fux update` no longer exists** (3.0). Every form of it is `fux ingest`,
> and `--all` is now `--refetch-all` — beside `--full` the old name read as its
> synonym, and the two are unrelated. A bare `fux ingest` **goes to the
> network** for the URLs known to be stale; `fux ingest --no-fetch` is the
> offline form, and it is what the git hooks run.

## 2 · The files, and their line syntax

| file | holds | one line looks like |
|---|---|---|
| `.fux/sources/dirs` | directories and single files, repo-relative | `docs/runbooks archived=false enrich=false` · `!docs/drafts` |
| `.fux/sources/urls` | `http(s)` URLs | `https://wiki.corp/x fetch=http keep=true ttl=24h enrich=false archived=false update=auto` |
| `.fux/formats.toml` | which file types are documents | `include = ["*.md", …]` and `[decoders]` `csv = "csv"` |
| `.fux/.fuxignore` | what is kept out | `.gitignore` grammar; `!` **re-includes** |

`fux.toml` can relocate the first two (`[sources] dirs_file`,
`[sources.url] urls_file`); the other two are fixed paths.

**Grammar of `dirs` and `urls`, exactly:**

- One entry per line, then `key=value` attributes. No quoting, no bare flags.
- `#` starts a comment **only at line start or after whitespace** — a URL
  `#fragment` is part of the URL.
- An unknown key, an illegal value, or a key given twice is an error naming
  `file:line`. Two lines for one entry with **different** attributes is an error.
- File order is irrelevant: the loader dedupes and sorts.
- `dirs` attributes: `archived`, `enrich` (`true`/`false`, default `false`).
- `urls` attributes: `fetch` (**any fetcher name** — see below)
  (`hashed`|`plain`), `keep`, `enrich`, `archived` (`true`/`false`), `ttl`
  (`0` or `<int>s|m|h|d`), `update` (`auto`|`never`).
- 🔴 **`fetch=` is a NAME, not an enum** (3.0). It resolves to
  `<fetchers dir>/<name>.py`, so `fetch=confluence` works the moment you write
  `.fux/fetchers/confluence.py` — the same pattern `.fux/decoders/` already
  uses. The grammar checks shape only; `fux doctor`'s `fetcher bindings` row
  reports a name with no file, and a **typo now parses**. The `fux-fetcher`
  skill covers writing one.
- **The attribute KEYS stay closed at seven.** Open values, closed keys — an
  unknown key is still a loud error naming `file:line`.
- `!<glob>` in `dirs` subtracts a path and everything under it. `*` does not
  cross `/`; `**` is any depth. There is no un-exclude.

**Hand-editing is legal; the reader is lenient.** A missing attribute takes its
default, and `fux add` marks such lines with `*` in its listing. The CLI edits
one line and keeps every comment.

**`fux add` writes EVERY attribute on a URL line**, defaults included, so a
line says what it means and a policy change is a one-word diff. The values it
writes are **your repo's** — `[sources.url]`'s `fetcher`, `keep`,
`ttl`, `enrich` and `update` are resolved first, and an explicit flag beats
both. ⚠ **A stated attribute beats `[sources.url]` afterwards**: editing
`fux.toml` later does not reach a line that already states the attribute, so
change the lines too (or hand-write lines that omit it).

## 3 · `fux add`

**The entry decides the list.** Anything with `scheme://` goes to `urls` (only
`http`/`https` are accepted); `--types` sends it to `.fux/formats.toml`;
everything else goes to `dirs` and must exist on disk. `docs/` and `docs` are one
entry.

| flag | records | valid for |
|---|---|---|
| `--archived` | `archived=true` | dirs, urls |
| `--cdp` / `--http` | `fetch=cdp` / `fetch=http` — the two shipped fetchers. **There is no `--fetch <name>` flag**: for a custom one, `fux add <URL> --no-ingest`, edit the `fetch=` value, then `fux ingest <URL>` | urls |
| `--keep` / `--no-keep` | `keep=` | urls |
| `--ttl D` | `ttl=D` (`0`, `30s`, `15m`, `1h`, `7d`) | urls |
| `--no-update` | `update=never` | urls |
| `--types` | the entry is a file-type pattern | types |
| `--dry-run` | prints `would add <line>` and the plan; writes nothing | all |
| `--no-ingest` | writes the line only | all |
| `--no-fetch` | writes the URL line and ingests offline | urls |

A flag for an attribute the list does not have (`--cdp` on a directory), or two
flags for one attribute, is an error and writes nothing. There is no flag for
`enrich=`; that is a hand edit, and the `fux-enrich` skill explains it.

**Exit codes — branch on these, the verbs have no `--json`:**

- `1` — an error, **or a URL whose fetch failed or was refused.** The line *is*
  written; stderr says `the line is written; the fetch failed: <reason>`.
- `0` — success, including a file the type allowlist rejects. Stdout then says
  `-> the line is listed, and the type allowlist rejects it` and names the
  `--types` command. **Adding a file never overrides the allowlist.**

⚠ **`--dry-run` never fetches.** It cannot tell you whether a URL works; see the
`fux-fetcher` skill for testing one.

**`fux add <URL> --no-update` fetches once, then never again.** One fetch is
what makes the line ingestable at all; the pin governs every run after it,
`--refetch-all` and `--full` included. ⚠ **A pinned line written BY HAND into
`.fux/sources/urls` is never fetched** — `fux add` on a line that already exists
reports `unchanged` and ingests nothing, so it has no record and no document.

⚠ **A URL needs `[sources.url]` in `fux.toml`**, including `max_parallel`.
Without it the line is recorded and nothing can fetch it.

## 4 · `fux remove`

**Always `--dry-run` first**, because there are two branches:

| dry run says | what happens |
|---|---|
| `would remove  X — it has its own line` | the line is deleted |
| `would exclude !X — covered by <parent>, which stays listed` | a `!X` line is added to `dirs` |

`urls` and `formats.toml` have no exclusions — the entry must be an exact line.
To keep files of a type out, write the pattern in `.fux/.fuxignore`.

Removal re-ingests offline and prints `dropped <id> from the index` (or
`nothing left the index`) and any inbound graph edges lost. Removing a URL
also forgets its retained bytes.

⚠ **Undoing an exclusion takes TWO edits.** Delete the `!X` line from
`.fux/sources/dirs`, **and** every `<path>   # excluded by !X` line fux wrote into
the `# >>> fux: not indexed >>>` block of `.fux/.fuxignore` — those lines keep the
files out on their own. `fux add X` refuses while the `!` line exists.

## 5 · `fux ingest`

| form | does |
|---|---|
| `fux ingest` | re-ingests; fetches the URLs **known to be stale** (all of them if nothing has recorded staleness yet) |
| `fux ingest --refetch-all` | re-ingests and fetches every listed URL |
| `fux ingest <entry>` | the entry must already be listed; a URL fetches that one only |
| `fux ingest --check` | **read-only, offline**: compares files on disk with the index |
| `fux ingest --no-fetch` | re-ingests from disk and opens no socket — what `fux hooks` writes |
| `fux ingest --failed` | fetches only the URLs whose last run failed |

- **A failed fetch keeps the prior record.** To drop a dead page, `fux remove` it.
- **Exit is `0` even when fetches fail.** Read stderr for
  `! <url> — <reason>; prior record kept`.
- **Pinned lines (`update=never`) are never fetched**, even by name. Only the
  `fux add` that writes the line gets its one fetch.
- `--check` prints `stale  <path>` / `gone   <path>` lines, then `N stale.` or
  `nothing has drifted.`; it never checks URLs and always exits `0` — **drift is
  a fact, not a failure**, so read the output, never the status.
- **`--failed` fetches exactly the URLs whose last run failed** (`fail_streak >
  0`) and nothing else. It is the most specific selector, so it wins over
  `--refetch-all`; with nothing failing it fetches nothing and says so.
- **`--no-fetch` opens no socket.** Same flag, same meaning `fux add` carries.
  Use it in CI and on an air-gapped clone; there is no `--offline` alias.
- **`--check` and `--list-skipped` are both exit-early.** Given both, `--check`
  wins — it is the one with a `--json` form and the one a pipeline gates on.

## 6 · "Why isn't file X indexed?"

A file is indexed only if **all** of these hold: a `dirs` entry covers it and no
`!` excludes it · `.fux/.fuxignore` does not ignore it · `.fux/formats.toml`
admits its type · it is readable.

```bash
fux ingest --list-skipped        # read-only, offline: one `path: reason` per line
```

| reason | fix |
|---|---|
| `not an indexed file type` | `fux add '*.ext' --types`, then see the frozen-line ⚠ below |
| `excluded by !<pattern>` | the `!` line in `.fux/sources/dirs` |
| `ignored by .fux/.fuxignore:<n> …` | that line, or a later `!path` in `.fuxignore` |
| `empty` · `binary` · `non-utf8` | nothing to index; no setting overrides these |
| path absent from the output | not under any `dirs` entry → `fux add`; or inside a dot-directory, which is never walked |

- **Listed, decoded to nothing** (a scanned PDF): it is in `.fux/enrich/queue.tsv`,
  not in `--list-skipped`. See `fux-enrich` or `fux-decoder`.
- ⚠ **Fix applied and still missing?** Ingest writes each skip into
  `.fux/.fuxignore`, and that line **keeps deciding**. Ingest then warns
  `.fux/.fuxignore lists <path> as <reason>, and that is no longer true`. Delete
  that line and run `fux ingest`.
- **A URL** is never in `.fuxignore`. Run `fux ingest <URL>` and read its `!`
  line; a sign-in or refusal reason means the `fux-fetcher` skill.

## 7 · `archived`, `keep` and PII

- **`archived` is declared, never inferred.** A directory named `archive/` is
  live until its line says `archived=true`. A nested line (`docs/old
  archived=true` under `docs`) applies to its subtree. Such results carry
  `archived: true` — follow the `fux-archived-results` policy.
- ⚠ **`meta` is GONE as of fux 3.x, and a list still carrying it will not
  load.** It existed for URLs only: `hashed` (the default) committed a title
  *hash* and no readable title or phrases. **Every URL record now commits a
  readable `title` and `phrases`, exactly like a file record** — so a private
  page's title is in the repo for anyone who clones it. Use `.fux/pii.toml` if a
  value must not be committed, or do not index the page. **The URL itself was
  always committed either way.** Fix: delete `meta=…` from the line.
- **`keep=true` (default) retains the fetched bytes in `.fux/acquired/`** —
  gitignored, local, not redacted. It lets `fux answer` verify offline;
  `--no-keep` for pages that must not sit on disk.
- **PII:** these verbs refuse to run without `.fux/pii.toml`, and redaction
  applies to the committed index only. See `fux-pii`.

## Don't

- **Don't change the corpus as a side effect** of another task.
- **Don't infer `archived` from a path or a title** — ask, then declare it.
- **Don't use `--plain` on an intranet page** without the owner saying it is public.
- **Don't trust `fux ingest`'s exit code** as "every URL fetched" — read the `!` lines.
- **`fux update` in a script is a 3.0 break.** It exits non-zero with argparse's
  *invalid choice*; there is no alias. Replace it with `fux ingest`.
- **Don't undo a remove by deleting only the `!` line** — the `.fuxignore` line stays.
- **Don't write `!path` in `.fux/.fuxignore` to exclude** — there it re-includes.
- **Don't treat `--dry-run` as proof a URL is fetchable.**

Related skills: fux-usage, fux-search, fux-answer, fux-graph, fux-index, fux-maintain, fux-config, fux-mcp, fux-fetcher, fux-pii, fux-decoder, fux-enrich, fux-archived-results.
