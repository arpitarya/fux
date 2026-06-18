# Debate transcript — con-amendment-v2 (supersedes con-amendment: adds the "is this constitutional?" test)

**Rule under debate (tier: constitutional):** con-amendment-v2 supersedes con-amendment, adding ONE
additive clause — the authoring heuristic for whether a rule belongs in the constitutional tier.
**Date:** 2026-06-18 · **Format:** two-agent free debate (no assigned sides, blind first passes) →
reveal/cross-examination → human tie-break. **Harness:** `$0`, deterministic; intelligence is the
host session's tokens. **Ratifier:** Arpit (pending). **Predecessor:** con-amendment → deprecated.

---

## Blind first pass — Reviewer A

**Position: ADOPT.** This is the textbook legitimate amendment: a single, additive, normative clause
landed by supersession (new id, `edges.supersedes: [con-amendment]`, predecessor deprecated, fresh
debate). It dogfoods the very rule it amends — the first real test of whether the meta-rule binds its
own author, and it passes by being done the hard way rather than re-stamped in place.

Objections:
1. **Single-concern discipline.** v2 must carry ONLY the heuristic. The four converged-wording
   enforcements (supersedes-edge check, predecessor→deprecated, minimum-transcript-content,
   constitutional-successor tier) are NOT eligible here — they are not yet built, so folding them in
   would re-introduce the aspirational-vs-code gap the founding debate disclosed. Keep them for a v3
   once the engine supports them. v2 stays additive prose, enforceable today. **Sustained.**
2. **The "trust" leg is the fuzziest of the four costs** (money/PII/audit/trust). Trust is real but
   elastic — almost anything can be argued to "cost trust." The `AND` half (never legitimately
   changes) is what keeps it honest: a rule that flexes is disqualified no matter how much trust is
   at stake. The conjunction is load-bearing; keep it explicit.

## Blind first pass — Reviewer B

**Position: ADOPT.** The heuristic earns its place: the residual risk after Phase 0–5 is humans
mis-tiering rules, and a one-line test at authoring is the cheapest possible guard. It is decidable by
a human at authoring time, needs no new code, and reads as policy, not implementation.

Objections:
- **(a) The test must catch BOTH failure modes, not just over-reach.** Over-constitutionalizing
  (locking a rule that should flex) and under-constitutionalizing (leaving a money/PII invariant in
  the mutable tier) are equal harms. The wording must name both so it isn't read as a one-way ratchet
  toward fewer constitutional rules. **Adopted into the wording.**
- **(b) Don't make the test a deterministic gate.** Whether a wrong answer "costs trust" or a rule
  "never legitimately changes" is judgment — exactly the kind of call the deterministic/judgment split
  says no `$0` check can make. The heuristic belongs in `/fux debate` as a surfaced *prompt* to the
  human ratifier, never as a machine block. Surfacing ≠ enforcing.

## Reveal + cross-examination

Both reviewers converge immediately — no assigned sides, and the proposal is narrow:

- A and B agree on **single-concern** (objection 1): v2 = the heuristic only; the four enforcements
  are filed as v3 + tracked Phase-2 work. Mixing correction-lane policy with the heuristic would make
  a worse audit unit.
- B-a is folded in: the converged clause names **both** over- and under-constitutionalizing.
- B-b sets the integration contract: the debate skill **surfaces** the test when a proposal is tagged
  `tier: constitutional`; it does not add a deterministic check. A concurs — a judgment test faked as
  a machine gate would itself violate the split.
- A-2 (the `AND` is load-bearing; "trust" is elastic) is kept in the wording: both halves required.

## Converged wording (both reviewers)

> **Is this constitutional? (the authoring test):** A rule belongs in the constitutional tier **only
> if** a wrong answer costs money, PII, audit, or trust **and** the rule never legitimately changes.
> If either half fails — the stakes are ordinary, or the rule is expected to evolve — it is a
> `standard` rule, not constitutional. This test stops both over-constitutionalizing (locking down
> rules that should flex) and under-constitutionalizing (leaving a must-never-break invariant in the
> mutable tier).

## RESIDUAL CRUX — for the human ratifier

None blocking. One disclosed decision: the heuristic is a **judgment** test, surfaced by `/fux debate`
to the human, never a deterministic gate (no `$0` check can decide "costs trust" / "never legitimately
changes"). The ratifier confirms this is the intended contract.

### Human tie-break (Arpit, 2026-06-18) — RULING

- **ADOPT con-amendment-v2 by supersession.** New id, `edges.supersedes: [con-amendment]`, predecessor
  con-amendment marked `status: deprecated` and re-ratified in its deprecated state (re-stamping the
  seal after a sanctioned lifecycle event — the body is unchanged), v2 ratified with this transcript.
  This is the constitution's first real amendment, and it is landed the hard way on purpose: the cost
  is the proof the system binds its own author.
- **Single-concern upheld:** v2 carries only the authoring heuristic. The converged wording's four
  enforcements remain the tracked Phase-2 follow-up and will land as a later supersession (v3) once
  the engine enforces them.
- **Integration contract:** `/fux debate` surfaces this test when a proposal is tagged
  `tier: constitutional`; it is never a deterministic check.
- **Ratifier of record:** arpit arya (git user.name).

## Implementation debt this wording commits us to (disclosed)

The heuristic itself is enforceable today (it is authoring-time guidance surfaced by the debate skill,
not engine logic). The **supersedes-edge check** — the engine should reject re-stamping a constitutional
rule whose body changed without a declared supersession, and validate that a successor declares
`edges.supersedes` + is itself `tier: constitutional` — is **still not built**. This very amendment is
live evidence for its priority: right now the human upholds the supersession discipline the engine
cannot yet enforce. Filed in the Phase-2 follow-up with that concrete reason.
