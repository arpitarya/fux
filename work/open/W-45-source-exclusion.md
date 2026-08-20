# W-45 — A source tree needs a way to exclude mechanical artifacts

**Status:** OPEN (Lane A) — **verdict E ratified by Arpit, 2026-08-20** ([`source-exclusion.compare.md`](../compare/source-exclusion.compare.md)): an exclusion **entry** (`!path/glob`) in `.fux/sources/dirs`, not an attribute. What remains is the build, and **it lands with [W-55](W-55-no-file-type-filter.md)** — one grammar change, not two
**Blocked by:** —
**Evidence:** [`../regression/2026-08-12-r2-close/report.md`](../regression/2026-08-12-r2-close/report.md)
§Finding 3
**Opened by:** M2 build, 2026-08-12
**Model:** **Opus** for the config decision, Sonnet to build it once decided.

## The finding

The source list is an include-only whitelist. There is no way to say *"index
this directory, except the machine-generated parts."*

**The list moved on 2026-08-19** — it is `.fux/sources/dirs`, not
`[sources] dirs`, which is now a retired key ([ADR-DIR-LIST](../../docs/adr/0023_dir-list.md)
decision 1). Nothing about the finding below changed; only where the whitelist
lives, and the fact that a line can now carry an attribute.

That bit immediately, in this repo, in the most self-referential way
possible: committing a conformance run's **raw CLI output** into `docs/` put
the query strings and the result titles into the corpus, so the evidence for
"why did pruning fail" became the top-ranked answer to *"why did pruning
fail"*. Every future run filed makes it worse.

## Why the current remedy is not the fix

The dumps moved to a **dot-prefixed** `.evidence/` directory, because the
git-dir walker already skips any path with a dot-prefixed part. That works,
costs nothing, and needs no engine change.

But it is a convention riding on an implementation detail:

- It is invisible — nothing says *"dot-prefix means not indexed"* except
  `gitdir.py`'s walker.
- It conflicts with the conformance law in `CLAUDE.md`, which names
  `evidence/`.
- It does not generalize. A consumer with generated API docs, vendored
  fixtures, or a `build/` directory inside a documentation tree has the same
  problem and no dot-prefix to reach for.

> **2026-08-19 — this item now has a home, and still no verdict.**
> [ADR-DIR-LIST](../../docs/adr/0023_dir-list.md) moves source directories into
> a line-oriented committed file with per-entry attributes, so "index this
> directory, except the generated parts" is an attribute on a line rather than a
> new config shape. **The schema question is answered; the fork is not.** The
> attribute set is closed at one (`archived`), so adding an exclusion is a change
> to that record, and this item still owes its compare doc.

## 2026-08-20 — the compare doc is written, and it changed the shape of the answer

[`work/compare/source-exclusion.compare.md`](../compare/source-exclusion.compare.md)
is the fork's doc. Three things came out of writing it that this file did not
know:

1. **Options C and D are eliminated by measurement, not argument.** C
   (`.gitignore`) solves nothing — every contaminating file is git-*tracked*.
   D (document the dot-prefix) is **measurably decayed**: of seven filed runs,
   **two use `.evidence/` and five use plain `evidence/`**, and the five
   include every run filed after this item was opened.

2. **The proposed verdict is *not* the attribute ADR-DIR-LIST anticipated.**
   It is an exclusion **entry** (`!work/regression/*/evidence`), because the
   attribute grammar describes properties of the thing on the line, and
   attribute values carry no whitespace and no quoting — so two exclusions
   would need a comma sub-grammar the format has never had. This is a
   judgment, it is argued in the doc, and it is Arpit's to override.

3. **A larger, unrecorded cause was found underneath it.** The walker has **no
   file-type filter**: 21 of 150 indexed documents (14 %) are `.json`, `.svg`,
   `.sh`, `.py` or `.mermaid`. Filed as
   [W-55](W-55-no-file-type-filter.md). **14 of the 16 files this item was
   opened about are non-prose**, so a type filter alone would close most of
   the motivating case. The compare doc recommends deciding W-55 first or
   together — buying a path-exclusion system to solve a problem an extension
   allowlist mostly closes is the wrong purchase.

The measured contamination, re-derived rather than read: **150 indexed
documents · 33 (22.0 %) from `work/regression/` · 16 under `evidence/`**, and
a `fixture.sh` outranks the very record it illustrates.

## The options

*Superseded by the compare doc's option set — kept because it is what the
options looked like before they were measured.* Option A read
`[sources] exclude`, a config key that **no longer exists**: `[sources] dirs`
was retired on 2026-08-19 and the list is now `.fux/sources/dirs`, so A became
"an attribute on a directory line" and, after the argument above, an exclusion
**entry** instead.

| option | shape | measured outcome |
|---|---|---|
| **A · an exclusion on the directory line** | an attribute, or (proposed) a `!`-prefixed entry | **live** — the two shapes are the real fork |
| **B · a `.fuxignore` file** | gitignore-syntax, per-directory | **rejected** — a second ignore language, and gitignore's negation/`**`/precedence rules are what a stdlib reimplementation would owe |
| **C · honour `.gitignore` only** | index nothing git ignores | **eliminated by measurement** — every contaminating file is git-*tracked*; this solves nothing |
| **D · document the dot-prefix rule** | make the implementation detail an explicit contract | **eliminated by measurement** — followed by 2 of 7 filed runs and dropped by the other 5 |

**No recommendation from this file** — the compare doc carries the proposed
verdict, and the call is Arpit's. This is a config-surface decision on a `$0`,
stdlib-only tool where every added key is permanent, and the adapter-cap
discipline says config surface is not free.

## Definition of done

- [x] A compare doc, per the standing rule — this is a fork with real options.
      **Done 2026-08-20:** [`source-exclusion.compare.md`](../compare/source-exclusion.compare.md).
- [ ] **Arpit's verdict**, then an ADR. *This is the only thing standing
      between this item and a build.*
- [ ] Decided with or after [W-55](W-55-no-file-type-filter.md), per the
      compare doc's sequencing recommendation.
- [ ] `CLAUDE.md`'s conformance-law wording reconciled with whatever wins.
      **Corrected 2026-08-20:** this line used to say "this repo now writes
      `.evidence/`". It does not — it writes **both**, `.evidence/` in 2 runs
      and `evidence/` in 5, which is the decay that killed option D.
- [ ] The three frozen R2 questions re-run afterwards, since this changes what
      is in the corpus.

## Hazard

**Do not let this quietly widen into a general ignore system.** The whole
point of the whitelist being short is that a reader can tell what is indexed
by reading five lines of `.fux/sources/dirs`. An exclusion mechanism
that needs its own mental model has cost more than it saved.
