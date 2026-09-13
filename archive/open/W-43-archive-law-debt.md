# W-43 — Pay the archive-law debt and fix three stale claims

**Status:** OPEN · mechanical
**Blocked by:** —
**Law:** `CLAUDE.md` §"Archive implemented docs" — an executed
handoff/prompt pair moves to `docs/archive/` **in the same change** as its
ADR, stamped `status: implemented` with the ADR link. Active directories
hold *live* work only, so "what is in flight" is answerable by listing
them. That property is currently false.

## What is wrong

1. **Two executed pairs are still in `docs/handoff/`:**
   - `v0.30.0-m1-t0-slice-handoff.md` + `-prompt.md` — executed
     2026-08-10, closed by [ADR-0004](../adr/0004-index-format.md).
   - `v0.31.0-fux-playground-extraction-handoff.md` + `-prompt.md` —
     executed 2026-08-12, closed by [ADR-0012](../adr/0012-playground-sibling-repo.md).

   Both are marked **executed** in
   [`handoff/README.md`](../handoff/README.md) and neither was moved.

2. **`OPEN-WORK.md` claimed `docs/archive/` is gone.** It is not — it
   exists, has a README, and holds the v0.31.0 `.fux`-layout pair. The
   ruling that flattened things applied to the **v0.26 doc set** (now at
   root `archive/v0.26-docs/`), not to `docs/archive/`. *(Corrected in the
   2026-08-11 restructure; listed here because the same confusion is
   recorded in two other places.)*

3. **`docs/archive/README.md` and `handoff/README.md` disagree about where
   executed pairs go** — one says `docs/archive/`, the other says "the root
   archive". Root `archive/` holds *old builds* (`v0.26/`, `v0.1/`,
   `v0.30-rev1-planning/`); `docs/archive/` holds *completed doc
   artifacts*. Both readings are live in the tree today.

## Definition of done

- [ ] Both executed pairs moved to `docs/archive/`, stamped
      `status: implemented` + ADR link.
- [ ] `docs/archive/README.md` table gains their rows.
- [ ] `handoff/README.md` keeps only **live** pairs; its executed rows
      point at the new paths, and its "root archive" sentence is corrected
      to `docs/archive/`.
- [ ] `docs/archive/README.md`'s "reset discrepancy" paragraph updated —
      the v0.26 doc set's location was **resolved** on 2026-08-10 (root
      `archive/` is the only archive for old builds); it is no longer open.
- [ ] `DOC-REGISTRY.md` rows bumped for every file touched.
- [ ] No dangling links anywhere in `docs/` after the moves — check, do not
      assume.

## Why it matters

The archive law exists so that listing `docs/handoff/` answers "what is in
flight". Right now that listing returns four files for zero in-flight
milestones, which means the law has stopped being load-bearing — and a law
nobody notices breaking is worse than no law.
