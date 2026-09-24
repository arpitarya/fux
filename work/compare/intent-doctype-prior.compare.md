---
type: Compare Doc
title: "W-168 step 9 — the intent → doc-type prior: where a document's type is declared, how a question's intent is read, and whether step 3's intent joins it"
description: "Step 9 starts as a compare doc (proposal §2). Three forks decide whether it can be measured at all: where the doc-type is declared (per source, front-matter, or a query-time glob table), how intent is read from a question (a fixed engine cue lexicon or consumer cues), and whether the history/current intent that foreclosed step 3 becomes part of this step. Measured first: the golden seed declares no type anywhere — 0 of 32 front-matters carry one, and every seed sits in one source directory — so only a query-time table can be tested without changing the frozen ladder. Proposed, not ruled."
status: parked — the measured pool is below 6 (2026-09-24); forks deferred
timestamp: 2026-09-24T00:00:00Z
filed: 2026-09-24
---

# The intent → doc-type prior — W-168 step 9

**Model: Opus** — a prior that moves rank 1 on a class of question is a
bias; whether it is the *right* bias is the whole question.

**Graduates:** [`proposals/search-improvements-v3.md`](../proposals/search-improvements-v3.md)
idea #9 — *"'how do I…' prefers runbooks, 'why did we…' prefers records;
declared per source"*, which says it *"starts as a compare doc"*.
**Owning records:** [SR-RANKING](../../records/0111_ranking.md),
[SR-TUNE](../../records/0135_tuning.md), [SR-ASK](../../records/0103_ask.md),
[SR-RS](../../records/0133_predictions.md) (the measurement).
**Item:** [W-168](../open/W-168-search-improvements.md) step 9.

---

## Verdict block

| | |
|---|---|
| **status** | ⏸ **parked 2026-09-24** — the I1-tagged pool on generation 2 is **2 (set-2-u) and 1 (set-3-u)**, below 6 at every `k` ([pools](../regression/2026-09-24-golden-gen2-rung-01000/report.md)). By this doc's own stop rule the step stops before any build, so the three forks are **deferred, not refused** |
| **the call, recommended** | **D2 · I1 · M1, and step 3's intent stays OUT (S1).** A committed glob → type table read at query time, a fixed engine cue lexicon for three intents, one multiplicative weight at `0.0` by default |
| **confidence** | medium on D2 (it is the only option testable on the frozen ladder); low that step 9 clears the floor — see *What the pool can be* |
| **endpoint (already ruled)** | `hit@1`, `primary@1` beside it (Arpit, 2026-09-23) |
| **reopen-trigger** | at the foot |

---

## Context

**What is measured before any option is argued** (2026-09-24, from
`work/golden/seed/` alone — the one part of `work/golden/` a session may read):

- **0 of 32 seed front-matters declare a type.** Every one carries `title`,
  `status` and `owner`; 28 carry `doc_id`. No `type:`, `doc_type:` or `kind:`.
- **Every seed document is in one source directory** (`seed/`, plus
  `seed/archive/` declared `archived=true`). A per-source declaration cannot give
  a runbook and a decision record different types there.
- **The type IS written down — in the file name.** `01-sop-…`,
  `03-postmortem-…`, `05-decision-…`, `07-rate-card-…`, `08-…-policy`,
  `09-…-wiki-export`, `10-new-joiner-faq`, `23-mapping-study-…`,
  `27-lane-qualification-…`, `30-…-checklist`, `31-…-procedure`.
- **The ladder's paths are part of the key**, so any option that moves or
  renames a document, or edits its bytes, changes what the frozen answers
  point at.

**The rule the proposal set:** *declared, not inferred; an undeclared repo is
byte-identical*. On FAIL the declaration key stays and the weight is `0`.

---

## Fork 1 — where a document's TYPE is declared

| | D1 · per source | D2 · a glob → type table in `.fux/tune.toml` | D3 · front-matter `type:` |
|---|---|---|---|
| shape | `runbooks/ type=runbook` in `.fux/sources/dirs` | `[doctype]` · `"**/*-sop-*" = "procedure"` | `type: runbook` in each document |
| read at | ingest (a record field) | **query time** | ingest (a record field) |
| undeclared repo byte-identical | ✅ | ✅ | ✅ |
| changes `.fux/index/` when declared | ✅ yes — a re-ingest | ❌ **no** — like `[priority]` | ✅ yes — a re-ingest |
| testable on the frozen ladder | ❌ one directory holds every seed | ✅ **the arm's own `tune.toml` copy; no document or path moves** | ❌ edits 32 seed documents, which is a new ladder |
| precedent | `archived=` on a source line | `[priority]` — an open table keyed by the consumer's own paths | `aliases:`, `doc_id:` (SR-INGEST 23) |
| cost to a consumer | one line per folder | one line per naming convention | one line per document |
| drift risk | low | ⚠ a renamed file silently changes type | low |

**Recommend D2.** It is the only one of the three that can be measured
without building a new ladder, and it is the shape `[priority]` already
established: a committed, consumer-keyed table read at query time, with an
empty table as the default. ⚠ **Its cost is real:** the type follows the file
*name*, so a rename changes it with nothing to notice. D1 and D3 are
not refused — either can be added later as another source of the same type, if a
consumer's corpus is shaped for it.

## Fork 2 — how a question's INTENT is read

| | I1 · a fixed engine cue lexicon | I2 · consumer cues in `tune.toml` | I3 · a classifier |
|---|---|---|---|
| shape | ~3 intents, each a short list of opening phrases (`how do i`, `how to`, `steps to` → *procedure*; `why did we`, `why was`, `rationale` → *rationale*; `what is`, `what does … mean`, `define` → *reference*) | the same table, written by the consumer | a model |
| deterministic | ✅ | ✅ | ❌ |
| laws | ✅ | ✅ | ❌ L1 (`$0`, no hosted model) for the default path |
| a restatement risk | the lexicon lives in ONE module, bound by a test | — | — |
| taggable from question text alone ([SR-WORK-TESTDATA](../../records/0068_WORK-test-data.md) T2) | ✅ **the same lexicon tags the pool** | only once a consumer writes one | ❌ |

**Recommend I1**, with I2 left for later: the pre-registration needs a tag
computable from the question text alone, and I1 *is* that tag. A cue lexicon
is English-only and misses paraphrase. Both are properties of the
mechanism, so they are named in its record rather than worked around.

## Fork 3 — does step 3's intent join this step?

Step 3 (supersession) is **foreclosed**, and the ruling that foreclosed it
points here: *"Supersession belongs to the query's intent, not to the
document"* (Arpit, 2026-09-11). A *history-seeking* question wants the
superseded document; a *current-seeking* one wants its successor.

| | S1 · keep them apart | S2 · one step, four intents |
|---|---|---|
| step 9 measures | procedure / rationale / reference → doc-type | the same **plus** history / current → `superseded` |
| one mechanism per arm (W-168's rule) | ✅ | ⚠ two mechanisms behind one weight |
| a FAIL says which half failed | ✅ | ❌ |
| cost | step 3's intent waits for its own step | none now; an unreadable verdict later |

**Recommend S1.** W-168's standing rule is *one step per measurement*, and a
combined arm that fails cannot say which half failed. **This is a scoping call
and it is Arpit's**, as the identifier work becoming one subject was.

## The mechanism — M1

`[ranking] intent_weight`, default **`0.0`**. When the question's intent (I1)
matches a document's declared type (D2), that document's score is multiplied
by `1 + intent_weight`. A multiplicative prior, not a filter, and not a
term. Off at `0.0` means the lexicon is never consulted, which the test holds
byte-for-byte (the way RM3's `0.0` was held).

## What the pool can be — measured where possible, and the rest disclosed

- The pool is **tagged ∩ in the baseline top 10 ∩ missing rank 1**, among
  answerable questions. The tag is I1 over question text; the other two
  terms need a **scored baseline on the rebuilt ladder** —
  [`2026-09-24-golden-gen2-rung-01000`](../regression/2026-09-24-golden-gen2-rung-01000/report.md),
  whose scoring is Arpit's.
- ⚠ **On the retired sets, intent was abundant** (50 current-seeking and 17
  history-seeking tags) — **but those are fork 3's intents**, which S1 leaves
  out. How many generation-2 questions carry a *procedure / rationale /
  reference* cue is unknown until the lexicon exists. **Below 6 in the pool,
  the step stops** (W-219's floor) — before any build.

## Consequences of the recommendation

- A new open table, `[doctype]`, and one new key, `[ranking] intent_weight`.
  SR-TUNE and SR-RANKING amended; `fux ask --why` names the prior when it moves a
  score, as it names `archived_weight`.
- The treatment arm is a copy (`arm_corpus.py`) whose `tune.toml` carries a
  `[doctype]` table **written from file names alone and frozen in the
  pre-registration**. The frozen rungs are never edited.
- ⚠ **Python and Node both**, as every ranking key is.

## References

- [`proposals/search-improvements-v3.md`](../proposals/search-improvements-v3.md) §1 idea #9, §3b
- [W-168](../open/W-168-search-improvements.md) — the 2026-09-23 endpoint ruling; §Step 3 foreclosed
- [VERDICT-W143](../regression/2026-09-12-priors-and-tables/VERDICT-W143.md) — why supersession is intent
- [SR-TUNE](../../records/0135_tuning.md) decisions 8–9a — `[priority]`, the precedent D2 follows
- Broder, *A taxonomy of web search*, SIGIR Forum 2002 — navigational /
  informational / transactional intent, the canonical case for reading intent
  off the query rather than the document

## Reopen-trigger

- **The pre-registered run FAILs** → `intent_weight` stays `0.0`, `[doctype]`
  stays as a declaration, and this doc records the failed direction.
- **The I1-tagged pool on generation 2 is below 6** → the step stops before any
  build, and the trigger becomes *a question set whose tagged pool is ≥ 6*.
- **A corpus arrives whose types are declared per folder or per document** →
  D1 or D3 is re-weighed as an additional source of type, never as a
  replacement for D2.
