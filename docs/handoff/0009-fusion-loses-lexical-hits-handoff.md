---
type: Handoff
title: Fusion loses lexical top-5 hits — diagnose, then decide (phase 9)
description: The "non-monotone fusion" finding is a misdiagnosis — RRF is provably monotone in per-list rank, and the reported demotion reconciles to the exact specified arithmetic. The real question is a product one: should hybrid be allowed to lose a document lexical alone would have returned? Diagnose the population, then take the fork through a compare doc.
status: ready
timestamp: 2026-07-24T00:00:00Z
tags: [fusion, retrieval, rrf, correctness]
---

# Handoff: Fusion loses lexical top-5 hits (phase 9)

**Model: Opus.** Not because the code is hard — the mechanism is already solved
below — but because the deliverable is a **judgment about a guarantee**: whether
hybrid should be constrained never to lose what lexical alone would have found.
That trades one failure mode for another, and no test settles it. An
under-powered model will read the pre-work below, agree, and ship a "fix" for a
bug that does not exist.

**One-liner:** the orbit run filed *"fusion is not monotone — hybrid demoted a
lexical rank-5 hit out of top-5."* **The monotonicity claim is false.** The
demotion is correct RRF arithmetic over a weak dense signal. What remains is a
real but different question, and it may already belong to another phase.

**Owner / executor:** Claude Code
**Status:** Ready. No blockers. **Read §2 before planning anything** — it
changes what this phase is.

## 1. Context & background

- Filed by `docs/conformance/2026-07-24-orbit-fulfillment/` as a named engine
  finding: *"One active regression: hybrid pushed a lexical rank-5 hit out of
  top-5. Fusion is not monotone — it can lose a document lexical alone would
  have found."*
- Phase 8 made it **auto-detected** rather than anecdotal: the suite's new
  `zero_overlap_demoted` metric fires at **1** on orbit
  (`docs/conformance/2026-07-24-v0.26.0-release-verification/`).
- It was deliberately left untouched through the v0.26.0 release — fusion is not
  something to patch mid-release.

## 2. Pre-work already done — READ THIS FIRST

**Do not start by hunting a monotonicity bug. There isn't one.** This was
diagnosed while closing phase 8; the evidence is reproduced here so this phase
starts from the truth rather than the filed framing.

### 2a. RRF is monotone in per-list rank — provably, in one line

`RRF(d) = Σ_r 1/(k + rank_r(d))`. Each term `1/(k + rank)` is **strictly
decreasing in `rank`** for `k > 0`. Improving a document's rank in any list, all
else equal, strictly increases its fused score. There is no non-monotonicity to
find.

The filed claim conflates two different properties:

| property | true? |
|---|---|
| RRF is monotone in per-list rank | **yes**, by construction |
| RRF is rank-*preserving* w.r.t. a single input list | **no — and that is what fusion IS** |

A fusion method that could never reorder relative to one input list would be
that input list.

### 2b. The reported case reconciles to the exact specified arithmetic

Query: *"How is inventory accuracy verified without shutting the warehouse?"*
(orbit, `zero-overlap`). Expected doc: `docs/notes/counting-without-closing.md`.

Three lists fuse: `bm25f`, `dense`, `dense_global`. With `rrf_k = 60`:

| document | bm25f | dense | dense_global | computed | reported |
|---|---|---|---|---|---|
| `local-simulator.md` (hybrid #1) | 2 | 2 | 2 | `3 × 1/62` = **0.048387** | 0.04839 |
| `packing-guide-08.md` (hybrid #2) | 13 | 1 | 1 | `1/73 + 2 × 1/61` = **0.046485** | 0.04649 |
| **`counting-without-closing.md`** (hybrid #23) | **5** | **56** | **117** | `1/65 + 1/116 + 1/177` = **0.029655** | 0.02966 |

**All three reconcile to five decimals.** The fusion code is doing exactly what
it is specified to do.

### 2c. The actual mechanism — a weak dense signal, faithfully propagated

The correct document loses because **two of its three lists vote against it**:

- dense similarity **0.3297** — barely above the **0.23–0.26 noise band** ADR
  0010 measured. `dense_rank = 56`, `dense_global_rank = 117`.
- The document that beats it has *worse* lexical (rank 13 vs 5) and *much*
  better dense (0.4895, rank 1).

So this is **not a fusion defect. It is a dense-retrieval-quality defect**, on
precisely the `zero-overlap` class the dense plane exists to serve — and fusion
correctly propagates the weakness of its input.

**That defect already has a scoped owner: chunk-level dense codes.** Part of this
phase's job is to decide whether this finding collapses into that phase entirely.

### 2d. The supersession penalty is NOT implicated

- The demoted document is **not superseded** (`superseded: false`, no penalty
  applied) — verified directly with `fux why --json`.
- The finding **predates v0.26.0**: it was filed from the 0.25.0 orbit run,
  before the penalty existed.
- The open question *"does the supersession offset interact with this?"* is
  therefore answered **no** for this case. Whether it can interact **in general**
  is still worth one bounded check (§5.2) — an offset is a rank shift, and rank
  shifts are the input to exactly this arithmetic.

Repro:
```bash
cd ~/my_programs/fux-lab/orbit/corpus
../.venv/bin/fux ask "How is inventory accuracy verified without shutting the warehouse?" --json --top 30
../.venv/bin/fux why "How is inventory accuracy verified without shutting the warehouse?" \
    --doc docs/notes/counting-without-closing.md --json
```

## 3. What this phase is actually for

The mechanism is settled. **The open question is a product guarantee:**

> Should `fux ask`/`find` in hybrid mode be constrained never to drop a document
> that `--lexical-only` would have returned in its top-5?

That is a genuine fork with real costs on both sides, so it goes through a
**compare doc** (CLAUDE.md step 0), not straight to code.

- **Yes (add a guard).** Hybrid becomes a strict improvement over lexical — a
  clean, explainable promise. Costs: it constrains fusion permanently, needs a
  merge rule, and the guaranteed slots are taken from genuinely-fused results.
- **No (accept it).** Fusion means fusion; a document with one strong and two
  weak signals *should* lose. Costs: hybrid can be worse than lexical on
  individual questions, which is exactly what orbit measured (hit@1 0.642
  lexical vs 0.566 hybrid at 0.25.0).
- **Neither — it's the dense plane's fault.** Fix input quality (chunk-level
  dense codes) and the symptom disappears without touching fusion at all.

**A defensible outcome is "no engine change; this is the zero-overlap phase in
disguise."** Say so plainly if that is what the evidence supports.

## 4. Definition of done

- [ ] **DoD 1 — The filed finding is corrected.** `zero_overlap_demoted`'s
      description and the orbit ANALYSIS's "fusion is not monotone" wording are
      amended to the accurate statement (monotone per-list; not rank-preserving
      w.r.t. one list). Correct in place, marked — do not rewrite history.
- [ ] **DoD 2 — The population is measured, not extrapolated.** How often does
      hybrid lose a lexical top-5 hit, across **acme + orbit + fixture +
      synthetic**, over **all** question kinds (not just `zero-overlap`)? n=1 is
      an anecdote; this phase needs the rate and the affected kinds.
- [ ] **DoD 3 — The interaction check.** Does a supersession offset ever
      *create* such a demotion? Bounded: sweep penalty `0` vs `15` and compare
      the lexical-top-5-lost set. Expected answer no; measure it.
- [ ] **DoD 4 — A compare doc** in `docs/compare/` taking the §3 fork: guard vs
      accept vs fix-the-input. Debate, matrix, grounded references,
      reopen-trigger, proposed verdict for Arpit.
- [ ] **DoD 5 — Arpit's verdict recorded**, then either (a) an ADR + the
      implementation, or (b) an ADR-free close-out that graduates the finding
      into the chunk-level-dense-codes phase with the evidence attached.
- [ ] **DoD 6 — No fusion change ships without the four-eval-set gate** that
      ADR 0015 established: zero hit@5 regression on any gate, any question kind.
- [ ] **DoD 7 — Docs:** PLAN, IMPLEMENTATION (per milestone), WORKLOG,
      DOC-REGISTRY, GLOSSARY if a term lands; handoff+prompt archived.

## 5. Milestones

- **M1 — Correct the record.** DoD 1. No code. Small and first, so nobody
  inherits the wrong framing again.
- **M2 — Measure the population.** DoD 2 + DoD 3. Extend the lab harness to
  report lexical-top-5-lost across all kinds and all four eval sets. This is the
  phase's real evidence.
- **M3 — Compare doc.** DoD 4. Pause for Arpit's verdict.
- **M4 — Execute the verdict.** DoD 5/6 — implementation + ADR, or a documented
  close-out into the dense-codes phase.
- **M5 — Close out.** DoD 7.

## 6. Non-negotiables

- **Do not "fix" monotonicity.** It is not broken. A patch that makes the symptom
  go away by special-casing lexical rank is a ranking change with no measured
  justification — the exact blind tuning this project forbids.
- **Any fusion change is gated on the four-eval-set sweep** (ADR 0015's bar) and
  on `--lexical-only` staying byte-identical.
- **Do not touch** the supersession penalty's calibrated default, BM25F params,
  FuxVec, or the confidence floor.
- `$0`/stdlib-only, deterministic, **no model** anywhere in the path.
- `main` has no required checks — read `gh pr checks` yourself; never merge red.
- Docs style: short points, roomy.

## 7. Edge cases & risks

- **The most likely outcome is "no change,"** and that must stay comfortable to
  say. The pull toward justifying a fix because a phase was opened is the main
  risk here.
- **A guard interacts with the supersession penalty in an ugly way:** a
  superseded document sitting at lexical rank ≤5 would be *protected* by a
  lexical-preserving guard, partially undoing the penalty v0.26.0 just shipped.
  If the guard option is taken, this interaction must be measured, not reasoned
  about.
- **`dense_global` is the third list** and is easy to forget — any arithmetic
  that ignores it will not reconcile (as §2b shows, two-list sums are wrong).
- **n=1 evidence.** If M2 finds the rate is ~1 question per corpus, that is
  itself the finding, and it argues for accept-and-document.

## 8. Testing & validation

- Unit: none expected unless a guard ships; then the merge rule and its
  tie-breaks, plus `--lexical-only` untouched.
- E2e: goldens change only with eval evidence (phase-4 law).
- Lab: the four-eval-set lexical-top-5-lost measurement (M2), filed to
  `docs/conformance/` like every run.

## 9. Open questions

- **OPEN (Arpit, at M3):** the §3 fork — guard, accept, or fix-the-input.
- **OPEN (M2 may answer):** is this finding distinguishable from the
  zero-overlap/dense-quality finding at all, or is it the same defect seen from
  the fusion side?

## References

- The filed finding: [`../conformance/2026-07-24-orbit-fulfillment/ANALYSIS.md`](../conformance/2026-07-24-orbit-fulfillment/ANALYSIS.md) §Finding 3.
- Auto-detection + the corrected metric: [`../conformance/2026-07-24-v0.26.0-release-verification/ANALYSIS.md`](../conformance/2026-07-24-v0.26.0-release-verification/ANALYSIS.md).
- The fusion baseline: Cormack, Clarke & Buettcher, *Reciprocal Rank Fusion
  Outperforms Condorcet and Individual Rank Learning Methods* (SIGIR 2009) —
  https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf. Note the paper's own
  framing: RRF's value comes precisely from letting corroboration across rankers
  override a single ranker's confidence. **"Hybrid lost a lexical hit" is the
  method working, not failing.**
- The 0.23–0.26 dense noise band that makes 0.3297 a weak signal:
  [`../adr/0010-fuxvec-binary-dense-search.md`](../adr/0010-fuxvec-binary-dense-search.md).
- The gate any ranking change must clear:
  [`../adr/0015-supersession-downrank-penalty.md`](../adr/0015-supersession-downrank-penalty.md).
