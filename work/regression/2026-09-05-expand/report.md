---
type: Run Report
run: 2026-09-05-expand
classification: informed
date: 2026-09-05
---

# W-109's gate — `--expand`, with the expansions written by an author blind to the judgments

**16 fixed, 0 broken.** The bar was **net ≥ 6 discordant** and **0 broken among
goldens that pass without expansion**; both are met, and the margin is not
marginal.

## Authorship — classification `informed`

| artifact | author | could reach |
|---|---|---|
| the 50 goldens' questions and relevance sets | pre-existing (playground); the sets by two mutually blind sessions, κ = 0.960 | — |
| 🟢 **the 50 expansions** | **a separate agent session with a fresh context**, 2026-09-05 | **the 10 corpus documents and the 50 question strings — nothing else.** No `doc`, no `relevant` list, no `known_failure` note, no prior score, no report |
| 🔴 the feature, the harness and this report | Claude Code, this session | everything, including the judgments |

**Why the run is `informed` even though its expansions are blind.**
CLAUDE.md's rule is that **every** artifact — *"and the analysis"* — must be
authored without access. The analysis is this session's, and this session has
read the judgments. So: `informed`, and **not a generalisation estimate**.

⚠ **What "blind" means here, exactly, and its limit.** The expansion author was
given `{"id","q"}` per query (`evidence/blind-queries-as-given.jsonl`, filed as
handed over) and the corpus, and was instructed in writing not to open the
goldens, run any search or evaluation, or read anything under the fux or
playground repositories. **Compliance is asserted by that agent and was not
mechanically verified.** An expansion author must see the *question* — that is
the task — so this is blindness to **judgments**, which is what W-109's
definition of done asks for, and not to queries, which is impossible here.

## The corpus is the re-derived one

Same corpus as [`2026-09-05-vector-gate`](../2026-09-05-vector-gate/report.md):
`fux-playground` re-derived from its ten committed documents, **no enrichment**,
because the playground's committed index is `fux.index.v1` (unreadable by this
engine) and its enrichment files were never committed. Base grade **28 / 50**.

⚠ **This is a paired before/after on one corpus state**, which is what the gate
needs. No absolute number here is comparable with a run measured on the
enriched corpus.

## The bar, written in W-109 before the run

> Gate filed: a **blind** author writes expansions for the 50 goldens without
> seeing judgments; per-query rows; **net ≥ 6 discordant; 0 broken** among
> goldens that pass without expansion.

## The result

| arm | pass | | |
|---|---|---|---|
| `base` — `fux ask --json`, as it ships | **28 / 50** | | |
| `expand` — the same, plus the blind author's expansion | **44 / 50** | | |

| | count | ids |
|---|---|---|
| **fixed** | **16** | `q005 q006 q013 q017 q018 q020 q026 q028 q029 q032 q034 q035 q043 q044 q049 q050` |
| **broken** | **0** | — |
| discordant | 16 | net **+16** |

**Resolution.** 16 discordant, 16–0. The paired bar
([ADR-RS](../../../docs/adr/0036_predictions.md) decision 19) puts the floor at
6 for a net; a 16–0 split clears it by a wide margin and is not a
below-resolution result.

## The population the feature exists for

**6 of the 9 `known_failure` goldens now pass, and 0 of them passed before.**
Those nine are the hand-annotated vocabulary-gap failures — `q006`'s note is
the archetype: *"the document never says the query's noun. The target is titled
'checkout unavailable for 47 minutes'; the query asks about the 'outage', a
word that appears nowhere in it."*

That is the claim W-109 was built on, measured: **an agent that has read the
corpus can close a vocabulary gap that no weighting can reach.**

⚠ **And it is the claim with the largest caveat.** The blind author read all
ten documents before writing the expansions. On a 10 000-document corpus no
agent reads everything, and this run says **nothing** about how well an
expansion written from a partial view performs. That is the next measurement,
and it is not this one.

## The guard held

**0 broken**, and no expansion pulled in a document that matched none of its
query's own terms — `rank()` drops those before they are scored
(ADR-EXPAND decision 3). The guard is asserted directly in
`tests/query/test_expand.py` on both candidate paths; this run is the evidence
that it does not cost recall in practice.

## Reproduce

```bash
E=work/regression/2026-09-05-expand/evidence
python $E/expand_bench.py <corpus> <path-to>/fux/src \
    ~/my_programs/fux-playground/goldens/queries.jsonl \
    $E/blind-expansions.jsonl /tmp/rows.csv
```

The corpus is a copy of `fux-playground` with `docs` restored to
`.fux/sources/dirs` and re-ingested; **the playground itself was not modified.**

## Evidence

- `evidence/per-query.{csv,jsonl}` — **50 rows**: base rank, expanded rank,
  pass per arm, the expansion used, and both top-5 lists.
- `evidence/blind-expansions.jsonl` — every expansion, as written.
- `evidence/blind-queries-as-given.jsonl` — exactly what the blind author was
  handed, so the claim about what it could reach is checkable.
- `evidence/expand_bench.py`, `evidence/summary.txt`.

## Nothing is claimed at 10 000 documents

Ten documents, 50 questions, one corpus state, one machine.
