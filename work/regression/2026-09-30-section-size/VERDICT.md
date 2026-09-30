---
type: Verdict
name: W-236-SECTION-SIZE
description: "W-236 Part A step 2: PASS on both external commit limits at rung-10000 (largest file 168 451 B against a 50 MiB limit; whole index 50.4 MB against 1 GB). No record grades the +98.4 % growth, so it goes to Arpit as a number, not as a verdict."
verdict: PASS
prediction: W-236-SECTION-SIZE
pre_registration: work/regression/2026-09-30-section-size/PRE-REGISTRATION.md
run: 2026-09-30-section-size
item: W-236
filed: 2026-09-30
classification: blind
---

# VERDICT: PASS. The section plane can be committed at 10 000 documents

Judged against [PRE-REGISTRATION.md](PRE-REGISTRATION.md) §2. No threshold
moved.

| gate | FAIL if | measured at rung-10000 | holds |
|---|---|---|---|
| H1 | any committed file > 50 MiB | 168 451 B | ✅ |
| H2 | doc plane + section plane > 1 GB | 50 351 784 B | ✅ |

**What this verdict does NOT say.** It does not say that doubling the index is
acceptable. No record sets a growth number: SR-WORK-SCALE judges *holds up at
10 000* by reasoning, and SR-INDEX-LIFECYCLE says index size is measured, never
gated. So **+98.4 %** (+79.6 % after zlib) goes to Arpit as a measured cost of
U2. The compare doc names U3 as the fallback if the size fails, but U3 would
not be much smaller ([ANALYSIS.md](ANALYSIS.md) §3).
