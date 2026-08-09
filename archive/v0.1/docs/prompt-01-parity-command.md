# Claude Code prompt: `fux parity` command

You are implementing `fux parity`, a `$0`/stdlib-only CLI command that measures how
much of the user's real Graphify usage Fux already covers. Full spec:
`docs/handoff-01-parity-command.md` — read it first; its Definition of Done and
Non-negotiables are binding. Decision context: `docs/fux-vs-graphify-parity-matrix.md`.

## Context to load first
- Read: `fux/registry.py`, `fux/cli.py`, `fux/clihelp.py`, `fux/recall.py`,
  `fux/graphquery.py`, `docs/cli.md` (registry-table regen step).
- Follow the existing command-module pattern (e.g. an existing `cli*.py`).

## Task
Add `fux/cliparity.py` implementing `fux parity [PATH] [--from-log FILE] [--json]
[--top N] [--threshold T] [--min PCT]`. It scores **two** sub-scores — graph-parity %
(replaceable surface) and a fux-only capability count — plus a gap list. With
`--from-log`, replay graphify's JSONL query log and score, per question, whether Fux
returns a relevant non-empty result via in-process `recall`. Without a log, score from
a committed `fux/data/parity-manifest.json` encoding the matrix rows. Optionally shell
out to `graphify` when present; degrade gracefully (labelled) when absent.

## Required workflow
1. **Explore** the command registration + retrieval modules before writing.
2. **Plan** the module, the manifest schema, and the scoring function; pause for my
   confirmation.
3. **Implement incrementally**: command skeleton + registry wiring → manifest scoring
   → log replay → `--json`. Keep the suite green each step.
4. **Update docs**: README command list, regenerate `docs/cli.md` registry table (use
   the documented regen command, don't hand-edit), `docs/fux-implementation.md`. Propose
   any CLAUDE.md edit for review — don't auto-apply.
5. **Verify**: `python -m pytest -q`, `fux parity fux-lab/` (or any repo), `fux parity --json`.

## Constraints (hard)
- Python ≥ 3.11, **stdlib-only, `$0`, deterministic**. NO LLM to judge relevance —
  reuse `recall`'s lexical/graph overlap.
- Do NOT add a dependency on graphify or import it as a library; call it only via
  `subprocess` when on PATH. No network calls.
- Never blend the two sub-scores into one number.
- Honour the CLI error boundary (`FuxError` → terse `error:`, exit 1).

## Acceptance criteria (self-check)
- [ ] `fux parity` prints two sub-scores + gap list; `--json` matches the removal-checklist consumer.
- [ ] `--from-log` replays a JSONL log, reports per-question hits/misses, tags use-case-#2 queries as out-of-scope.
- [ ] Manifest-only fallback works and is labelled when no log/graphify present.
- [ ] Registry + help + cli.md table updated; tests pass.

## Tests
Add `tests/test_parity.py`: manifest scoring, log-replay fixture (hits, misses,
malformed line, out-of-scope query), `--json` shape, graceful no-graphify path.

## Guardrails
- Resolve handoff §10 (hit threshold; gate-vs-report) with me before finalizing scoring.
- If a fux retrieval path returns something that contradicts `cli.md`, record it as a
  finding — don't reshape the test to hide it.
- Ask before changing any shared retrieval internals.
