# W-73 — a non-default score weight breaks the accelerator's pruning bound

**Status:** OPEN
**Lane:** `agent` — **fork 9 ruled 2026-08-22 (Arpit): both directions allowed, the consumer chooses, fux states the cost.** Both accelerator changes are therefore in scope; the demotion-only shortcut is off the table.
**Filed:** 2026-08-22 (Cowork), while researching per-source priority
**Spec:** this file · design context in
[`../proposals/tune-file-and-source-priority.md`](../proposals/tune-file-and-source-priority.md) §6
**Closes with:** **[ADR-TUNE](../../docs/adr/0038_tuning.md) decision 12** (written 2026-08-22; its
**veto condition 2 is FIRING** and names this item) plus an **`ADR-T1-ACCELERATOR`**
amendment, since that record owns the bound
**Model:** **Opus** — it is a correctness argument about an invariant, and a
wrong call here is silent. The *edit* is small; the reasoning is not.

## The claim

**The differential law holds only at `archived_weight == 1.0`, and nothing
says so.**

`config.py` accepts any non-negative float. At any other value,
`fux ask --fast` and `fux ask --scan` can return different documents.

## Why

`rank()` applies the weight **after** the accelerator has already truncated the
candidate set:

- `block_bound()` is computed from `mx` / `mnw` — **unweighted**
- `_kth_score()` computes `theta` from candidate scores — **unweighted**
- `rank()` multiplies by `archived_weight` — **afterwards**

Block skipping is safe on one property, and only one:

```
∀d : S(d) ≤ UB(d)      then      UB(d) < theta  ⟹  d cannot enter the top-k
```

With `S'(d) = w(d)·S(d)`, `theta` is drawn from `S'` but the skip test still
uses `UB`. Safety then needs `w(d)·S(d) ≤ UB(d)` — and `UB` is a maximum that
some document actually attains, so it is **tight**. The only condition that
holds independent of corpus and query is `sup_d w(d) ≤ 1`, *with `theta`
computed on the weighted scores*. Neither holds today.

**Both directions diverge:**

- **`w > 1`** — an archived document with bound `0.5` is skipped at
  `theta = 0.8`; the scan scores it `1.0` and ranks it in the top-k. The
  accelerator returns a wrong list.
- **`w < 1`** — demoting the current top-k lowers the real threshold, so a
  document in a block that was never opened should now enter. It was pruned on
  a `theta` that no longer applies.

## Why it was not caught

- `rank()`'s docstring states the guarantee it *actually* makes — *"at the
  shipped default (`1.0`) the multiply is skipped outright"* — and the test it
  names (`test_the_marker_does_not_move_the_ranking`) asserts exactly that
  default.
- `tools/differential/` never varies the weight, so the "thousands of
  comparisons" all ran at `1.0`.
- **W-44's own row claims the opposite** — *"applied in the one shared `rank()`
  so the differential law carries it down both the scan and accelerator paths
  for free"*. It carries at the default. The word doing the damage is *free*.

## Definition of done

- [ ] `theta` in `_kth_score()` is computed on **weighted** scores.
- [ ] The deferred-terms ceiling in `_cannot_reach()` is multiplied by
      `w_max` — the largest weight the configuration can produce.
- [ ] `tools/differential/` sweeps weights, not just the default, and the
      sweep includes an **adversarial** case: the largest weight on the
      **lowest-impact document in a block**. That is the one configuration
      separating a correct bound from a subtly wrong one, and uniform random
      sampling will essentially never generate it.
- [ ] A prunability measurement is filed under `regression/` with a prediction
      id and a frozen pre-registration (ADR-RS), at or below 10 000 documents.
      **R3's headroom is the budget**: warm p95 27.2 ms against a 150 ms bar.
- [ ] `ADR-T1-ACCELERATOR` gains the weighted-bound rule and a veto condition
      that fires if a weight can reach the scorer without reaching the bound.
- [ ] `ADR-RANKING` states the legal weight range and where it is enforced.

## Options, if the fix is judged too expensive

Ranked in [the proposal](../proposals/tune-file-and-source-priority.md) §6.3.
The cheap fallback is **demotion-only by contract** — validate `w ∈ (0, 1]` at
load. ⚠ **It is cheaper, not free**: it removes the need to scale the ceiling,
but the weighted `theta` is still required, because demoting the current top-k
lowers the real threshold. And promotion and demotion are the **same ranking**
(`docs/=1.5, rest=1.0` ≡ `docs/=1.0, rest=0.667`), so demotion-only buys no
pruning headroom either — what costs pruning is the **spread**, not the
direction. What it does cost is that *"prefer `docs/`"* must be written as
*"demote the other nine"*, and every source added later arrives at **maximum
priority** by default. See the proposal's §6.4.

## Hazards

- **The bug is silent, data-dependent and non-local.** No exception, no short
  read, no diagnostic — just a missing document. Whether it fires depends on
  the trajectory of `theta`, which depends on block boundaries and on `top`.
  The same query at `--top 5` and `--top 10` can differ in whether it appears.
- **Do not "fix" it by widening the candidate set.** Retrieve-wide-then-rescore
  makes results a function of a window size rather than of the index — which is
  the differential law traded away for convenience.
- **Do not normalise weights so `max = 1`.** It is algebraically the same as
  scaling the bound, and it moves the constant onto **displayed scores**.
