# Claude Code prompt: `fux-lab` exhaustive Fux test harness

You are building an automated, offline test harness that exercises **every** Fux
command and reports what's broken. The full spec is in the handoff doc
(`docs/fux-lab-handoff.md`) — read it first and treat its Definition of Done and
Non-negotiables as binding.

## Context to load first
- Read: `docs/fux-lab-handoff.md` (the spec), `docs/cli.md` (commands + exit codes),
  `fux/registry.py` (the command source of truth), `fux/data/schema.json` (rule
  frontmatter), `docs/fux-test-repo-plan.md` (the v1 map being refined).
- Follow existing patterns in: `tests/` (style, idioms) and `CLAUDE.md` (house rules).
- Respect project conventions: Python ≥ 3.11, **stdlib-only**, deterministic, `$0`.

## Task
Create (1) a polyglot fixture repo `fux-lab/` (Python + JS/TS + Go + Rust) with the
seeded rules and traps from handoff §5, and (2) a stdlib-only runner `run_lab.py`
that: parses `fux/registry.py` into a coverage manifest, drives every command,
captures stdout/stderr/exit-code, diffs machine output against committed golden
fixtures, runs the negative/false-positive guards, enforces `$0` via an offline
sweep, isolates each mutating trap in a fresh `git worktree`, and writes
`FINDINGS.md` ranking what needs fixing in fux.

## Required workflow
1. **Explore** `registry.py`, `cli.md`, and `tests/` before writing anything. Confirm
   the exact command list and which commands support `--json`.
2. **Plan** — lay out the fixture file tree, the seeded rules, the runner's modules,
   and the golden-fixture strategy. **Pause for my confirmation before implementing.**
3. **Implement incrementally** — fixture repo first, then the registry-coverage
   manifest, then positive traps, then negative guards, then the offline `$0` sweep,
   then `FINDINGS.md` generation. Keep each step runnable.
4. **Update docs to match** — add `fux-lab/README.md` (how to run, regenerate
   goldens, read findings); update `docs/fux-implementation.md` (status/test count);
   mark `docs/fux-test-repo-plan.md` as refined-by this harness. For CLAUDE.md /
   AGENTS.md: **propose** a short "Lab harness" note and flag it for my review —
   do not silently rewrite steering files. Don't mark done while docs contradict reality.
5. **Verify**: `python run_lab.py` (full sweep), `python run_lab.py --coverage-only`
   (manifest equals registry — no silent omissions), and `python -m pytest -q` (engine
   suite still green). Fix what *you* break in the harness; do not edit the engine.

## Constraints (hard)
- Use: the installed `fux` console script, `--json` outputs, `subprocess`, `git
  worktree`/`stash`, `unshare -n` (CI) or deny-all proxy (local) for the offline sweep.
- Do NOT use: any third-party Python dependency; any network call to "verify" `$0`
  (the proof is that maintenance commands succeed with network **disabled**).
- Do NOT modify: the `fux/` engine source or existing `tests/`. The harness *reports*
  bugs — it must never edit the engine to turn a finding green.
- Skills (`plan`/`adr`/`debate`/`critic`-judgment/`distill`) are tested for wiring and
  output-shape only, never for `$0` — label them as session-cost.
- Golden diffs must normalize timestamps/abs-paths/ordering before comparing.

## Acceptance criteria (self-check before finishing)
- [ ] Coverage manifest is generated from `registry.py`; every command is `tested` or
      `not-tested` **with a reason** — zero silent omissions (including `capture`,
      `components`, `validate-spec`, `feedback`).
- [ ] Every supported command diffs against a committed golden; a divergence is a finding.
- [ ] Negative guards pass: cosmetic edit stays `sealed`; benign change passes `critic`;
      governed file yields no coverage finding; clean `check` exits 0.
- [ ] Offline `$0` sweep passes with network disabled; any socket/model call fails it.
- [ ] Mutating traps are state-isolated (fresh worktree/reset); order-independent.
- [ ] `FINDINGS.md` written: per-command pass/fail/divergence/crash + ranked fix list.
- [ ] Error contract observed: exit `0/1/2/130`, terse `error:`, fail-open hooks, `FUX_DEBUG=1`.
- [ ] Docs updated (handoff §9.5); agent-file edits proposed, not auto-applied.

## Tests
The harness *is* the test artifact. Additionally add a tiny `pytest` that asserts
`run_lab.py --coverage-only` reports 100% of registry commands accounted for, so the
"exhaustive" claim can't silently rot. Run: `python -m pytest -q`.

## Guardrails
- Before starting, resolve handoff §10 open questions with me: **where `fux-lab` lives**
  (`tests/lab/` fixture vs external repo), **golden regeneration policy** (commit +
  `--bless`), and **offline-sweep strictness**. Don't guess these.
- Ask before: deleting any worktree outside the lab dir, changing CI config, or any
  irreversible git action.
- If a fux command's actual output contradicts what `cli.md` documents, do **not**
  reshape the test to hide it — that's a finding. Record it and continue.
