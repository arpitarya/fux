---
type: Report
title: R10 — the separation floor, measured against the frozen pre-registration
description: "The curve reaches t = 0.75 at separation 0.3, FALLS BACK at 0.4, then rises. Two frozen rules disagree about what that means, so the outcome is AMBIGUOUS and is handed to Arpit rather than adjudicated."
classification: informed
timestamp: 2026-08-27T17:05:00Z
---

# R10 — the separation floor

**Prediction:** R10 · **Pre-registration:**
[`evidence/PRE-REGISTRATION.md`](evidence/PRE-REGISTRATION.md), frozen
2026-08-27 and **not edited by this run**.

> ⚠ **The outcome is AMBIGUOUS.** Two rules frozen in the same document give
> two different answers on this data. `CLAUDE.md` §A pre-registered threshold
> may never move says an ambiguous result is written up and **handed to Arpit**,
> not adjudicated, and not resolved by restating the threshold in looser words.
> This report does not pick.

## Conditions, as frozen

| condition | met |
|---|---|
| corpus `fux-playground`, committed 50 goldens, unmodified | ✅ |
| every arm **unenriched** (`.fux/enrich` absent) | ✅ moved aside for the run, restored after |
| `.fux/tune.toml` at defaults | ✅ moved aside, restored after |
| `fux ingest --full && fux build` once; one index, no arm changes a byte | ✅ |
| ten equal bins of 0.1, fixed before the data existed | ✅ not re-binned |
| classification **`informed`** | ✅ — see §Authorship |

⚠ **The playground's committed index could not be read at all when this
started.** It was `fux.index.v1`; the engine writes `fux.index.v2`. All 50
goldens returned `shard missing/mismatched _format header`. A full re-ingest was
required before any measurement could run — see [`ANALYSIS.md`](ANALYSIS.md) §2.

## The measurement

**n = 50 goldens · 28 correct** under frozen (unenriched, default-tune)
conditions.

| bin | n | correct | P(correct) | note |
|---|---:|---:|---:|---|
| `[0.0,0.1)` | 18 | 8 | **0.44** | |
| `[0.1,0.2)` | 11 | 5 | **0.45** | |
| `[0.2,0.3)` | 6 | 3 | **0.50** | |
| `[0.3,0.4)` | 4 | 3 | **0.75** | ⚠ n=4 — reaches `t` exactly |
| `[0.4,0.5)` | 5 | 3 | **0.60** | ⚠ **falls back below `t`** |
| `[0.5,0.6)` | 3 | 3 | **1.00** | ⚠ n=3 |
| `[0.6,0.7)` | 2 | 2 | **1.00** | ⚠ n=2 |
| `[0.7,0.8)` | 1 | 1 | **1.00** | ⚠ n=1 |
| `[0.8,0.9)` | 0 | 0 | — | empty |
| `[0.9,1.0)` | 0 | 0 | — | empty |

- **`separation == 1.0`: n = 0.** The frozen special case never fired — no query
  on this corpus produced exactly one scoring document. Reported because the
  pre-registration requires it, and it is a structural fact about the corpus.
- **Monotone non-decreasing across occupied bins: `False`.**
- **Lowest bin reaching `t` and staying at or above it for every higher bin:
  `0.5`.**

## Why this is ambiguous

The pre-registration froze **two** rules, and on this data they disagree.

| frozen text | reads this data as |
|---|---|
| §The measurement: *"the lowest `separation` at which observed `P(correct)` reaches `t = 0.75` **and stays at or above it for every higher bin**"* | a floor of **0.5** — outcome **A** |
| §Frozen verdict rules, row 4: *"Crossing exists but non-monotone → too noisy to read → **no change**"* | outcome **D**, no change |

**Both descriptions fit.** The curve crosses `t` at `0.3` and falls back at
`0.4`, which is non-monotone (row 4); it also has a highest contiguous run at
or above `t` beginning at `0.5` (§The measurement).

⚠ **This is a defect in the pre-registration, not in the data**, and it is the
kind that only appears once real numbers exist. Naming it is the point of
freezing the document first.

## Power — and why it dominates either reading

The pre-registration said this run *"cannot resolve a boundary to better than
about ±0.2 in `separation`"*. **The data is worse than that at the top.**

- Bins at or above `0.5` hold **6 queries in total** (3 + 2 + 1). A floor of
  `0.5` would rest on six observations.
- The bin that first reaches `t` holds **4**. Three of four correct is `0.75`
  exactly; one query moving either way makes it `0.50` or `1.00`.
- The top two bins are **empty**, so the curve says nothing at all above `0.8`.

**Whatever Arpit rules, no reading of this table supports shipping a constant.**
The pre-registration already says so: *"a crossing yields a recommendation plus
the named blocker, not a shipped constant."*

## What did NOT happen

- **`SEPARATION_FLOOR` was not changed.** It remains `0.10`.
- **No test was edited.** `tests/query/test_confidence.py` asserts the rule
  relative to the constant and never its value, exactly so this run could land
  without touching it.
- **The pre-registration was not edited**, including to fix the contradiction
  §Why this is ambiguous names. W-82 ruling 8: a frozen pre-registration is
  never touched, and the correction lives in the record that cites it.
- **The floor is not called "calibrated."** `separation` is ordinal; the
  pre-registration fixed this wording in advance and it is honoured.

## Authorship

**`informed`, as the pre-registration itself declared in advance** — there is no
blind option here and none is pretended.

| artifact | author | could reach |
|---|---|---|
| the corpus and its 10 documents | prior sessions, 2026-08-20 | — |
| the 50 goldens | drafted by an agent 2026-08-24, **human-author rule waived by Arpit** | the corpus |
| the enrichment | **absent from this run by construction** | — |
| the harness, the run, this analysis | Claude Code (Opus 5), 2026-08-27 | the pre-registration **and the goldens** |

⚠ **No delta is stated in this report**, against a blind run or any other. The
28/50 figure is a property of these frozen conditions and is reported as a
condition of the curve, not as a comparison.

## Reproduce

```bash
cd ~/my_programs/fux-playground
mv .fux/enrich /tmp/ && mv .fux/tune.toml /tmp/      # the frozen conditions
.venv/bin/python -m fux.cli ingest --full && .venv/bin/python -m fux.cli build
.venv/bin/python <fux>/work/regression/2026-08-27-r10-separation-floor/evidence/harness.py
mv /tmp/enrich .fux/enrich && mv /tmp/tune.toml .fux/tune.toml && \
  .venv/bin/python -m fux.cli ingest --full        # restore
```

`evidence/render.py per-query.json` re-renders the table from the saved data
without re-measuring — which is deliberate, because running the harness against
the playground's normal enriched state writes a different table under the same
filename. That happened once while this run was being filed.
