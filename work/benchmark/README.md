---
type: Index
description: "Index of the version-comparison benchmark plans and their pre-registrations."
---

# `work/benchmark/` — the version-comparison plans

**How to use this directory.** This is where a **version-to-version** or
**knob-to-knob** benchmark is specified and its thresholds frozen, before any
number exists. It holds plans and runbooks, not results.

**Results do not live here — one narrow exception, named, and since 2026-09-13
it has its own directory.** Every benchmark run's HTML report lives in
[`reports/`](reports/README.md), one per run, dated
`<yyyy-mm-dd>-<run>.html` — the run directory's own name with `.html` on the
end. It is read by people rather than cited by documents. **The evidence is not
duplicated**: a report carries no number the filed run does not, and anything
that disagrees with `../regression/` is the report being wrong. **What must be
in one is [SR-WORK-BENCHMARK](../../records/0053_WORK-benchmark.md); the
skeleton is [`reports/TEMPLATE.html`](reports/TEMPLATE.html).**

Every executed run still files under
[`../regression/<date>-<run>/`](../regression/README.md) under the per-run
contract — report, `ANALYSIS.md`, `evidence/`, `VERDICT.md` where a threshold
is ruled on, a row in that README, a registry bump (SR-WORK-REGISTRY §3). That contract is a
repo law and this directory does not fork it. What is *new* here is only that a
benchmark's pre-registration is written once and cited by many dated runs,
rather than being buried in one run's `evidence/`.

## What is here

Three kinds of document, and the kind decides whether it may ever be edited:

| kind | may it change? | what it is for |
|---|---|---|
| **`PRE-REGISTRATION-*.md`** | 🔴 **never** — frozen once the first corpus byte exists. A later `HEAD`, a later knob, a better idea = a **new** pre-registration with a **new id space** | the bars, the metrics, the predicted verdicts, the things the run may never be used to say |
| **`RUNBOOK-*.md`** | yes — an operating procedure, corrected as the harness teaches | the step-by-step an agent executes, with the gate at every step, where each step runs, and which model runs it. **A runbook restates no bar**; it points at the pre-registration for every one |
| **`reports/*.html`** | yes, but only to agree with `../regression/` | **CAP-7** — one report per executed run, dated, built from `reports/TEMPLATE.html`. [Its own index](reports/README.md) |

| document | what it is |
|---|---|
| [`PRE-REGISTRATION-V1-VS-HEAD.md`](PRE-REGISTRATION-V1-VS-HEAD.md) | the frozen thresholds for `1.0.0` vs working-tree `HEAD`. ⚠ **It defines B1, B2, B3, B5, B6, B7 and B9** — *"B1–B9"* is prose, and **B4 and B8 were never written**. ⚠ Its §7 *"owed before this can run"* is **discharged** — everything on it was built on 2026-08-28 — and its **B-full ceiling table (§1, §6 step 11) was never produced**: the filed run carries arms A and B-core only. Both stand as written because the document is frozen; the runbook is where the correction lives. Executed as [`../regression/2026-08-28-benchmark-v1-vs-head/`](../regression/2026-08-28-benchmark-v1-vs-head/report.md) |
| [`PRE-REGISTRATION-V1-V2-HEAD.md`](PRE-REGISTRATION-V1-V2-HEAD.md) | the frozen thresholds for **`1.0.0` vs `2.0.1` vs frozen `HEAD`** on the golden ladder (W-204 phase B), ids **`P1`–`P8`** — a **new id space**, because the 2026-08-28 document froze one sha, two arms and a generated corpus, and all three have moved. It cites that document and does not edit it. 🔴 **Descriptive per set, never pooled**: 125 + 124 + 125 questions put each set at power 0.23–0.67, so a pair that does not clear [SR-RS](../../records/0133_predictions.md) decision 19's net of 6 is reported as *not distinguishable at this N* and never as *no difference*. 🔴 **It files no correctness number** — the key is not open, and captures 3, 4 and 7 of [SR-WORK-BENCHMARK](../../records/0053_WORK-benchmark.md) stay empty until phase D. ⚠ **Two asymmetries are frozen into it BEFORE the run, both measured on a smoke arm rather than predicted:** `v1.0.0` has no `formats.toml` and indexes `.md`/`.txt` only, so it **cannot see 4 of the 28 seed documents** and that is part of the arm, not a defect to patch; and `v1.0.0`'s `ask` has **no `--band`**, so the confidence band is a `v2 → HEAD` statement only. **The null control (`v1` against itself) runs first and nothing else runs until it reports zero moved rows.** Not yet executed |
| [`PRE-REGISTRATION-CONTESTED.md`](PRE-REGISTRATION-CONTESTED.md) | the frozen thresholds for the **contested-answer suite** (W-95), `sha256 e8417b33…`. ⚠ It defines **`C1`–`C6`** — a **new id space**, because the `B` ids belong to the frozen v1-vs-HEAD document and may never be reused or renumbered. Its arms are **deliberately identical** to that run's, so only the instrument differs. Executed as [`../regression/2026-08-28-benchmark-contested/`](../regression/2026-08-28-benchmark-contested/report.md). ⚠ Its `heading` control **saturated** (C4 Inconclusive) and must be rebuilt before it is cited as a control again |
| [`PRE-REGISTRATION-TUNER.md`](PRE-REGISTRATION-TUNER.md) | the frozen thresholds for the **knob sweep** over `.fux/tune.toml` (W-97), ids **`T0`–`T5`** — a third id space. **One engine, many knob values**; the arms of a version benchmark do not appear. It answers *"which shipped default, if any, is defensible?"* and is built so that it **cannot** answer it alone: a generated suite selects, a hand-graded set vetoes, and the default change itself is an SR-TUNE amendment Arpit ratifies. 🔴 **Never executed, and now void in part** — the veto leg's corpus was `fux-playground`, closed by [SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md); the two in-scope knobs were instead measured by [the priors run](../regression/2026-09-12-priors-and-tables/PRE-REGISTRATION.md) §3, which supersedes this file rather than editing it |
| [`PRE-REGISTRATION-NODE.md`](PRE-REGISTRATION-NODE.md) | the frozen bar for the **Node read plane** (W-107), ids **`N0`–`N4`** — a **fourth id space**. **One index, two readers**; not a version comparison. 🔴 **ONE CELL IS DELIBERATELY UNFROZEN** — §2's score-comparison mode is Arpit's `log()` decision, which the 2026-09-05 ratification left unstruck, and **the document is not frozen until he fills it in**. Everything else is: the byte-equal field table, ids `N0`–`N4`, `N4`'s **p95 ≤ 150 ms at 10 000 documents** (3× Python's measured 50.2 ms — a fence against an algorithmic divergence, not a constant factor), the corpora, and **all three OS/libm pairs**. Grounded in [`../regression/2026-09-05-node-log-divergence/`](../regression/2026-09-05-node-log-divergence/report.md). **Not yet executed; Phase 1 does not start before §0 is filled.** |
| [`RUNBOOK-BENCHMARK.md`](RUNBOOK-BENCHMARK.md) | the agent-executable procedure for a **version** benchmark against either frozen pre-registration above — stand-up, gates, machine split, the two-session `blind` protocol, filing. Written 2026-08-28 from what the two executed runs learned |
| [`RUNBOOK-TUNER.md`](RUNBOOK-TUNER.md) | the agent-executable procedure for the **knob sweep** — one index per corpus, many query passes, a veto leg, the candidate table. 🔴 **Void in part**: the veto leg has no instrument since SR-WORK-ENVIRONMENTS |
| [`reports/`](reports/README.md) | **every benchmark run's HTML report**, one per run, dated `<yyyy-mm-dd>-<run>.html`, plus the [`TEMPLATE.html`](reports/TEMPLATE.html) they are built from. 🔴 **This is the only home for CAP-7** — SR-WORK-BENCHMARK decision 7, amended 2026-09-13. Three reports are there today; [`2026-09-12-benchmark-l9`](../regression/2026-09-12-benchmark-l9/report.md) is the one filed benchmark run with none, and is owed as **W-158** |

**Id spaces, so far:** `B` (v1-vs-HEAD) · `C` (contested) · `T` (tuner). The
next pre-registration takes the next letter. An id is never reused, renumbered
or given a second meaning.

## Why this is not `work/regression/`

A regression run answers *"did this change break something?"* against a
baseline the same engine produced. A benchmark answers *"what is the difference
between two engines?"* — or, for the tuner, *"between two settings of one
engine?"* — two installs or two configurations, two indexes or one, one corpus.
The instrument is different enough that its plan is worth reading on its own,
and it is cited by more than one dated run.

## Why this is not `fux-lab`

The lab measures **one** engine against its own baselines, and its environments
pin **one** `VERSION`. A version comparison needs two engines resident at once,
in two venvs, over byte-identical corpora. That is a different harness, and it
lives in a sibling working directory — [SETUP-BENCHMARK](../setup/fux-benchmark.md),
`~/my_programs/fux-benchmark`. The tuner uses the same harness with one arm.

⚠ **This does not license deleting or bypassing `fux-lab`.** SETUP-LAB's
standing rule — *never delete it, never start a parallel harness* — exists
because losing it once cost every baseline. `fux-benchmark` is additive: it
answers a question the lab's one-version-per-environment shape cannot express,
and it borrows the lab's `shared/generate/make_corpus.py` rather than
reimplementing corpus generation. If the two ever diverge on how a corpus is
generated, the lab is canonical.

## The rules a benchmark run inherits

1. **Per-query rows are mandatory** (Arpit, 2026-08-28). One row per query per
   arm — or per knob value — under `evidence/`. `b`, `c`, the discordant count
   and every test fall out of those rows and out of nothing else. ⚠ **The lab
   harness still emits totals only**; a run that needs a graded pass must emit
   rows for it or it cannot be filed.
2. **`blind` or `informed`, declared in frontmatter, with an `## Authorship`
   section.** A benchmark is unusually exposed here: whoever writes the corpus
   generator and the query set must not have seen either arm's output. **One
   session cannot produce a `blind` run** — both 2026-08-28 runs say so. The
   two-session protocol is in
   [SETUP-BENCHMARK](../setup/fux-benchmark.md#the-two-session-blind-protocol)
   and [RUNBOOK-BENCHMARK §6](RUNBOOK-BENCHMARK.md).
3. **A delta below the set's resolution is `no detected change`.** The
   resolution is the **discordant count**, never the set size — see
   [`../regression/2026-08-28-resolution-floor/`](../regression/2026-08-28-resolution-floor/report.md).
   A net of 1–5 cannot clear α = 0.05 at any discordant count.
4. **Every benchmark run ships a presentation** (Arpit, 2026-08-28). One
   self-contained, theme-aware HTML deck per executed run, filed **beside the
   plan** under the named exception above and linked from the table. **Precise
   and to the point** — and **a diagram, chart or worked example wherever the
   content has a shape**: a cluster's anatomy, the pipeline's gates, headroom by
   suite, an arm-vs-arm bar. ⚠ **The deck carries no number the filed run does
   not**, and anything that disagrees with `../regression/` is the deck being
   wrong. It is a presentation of evidence, never a second source of it.
   Charts follow the house tokens; **arm A is the neutral baseline and arm B the
   accent**, with a legend and a direct value label on every mark so identity is
   never colour-alone.
5. **Headroom is declared beside power, per endpoint** — the current score and
   how many queries *could* change. Practised since the contested run
   (C6), where it caught a saturated control inside the run that introduced
   it. ⚠ **Ratifying this into SR-RS is Arpit's** (OPEN-WORK, *adr update*);
   until then it is run practice, not law — but no run in this directory is
   filed without it. **A control with no headroom is decoration, and its
   verdict is `INCONCLUSIVE`, not `PASS`.**
6. **The null control is the same-corpus repeat.** Arm A twice on identical
   bytes → byte-identical rows, or halt. A cross-seed pairing compares
   *different questions* and is a rate check, reported descriptively. The
   v1-vs-HEAD B9 was read as a determinism check and carries this weakness.
7. **The harness never picks a threshold, and a runbook never restates one.**
   Bars live in the frozen pre-registration; the harness prints `p`; the runbook
   says *"rule against §4.x"*. If a runbook and a pre-registration disagree, the
   pre-registration wins and the runbook is fixed in the same change.
