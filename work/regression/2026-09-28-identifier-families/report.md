---
type: Regression Run
name: identifier-families
description: "W-233's pre-registered run: PASS. Identifier families lift a variant-spelled ID query to its own document at rank 1 by +25 / +88 / +105 net (0 broken) on rung-00100 / 01000 / 10000. The exact spelling holds at 100 % in both arms, 0 of 60 prose questions move, all three gates pass, and the committed index grows +0.3 % at rung-10000."
run: 2026-09-28-identifier-families
item: W-233
classification: informed
status: complete
timestamp: 2026-09-28T00:00:00Z
---

# Identifier families on the ladder

**Pre-registered in [PRE-REGISTRATION.md](PRE-REGISTRATION.md)**, frozen at
`cca32152` before any of the mechanism existed. **Verdict: [PASS](VERDICT.md).**

**Reproduce** (about 25 minutes; it rebuilds six arm copies under
`fux-lab/arms/runs/`, never a rung):

```bash
bash work/regression/2026-09-28-identifier-families/evidence/run-arms.sh
.venv/bin/python work/regression/2026-09-28-identifier-families/evidence/control_e3.py <tree> <out>   # per arm
.venv/bin/python work/regression/2026-09-28-identifier-families/evidence/parity_g1.py
.venv/bin/python work/regression/2026-09-28-identifier-families/evidence/decide.py
```

| arm | engine | families |
|---|---|---|
| before | `cca32152`, from a worktree via `PYTHONPATH` | none (the feature does not exist) |
| after | the W-233 build (this change) | what `fux identifiers --write` wrote on each copy: **12 / 42 / 42**, filed as `evidence/identifiers-<rung>.toml`, never edited |

Every copy was committed at one fixed stamp, so the two arms' `mtime` agree and
G3 compares bytes.

## Gates (§4)

| gate | result |
|---|---|
| **G1** parity: every one of 999 queries analyzed by both readers under the after rules | ✅ 0 divergent ([g1.txt](evidence/g1.txt)) |
| **G2** determinism: two from-scratch after-arm builds per rung | ✅ byte-identical on all three |
| **G3** inertness: the W-233 engine with an empty file, against the before engine on rung-01000 | ✅ `.fux/index/` byte-identical |

## Headroom, disclosed before any net (decision 22)

Improvement headroom is the queries the before arm missed. Regression headroom
is the queries it already got right.

| rung | E1 improvement headroom | E1 regression headroom | E2 improvement headroom | E2 regression headroom |
|---|---:|---:|---:|---:|
| rung-00100 | 25 | 62 | 0 | 28 |
| rung-01000 | 88 | 244 | 0 | 119 |
| rung-10000 | 105 | 215 | 0 | 113 |

⚠ **E2 could only break.** Every exact spelling was already at rank 1 in the
before arm, which is the fixture's finding reproduced at scale. So E2 is a pure
guard, and it held.

## Endpoints (§5), hit@1 of the primary, paired

| rung | E1 before → after | fixed | broke | **net** | E2 before → after | E2 net |
|---|---|---:|---:|---:|---|---:|
| rung-00100 | 62 → **87** / 87 | 25 | 0 | **+25** | 28 → 28 / 28 | 0 |
| rung-01000 | 244 → **332** / 332 | 88 | 0 | **+88** | 119 → 119 / 119 | 0 |
| rung-10000 | 215 → **320** / 320 | 105 | 0 | **+105** | 113 → 113 / 113 | 0 |

**By variant, reported and never judged alone (§5):**

| rung | `space` | `nosep` | `endash` | `unpadded` |
|---|---|---|---|---|
| rung-00100 | 25 → 28 / 28 | 6 → 21 / 21 | 25 → 28 / 28 | 6 → 10 / 10 |
| rung-01000 | 114 → 119 / 119 | **10 → 84** / 84 | 114 → 119 / 119 | 6 → 10 / 10 |
| rung-10000 | 101 → 113 / 113 | **7 → 84** / 84 | 101 → 113 / 113 | 6 → 10 / 10 |

**E3, the prose control:** **0 of 60** retired set-1 questions changed their
rank-1 document on rung-01000.

## Cost (§7): reported, no threshold

| rung | committed `.fux/index/` (du, KB) | distinct terms | postings |
|---|---|---|---|
| rung-00100 | 648 → 652 | 3 416 → 3 456 | 18 339 → 18 383 |
| rung-01000 | 3 304 → 3 312 (+0.2 %) | 6 774 → 6 987 | 98 763 → 99 060 |
| rung-10000 | 26 160 → 26 248 (**+0.3 %**) | 30 841 → 31 306 (+1.5 %) | 902 972 → 905 857 (+0.3 %) |

The distinct-term and posting counts are the accelerator's line in
[output.txt](evidence/output.txt). Ingest wall-clock was not separated from the
build and is not claimed.

## ⚠ Post-hoc: the lens was tightened after the run, and the ladder is unchanged

After the arms ran, the lens was tried on fux's own prose. It proposed 154
families, and many were noise:

- file names (`W-104-enrich.md`);
- parameter values (`anchor-0.5`, `alpha.0`);
- section numbers (`A.13`);
- ranges (`L0-L12`).

The candidate rule now requires a `-` or `_` and excludes file names, decimals
and same-prefix ranges ([SR-INSPECT](../../../records/0156_inspect.md), the
identifier lens). **Re-run on each after-arm copy, it writes families
identical to the three filed `identifiers-<rung>.toml`**, so the verdict
describes the lens that ships. On fux's own repository the count falls from 154
to 102. This is labelled post-hoc and is kept out of the verdict (SR-RS decision
10b).

## Per-query rows

[`evidence/per-query-rows.jsonl`](evidence/per-query-rows.jsonl): 999 rows,
one per `(rung, id, variant)`, with both ranks. The raw per-arm rows are in
`before-<rung>.jsonl` and `after-<rung>.jsonl`, and E3's in
`control-<arm>.jsonl`.

## Authorship

| what | who |
|---|---|
| the ladder rungs and their identifiers | **Codex** and **Claude** (gen 3) |
| the variant rule, the query sets, the mechanism, every script here | this session |
| golden answers | **none used, needed or reachable**. E3 reads retired question text only |

**`informed`.** The measurer built the mechanism and wrote the rule that
generated the queries, and the tree has been unlocked since 2026-09-21 (L11).
