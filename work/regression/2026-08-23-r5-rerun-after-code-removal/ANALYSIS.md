# R5 re-run — analysis

## The finding in one line

**A change made for a completely different reason deleted most of the problem
Phase 3 was designed to solve**, and nobody would have noticed without
re-measuring.

`code` was removed in Phase 1 to make ingest faster and the index smaller. It
happened to be 91 % of what the post-commit hook was paying on every run. The
delta-hook design in doc 05 of the ideal set attributes R5's 44 s to "two
O(corpus) passes — the source walk + hash of every file, and re-resolving every
edge." Those passes are still there and still O(corpus); they are simply not
expensive once the embedding is gone.

## Why this is worth a filed verdict rather than a silent skip

Phase 3 is written into W-76 as a build step, and W-76's own row calls it
*"now the only fix for R5"*. A later session reading that would build it. The
verdict has to be recorded where that session will look, with the number that
justifies it, or the work happens anyway.

## What this does NOT say

- It does not say the delta design is wrong. It says it is **not yet earning
  its complexity**, at a size the project targets.
- It does not retract R5. R5 measured a real 44.4 s on the engine of
  2026-08-20.
- It does not clear the hook end to end. This times `run()`, not
  `post-commit` — process start-up and the detached-runner handoff are
  excluded and unmeasured.

## The trap this verdict sets for Phase 7

Phase 7 commits per-chunk `int8` vectors. That is an embedding pass again, at
roughly **9.8 chunks per document** against the one-per-document pass Phase 1
removed. If it lands and nobody re-runs this harness, the hook silently returns
to R5's territory and the reopen condition never fires because nobody is
looking at it.

**The report names this explicitly.** It is the highest-value sentence in the
run, and it is the one most likely to be skipped.
