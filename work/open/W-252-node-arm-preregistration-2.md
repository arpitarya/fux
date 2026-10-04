---
type: Handoff
name: W-252
description: "A superseding pre-registration for the Node differential arm on lab golden rungs, so the arm can be called green — its live pre-registration names fux-playground, voided as an instrument. Paperwork plus one rerun. Ratified 2026-10-03 by delegation, NOT built."
item: W-252
filed: 2026-10-03
ball: agent
---

# W-252 — the Node arm's pre-registration, on data that counts

**Model:** Claude Code, **Sonnet** — the endpoint is zero and the harness exists.

**From** backlog B-125. [SR-NODE-SEARCH](../../records/0153_node-search.md)
Consequences: *"cannot be called green yet: its pre-registration names
`fux-playground`, voided as an instrument."* Parity has since been measured
three times — 0/750 discordant (2026-09-12), 60/60 identical (2026-09-16),
0/225 (2026-09-29) — on lab rungs, under a pre-registration that names the
wrong corpus. The number is in hand; the paper is not.

## Definition of done

1. `work/regression/<date>-node-arm-2/PRE-REGISTRATION-NODE-2.md`, frozen and
   committed alone: rung-01000 and rung-10000 in fux-lab (L9 — never the
   playground); every verb the arm covers; `fux build` run in the arm;
   endpoint **0 discordant of N** and identical graph digests. No key is read.
2. `tools/differential/node_arm.py` rerun under it; `VERDICT.md` filed.
3. SR-NODE-SEARCH Consequences rewritten — the arm is green under a
   pre-registration that names its corpus; `sr-hash` restamped.

## Hazards

- A W-242 Tier 2 build in flight changes what Node reads; **run after Tier 2
  lands or say which tier the arm ran against** in the pre-registration.
- Every number here is `informed` (same model family built both readers); the
  endpoint is parity, not quality, so that costs nothing.
