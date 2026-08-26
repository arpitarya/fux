---
type: Report
name: 2026-08-25-supersession-and-reranker-default
classification: informed
description: "The supersession prior fires for the first time since it shipped — and FAILS its bar. It fixes q015, the canonical failure it was designed for, and breaks four queries whose correct answer IS the superseded document. Separately, the reranker reproduces +4 / 0 broken exactly."
timestamp: 2026-08-25T00:00:00Z
---

# The supersession prior, exercised for the first time — and the reranker default

Method frozen before any number existed:
[`evidence/PRE-REGISTRATION.md`](evidence/PRE-REGISTRATION.md), committed in its
own commit ahead of the run.

## Authorship

**Classification: `informed`** (ADR-RS decisions 11 and 13), declared in the
pre-registration before measuring.

| artifact | author | evaluation material reachable |
|---|---|---|
| the `supersedes:` frontmatter line | this session | **everything** — `q015` known by id and by mechanism |
| tune configuration, harness, analysis | this session | everything |
| the corpus and the 50 goldens | pre-existing, unmodified | — |

**No blind option existed.** What limits the exposure: the only corpus edit is
**one line asserting a relation the document's own prose already states twice**,
and **arm A1 exists to measure exactly that edit's effect.**

## Result

All arms unenriched. 50 goldens.

| arm | `supersedes:` | `superseded_weight` | `rerank_weight` | pass |
|---|---|---|---|---|
| A0 baseline | no | 1.0 | 0.0 | **28 / 50** |
| **A1 control** | **yes** | 1.0 | 0.0 | **28 / 50** |
| A2 | yes | 0.5 | 0.0 | 28 / 50 |
| A3 | yes | 0.25 | 0.0 | **26 / 50** |
| B0 | no | 1.0 | 0.0 | 28 / 50 |
| **B1** | no | 1.0 | **1.0** | **32 / 50** |

**The control is clean.** A1 vs A0: **0 fixed, 0 broken.** The frontmatter edit
— new tokens, a changed `sha`, a new edge — moves nothing on its own. Every
difference below is the prior, not the edit.

### P-SUPERSEDE — the prior fires, and it FAILS its bar

| arm vs A1 | fixed | broken | net |
|---|---|---|---|
| A2 (`0.5`) | `q015`, `q049` | `q022`, `q033` | **0** |
| A3 (`0.25`) | `q015`, `q049` | `q004`, `q022`, `q033`, `q046` | **−2** |

**Frozen bar: ≥ 1 fixed AND 0 broken. Neither arm reaches 0 broken. FAIL.**

**It is NOT inert, and that is new.** `superseded_weight` shipped in
`v2.0.0-alpha.1` and **had never been exercised by any measurement** — the
playground declared supersession in prose only, so the flag never set. This is
the first evidence in the project's history that the mechanism reaches the
ranking at all. **It does. It fixes `q015`**, the exact failure it was built
for.

### And every query it breaks has the SUPERSEDED document as its correct answer

| query | asks | correct answer |
|---|---|---|
| `q022` | *"can I start new work against helix mesh"* | **ADR-0007** |
| `q033` | *"why keep a superseded record in the repository"* | **ADR-0007** |
| `q004` | *"why did we adopt a service mesh in the first place"* | **ADR-0007** |
| `q046` | *"how do we stop a slow dependency taking down checkout"* | **ADR-0007** |

Against the one it fixes:

| `q015` | *"what is the **current** decision for east west traffic"* | ADR-0019 |
|---|---|---|

**A superseded document is not a worse document. It is the right answer to
questions about the past, the rationale, and whether-to-use — and the wrong
answer to exactly one kind of question: *what is true now*.** A global
multiplier cannot express that difference, because the difference is **not a
property of the document.**

### P-RERANK-DEFAULT — the bar is met, and it reproduces exactly

| B1 vs B0 | fixed | broken | net |
|---|---|---|---|
| | `q013`, `q015`, `q020`, `q026` | **none** | **+4** |

`28 → 32`, which **reproduces the filed 2026-08-24 number exactly** — the
instrument is measuring what it measured before.

⚠ **This "prediction" was MIS-FRAMED and is reported as a measurement, not a
verdict.** Its own frozen rule says a pass *"yields a recommendation plus the
named blocker, not a changed default"* — so no outcome of it could change
behaviour. **A prediction whose passing rule cannot change anything is not a
prediction**, and only one `VERDICT.md` is filed here, for P-SUPERSEDE.

## Reproduce

```bash
python evidence/run_arms.py    # stages six arms under /tmp/arms, grades each
```
