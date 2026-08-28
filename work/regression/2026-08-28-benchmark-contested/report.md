---
type: RegressionRun
name: 2026-08-28-benchmark-contested
description: "The contested-answer suite (W-95) built and read for the first time. On an endpoint with 94 queries of asserted headroom, shipped-default HEAD separates nothing that 1.0.0 does not; the proximity reranker fixes 94/120 and breaks 0 when switched on, and ships at 0.0."
classification: informed
timestamp: 2026-08-28T00:00:00Z
prereg: work/benchmark/PRE-REGISTRATION-CONTESTED.md
---

# Contested answers — `1.0.0` vs `HEAD`, on a suite that could actually detect a change

**Pre-registration:** [`PRE-REGISTRATION-CONTESTED.md`](../../benchmark/PRE-REGISTRATION-CONTESTED.md),
`sha256 e8417b33…`, written and delivered to disk **before the first corpus byte
existed**. **Arms unchanged** from
[`2026-08-28-benchmark-v1-vs-head`](../2026-08-28-benchmark-v1-vs-head/report.md):
`A = fux-engine 1.0.0`, `B-core = HEAD @ 75ade57` on shipped defaults. **Only
the instrument changed.**

---

## The result, before the detail

| id | endpoint | verdict | measured | reading |
|---|---|---|---|---|
| **C1** | proximity, A vs B-core — **primary** | **No detected change** | 0 discordant of 120 · `p = 1.0` · **94 queries of headroom** | Both arms **21.7 %**, indistinguishable from the 25 % chance of a 4-candidate cluster. The null is now about the engine, not the corpus. |
| **C2** | proximity, B-core vs **B-tuned** — *ablation* | **Pass**, tuned better | b = 94, c = 0 · `p = 1.0e-28` · 22 % → **100 %** | The proximity reranker **works, and ships switched off** (`rerank_weight = 0.0`). |
| **C3** | path, A vs B-core | **Pass**, B better | b = 60, c = 0 · `p = 1.7e-18` · 0 % → **100 %** | A **capability** delta: B has a `path` tf field and A has none. |
| **C4** | heading, A vs B-core — *negative control* | 🔴 **Inconclusive** | 0 discordant of 40 · **0 queries of headroom** | Returned the predicted null **but saturated at 100 % in both arms**, so it did not discharge its job. See finding 3. |
| **C5** | null control — halt gate | **Pass** | 380/380 substantive rows identical, arm A twice | Run first. Everything above depends on it. |
| **C6** | headroom disclosure | reported | table below | The line the previous pre-registration had no way to print. |
| — | marker `hit@5` (retained as control) | — | **120/120 both arms**, 0 discordant | The 2026-08-28 saturation **reproduces on a fresh corpus**. |

🔴 **The headline is C1, and it is a null.** The previous run's null could not be
told apart from a broken instrument. This one can: the corpus **asserts** that 94
of the 120 clusters could have changed hands, and none did.

---

## 1. What a contested cluster is

Four candidate documents share the query's terms **at equal term frequency,
equal field and equal length**. Exactly one is the target, distinguished by a
single property:

| kind | every candidate carries | only the target has it | isolates | N |
|---|---|---|---|---:|
| `proximity` | marker `a` once **and** `b` once, two fixed-shape sentences | **in the same sentence** | `rerank_weight` | 120 |
| `path` | the marker exactly once | **in the filename**, in no prose | the `path` tf field | 60 |
| `heading` | the marker exactly once | **as heading text** | intended as a control | 40 |

The generator's `--selftest` **fails the run** rather than reporting a number
unless: every candidate carries each term exactly once; exactly one candidate
has the distinguishing property; the target is path-first in *some but not all*
clusters (the tie-break guard the chains carry); and the corpus is
byte-deterministic. **The headroom is asserted, not assumed** — which is the
whole of W-95.

⚠ The extension is **strictly additive**: every corpus the pre-W-95 generator
produced still regenerates **byte-identical**, verified on both the plain and
bench paths, so no prior run stops reproducing.

---

## 2. C6 — the headroom disclosure

`target_first` = the target outranked **every other candidate in its own
cluster**. Scored inside the cluster, because the contest is between these four.

| suite | N | arm A | B-core | B-tuned | at ceiling in **both** | **could have changed** |
|---|---:|---:|---:|---:|---:|---:|
| contested `proximity` | 120 | 21.7 % | 21.7 % | **100 %** | 26 / 120 | **94** |
| contested `path` | 60 | 0 % | **100 %** | 0 % | 0 / 60 | **60** |
| contested `heading` | 40 | 100 % | 100 % | 100 % | 40 / 40 | 🔴 **0** |
| marker `hit@5` | 120 | 100 % | 100 % | 100 % | 120 / 120 | 🔴 **0** |

**Read the last column first.** Two of these four suites cannot detect anything
at any sample size, and the table says so before any p-value is quoted. That is
the previous run's recommendation R2 made mechanical.

**All four candidates were visible in the top 10 in 120 of 120 proximity
clusters**, so the contest was genuinely joined every time — the null is not an
artefact of candidates falling out of the window.

**Tier `t10000` — 8 x the corpus, every finding unmoved.** Descriptive, and
run because a scale-dependent instrument would be worth knowing about:

| suite | N | arm A | B-core | b | c | p | headroom |
|---|---:|---:|---:|---:|---:|---:|---:|
| `proximity` | 120 | 29.2 % | 29.2 % | 0 | 0 | 1.0 | 85 |
| `path` | 60 | 0 % | 100 % | 60 | 0 | 1.7e-18 | 60 |
| `heading` | 40 | 100 % | 100 % | 0 | 0 | 1.0 | 0 |
| marker `hit@5` | 120 | 100 % | 100 % | 0 | 0 | 1.0 | 0 |

Both arms rise together on proximity (21.7 % → 29.2 %) — more documents, more
chances a candidate is displaced — **and the discordant count stays 0 in both
directions.** The instrument is not scale-dependent and neither is the null.

---

## 3. The three findings

### Finding 1 — on shipped defaults, `HEAD` separates nothing `1.0.0` does not

Both arms sit at **21.7 %** on a contest whose chance level is 25 %. Not close
to each other by coincidence: **0 of 120 clusters changed hands in either
direction.** With 94 queries of headroom and power 0.99 against a
`pb .25 / pc .05` effect, this is a null the instrument could have broken and
did not.

**The mechanism was named in the pre-registration, from source, before the
run:** `rerank_weight` ships at `0.0`. B-core has no proximity signal to bring,
so it ranks these clusters on bag-of-words evidence that is equal by
construction — and lands at chance, exactly like `1.0.0`.

### Finding 2 — the reranker works. It ships switched off.

| | inversions of the contest | |
|---|---|---|
| arm B-core, `rerank_weight = 0.0` | **26 / 120** (21.7 %) | shipped |
| arm B-tuned, `rerank_weight = 0.5` | **120 / 120** (100 %) | one key |

**b = 94 fixed, c = 0 broken, `p = 1.0e-28`.** Not one cluster was made worse.

🔴 **This is the third ranking prior found shipping as a no-op**, and the
pattern is now the finding rather than the instance:

| knob | ships at | effect | already on record |
|---|---|---|---|
| `superseded_weight` | `1.0` | multiplicative no-op | W-94, 2026-08-28 |
| `recency_half_life_days` | `0.0` | no-op | 2026-08-28 |
| `rerank_weight` | `0.0` | the proximity reranker is off | **yes** — [2026-08-25](../2026-08-25-supersession-and-reranker-default/report.md) measured the reranker and recorded that *"the default still does not flip"*, and `P-RERANK-DEFAULT` was withdrawn as mis-framed |

⚠ **Nothing in that table is discovered here, and saying otherwise would be
claiming someone else's finding.** What is new is that the three are now
visible as **one pattern** rather than three instances, and that the third has
been measured on an endpoint with asserted headroom.

**Every ranking prior `HEAD` added is disabled at the default.** That, not the
saturated corpus alone, is why a version comparison on shipped defaults keeps
returning nulls: on ranking priors, **B-core *is* A**. The five committed tf
fields are the one exception — structural, always on, and the only place C3
found a delta.

🔴 **This is not an argument for changing the default, and the pre-registration
said so before the number existed.** `0.5` was an arbitrary mid-scale probe, not
a tuned optimum. The precedent is
[`P-SUPERSEDE`](../2026-08-25-supersession-and-reranker-default/VERDICT.md): a
weight change that looked excellent on a generated corpus had already been ruled
**FAIL** on the hand-graded playground — at `0.5` it fixed `q015` and `q049`
and **broke `q022` and `q033`**, and every broken query had the superseded
document as its correct answer. **This corpus has the same blindness by
construction** — every planted target *is* the co-occurrence, so the document
that should win *without* co-occurrence does not exist here and cannot be
broken. **`c = 0` is a property of the generator, not a safety result.**

🔴 **And the magnitude here is inflated by construction.** The reranker's value
on **hand-graded** text is on record and it is small: `28 → 32` on the
playground's 50 goldens, **+4 fixed, 0 broken**
([2026-08-24](../2026-08-24-rerank-and-goldens/report.md),
[2026-08-25](../2026-08-25-supersession-and-reranker-default/report.md)) — and
even that is `informed` and below the resolution floor. **This suite rewards
exactly what the reranker does**, so `94/120` measures that the machinery
functions, **not that it is worth 78 points to anyone**. The hand-graded `+4` is
the better estimate of real value, for the same reason P-SUPERSEDE's playground
result outranked a generated corpus.

### Finding 3 — 🔴 the negative control saturated, and this run's own table caught it

`heading` was pre-registered as a control that must return a null: both arms
weight `heading` 3.0 against `body` 1.0, so a delta there would have meant the
instrument was measuring something other than the field it names.

**It returned the null — at 100 % in both arms, with zero headroom.** So it
returned the *right answer for the wrong reason*: it could not have produced a
delta whatever the engines did, which is precisely the failure mode this whole
run exists to expose, **reappearing inside the instrument built to expose it.**

The control is therefore **Inconclusive, not Pass**, and C1 and C3 rest on the
generator's assertions rather than on a discharged control. Reporting it as a
pass would have been the easiest and most dishonest line in this document.

---

## 4. What this run may never be used to say

- 🔴 **It states no delta.** The session that authored the generator also read
  the scores, so the run is **`informed`** by the standing rule. It may be
  filed, listed, cited and used to inform the corpus. It is **not a
  generalisation estimate**. A `blind` version needs two sessions — W-96.
- **C3 is a capability demonstration, not a ranking win.** Its contest is
  decided by a field arm A does not have, which is close to tautological. The
  honest sentence is *"B can see a filename and A cannot"*.
- **C2 is an ablation**, one engine and one knob. It carries no version claim
  and no recommendation about the default.
- **A null is not equality**, even with headroom. It says these engines do not
  separate *these* clusters.
- **"Correct" here is declared by construction, not true.** The base documents
  state no facts. This measures whether an engine prefers co-occurrence and
  whether it can see a filename — never whether a document answers anything.
- **No wall-clock claim.** Quality and byte numbers only; latency was not
  re-measured and the previous run's B5/B6 stand unchallenged.

---

## 5. Reproduce

```
python3 bin/make_corpus.py --selftest
python3 bin/make_corpus.py --out corpora/t1200 --docs 1200 --seed 12 --bench \
  --pairs 120 --chains 20 --decoys 30 --unanswerable 20 \
  --contested 120 --heading 40 --path 60 --cluster 4

python3 bin/bench.py prepare --run C --arm A --tier t1200
python3 bin/bench.py quality --run C --arm A --tier t1200 --label A

python3 bin/bench.py mcnemar --a runs/C/rows/A-t1200.jsonl \
  --b runs/C/rows/B-t1200.jsonl --suite contested --key target_first --kind proximity
```

`evidence/` carries 5 row files (1 900 per-query rows), both eval sets, the
frozen `ARMS.toml`, and the harness as run. Every aggregate above is derivable
from the rows and from nothing else.

---

## Authorship

**Classification: `informed`** — ruled by
[`PRE-REGISTRATION-CONTESTED.md`](../../benchmark/PRE-REGISTRATION-CONTESTED.md)
§5's own line, which says it in advance: *"the session that authored the
generator also reads the scores, so by `PRE-REGISTRATION-V1-VS-HEAD.md` §3 the
run is `informed`."* That is this session exactly — one session wrote
`make_corpus.py`, froze the pre-registration, ran the harness and read every
number in this report. It could reach **the generator and every prior score**,
never the annotators' judgments (there are none here — correctness is declared
by construction, §3 above) and never a second session's blind read.

It is filed, listed and citable; **no delta is stated from it, and it is not a
generalisation estimate.** A `blind` version needs two sessions that never
share the corpus or the scores — [W-96](../../OPEN-WORK.md).
