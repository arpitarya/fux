---
type: Verdict
name: VERDICT-C6
threshold: C6
description: "C6 — the headroom disclosure. Reported, not tested: how many queries could have changed, per suite, per arm."
verdict: REPORTED
---

# C6 — headroom, declared beside power

| suite | N | arm A | B-core | B-tuned | ceiling in **both** | **could have changed** |
|---|---:|---:|---:|---:|---:|---:|
| contested `proximity` | 120 | 21.7 % | 21.7 % | 100 % | 26 / 120 | **94** |
| contested `path` | 60 | 0 % | 100 % | 0 % | 0 / 60 | **60** |
| contested `heading` | 40 | 100 % | 100 % | 100 % | 40 / 40 | 🔴 **0** |
| marker `hit@5` | 120 | 100 % | 100 % | 100 % | 120 / 120 | 🔴 **0** |

**Two of four suites cannot detect anything at any sample size, and this table
says so before a p-value is quoted.** That is the 2026-08-28 recommendation R2
made mechanical, and it immediately earned its place by catching a saturated
control (C4) inside this very run.

**Standing obligation this establishes:** a paired run states, for every
endpoint, *what the current score is and how many queries could change* — beside
the power figure, never instead of it. A suite at 100 % has a maximum detectable
effect of zero whatever `N` says.
