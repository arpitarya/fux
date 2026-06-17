---
id: con-amendment
domain: governance
type: rule
status: active
tier: constitutional
created: 2026-06-16
updated: 2026-06-16
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
ratification:
  by: arpit arya
  date: 2026-06-17
  content_seal: 9eda2f6b1309972b
  debate_hash: 36e62224da098227
---
**Rule (constitutional — the amendment article):** A constitutional rule is created
or changed **only** through `propose → debate → ratify`. It changes **only by
supersession** — a successor rule that supersedes it — and **never by in-place edit**.
Ratification requires a **named human ratifier** and a **recorded debate**.

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
