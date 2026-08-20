---
type: Compare Doc
title: Source Exclusion
description: How a source tree says "index this directory, except the machine-generated parts" — attribute vs exclusion line vs .fuxignore vs .gitignore vs convention.
status: proposed
timestamp: 2026-08-20T00:00:00Z
---

# Excluding part of a source tree — Comparison

> **VERDICT: E — DECIDED by Arpit, 2026-08-20.** An exclusion *entry* in `.fux/sources/dirs`, one
> per line, `!` prefix, repo-relative glob, applied to the whole walk and
> order-independent. **Not** an attribute on a directory line.
> **Status:** **decided** — the build is [W-45](../open/W-45-source-exclusion.md), which stays open until
> it lands, and **lands with [W-55](../open/W-55-no-file-type-filter.md)**: one
> grammar change, not two. · **Confidence at the time of the call:** medium-high on eliminating
> B/C/D (measured), medium on E over A (a grammar-shape judgment, not a
> measurement) · **Reopen when:** a consumer needs an exclusion that must
> apply to one include root and *not* another — that is the one thing the
> attribute form expresses and this one does not.
>
> **This verdict is half an answer, and says so.** The measurement below found
> a second, larger cause that no option here addresses:
> **fux has no file-type filter at all**, so `.json`, `.sh` and `.py` are
> indexed as documents. That is [W-55](../open/W-55-no-file-type-filter.md),
> and **it should be decided before or with this one** — see §The interaction.

## Context

`.fux/sources/dirs` is an include-only whitelist
([ADR-DIR-LIST](../../docs/adr/0023_dir-list.md)). There is no way to say
*"index this directory, except the machine-generated parts."*

It bites in this repo in the most self-referential way available: the
conformance law requires every measured run to file its raw output under
`work/regression/<run>/evidence/`, `work/` is a configured source, and so
**the evidence for a finding becomes a top-ranked answer to the question the
finding was about.**

### What is actually in the index today (measured, 2026-08-20)

Re-derived from the committed index, not read from the prior write-up:

| | count | share |
|---|---|---|
| indexed documents | 150 | — |
| from `work/regression/` | 33 | 22.0 % |
| under a `regression/*/evidence/` directory | 16 | 10.7 % |

Reproduce:

```bash
python3 - <<'PY'
import json, pathlib
recs = [json.loads(l) for p in sorted(pathlib.Path(".fux/index").glob("*.jsonl"))
        for l in p.read_text().splitlines() if l.strip() and '"_format"' not in l]
ev = [r for r in recs if "/evidence/" in r["loc"]]
print(len(recs), len([r for r in recs if r["loc"].startswith("work/regression/")]), len(ev))
PY
```

And it is **ranking-visible**, not merely present:

```console
$ fux ask "the fixture behind the CLI examples" --scan --top 3
10.2071  The fixture behind ADR-CLI's examples. …  (work/regression/2026-08-18-cli-surface/evidence/fixture.sh)
 7.5843  SUPERSEDED 2026-08-19 by …                (work/regression/2026-08-18-ingest-and-index/evidence/fixture.sh)
 7.2232  ADR-CLI (0002) — the command-line surface (docs/adr/0002_cli-surface.md)

$ fux ask "arm audit results" --scan --top 3
 9.2050  ANALYSIS — M1-rerun, the pruning gate made decidable  (…/ANALYSIS.md)
 8.7376  arm-audit.json                                        (…/evidence/arm-audit.json)
```

A shell fixture outranks the record it was written to illustrate, and a raw
JSON blob with no prose in it takes second place.

### The current remedy has already failed, and that is the new fact

W-45 recorded that the dumps "moved to a dot-prefixed `.evidence/`", which the
walker skips (`gitdir.py::_candidate_paths` drops any dot-prefixed part). The
item argued this was a convention riding on an implementation detail. **It can
now be shown to have decayed rather than argued to be fragile:**

| runs under `work/regression/` | 7 |
|---|---|
| using dot-prefixed `.evidence/` (skipped) | **2** |
| using plain `evidence/` (indexed) | **5** |

The two that hold the convention are the two filed on 2026-08-12. Every run
filed since — including the three filed on 2026-08-18 and 2026-08-19, by
sessions that had read this item — used plain `evidence/`. **An invisible rule
was followed twice and then dropped**, which is the strongest available
argument that option D cannot work.

## Options

- **A — an `exclude=` attribute on a directory line.** What ADR-DIR-LIST
  anticipated. `work exclude=regression/*/evidence`.
- **B — a `.fuxignore` file**, gitignore syntax, per-directory.
- **C — honour `.gitignore` only.**
- **D — document the dot-prefix rule** and make the implementation detail a
  contract.
- **E — an exclusion *entry* in the same file** *(proposed verdict)*:
  `!work/regression/*/evidence`, one per line, same grammar position as an
  include, applied to the whole walk regardless of line order.

## Matrix

| criterion (weight) | A attribute | B `.fuxignore` | C `.gitignore` | D convention | **E exclusion line** |
|---|---|---|---|---|---|
| **solves the measured case** (H) | yes | yes | **no** — every contaminating file is git-*tracked*; `.gitignore` says nothing about them | partly, and only while remembered | yes |
| **visible in the one file you read to know what is indexed** (H) | yes | **no** — a second file, and the hazard names this | no | **no** | yes |
| **survives being forgotten** (H) | yes | yes | yes | **no — measured: 2 of 7** | yes |
| **new grammar concepts** (H) | **a delimiter inside a value** — values carry no whitespace and no quoting (ADR-URL-LIST 8) and a repeated key is a loud error (10), so two exclusions need `exclude=a,b` | a whole second ignore language | none | none | **one prefix character** |
| **merges line-by-line at scale** (M) | one long line grows and conflicts | yes | n/a | n/a | yes — the property the file format exists for |
| **generalises past this repo** (M) | yes | yes | no | **no** | yes |
| **stays inside the hazard** ("do not widen into a general ignore system") (H) | yes | **no** — gitignore syntax is negation + `**` + trailing-slash precedence, and a *partial* implementation is the dangerous kind | yes | yes | yes — one prefix, repo-relative globs, **no negation**, order-independent |

## Why not A, which is what the record anticipated

A is the closest call, and the argument against it is a grammar-shape
judgment rather than a measurement — which is why the confidence line above
separates the two.

**The attribute grammar describes properties of the thing on the line.**
`fetch=`, `meta=` and `archived=` each say something about *that* URL or *that*
directory. An exclusion is not a property of `work`; it is a statement about a
different path that happens to sit underneath it. Encoding one path inside an
attribute value of another is the mismatch, and the comma sub-grammar is the
symptom: values have never had internal structure, and a delimiter is the
workaround for the quoting the grammar deliberately does not have.

**A's one genuine advantage** is scope: `work exclude=…` cannot accidentally
exclude something under `docs`. That is the reopen-trigger above, stated as a
condition someone can check.

## The interaction — and why this verdict is half an answer

Measuring the corpus to write this doc surfaced a **separate and larger
cause**, filed as [W-55](../open/W-55-no-file-type-filter.md):
`gitdir.py::_candidate_paths` applies **no extension filter**. Anything
UTF-8-decodable is a document.

| extension | indexed |
|---|---|
| `.md` | 129 |
| `.json` | 9 |
| `.svg` | 6 |
| `.sh` | 3 |
| `.py` | 2 |
| `.mermaid` | 1 |

**14 % of this repo's index is not prose**, and it is the non-prose files that
produced both embarrassments in the repro above. Of the 16 contaminating files
under `evidence/`, **14 are `.json`, `.sh` or `.py`** — a type filter alone
would remove them without any exclusion mechanism at all.

The two are genuinely orthogonal and both real: a type filter does not stop
`evidence/report.md` being indexed, and an exclusion does not stop a
`package-lock.json` in `docs/`. But **their sizes are not comparable at the
design point.** Under the litmus — a 10k-engineer corporation's mega-project,
10⁵–10⁶ documents across thousands of repos — "index every text-decodable
file" means indexing lockfiles, generated OpenAPI specs, vendored fixtures and
Terraform. The path problem is this repo's; the type problem is everyone's.

**Recommendation on sequencing:** decide W-55 first or together. Choosing an
exclusion mechanism while the type question is open risks buying a general
path-exclusion system to solve a problem a one-line extension allowlist mostly
closes.

## Consequences if E is accepted

- `sourcelist.py` gains the `!` prefix in the entry position; `_dir_reason`
  accepts it; `DIRS` keeps its closed attribute set of one.
- **Exclusions are order-independent** and apply to the whole walk — which is
  forced, because the loader sorts, and is L3 applied to config: two people
  holding the same set in different orders must produce the same committed
  bytes.
- No negation, ever. `!` excludes; there is no un-exclude.
- ADR-DIR-LIST changes: decision 2's grammar gains the prefix, and the
  anticipation of "an exclusion attribute on a directory line" is corrected.
- `CLAUDE.md`'s conformance law is reconciled — it says `evidence/`, the repo
  writes both, and with E it can say `evidence/` and mean it.
- The three frozen R2 questions are re-run, because this changes the corpus.

## References

- [ADR-DIR-LIST](../../docs/adr/0023_dir-list.md) — the file, the grammar, the
  closed attribute set.
- [ADR-URL-LIST](../../docs/adr/0018_url-list.md) decisions 8, 10, 13 — no
  whitespace or quoting in values; a repeated key is an error; reader lenient,
  writer strict. These are what rule out the multi-value attribute.
- [`../regression/2026-08-12-r2-close/report.md`](../regression/2026-08-12-r2-close/report.md)
  §Finding 3 — where the contamination was first observed.
- [`src/fux/ingest/gitdir.py`](../../src/fux/ingest/gitdir.py) —
  `_candidate_paths`, the dot-prefix skip and the absent type filter.
- Git's own `gitignore(5)` precedence and negation rules — the concrete
  measure of what option B commits to reimplementing in stdlib:
  <https://git-scm.com/docs/gitignore>

## Reopen-trigger

**A consumer needs an exclusion that applies to one include root and not
another** — the single thing A expresses and E does not. Checkable today by
asking of any proposed exclusion: would it be wrong applied repo-wide?
