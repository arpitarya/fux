---
type: Report
description: "The golden ladder built to rung 1 000 and run against all 124 released questions — five rungs, per-query rows, and three findings that need no answer key."
run: 2026-09-12-golden-ladder
item: W-136
classification: informed
engine: fux-engine 2.0.0-alpha.7
engine_sha: 676e973
pre_registration: work/regression/2026-09-12-golden-ladder/PRE-REGISTRATION.md
filed: 2026-09-12
---

# Golden ladder — phase 2 built, phase 4 run, rungs seed → 1 000

**Five rungs built blind and frozen, then 124 questions asked on each.** The
answers are in [`ANSWERS-FOR-REVIEW.md`](ANSWERS-FOR-REVIEW.md); the scoring is
Codex's, in phase 5.

---

## 1. Authorship and classification — `informed`, and why

**This run is `informed`.** Not because anything leaked, but because of who
wrote what:

| artifact | author | could reach the queries? | could reach the answers? |
|---|---|---|---|
| seed documents 01–10 | Codex | no | no |
| seed documents 11–15, `seed/archive/` | Claude (earlier session) | — | it *wrote* the key |
| `seed-dates.tsv` | Claude (earlier session) | — | mechanical |
| the 124-question key | **Claude** (stopgap, [W-145](../../open/W-145-codex-regenerates-the-key.md)) | wrote them | wrote them |
| `ext/` corpus, all 5 rungs | Claude, **this session** | **no** — built and committed before `questions/` was opened | no |
| this analysis | Claude, this session | yes, after the ladder was frozen | **no** |

The defect is upstream of any seal: the same model family authored the
questions and grew the corpus. A leak is detectable after the fact; correlated
priors between the question-writer and the corpus-writer are not, and no test
finds them.

🔴 **Binding, and fixed in the pre-registration before any number existed:**
**no delta is stated in this report, in any direction** — not rung-to-rung, not
against another run, not "unchanged". Per-rung absolutes are reported. No
verdict is filed. This run adjudicates nothing.

**What it is for:** it exercises the whole path end to end, and it records
per-query rows for 620 (question, rung) pairs so that the blind re-run — same
frozen ladder, Codex's regenerated key — has something to be compared with.

---

## 2. Phase 2 — what was built

**Arpit capped this session at rung 1 000.** `rung-02000`, `rung-05000` and
`rung-10000` are **not built**, not frozen, and nothing here says anything
about them.

| rung | documents | archived | superseded | carrying `mtime` |
|---|---:|---:|---:|---:|
| `rung-seed` | 20 | 5 | 4 | 20 / 20 |
| `rung-00100` | 100 | 13 | 12 | 100 / 100 |
| `rung-00200` | 200 | 23 | 22 | 200 / 200 |
| `rung-00500` | 500 | 53 | 52 | 500 / 500 |
| `rung-01000` | 1 000 | 103 | 102 | 1 000 / 1 000 |

Each rung is its own git repository under
`~/my_programs/fux-lab/corpora/golden/`, with its own committed `.fux/` index,
built once with this engine version.

**Properties checked rather than asserted:**

- **Nesting.** Rung N's manifest contains rung N−1's documents with identical
  hashes. All twenty seed documents are in every rung, at the paths the key
  names.
- **Category mix, exact at every rung** — sibling 40 % · adjacent 30 % ·
  filler 20 % · variant 10 %. The generator emits blocks of ten and every
  rung's `ext` count is a multiple of ten, so no rung cuts a block.
- **Declared, never derived** — `seed`, `seed/archive archived=true`, `ext`,
  `ext/archive archived=true`. The coverage file reads the counts back out of
  each built index and the rung is not frozen unless they match.
- **Dated.** Every document is committed at its own date, so all 1 000 carry an
  `mtime` and the recency prior is alive rather than a configured no-op.
- **No `ext/` document names a seed entity**, and none declares `supersedes:`
  on a seed. The generator holds the blacklist and refuses to write rather than
  emit one.

**Blindness.** The ladder was built, frozen and **committed** (`92f5bff`) before
`work/golden/questions/` was opened. That ordering is visible in `git log` and
is the only thing that makes these rungs blind; the questions were released
early, so phase 2 was on its honour and this is the record of it.

**Reproducibility.** The lab commits nothing, so the generator and the twenty
hand-authored hard negatives are filed under
[`evidence/generator/`](evidence/generator/). The corpus is regenerable from
committed bytes.

---

## 3. Phase 4 — what was run

Per question, per rung, exactly once, exactly as pre-registered:

```
fux ask "<question>" --json --band --top 10
fux answer "<question>" --json
```

No retry, no reformulation, no `-q` fusion, no `--expand`, no `--fast`, no tune
override. Each rung was hashed against its frozen manifest immediately before
it was queried, and the engine version was checked against
`ladder/rung-NNNNN.index`; no rung needed re-ingesting.

| rung | questions | ask failures | median latency |
|---|---:|---:|---:|
| `rung-seed` | 124 | 0 | 140 ms |
| `rung-00100` | 124 | 0 | 147 ms |
| `rung-00200` | 124 | 0 | 154 ms |
| `rung-00500` | 124 | 0 | 170 ms |
| `rung-01000` | 124 | 0 | 192 ms |

620 per-query rows in total — `evidence/<rung>/predictions.jsonl` (the phase-5
input), `evidence/<rung>/answers.jsonl` (the prose passages) and
`evidence/per-question.tsv` (the flat grid).

---

## 4. Three findings that need no answer key

These are read off the ranked lists and the corpus structure. **None of them
uses the key**, so none is affected by W-145, and none is a delta.

### 4.1 🔴 Zero abstentions, on every rung

| rung | questions reported `answerable: false` |
|---|---:|
| `rung-seed` | 0 / 124 |
| `rung-00100` | 0 / 124 |
| `rung-00200` | 0 / 124 |
| `rung-00500` | 0 / 124 |
| `rung-01000` | 0 / 124 |

The key contains **12 `unanswerable` questions** — that count is recorded in
[W-145](../../open/W-145-codex-regenerates-the-key.md), not read from the key.
So `abstain_correct` on the unanswerable slice is **0 of 12 at every rung**,
and that conclusion needs no scoring pass.

**Band distribution, per rung, absolute:**

| rung | grounded | partial | weak |
|---|---:|---:|---:|
| `rung-seed` | 26 | 74 | 24 |
| `rung-00100` | 29 | 53 | 42 |
| `rung-00200` | 29 | 53 | 42 |
| `rung-00500` | 31 | 53 | 40 |
| `rung-01000` | 32 | 53 | 39 |

`weak` is reached — 39 of 124 at rung 1 000 — but `weak` is not
`answerable: false`. **The band moves; the abstention decision does not.**

This is the third time this question has come back with the same answer. The
open blocker records an abstention re-run at 20/20 with 0 flips, twice. This is
a 124-question, five-rung instance of it, on purpose-built data.

### 4.2 🔴 The retired document outranks its successor about half the time

Four seed supersession pairs are declared, and the index carries the
`superseded` flag on all four retired documents (§2 coverage). Counting, per
rung, the ranked lists where **both halves of a pair appear**, and how often the
retired half is placed **above** its successor:

| rung | pairs co-ranked | retired above successor | share |
|---|---:|---:|---:|
| `rung-seed` | 145 | 74 | 51 % |
| `rung-00100` | 50 | 29 | 58 % |
| `rung-00200` | 46 | 24 | 52 % |
| `rung-00500` | 43 | 23 | 53 % |
| `rung-01000` | 38 | 21 | 55 % |

**A declared supersession is landing at about a coin flip.** Whatever
`superseded_weight` is contributing, it is not enough to order a pair the
corpus explicitly labels. 145 co-ranked pairs at `rung-seed` is real headroom —
this is the input the prior acts on, present and countable.

⚠ **This is a DOCUMENT-plane finding, and the passage plane does not share it.**
On *"what is the diesel surcharge percentage"* at `rung-seed`, `fux ask` returns
the retired card first (6.257) and its successor second (6.145) — but
`fux answer` returns `seed/12-rate-card-2026-h2.md:L28-L32`, the **current**
rule, with the retired passage second. Re-scoring on the fetched bytes puts it
right where document ranking did not.

**So the finding is narrower and more useful than "supersession is broken":
which endpoint a caller reads decides whether the inversion is visible at all.**
Any `superseded_weight` sweep must name its endpoint before it runs, or it
measures two different things and averages them.

### 4.3 An archived document is the top result for 16 questions

| rung | top-1 is `seed/archive/` | top-1 is `ext/archive/` |
|---|---:|---:|
| `rung-seed` | 16 | — |
| `rung-00100` | 16 | 2 |
| `rung-00200` | 14 | 2 |
| `rung-00500` | 14 | 2 |
| `rung-01000` | 14 | 2 |

`g001` is the clean case: *"max hours a driver can be on duty in a day"* returns
`seed/archive/a04-driver-hours-policy-2019.md` at rank 1 and the in-force
`seed/08-driver-hours-and-safety-policy.md` at rank 2, on **every** rung — and
the `fux answer` passage is drawn from the 2019 document, so the answer a reader
sees is the retired rule.

---

## 5. An upper bound on `hit@5`, derivable without the key

Every answer-bearing document is under `seed/`. `ext/` states no fact about any
seed entity by construction, and the generator refuses to write one that does —
so a ranked list with **no `seed/` path in its top 5 cannot score `hit@5`**,
whatever the key says.

| rung | questions with no `seed/` document in the top 5 | so `hit@5` ≤ |
|---|---:|---:|
| `rung-seed` | 0 | 124 / 124 |
| `rung-00100` | 16 | 108 / 124 |
| `rung-00200` | 18 | 106 / 124 |
| `rung-00500` | 28 | 96 / 124 |
| `rung-01000` | 30 | 94 / 124 |

The thirty ids at rung 1 000 are listed in
[`ANALYSIS.md`](ANALYSIS.md) §3. **This is a bound, not a score** — a seed
document in the top 5 is necessary for `hit@5`, not sufficient, and the actual
figure is Codex's to produce.

---

## 6. Headroom disclosure (ADR-RS decision 22)

Single-arm run; no paired endpoint, and §1 forbids the delta that would need
one. Disclosed per rung, from the per-query rows, and **labelled unproven** —
this run carries no feature-off/on arm and no generator `--selftest`
establishing separability (22c). Unproven is disclosed, not voided.

| rung | improvement headroom (ids not top-1 on a `seed/` path) | regression headroom (ids top-1 on a `seed/` path) |
|---|---:|---:|
| `rung-seed` | 0 | 124 |
| `rung-00100` | 43 | 81 |
| `rung-00200` | 49 | 75 |
| `rung-00500` | 49 | 75 |
| `rung-01000` | 48 | 76 |

⚠ `rung-seed` shows **zero improvement headroom** on this proxy, because with
only seed documents present every top-1 is trivially a `seed/` path. Per 22d
that direction is **Inconclusive at `rung-seed`**, not "no detected change" —
and it is exactly the saturation the 2026-08-28 `heading` control ran into.
**`rung-seed` is not a discriminating rung for anything ranking-related**, and a
later run should not use it as one.

---

## 7. What this run does not do

- It files **no verdict** and closes **no prediction**.
- It states **no delta**, in any direction.
- It says nothing about 2 000, 5 000 or 10 000 documents; those rungs are not
  built, and per the 2026-08-22 ceiling nothing above 10 000 is even discussed.
- It does not score. `hit@1`, `hit@5`, `recall@5`, `rank_first_relevant` and
  `abstain_correct` are Codex's, in phase 5, from
  `evidence/<rung>/predictions.jsonl`.

---

## Reference

- Pre-registration, frozen first: [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md)
- The answers to grade: [`ANSWERS-FOR-REVIEW.md`](ANSWERS-FOR-REVIEW.md)
- Diagnosis and repro commands: [`ANALYSIS.md`](ANALYSIS.md)
- Process: [`work/golden/README.md`](../../golden/README.md) · item:
  [W-136](../../open/W-136-golden-benchmark.md)
- Why `informed`: [W-145](../../open/W-145-codex-regenerates-the-key.md)
- Authorship, classification, per-query rows, headroom, test-data coverage:
  [ADR-RS](../../../docs/adr/0133_predictions.md) decisions 11–15, 22, 23
