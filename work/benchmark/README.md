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
| [`benchmark-v1-vs-head.html`](benchmark-v1-vs-head.html) | the **presentation** of the 2026-08-28 run — 18 slides, self-contained, no network. Open it in a browser; `←` `→` to move. The run itself is [`../regression/2026-08-28-benchmark-v1-vs-head/`](../regression/2026-08-28-benchmark-v1-vs-head/report.md) |

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
