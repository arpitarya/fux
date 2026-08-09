# Fux Global Rules Home — Comparison

> **Verdict:** Make `~/.claude/fux/global/` **its own git repo** (init in place,
> add a remote when needed) — versioned, syncable, and PR-reviewable while still
> resolving to the single path the engine reads.
> **Status:** ✅ Accepted · **Confidence:** High · **Decided:** 2026-06-01 · **By:** arpit
> **Revisit when:** more than ~3 machines or a team needs RBAC on best practices → reconsider a separate symlinked repo or a published package.

## Context

Fux holds two layers of rules (see [fux-plan.md §5](fux-plan.md)): per-project
rules in `.fux/`, and **global best practices** shared across every project
("files ≤100 lines", "no secrets in env", "async everywhere", "doc-update per
code change"). The whole point of the global layer is *maintain once, inherit
everywhere*. The question: **where does that global set physically live**, given
the engine always reads it from `~/.claude/fux/global/`?

Constraints: must resolve to one stable local path; changes should be
reviewable and reversible; ideally syncs across machines; must add **zero** API
cost; must not leak secrets into a shared/synced location.

## Options

- **A — Plain dir.** A normal, unversioned folder at `~/.claude/fux/global/`.
- **B — Git repo in place.** `git init` *at* `~/.claude/fux/global/`, optional remote. *(verdict)*
- **C — Separate repo, symlinked.** Repo lives elsewhere (e.g. a dotfiles repo); `~/.claude/fux/global/` is a symlink into it.
- **D — Published package.** Ship global rules as a pip/npm package installed into the path.

## Comparison matrix

| Criterion (weight) | A: Plain dir | B: Git in place | C: Symlinked repo | D: Package |
|--------------------|--------------|-----------------|-------------------|------------|
| Version history (H) | None | Full | Full | Per-release |
| Single resolve path (H) | Yes | Yes | Yes (via symlink) | Yes |
| Multi-machine sync (M) | Manual copy | `git pull` | `git pull` | Reinstall |
| Reviewable changes (M) | No | Yes (commits/PRs) | Yes | Yes (PR + release) |
| Rollback (M) | No | `git revert` | `git revert` | Pin version |
| Setup simplicity (M) | Trivial | One `git init` | Symlink + repo | Build/publish pipeline |
| Distribution to others (L) | None | Clone | Clone | Best (registry) |
| **Score** | Weakest | **Strongest for solo/small** | Strong, more moving parts | Heaviest |

## Analysis

### A — Plain dir
- **Pros:** zero setup; always present locally.
- **Cons:** no history, no rollback, no review, no sync. Best practices change
  silently with no audit trail — the opposite of what a rules system wants.

### B — Git repo in place *(verdict)*
- **Pros:** one `git init` upgrades A into a fully versioned, reviewable,
  syncable store with rollback — without changing the path the engine reads.
  Add a private remote and every machine `git pull`s the same best practices.
  Commits give an audit trail of *why* a practice changed.
- **Cons:** you must remember to commit (mitigated: `fux build` can auto-commit
  generated changes); a single repo couples all global rules together.

### C — Separate repo, symlinked
- **Pros:** lets global rules live inside an existing dotfiles repo; same
  versioning benefits as B.
- **Cons:** symlink is an extra moving part that breaks on some sync tools and
  on Windows without dev mode; more to explain in `fux init`. Worth it only if
  you already centralize config in one dotfiles repo.

### D — Published package
- **Pros:** best for distributing a *curated* best-practice set to many people
  or a team; explicit versioning and pinning.
- **Cons:** release-cycle friction for what should be a quick edit; overkill for
  personal/solo use; editing a rule shouldn't require a publish step.

## References

- Internal: [fux-plan.md §4–§5](fux-plan.md) — global layer, resolve path, layered resolution.
- Internal: [docs/conventions.md](conventions.md) — "every code change ships a doc update" rule that the global layer encodes.
- Internal: [docs/guardrails.md](guardrails.md) — "never commit `.env`/keys", the secret-hygiene constraint below.
- External: [Pro Git — Getting a Git Repository](https://git-scm.com/book/en/v2/Git-Basics-Getting-a-Git-Repository) — `git init` in place + remotes (accessed 2026-06-01).

## Additional things to look into

- **Secret hygiene:** global rules sync across machines — enforce "no secrets in
  global rules" (a `fux check` lint), since a synced/remote repo widens exposure.
- **Auto-commit ergonomics:** decide whether `fux build`/`fux check --fix`
  auto-commits global edits or leaves them staged for manual review.
- **Graduation trigger:** if rules need to split by audience (personal vs
  team-shared), revisit C (symlink a dotfiles repo) or D (publish a pack).
- **Pack overlap:** clarify the boundary between the global layer and opt-in
  rule packs ([fux-plan.md §5](fux-plan.md)) so a rule isn't defined in both.
- Not tested: behavior of the symlink option (C) under iCloud/Dropbox sync and on Windows.
