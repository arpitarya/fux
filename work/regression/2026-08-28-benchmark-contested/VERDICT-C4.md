---
type: Verdict
name: VERDICT-C4
threshold: C4
prediction: C4
description: "C4 — heading contest, the pre-registered negative control. Returned its predicted null with ZERO headroom, so it did not discharge its purpose."
verdict: INCONCLUSIVE
pre_registration: work/benchmark/PRE-REGISTRATION-CONTESTED.md
---

# C4 — the negative control saturated. **Inconclusive, not Pass.**

**Bar (frozen):** predicted NO DETECTED CHANGE; a delta here would mean the
instrument was measuring something other than the field it names.
**Measured:** 0 discordant of 40, `p = 1.0` — **and 100 % in both arms, with
zero queries of headroom.**

🔴 **It returned the right answer for the wrong reason.** A control exists to be
able to fail. This one could not have produced a delta whatever the engines did,
which is **the exact failure mode this run was built to expose, reappearing
inside the instrument built to expose it.** Recording it as a pass would have
been the easiest and least honest line available.

**Consequence:** C1 and C3 rest on the generator's `--selftest` assertions rather
than on a live, discharged control.

**The fix:** a control with headroom by construction — e.g. a heading contest
whose distractors are *also* heading-matched, so the contest is genuinely close.
**The C6 headroom column is what caught this**, which is the strongest argument
available that the column belongs in every future paired run.
