---
name: fux-sources
description: Manage what is in a Fux corpus with `fux add`, `fux remove` and `fux ingest` — the ONE verb for the first ingest and every re-ingest. Paths, file types and URLs in .fux/sources.yaml, the mandatory fetch and decoder on a URL entry, archived, keep, ttl, and why a file is not indexed. Use ONLY when explicitly asked to change the corpus ("index this folder", "add this URL", "stop indexing X"), or to answer "why isn't file X indexed". Edits committed files in .fux/.
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
| "re-index / bring the index up to date" | `fux ingest` — the same verb as the first time, for paths and URLs alike |
| "add this page / Confluence URL" | `fux add https://…` — fetches **that URL only**, then ingests |
| "index our `.srt` files" | `fux add '*.srt' --types` — a format with no decoder also needs the `fux-decoder` skill |
| "stop indexing X" | `fux remove X --dry-run`, read the branch, then `fux remove X` |
| "mark these docs archived" | `fux add old/2023-platform --archived` (a URL takes `--archived` too) |
| "refresh the URLs" | `fux ingest` — add `--refetch-all` to fetch every URL |
| "why isn't X indexed?" | §6. Change nothing until you know the reason |
| the page comes back as a login page | the `fux-fetcher` skill — that is a fetcher problem, not a list problem |

**`add` and `remove` write entries; `ingest` never writes one.** Changing an
attribute is another `fux add` on the same entry — it is an upsert.

> 🔴 **`fux update` no longer exists** (3.0). Every form of it is `fux ingest`,
> and `--all` is now `--refetch-all` — beside `--full` the old name read as its
> synonym, and the two are unrelated. A bare `fux ingest` **goes to the
> network** for the URLs known to be stale; `fux ingest --no-fetch` is the
> offline form, and it is what the git hooks run.

## 2 · The files, and their syntax

| file | holds | looks like |
|---|---|---|
| `.fux/sources.yaml` | **what is indexed, includes only**: `paths:` (directories and single files, repo-relative) and `urls:` (`http(s)` URLs) | see below |
| `.fux/config/formats.toml` | which file types are documents | `include = ["*.md", …]` and `[decoders]` `csv = "csv"` |
| `.fux/.fuxignore` | what is kept out — **the one place exclusion is spelled** | `.gitignore` grammar; `!` **re-includes** |

`fux.toml` can relocate `.fux/sources.yaml` (`[sources] sources_file`); the
other two are fixed paths.

```yaml
paths:
  include:            # indexed, no flag
    - docs
    - README.md
  archived:           # indexed as history
    - old/2023-platform
  enrich:             # in scope for `fux enrich`
    - docs/runbooks
urls:
  - url: https://wiki.corp/x
    fetch: http
    decoder: prose
    keep: true
    ttl: 24h
    enrich: false
    archived: false
    update: auto
```

**The fux YAML subset, exactly:**

- Top-level keys `paths` and `urls` only. Under `paths`, the lists `include`,
  `archived`, `enrich` — a path in any list is indexed, and each list it sits in
  is a flag it carries. `urls` is a list of entries.
- Block maps and block lists, plain or quoted values, `#` comments **at line
  start or after whitespace** — a URL `#fragment` is part of the URL.
- **Refused, naming `file:line`:** `{}` / `[]`, anchors, aliases, tags
  (so a `!` entry — exclusion goes in `.fux/.fuxignore`), `---`, `|` / `>`
  blocks, tabs, a duplicate key, a path twice in one list, a URL twice, an
  unknown key, an empty list.
- **Every value is text unless its key says otherwise** — a path named `no`
  or `1.10` is that path. File order is irrelevant: the loader sorts.
- URL entry keys: `url`, `fetch` and `decoder` (**`fetch` and `decoder` are
  any module name, both mandatory** — see below), `keep`, `enrich`, `archived`
  (`true`/`false`), `ttl` (`0` or `<int>s|m|h|d`), `update` (`auto`|`never`).
- 🔴 **`fetch` is a NAME, not an enum** (3.0). It resolves to
  `.fux/fetchers/<name>.py` when that file exists, else to the fetcher package
  `.fux/config/plugins.toml` declares (`fux-fetcher-http`, `fux-fetcher-cdp`), so
  `fetch: confluence` works the moment you write that file — the same pattern
  `.fux/decoders/` already uses. The reader checks shape only; `fux doctor`'s
  `fetcher bindings` row reports a name with no file, and a **typo parses**.
  The `fux-fetcher` skill covers writing one.
- 🔴 **`decoder` is a NAME too, and a URL entry MUST state it.** A fetcher
  retrieves bytes; the decoder named here turns them into Markdown. `prose` is
  the reserved word for a page that is already text; anything else is a
  built-in (`html`, `pdf`, `xlsx`, …) or a file in `.fux/decoders/`. **No
  default and no `[sources.url]` layer** — a URL has no trustworthy extension,
  so the entry says it. `fux add` observes the `Content-Type` once and writes
  what it saw; `fux doctor`'s `url decoders` row reports a name with no module.
- **The URL keys stay closed.** Open values, closed keys — an unknown key is a
  loud error naming `file:line`.

**Hand-editing is legal; the reader is lenient about URL attributes.** A
missing optional attribute takes its default, and `fux add` marks such entries
with `*` in its listing. The CLI inserts or deletes one line or one entry block
as text and keeps every comment and your hand order.

**`fux add` writes EVERY attribute on a URL entry**, defaults included, so an
entry says what it means and a policy change is a one-word diff. The values it
writes are **your repo's** — `[sources.url]`'s `keep`, `ttl`, `enrich` and
`update` are resolved first, and an explicit flag beats both. `fetch` is
**resolved** from `[sources.url.routes]` and the fetchers' `ROUTES` claims, and
`decoder` is **observed** on the one fetch the add performs; neither has a
source-wide key, and `fux add` refuses rather than guessing either. ⚠ **A stated attribute beats `[sources.url]` afterwards**: editing
`fux.toml` later does not reach an entry that already states the attribute, so
change the entries too (or hand-write entries that omit it).

## 3 · `fux add`

**The entry decides where it goes.** Anything with `scheme://` becomes a
`urls:` entry (only `http`/`https` are accepted); `--types` sends it to
`.fux/config/formats.toml`; everything else becomes a `paths:` entry and must
exist on disk. `docs/` and `docs` are one entry.

| flag | records | valid for |
|---|---|---|
| `--archived` | a path into the `archived:` list; a URL's `archived: true` | paths, urls |
| `--fetch STEM` | `fetch=STEM` — a file in `.fux/fetchers/`, or a declared fetcher package. Without it the routes table and the modules' `ROUTES` claims decide, and nothing matching **refuses** | urls |
| `--cdp` / `--http` | aliases of `--fetch cdp` / `--fetch http`, the two shipped fetchers | urls |
| `--decoder STEM` | `decoder=STEM` — a built-in, `prose`, or a file in `.fux/decoders/`. Without it the add **observes** the `Content-Type` on its one fetch and writes what it saw, and **refuses** if nothing claims that format | urls, types |
| `--keep` / `--no-keep` | `keep=` | urls |
| `--ttl D` | `ttl=D` (`0`, `30s`, `15m`, `1h`, `7d`) | urls |
| `--no-update` | `update=never` | urls |
| `--types` | the entry is a file-type pattern | types |
| `--dry-run` | prints `would add <line>` and the plan; writes nothing | all |
| `--no-ingest` | writes the entry only | all |
| `--no-fetch` | writes the URL entry and ingests offline. 🔴 **Requires `--decoder`** — it forbids the one fetch that would observe the type | urls |

A flag for an attribute the entry cannot have (`--cdp` on a directory), or two
flags for one attribute, is an error and writes nothing. There is no flag for
`enrich`; that is a hand edit, and the `fux-enrich` skill explains it.

**Exit codes — branch on these, the verbs have no `--json`:**

- `1` — an error, **or a URL whose fetch failed or was refused.** The entry *is*
  written; stderr says why the fetch failed.
- `0` — success, including a file the type allowlist rejects. Stdout then says
  `-> the line is listed, and the type allowlist rejects it` and names the
  `--types` command. **Adding a file never overrides the allowlist.**

⚠ **`--dry-run` never fetches.** It cannot tell you whether a URL works; see the
`fux-fetcher` skill for testing one.

**`fux add <URL> --no-update` fetches once, then never again.** One fetch is
what makes the entry ingestable at all; the pin governs every run after it,
`--refetch-all` and `--full` included. ⚠ **A pinned entry written BY HAND into
`.fux/sources.yaml` is never fetched** — `fux add` on an entry that already
exists reports `unchanged` and ingests nothing, so it has no record and no
document.

⚠ **A URL needs `[sources.url]` in `fux.toml`**, including `max_parallel`.
Without it the entry is recorded and nothing can fetch it.

## 4 · `fux remove`

**Always `--dry-run` first**, because there are two branches:

| dry run says | what happens |
|---|---|
| `would remove  X — it has its own line` | the entry is deleted from `.fux/sources.yaml` |
| `would exclude /X — covered by <parent>, which stays listed` | an anchored `/X` pattern is added to `.fux/.fuxignore` |

A URL and a `formats.toml` pattern have no exclusions — the entry must be
listed exactly. To keep files of a type out, write the pattern in
`.fux/.fuxignore`.

Removal re-ingests offline and prints `dropped <id> from the index` (or
`nothing left the index`) and any inbound graph edges lost. Removing a URL
also forgets its retained bytes.

⚠ **Undoing an exclusion means deleting its `.fuxignore` pattern, then `fux
ingest`.** `fux add X` refuses while a hand-written `.fuxignore` line excludes
`X` — it names the line to delete.

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
- **Pinned entries (`update: never`) are never fetched**, even by name. Only
  the `fux add` that writes the entry gets its one fetch.
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

A file is indexed only if **all** of these hold: a `paths:` entry of
`.fux/sources.yaml` covers it · `.fux/.fuxignore` does not ignore it ·
`.fux/config/formats.toml` admits its type · it is readable.

```bash
fux ingest --list-skipped        # read-only, offline: one `path: reason` per line
```

| reason | fix |
|---|---|
| `not an indexed file type` | `fux add '*.ext' --types`, then see the frozen-line ⚠ below |
| `ignored by .fux/.fuxignore:<n> …` | that line, or a later `!path` in `.fuxignore` |
| `empty` · `binary` · `non-utf8` | nothing to index; no setting overrides these |
| path absent from the output | not under any `paths:` entry → `fux add`; or inside a dot-directory, which is never walked |

- **Listed, decoded to nothing** (a scanned PDF): it is in `.fux/enrich/queue.tsv`,
  not in `--list-skipped`. See `fux-enrich` or `fux-decoder`.
- ⚠ **Fix applied and still missing?** Ingest writes each skip into
  `.fux/.fuxignore`, and that line **keeps deciding**. Ingest then warns
  `.fux/.fuxignore lists <path> as <reason>, and that is no longer true`. Delete
  that line and run `fux ingest`.
- **A URL** is never in `.fuxignore`. Run `fux ingest <URL>` and read its `!`
  stderr line; a sign-in or refusal reason means the `fux-fetcher` skill.

## 7 · `archived`, `keep` and PII

- **`archived` is declared, never inferred.** A directory named `archive/` is
  live until it is listed under `paths: archived:`. A nested path (`docs/old`
  under `archived:` while `docs` is under `include:`) applies to its subtree. Such results carry
  `archived: true` — follow the `fux-archived-results` policy.
- ⚠ **`meta` is GONE as of fux 3.x, and an entry still carrying it will not
  load.** It existed for URLs only: `hashed` (the default) committed a title
  *hash* and no readable title or phrases. **Every URL record now commits a
  readable `title` and `phrases`, exactly like a file record** — so a private
  page's title is in the repo for anyone who clones it. Use `.fux/config/pii.toml` if a
  value must not be committed, or do not index the page. **The URL itself was
  always committed either way.** Fix: delete `meta` from the entry.
- **`keep=true` (default) retains the fetched bytes in `.fux/acquired/`** —
  gitignored, local, not redacted. It lets `fux answer` verify offline;
  `--no-keep` for pages that must not sit on disk.
- **PII:** these verbs refuse to run without `.fux/config/pii.toml`, and redaction
  applies to the committed index only. See `fux-pii`.

## Don't

- **Don't change the corpus as a side effect** of another task.
- **Don't infer `archived` from a path or a title** — ask, then declare it.
- **Don't use `--plain` on an intranet page** without the owner saying it is public.
- **Don't trust `fux ingest`'s exit code** as "every URL fetched" — read the `!` lines.
- **`fux update` in a script is a 3.0 break.** It exits non-zero with argparse's
  *invalid choice*; there is no alias. Replace it with `fux ingest`.
- **Don't write `!path` in `.fux/sources.yaml`** — it is refused; exclusion goes in `.fux/.fuxignore`.
- **Don't write `!path` in `.fux/.fuxignore` to exclude** — there it re-includes.
- **Don't treat `--dry-run` as proof a URL is fetchable.**

Related skills: fux-usage, fux-search, fux-answer, fux-graph, fux-index, fux-maintain, fux-config, fux-mcp, fux-fetcher, fux-pii, fux-decoder, fux-enrich, fux-archived-results.
