---
type: Pre-registration
description: "Re-registration of W-168 step 5, RM3. It is the 2026-09-23 pre-registration in every row except one: RM3's ten feedback documents are the graph-boosted top 10 that `ask` shows, not the lexical top 10. Arpit ruled the re-run on W-221 (2026-09-25). Written before the build and before any treatment number exists."
run: 2026-09-25-rm3-boosted
item: W-221
filed: 2026-09-25
measured: "not yet"
classification: informed
supersedes_mechanism_of: work/regression/2026-09-23-rm3/PRE-REGISTRATION.md
---

# Pre-registration: RM3 on the boosted first pass (W-221 re-run)

## Why this run exists

The [2026-09-23 run](../2026-09-23-rm3/VERDICT.md) was ruled **FAIL, drift**. Its
verdict names one reopen route: *"only if ANALYSIS §1 is overturned, and then
by a **new run**, never by re-reading this one."* That run fed RM3 the
**lexical** top 10, while `ask` on `rung-01000` (where `ask_boost = true`)
shows a **graph-boosted** top 10.

[W-221's check](../2026-09-23-rm3/evidence/first-pass-check.md) measured the
difference between those two lists:

- rank 1 is the same on 124 of 125 questions
- the ten documents differ on 73 questions
- 2–6 of the 10 feedback terms differ on 35 questions

**Arpit ruled the re-run on 2026-09-25**, answering W-221: *"re-run"*.

## Frozen by reference, byte for byte

**Every row of
[`2026-09-23-rm3/PRE-REGISTRATION.md`](../2026-09-23-rm3/PRE-REGISTRATION.md)
at commit `d9bd57a6` holds here unchanged, except §The one change below.** That
covers:

- **the endpoint:** `hit@1` gates; `primary@1` is reported beside it
- **the feedback counts and term score:** `FB_DOCS = 10`, `FB_TERMS = 10`, the RM1 term score, the tie-break, scoring through `expand.build`
- **the arms and their order:** `rm3_weight ∈ {0.1, 0.2, 0.3, 0.5}` against `0.0`, tried ascending
- **the held values:** the index, `k1`, `b`, the field weights, `anchor = 0.0` pinned in the rung's `tune.toml`, `rerank_weight` and `expand_weight`
- **the data:** `set-2-u` and `rung-01000`, index root `17fe414e52d2…`
- **the harness:** `golden_run.py`, `ask --json --band --why --top 10` plus `answer --json`, no `--expand`
- **the tag:** unchanged, and not re-tagged
- **the pool:** unchanged and not re-counted — 39, no STOP
- **the decision rule and verdict table:** unchanged, with no threshold moved ([SR-RS](../../../records/0133_predictions.md) d10b)
- **§What this run may NOT do:** items 1–8 unchanged

Hashes checked on 2026-09-25, before this file was written:

| input | sha256 |
|---|---|
| `work/golden/questions/set-2-u.jsonl` | `274f89cc…74fc47e` |
| `2026-09-23-rm3/evidence/tags-set-2-u.jsonl` | `b6145354…ebc891487` |
| `2026-09-23-rm3/evidence/tag_underspecified.py` | `f1e68379…c1cac9cbd` |

## The one change

| | 2026-09-23 | **this run** |
|---|---|---|
| feedback documents | the top 10 of the **lexical** pass: `scan`/`accel` `ask`, un-expanded, before rerank, pin and graph tier | the top 10 **as `ask` would show them without RM3**: the same un-expanded window, then rerank, then pin, then the graph tier (Tier A), taking `FB_DOCS = 10` |
| `P(q|d)` | the document's first-pass score, normalised over the ten | **unchanged in definition.** The boost reorders but keeps each document's lexical score ([`compose._boost`](../../../src/fux/query/compose.py)), so the score is the same number |
| when the tier is off (`ask_boost = false`) | the lexical top 10 | the same top 10, since the two lists are then identical by construction, and a test asserts it |

**Why this and not another:** this is the reading the 2026-09-23 rationale
gave: *"exactly the `--top 10` list the harness already captures."*

- **No new tunable.** The first pass follows the tune in force, as the final pass does.
- **Carried unchanged:** a caller's `--expand` still wins, and the first pass still writes no stats and prints no graph note.
- **Both readers change in the same commit**, Python and Node, with byte equality across scan, accelerator, Node reader and bundle.

## The arms

The same five weights, **all captured fresh at ONE engine commit**: the build's.
**None of the 2026-09-23 captures is reused**, not even `rm3-0.0`, because that
run was at `36c913c7`
([SR-RS](../../../records/0133_predictions.md) d21c).

## What this run may NOT do, in addition

1. **Compare with the 2026-09-23 arms as if they were arms of this run.** A
   side-by-side row may be reported after scoring, and gates nothing.
2. **Be adjudicated by this session.** This session captured the arms and ran
   W-221's ranking comparison, so the verdict goes to a session that did
   neither. **INCONCLUSIVE goes to Arpit.**

## If it passes

Exactly as §If it passes of the 2026-09-23 pre-registration: the first clearing
value ships as the default, with the records amended in the same change. The
mechanism that ships is **this** one.
