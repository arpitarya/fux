# W-25 — M5: maintenance

**Status:** OPEN
**Blocked by:** W-23, W-24
**Spec:** this file — see §Scope below (migrated from the retired `PLAN.md`, 2026-08-18)
**Closes with:** **`ADR-MAINTENANCE`** (reserved) · predictions **R5**, **R6**. **Reserved by NAME, never by number** — a number is a filename ordinal assigned when the record is written (Arpit, 2026-08-19, closing W-33).
**Model:** **Sonnet** — well-specified against two measured DoDs.

## Goal

Make the index maintain itself in a real repository: incremental on
commit, conflict-free on merge, and honest about what it stores.

## What lands

- **Hooks** — `post-commit` / `post-merge` / `post-checkout` → delta
  ingest, which is a re-emit of changed lines only, not a rebuild.
- **A line-wise merge driver** via `.gitattributes`: last-writer-wins on
  `(ver, sha)`. Machine planes never conflict; snapshot-mode human files
  conflict normally **on purpose** — that asymmetry is the design, not a
  gap.
- **`meta: hashed` enforced at write time** for every non-git source — the
  council's ACL ruling, as code rather than as documentation.

## Definition of done

- [ ] **R5**: a 20-doc commit re-indexes in **< 1 s** via the hook.
- [ ] **R6**: the three-tier merge harness shows machine planes
      conflict-free and human conflicts preserved.
- [ ] Hashed-meta enforcement is unbypassable from config for a non-git
      source, and has a test that tries to bypass it.
- [ ] `ADR-MAINTENANCE` written and accepted.

## Hazards

- A hook that fails must never leave a half-written committed shard. Write
  through a temp file and rename, or the determinism law dies quietly.
- The merge driver is the piece a user cannot debug when it goes wrong.
  Its failure mode must be "refuse and leave both sides", never "silently
  pick one".

---

## Scope — M5 — maintenance

*Migrated verbatim from `PLAN.md` §M5 on 2026-08-18, when
that document was archived. **This file is now the spec**; there is no other.*

Hooks (post-commit/merge/checkout → delta ingest = re-emit changed lines);
merge driver via gitattributes: line-wise LWW on `(ver, sha)`, machine planes
never conflict, snapshot-mode human files conflict normally **on purpose**;
`meta: hashed` enforced at write time for every non-git source (the council's
ACL ruling, as code not docs).

**DoD:** R5 (20-doc commit < 1 s); R6 three-tier merge harness; a record for
the maintenance contract.
