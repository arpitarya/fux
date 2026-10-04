---
type: Handoff
name: W-250
description: "Register the fux merge driver in this repository by running `fux hooks` here and committing `.gitattributes` — SR-MERGE-DRIVER's own 'nobody has' sentence, closed. Ratified 2026-10-03 by delegation, NOT built."
item: W-250
filed: 2026-10-03
ball: agent
---

# W-250 — run `fux hooks` in the fux repository

**Model:** Claude Code, **Sonnet** — a hands-on action with a written outcome.

**From** backlog B-037. [SR-MERGE-DRIVER](../../records/0130_merge-driver.md)
Consequences: *"This repository does not have the driver registered …
dogfooding the driver means running `fux hooks` here, which nobody has."*
No ruling is needed — SR-MAINTENANCE 5a: hooks touch no network.

## Definition of done

1. `fux hooks` run at this repo's root; `.gitattributes` committed with the
   `.fux/index/**` driver lines it writes; the local `.git/config` registration
   is **not** committed (it never is) — `MACHINE.md` gains the one-line
   per-clone step.
2. The driver is exercised once: two branches each re-ingest, merge, and the
   index resolves without a hand edit. Filed under `work/regression/` as a
   one-paragraph capture.
3. SR-MERGE-DRIVER Consequences rewritten; `sr-hash` restamped.

## Hazards

- ✅ **`fux ingest` at this repo's root is safe again**: W-244 landed on 2026-10-04,
  and the walk prunes `work/golden/`. The merge exercise in DoD 2 still uses a
  scratch copy of the repo, never this tree.
- A concurrent session is active in this tree; `fux hooks` writes to `.git/`.
  Say so in the session before running it (SR-WORK-SESSION d12).
