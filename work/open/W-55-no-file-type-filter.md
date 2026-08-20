# W-55 — the walker has no file-type filter, so machine data is indexed as documents

**Status:** OPEN (Lane A) — **verdict G ratified by Arpit, 2026-08-20**
([`file-type-filter.compare.md`](../compare/file-type-filter.compare.md)): a
built-in default allowlist, overridable by `.fux/sources/types` — one glob per
line, `dirs` grammar, `!` subtracts, **absent means the default applies**.
Built-in: `*.md` `*.markdown` `*.txt` `*.rst` `*.adoc` `*.org`. What remains is
the build, and **it lands with [W-45](W-45-source-exclusion.md)** (verdict E) —
one grammar change to `.fux/sources/`, not two. · **Filed:** 2026-08-20
**Blocked by:** — · **[W-45](W-45-source-exclusion.md) was decided 2026-08-20
(verdict E) and now waits on this one**: both change the same grammar, so they
land as one change
**Model:** **Opus** to decide (it is a permanent config-surface question on a
`$0` tool), Sonnet to build once decided.

## The finding

`gitdir.py::_candidate_paths` applies **no extension filter of any kind**. It
skips dot-prefixed paths, then `_skip_reason` drops empty, binary and non-UTF8
content. **Everything else is a document.**

```python
for path in base.rglob("*"):
    if not path.is_file():
        continue
    if any(part.startswith(".") for part in path.relative_to(base).parts):
        continue  # dotfiles/dotdirs (.git, .DS_Store, …) are never doc content
    yield path
```

There is no third condition, and no record decides that there should not be.

## Measured, on this repo's committed index (2026-08-20)

| extension | indexed | |
|---|---|---|
| `.md` | 129 | prose |
| `.json` | 9 | **not prose** |
| `.svg` | 6 | **not prose** |
| `.sh` | 3 | **not prose** |
| `.py` | 2 | **not prose** |
| `.mermaid` | 1 | **not prose** |

**21 of 150 documents — 14 % of the index — are not documents.**

```bash
python3 - <<'PY'
import json, pathlib, collections
c = collections.Counter()
for p in sorted(pathlib.Path(".fux/index").glob("*.jsonl")):
    for l in p.read_text().splitlines():
        if l.strip() and '"_format"' not in l:
            c[pathlib.Path(json.loads(l)["loc"]).suffix or "(none)"] += 1
print(dict(c))
PY
```

## Why it is real, and not cosmetic

**It is ranking-visible.** A raw JSON blob takes second place on a plain query:

```console
$ fux ask "arm audit results" --scan --top 3
9.2050  ANALYSIS — M1-rerun, the pruning gate made decidable  (…/ANALYSIS.md)
8.7376  arm-audit.json                                        (…/evidence/arm-audit.json)
```

`arm-audit.json` has no title, no headings and no prose. Its `title` is its
filename, because the frontmatter parser found nothing and fell back — so the
index is carrying a document whose every extracted field is an artefact of
having no fields.

**It inflates `df` for exactly the terms that matter.** A `results.json`
repeats the corpus's own vocabulary — `pruning`, `recall`, `retention` — in
machine form, which raises those terms' document frequency and *lowers* their
discriminating power for the prose documents a reader actually wants. This is
the same class of contamination as [W-52](W-52-df-over-the-union.md) and is
**not** the same instance: W-52 is live-vs-archived, this is prose-vs-data.

**It is a scale problem, not a this-repo problem.** Under the litmus — a
10k-engineer corporation's mega-project, 10⁵–10⁶ documents across thousands of
repos — "index every UTF-8-decodable file under a configured directory" means
indexing `package-lock.json`, generated OpenAPI specs, vendored fixtures,
Terraform, minified JS that happens to decode, and every `.csv` in the tree.
The failure is not 14 %; it is unbounded, and it lands on the first consumer
who points fux at a repo root.

## The fork (this is why it needs a verdict, not a build)

| option | shape | cost |
|---|---|---|
| **A — a closed extension allowlist in code** (`.md`, `.markdown`, `.txt`, `.rst`?) | no config surface at all; a record decides the set | smallest; wrong for a consumer whose runbooks are `.adoc` |
| **B — an allowlist with a config override** | a key in `fux.toml` or an attribute in `.fux/sources/dirs` | permanent config surface, and the adapter-cap discipline says that is not free |
| **C — a `types=` attribute per directory line** | `docs types=md,adoc` | same value-delimiter problem [W-45's compare doc](../compare/source-exclusion.compare.md) raises against `exclude=` |
| **D — keep indexing everything; solve it with path exclusion only** | W-45 alone | leaves the scale problem entirely unsolved |
| **E — content sniffing** (does it look like prose?) | no list to maintain | **almost certainly wrong**: a heuristic on the maintenance path is a determinism and debuggability hazard, and "why is this file not indexed" becomes unanswerable |

**No recommendation is offered here** — that is [the compare doc's](../compare/source-exclusion.compare.md)
job if this graduates, and Arpit's call either way. What this file asserts is
only that the question is **open, unrecorded, and larger than the item it was
found under**.

## Definition of done

- [ ] A compare doc, per the standing rule — this is a fork with real options.
      It may be folded into
      [`source-exclusion.compare.md`](../compare/source-exclusion.compare.md)
      if Arpit prefers one decision over two.
- [ ] Arpit's verdict, then an ADR — or an amendment to
      [ADR-INGEST](../../docs/adr/0007_ingest.md) /
      [ADR-DIR-LIST](../../docs/adr/0023_dir-list.md), whichever owns it.
- [ ] `_candidate_paths` implements the verdict, with a test that a `.json`
      beside a `.md` in a configured directory is skipped **with a reason**
      (`fux ingest --list-skipped` must say why, or this becomes the next
      invisible rule).
- [ ] The three frozen R2 questions re-run, since this changes the corpus.

## Hazard

**Do not build the obvious allowlist and call it decided.** `.md`-only is
right for this repo and wrong for a consumer with an `.adoc` or `.rst` estate,
and a hardcoded set that a consumer cannot change is the kind of thing that
gets discovered at adoption time. That is precisely why this is filed as a
fork rather than fixed as a defect.

## Evidence

Measured in this file, reproducible by the two commands above against the
committed index. Found while writing
[`../compare/source-exclusion.compare.md`](../compare/source-exclusion.compare.md)
for [W-45](W-45-source-exclusion.md).
