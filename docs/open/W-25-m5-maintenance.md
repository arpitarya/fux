# W-25 — M5: maintenance

**Status:** OPEN
**Blocked by:** W-23, W-24
**Spec:** [`PLAN.md` §M5](../PLAN.md)
**Closes with:** ADR-0008 (reserved) · predictions **R5**, **R6**
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
- [ ] ADR-0008 written and accepted.

## Hazards

- A hook that fails must never leave a half-written committed shard. Write
  through a temp file and rename, or the determinism law dies quietly.
- The merge driver is the piece a user cannot debug when it goes wrong.
  Its failure mode must be "refuse and leave both sides", never "silently
  pick one".
