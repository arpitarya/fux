# W-45 — A source tree needs a way to exclude mechanical artifacts

**Status:** OPEN · the config-surface question is **answered** ([ADR-DIR-LIST](../../docs/adr/0023_dir-list.md): an attribute on a directory line); the fork itself is not, and still owes a compare doc
**Blocked by:** —
**Evidence:** [`../regression/2026-08-12-r2-close/report.md`](../regression/2026-08-12-r2-close/report.md)
§Finding 3
**Opened by:** M2 build, 2026-08-12
**Model:** **Opus** for the config decision, Sonnet to build it once decided.

## The finding

`[sources] dirs` is an include-only whitelist. There is no way to say *"index
this directory, except the machine-generated parts."*

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

## The options

| option | shape | cost |
|---|---|---|
| **A · `[sources] exclude`** | a list of repo-root-relative globs, applied after the walk | small; one config key, one schema line, an ADR |
| **B · a `.fuxignore` file** | gitignore-syntax, per-directory | familiar to users, but a second ignore language in a repo that already has `.gitignore` |
| **C · honour `.gitignore` only** | index nothing git ignores | free and already true (untracked files are walked, though — this would be a change) |
| **D · document the dot-prefix rule** | make the implementation detail an explicit contract | free, but does not generalize past this repo |

**No recommendation.** This is a config-surface decision on a `$0`,
stdlib-only tool where every added key is permanent, and the adapter-cap
discipline says config surface is not free. Worth one compare doc rather than
a builder's guess.

## Definition of done

- [ ] A compare doc, per the standing rule — this is a fork with real options.
- [ ] Arpit's verdict, then an ADR.
- [ ] `CLAUDE.md`'s conformance-law wording reconciled with whatever wins
      (it currently says `evidence/`; this repo now writes `.evidence/`).
- [ ] The three frozen R2 questions re-run afterwards, since this changes what
      is in the corpus.

## Hazard

**Do not let this quietly widen into a general ignore system.** The whole
point of `[sources] dirs` being a short whitelist is that a reader can tell
what is indexed by reading five lines of `fux.toml`. An exclusion mechanism
that needs its own mental model has cost more than it saved.
