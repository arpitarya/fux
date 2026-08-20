# W-27 — M7: dogfood and the release gate

**Status:** OPEN
**Blocked by:** W-26
**Spec:** this file — see §Scope below (migrated from the retired `PLAN.md`, 2026-08-18)
**Closes with:** — (a release, not an ADR)
**Model:** **Sonnet** — docs and fixes against real usage.

## Goal

Fux answers real questions daily, for **two weeks**, in the `fux` repo and
in Anton (AlphaForge), and Arpit ships a release he has actually been
using.

## What lands

- Two weeks of daily use in both repos, with the friction written down as
  it happens rather than reconstructed at the end.
- `DOGFOOD.md` refreshed from that record.
- `README.md` becomes a real front door rather than a status board.
- `CHANGELOG.md` current.

## Definition of done

- [ ] Two weeks of real daily use in both repos, logged.
- [ ] **Arpit ships a release he has been using himself.** Nobody else can
      sign this box.

## Hazards

- **Launch work (product-gtm) starts only after this gate.** Writing launch
  copy for something not yet dogfooded is the failure this gate exists to
  prevent.
- Anton is a *convenient small testbed*, not the priority filter. The
  design point is a very large-scale corporate mega-project; friction found
  only in Anton must be judged against that, not shipped because it is
  easy.

---

## Scope — M7 — dogfood & release gate

*Migrated verbatim from `PLAN.md` §M7 on 2026-08-18, when
that document was archived. **This file is now the spec**; there is no other.*

Fux answering real questions daily in the fux and Anton repos for two weeks;
`DOGFOOD.md` refreshed; README becomes a real front door; CHANGELOG current.
Launch work starts only after this gate.

**DoD:** Arpit ships a release he has been using himself.
