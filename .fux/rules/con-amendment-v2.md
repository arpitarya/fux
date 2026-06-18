---
id: con-amendment-v2
domain: governance
type: rule
status: active
tier: constitutional
created: 2026-06-18
updated: 2026-06-18
aliases:
  - amendment-article
  - constitution-amendment
keywords:
  - constitution
  - amendment
  - ratify
  - supersession
  - governance
  - propose
  - debate
  - constitutional-test
edges:
  supersedes:
    - con-amendment
ratification:
  by: arpit arya
  date: 2026-06-18
  content_seal: 014cce6a37d3157b
  debate_hash: f1f5eefc8924fb6c
---
**Rule (constitutional — the amendment article):** A constitutional rule is created
or changed **only** through `propose → debate → ratify`. It changes **only by
supersession** — a successor rule that supersedes it — and **never by in-place edit**.
Ratification requires a **named human ratifier** and a **recorded debate**.

**Is this constitutional? (the authoring test):** A rule belongs in the constitutional tier
**only if** a wrong answer costs money, PII, audit, or trust **and** the rule never legitimately
changes. If either half fails — the stakes are ordinary, or the rule is expected to evolve — it
is a `standard` rule, not constitutional. This test stops both over-constitutionalizing (locking
down rules that should flex) and under-constitutionalizing (leaving a must-never-break invariant
in the mutable tier).

**Why:** The constitution is the thin apex of trust — the must-never-break invariants
(determinism, money/PII, audit, and this process itself). An invariant that can be
quietly edited in place is not an invariant: its meaning could drift with no debate, no
ratifier, and no trace. Forcing change through supersession keeps every amendment
deliberate, attributable, and auditable, and leaves the superseded rule on the record
rather than overwritten.

**How to apply:** To add or amend a constitutional rule, run `/fux debate "<rule>"`
(two-agent debate, human tie-break) then `fux ratify <id>`, which records the ratifier
and the debate hash. The debate transcript is **immutable evidence**, pinned at
`.fux/debates/<id>.md`: it is corrected by re-ratification, never by editing the file —
`fux check` re-hashes it and blocks on drift. To retire or replace a rule, author its
successor with `edges.supersedes: [<old-id>]` and ratify that — do not edit the ratified body.
Deterministic enforcement of this article — `tier` blocking, `tampered`/`unsealed`, the
`.fux/constitution.lock`, the provenance check, and `fux ratify` — is implemented (Phases 1–3).

<!-- probe: tamper to make ai-review RED on a branch that HAS the ai-review job -->
