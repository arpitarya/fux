---
type: Pre-registration
name: node-graph-speed
description: "W-259 DoD 3 and 4, frozen before any timing: (a) Node find/ask wall time with the graph.json read against the forced rebuild, at the v7 copies of rung-01000 and rung-10000, 12 fixed queries x 9 interleaved repeats, gain = median saving >= 10% with the read faster in >= 10 of 12 cells; (b) one graph build per Node process, reused across that process's comparisons, against N processes, W-243 step 1's bench on this repo, bar >= 5.0x on the median of 5 trials. W-243 step 1 reopens on whichever of the two clears its bar in a configuration the arm can run, which only (b) can be. Otherwise it stays STOP. informed."
run: 2026-10-04-node-graph-speed
item: W-259
frozen: 2026-10-04
classification: informed
---

# W-259 — speed, pre-registered before any number

**Frozen 2026-10-04, after the read was built and shown byte-identical
([`2026-10-04-node-graph-read`](../2026-10-04-node-graph-read/report.md)) and
before any timing of it was taken.** It is a latency run, not a ranking run: no
golden question, key or score is read, and nothing is scored per query. It is
labelled **`informed`** because the session that built the read wrote this
file and will run it. It also already knows the read's expected size, which is
W-242's ~55 ms of a 383 ms query, measured through the Cowork VM mount. No
threshold below moves after the first measurement (SR-RS decision 10b). A
result this file did not anticipate goes to Arpit and is not re-interpreted by
whoever ran it.

**The instruments are phase 2's.** No script for (a) or (b) exists yet. Each one
is written to the spec below and committed **before its first run**, and it
writes every timing it takes.

---

## (a) Does the read make a Node query faster?

### Arms

The same code (the W-259 tree), the same corpus and a fresh plane in both arms.
The arms differ only in the environment:

| arm | environment | what the graph tier does |
|---|---|---|
| `read` | `FUX_GRAPH_REBUILD` unset | reads `.fux/runtime/graph.json` |
| `rebuild` | `FUX_GRAPH_REBUILD=1` | rebuilds the plane in memory, as before W-259 |

### Corpora

The v7 copies of fux-lab's `scratch/shared-runtime/rung-01000-v7` and
`rung-10000-v7`, made fresh by
[`migrate.sh`](../2026-10-04-node-graph-read/evidence/migrate.sh): `cp -R` into
a scratch directory, then `doctor --fix`, `ingest --full` and `build`.
`~/my_programs/fux-lab` is only read. **`accel.is_fresh` must be true before
and after each rung's block. A plane that went stale voids that block**, and the
block is re-run.

### Cells

Two verbs, each corpus's own `tune.toml` in force:

| verb | argv |
|---|---|
| find | `find Q --json --top 5` |
| ask | `ask Q --json --top 5 --band` |

Each rung uses **12 fixed queries**. They are the first twelve, by position, of
that rung's `find --json` rows in
`2026-10-04-node-graph-read/evidence/identity-<rung>.jsonl`, skipping any row
whose read arm did not open `graph.json`. Those are the queries with no result,
where the tier never runs. The list is fixed here and does not change:

- **rung-01000:** `owner`, `befor`, `check`, `dock`, `first`, `financ`, `7`,
  `15`, `more`, `zac-q7`, `00075`, `00215`
- **rung-10000:** `owner`, `site`, `time`, `list`, `21`, `record`, `longer`,
  `chain`, `zac-qa-40`, `0.4`, `00115`, `00255`

That gives 2 rungs × 2 verbs × 12 queries = **48 cells**.

### Repeats and interleaving (SR-WORK-SESSION decision 12)

- One **discarded** warm-up process per cell per arm, before anything is timed.
- Then **9 repeats**. In repeat `r`, the cells run in their fixed order, and
  within each cell the two arms run back to back. The order is `read` then
  `rebuild` when `r` is odd and `rebuild` then `read` when `r` is even (ABBA),
  so the machine's drift lands on both arms.
- The endpoint is **the wall time of one whole `node node/fux.mjs …` process**:
  `time.perf_counter()` around `subprocess.run`, with the corpus as `cwd`.
- Every timing row carries the cell, the arm, the repeat, the return code, the
  stdout sha256 and `os.getloadavg()`.
- **A rung × verb block in which any cell ran at a 1-minute load above 6 is
  re-run once.** Both runs are filed, and the decision uses the re-run.
- **Identity gate:** within a cell, every `read` stdout must equal every
  `rebuild` stdout, with return code 0. One differing byte **voids (a)** and is
  a defect in the read, not a timing result.

### The statistic

For each cell `c`, let `m_read(c)` and `m_rebuild(c)` be the medians of its 9
timed repeats in each arm.

- `saving(c) = (m_rebuild(c) − m_read(c)) / m_rebuild(c)`
- For each rung × verb: **`S`** is the median of `saving(c)` over its 12 cells,
  and **`W`** is the number of those cells where `m_read(c) < m_rebuild(c)`.

### What counts, for each rung × verb (fixed now)

| outcome | rule |
|---|---|
| **gain** | `S ≥ 0.10` **and** `W ≥ 10` of 12 |
| **loss** | `S ≤ −0.05` **and** `W ≤ 2` of 12, so the read is slower in at least 10 cells |
| **null** | anything else |

**Why 10 %:** the item's own estimate is ~55 of 383 ms (14 %), and that was
measured on this repo through a VM mount, which inflates I/O. Ten percent is
below the estimate, so that a real but smaller effect can still count. It is
above anything a single noisy cell could produce once 9 interleaved repeats are
reduced to medians and 12 cells to a median, with a sign count on top.

**Fork A's speed verdict is rung-10000's.** It is a gain only if both `find`
and `ask` are a gain there. rung-01000 is reported by the same rule and decides
nothing. Its graph has 181 edges against rung-10000's 1 081, as counted while
writing this file from the plane the identity run built. That leaves little
rebuild to save, which is a reason to report it, not to judge by it.

---

## (b) One graph build per Node process — the alternative that CAN help CI

The differential arm may never take the read (W-259 point 2; SR-T1-ACCELERATOR
decision 19). So (a) cannot make CI faster however it comes out. What the arm
CAN use is to rebuild the plane **once per Node process** and reuse it across
that process's comparisons, with the switch still set, so that each process
still compares two builders.

### The harness change it is

W-243 step 1's driver is a script under `tools/differential/` that starts **one**
Node process per arm pass and feeds it comparisons as JSON lines, as
`compare_mcp` already drives a stdio session. **Plus** a per-process memo of the
rebuilt plane, keyed like `verbs/mcp.mjs::Resident`: on `stamp.json` and every
shard's size and mtime, and dropped when either moves. That keeps a long-lived
process from answering from an index that has since been rewritten (W-242's one
design constraint).

⚠ **Timing it needs a prototype**, because `compose.tiers` has no way to accept
a plane made earlier. The prototype is **phase 2's**. It must not ship as the
driver without its own item step and records (W-243 step 1's constraint on the
verb seam still applies). This file fixes only how it is timed.

### Arms (all with `FUX_GRAPH_REBUILD=1`)

| arm | what runs |
|---|---|
| `n-proc` | 24 `node node/fux.mjs` processes, one per comparison. This is the arm today |
| `one-proc-rebuild` | one process, calling the verb handlers directly, rebuilding the plane for each comparison. This is W-243's existing spike, `2026-09-30-ci-arm-batching/evidence/one-process.mjs`, run unchanged |
| `one-proc-once` | the same single process, with the plane rebuilt **once** and reused for every comparison. This is the prototype |

### Cells and corpus

These are W-243's spike jobs, unchanged, so the bar means what it meant: 6
queries (`rollback`, `ranking`, `confidence band`, `graph plane`, `BM25F`,
`node read plane`) × tops {1, 20} × {find, ask}, with `--no-tune` and
`ask --band`. That is **24 comparisons**.

The deciding corpus is **this repo, as a `git archive HEAD` snapshot plus
`fux build` in a scratch directory**. It is not the live tree, whose index
another session may be rewriting. The two rung copies above are run the same
way, reported, and decide nothing.

### Trials, interleaving and the statistic

- **5 trials.** Trial `t` runs the three arms in rotated order, starting at arm
  `t mod 3`, so no arm always runs first.
- Each arm's time is the wall time of the whole arm:
  `time.perf_counter()` around the N processes, or around the one process.
- Each trial records `ratio = n-proc / one-proc-once`, and reports
  `n-proc / one-proc-rebuild` beside it. The second ratio says how much of the
  gain is the plane and how much is process start-up.
- **The statistic is the median of the 5 trial ratios.**
- The 1-minute load is recorded per trial. A trial run at a load above 6 is
  re-run, both are filed, and the re-run counts.
- **Identity gate:** `one-proc-once` must print, for each comparison, the bytes
  `n-proc` printed. The prototype captures stdout per comparison instead of
  swallowing it. One differing byte **voids (b)** and makes the prototype a
  defect.

### The bar — W-243 step 1's, quoted

> **Spike first, before building:** time N comparisons as N processes against
> one process, on this repo, natively. Record it in a `work/regression/` run.
> If one process is not at least ~5× faster per comparison after W-242's
> landed tiers, stop and report — the step is not worth its complexity.

— [W-243](../../open/W-243-ci-two-minutes.md), §Step 1.

**Frozen as: the median trial ratio `n-proc / one-proc-once` ≥ 5.0.** The "~"
is resolved here to its strict reading, on purpose, so that a 4.6 cannot be
argued up after it is seen.

### What reopens W-243 step 1

**W-243 step 1 reopens on whichever of (a) or (b) clears ~5x in a
configuration the differential arm can run. Otherwise it stays STOP.**

- **(b) is eligible.** If its median ratio is ≥ 5.0, step 1 reopens with (b)'s
  driver as its design. If it is below 5.0, step 1 stays STOP.
- **(a) is not eligible, by construction:** the arm forbids the read. (a) is
  still timed in W-243's shape, the same 24 comparisons with the switch unset,
  as `n-proc` against `one-proc` (the existing spike, with the read). Its ratio
  is reported for the record. **If (a) clears 5.0 and (b) does not, step 1
  stays STOP and the result goes to Arpit.** Using it would mean letting the
  arm read `graph.json`, which N2 forbids and only Arpit can reopen.

---

## (c) What a null or a negative result means

- **(a) null at rung-10000:** the per-query rebuild was not where a native Node
  query spends its time at 10 000 documents. **The read stays.** Its output is
  identical, it is the ruled behaviour, and removing it would be a new ruling.
  The null is recorded in the compare doc's Fork A row and goes to Arpit. It is
  not a reopen-trigger by itself.
- **(a) loss at rung-10000 for either verb:** parsing `graph.json` costs more
  than rebuilding the plane. This **is a reopen-trigger for Fork A**, filed to
  Arpit with the numbers. Neither the read nor its threshold is changed by the
  session that finds it.
- **(a) gain at rung-01000 but not at rung-10000, or the reverse:** reported
  per rung. The verdict is rung-10000's, as fixed above.
- **(b) below 5.0:** W-243 step 1 **stays STOP**. W-259 offers no further
  lever, and the next trigger is whatever makes the scan itself cheaper. Both
  ratios are filed, so the share that is start-up and the share that is the
  plane can be read without re-running anything.
- **Either gate voided** (a stdout byte differs): there is no timing verdict. A
  void of (a) is a defect in the shipped read, and it goes to Arpit before
  anything else. A void of (b) is a defect in the prototype only.

**Every number this run produces is `informed`.** No golden material is
involved. The label records that the builder of the change is also the one
measuring it.
