---
type: Compare Doc
title: "Keeping the index current — hooks, CI, or a watcher"
status: proposed
filed: 2026-08-21
laws_bracketed: []
---

# Keeping the index current — hooks, CI, or a watcher

## What exists, and what R5 measured

- `fux hooks` installs `post-commit` / `post-merge` / `post-checkout`; each
  runs a full `fux ingest` (delta-aware on extraction, **not** on the walk or
  the edge pass).
- **R5 FAIL:** a 20-doc commit re-indexes in 0.65 s at 1k docs, **44.4 s at
  100k**. Attribution: two O(corpus) passes — the source walk + hash of every
  file, and re-resolving every edge.

The failure is not "hooks are the wrong mechanism"; it is **"the hook does
O(corpus) work for an O(delta) event."**

## Options

| | A · hooks, full ingest (today) | B · hooks, true delta via `git diff` | C · CI builds on push, clone fetches a ref (doc 01-C) | D · background watcher daemon (fswatch + incremental) |
|---|---|---|---|---|
| work per commit | O(corpus) | **O(changed files + affected edges)** | 0 locally; O(delta) in CI | O(changed files), continuous |
| 100k-doc, 20-file commit | 44 s (measured) | est. < 1 s (20 files + reverse-edge lookup) | 0 local | < 1 s |
| uncommitted edits searchable? | no | no | no | **yes** |
| moving parts | git hooks | git hooks | CI job + custom refs | a daemon (lifecycle, crashes, Windows service) |
| multi-branch | re-ingests on every checkout | re-ingests only the diff between checkouts | one ref per tree sha, instant switch | re-index on checkout |
| what blocks a commit | nothing (best-effort) | nothing | nothing | nothing |
| prior art | — | — | Cursor anchors the index at a git commit and overlays local edits ([Cursor](https://cursor.com/blog/fast-regex-search)); Zoekt indexes per commit with branch bitmasks ([Zoekt](https://github.com/sourcegraph/zoekt/blob/main/doc/design.md)) | Cursor's local overlay |

## The delta design (B), concretely

1. **Walk only the diff.** `post-commit`: `git diff --name-only HEAD~1 HEAD`;
   `post-merge`/`post-checkout`: `git diff --name-only <old> <new>` (both
   shas are hook arguments). Apply the source-dir/type filters to that list.
2. **Edges by reverse index.** Maintain `target → {referencing doc ids}` in
   the derived plane. On a delta, re-resolve only: edges *from* changed docs,
   and edges *to* any changed/added/deleted target. Everything else is
   carried forward.
3. **Statistics incrementally.** `n`, `total_wlen`, and `df` per term are
   additive; update in place. (The accelerator recomputes block tables for
   touched terms only.)
4. **Safety net.** A `fux doctor --verify-delta` that does a full ingest and
   asserts equality; run it in CI nightly. The differential-law pattern the
   repo already trusts, applied to maintenance.

## Debate

- **B vs C:** not exclusive. B makes a solo developer's repo instantly
  current; C makes a team's clone instantly current without anyone's laptop
  paying. Together they cover both, and C reuses B's delta code in CI.
- **D** is the only option that answers the question agents actually ask —
  *"what did I just write?"* — but that is a different product (Cursor's
  local overlay). It is a clean follow-on once B exists: the overlay is a
  delta over the committed anchor.

## Proposed verdict

**B immediately; C when the index moves off the working tree (doc 01).**
R5's 44 s is a design bug, not a ceiling; re-run R5 after B and expect it to
pass by two orders of magnitude.

## Reopen trigger

Reopen for D if a measured agent workflow shows > 20 % of questions target
documents changed since the last commit.
