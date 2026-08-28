# `work/benchmark/` — the version-comparison plan

**How to use this directory.** This is where a **version-to-version** benchmark
is specified and its thresholds frozen, before any number exists. It holds
plans, not results.

**Results do not live here — one narrow exception, named.** A **presentation**
of an executed run may live beside its plan, because it is read by people rather
than cited by documents. **The evidence is not duplicated**: the presentation
carries no number the filed run does not, and anything that disagrees with
`../regression/` is the presentation being wrong.

Every executed run still files under
[`../regression/<date>-<run>/`](../regression/README.md) under the per-run
contract — report, `ANALYSIS.md`, `evidence/`, `VERDICT.md` where a threshold
is ruled on, a row in that README, a `DOC-REGISTRY` bump. That contract is a
repo law and this directory does not fork it. What is *new* here is only that a
benchmark's pre-registration is written once and cited by many dated runs,
rather than being buried in one run's `evidence/`.

| document | what it is |
|---|---|
| [`PRE-REGISTRATION-V1-VS-HEAD.md`](PRE-REGISTRATION-V1-VS-HEAD.md) | the frozen thresholds for `1.0.0` vs working-tree `HEAD`. ⚠ **It defines B1, B2, B3, B5, B6, B7 and B9** — *"B1–B9"* is prose, and **B4 and B8 were never written** |
| [`PRE-REGISTRATION-CONTESTED.md`](PRE-REGISTRATION-CONTESTED.md) | the frozen thresholds for the **contested-answer suite** (W-95), `sha256 e8417b33…`. ⚠ It defines **`C1`–`C6`** — a **new id space**, because the `B` ids belong to the frozen v1-vs-HEAD document and may never be reused or renumbered. Its arms are **deliberately identical** to that run's, so only the instrument differs. Executed as [`../regression/2026-08-28-benchmark-contested/`](../regression/2026-08-28-benchmark-contested/report.md) |
| [`benchmark-v1-vs-head.html`](benchmark-v1-vs-head.html) | the **presentation** of the 2026-08-28 run — 18 slides, self-contained, no network. Open it in a browser; `←` `→` to move. The run itself is [`../regression/2026-08-28-benchmark-v1-vs-head/`](../regression/2026-08-28-benchmark-v1-vs-head/report.md) |
| [`benchmark-contested.html`](benchmark-contested.html) | the **presentation** of the 2026-08-28 contested-answer run — 12 slides, self-contained, theme-aware. Open it in a browser; `←` `→` to move. The run itself is [`../regression/2026-08-28-benchmark-contested/`](../regression/2026-08-28-benchmark-contested/report.md) |

## Why this is not `work/regression/`

A regression run answers *"did this change break something?"* against a
baseline the same engine produced. A benchmark answers *"what is the difference
between two engines?"* — two installs, two indexes, two wheels, one corpus.
The instrument is different enough that its plan is worth reading on its own,
and it is cited by more than one dated run.

## Why this is not `fux-lab`

The lab measures **one** engine against its own baselines, and its environments
pin **one** `VERSION`. A version comparison needs two engines resident at once,
in two venvs, over byte-identical corpora. That is a different harness, and it
lives in a sibling working directory — [SETUP-BENCHMARK](../setup/fux-benchmark.md),
`~/my_programs/fux-benchmark`.

⚠ **This does not license deleting or bypassing `fux-lab`.** SETUP-LAB's
standing rule — *never delete it, never start a parallel harness* — exists
because losing it once cost every baseline. `fux-benchmark` is additive: it
answers a question the lab's one-version-per-environment shape cannot express,
and it borrows the lab's `shared/generate/make_corpus.py` rather than
reimplementing corpus generation. If the two ever diverge on how a corpus is
generated, the lab is canonical.

## The three rules a benchmark run inherits

1. **Per-query rows are mandatory** (Arpit, 2026-08-28). One row per query per
   arm, under `evidence/`. `b`, `c`, the discordant count and every test fall
   out of those rows and out of nothing else.
2. **`blind` or `informed`, declared in frontmatter, with an `## Authorship`
   section.** A benchmark is unusually exposed here: whoever writes the corpus
   generator and the query set must not have seen either arm's output.
3. **A delta below the set's resolution is `no detected change`.** The
   resolution is the **discordant count**, never the set size — see
   [`../regression/2026-08-28-resolution-floor/`](../regression/2026-08-28-resolution-floor/report.md).
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
