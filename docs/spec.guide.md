# Spec Entries — How to Write Them

How to write a `type: spec` Fux entry — the artifact `/fux plan` produces in its
first stage (plan §16). A spec exists to **land the contract before code**: what
we are building and how we will know it works, captured as a durable, code-linked
Fux entry rather than a throwaway `docs/*-plan.md`. A future reader (human or
agent) should be able to implement against it without re-deriving the intent.

## When to write one

Write a spec whenever a change is large enough that "spec before code" pays off —
a new feature, a non-trivial refactor, a behaviour change with acceptance
criteria. Skip it for a one-line fix; a `task` entry or a direct edit suffices.

A spec is a Fux entry, so it is indexed, recalled, graphed, and drift-checked
like any rule. **Never** write the plan as orphan markdown — that recreates the
sprawl Fux replaces (plan §16 guardrail).

## File naming & location

- **Name:** `.fux/rules/<kebab-id>.md`, `id: <kebab-id>`, `type: spec`.
- Scaffold it: `fux new spec <kebab-id> --domain <domain>`.
- One feature per spec. Tasks live in their own `type: task` entries linked back.

## Required structure (requirements first)

Every spec **must** open with **Requirements** — a reader should know what is
being built and for whom in the first five seconds. Required sections, in order:

1. **Requirements** — user stories: `As a <role> I want <capability> so that
   <benefit>`. The *what* and *why*, never the *how*.
2. **Acceptance criteria (EARS)** — testable, in EARS form:
   - `WHEN <trigger> THE SYSTEM SHALL <response>`
   - `WHILE <state> THE SYSTEM SHALL <response>`
   - `IF <condition> THEN THE SYSTEM SHALL <response>`
   Each criterion should map to something `fux verify` or a probe can assert.
3. **Design** — components and data flow. The affected files come **from the
   graph** (`fux build` then `fux refs`/`graph.json`), not a guess, and are
   recorded in frontmatter `code_refs:`.
4. **Tasks** — an ordered, checkable list. Each becomes a `type: task` entry
   (`fux new task <id>`) carrying `status`, linked via `edges: { implements:
   [<spec-id>] }`.

## Frontmatter contract

- `type: spec`, `status: draft` → `active` (in progress) → `done`.
- `code_refs:` — the files the change touches, pulled from the graph.
- `edges.implements:` — the higher-level goal/spec this realises, if any.
- Decisions made while designing graduate into `adr` entries (`/fux adr`) and are
  linked, so the *why* survives after the spec is `done`.

## Lifecycle

A spec is not write-once. `fux check` flags a spec (or its `task` children) whose
`code_refs` changed while still `todo` — drift between plan and code. On
completion, set `status: done`; the design notes graduate into `adr`/`rule`
entries. The spec then stays as durable, code-linked history.

## Checklist before you call a spec done

- [ ] Requirements stated as user stories (role · capability · benefit).
- [ ] Every acceptance criterion is in EARS form and is assertable.
- [ ] `code_refs` come from the graph, not a guess.
- [ ] Each task is its own `task` entry linked with `implements`.
- [ ] Decisions captured as `adr` entries and linked.
- [ ] `fux build` run; the spec appears in INDEX and the graph.
