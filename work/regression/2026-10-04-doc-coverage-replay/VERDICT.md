---
type: Verdict
name: PRE-REG-DOC-COVERAGE
description: "W-256 section 2 - INCONCLUSIVE (branch b): floor 0.80 meets the point criteria pooled (catch 12/21 = 0.571; 61 correct demoted vs a coin's 64.1) but p = 0.3545 > 0.00625 and it fails set-1 and set-3. doc_coverage_floor stays 0.0; the question goes to Arpit."
verdict: INCONCLUSIVE
prediction: PRE-REG-DOC-COVERAGE
pre_registration: work/regression/2026-10-04-doc-coverage-replay/PRE-REGISTRATION.md
run: 2026-10-04-doc-coverage-replay
item: W-256
filed: 2026-10-04
classification: informed
---

# VERDICT - INCONCLUSIVE

Ruled against the frozen text of PRE-REG-DOC-COVERAGE section 6:

> **INCONCLUSIVE** - any of: (a) fewer than 20 reachable unanswerables pooled
> ...; or (b) some floor meets (1) pooled but no floor meets (2) and (3)
> together - the direction is right and not distinguishable from chance, or it
> does not hold set by set. (b) is filed with the floor named, never promoted to
> PASS by a looser alpha, and goes to Arpit.

Branch (b): floor **0.80** meets (1) pooled (catch 12/21 = 0.571 >= 0.50; 61
correct demoted < 64.1 expected) and fails (2) (p = 0.3545 > 0.00625) and (3)
(set-1: 21 > 20.2; set-3: catch 1/3 and 19 > 18.5). No other floor meets (1).
Branch (a) did not apply (21 >= 20 reachable).

**Consequence:** `doc_coverage_floor` is not moved; no ruling is made by the
runner. For Arpit.
