---
type: Report
name: BENCH-V1-VS-HEAD
title: "fux-engine 1.0.0 vs working-tree HEAD — the version benchmark, executed"
description: "Two engines, one corpus, three tiers, 240 generated marker queries per tier plus 40 supersession chains and 20 unanswerables. Every pre-registered paired test returned a discordant count of ZERO. The primary endpoint is saturated at 100% in both arms and could not have detected anything; the supersession endpoint failed its predicted PASS because the prior that would fix it ships switched off."
classification: informed
timestamp: 2026-08-28T00:00:00Z
---

# `1.0.0` vs `HEAD` — the run

**Pre-registration:** [`../../benchmark/PRE-REGISTRATION-V1-VS-HEAD.md`](../../benchmark/PRE-REGISTRATION-V1-VS-HEAD.md),
frozen with `HEAD = 75ade572165cf06161bc58d0d8519f771da37636` written in before
the first command ran.

**Arms:** `fux 1.0.0` (arm A) and `fux 2.0.0-alpha.2` at that sha (arm B), each
in its own venv on CPython 3.11.15, each ingesting its own copy of identical
corpus bytes. Manifest: [`evidence/ARMS.toml`](evidence/ARMS.toml).

---

## The one-line result

🔴 **Every pre-registered paired test returned a discordant count of ZERO.**
Not a small delta — *no query changed its outcome in either direction*, on any
tier, on any suite. Under the measured resolution floor
([ADR-RS](../../../docs/adr/0036_predictions.md) decision 19) that is
**no detected change**, and it is the strongest possible form of one.

---

## What was measured

| tier | arm | hit@5 | hit@10 | MRR@10 | rank-1 | chain inversions | declines |
|---|---|---|---|---|---|---|---|
| 100 | A | 240/240 | 240/240 | 1.0000 | 240/240 | 5/10 | 0/20 |
| 100 | B | 240/240 | 240/240 | 1.0000 | 240/240 | 5/10 | 0/20 |
| **1 000** | **A** | **240/240** | 240/240 | **1.0000** | 240/240 | **21/40** | **0/20** |
| **1 000** | **B** | **240/240** | 240/240 | **1.0000** | 240/240 | **21/40** | **0/20** |
| 10 000 | A | 240/240 | 240/240 | 1.0000 | 240/240 | 17/40 | 0/20 |
| 10 000 | B | 240/240 | 240/240 | 1.0000 | 240/240 | 17/40 | 0/20 |

### The paired tests, exact two-sided McNemar, α = 0.05

| endpoint | tier | metric | `n` | `b` fixed by B | `c` broken by B | discordant | `p` |
|---|---|---|---:|---:|---:|---:|---:|
| **B1** | 1 000 | `hit@5` | 240 | 0 | 0 | **0** | 1.0 |
| B1 | 100 / 10 000 | `hit@5` | 240 | 0 | 0 | **0** | 1.0 |
| **B2** | 1 000 | current-ranks-first | 40 | 0 | 0 | **0** | 1.0 |
| B2 | 100 / 10 000 | current-ranks-first | 10 / 40 | 0 | 0 | **0** | 1.0 |
| **B7** | all | declined | 20 | 0 | 0 | **0** | 1.0 |
| **B9** | 1 000 | `hit@5`, A vs A′ | 240 | 0 | 0 | **0** | 1.0 |

### B3 — committed bytes and wheel

| | arm A | arm B | ratio | bar |
|---|---:|---:|---:|---|
| index bytes, 1 000 docs | 1 462 342 | 1 465 065 | **1.002 ×** | ≤ 1.25 × |
| index bytes, 10 000 docs | 14 147 492 | 14 117 857 | **0.998 ×** | ≤ 1.25 × |
| shards, 10 000 docs | 256 | 256 | — | — |
| **published wheel** | 7 113 352 | 258 901 | **0.036 ×** | — |

**`HEAD` does not commit per-chunk `int8` vectors** — the thing B3 named as the
one item to actually check. Read from a record, not assumed: arm A's document
records carry a `code` key (the dense lane), arm B's do not, and neither carries
a `vectors` key. Record shapes are `fux.index.v1` / `fux.index.v2`, with
`tf_fields` going from `["heading","body"]` to
`["body","heading","title","path","ctx"]`.

### B5 / B6 — latency, arms interleaved `A B A B`, tier 10 000

| | arm A | arm B | ratio | bar |
|---|---:|---:|---:|---|
| `ask` p50 | 79.3 ms | 103.7 ms | 1.31 × | — |
| **`ask` p95** | **85.6 ms** | **112.6 ms** | **1.32 ×** | ≤ 1.5 × |
| **cold `ingest` median** | **25.68 s** | **26.78 s** | **1.04 ×** | ≤ 2.0 × |
| `build` median | 612 ms | 1 086 ms | 1.77 × | — |

1 200 timed queries per arm (240 × 5 repeats), 20 warm-up queries per arm
discarded, three cold ingest repeats per arm. ⚠ **Arm B's three ingest repeats
were 25.4 / 26.8 / 38.8 s** — the third is an outlier on a laptop that was doing
other things; the median is reported and all three are filed.

**The differential law holds in both arms**: `ask --fast` and `ask --scan`
byte-identical across all 240 queries, 0 mismatches, checked before any `--fast`
number was produced.

### The controls

- **Decoys** — topically adjacent, factually silent documents shadowing a marker
  query. A decoy reached the top 5 for **1 of 50** shadowed queries at tier
  1 000 and **1 of 208** at tier 10 000, **identically in both arms**.
- **B9 null control, run first**, in two halves: arm A twice on one corpus →
  **300/300 rows identical**; arm A vs arm A′ on a second seed → **0 discordant,
  p = 1.0**. Neither number was produced before this gate passed.

### Capability delta — arm B only, no comparison

Arm A emits no confidence block at all, so this is a capability table, not a
contrast. On all 20 unanswerables arm B returned `band: partial`,
`answerable: true` — and for the absent-entity half it named the missing term:
`missing: ["zq00000w"]`, `coverage: 0.0009`. **Arm B knows the queried term is
absent and answers anyway.**

---

## Deviations from the pre-registration, stated rather than absorbed

1. **`B4` and `B8` do not exist.** The item and the register both say
   "thresholds **B1–B9**"; the frozen document defines B1, B2, B3, B5, B6, B7
   and B9 only. Nothing was skipped — two ids were never written.
2. **Chains at tier 100 are 10, not ~40.** 40 chains is 80 documents, which
   would be 80 % of a 100-document corpus. The primary tier has the
   pre-registered count.
3. **B9's "two seeds" is computable only because the markers are
   seed-independent.** `zx00007q` is the same query string in both corpora and
   only its host document differs, so the qids pair. Had the generator drawn
   markers from the seed, the pre-registered paired form would have had no
   meaning and the run would have had to say so.
4. **"Decline" had to be operationalised.** The pre-registration asks whether
   `answer` "declines or fabricates" and names no observable. The only one both
   arms have is *did it return a passage* — arm A has no band. ⚠ **This was
   defined after observing that both arms return three passages for an absent
   term**, which is the single strongest reason this run is `informed`.

---

## Authorship

**Classification: `informed`** — ruled by the pre-registration's own §3, which
says it in advance: *"If the same session writes the generator and reads a
score, the run is `informed` and no delta may be stated from it."* That is this
session exactly. It is filed, listed and citable; **no delta is stated from it,
and it is not a generalisation estimate.**

| artifact | author | could reach |
|---|---|---|
| the pre-registration + thresholds | an earlier session (2026-08-28) | none — it contains no score |
| corpus generator `--bench` extensions | **this session (Claude Code, Opus)** | none *at authoring time* — written and frozen before either arm ran |
| the three query sets + the two typed subsets | **this session**, generated mechanically from planted facts | same |
| the harness (`bench.py`, `latency.py`) | **this session** | the arms' output *shape* (probed on a throwaway corpus after the eval corpora were frozen) |
| the "decline" observable | **this session** | ⚠ **arm behaviour** — see deviation 4 |
| this report + `ANALYSIS.md` | **this session** | every per-query row |

**What argues the exposure was small, and it is an argument rather than a
proof:** the four corpora were generated and `sha256`-recorded before any arm
was installed against them, the generator is filed byte-for-byte in
`evidence/harness/`, and the pre-registered bars were frozen in git by a
separate commit before the first command ran. **What argues it was real:** the
decline observable was chosen after seeing how both arms behave, and one session
did everything.

**What would make a re-run `blind`:** one session authors and freezes the
generator and the query sets and stops; a second session, which never reads
them, executes and analyses. That is a two-session protocol, and nothing in the
repo currently makes it happen.

## Reproduce

```bash
# harness: ~/my_programs/fux-benchmark (SETUP-BENCHMARK), generator: fux-lab/shared/generate/
python3 shared/generate/make_corpus.py --out corpora/t1000 --docs 1000 --seed 12 \
        --bench --pairs 240 --chains 40 --decoys 50 --unanswerable 20
python3 bin/bench.py prepare --run <run> --arm A --tier t1000
python3 bin/bench.py quality --run <run> --arm A --tier t1000 --label A
python3 bin/bench.py mcnemar --a rows/A-t1000.jsonl --b rows/B-t1000.jsonl --suite pairs --key hit@5
python3 bin/latency.py --run <run> --tier t10000 --queries 240 --repeats 5
```
