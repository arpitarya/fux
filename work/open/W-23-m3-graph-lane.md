# W-23 — M3: the graph lane

**Status:** OPEN
**Blocked by:** — (W-22 was M2, the T1 accelerator; it **shipped as `v0.32.0`** on 2026-08-12. Stale blocker cleared 2026-08-19)
**Spec:** this file — see §Scope below (migrated from the retired `PLAN.md`, 2026-08-18)
**Closes with:** **`ADR-GRAPH`** (reserved). **Reserved by NAME, never by number** — a number is a filename ordinal assigned when the record is written (Arpit, 2026-08-19, closing W-33).
**Model:** **Sonnet** — the port is well-specified and the archived
relational eval is the test that catches a bad one.

## Goal

Turn the `ref`/`tag`/`code` edges M1 already extracts into a queryable
lane: `explain`, `graph`, `path`.

## What lands

- Edge extraction ported from `archive/v0.26/` **with its tests**.
- `community` assignment — deterministic label-propagation or a
  Leiden-class algorithm with a **fixed seed**; the choice is `ADR-GRAPH`'s
  decision, not an implementation detail to be made silently.
- PPR-lite (ported).
- `explain` / `graph` / `path` verbs.

## Definition of done

- [ ] The **archived relational eval passes** on the new kernel.
- [ ] Community assignment is byte-deterministic across two runs and two
      machines (the R1 discipline, applied to a new artifact).
- [ ] `ADR-GRAPH` written and accepted, carrying the algorithm choice and a
      reference for it.

## Named acceptance targets (from `fux-playground`)

The **supersession and near-duplicate** gaps — `q005`, `q009`, `q011`,
`q015` — are this lane's targets. They are precisely the queries no amount
of term statistics can answer, which is the argument for the lane existing.
Report the XPASS count.

## Hazards

- A non-deterministic community algorithm silently violates the
  determinism law and will not be caught by a ranking test. Seed it, then
  assert the assignment bytes.
- M3 and M4 may interleave after M2; they must not share a commit.

---

## Scope — M3 — the graph lane

*Migrated verbatim from `PLAN.md` §M3 on 2026-08-18, when
that document was archived. **This file is now the spec**; there is no other.*

Edge extraction ported; `community` assignment (deterministic
label-propagation or Leiden-class with fixed seed — decided in the graph
lane's own record); PPR-lite; `explain`/`graph`/`path` verbs.

**DoD:** the archived relational eval passes on the new kernel, plus a record
for the community-assignment choice.

**Also:** the playground's supersession and near-duplicate gaps (`q005`,
`q009`, `q011`, `q015`) are named acceptance targets for this lane — they are
precisely the queries no amount of term statistics can answer.
