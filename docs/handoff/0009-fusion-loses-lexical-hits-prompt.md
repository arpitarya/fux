---
type: Prompt
title: Fusion loses lexical top-5 hits (phase 9) — Claude Code prompt
description: Paste-ready prompt executing handoff 0009 — correct the misdiagnosed "non-monotone fusion" finding, measure how often hybrid loses a lexical top-5 hit across all four eval sets, and take the guard-vs-accept-vs-fix-the-input fork through a compare doc. "No engine change" is a valid outcome.
status: ready
timestamp: 2026-07-24T00:00:00Z
tags: [fusion, retrieval, rrf, correctness]
---

# Prompt — phase 9: fusion loses lexical top-5 hits

**Model: Opus.** The code is easy; the deliverable is a judgment about a
*guarantee*. §2 of the handoff already disproves the filed framing — an
under-powered model will read it, agree, and then ship a fix for a bug that does
not exist.

---

You are diagnosing a filed engine finding and deciding what, if anything, to do
about it. Full spec: `docs/handoff/0009-fusion-loses-lexical-hits-handoff.md` —
read it first; its Definition of Done and Non-negotiables are binding.

## The situation (then go read)

The orbit run filed *"fusion is not monotone — hybrid demoted a lexical rank-5
hit out of top-5."* **That framing is wrong, and the handoff's §2 proves it:**
RRF is provably monotone in per-list rank, and the reported case reconciles to
the exact specified arithmetic to five decimals. The document lost because its
dense signal was near noise (0.3297 vs the 0.23–0.26 band) — two of three lists
voted against it.

So this phase is **not** a bug hunt. It is: correct the record, measure how big
the population really is, and decide a product question.

## Context to load first

- `docs/handoff/0009-fusion-loses-lexical-hits-handoff.md` — **§2 first**; it
  changes what this phase is.
- `docs/conformance/2026-07-24-orbit-fulfillment/ANALYSIS.md` §Finding 3 — the
  original filing.
- `docs/conformance/2026-07-24-v0.26.0-release-verification/ANALYSIS.md` — where
  `zero_overlap_demoted` came from.
- `src/fux/index/fuse.py` and `_passages` in `src/fux/kernel.py` — the fusion
  path. **Three lists** fuse (`bm25f`, `dense`, `dense_global`); arithmetic that
  ignores the third will not reconcile.
- ADR 0010 (the dense noise band), ADR 0015 (the gate any ranking change clears).
- `CLAUDE.md`, `docs/INTERVIEW.md` — read before your first change.

## Required workflow — order matters

1. **Reproduce §2 yourself** before accepting it. Run the two repro commands and
   confirm the arithmetic reconciles. If it does not, STOP and tell me — that
   would mean the pre-work is wrong and the phase changes shape.
2. **M1 — Correct the record.** Amend the orbit ANALYSIS's "non-monotone"
   wording and the `zero_overlap_demoted` description to the accurate statement.
   Correct in place, clearly marked; do not rewrite history. No code.
3. **M2 — Measure the population.** Extend the lab harness to report
   *lexical-top-5-lost* across **all question kinds** and **all four eval sets**
   (fixture, acme, orbit, synthetic). Also check whether the supersession offset
   (`0` vs `15`) ever *creates* such a demotion. File the run into
   `docs/conformance/` with evidence and repro commands, per CLAUDE.md law.
4. **M3 — Compare doc.** Take the fork: **guard** (hybrid never loses a lexical
   top-5 hit) vs **accept** (fusion means fusion) vs **fix the input**
   (chunk-level dense codes own this). Debate, matrix, grounded references,
   reopen-trigger, proposed verdict. **Pause for my verdict.**
5. **M4 — Execute the verdict.** Either implement + ADR, or close out and
   graduate the finding into the dense-codes phase with its evidence attached.
6. **M5 — Close out.** Docs, archive, trackers.

Update `docs/IMPLEMENTATION.md` at **every** milestone and on **every** outcome
including failure or abandonment (🟡/⛔). CLAUDE.md law.

## Constraints (hard)

- **Do not "fix" monotonicity — it is not broken.** A patch that special-cases
  lexical rank to make the symptom disappear is an unjustified ranking change.
- **"No engine change" is a correct, valid outcome.** If the evidence says this
  is the zero-overlap/dense-quality defect seen from the fusion side, say so and
  close it. Do not manufacture a fix because a phase was opened.
- Any fusion change is gated on the **four-eval-set sweep** (ADR 0015's bar):
  zero hit@5 regression on any gate, in any question kind.
- `--lexical-only` stays **byte-identical**. Hybrid goldens change only with eval
  evidence.
- Do not touch: the supersession penalty's calibrated default (15), BM25F params,
  FuxVec, the confidence floor, `archive/`.
- `$0`/stdlib-only, deterministic, **no model** in the path.
- Read `gh pr checks` yourself; never merge red.
- Docs style: short points, roomy.

## Acceptance criteria (self-check)

- [ ] §2's arithmetic independently reproduced before anything else
- [ ] Filed "non-monotone" wording corrected in place, marked
- [ ] lexical-top-5-lost measured across all four eval sets and all kinds
- [ ] Supersession-offset interaction checked (`0` vs `15`), result stated
- [ ] Conformance run filed with evidence + repro commands
- [ ] Compare doc written; my verdict recorded
- [ ] Verdict executed — implementation + ADR, or documented close-out
- [ ] Both suites green; trackers updated; handoff+prompt archived

## Guardrails

- **Ask before:** changing any fusion code, changing hybrid goldens, editing
  CLAUDE.md or the README's guarantees, anything irreversible.
- **If M2 finds the rate is ~1 question per corpus**, that is the finding — it
  argues for accept-and-document, and you should say so plainly rather than
  building a guard for an n=1 population.
- **If the guard option wins**, measure its interaction with the supersession
  penalty explicitly: a superseded document at lexical rank ≤5 would be
  *protected* by a lexical-preserving guard, partly undoing what v0.26.0 shipped.
- If a requirement is ambiguous or conflicts with the code, **STOP and ask**.

## What's next after this (not in scope)

- **Chunk-level dense codes** — the structural fix for zero-overlap recall, and
  quite possibly the real owner of this finding. Its own phase.
- **Query-at-scale** (ADR 0011) — a 100k query still loads the whole index.
