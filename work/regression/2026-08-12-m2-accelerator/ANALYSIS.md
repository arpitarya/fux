# Analysis — M2: what the run diagnosed, and what it earns

## 1 · R3 passed, and the margin is the interesting part

**Nothing to improve in the accelerator's latency.** 27.2 ms against a 150 ms
bar is not a near miss that needs tuning; it is 5.5× headroom on the
population the threshold was written for.

The improvement this earns is **not** further optimization. It is the
opposite: **T2 (M6) must not be pre-built.** The compare doc scoped mmap
segments as the escape hatch for a JSONL parse tax worse than modelled. At
8,870 documents the tax is 27 ms. The tripwire did not fire, so the escape
stays unbuilt — and M6 should re-measure at 100k before assuming it will.

**Repro:** `python tools/differential/bench_r3.py --root ~/my_programs/fux-lab/2026-08-12-m2-r3`

## 2 · The corpus decides whether a safety test is a test

This is the finding worth carrying forward, and it is a direct echo of M1's.

M1 recorded: *an aggregate delta of zero over an untreated population is not
evidence* — top-128 pruning was a no-op on 97 % of documents, so a zero delta
measured nothing. M2 hit the same shape from the other side: on this repo's
124-document corpus, **the block bound was never load-bearing**, so a bound
replaced by a constant zero still produced byte-identical output. The
differential was green and proving nothing.

Two things fixed it, and both were needed:

1. **Sweep `top`.** At `top=5` the rarest query term already determines the
   answer; at `top=20` and `top=50` the bound decides. One line of harness
   configuration separated "green" from "green and meaningful".
2. **Run on a corpus where the mechanism engages.** At RFC scale, skipping
   halves worst-case p95 — the mechanism is exercised by the benchmark itself.

**The improvement:** every future safety mechanism in this engine gets a test
that *fails when the mechanism is disabled*. If disabling it changes nothing,
the test is measuring the corpus, not the code. M4's ARC cache carries the
same differential law and must carry this check with it.

**Repro:** replace `accel.block_bound` with `lambda *a: 0.0` and re-run
`tools/differential/run.py` at `--tops 5` (passes) and `--tops 20 50` (fails).

## 3 · Hybrid: the archive predicted this, in writing

The dense lane closed three named gaps and broke nine queries, five of them
the entire no-answer class. `INTERVIEW.md`'s "what a confident successor must
not clean up", item 5, states the mechanism outright: a binary prefilter
always has a nearest neighbour, so "No confident matches" stops being
reachable. The archived calibration had already measured that no score floor
separates noise (0.23–0.26 cosine) from a true rescue (0.34).

**The improvement is procedural, not technical:** the succession record
already contained the answer, and the implementation still had to be measured
to find it. Reading the archive's warnings *before* building a lane is cheaper
than grading it afterwards — but grading it afterwards is what caught it, so
**the graded corpus is the thing that must not be allowed to rot.**

**What this does not earn:** a floor, a threshold, or a tuned `DENSE_WIDTH`.
Archived ADR-0014 recorded that no `min_confidence` value clears both the
answerable and unanswerable gates on a pool-relative score. Inventing one here
would repeat a closed experiment.

**Repro:** `python tools/differential/playground_grade.py`

## 4 · Specific changes this run earns

| # | change | why | status |
|---|---|---|---|
| 1 | Correct `PLAN.md` §M2 and `W-22`'s class-3 list | `q008`/`q017` are not known failures; the DoD names queries that pass | **applied this change** |
| 2 | Keep hybrid default-off | net −6 on the graded corpus, and it breaks R2 | **applied** |
| 3 | Do not pre-build T2 | R3's tripwire did not fire | applied (scope held) |
| 4 | A source-exclusion mechanism | filing evidence into `docs/` contaminates the corpus | [W-45](../../open/W-45-source-exclusion.md), open |
| 5 | Re-measure R3 at 100k in M6 | this run says nothing about 100k; the size model is still a projection | owed by M6 |

## 5 · Unresolved

- **Absolute latency is machine-specific.** This ran on the device rather than
  in the cloud (handoff deviation, stated in the report). The margin is wide
  enough that the verdict is not in question; the *numbers* should not be
  quoted as portable.
- **Why skipping costs ~0.4 ms on typical queries** is understood in principle
  (threshold computation on queries that cannot skip) but not profiled. It is
  0.4 ms inside a 150 ms budget, so it buys nothing to chase now.
- **Whether the three closed gaps could be closed without the nine
  regressions** is open. It would need a lane that can decline — which is the
  no-answer problem archived ADR-0014 left unsolved, not a fusion parameter.
