---
type: Handoff
name: W-243
description: "CI in ~2 minutes (Arpit, 2026-09-30). Built 2026-09-30, not yet run on main: FULL skips a cell whose verdict is known (step 2), Windows temp moved and the freshness gate batched (step 3). Step 1 STOPPED at 1.1-1.4x against a 5x bar and waits on W-242; step 4 keeps needs: at 38 jobs against a cap of 20."
item: W-243
filed: 2026-09-30
ball: agent
---

# W-243 — CI in about two minutes

**Status: built 2026-09-30 (Claude Code), uncommitted, and not yet run on
`main`.** Where each step stands:

| step | state | evidence |
|---|---|---|
| 1 — one Node process per pass | 🛑 **STOPPED by its own rule, twice**: one process is 1.11–1.44x faster, not ~5x. **Re-run 2026-10-03 after W-242 landed: 1.21–1.43x, still STOP.** The arm compares the scan, which Tier 1's plane does not touch, and each call still rebuilds the graph plane. **Reopens only when W-242's Fork A (Node reads `graph.json`) is ruled and built** | [`2026-09-30-ci-arm-batching`](../regression/2026-09-30-ci-arm-batching/report.md) |
| 2 — skip FULL on a known verdict | ✅ built: [`scripts/ci-key.py`](../../scripts/ci-key.py), [`full-verdict`](../../.github/actions/full-verdict/action.yml), a `verdict` job, the `publish.yml` gate, [SR-WORK-RELEASE](../../records/0063_WORK-release.md) d14. **17 of 40** recent commits would skip, not 22 | [analysis §Step 2](../regression/2026-09-30-ci-arm-batching/ANALYSIS.md) |
| 3 — Windows at the cause | 🟡 partly: profiled (one test was 54 % of the suite's spawns and 72 s on Windows; batched, answers identical on 166 commits); `TMP`/`TEMP` on `$RUNNER_TEMP`; FULL prints `--durations=30`. **In-process CLI tests and a second shard not done** — they wait on the 30-slowest profile from the first `main` run | [analysis §Step 3](../regression/2026-09-30-ci-arm-batching/ANALYSIS.md) |
| 4 — no queue, no serial stage | 🟡 `ladder` folded into `build`. **`needs:` stays**: 38 jobs against 20, and 8 macOS against 5, so the drop condition does not hold. It can only hold after step 1 | [analysis §Step 4](../regression/2026-09-30-ci-arm-batching/ANALYSIS.md) |

**First `main` runs read 2026-10-04 (Claude Code, Opus):**
- ✅ **The `verdict` job saved its key** on the green push run `37140432209`
  (`ci-full-v1-e9350750…-all`), and the nightly `37161222731` computed the same
  key for the same tree.
- **Windows (py3.14) slowest test:** `test_sr_freshness` at **29.5 s**, down
  from 72 s before step 3's batching.
- ⚠ **A new cost, from W-242's tests:** `tests/derive/test_node_accel.py` adds
  ~40 s on Windows: 128 Node processes across four `top` values. Batching it in
  one Node process is the cheap fix, and it is not done.
- ⏳ **Still to observe:** a docs-only push after a green FULL skipping every
  FULL cell. The 2026-10-04 session-close push is that push.

**What was left for done (as written 2026-09-30):** push, then read the first `main` run. Check that the
`verdict` job saved its key, that a docs-only push after it skips every FULL
cell, and what the Windows durations say. Then DoD 1–4 as below. DoD 3 (the arm
still finds a planted defect) is untouched, because the arm did not change.

**Ratified 2026-09-30.** Arpit, 2026-09-30, after the
timing analysis: *"let's implement number one, number two, number three,
number four"*, having said of the hash idea *"Hash one makes sense"*. He chose
to have Claude Code build it rather than the Cowork session. Pipeline diagram:
[`architecture-cicd.svg`](../architecture-cicd.svg).

**Model:** Claude Code. **Opus** for step 1 (it touches the differential arm,
whose value is that it cannot be fooled). **Sonnet** for steps 2–4 (workflow
and test plumbing).

## Why — measured 2026-09-30 from the GitHub API

Median of the last 5 green `ci.yml` runs on `main` (4 pushes, 1 nightly):

| | today | target |
|---|---|---|
| FAST verdict | 94–104 s | ≤ 2 min (already met; keep it) |
| whole run, push → last job | **546–735 s, median 620 s** | **≤ ~2.5 min** |
| runner time per push to `main` | ~109 min (13 FAST + 25 FULL jobs) | ~25–30 min |
| `publish.yml` | 83–88 s | unchanged |

Where the 10 minutes go:

1. **The Node arm is ~70 % of runner time.** A 1/3 `node-arm` shard spends
   101–147 s in its two `node_arm.py` passes; setup is 15–25 s. `node_arm.py`
   spawns **one `node` process per comparison** (`subprocess.run(["node", …,
   verb, query])`), and each one re-reads the committed index. Per-query cost
   and its split are in W-242 (closed 2026-10-03)'s compare doc.
2. **Windows runs the same tests ~3× slower.** Unit is 219–221 s on Windows
   against 67–75 s on Linux.
3. **Queueing.** 38 jobs against the plan's 20-concurrent cap, and 8 macOS jobs
   against its cap of 5. One job waited 163 s to start; a run's worst queue was
   182–304 s.
4. **`needs:` serialises FULL behind FAST**, adding ~100 s to the critical path.

## Relation to W-242 — do not duplicate it

W-242 (closed 2026-10-03) (ratified the same day) makes **each Node
query** cheaper: T0 reads each shard once, T1 reads Python's `.fux/runtime/`,
T2 lets Node build it. **This item does not re-do any of that.** Step 1 below
is the **harness** half — how many Node processes the arm starts — and it
**measures after** whatever of W-242 has landed. If W-242 T1 alone brings a
shard under ~30 s, step 1 shrinks to the job-count change.

## The four steps

### Step 1 — the arm answers many comparisons per Node process

- A driver under `tools/differential/` that starts **one** Node process per
  pass and feeds it the comparisons as JSON lines — the same way
  `compare_mcp` already drives a stdio session.
- 🔴 **Constraint — keep the verb seam covered.** `node_arm.py`'s own note says
  the W-107 defect *"lived in the VERB"*: comparing through the API alone would
  have missed it. So either the driver calls the same code path the CLI verb
  does (argument parsing and JSON rendering included), or a **fixed CLI
  sample** (every verb × a handful of queries) still runs one process each.
  Say which in the change, and why the chosen one cannot hide a verb-only
  defect.
- **Spike first, before building:** time N comparisons as N processes against
  one process, on this repo, natively. Record it in a `work/regression/` run.
  If one process is not at least ~5× faster per comparison after W-242's
  landed tiers, stop and report — the step is not worth its complexity.
- Then collapse the matrix: FAST `arm` 10 shards → the fewest that keep it
  ≤ ~60 s; FULL `node-arm` 3 shards per cell → 1 if the pass fits.
- Records: SR-NODE-SEARCH (the harness decision) and the `node_arm.py`
  sharding comment, which says batching cannot help — true only while every
  process pays the full read.

### Step 2 — skip FULL when its verdict is already known

Ruled design (Arpit, 2026-09-30, from the chat):

- **Key** = the git tree hashes of every path that can change a FULL verdict,
  **plus** OS, Python and Node versions, **plus** the runner image
  (`ImageOS` + `ImageVersion`).
- **Exclude list, not include list** — hash the whole tree **except** named
  inert paths (`work/`, `docs/`, `*.md` outside `src/`/`node/`/`tests/`,
  `CHANGELOG.md`). A new top-level folder then counts as code by default:
  it can cost speed, never correctness. Check `records/` before excluding it:
  67 of 117 test files read `records/` or `work/`.
- **Store** a verdict only on a green FULL run (`actions/cache` with
  `lookup-only`, or a commit status keyed by the hash — pick one and record
  why).
- **Nightly never reads the cache**: it always runs FULL. That is the backstop
  for floating dependencies (CI installs with `pip install -e`, not from
  `uv.lock`) and runner-image drift the key misses.
- **FAST always runs.** Only FULL is skippable.
- **`publish.yml`'s gate** changes from *"ci.yml green on this exact sha"* to
  *"a green FULL verdict for this sha's key"*. Keep the refusal wording: still
  running, red or missing → refuse.
- Measured on the last 40 commits: **22 of 40 would have skipped FULL** (all
  worklog, W-item, compare-doc and CHANGELOG commits). Every release commit
  touches `node/` (the version bump), so a release always gets a fresh run.
- Records: **SR-WORK-RELEASE** — a new decision amending the gate (d10/d13's
  "exact sha" wording) and naming the exclude list; the `ci.yml` and
  `publish.yml` header comments.

### Step 3 — Windows at the cause

In this order, measuring each with `--durations`:

1. Profile first: the slowest 30 Windows tests, and how many start a
   subprocess.
2. `TMP`/`TEMP`/pytest `--basetemp` on `$RUNNER_TEMP` (the D: drive). pip's
   CI saw 10–28 % from this alone
   ([source](https://ichard26.github.io/blog/2025/03/faster-pip-ci-on-windows-d-drive/)).
3. CLI tests that spawn `python -m fux …` run the entry point in-process
   (`main(argv)` with captured output) where that proves the same thing.
   Keep a small spawned sample, as step 1 does, for the real process seam.
4. If still over ~90 s, split the Windows unit suite into 2 duration-balanced
   shards.

Target: each Windows Python cell ≤ ~2 min.

### Step 4 — no queue, no serial stage

- After steps 1 and 3, count the jobs: **≤ 20 total and ≤ 5 macOS** (Free-plan
  caps, [GitHub docs](https://docs.github.com/en/actions/reference/limits)).
  Fold the 18 s `ladder` job into `build`.
- Then **drop `needs:`** from the FULL jobs, so every job starts at t=0 and
  the run lasts as long as its slowest job. The reason `needs:` exists — FULL
  starving FAST of runners (the `ci.yml` header, measured 2026-09-29) — is
  gone once the job count fits under the cap. **Re-measure that claim; do not
  assume it.**
- If the count cannot fit, keep `needs:` and say so. The two-minute FAST
  verdict matters more than the whole run.

## Definition of done

1. Five consecutive green runs on `main`: FAST ≤ 2 min, whole run ≤ ~2.5 min
   median, no job queued > 20 s. Numbers from the GitHub API, filed under
   `work/regression/`.
2. A docs-only push runs FAST alone. A release commit gets a fresh FULL run.
   A deliberately broken Windows-only test still reddens the nightly run.
3. The arm still finds a planted transcription defect (re-run W-107's H1/H2
   reproduction or an equivalent plant) after steps 1 and 4.
4. `architecture-cicd.svg` redrawn to the new shape.
5. Records amended in the same change: SR-WORK-RELEASE, SR-NODE-SEARCH, the
   workflow header comments.

## Out of scope

- Anything W-242 owns (Node reading or building `.fux/runtime/`).
- Paid or self-hosted runners.
- Removing an OS or version from the support matrix (L7/L8).
- The golden corpus (local-only, L11).
