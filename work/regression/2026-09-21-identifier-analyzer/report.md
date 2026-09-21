---
type: Report
run: 2026-09-21-identifier-analyzer
item: W-205
classification: informed
description: "W-205 part 2 family (a) — `-`, `.` and `/` become identifier separators as `_` already was. 33 of 33 seed identifiers survive whole, from 0 of 33, on both readers. Ranking: +1 / +3 / +4 net at 100 / 1 000 / 10 000 documents, 0 regressions, all below decision 19's floor. INCONCLUSIVE; the change does not ship. The sibling identifiers set 3 was written to supply moved ZERO — they already ranked first in both arms."
filed: 2026-09-21
---

# REPORT — the analyzer keeps an identifier whole, and the ranking did not notice

**Verdict: [INCONCLUSIVE](VERDICT.md).** The arithmetic and the ruling are there;
this report carries what was run and what was seen.

**Pre-registration:** [frozen 2026-09-21](PRE-REGISTRATION.md), committed at
`576db3ec` **before any arm ran**, with its one self-contradiction corrected in
place at `f263cde7` — also before any arm ran, and in the **stricter** direction.

## The arms

| | engine | analyzer | what differs |
|---|---|---|---|
| **before** | main working tree at `7a88a165` | `v2` | — |
| **after** | an isolated `git worktree` on branch `w205-part2` | **`v3`** | `_WORD_RE` and `_BOUNDARY_RE` treat `-`, `.`, `/` as `_`; `ANALYZER_VERSION` |

🔴 **An arm is an ENGINE BUILD, not a tunable**, and the reason is structural:
an analyzer change rewrites the committed postings, and `store/format.py`'s
header pins `analyzer` precisely so two indexes holding different terms cannot
both claim to be the same one. **`_format` does not bump** —
[SR-INDEX-LIFECYCLE](../../../records/0108_index-lifecycle.md) **decision 10
already rules this**: *"An analyzer change bumps `analyzer` and not `_format`."*
⚠ The pre-registration argued that from first principles and reached the same
answer the record had already reached; it should have cited decision 10.

**The two arms differ by five files and nothing else** — `analyzer.py`,
`format.py`, `analyzer.mjs`, `format.mjs` and the Node fixture test. `git diff
3c885386..HEAD -- src node` on the main tree is empty.

## The mechanism — W-168's gate A, met

**33 of 33 seed identifiers survive whole. It was 0 of 33.**
[`evidence/w202-diff.md`](evidence/w202-diff.md) names **every moving row** of
W-202's frozen fixture — 33 seed identifiers and 3 of 10 contrast tokens — as
that fixture's docstring requires of any change to identifier handling.

| | `v2` | `v3` |
|---|---|---|
| `RF-118` | `rf` · `118` | **`rf-118`** · `rf` · `118` |
| `QCL-IT-ADR-08` | `qcl` · `adr` · `08` | **`qcl-it-adr-08`** · `qcl` · `adr` · `08` |
| `SKU.4471` | `sku` · `4471` | **`sku.4471`** · `sku` · `4471` |
| `ERR_2031` | `err_2031` · `err` · `2031` | unchanged — `_` always worked |

**Both readers agree byte for byte** on every fixture row; all 82 Node tests
pass. ⚠ **The Node fixture test had gone vacuous** and was repaired in the same
change: it asked `out.length === 1 && out[0] === id`, which can never hold once a
whole form arrives *beside* its parts, so the filter was always empty and the
assertion checked nothing. **Membership is the question now, on both readers.**

⚠ **Two behaviour changes beyond identifiers, both pinned as tests:**

- **Decimals are one token.** `0.75` was `0` + `75`; searching `0.75` used to
  match a document that merely said `75`.
- 🔴 **A single-character segment that `v2` kept is now dropped.** `COLD-1` was
  two raw tokens so `1` reached the index; it is now one token whose parts go
  through `split_identifier`, which drops single characters. **8 of 33 seed
  identifiers lose one** — `COLD-1`, `DAIRY-2`, `GHY-7`, `QCL-F-09/17/22`,
  `TSL-RF-118-A`, `TSL-RF-221-A`. The whole form compensates and discriminates
  far better than a bare `1`, but the bare `1` is genuinely gone.

## The ranking — what was run

**43 id-queries** (the 33 of 2026-09-18 plus 10 authored from set 3 by grep, no
key), **two queries each** — the bare identifier and the identifier in a question
— on **`rung-00100` · `rung-01000` · `rung-10000`**, each arm on **its own
`arm_corpus.py` copy**, ingested end to end by its own engine.

**Endpoint: `rank_primary_bare` at hit@1, paired.** The question form is reported
beside it and never averaged with it — surrounding words rescue a mangled
identifier, which is how the 2026-09-16 survival run reached a wrong conclusion.

| rung | before | after | fixed | broke | **net** |
|---|---:|---:|---:|---:|---:|
| `rung-00100` | 32/43 | 33/43 | 1 | **0** | **+1** |
| `rung-01000` | 30/43 | 33/43 | 3 | **0** | **+3** |
| `rung-10000` | 29/43 | 33/43 | 4 | **0** | **+4** |

**Question form:** net **+0 · +0 · +1**. `G-DAIRY-2` broke at `rung-01000` and
`rung-10000`; `RF-203` and `WIKI-NGP-DOCK-12` were fixed.

🔴 **The sibling families — the entire reason set 3 exists — moved zero at every
rung, because all eight already ranked their own document first in both arms.**
That is the report's real content and it is the verdict's headline.

## Headroom, disclosed before any net is quoted

[SR-RS](../../../records/0133_predictions.md) decision 22b, in its own terms:
**improvement headroom is the queries not right in BOTH arms**, **regression
headroom the queries not wrong in both.** They are different questions and one
number answers neither.

| rung | right in both | **improvement headroom** | wrong in both | **regression headroom** | net taken |
|---|---:|---:|---:|---:|---:|
| `rung-00100` | 32 | **11** of 43 | 10 | **33** of 43 | +1 |
| `rung-01000` | 30 | **13** of 43 | 10 | **33** of 43 | +3 |
| `rung-10000` | 29 | **14** of 43 | 10 | **33** of 43 | +4 |

🔴 **The run was not structurally unable.** At `rung-10000` there were **14**
queries that could have improved against a floor of 6, and **33** that could have
regressed. The arm converted **4** and broke **0**. That is the difference
between *this measurement could not have produced a result* — which is what
stopped this item on 2026-09-18 at 3–4 of 33 — and *this measurement could have,
and did not*. **Only the second is a fact about the change.**

⚠ **10 of 43 are wrong in both arms at every rung**, and they are the same ten.
They include `QCL-QA-MAP-01`, which is frontmatter-only and waits on **part 1**;
no analyzer change can reach a document that was never read.

## Where the unshipped change lives

🔴 **The branch is NOT merged**, because the pre-registration says an
inconclusive does not ship. The mechanism is preserved as
[`evidence/family-a.patch`](evidence/family-a.patch) — a `git diff` of `src/`,
`node/` and `tests/` against `3c885386`, 8 files, so it applies cleanly if Arpit
rules to ship on the correctness argument (verdict question 1).

⚠ **It is filed as evidence rather than committed as code on purpose.** Engine
code on a branch nobody merged rots against `main` and reads, months later, like
something that was half-done. A patch beside its verdict reads like what it is:
a measured change that did not clear its bar.

## Reproduce

```bash
work/regression/2026-09-21-identifier-analyzer/evidence/run-arms.sh
```

Six `arm_corpus.py` builds, six `identifier_probe.py` probes, two `control_60.py`
runs and three `compare_arms.py` comparisons. Every JSON in `evidence/` is one of
their outputs; nothing in this report is typed.

## Authorship

| artifact | author | blind? |
|---|---|---|
| the 33 id-queries | Claude (Cowork, 2026-09-18), targets by grep | no |
| the 10 set-3 id-queries | **Claude Code, this session**, targets by grep | no |
| the seed documents they target | Codex (`01`–`15`) and Claude (`16`–`22`) | — |
| the analyzer change | Claude Code, this session | — |
| the pre-registration and the floor | Claude Code, frozen before any arm | — |

**`classification: informed`** — the measurer's family authored the queries and
rebuilt the corpus. 🔴 **No golden answer was used, needed or reachable.** An
id-query carries no answer and never enters `work/golden/`, which is the whole
reason an analyzer change can be measured while L11 stands.
