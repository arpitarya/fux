---
type: Handoff
name: W-281
description: "Arpit's ask (2026-10-13, Claude Code): make a measured run's capture faster. W-278's capture takes ~45 min and its ladder build stalled 12 h on commit signing. Parallelise what does not care about load (G1's 10 000-doc ingest, G3's arms), keep the latency guardrail standalone, and stop the ladder builder from waiting on gpg. Driver and builder changes only; no bar, gate or engine change."
item: W-281
filed: 2026-10-13
filed_by: "Arpit (Claude Code, Opus 5.5)"
updated: 2026-10-18
updated_by: "Arpit (Cowork, Opus 5.5)"
ball: agent
---

# W-281 — capture and ladder speed

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | Stop the test-data builder signing its commits | no more 12-hour stall waiting on gpg | ✅ built (template) |
| 2 | Run the 10 000-document ingest in the background | about 10 minutes saved | ✅ built (template) |
| 3 | Run the three comparison arms side by side | about 10 minutes saved | ✅ built (template) |
| 4 | Keep the timing check last and alone | speed numbers stay honest | ✅ built (template) |
| 5 | Time every step of the next capture | proof: about 45 min down to 30 or less | ⏳ owed by the next capture |

**Arpit, 2026-10-13 (Claude Code):** *"why does it take an hour? can it be
done faster … okay add a work item for improving the performance."*

**Model:** Claude Code, **Sonnet**: a driver change against a written
procedure. No ranking, gate or record decision moves.

## Where the time goes (W-278's capture, `evidence/capture.sh`)

| step | ~time | load-sensitive? |
|---|---|---|
| base copy + `ingest --full` (1 000 docs) | 3 min | no |
| 4 captures × 165 questions (`ask` + `answer`, a fresh process each) | 8 min | only `ask_ms`/`answer_ms`, which no gate reads (G0 ignores them) |
| **G3**: `ask --why --top 1000` × 165 × 3 arms, serial | 10–15 min | no |
| G4 (in-process) | 2 min | no |
| **G1**: `ingest --full` of `rung-10000`, after everything else | ~10 min | no: it measures bytes |
| latency: 2 rebuilds + 3 × 165 × 2 timed calls | ~8 min | 🔴 **yes**: L13 requires it standalone |

And the ladder: **rung-10000 took 43 690 s on 2026-10-13** (rung-05000 took
508 s). The builder's per-date `git commit`s inherit the user's
`commit.gpgsign = true`, and signing blocked on gpg from 01:16 until 13:23
([build log](../regression/2026-10-13-ladder-gen6-rebuild/evidence/build.log)).

## Definition of done

| DoD | what | state |
|---|---|---|
| 1 · ladder never signs | the builder's commits run with `-c commit.gpgsign=false` (a rung is lab data, never pushed). The driver change goes in the next ladder run's `build_from_worktree.py`; the fux-lab builder stays unmodified unless Arpit says otherwise | ✅ built in tools/quality-controls/capture-driver/, unmeasured |
| 2 · G1 in parallel | the `rung-10000` copy and its `ingest --full` start in the background at the top of the capture and are joined before latency | ✅ built in tools/quality-controls/capture-driver/, unmeasured |
| 3 · G3 by arm in parallel | one `g3.py` process per treatment arm, or the arms' `--why` calls interleaved in one process: **the frozen `g3.py` is not edited** (its hash is in a bar); a driver may only run it differently | ✅ built in tools/quality-controls/capture-driver/, unmeasured |
| 4 · latency untouched | runs last, alone, after every background job is joined and `uptime` is recorded; nothing here changes `latency.py` or its three-runs rule | ✅ built in tools/quality-controls/capture-driver/, unmeasured |
| 5 · measured | the next capture logs each step's wall time; target ≤ 30 min, with the latency step unchanged | ⏳ owed by the next run: capture.sh logs capture-timing.tsv; not run (shared machine, SR-RS filing) |

## Hazards

- ⚠ **A frozen script is not touched.** `g0.py`, `g3.py`, `g4.py`, `latency.py`
  and `decide.py` are hashed in their run's pre-registration. Only the driver
  (`capture.sh`, unfrozen by design) changes.
- ⚠ **The latency guardrail stays standalone** (L13 decision 3,
  SR-WORK-SESSION decision 12). Parallel load must be joined before it starts.
- ⚠ Applies from the next run. W-278's capture in flight on 2026-10-13 runs
  serially, as written.

## Reference

[W-278](../../archive/open/W-278-section-term-v3.md) ·
[`capture.sh`](../regression/2026-10-13-section-term-v3/evidence/capture.sh) ·
[W-270's capture](../regression/2026-10-11-section-retest-set-6/evidence/capture.sh) ·
[L13](../../records/0015_LAW-13-the-standing-bar.md)
