---
type: Verdict
name: PRE-REG-LOOPBACK
description: "W-256 section 4 - PASS for B-102 loopback (14/14) and B-124 loopback (13/13), ruled separately as pre-registered; B-103 excluded, no verdict. Loopback only: it shows the mechanism is wired, not any real host's behaviour."
verdict: PASS
prediction: PRE-REG-LOOPBACK
pre_registration: work/regression/2026-10-04-loopback-network/PRE-REGISTRATION.md
run: 2026-10-04-loopback-network
item: W-256
filed: 2026-10-04
classification: informed
---

# VERDICT - PASS (B-102 loopback, B-124 loopback); B-103 not measured

Frozen text, section 6:

> **PASS (per scenario)** - every observation of that scenario holds. ... The
> scenarios are ruled separately: B-102 loopback can pass while B-124 loopback
> fails. B-103 carries no verdict (section 0).

- **B-102 loopback: PASS**, 14 of 14 observations (R1-R5) on the third attempt;
  the two earlier attempts failed for script defects disclosed in the report,
  not for an engine fact, and are filed.
- **B-124 loopback: PASS**, 13 of 13 (A1-A5, A5-fires) at the first attempt.
- **B-103: excluded**, no verdict; SR-MAINTENANCE 9c-i untouched.
