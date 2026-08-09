---
type: Conformance Analysis
status: final
date: 2026-07-24
run: 2026-07-24-supersession-penalty-calibration
engine: fux 0.26.0 (supersession_penalty knob, phase 7 M2)
corpora: fixture (21 pairs) · acme-payments (55) · orbit-fulfillment (53) · synthetic 1k/5k/10k
---

# Analysis — supersession penalty calibration, and the margin re-measurement it unblocked

## What this run was for

Two questions, one experiment — because the second could not be answered
honestly until the first was fixed:

1. **M3 — is there a penalty magnitude that recovers staleness inversions
   without regressing hit@5 on any eval gate?** The reopen-trigger's second
   clause, untested until now.
2. **M4 — does the runner-up margin separate fabrications once superseded twins
   stop tying?** The orbit run refuted the margin check but flagged the
   refutation as *confounded*: the smallest "answerable" margins came from
   documents tying with their own retired versions.

## Headline

| question | verdict |
|---|---|
| safe penalty interval | **NON-EMPTY — `[11, ∞)` measured to 500** |
| inversions recovered | **100% of the frontmatter-reachable ones, both corpora** |
| hit@5 regression | **zero, on every gate, at every value tested** |
| hit@1 | **improves** — orbit 0.566 → 0.698, acme 0.491 → 0.564 |
| margin check after de-confounding | **still empty — refuted independently** |
| fabrication | **permanent no-model boundary, now established** |

The penalty result is unusually clean. **The margin result is a negative, and it
is reported as one** — de-confounding was necessary to make the test fair, and
the test still fails.

## Method

- Engine: `fux 0.26.0` built as a wheel from the working tree
  (`uv build --wheel`), installed into each environment's venv. acme is an
  editable install of the same tree.
- **The penalty is read at query time**, so no re-ingest is needed between
  values. That is what made a 14-value sweep affordable.
- Every measurement drives the `fux` binary through `subprocess`; the sweep
  harness never imports `fux`.
- Harness validated against published numbers **before** any sweep: at penalty
  `0`, orbit reproduces `8/12` inversions, hit@1 `0.566`, hit@5 `0.887` —
  matching `2026-07-24-orbit-fulfillment/ANALYSIS.md` exactly.
- Each environment's `fux.toml` is restored in a `finally` block, so a failed
  sweep cannot leave a corpus configured.

```bash
python3 evidence/sweep.py ~/my_programs/fux-lab/orbit \
    ~/my_programs/fux-lab/orbit/.venv/bin/fux 0,1,2,3,5,8,10,15,20,30,50,100,200,500
```

## M3 — the calibration curve

### orbit-fulfillment (independent domain, 6/12 marked by construction)

| penalty | inversions | hit@1 | hit@5 | MRR |
|---|---|---|---|---|
| **0** (shipped) | **8/12** | 0.566 | 0.887 | 0.723 |
| 1 | 5/12 | 0.660 | 0.887 | 0.770 |
| 2 | 4/12 | 0.698 | 0.887 | 0.789 |
| 5 | 4/12 | 0.698 | 0.887 | 0.789 |
| **8** | **3/12** | **0.698** | **0.887** | **0.789** |
| 15 – 500 | 3/12 | 0.698 | 0.887 | 0.789 |

### acme-payments (5/12 marked, accidentally)

| penalty | inversions | hit@1 | hit@5 | MRR |
|---|---|---|---|---|
| **0** (shipped) | **9/12** | 0.491 | 0.855 | 0.665 |
| 1 | 8/12 | 0.509 | 0.855 | 0.674 |
| 2 | 7/12 | 0.545 | 0.855 | 0.692 |
| 5 – 10 | 7/12 | 0.564 | 0.855 | 0.702 |
| **11** | **6/12** | **0.564** | **0.855** | **0.703** |
| 12 – 500 | 6/12 | 0.564 | 0.855 | 0.703 |

### The gates that hold it honest

- **Fixture gate (21 pairs): perfectly flat** at every value — hybrid hit@1
  0.810, hit@5 1.000, MRR 0.873; lexical hit@5 0.952.
- **Synthetic 1k / 5k / 10k: byte-identical** at 0, 5, 50, 500.
- **Both flat lines are a no-op proof, not evidence of recovery.** The fixture
  corpus and the synthetic generator contain **zero** supersession markers
  (`grep -rl superseded` → 0 files). They prove the penalty cannot touch an
  unmarked corpus; they say nothing about how well it fixes a marked one. Stated
  explicitly so the four-gate sweep is not over-read.

### Per-kind — never the aggregate alone

Zero kinds regressed on either corpus, at any value from 1 to 500:

| kind | orbit p0 → p8 (hit@1/hit@5) | acme p0 → p11 |
|---|---|---|
| factual | 0.471/0.941 → **0.647**/0.941 | 0.333/1.000 → **0.500**/1.000 |
| stale-vs-current | 0.333/0.917 → **0.667**/0.917 | 0.167/0.833 → **0.333**/0.833 |
| why | 0.875/1.000 → unchanged | 0.909/1.000 → unchanged |
| how-to | 1.000/1.000 → unchanged | 0.875/1.000 → unchanged |
| cross-doc | 0.750/1.000 → unchanged | 0.500/0.833 → unchanged |
| zero-overlap | 0.333/0.333 → unchanged | 0.167/0.167 → unchanged |

### The decisive detail: the penalty recovers exactly what it can reach

Cross-referencing every inversion against whether its retired document actually
carries frontmatter:

| corpus | marked inversions | recovered | unmarked inversions | recovered |
|---|---|---|---|---|
| orbit | 5 | **5 (100%)** | 3 | 0 |
| acme | 3 | **3 (100%)** | 6 | 0 |

**Perfect separation.** Every frontmatter-marked inversion is fixed; every
residual one is a document whose author left no machine-readable marker. The
residual is not a tuning shortfall — it is the no-NLP constraint, showing up
exactly where the compare doc predicted it would.

### Reading the "majority" gate honestly

DoD 5 asks for "a majority of inversions recovered." Against **all** inversions:

- orbit **5 of 8 = 62%** — a majority.
- acme **3 of 9 = 33%** — **not** a majority.

Against the **reachable** set it is 100% on both. Both framings are stated
because they lead to different answers, and choosing the flattering one silently
would be exactly the kind of quiet reinterpretation this project's gates exist to
prevent. **The judgment is Arpit's, not this run's.**

## M4 — the margin re-measurement (Finding 2)

Re-collected top-vs-runner-up margins on all 57 orbit and 55 acme questions at
penalty `15`, and compared against penalty `0`.

### The confound was real — and it was not the cause

**orbit, smallest answerable margins:**

| rank | penalty 0 | penalty 15 |
|---|---|---|
| 1 | 1e-05 `factual` — pick wave lines | 1e-05 `stale-vs-current` — parcel carrier |
| 2 | **1e-05 `how-to` — inbound ASN** | **1e-05 `how-to` — inbound ASN** |
| 3 | 7e-05 `zero-overlap` | 7e-05 `zero-overlap` |

- The previously-minimal `factual` question **did** improve — the confound was
  genuine, and de-confounding did what it was supposed to.
- **A `how-to` question sits at 1e-05 before and after, unmoved.** Its tiny
  margin has nothing to do with supersession: two documents genuinely agree.
- **Unanswerable margins are completely unchanged** (0.00052 – 0.00411) in both
  corpora — as they must be, since no unanswerable question involves a retired
  twin.

**acme: identical before and after**, and its minimum is held by a `cross-doc`
question (1e-05) — supersession was never involved at all.

### Verdict on Finding 2 — refuted independently, and closed

| discriminator | acme | orbit | orbit de-confounded |
|---|---|---|---|
| absolute floor | empty | empty | **empty** |
| runner-up margin | empty | empty & inverted | **empty & inverted** |
| margin ratio | empty | empty | **empty** |

`max(unanswerable) = 0.00411` still exceeds `min(answerable) = 1e-05` by **two
orders of magnitude**. The margin check is refuted on its own merits, not as a
side-effect of the staleness defect.

**And the residual failure mode is the one the compare doc predicted a year of
reasoning ago:** acme's minimum is a `cross-doc` question — *"when several
documents genuinely agree on an answer, their scores are legitimately close. A
margin check declines precisely there."* That was written as an argument against
Option B before anyone measured it. It is now measured.

**Fabrication on well-formed out-of-scope questions is a permanent product
boundary of extractive answering without a model.** Three no-model
discriminators — absolute floor, runner-up margin, margin ratio — are now
refuted across two independent corpora, one of them de-confounded. No fourth
mechanism is proposed, and inventing one to force a fix would be the wrong move.

## `fux why` surfaces the penalty (DoD 7)

Real output, orbit, penalty 15 (`evidence/why-penalty.txt`):

```
docs/adr/0012-same-day-cutoff-1200.md
  superseded: true → docs/adr/0024-same-day-cutoff-1400.md
  superseded → rrf penalised by 15 ranks (rank 1→17)
  lexical: rank=2 score=34.9969 in_pool=True (pool=200)
  dense: similarity=0.7016 in_prefilter=True hamming=59 (width=500)

verdict: not returned at --top 5: rank 17 overall (raise --top to 17 to see it)
```

The retired document moved from **rank 1 to rank 17** and **is still
retrievable** — a demotion, not a filter, exactly as the pre-mortem required.

## Specific engine decisions this run supports

1. **A safe interval exists: `[11, ∞)`.** Recommended default **15** — inside
   the plateau, clear of the 11 boundary, far from any measured harm. Enabling
   it by default is Arpit's call (M5); the knob ships either way.
2. **Report reachable recovery, not raw recovery.** The penalty's ceiling is the
   marked set. A metric that ignores this understates a mechanism working at
   100% of its designed reach.
3. **Close the fabrication line.** Convert it from an open defect into a
   documented boundary in README/PLAN, and keep the floor knob permissive.
4. **The unmarked residual is the reason to evangelise `superseded_by:`** —
   documentation, not engineering, is the remaining lever.

## Unresolved — stated as unresolved

- **Why the plateau sits where it does** (orbit 8, acme 11) is not isolated. It
  is consistent with "the penalty must exceed the rank gap RRF was flipping," but
  no experiment here varies the gap independently.
- **No upper bound was found.** Values to 500 show no harm, but "no harm at 500
  on three marked corpora" is not proof that a very large penalty is safe on a
  corpus where a superseded document is the best answer to an unrelated query.
  The unit test covers the shape of that case; no real corpus exercises it.
- **The graph-refusion path is deliberately un-penalised** (see ADR 0015). No
  corpus here shows a superseded document being re-promoted by graph expansion,
  but none was constructed to try.
- **Only frontmatter-marked docs are reachable, permanently.** 3/12 (orbit) and
  6/12 (acme) inversions cannot be fixed without a model.

## Files

- `evidence/orbit-sweep.json`, `acme-sweep.json`, `acme-fine.json` — full curves.
- `evidence/fixture-sweep.json`, `1k/5k/10k-sweep.json` — the no-op gates.
- `evidence/orbit-margin-p0.json` / `-p15.json` — the de-confounding pair.
- `evidence/acme-margin-p0.json` / `-p15.json` — acme's unchanged pair.
- `evidence/why-penalty.txt` — DoD 7, human + `--json`.
- `evidence/sweep.py`, `fixture_sweep.py` — the harnesses, for exact repro.
