---
type: OpenItem
id: W-148
title: "W-148 — what the two readers still owe: CI reach, the latency fence, and the renderer split"
description: "The three things W-107 could not close and one SR-API deliberately staged. None is a build task: two are decisions Arpit has not taken, one needs an environment nobody has built, and the fourth is a refactor of a 1 481-line hot file that is explicitly not in scope until someone asks for it. Filed so that closing W-107 does not close them by silence."
status: open
lane: agent
timestamp: 2026-09-12T00:00:00Z
---

# W-148 — what the two readers still owe

**Model: Opus** for rows 1 and 2 (each is a call about what a measurement is
allowed to claim); **Sonnet** for row 4 once row 4's definition-of-done exists.

## 🔴 A third call, named 2026-09-14: the benchmark harness has no commits

**`~/my_programs/fux-benchmark` is a git repo with ZERO commits and every file
untracked.** W-158 rewrote `bin/report.py` there so that
[SR-WORK-BENCHMARK](../../records/0053_WORK-benchmark.md) decisions 8–10 are
actually enforced by code — and that code now exists **on one machine**.

⚠ **Nothing in fux would notice it going.** `tests/test_benchmark_capture.py`
checks that a report was *filed*, never that anything can still generate one,
so a wiped `fux-benchmark` leaves every past report intact and every future one
impossible, silently.

**This is the same question this item already asks in its second row** —
*whether `fux-benchmark` gets built or Node's latency stays unmeasured* — with
one more thing riding on the answer. Three shapes, and the call is Arpit's:

| | what it means |
|---|---|
| **commit the harness in place** | one `git commit` in that repo. Cheapest, and it makes the environment something more than scratch, which is a change to what SR-WORK-ENVIRONMENTS says it is |
| **vendor the emitter into fux** | `report.py` reads only `TEMPLATE.html` and a run's `evidence/`, both of which live in fux — so it could live in `tools/` with an ownership row and a test. It is the only part of the harness with no dependency on the sibling environment |
| **leave it scratch and accept the exposure** | then decisions 8–10 are enforced by a file with no home, and this record should say so where it states them rather than only here |

## Why this file exists, said plainly

[W-107](../IMPLEMENTATION.md) closed on 2026-09-12: the Node read plane is
built, five surfaces are compared against Python, and
[SR-NODE-SEARCH](../../records/0153_node-search.md) is accepted and built.

**Four obligations were open inside it and none of them is agent-closable.**
Deleting W-107's row without carrying them forward would have closed them by
silence, which is the failure OPEN-WORK rule 2 exists to prevent: an item is
removed once its outcome is in `IMPLEMENTATION.md`, **not once the parts nobody
can do have become invisible.**

⚠ **This file is not a place to park W-107's unfinished build.** There is no
unfinished build. Every row below was already written down in W-107 or in
SR-API as blocked, staged, or a decision — check that claim against
[the register](../../records/README.md) before believing it.

---

## 1 · 🔴 CI cannot meet PRE-REG-NODE-2 §4's cadence, and the routes out are decisions

**§4 says `rung-00100` + `rung-10000` per push, all eight nightly and before a
release.** [`node-arm.yml`](../../.github/workflows/node-arm.yml) runs
`ladder_check.py` (manifests only, no corpus) always, and runs the arm the
moment `FUX_GOLDEN_CORPORA` points at a checkout that has the rungs.

**A GitHub runner does not have them**, and each reason is separately fatal:

| | |
|---|---|
| the corpora are not committed | and [L2](../../records/0004_LAW-2-content-never-durable.md) is why |
| `rung-10000` is **120 MB** | too big for the repository whatever L2 said |
| `build_golden_rung.py` hard-codes two absolute paths | on Arpit's machine |

**So the cadence is met in fux-lab, on one OS.** That is stated in the workflow
and in every report; nothing claims otherwise.

**The three routes, none taken:**

1. **A self-hosted runner** — the corpora exist on exactly one machine, so this
   is the only option that needs no new artifact. It also means CI runs on
   Arpit's hardware, which is a standing cost and a security surface.
2. **A committed small rung** — `rung-00100` is small enough to commit. It
   would give a real corpus on every push on three OSes. ⚠ **It is committed
   corpus content**, and L2 is the law the whole architecture rests on; whether
   a synthetic generated corpus is "content" is precisely the question.
3. **A portable builder** — de-hard-code the paths so a runner can generate a
   rung from the committed seed. Costs runner minutes on every push and makes
   the corpus a function of the generator's version rather than of a manifest.

**Nothing may start until one is chosen.** Building the wrong one is a week.

## 2 · 🔴 Nothing measures Node's latency, and the instrument does not exist

N4's `p95 ≤ 150 ms` fence was retired with PRE-REGISTRATION-NODE and moved to
`fux-benchmark` ([SETUP-BENCHMARK](../setup/fux-benchmark.md)), so the bar is
**stated rather than silently dropped**.

**`fux-benchmark` is unbuilt and is carried by no open item** — W-139 was
removed from the queue on 2026-09-12.
[SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md) puts benchmarks there and
nowhere else, so this cannot be measured in fux-lab or in the repo as a
workaround.

⚠ **The structural argument is not a measurement and must not be filed as
one.** Node's scan is the same algorithm over the same shards; the
2026-09-12 change adds three small config reads per query and a reranker that
touches at most 20 documents and only when `rerank_weight > 0`. **That says
where to expect the number, not what it is.**

**The decision:** build `fux-benchmark` (its own item), or accept that Node's
latency is unmeasured and say so in the record rather than in a report nobody
re-reads.

## 3 · 🟠 [`log-probe.yml`](../../.github/workflows/log-probe.yml) has still never run

Phase 0's `log()` evidence covers **darwin/arm64** and **glibc 2.39/x86-64**,
the second from a Linux container rather than from CI. **musl, Windows and
Node 20 are unmeasured.**

The workflow exists, is `workflow_dispatch`-only by design, and **is not on
`origin/main`** — so it cannot be dispatched until the branch is pushed.

⚠ **Phase 0's conclusion does not depend on it.** Arpit ruled option (b) in
2026-09-06: the arm compares the score at `round(9)`, and across
**10 939 enumerated `idf` arguments** at three corpus sizes, 841 differ
bit-for-bit and **0 differ at `round(9)`**. A third libm would have to diverge
by ~7 orders of magnitude more than the two measured ones to matter. **This row
is about closing a stated gap, not about a risk anyone has a reason to expect.**

## 4 · 🟠 The renderer split — SR-API's `partial`, deliberately staged

[SR-API](../../records/0154_api.md) records `cmd_ask -> print(render(api.ask(...)))`
as the finished shape and the current arrangement as **staged, not done**. It
touches [`query/__init__.py`](../../src/fux/query/__init__.py), a **1 481-line**
file on the hot path, and W-107 put it out of scope explicitly.

**What it would buy, now that both library surfaces are compared:**
`api.py::_answer_from` still runs `cmd_answer` and **parses its own stdout
back** to build an `Answer`. Node no longer does — `answerPayload` returns the
object and `runAnswer` renders it (2026-09-12), so the Node half of the split
is already taken on the one verb that needed it. The asymmetry is now visible
rather than theoretical.

**Not started, and it should not be started casually.** A refactor of that file
with no failing test driving it is how a renderer change becomes a ranking
change.

---

## What this item does NOT contain

- **No part of the Node reader's build.** It is finished and measured —
  [`2026-09-12-node-tune-and-surfaces`](../regression/2026-09-12-node-tune-and-surfaces/report.md).
- **`verify`, `--why`, `--receipt`, `--journal` and `--expand` in Node.** Out of
  scope by W-107 R6, which is a decision rather than a debt. `--expand` is the
  one of the five that *could* be compared today and is not; naming it here is
  a note, not a commitment.
- **The `find --under` semantics fork** between `fux.api` and the CLI. That is
  SR-API decision 6's stated difference on a frozen surface, and it is Arpit's
  call — it belongs in the inbox if he wants it, not in a build item.

## ✅ RULED 2026-09-14 (Arpit) — all three calls

| call | ruling | agent work |
|---|---|---|
| **1 · CI and the golden corpus** | **The golden corpus is not for CI.** Golden runs local-only, in `fux-lab`. No self-hosted runner, no committed rung, no portable builder | `node-arm.yml` keeps `ladder_check.py` (manifests only) and drops the `FUX_GOLDEN_CORPORA` arm; PRE-REG-NODE-2 §4's cadence is rewritten as a local cadence; every report that says *"CI would…"* says *local* |
| **2 · Node's latency** | **Add the Node measurement to `fux-benchmark`, the same shape as Python's** — same rungs, same `p95`, one more column | a `node` arm in `fux-benchmark`'s capture, the row in [SR-WORK-BENCHMARK](../../records/0053_WORK-benchmark.md), the N4 fence re-stated as measured |
| **3 · the harness's zero commits** | **Insignificant.** `fux-benchmark` is scratch for testing; commits are optional — *"if you do it, great; if not, also fine"* | the record states the harness is scratch and that SR-WORK-BENCHMARK decisions 8–10 are enforced by an uncommitted file, so nobody rediscovers it |

## Blockers

- ✅ Rows 1 and 2 were Arpit's calls; **ruled above**. Agent work proceeds.
- 🟡 Row 3 needs the branch on `origin/main`; **no session pushes without being
  asked** (CLAUDE.md).
- 🟢 Row 4 is agent work whose definition-of-done does not exist yet.
