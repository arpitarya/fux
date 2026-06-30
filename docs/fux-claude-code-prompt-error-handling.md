# Claude Code prompt: fux error-handling hardening

You are hardening error handling in the **fux** repo. The full spec is in `fux-handoff-error-handling.md` — read it first and treat its Definition of Done, Scope, and Non-negotiables as binding.

## Context to load first
- Read: `fux/cli.py` (`main`, ~line 305), `fux/hooks.py` (all entrypoints), `fux/data/hooks/*.sh`, `fux/hookinstall.py`, `fux/mcpserver.py`, `fux/clicmds.py`, `docs/cli.md`, `CLAUDE.md`.
- Mirror this proven pattern (READ-ONLY, sibling repo, do not modify): `/Users/arpitarya/my_programs/cage/cage/hooks.py` (fail-open `try/except → exit 0`, `# noqa: BLE001 — fail-open`, debug trace) and `cage/cli.py main()` (KeyboardInterrupt → 130).
- Respect `CLAUDE.md`, stdlib-only, Python ≥3.11.

## Task
1. Add `fux/errors.py` with a single thin `class FuxError(Exception)`.
2. Add a top-level guard to `fux/cli.py main()`: `KeyboardInterrupt`→`130`, `FuxError`→`error: <msg>`+`1`, any other exception→`error: <msg>`+`1` with full traceback only when `FUX_DEBUG=1`.
3. Make every `fux/hooks.py` entrypoint (`session_start`, `post_tool_use`, `stop`, `session_end_propose`, `user_prompt_recall`) fail-open: no exception escapes, return 0 on a caught error — EXCEPT the intentional strict-mode `return 2` in `stop`, which must still fire. Under `FUX_DEBUG=1`, print the swallowed exception to stderr.
4. Raise `FuxError("<clear message>")` at the obvious expected-failure sites in read commands (unknown rule id, missing `.fux/`, etc.) instead of leaking raw exceptions. Enumerate these during Explore and confirm the list with me before wiring.
5. Guard the shell hooks (`fux/data/hooks/*.sh`) so a failing `fux_run` doesn't trip `set -e` into breaking the session (non-blocking hooks tolerate failure; the strict `stop` hook keeps its exit-2 passthrough).
6. Verify `mcpserver.py` returns `isError` (not a crash) on malformed input, and `hookinstall.py` fails cleanly without leaving half-written settings.

## Required workflow
1. **Explore** all four boundaries (CLI main, hook entrypoints, MCP dispatch, installer) and the exact read-command failure sites. Do not assume — list them.
2. **Plan** — show the files you'll change, the exact `main()` guard, the per-hook wrap, the `FuxError` raise sites, and the test list. **Pause for my confirmation**, especially the `FuxError` site list.
3. **Implement incrementally** — `errors.py` → `main()` guard → hook wraps (preserve strict `return 2`) → `FuxError` raises → shell-hook guards → MCP/installer verify. Keep the build green.
4. **Update docs to match** — `docs/cli.md` (exit-code contract + `FUX_DEBUG`), `docs/fux-plan.md` + `docs/fux-implementation.md` (contract + status), README if it documents CLI behavior, CHANGELOG if kept. For `CLAUDE.md`: PROPOSE the error-contract rule as a diff for my review — do NOT auto-write it.
5. **Verify** — `python -m pytest -q`, `fux build && fux check`, and manually run `fux why ghost` vs `FUX_DEBUG=1 fux why ghost`. Don't report done until green.

## Constraints (hard)
- Use: stdlib only (`os`, `sys`, `traceback`). Do NOT use: any dependency, logging framework, retries, or an exception hierarchy beyond the single `FuxError`.
- **Fail-open ≠ fail-silent:** every swallowed exception MUST be reachable via `FUX_DEBUG`. No silent `except: pass`.
- **Do not change strict-mode behavior** or remove the `return 2` path — a test must prove it still fires.
- **Do not** convert fail-open *write* paths into raising paths; the guard belongs at boundaries only, not sprinkled through internals or compute functions.
- **Do not touch:** the skillgen renderer, schema, or constitution lock.
- Every broad `except Exception` carries a `# noqa: BLE001 — <reason>` comment, matching cage's style.

## Acceptance criteria (self-check before finishing)
- [ ] Each hook returns 0 when its core raises (test via monkeypatch); `stop` still returns 2 on a forced blocking finding (test).
- [ ] `FUX_DEBUG=1` surfaces a forced hook exception on stderr (test).
- [ ] `main()`: `FuxError`→1, `KeyboardInterrupt`→130, unexpected→1 (traceback only under `FUX_DEBUG`) (test).
- [ ] Read command with no `.fux/` exits 1 with an `error:` line and no traceback (test).
- [ ] MCP dispatch returns `isError` on a malformed `tools/call` (test).
- [ ] `docs/cli.md` + plan/implementation updated; `CLAUDE.md` rule proposed for review.

## Tests
Add tests covering: per-hook fail-open; strict `return 2` preserved; `FUX_DEBUG` trace; `main()` exit-code mapping; read-command `FuxError`→clean exit 1; MCP isError. Run via `python -m pytest -q`.

## Guardrails
- Ask before: changing any strict/gate blocking semantics, broadening the `FuxError` raise list beyond what we confirm, or editing shell-hook exit behavior in a way that affects the strict path.
- Do not auto-edit `CLAUDE.md` — propose the diff.
- If a requirement is ambiguous (env var name, which sites raise `FuxError`), STOP and ask rather than guessing.
