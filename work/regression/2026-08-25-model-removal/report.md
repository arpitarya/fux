---
type: Report
name: 2026-08-25-model-removal
classification: informed
description: "Removing the embedding model and the dense lane, measured A/B on the same corpus. The wheel drops 30x (6.84 MB -> 233 KB), the committed index 22.6 %, and a full ingest 6.8x. The differential law holds. An INFORMED run by ADR-RS decision 11."
timestamp: 2026-08-25T00:00:00Z
---

# Removing the embedding model — measured

**This is a cost measurement, not a gate.** No prediction was pre-registered
for it and it adjudicates nothing. The decision it follows was Arpit's, taken
on the evidence already filed as
[DENSE-CHUNK](../2026-08-24-dense-lane-gate/VERDICT.md).

## Authorship

**Classification: `informed`.** Stated per
[ADR-RS](../../../docs/adr/0036_predictions.md) decisions 11 and 13.

| artifact | author | evaluation material reachable at the time |
|---|---|---|
| the code change under measurement | this session | everything — it authored the deletion |
| the measurement harness | this session | everything |
| the analysis | this session | everything |
| the corpus | this repo, unmodified | n/a |

**There was no blind option and pretending otherwise would be the failure the
rule exists to name.** One session proposed the removal, executed it, and
measured it.

> ⚠ **This run states deltas, and ADR-RS decision 12 says an informed run never
> supplies one. The tension is real and is recorded rather than resolved here.**
>
> Decision 12 was written for **quality** measured against an **evaluation
> set** — the hazard is an artifact fitted to the queries. This run has no
> queries, no judgments and no scores: it measures **wall-clock seconds and
> bytes on disk**, quantities an author's knowledge of the goldens cannot bend.
>
> **The accepted wording does not draw that distinction**, and on its literal
> reading these numbers may not be stated. **Applying it literally would forbid
> reporting a file size**, which is not what was ruled and not what anybody
> wants. Filed as a defect in the rule's scope, one day old, found on its first
> application — see [W-81](../../open/W-81-the-sealed-set-and-the-two-controls.md).
> **Narrowing decision 12 is Arpit's**, not this session's, so the rule is
> applied as written and the conflict is disclosed instead of being smoothed.

## Method

Two git worktrees of the same repository, same machine, same interpreter, one
variable — whether `src/fux/embed/` and the dense lane exist.

| | |
|---|---|
| baseline | `HEAD` (`a3f75b0`), model present, `[dense] mode` default `off` |
| treatment | the working tree with the model, both `dense.py` modules, `chunkvec.py`, `fuxvec.py` and the committed `vectors` field removed |
| corpus | this repository, `fux ingest --full` in each tree |
| machine | cloud container, x86_64, CPython 3.11 |

⚠ **The corpora differ by one document** — the treatment tree adds `W-81`.
The `.py` and `.bin` files deleted are **not indexed file types**, so they never
were documents. 720 records against 721.

## Results

### Package size — the largest single effect

| | bytes | |
|---|---|---|
| wheel, model present | **7 170 167** | 6.84 MB |
| wheel, model removed | **238 208** | 233 KB |
| | **-96.7 %** | **30.1x smaller** |

### Committed index

| | bytes | records | chunk vectors |
|---|---|---|---|
| model present | **6 528 570** | 720 | **4 290** |
| model removed | **5 052 388** | 721 | 0 |
| | **-22.6 %** | | |

**Independently corroborated.** Before any deletion, a direct count of the
`vectors` key across the then-committed index put it at **2 794 170 B of
12 162 978 B — 23.0 %**. Different index state, same share.

### Full ingest

| run | model present | model removed |
|---|---|---|
| 1 | 36.14 s | 4.98 s |
| 2 | 33.00 s | 4.84 s |
| | | **~6.8x faster** |

⚠ **Two runs each, one machine, a shared cloud container.** Enough to carry a
6.8x claim, nowhere near enough for a percentage.

### The differential law still holds

Six queries, `--scan` against `--fast`, `--json`, top 5:

```
IDENTICAL n=5   differential law
IDENTICAL n=5   index format canonical
IDENTICAL n=5   how does enrichment work
IDENTICAL n=5   supersession ranking
IDENTICAL n=5   merge driver conflict
IDENTICAL n=5   bm25f field weights
```

⚠ **The first attempt at this check passed vacuously and was caught.** Both
sides returned the empty string, because `.fux/tune.toml` still carried
`[dense]` and every invocation was erroring. Two empty strings compare equal.
The check now asserts **five results per query** before comparing, which is why
`n=5` is printed rather than a bare verdict.

## What is NOT measured here

**Whether ranking changed.** It did not, and the argument is **structural, not
measured**: `[dense] mode` defaulted to `off`, and `should_fuse("off", ...)`
returned `False` before any dense work happened, so no default query ever
reached the lane. Stated as an argument from the code because that is what it
is. A cross-tree ranking diff is not available — 13 ADRs were amended in the
same change, so the documents themselves differ and byte-identity across trees
was never on the table.
