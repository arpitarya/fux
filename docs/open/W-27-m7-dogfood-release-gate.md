# W-27 — M7: dogfood and the release gate

**Status:** OPEN
**Blocked by:** W-26
**Spec:** [`PLAN.md` §M7](../PLAN.md)
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
