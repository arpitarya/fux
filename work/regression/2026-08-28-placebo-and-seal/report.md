---
type: Run Report
run: 2026-08-28-placebo-and-seal
classification: informed
date: 2026-08-28
---

# The placebo arm rules out source bias — and the seal cannot rule on anything yet

**The last two never-run controls ran.** ADR-RS decision 15's
`BUILT IS NOT PROVEN` is now discharged for the placebo. **It is not discharged
for the sealed subset**, and this run explains why that is a fact about
*chronology*, not about the control.

## Authorship — classification `informed`

Required from 2026-08-25 (CLAUDE.md §Conformance runs), ADR-RS decision 13.

| artifact | author | could reach |
|---|---|---|
| the `real` enrichment arm | an agent, 2026-08-24 | 🔴 **the queries** — this is the contaminated arm, and it is why the whole run is `informed` |
| the `placebo` arm | `tools/quality-controls/placebo.py`, deterministic from source sha | **none** — no author, no model, no query access by construction |
| the `none` arm | nobody — enrichment removed | **none** |
| the 15/35 seal | `tools/quality-controls/seal.py`, `sha256(id)` | **none** — content-blind and score-blind by construction |
| the harness and this report | Claude Code | everything |

⚠ **The run is `informed` because one arm is**, and the rule sorts rather than
bans. **The `none` vs `placebo` comparison is the exception worth naming: neither
of those two arms had an author with query access**, so that specific delta is
not contaminated by anything. It is the comparison the placebo exists for, and
it is the one this run adjudicates on.

## Harness correctness check, first

**`none` = 32/50 and `real` = 41/50 reproduce
[2026-08-24](../2026-08-24-blind-enrichment-regrade/report.md) exactly.** Two
independently-built harnesses landing on the same two integers is what makes
the third number a comparison rather than a different experiment.

## The three arms

| arm | score | terms in index |
|---|---:|---:|
| `none` — enrichment removed | **32/50** | 750 |
| `placebo` — matched length, content-free, one shared pool | **33/50** | 786 |
| `real` — the committed enrichment | **41/50** | 827 |

Every arm was ingested from a **wiped** `.fux/index` and `.fux/runtime`. ⚠ The
first attempt did not: ingest reported *"0 changed, 10 carried forward"* and all
three arms produced an identical 827-term index, because a copied index is
carried forward on unchanged source shas. **Three arms with identical term
counts is the shape of a harness measuring nothing**, and it is caught here only
because the counts were printed.

## Finding 1 — source bias does NOT explain the lift 🔴

Paired, McNemar exact, per the resolution floor
([ADR-RS](../../../docs/adr/0036_predictions.md) decision 19):

| comparison | net | discordant `n_d` | `b` / `c` | two-sided exact `p` | verdict |
|---|---:|---:|---|---:|---|
| `none` → `placebo` | **+1** | **1** | 0 lost / 1 gained | **1.0000** | 🔴 **no detected change** |
| `none` → `real` | +9 | 9 | 0 lost / 9 gained | **0.0039** | clears α = 0.05 |
| `placebo` → `real` | +8 | 8 | 0 lost / 8 gained | **0.0078** | clears, exactly at the floor |

**~100 words of fluent, domain-plausible, content-free prose added to nine of
ten documents moved exactly one query, and a net of 1 cannot clear α = 0.05 at
any discordant count.**

**So the KDD-2024 source-bias confound is ruled out on this corpus.** The
concern was that enrichment's lift might come from the mere *presence* of
fluent LLM text rather than from what it says. Matched-length text carrying no
information about its document buys **no detected change**. Whatever the `real`
arm is worth, it is worth it for its content.

⚠ **That is not the same as saying the `real` arm's +9 generalises.** The
placebo controls for **source bias**. It does **not** control for
**contamination** — the `real` arm's author had read the queries — and those are
two different confounds. Decision 12 governs the second, and this run does not
discharge it. **The +9 remains `informed` and is not a generalisation estimate.**

### A cross-run observation, labelled as one

2026-08-24 measured **blind** enrichment at **33/50** — the same integer this
run measures the **content-free placebo** at. If that holds, enrichment written
without sight of the queries is worth about what meaningless text of the same
length is worth.

🔴 **This is an observation, not a delta, and it may not be reported as one.**
The two numbers come from different runs, so the comparison is **not paired**;
worse, **no run filed before 2026-08-28 carries per-query rows**, so the
discordant count for that pair cannot be recovered from what was filed and no
test can be run on it by anybody. Stated because it is the most interesting
thing on the page, and fenced because it is not evidence.

## Finding 2 — an OPEN-WORK item was wrong, and the check took one command

The queue has carried this since the resolution-floor ruling:

> ⚠ The `+9` contaminated enrichment delta is the one marked claim that is
> large enough to be testable — **its discordant count was never filed**, so it
> sits in the one bad state: big enough to matter, **impossible to check,
> impossible to re-run (the corpora went in the 2026-08-20 wipe)**.

**Both impossibility claims are false.** The wipe took `acme` and `orbit`; the
`+9` was measured on **`fux-playground`**, which is on the machine. Re-running
it reproduced `32 → 41` exactly, and its discordant count is now filed:

**`n_d = 9`, `b = 0`, `c = 9`, two-sided exact `p = 0.0039`.**

**The `+9` clears the floor** — the table requires a net of 8 at 6–12 flips, and
this is 9. It is *statistically resolvable* and *still informed*: clearing the
resolution floor and being a generalisation estimate are different claims, and
only the first is now settled.

⚠ **The queue rule this instance illustrates is rule 4 — re-derive, do not
read.** An item asserting a measurement was impossible was refuted by attempting
the measurement.

## Finding 3 — the seal RAN, and it cannot adjudicate this artifact 🔴

`seal.py` split the 50 deterministically by `sha256(id)`: **15 sealed, 35
visible**, content-blind and score-blind.

| half | `none` | `placebo` | `real` | `none`→`real` net | `n_d` | `p` |
|---|---:|---:|---:|---:|---:|---:|
| **sealed** (15) | 9 | 9 | 10 | **+1** | 1 | 1.0000 |
| **visible** (35) | 23 | 24 | 31 | **+8** | 8 | 0.0078 |

The lift sits almost entirely in the visible half. **That pattern is what a
contamination signature looks like — and it may NOT be read as one here.**

🔴 **The seal postdates the enrichment by four days.** `seal.py` was written
2026-08-28; the `real` arm was authored 2026-08-24, when its author could see
**all fifty** queries. Nothing was hidden from them. This is a **post-hoc
split of a fully-seen set**, and a post-hoc split cannot test contamination
however cleanly it is computed.

Two further reasons the sealed column carries no verdict:

1. **`n_d = 1`.** Nothing is resolvable in a 15-query half that produced one
   discordant pair, whatever the direction.
2. **The sealed half is known to be harder** — ADR-RS decision 15 records that
   **5 of the 9 `known_failure` goldens landed in the sealed 15** (33 % against
   11 %). A lower lift there is expected before contamination is invoked.

**So the seal is EXERCISED, not PROVEN.** It runs, it is deterministic, it is
integrated into a report. Its first *adjudicating* use must be on an artifact
authored **after** the seal existed, by an author who never saw the sealed half.
**That run has not happened and this one is not it.**

## What this run does NOT establish

- **It does not discharge decision 12.** The `real` arm stays `informed`.
- **It does not re-judge any filed verdict.** 2026-08-24's numbers are
  reproduced, not revised.
- **It proposes no threshold** and touches R10 not at all.
- **It says nothing about 50 000 or 100 000 documents.** Ten documents, fifty
  queries, three orders of magnitude below the design point.

## Evidence

- [`evidence/per-query.csv`](evidence/per-query.csv) — **one row per query per
  arm**, mandatory since 2026-08-28. Every number above is derivable from it,
  including all three discordant counts.
- [`evidence/placebo-arm/`](evidence/placebo-arm/) — the ten generated placebo
  files, so the matched-length claim is checkable.

## Reproduce

```bash
# three arms in a scratch copy; the playground itself is never mutated
cp -R ~/my_programs/fux-playground /tmp/base && rm -rf /tmp/base/.git /tmp/base/.venv
cp -R /tmp/base /tmp/arm_none    && rm -rf /tmp/arm_none/.fux/enrich
cp -R /tmp/base /tmp/arm_placebo && rm -rf /tmp/arm_placebo/.fux/enrich
python3 tools/quality-controls/placebo.py /tmp/base/.fux/enrich /tmp/arm_placebo/.fux/enrich

# ⚠ wipe the derived state per arm, or ingest carries the copied index forward
for a in arm_none arm_placebo base; do
  rm -rf /tmp/$a/.fux/index /tmp/$a/.fux/runtime
  (cd /tmp/$a && python -m fux.cli ingest | tail -2)   # term counts must DIFFER
done

python3 tools/quality-controls/seal.py ~/my_programs/fux-playground/goldens/queries.jsonl
python3 tools/quality-controls/resolution.py 0.05
```
