# Handoff: fux error-handling hardening

**One-liner:** Make fux's CLI and hooks robust — a top-level CLI guard (clean message + exit code instead of raw tracebacks), genuinely fail-open hook entrypoints (a hook exception must never break an agent session), one typed `FuxError` for expected failures, and a documented+tested exit-code contract — without weakening strict-mode blocking or hiding real bugs.
**Owner / executor:** Claude Code
**Status:** Ready to build
**Stress-tested:** Challenged on (1) typed-error machinery being ceremony → constrained to ONE message-carrying error class, no hierarchy; (2) fail-open hook wrapping masking real bugs and silently breaking strict mode → constrained so the deliberate strict `return 2` passes through untouched and every swallowed exception traces under `FUX_DEBUG` (fail-open ≠ fail-silent); (3) scope creep on "IDE/agent errors" → bounded to the agent boundary (hooks fail-open, MCP returns isError, wiring fails gracefully). Pre-mortem residual: a swallowed hook bug going unnoticed → mitigated by `FUX_DEBUG` tracing + tests asserting strict-2 still fires and a forced exception surfaces under debug.

## 1. Context & background
fux runs inside agent sessions via SessionStart / PostToolUse / Stop / UserPromptSubmit hooks. Today the Python hook entrypoints in `fux/hooks.py` are **not internally fail-open**: `session_start` calls `print(context.run(root))` bare, `post_tool_use` does `(root/rel).read_text()` bare, `stop` calls `checkmod.run`/`fix.apply`/`capture.observe` bare. The shell wrappers (`fux/data/hooks/*.sh`) use `set -euo pipefail`, so any Python exception → nonzero exit → **the agent session sees a broken hook**. Separately, `fux/cli.py main()` is just `return args.fn(args)` with no guard, so a missing file / bad rule id / Ctrl-C dumps a raw traceback at the user. cage already solved both (every hook `try/except → exit 0`; `main()` catches `KeyboardInterrupt → 130`); this packet brings fux to that bar. Sibling packet: `cage-handoff-error-handling.md`.

## 2. Definition of done
- [ ] **Every hook entrypoint in `fux/hooks.py` is fail-open**: `session_start`, `post_tool_use`, `stop`, `session_end_propose`, `user_prompt_recall` wrap their body so no exception escapes; on a caught exception they return 0 (never break the session). The **only** non-zero exit is the existing intentional strict-mode `return 2` in `stop`, which must still fire.
- [ ] **Swallowed hook exceptions are traced under `FUX_DEBUG`** (env `FUX_DEBUG=1`): when set, the caught exception is printed to stderr (type + message + short traceback) so fail-open never means fail-silent. Mirror cage's `CAGE_DEBUG` discipline.
- [ ] **CLI top-level guard** in `fux/cli.py main()`: `KeyboardInterrupt → print "\naborted." → return 130`; `FuxError → print "error: <msg>" to stderr → return 1`; any other unexpected exception → short `error: <msg>` + return 1, with the full traceback shown only when `FUX_DEBUG=1`.
- [ ] **One typed error**, `FuxError(Exception)`, defined once (e.g. `fux/errors.py`, ≤ a few lines). Expected user-facing failures (unknown rule id, missing `.fux/`, bad arg, unreadable file in a *read* command) raise `FuxError("<clear message>")` instead of leaking a raw exception. **No subclass hierarchy.**
- [ ] **Exit-code contract documented + enforced**: `0` ok · `1` error (FuxError / unexpected) · `2` blocking (strict gate/stop) · `130` interrupted. Documented in `docs/cli.md` + proposed for `CLAUDE.md`; asserted by tests.
- [ ] **Shell hooks never exit nonzero except the intended `exit 2`**: the wrappers tolerate a missing/failing `fux` binary and a crashing `python -m fux` without `set -e` propagating a spurious failure into the session (keep `set -u`/`pipefail` discipline but guard the `fux_run` call).
- [ ] **MCP + wiring boundary checked**: `fux/mcpserver.py` returns `isError` tool results rather than crashing (already true for `tools/call` — verify the other dispatch paths don't crash on malformed input); `fux/hookinstall.py` install/uninstall surface failures as a clear message + nonzero return, never a half-written settings file.
- [ ] Tests cover the above (see §9). `python -m pytest -q` + `fux build && fux check` green.
- [ ] Docs updated (see §9.5).

## 3. Scope
**In scope:** `fux/hooks.py` fail-open wrapping + `FUX_DEBUG` tracing; `fux/cli.py main()` guard; new `fux/errors.py` (`FuxError`); raising `FuxError` at the obvious expected-failure sites in **read** commands (why/refs/recall/explain/path/impact/coverage/stats) and `init`/`build`/`check` arg handling; shell-hook guard; exit-code contract doc + tests; a verify pass over `mcpserver.py` + `hookinstall.py` error surfaces.

**Out of scope (explicit) — do NOT do:**
- Do **not** change what strict mode blocks on, or remove/relax the `return 2` path. Behavior of `check`/`gate`/`stop` findings is unchanged — only how errors *around* them surface.
- Do **not** convert fail-open *write* paths into raising paths (the constitution's fail-open discipline stays; you're making hooks MORE fail-open, not less).
- Do **not** add retries, custom logging frameworks, or an exception hierarchy beyond the single `FuxError`.
- Do **not** touch the skillgen renderer from the other packet, the schema, or the constitution lock.
- Do **not** swallow exceptions in pure *compute* library functions where a raise is correct — the guard belongs at the **boundaries** (CLI `main`, hook entrypoints, MCP dispatch, installer), not sprinkled through internals.

## 4. Current state
- Repo: `/Users/arpitarya/my_programs/fux`
- Read first: `fux/cli.py` (`main`, ~line 305), `fux/hooks.py` (all entrypoints), `fux/data/hooks/*.sh`, `fux/hookinstall.py`, `fux/mcpserver.py`, `fux/clicmds.py` (`cmd_gate`/`cmd_check` exit codes), `docs/cli.md`, `CLAUDE.md`, `docs/fux-plan.md`.
- Reference pattern to mirror (same repo family, READ-ONLY): `/Users/arpitarya/my_programs/cage/cage/hooks.py` (fail-open `try/except ... exit 0` with `# noqa: BLE001 — fail-open` comments + `_trace_entry` under `CAGE_DEBUG`) and `cage/cli.py main()` (KeyboardInterrupt → 130).
- Today: fux is zero-dep stdlib ≥3.11; hooks return `int`; `cmd_gate`/strict `stop` already use exit 2 for blocking.

## 5. Technical approach (decided)
- **Boundary discipline:** errors are caught/rendered only at the four boundaries (CLI `main`, hook entrypoints, MCP dispatch, installer). Internals keep raising; that's correct.
- **`FuxError`** is a thin `class FuxError(Exception): pass` in `fux/errors.py`. `main()` distinguishes `FuxError` (expected → terse `error:` + 1) from everything else (unexpected → terse `error:` + 1, full traceback only under `FUX_DEBUG`). `KeyboardInterrupt` → 130.
- **Hooks:** each entrypoint gets an outer `try/except Exception` that returns 0, EXCEPT `stop` whose intentional `return 2` is computed *before* the guard or explicitly re-raised/passed through. Under `FUX_DEBUG`, the guard prints the exception to stderr. Add `# noqa: BLE001 — hook fail-open` comments to satisfy lint, matching cage's style.
- **`FUX_DEBUG`** is the single debug switch (parallel to `CAGE_DEBUG`): controls both the CLI traceback and the hook-swallow trace. Document it.
- **Shell hooks:** wrap the `fux_run` invocation so a nonzero from it doesn't trip `set -e` into failing the hook (e.g. `fux_run context || true` for the non-blocking hooks; the strict `stop` hook keeps its ability to pass exit 2 through).

## 6. Non-negotiables / constraints
- **Style/patterns:** fux house style — small modules, absolute imports, stdlib only, Python ≥3.11; follow `CLAUDE.md`. Match cage's `# noqa: BLE001` comment discipline for every broad catch.
- **Use:** stdlib only (`os`, `sys`, `traceback`). **Avoid:** any third-party dep; any logging framework; any LLM/network.
- **Fail-open ≠ fail-silent:** every swallowed exception MUST be reachable via `FUX_DEBUG`. A silent `except: pass` with no debug trace is a defect.
- **Strict mode is sacred:** the `return 2` blocking path must still fire under all conditions it fires today. A test must prove it.
- **Determinism / `$0`:** no behavior change to derived views or checks; this is purely error-surface work.
- **Do not touch:** write-path fail-open internals, schema, constitution lock, the skillgen work.

## 7. Dependencies & prerequisites
- Python ≥3.11. No env/services/secrets. `FUX_DEBUG` is a new documented env var (off by default).

## 8. Edge cases & risks
- **`.fux/` absent** when a read command runs → `FuxError("no .fux/ in <cwd> — run `fux init`")`, exit 1, no traceback.
- **Unknown rule id** (`fux why ghost`) → `FuxError`, exit 1.
- **Unreadable/deleted file mid-hook** (`post_tool_use` read) → caught, exit 0, traced under debug.
- **`context.run` raises in SessionStart** → caught, exit 0 (session must start cleanly even if fux is broken).
- **Strict findings present** → still `return 2` (not swallowed). RISK: an over-broad guard around `stop` swallows the 2 → a test must guard this.
- **Malformed MCP request** → `isError` result, not a crash that kills the stdio server.
- **`hookinstall` partial failure** (e.g. unwritable `.claude/settings.json`) → clear message + nonzero, no corrupted JSON left behind.

## 9. Testing & validation
- **Must test:** (a) each hook entrypoint returns 0 when its core raises (monkeypatch the inner call to raise); (b) `stop` still returns 2 on a forced blocking finding; (c) `FUX_DEBUG=1` causes a forced hook exception to appear on stderr; (d) `main()` maps `FuxError`→1, `KeyboardInterrupt`→130, unexpected→1 with traceback only under `FUX_DEBUG`; (e) a read command on a dir with no `.fux/` exits 1 with an `error:` line and no traceback; (f) MCP dispatch returns isError on a malformed `tools/call`.
- **Verify locally:** `python -m pytest -q` · `fux build && fux check` · manually run `FUX_DEBUG=1 fux why ghost` and `fux why ghost` to see the with/without-traceback behavior.
- **Manual check:** simulate a SessionStart hook with a broken `.fux/` and confirm exit 0 + (under debug) a stderr trace.

## 9.5 Documentation impact
- [x] **docs/cli.md** — required: document the exit-code contract (0/1/2/130) and the `FUX_DEBUG` env var.
- [x] **AI agent files (CLAUDE.md)** — required, ⚠️ PROPOSE for review (do not auto-write): add a "hooks are fail-open; errors surface via `FUX_DEBUG`; CLI exit codes 0/1/2/130; raise `FuxError` for expected failures" rule. Surface the diff.
- [x] **docs/fux-plan.md + docs/fux-implementation.md** — required: note the error-handling contract + flip/add a status row.
- [x] **README** — required only if it documents CLI usage/exit behavior; add the `FUX_DEBUG` mention if so, else N/A with reason.
- [ ] **CHANGELOG** — add an entry if fux keeps one (it ships as fux-engine) — user-facing robustness change.
- [ ] **schema / ADR** — N/A: no schema change; the boundary-discipline decision can be a one-line note in fux-plan.

## 10. Open questions
- OPEN QUESTION: env var name — `FUX_DEBUG` (parallel to `CAGE_DEBUG`) vs reuse an existing fux verbosity flag if one exists. Default: `FUX_DEBUG`; confirm none already exists.
- OPEN QUESTION: should unexpected (non-`FuxError`) exceptions in `main()` print a one-line `error:` + a "re-run with FUX_DEBUG=1 for details" hint, or the short repr? Recommend the hint form.
- OPEN QUESTION: which exact read-command failure sites get `FuxError` in this pass vs left as-is — enumerate during Explore and confirm the list before wiring (keep it to the obviously-user-facing ones; don't blanket-convert).
