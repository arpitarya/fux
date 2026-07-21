# Handoffs

The **plan → handoff → prompt** lifecycle artifacts live here (CLAUDE.md).

For each non-trivial feature, commit two files named for the feature:

- `NNNN-<feature>-handoff.md` — self-contained spec: context, definition-of-done,
  scope in/out, key files, constraints, edge cases, tests, open questions.
- `NNNN-<feature>-prompt.md` — the paste-ready Claude Code prompt that executes the
  handoff (explore → plan → implement → verify).

On completion, the feature also gets exactly one ADR in [`../adr/`](../adr/).
