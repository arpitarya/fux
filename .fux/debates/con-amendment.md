# Debate transcript — con-amendment (the amendment article)

**Rule under debate (tier: constitutional):** How a constitutional rule is created and changed.
**Date:** 2026-06-17 · **Format:** two-agent free debate (no assigned sides, blind first passes) →
reveal/cross-examination → human tie-break. **Harness:** `$0`, deterministic; intelligence is the
host session's tokens. **Ratifier:** Arpit (pending).

---

## Blind first pass — Reviewer A

**Position: ADOPT-AMENDED.** The enforcement (`constitution.py` content_seal/lock, `provenance.py`,
`findings.py::blocking`) genuinely backs the prose — "never by in-place edit" is mechanically
detectable and always-blocking. But the rule overclaims on two points the code doesn't enforce.

Objections:
1. **Typo-fix / re-ratify tax.** `_VOLATILE` excludes only ratification/seal/updated, so a one-char
   body typo changes `content_seal` → `tampered` → hard block; only sanctioned fix is a full
   supersession cycle. Disproportionate for a cosmetic edit.
2. **"Named human ratifier" is asserted, not verified.** `--by` falls back to `git user.name`
   (`cliconstitution.py:16`) — free text, spoofable by a bot/service account. Engine can't tell a
   human from a script. Should say *recorded* ratifier.
3. **Lost transcript = permanent self-inflicted block** (`provenance.py:38` fires on missing file,
   no `--allow-missing`); only fix is re-ratify. Needs an explicit "re-ratification regenerates
   provenance" escape hatch in the article.
4. **Self-amendment underspecified.** `ratify()` never validates the `supersedes:` edge; a
   `standard`-tier rule could "supersede" con-amendment and escape tamper/lock. Successor must
   itself be constitutional + ratified.

A's amended wording added a *cosmetic-correction exception* (re-stamp the same id for typos).

## Blind first pass — Reviewer B

**Position: ADOPT-AMENDED.** A self-enforcing meta-rule that is `$0`, deterministic, stdlib-only and
already shipped is exactly what belongs in the constitution. The machinery backs every clause.

Objections:
- **(a) Bootstrap deadlock, live now.** con-amendment is itself un-ratified, lock empty, no
  `.fux/debates/`. The rule mandating a debate has no debate of its own. Ratify with no `--debate` →
  `debate_hash=None` → `check_provenance` returns early (`provenance.py:35`): the founding rule is
  exempt from its own evidence requirement. Needs a **genesis clause**.
- **(b) "recorded debate" is unvalidated.** `transcript_hash = sha256(bytes)[:16]` — a one-character
  file `x` is a valid immutable "debate." Code enforces *recorded bytes*, not *recorded debate*.
  Propose a minimum-content requirement (≥2 positions, ≥1 objection, recorded tie-break).
- **(c) "ONLY by supersession" → unbounded graph growth**, and `ratify()` never sets/validates the
  `supersedes:` edge or marks the predecessor `deprecated` — the lineage the "Why" depends on is
  unenforced.

B's amended wording added a genesis clause + explicit `supersedes:`/`status: deprecated` +
minimum transcript content.

## Reveal + cross-examination — Reviewer A sees Reviewer B

A verified all three of B's code claims and conceded the central tension:

- **Withdraws the cosmetic-correction exception.** For a money/PII/audit apex, "it's just a typo" is
  the social-engineering wedge for an in-place mutation. The invariant "a ratified body is never
  re-ratified in place" must be **exceptionless**. The proportionality fix belongs in a cheaper
  *process lane*, not an exception to the rule.
- **B-a dissolves A's objection 3** (re-ratification of provenance is already the repair path in
  code; it was a doc-clarity gap, not a deadlock). Same-id re-ratification is legitimate in exactly
  one place: regenerating *evidence*, never changing the normative body.
- **Adopts B-b** (minimum transcript content) and **B's genesis clause**.
- **Holds objection 2** (recorded, not "named human" — overclaiming verification in an audit
  constitution is itself an audit defect) and **objection 4** (successor must itself be
  constitutional + ratified, else supersession is a downgrade-laundering path).
- **Holds objection 1 in substance**: still wants a non-normative-correction lane, but conceding to
  B it must be a *superseding successor* (new id, `supersedes:`, predecessor → deprecated) whose
  debate requirement is met by a recorded attestation that the change is non-normative — not a full
  debate. Normative change ⇒ full debate; non-normative ⇒ attested successor; ratifier classifies,
  classification recorded.

## Converged wording (both reviewers)

> **Rule (constitutional — the amendment article):** A constitutional rule is created or changed
> **only** through `propose → debate → ratify`, and **only by supersession** — a successor that
> declares `edges.supersedes: [<old-id>]`, whose predecessor is marked `status: deprecated` at
> ratification — **never by in-place edit of a ratified body or governing frontmatter**. A successor
> to a constitutional rule must itself be `tier: constitutional` and ratified. Ratification requires
> a **recorded ratifier** (attributed name + date, as stamped by `fux ratify`) and a **recorded
> debate transcript** containing at least two distinct reviewer positions, at least one sustained
> objection, and a recorded tie-break; the transcript is **immutable evidence**
> (`.fux/debates/<id>.md`), corrected only by re-ratifying provenance for the same id, never by
> editing the file. **Genesis:** the founding ratification of this article is its own authority —
> ratified with the transcript of the debate that produced it; once sealed, every later
> constitutional change (including any change to this article) is bound by the process above.

## RESIDUAL CRUX — for the human ratifier

The **non-normative correction lane** is unresolved and is the ratifier's call. The
normative/non-normative boundary is judgment; no `$0` deterministic check can decide whether a prose
edit changes meaning. Three options:

1. **No fast lane (B's pure position).** Every change — even a typo — gets the full debate.
   Maximally safe; will be routed around in practice.
2. **Fast lane, ratifier as sole classifier (A's first form).** Proportionate; trusts one human at
   the apex to honestly label "non-normative."
3. **Fast lane, two-signature (A's recommendation).** Non-normative classification itself attested
   by a *second* recorded reviewer. Closes the relabeling hole for one extra signature, no debate.

**Reviewers' recommendation:** option 3 — preserves the exceptionless in-place-edit ban, answers
proportionality, removes single-actor capture from the cheap path.

### Human tie-break (Arpit, 2026-06-17) — RULING

- **Crux resolved: option 3, the two-signature non-normative lane.** A non-normative correction
  ships as a superseding successor whose debate requirement is met by a *second* recorded reviewer's
  attestation that the change is non-normative. The in-place-edit ban stays exceptionless.
- **Sequencing: ratify the current con-amendment body now**, with this transcript, to populate the
  full audit trail (the engine already enforces the current wording: content_seal, lock,
  un-ratified-tier block, provenance drift). The converged wording above + its four new enforcements
  (`supersedes:` edge check, predecessor→`deprecated`, minimum-transcript-content, constitutional-
  successor tier) are filed as a tracked Phase-2 follow-up and will land as a *successor* ratified
  under this very article — dogfooding supersession.
- **Ratifier of record:** arpit arya (git user.name).

## Implementation debt this wording commits us to (disclosed)

The converged text is **aspirational vs. the code today**. `cmd_ratify` does not yet enforce: the
`supersedes:` edge, the predecessor `deprecated` flag, the minimum-transcript-content check, or the
constitutional-successor tier check. Ratifying this text commits a Phase-2+ follow-up to implement
those four, or the article again oversells what the engine guarantees. **Two reviewers also
confirmed a live mechanical gap: a constitutional rule ratified with no `--debate` has
`debate_hash=None` and is silently exempt from `check_provenance` — the genesis/founding rule must
be ratified WITH this transcript so it is not self-exempt.**
