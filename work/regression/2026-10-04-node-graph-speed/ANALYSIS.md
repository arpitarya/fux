---
type: Analysis
description: "Why the read saves ~15-19 ms at 10 000 documents and not 10 %, why one build per process cannot reach 5x, and what is left on a Node query."
run: 2026-10-04-node-graph-speed
item: W-259
---

# Analysis: the graph plane is no longer where a Node query spends its time

## (a) A real effect, below the bar

At rung-10000 the read wins **every** cell for both verbs (24 of 24), with a
nearly constant absolute saving of about **15–19 ms**. That saving is the
rebuild's cost: `graphRecords` skims `id` and `edges` from the shards the scan
already holds, then `buildPlane` and `assign` run over 1 081 edges. Because the
saving is roughly constant while query cost varies from 83 to 270 ms, the
relative saving runs from about 6 % to 19 %. Its median (9.48 % and 9.71 %)
falls just under the frozen 10 %. **A lower bar chosen after seeing this would
have passed it, and that is exactly the move SR-RS decision 10b forbids.** The
pre-registration predicted the risk in so many words: the item's 14 % estimate
came from this repo measured through a VM mount, and the rungs carry little
graph.

At rung-01000, with 181 edges, there is almost nothing to save (≈1 ms), and the
outcome is null by a wide margin.

**What the null says, and what it does not.** It does not say the read is
useless. The read is faster in every cell of the deciding rung, and its output
is identical. It says the per-query rebuild is about a tenth of a native Node
query at 10 000 documents, not more. **The scan is the cost.** W-242 already
measured that: Tier 1's plane takes a rung-10000 query from 0.13 s to 0.09 s,
but only under `--fast`.

## (b) Why one process cannot reach 5×

Each arm on the deciding corpus, as a median of trials:

- n-proc: ≈7.1 s, or 24 processes at ≈295 ms each
- one-proc-rebuild: ≈5.2 s, or ≈215 ms per comparison
- one-proc-once: ≈4.5 s, or ≈188 ms per comparison

One process saves start-up and module load, about 80 ms per comparison: that is
the 1.37×, matching W-243's 2026-10-03 re-run (1.21–1.43×). Building the plane
once saves about 27 ms more, which brings it to 1.575×. **The remaining
≈188 ms per comparison is the default-path scan** over this repo's 2 103
documents and 103 688 terms. Neither lever touches it, and the arm must compare
the scan because it is the default path. To reach 5×, a comparison would have
to cost about 59 ms in-process, under a third of what the scan alone costs
today.

The rung ratios are higher (4.38× and 2.02×) for a reason that disqualifies
them: W-243's six queries are about this repo, so on the rungs most of the 24
comparisons return nothing. The memo counted 8 that ran the tier and 16 that
did not, so those processes are mostly start-up. That is why the
pre-registration made this repo the deciding corpus.

## What this leaves for W-243 step 1

Nothing in W-259 reopens it. What would reopen it is a cheaper default-path
scan per comparison, or an arm that compares the accelerated path. The second
would be a ruling about what the arm covers, not a speed change. Both are
outside this item.
