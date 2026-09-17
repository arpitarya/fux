---
type: Regression Run
name: identifier-survival
description: "W-168 step 2's premise, checked before anything is built. 0 of 33 distinct identifiers survive the analyzer whole; 3 are MANGLED — DAIRY-2 becomes `dairi`, a string no document contains. And 4 of 249 questions carry an identifier, which is below the floor of all floors, so the feature cannot be given a verdict on this corpus."
run: 2026-09-16-identifier-survival
item: W-168
classification: informed
status: complete
timestamp: 2026-09-16T00:00:00Z
---

# Do identifiers survive the analyzer, and can this corpus test the fix?

**A precondition check, not an arm. One configuration, no comparison, no bar.**

[The proposal](../../proposals/search-improvements-v3.md) §0 is explicit:
***"Build the golden question before the feature, or the verdict is theatre."***
So this asks the two questions that decide whether step 2 may start.

**Reproduce:**

```bash
.venv/bin/python tools/quality-controls/identifier_survival.py --json-out evidence/survival.json
```

**Not a paired run** — one analyzer, one pass, no arms — so
[SR-RS](../../../records/0133_predictions.md) decision 22's paired headroom does
not apply and none is faked.

⚠ **No per-query rows, because this run runs no queries.** Decision 15's unit
does not exist here: nothing was asked and nothing was ranked. **What it files
instead is one row per IDENTIFIER** — [`evidence/per-identifier-rows.jsonl`](evidence/per-identifier-rows.jsonl),
33 of them, each with its produced tokens, whether it survived whole, whether it
was mangled, and its separator. Every count below is derivable from those rows
and from nothing else, which is what decision 15 is actually for.

---

## 1 · The premise is TRUE, and worse than stated

Idea #3 asserts *"the stemmer mangles ids"*. Measured over the 33 distinct
identifiers in the 20 seed documents:

| analyzer outcome | count |
|---|---:|
| **survives whole** | 🔴 **0 of 33** |
| split into parts | **33** |
| **MANGLED — a letter lost** | **3** |

**Not *some*. Zero.** Every identifier in the corpus is broken into pieces
before it reaches a posting.

### The three that are worse than split

| identifier | what the analyzer produces |
|---|---|
| `DAIRY-2` | `['dairi', '2']` |
| `KFS-2014` | `['kf', '2014']` |
| `QCL-OPS-DOCK-03` | `['qcl', 'op', 'dock', '03']` — **`OPS` became `op`** |

🔴 **`DAIRY-2` becomes `dairi`, which appears nowhere in the document.** The
stemmer ran on a fragment of an identifier and produced a string that is not in
the corpus and is not what anybody types. **A query spelled the way a person
spells it cannot reach that piece at all** — and `KFS` losing its `S` is the same
failure.

⚠ **Split and mangled are different failures and the report separates them.**
Split leaves the parts matchable, so `RF-118` is still reachable through `rf` and
`118` — badly, because `rf` also matches everything else beginning `RF`. Mangled
leaves nothing to match.

### The asymmetry nobody had written down

**The separator decides the outcome.** A spot check during this run:

```
ERR_2031  ->  ['err_2031', 'err', '2031']     # underscore: survives whole, PLUS its parts
RF-118    ->  ['rf', '118']                    # hyphen: split, nothing whole
```

**`ERR_2031` survives and `RF-118` does not, purely because of the separator.**
That is not a decision anybody made; it is what the tokenizer happens to do, and
it means the corpus's ids are covered or not by an accident of punctuation.

## 2 · 🔴 But the corpus CANNOT give this feature a verdict

| question set | questions | carrying an identifier |
|---|---:|---:|
| set 1 (Codex) | 125 | **4** |
| set 2 (Claude) | 124 | **0** |
| **total** | **249** | **4** |

**4 is below [SR-RS](../../../records/0133_predictions.md) decision 19's floor of
all floors.** A net of 6 is the minimum that can clear α at *any* discordant
count, and **4 questions cannot produce 6 flips**. So no arm on this set can
return a result, whatever the feature does.

🔴 **That is a DATA DEFECT (decision 23b), fixed in the data — never filed as a
null.** It is the same shape as [W-191](../../open/W-191-the-ladder-carries-no-links.md)'s
zero `ref` edges, caught **before** a measurement was spent this time rather than
after.

⚠ **The documents are fine; the questions are the gap.** 51 identifier tokens
across all 20 seed documents is a real population — unlike the link case, where
the *input itself* was missing. **Only the questions need writing**, and they are
Codex's.

## 3 · What this decides about step 2

1. ✅ **The feature is justified.** Its premise is measured, not asserted, and it
   is stronger than the proposal claimed.
2. 🔴 **It may not be built yet**, by the proposal's own §0 rule: the golden
   questions come first or the verdict is theatre. **4 of 249 is theatre.**
3. **The request is [prompt 8](../../golden/prompts/8-codex-identifier-questions.md)** —
   id-queries over the identifiers the seed corpus already contains, written by
   Codex.
4. ⚠ **The design fork is named and NOT taken here.** An unstemmed identifier
   field needs committed postings, so it is a `_format` change
   ([SR-INDEX-LIFECYCLE](../../../records/0108_index-lifecycle.md) decision 9.1) —
   unlike the anchor field, which folds at read time and cost no bump. **Whether
   it rides 3.0's existing unreleased bump is a decision, and it belongs in the
   build's pre-registration, not in a precondition check.**

## What this run does NOT establish

- **Nothing about ranking.** No query was run and no arm exists.
- **Nothing about whether the field would help**, only that its premise holds and
  its verdict is currently unreachable.
- **Nothing about other corpora.** `informed`, and the seed corpus is Codex's.

## Authorship

| what | who |
|---|---|
| the seed corpus and its identifiers | **Codex**, prompt 1 |
| the question sets | **Codex** (set 1) and **Claude** (set 2) |
| this instrument | this session |

**`informed`.** The instrument's author reads the results, and it counts tokens
in a corpus this project's sessions read.
