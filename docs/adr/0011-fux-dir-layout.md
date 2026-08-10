---
type: ADR
title: "ADR-0011: the .fux directory — declared layout, committed vs derived"
description: Declares every child of .fux/ as committed (index, sources, middleware) or derived (runtime, cache), with a self-describing README, a narrow .gitignore that never uses `*`, CACHEDIR.TAG on derived dirs, and two `fux doctor` assertions. Relocates ADR-0010's URL list to .fux/sources/urls and its middleware to .fux/middleware/cdp.py, with tunables moving to an opaque [sources.url.config] table.
status: proposed
timestamp: 2026-08-11T00:00:00Z
---

# ADR-0011: the `.fux` directory — declared layout, committed vs derived

- **Status:** proposed (built at Arpit's direction in session, 2026-08-10; he
  ratifies by flipping this line)
- **Date:** 2026-08-11
- **Feature:** the `.fux/` directory as a declared layout, plus the relocation
  of ADR-0010's URL source into it.

## Context

`.fux/` held exactly one thing — `index/`, committed. Three pressures arrived
at once:

1. **Derived planes are coming regardless.** M2 writes mmap'd accelerator
   segments; M4 writes an ARC fetch cache. Neither belongs in git. A dotdir
   that mixes committed and derived children needs a rule *before* both exist,
   not after.

2. **ADR-0010's placements did not scale.** The URL list was an inline TOML
   array and the middleware sat at the repo root. Arpit's direction in
   session: the list can be huge and belongs in its own file under `.fux/`;
   the middleware belongs there too; its tunables belong in `fux.toml`.

3. **A 5k-entry TOML array is one diff hunk and one merge conflict.** The same
   argument that sharded the index applies to the URL list: line-oriented
   files are what git diffs and merges well. At the design point — a
   10k-engineer mega-project — a shared URL list is edited by many hands.

The riskiest part of putting committed and derived planes under one dotdir is
that an ignore rule silently drops a committed plane. The repo's own
`.gitignore` demonstrated the failure mode: it carried `.fux/*` plus
`!.fux/index/`, which would have ignored `sources/` and `middleware/` the
moment they existed, with no error anywhere.

## Decision

### The layout

Every child of `.fux/` is declared, exactly once, in
[`src/fux/store/fuxdir.py`](../../src/fux/store/fuxdir.py):

| entry | kind | what it is |
|---|---|---|
| `README.md` | committed | written-if-missing by fux; describes this table |
| `.gitignore` | committed | written-if-missing; lists ONLY derived dirs, never `*` |
| `index/` | committed | the wire-format index (ADR-0004) |
| `sources/` | committed | large line-oriented source lists (`urls`) |
| `middleware/` | committed | consumer-owned code (`cdp.py`) — edit freely |
| `runtime/` | derived | reserved for M2 accelerator segments · `CACHEDIR.TAG` |
| `cache/` | derived | reserved for M4 ARC fetch cache · `CACHEDIR.TAG` |

Three mechanisms make it hold:

- **`ensure_layout(root)`** — called at ingest start; writes `README.md` and
  `.gitignore` **only if missing**. A consumer's annotations survive forever.
- **`derived_dir(root, name)`** — what M2/M4 call; mkdirs and drops a
  `CACHEDIR.TAG` whose first line is the spec's byte-exact signature, so
  backup and archiving tools skip the directory without being told.
- **`fux doctor`** — errors if `git check-ignore` says `.fux/index` is
  ignored; warns (does not fail) on any undeclared top-level entry.

M2 and M4 may rename their reserved directories in their own ADRs — they
update the table, the README generator, and the ignore list in one change.

### The URL list is a file

`.fux/sources/urls` — one URL per line; `#` comments and blank lines ignored;
a non-`http(s)` line is a `FuxError` naming `file:lineno`; a missing file is a
loud error but **only under `--refresh-urls`** (an offline ingest must not
care); an empty file is a valid zero-URL state. The loader dedupes and sorts
before fetching, so file order is presentation and never changes committed
bytes. An inline `urls` key in `fux.toml` is now a `FuxError` pointing at the
file — a hard move, since ADR-0010 shipped hours earlier and unreleased.

### Tunables are an opaque table

```toml
[sources.url]
middleware = ".fux/middleware/cdp.py"   # default
urls_file  = ".fux/sources/urls"        # default
meta       = "hashed"

[sources.url.config]                     # OPAQUE — fux never reads a key
cdp_port   = 9222
settle_ms  = 500
```

The middleware contract gains one optional hook: **`configure(config: dict)`**,
called once after import, before `connect()`. Fux validates only that the
value is a table and passes it **verbatim**; it never reads a key inside.
`fetch`/`connect`/`close` are unchanged.

This is the load-bearing constraint, not a convenience. Typed `cdp_port` /
`settle_ms` keys in `config.py` would have put one middleware's vocabulary
into fux's own config schema — the adapter cap breached by the back door. The
opaque table is the same discipline PEP 518 uses for `[tool.*]`: the format
owner knows there *is* a table, never what it *means*.

## Alternatives considered

- **`.fux/*` blanket ignore + `!` unignores** (the status quo ante). Rejected:
  it is precisely the silent-drop failure. Git also cannot re-include a file
  whose parent directory is excluded, so the pattern is fragile in ways that
  surface as missing data, not as errors.
- **Derived planes outside `.fux/`** (e.g. `.fux-cache/`). Rejected: two
  dotdirs to explain, two things to ignore, and no gain over one declared
  table.
- **Typed middleware settings in `config.py`.** Rejected above — it breaches
  the adapter cap in spirit while keeping its letter.
- **Middleware at the repo root** (ADR-0010's original). Rejected: it puts a
  fux-shaped file in the consumer's top-level namespace, and roots are
  contested space in a mega-project monorepo.
- **`fux doctor --fix` generating the README instead of ingest.** Left open by
  the handoff (§10); built as ingest-time write-if-missing, which needs no
  extra command and is idempotent. Reversible if Arpit prefers otherwise.

## Consequences

- **Consumer-edited code now lives in a dotdir.** Precedent is strong —
  `.github/workflows/` and Husky's `.husky/` are exactly that — but linters
  that skip hidden directories by default (ruff does) will not lint
  `middleware/cdp.py`. Accepted: it is consumer code, not a CI target. Both
  the file's header and `.fux/README.md` say so explicitly.
- **The repo's own `.gitignore` had to change** — the `.fux/*` blanket is
  gone, replaced by nothing at root (the narrow `.fux/.gitignore` carries the
  derived names). `fux doctor` now asserts this stays true.
- **`src/fux/` still holds zero network code**, and the middleware is still
  imported only under `--refresh-urls`. Moving the file changed no law.
- **Tunables in `fux.toml` mean merges stay clean** — a consumer who only
  needs a different port never edits the middleware file at all, so a future
  template update does not conflict with their edit.
- **Owed:** M2 and M4 must call `derived_dir` rather than mkdir'ing their own
  paths, or the CACHEDIR.TAG guarantee silently lapses.
- **`git log --follow`** does not show pre-move history for
  `.fux/middleware/cdp.py` — the root file was never committed (it was staged,
  hours old, from the ADR-0010 session), so there was no history to preserve.
  The move was still made with `git mv`.

## References (required)

- **CACHEDIR.TAG specification** — the signature and semantics for
  cache-directory tagging: https://bford.info/cachedir/
- **pytest `cacheprovider`** — writes `CACHEDIR.TAG` + `.gitignore` +
  `README.md` into its own cache dir; the pattern this ADR copies:
  https://docs.pytest.org/en/latest/_modules/_pytest/cacheprovider.html
- **mypy PR #8193** — same tagging for `.mypy_cache`:
  https://github.com/python/mypy/pull/8193
- **Husky** — committed, consumer-edited shell hooks inside a dotdir
  (`.husky/`), the precedent for consumer code under `.fux/middleware/`:
  https://github.com/typicode/husky
- **PEP 518 `[tool]` table** — the format owner reserves a namespace and never
  interprets its contents; the model for `[sources.url.config]`:
  https://peps.python.org/pep-0518/#tool-table
- **gitignore(5)** — "It is not possible to re-include a file if a parent
  directory of that file is excluded", the fragility that killed the blanket
  pattern: https://git-scm.com/docs/gitignore
