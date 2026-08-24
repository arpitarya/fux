---
type: Compare Doc
title: File Type Filter
description: How fux decides which files in a source tree are documents — built-in allowlist vs a third source file vs a directory attribute vs content sniffing.
status: accepted
timestamp: 2026-08-20T00:00:00Z
---

# Which files are documents — Comparison

>
> ⚠ **Status corrected 2026-08-22 (queue review):** this read `proposed` while its verdict landed with **W-45 (verdict E, decided the same day)**, W-45 and W-55 are both archived, and [ADR-TYPES](../../docs/adr/0031_types-list.md) is `accepted` and shipped. Decided and built; only the frontmatter lagged.

> **VERDICT: G — DECIDED by Arpit, 2026-08-20.** A built-in default allowlist,
> overridable by `.fux/sources/types`. A third committed source file, one glob per line,
> same grammar as `dirs` and `urls`, `!` to subtract. **Absent means the
> built-in default applies** — not "index everything", which is today's
> behaviour and the defect.
> **Status:** **decided.** The build is [W-55](../../archive/open/W-55-no-file-type-filter.md)
> and it **lands with [W-45](../../archive/open/W-45-source-exclusion.md)** (verdict **E**,
> decided the same day) — one grammar change to `.fux/sources/`, not two.
> **Confidence at the time of the call:** high on rejecting F (content
> sniffing) and D (a TOML key); medium-high on G over A, which is a defaults
> judgment rather than a measurement.
> **Reopen when:** a consumer's corpus is majority non-`.md` prose and the
> built-in default is wrong more often than it is right — that is the one
> claim G rests on and it is measured on one repo.

## Context

`gitdir.py::_candidate_paths` skips dot-prefixed paths, then `_skip_reason`
drops empty, binary and non-UTF8 content. **There is no third condition.**
Anything text-decodable is a document, and no record decides that it should
be.

Measured on this repo's committed index, 2026-08-20 — re-derived, not copied:

| extension | docs | share | tokens | share |
|---|---|---|---|---|
| `.md` | 129 | 86.0 % | 180 144 | 85.0 % |
| **`.json`** | 9 | 6.0 % | **24 209** | **11.4 %** |
| **`.svg`** | 6 | 4.0 % | 4 743 | 2.2 % |
| **`.sh`** | 3 | 2.0 % | 2 088 | 1.0 % |
| **`.py`** | 2 | 1.3 % | 362 | 0.2 % |
| **`.mermaid`** | 1 | 0.7 % | 346 | 0.2 % |

**21 of 150 documents (14 %) are not prose, and they carry 15 % of the
tokens** — `.json` alone is 11.4 %, because a machine-written evidence file is
long and repetitive, which is exactly the shape that distorts `df`.

**Scope:** this decides the **git-dir walker only**. A URL record is whatever
its fetcher returned as markdown ([ADR-FETCHER](../../docs/adr/0019_fetcher.md)),
so there is no extension to filter on and nothing here applies to it.

## Prior art

- **ripgrep** — named type definitions mapping a name to globs
  (`--type-add 'web:*.html'`), composed with `--type` / `--type-not`, later
  definitions overriding earlier ones with `.gitignore` semantics, persisted
  in a config file. **The lesson taken:** names over raw globs at the point of
  *use*; globs at the point of *definition*.
- **GitHub Linguist** — four categories (`vendored`, `generated`,
  `documentation`, `detectable`) declared as `.gitattributes` attributes, over
  a **default heuristic** in `vendor.yml` / `generated.rb` / `documentation.yml`
  that most repos never touch. **The lesson taken:** ship a default that is
  right for the common case, and make the override declarative and committed.
- **Sphinx `source_suffix`** — an explicit allowlist mapping extension to
  parser; a file with an unlisted suffix is simply not a source. **The lesson
  taken:** allowlist, not denylist. A denylist is never finished.

## Options

- **A — a third source file, no built-in default** *(Arpit's shape)*:
  `.fux/sources/types`, one glob per line. Absent or empty means **index
  nothing**, so every repo must write it. Explicit, and nothing is implicit
  anywhere.
- **B — a built-in allowlist, no configuration at all.** `*.md`, `*.txt`,
  `*.rst`, `*.adoc` compiled in. Zero surface; changing it needs a release.
- **C — a `types=` attribute on each `dirs` line.** Per-root control:
  `docs types=md,rst`. Expresses "this root is prose, that one is code".
- **D — a `[sources] types` array in `fux.toml`.** The shape ADR-DIR-LIST
  just moved *away* from.
- **E — named type sets, ripgrep-style**, defined in the types file and
  referenced from `dirs` lines (`docs types=doc`). Two levels of indirection.
- **F — content-based classification.** Sniff the bytes and decide whether a
  file reads as prose.
- **G — a built-in default, overridable by `.fux/sources/types`**
  *(proposed verdict)*: the compiled-in allowlist applies unless the file
  exists, in which case the file **replaces** it. `!` subtracts, matching the
  exclusion grammar W-45 settled.

## Matrix

| criterion (weight) | A file-only | B built-in | C attribute | D toml | E named sets | F sniffing | **G default+file** |
|---|---|---|---|---|---|---|---|
| correct with **zero config** (H) | **no** — every repo must write it | **yes** | no | no | no | yes | **yes** |
| a consumer can change it **without a release** (H) | yes | **no** | yes | yes | yes | n/a | **yes** |
| deterministic, L3-safe (H) | yes | yes | yes | yes | yes | **no** | **yes** |
| one grammar, one parser (M) | **yes** | n/a | yes | no | partly | n/a | **yes** |
| survives 10⁵–10⁶ docs across many repos — *a deferred target since 2026-08-21, re-weighted to M; it was never the row that decided this fork* (M) | yes | rigid | **yes** | yes | **yes** | no | yes |
| reviewable in a diff (M) | **yes** | no | yes | yes | yes | **no** | **yes** |
| cost to build (L) | low | **lowest** | low | low | **high** | high | low |

## Why the losers lose

**F — content sniffing is disqualified, not merely rejected.** Deciding
whether bytes "read as prose" is a classifier, and a classifier that misfires
does so silently — indexing a lockfile as a runbook, or dropping a sparse but
real document. This repo has already ruled that a heuristic must not decide
what a document *means*
([ADR-HTTP-FETCHER](../../docs/adr/0021_http-fetcher.md) decision 3); the same
argument applies to deciding what a document *is*. It also cannot be reviewed:
there is no diff for a judgment made at ingest.

**D — a TOML array is the shape ADR-DIR-LIST just retired.** One diff hunk,
one merge conflict, and it puts a corpus decision back inside config after a
record deliberately took it out. Rejecting it is consistency, not taste.

**B — a built-in allowlist alone is right until it isn't.** A team whose
runbooks are `.adoc`, or whose handbook is `.org`, or who index `.txt`
postmortems, must wait for a fux release to index their own documents. For a
`$0` offline tool that is a hard stop, not an inconvenience.

**A — file-only is B's mirror image.** It makes the 86 % case do work for the
14 % case: every consumer writes a types file before fux indexes anything, and
the first one they write will be the same four lines everyone else wrote. It
is also a **silent-empty hazard** — a missing or empty file means an empty
index, which looks like a broken engine rather than a missing config.

**C — the attribute is more expressive than the problem.** Per-root types
answer "this root is prose, that one is code", which is real but rare; and it
puts the same four globs on every line of a long `dirs` file. **It is not
excluded forever** — the reopen trigger below is exactly the case that would
justify it.

**E — named sets are ripgrep's answer to a problem fux does not have.**
ripgrep needs names because a human types `-tweb` at a prompt fifty times a
day. Fux reads a committed file once per ingest. The indirection buys nothing
and costs a second grammar.

## The proposed shape

```console
$ cat .fux/sources/types
# absent -> the built-in default. Present -> this file replaces it.
*.md
*.markdown
*.txt
*.rst
*.adoc
!*.min.md              # subtract, same `!` grammar as dirs exclusions
```

**Built-in default:** `*.md`, `*.markdown`, `*.txt`, `*.rst`, `*.adoc`,
`*.org`. Prose formats only — no `.json`, `.svg`, `.sh`, `.py`, `.mermaid`,
and no extensionless files, which are `LICENSE`, `Makefile` and `Dockerfile`
far more often than they are documents.

**Precedence is a conjunction, and deliberately not a priority order.** A file
is indexed **iff** it is under an included `dirs` entry **and** not matched by
a `!` exclusion entry **and** matched by the type allowlist. No rule overrides
another, so there is no order to remember and no order to get wrong.

## Consequences

- **This is a breaking change for any existing index**, including this repo's:
  21 records disappear and `df` moves for every surviving document. It needs a
  re-ingest and a `CHANGELOG` entry flagged breaking. **It is also a ranking
  change**, which means it cannot ship on this corpus alone —
  [W-52](../../archive/open/W-52-df-over-the-union.md)'s pre-registration discipline
  applies here too, and the two should be measured in one run.
- **It removes 14 of W-45's 16 motivating files** — but not the other two, and
  not `evidence/report.md`. Both mechanisms are still needed; this one is
  larger and simpler, which is why it should land first.
- **`.mermaid` is a judgment call, stated so it is not silently made.** It is a
  diagram source, not prose, and the ASCII twin every ADR carries means the
  diagram's content is already indexed as markdown. Excluded.
- **A third file under `.fux/sources/` makes the trio complete**: `dirs` says
  *where*, `types` says *what*, `urls` says *what else*. That is a clean
  division and it is the argument for a file over an attribute.
- **`fux setup` should write the types file with the default in it, commented**
  — so a consumer sees what they are getting and can edit it, rather than
  discovering a built-in list by reading source.

## Reopen trigger

**A consumer needs different types for different roots** — `docs/` is prose,
`runbooks/` is `.adoc`, `vendor/` is nothing — which is precisely what option
**C**'s attribute expresses and this verdict does not. One real instance
reopens it, and the migration is additive: an attribute on a `dirs` line would
override the global file for that root.

## References

- ripgrep's type system — https://github.com/BurntSushi/ripgrep/blob/master/GUIDE.md
- GitHub Linguist overrides and its default heuristics —
  https://github.com/github-linguist/linguist/blob/main/docs/overrides.md
- Sphinx `source_suffix`, allowlist-by-extension —
  https://www.sphinx-doc.org/en/master/usage/configuration.html
- The measurement — re-derived from `.fux/index/*.jsonl`, 2026-08-20; the
  method is four lines and is reproduced in
  [W-55](../../archive/open/W-55-no-file-type-filter.md).
- The exclusion grammar this reuses —
  [`source-exclusion.compare.md`](source-exclusion.compare.md) verdict E.
