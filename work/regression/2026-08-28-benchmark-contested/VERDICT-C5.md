---
type: Verdict
name: VERDICT-C5
threshold: C5
prediction: C5
description: "C5 — the null control and halt gate. Arm A twice on one corpus; ruled BEFORE any A-vs-B number existed."
verdict: PASS
pre_registration: work/benchmark/PRE-REGISTRATION-CONTESTED.md
---

# C5 — the halt gate. **Pass.** Run first.

**Bar (frozen):** discordant count **0**, or halt.
**Measured:** arm A twice on the same corpus — **380 of 380 substantive rows
identical** (every field but wall-clock and the arm stamp). Ruled before any
A-vs-B number was produced.

⚠ **A correction to the method, not a result.** The pre-registration described
this as *"A vs A′ on two seeds"*. Query ids are **positional**, so pairing seed
12 against seed 13 compares *different questions*; its discordant count is a
rate check, **not** a determinism check. **The determinism check is the
same-corpus repeat**, and that is what this verdict rules on. The cross-seed
comparison is reported descriptively: proximity 21.7 % vs 20.0 %, path 0 % vs
0 %, heading 100 % vs 100 %.

🔴 **The previous run's B9 carries the same weakness.** Its "0 discordant of 240"
across two seeds should be read as a rate check, not as evidence of determinism.
Its companion claim — 300/300 identical rows on one corpus — is the part that
does the work.
