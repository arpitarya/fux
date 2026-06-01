---
name: fux-plan
description: "spec-driven planning (kiro-style): turn a request into requirements → design → tasks, each a durable, code-linked Fux entry — not a throwaway doc"
trigger: /fux plan
---

# /fux plan — spec-driven, kiro-style

Turn a request into three reviewable stages, **each a durable Fux entry**, so the
plan stops being write-once scaffolding and becomes tracked, code-linked
knowledge (plan §16). This is the capstone: it closes the loop the rest of Fux
only stores — plan → spec → code → rules → memory, all in one substrate.

> **Guardrail:** a Fux skill must read/write durable Fux entries — **never orphan
> markdown**. If you find yourself writing a `docs/*-plan.md`, stop: that is the
> sprawl Fux replaces. Write a `spec` + `task` entries instead.

## Inputs

`/fux plan "<request>"` — a feature request, bug, or change in plain language.

## Procedure

Confirm the engine is available (`fux --version`; see `skills/fux/SKILL.md`
Step 1) and you are in a `.fux/` project (`fux init` if not).

### Stage 1 — Requirements → a `spec` entry

1. `fux new spec <kebab-id>` to scaffold `.fux/rules/<id>.md` from the spec
   template.
2. Fill **Requirements** as user stories + **EARS** acceptance criteria
   (`WHEN <trigger> THE SYSTEM SHALL <response>`). Follow `docs/spec.guide.md`
   for the required sections.
3. Review with the user before proceeding. The spec is the contract.

### Stage 2 — Design → `code_refs` from the graph

1. Run `fux build` so the graph is current, then query it to find the **real**
   affected modules — `fux refs <file>` and reading `.fux/out/graph.json` /
   `INDEX.md` — instead of guessing.
2. Write the **Design** section (components, data flow) into the same `spec`
   entry, and set `code_refs:` to the files the change will touch.
3. Record any decision worth keeping as an `adr` (use `/fux adr`) and link it via
   `edges: { implements: [...] }`.

### Stage 3 — Tasks → `task` entries carrying status

1. For each unit of work, `fux new task <kebab-id>` (`status: todo`), set its
   `code_refs` to the files it will change, and link `edges: { implements:
   [<spec-id>] }`.
2. Implement task by task. As each lands, set its `status: done` and update or
   author the governing `rule`/`formula` in the **same session**
   (`doc-per-code-change`).
3. `fux check` flags a `task` whose `code_refs` changed while its status is still
   `todo` — drift between plan and code, caught automatically.

### Stage 4 — Graduation

After implementation, the design notes graduate into `adr` / `rule` entries so
the *why* survives. Mark the `spec` `status: done`. The plan is now durable,
code-linked knowledge — not a stale doc.

## Cost

`plan` is one of the only Fux skills that calls the LLM, and it rides the session
you are already in — no background spend, consistent with `fix`-mode (plan §8).
Everything it writes is a `$0`-maintainable Fux entry thereafter.
