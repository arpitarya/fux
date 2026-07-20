---
name: fux-adr
description: "capture an architecture/decision record as a durable `adr` Fux entry — one-step durable *why*, code-linked and graphed"
trigger: /fux adr
---

# /fux adr — capture an architecture decision

One-step durable *why*. The `adr` type already exists in the substrate (plan §6);
this skill makes recording a decision a single move instead of an orphan doc.

## Inputs

`/fux adr "<decision>"` — e.g. `/fux adr "use average-cost basis, not FIFO"`.

## Procedure

1. Ensure the engine + project (`skills/fux/SKILL.md` Step 1–2).
2. `fux new adr <kebab-id> --domain <domain>` → scaffolds `.fux/rules/<id>.md`.
3. Fill the body's four sections — keep each tight:
   - **Decision:** the verdict, stated as a present-tense rule.
   - **Context:** the forces that made a decision necessary.
   - **Options considered:** the real alternatives, one line each, with why each
     lost. (If you compared them rigorously, link a `*.compare.md`.)
   - **Consequences:** what this commits you to, and what it rules out.
4. Set `code_refs:` to the code the decision governs, and `edges:` —
   `supersedes:` any prior ADR this replaces (set the old one
   `status: deprecated`), `implements:` the `spec` it realises.
5. `fux build`. The decision now appears in INDEX, the graph (linked to its
   code), and is found by `fux recall`.

## Why a Fux entry, not a doc

A free-floating `decisions.md` rots and is never re-read. An `adr` entry is
indexed, code-linked, drift-checked (`fux check` flags it stale when the code it
governs changes), and surfaced at the moment it is relevant via recall — the
*why* survives the person who made the call.
