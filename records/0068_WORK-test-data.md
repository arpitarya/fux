---
type: Standing Record
kind: process
name: SR-WORK-TESTDATA
title: "SR-WORK-TESTDATA (0068) — what test data creation must carry: one checklist, pointers to each rule's home, and every authoring prompt bound to it"
description: "The checklist every piece of golden test data is authored against — seed documents, question sets, rungs. Each item is one line and points to the record that states it; the items with no other home are stated here. Every prompt that creates test data links this record and names the items it carries, and a test fails when one does not."
status: accepted
date: 2026-09-22
feature: the test-data checklist — what a seed document, a question set or a rung must contain before any measurement on it can mean anything
owns: [tests/test_test_data_prompts.py@bd8b66eef82e]
laws: [L0, L11]
timestamp: 2026-09-22T00:00:00Z
content_sha: 7e097297f321067ed5d7e1e1e4ce84741a10ff4caa6ccd7c665044f719952baf
ratifies: "Arpit, 2026-09-22 — 'note it down that this is also one of the cases that need to be tested. So in future, the prompt or test data creation should account for this use case … create a work document which will just have pointers what all things test data creation should have … keep everything precise … I was talking about SR work document'"
---

<!-- COMPONENTS-START — GENERATED from records/README.md's OWNERSHIP and DESCRIBES tables by scripts/gen-components.py. Do not edit by hand: change the table, then run `python scripts/gen-components.py --write`. -->

**Owns** — the components this record decides:

- [`tests/test_test_data_prompts.py`](../tests/test_test_data_prompts.py) · file

<!-- COMPONENTS-END -->

# SR-WORK-TESTDATA — what test data must carry

## §1 — For humans

**Test data decides what a measurement can say before the measurement runs.**
Four times now a feature was built, measured and came back empty because the
data never contained the thing the feature acts on. Each time, the missing
input was found one step at a time, the expensive way.

**This record is the checklist that stops that.** Fourteen items. Each is one
line, and each points to the record that owns the rule — **this record restates
none of them**. The four items nobody owned before (T4, T5, T11 and the
use-case rule in decision 4) are stated here.

**Every prompt that creates test data links this record** and says which items
it carries. A test fails when a prompt does not, so a future prompt cannot
forget the list exists.

---

## §2 — For agents

### Context

On 2026-09-22 two measurements
([the step-input run](../work/regression/2026-09-22-w168-step-inputs/report.md),
[the anchor census](../work/regression/2026-09-22-anchor-input-census/report.md))
found that **four of W-168's eight remaining ranking steps have no input in the
seed at all**, and that the three retired sets were too easy to decide the rest.
The rules that would have caught it existed, scattered across SR-RS, SR-WORK-GOLDEN,
the golden README and three prompts. **No one place listed them**, so no author
could check against them.

### Decision

1. **This record IS the test-data checklist, and it holds pointers.** An item
   whose rule lives in another record links that record and restates nothing
   ([SR-LAW-0](0002_LAW-0-authority.md) decision 1). An item with no other home
   is stated here, once.

2. **The checklist.** Every seed document, question set and rung is authored
   against it. **An item a piece of test data does not carry is named as
   *not carried* in that data's prompt or report — never silently skipped.**

   | # | the data must carry | home |
   |---|---|---|
   | **T1** | **The input each feature under test acts on.** A missing input is a data defect, not a null | [SR-RS](0133_predictions.md) d23 |
   | **T2** | **One coverage tag per feature, named for the step it gates** — not a tag that merely resembles it (`link_dependent` is multi-hop; `vocabulary_gap` is paraphrase) | [SR-RS](0133_predictions.md) d23c |
   | **T3** | **Headroom** — questions today's engine does not already answer, made hard *by construction* (a count of discriminations), **never** by consulting the engine's results | [SR-WORK-GOLDEN](0066_WORK-golden.md) d13; the bar is [SR-RS](0133_predictions.md) d19 |
   | **T4** | 🆕 **Anchor-only vocabulary** — see below | **stated here** |
   | **T5** | 🆕 **Abbreviation and glossary pairs** — see below | **stated here** |
   | **T6** | **Identifiers of the failing shape** — shared prefix + short number, near neighbours, in the body **and** as `doc_id:`, with ≥ 1 id-query each | [SR-RANKING](0111_ranking.md) d9 · [SR-INGEST](0106_ingest.md) d23d · [prompt 3](../work/golden/prompts/3-claude-questions.md) part B |
   | **T7** | **Link-bearing documents** — inline links that resolve to another ingested document, plus questions answerable only by following one | [`work/golden/README.md`](../work/golden/README.md) §Feature coverage |
   | **T8** | **Superseding pairs, archived documents and recency** — including cases where the **older** document is correct | [`work/golden/README.md`](../work/golden/README.md) §Feature coverage |
   | **T9** | **Unanswerable near-misses** at ~10 %, permuted so no id band carries a type | [prompt 3](../work/golden/prompts/3-claude-questions.md) §Three rules |
   | **T10** | **Heading-matched distractors** — so no question is answerable by heading alone | [`work/golden/README.md`](../work/golden/README.md) §Feature coverage, `heading` row |
   | **T11** | 🆕 **A corpus with real git history** — see below | **stated here** |
   | **T12** | **Additions only** — an existing seed document is never edited; new documents rebuild the ladder | [prompt 3](../work/golden/prompts/3-claude-questions.md) part B · [`work/golden/README.md`](../work/golden/README.md) phase 4 |
   | **T13** | **Custody and naming** — the one-session-per-set carve-out, `set-<gen>-<x\|u>`, and `informed` for every agent-authored set | [L11](0012_LAW-11-sealed-answer-key.md) · [SR-WORK-GOLDEN](0066_WORK-golden.md) d14 |
   | **T14** | **At most 10 000 documents** on any rung | [SR-WORK-SCALE](0057_WORK-scale.md) |

3. **The three items stated here.**

   - **T4 — anchor-only vocabulary.** At least one document must be findable
     **only** through the words *other* documents use when they link to it: a
     house nickname or acronym the target never uses about itself. Plus **a
     hub** — one document linked from many others in unrelated words. Plus
     **questions phrased in the linker's words**, never the target's.
     *Why:* the 2026-09-22 census found **one** anchor-distinctive term in the
     whole seed, and it was a filename — so the anchor-text feature (W-168
     step 1) had nothing to act on.
   - **T5 — abbreviation and glossary pairs.** `Term (ABBR)` pairs, glossary
     lines of the form `term — definition`, and `aliases:` front matter, with
     questions that use **one** form while the answering document spells out
     the **other**. *Why:* measured `0` / `1` (a false positive) / `3` on one
     document — so corpus-mined expansion (step 4) had nothing to mine.
   - **T11 — git history.** A feature that reads commit history is measured on
     a corpus that **has** history — several authors and commits over time —
     never on a synthetic ladder rebuilt at one stamp. *Why:* the git
     authority prior (step 8) otherwise stays a proposal by its own terms.

4. 🔴 **A new failure class becomes a new item here, in the same change that
   finds it.** A measurement that comes back empty because the data lacked an
   input adds a `T`-row naming that input, with the measured count that proved
   it missing. **That is how T4 and T5 arrived**, and it is the only way the
   list grows.

5. 🔴 **Every prompt that creates test data links this record and names the
   items it carries.** That is the seed prompts, the question prompts and the
   rung prompt under [`work/golden/prompts/`](../work/golden/prompts/). A prompt
   written for **one use case** — [prompt 10](../work/golden/prompts/10-claude-feature-input-seed.md)
   is the first — names the `T`-items it exists for in its first lines.

6. **Enforcement:** [`tests/test_test_data_prompts.py`](../tests/test_test_data_prompts.py)
   fails when an authoring prompt does not link this record, when a new prompt
   file is added without being classified as authoring or not, and when the
   `T`-items stop being numbered `T1…Tn` without a gap — so an item cannot be
   dropped silently.

### Consequences

- **An author has one list to check against**, and the list names where each
  rule actually lives, so it cannot drift from them — it states nothing they do.
- **The test binds the prompts, not the data.** Nothing checks that a seed
  document *actually* carries T4; a prompt can link this record and still
  produce data that lacks it. The measured census in each run is what catches
  that, after the fact.
- **T3 stays the hardest item to meet and the easiest to fake.** Hard by
  construction is checkable; *the engine fails it* is not allowed as a
  definition, because every claim built on it becomes circular.

### Alternatives considered

- **Put the list in `work/golden/README.md`.** Rejected: the README documents
  the benchmark process, and a list there has no owner a change can demand.
- **Restate each rule here in full.** Rejected: fourteen second copies, each
  able to disagree with its home while both look correct — the exact thing
  L0 forbids.

### Reference (required)

- [the step-input run](../work/regression/2026-09-22-w168-step-inputs/report.md)
  and [the anchor census](../work/regression/2026-09-22-anchor-input-census/report.md)
  — the measured counts behind T4, T5 and T11.
- [W-215](../archive/open/W-215-generation-2-corpus.md) — the six-item
  generation-2 specification these items were first listed in.

### Veto condition

**Reopen this decision if:** a measurement comes back empty because its data
lacked an input, and that input is not a `T`-row here — the list missed a class.

**How to check it:** read the *not carried* line in the run's prompt or
report; every input it names must appear in decision 2's table.

---

## References

**Records** — [SR-LAW-0](0002_LAW-0-authority.md) · [L11](0012_LAW-11-sealed-answer-key.md) · [SR-WORK-SCALE](0057_WORK-scale.md) · [SR-WORK-GOLDEN](0066_WORK-golden.md) · [SR-INGEST](0106_ingest.md) · [SR-RANKING](0111_ranking.md) · [SR-RS](0133_predictions.md)

**Work** — [`work/golden/README.md`](../work/golden/README.md) · [`work/golden/prompts/`](../work/golden/prompts/) · [W-215](../archive/open/W-215-generation-2-corpus.md)

**Code** — [`tests/test_test_data_prompts.py`](../tests/test_test_data_prompts.py)
