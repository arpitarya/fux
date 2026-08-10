# The archive — everything superseded, in one place

**Rule (Arpit, 2026-08-10): everything that needs archiving lives here, at
repo root.** Nothing under `docs/` is an archive. Entries are frozen and
reference-only; relative links inside them may reflect the tree as it was.

| entry | what it is |
|---|---|
| [`v0.1/`](v0.1/) | the first build (pre-reset #1) |
| [`v0.26/`](v0.26/) | the v0.19–0.26 substrate engine — runnable, reference-only; M1's eval baseline |
| [`v0.26-docs/`](v0.26-docs/) | that engine's documentation: ADRs 0001–0015 (cited as "archived ADR-NNNN"), compare docs, examples, tracker |
| [`v0.26-implemented/`](v0.26-implemented/) | the v0.26 line's implemented artifacts: master-prompt, PLAN-v0.26, every executed handoff/prompt pair v0.20→v0.26 |
| [`v0.30-rev1-planning/`](v0.30-rev1-planning/) | the rebuild's research phase: both gate handoff pairs (→ ADR-0001/0002/0003) and the superseded rev-1 diagrams |

Convention: executed v0.30 handoff pairs and superseded v0.30 artifacts get
version-named entries here (`v0.30-…`), never a `docs/archive/`.
