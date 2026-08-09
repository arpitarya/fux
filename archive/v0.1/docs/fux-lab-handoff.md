# Handoff: `fux-lab` — exhaustive Fux functionality test harness

**One-liner:** A polyglot dummy repo plus an automated, offline test runner that exercises *every* command in `fux/registry.py`, asserts against golden outputs (not just liveness), runs negative/false-positive cases, and emits a `FINDINGS.md` of what's broken.
**Owner / executor:** Claude Code
**Status:** Ready to build
**Stress-tested:** Devils-advocate pass on the v1 plan exposed four structural flaws — (1) not actually exhaustive (missing `capture`/`components`/`validate-spec`/`feedback` and the `plan`/`adr`/`trace`/`distill` skills); (2) no oracles, so a command that runs but computes *wrong* passes; (3) only tests signals firing, never false-positives (the `seal` "cosmetic edit stays sealed" claim, the core differentiator, went untested); (4) `$0`/deterministic asserted but never enforced. All four are fixed below. **Residual risk:** cross-language `references` edges may not be mechanically derivable (no shared symbol table across Python/TS/Go/Rust) — treated here as an explicit probe with a recorded verdict, not a pass/fail done-criterion.

## 1. Context & background

Fux is a `$0`, stdlib-only, deterministic knowledge engine (see [README.md](../README.md), [docs/cli.md](cli.md)). It has ~45 CLI commands across authoring / verification / governance / runtime / graph / hooks / MCP, plus session-skills. The objective is to verify **each and every** functionality and produce a concrete list of what needs fixing. The v1 plan ([docs/fux-test-repo-plan.md](fux-test-repo-plan.md)) is a good coverage *map* but, as a bug-finding instrument, it asserts only that commands run. This handoff upgrades it into a runnable suite with oracles.

## 2. Definition of done

The build is done when ALL are true:

- [ ] A **coverage manifest** is generated from `fux/registry.py` (not hand-written) listing every command, each marked `tested` / `not-tested` with a reason. Zero silent omissions.
- [ ] The `fux-lab/` polyglot repo (Python + JS/TS + Go + Rust) exists with the seeded rules and traps from §5.
- [ ] A **runner script** executes the full matrix offline, captures stdout/stderr/exit-code per command, and diffs machine output (`--json` where available) against committed **golden** fixtures.
- [ ] **Negative tests** pass: cosmetic edits stay `sealed`; a benign change passes `critic` without a hard-block; a fully-governed file yields no coverage finding.
- [ ] **`$0` is enforced**, not asserted: the maintenance-command sweep runs with network disabled and still exits clean; any socket/model call is a failure.
- [ ] Traps run **state-isolated** (fresh clone or `git stash` reset per trap) so no test contaminates another.
- [ ] The runner emits **`FINDINGS.md`**: per command — pass / fail / divergence-from-golden / crash — and a ranked "what to fix in fux" list.
- [ ] Documentation updated to match (see §9.5).

## 3. Scope

**In scope:**
- The `fux-lab/` fixture repo and its seeded `.fux/` content.
- A Python runner (`run_lab.py`, stdlib-only to match house style) that drives the CLI, captures output, diffs goldens, and writes `FINDINGS.md`.
- Golden fixtures for every command that supports `--json` or stable text output.
- Negative/false-positive cases and the offline `$0` sweep.

**Out of scope (explicit):**
- **Do not** modify the fux engine itself to make tests pass — this harness *reports* bugs, it does not fix them. Fixes are a separate, later task driven by `FINDINGS.md`.
- The GitHub merge wall (`ai-review`, branch-protection) — needs a real remote; record as "untestable locally," don't stub a fake gh.
- Performance/load testing of the graph viewer.

## 4. Current state

- Repo / project: the Fux engine lives at the repo root (`fux/`, `docs/`, `tests/`).
- Read first: [docs/cli.md](cli.md) (command surface + exit codes), [fux/registry.py](../fux/registry.py) (source of truth for commands), [fux/data/schema.json](../fux/data/schema.json) (rule frontmatter), [docs/fux-test-repo-plan.md](fux-test-repo-plan.md) (the v1 map this refines), [CLAUDE.md](../CLAUDE.md) (house rules), existing [tests/](../tests/) for the pytest style to mirror.
- Architecture context: every maintenance command is `$0` (shell/AST/parse). Skills (`plan`/`adr`/`debate`/`critic`-judgment/`distill`) spend the host session's tokens — they are tested for wiring/output-shape only, never for `$0`.

## 5. Technical approach (decided)

1. **Coverage from the registry.** First runner step parses `fux/registry.py` to enumerate commands → manifest. "Exhaustive" must be *provable*, so the suite fails if any registry command lacks a test entry (a `not-tested` row needs an explicit reason: e.g. "needs remote", "session-skill").
2. **Oracles, not liveness.** Every command captures `--json` output where it exists; the runner diffs against a committed golden fixture. Text-only commands get a normalized golden (strip timestamps/paths). A diff = a finding.
3. **Negative tests are first-class.** Explicit cases that assert a signal does **not** fire (false-positive guard). These carry equal weight to the positive traps.
4. **Offline `$0` enforcement.** The maintenance sweep runs under a no-network shell (e.g. `unshare -n` on Linux, or a deny-all proxy env); success offline *is* the `$0` proof for those commands. Skill commands are excluded and labeled.
5. **State isolation.** Each mutating trap runs against a fresh `git worktree`/clone of `fux-lab` or a `git stash && git checkout -- .` reset, so order-independence holds.
6. **Polyglot probes, honestly scored.** Cross-language edges are *probed and recorded* (what edges fux actually produced, and whether they're meaningful), not asserted as required.

### 5.1 `fux-lab/` layout
```
fux-lab/
├── python/pnl/{aggregator.py, corp_actions.py, __init__.py}   # money path (governed, sealed)
├── web/src/{format.ts, dashboard.tsx}  web/package.json        # rounding convention
├── svc/{settle.go, go.mod}                                     # T+1 invariant
├── engine/{src/lib.rs, Cargo.toml}                             # UNGOVERNED (coverage gap)
├── docs/{adr-0001-postgres.md, settlement-policy.md}           # import/ingest sources
├── .fux/                                                       # init + 6 seeded rules
└── CLAUDE.md  AGENTS.md  .github/copilot-instructions.md
```

### 5.2 Seeded rules (schema-valid per schema.json)
`day-pnl` (formula, → constitutional via debate/ratify, sealed, `check:` + 2 `examples:`), `settlement-tplus1` (invariant, Go), `usd-rounding` (convention, TS; global vs project variants = deliberate conflict), `money-never-floats` (regulatory, constitutional, `enforcement: deterministic`), one untagged `check:` rule (→ `untagged-candidate`), and **no** rule for `engine/` (coverage gap).

### 5.3 Traps (positive) and guards (negative)
Positive traps — each must produce its finding: magic-number `0.15` ×3 sites → `mine`; dead `code_ref` → `check` dead-ref + `--fix` drops it; structural edit post-`seal` → `unsealed`; rounding conflict → `conflict`; post-`ratify` body edit → `tampered` (blocking); unguarded `/` → `verify --fuzz`; ungoverned Rust → `coverage`; untagged invariant → `untagged-candidate`; `[ast]` backend swap → `extractor-drift`.

Negative guards — each must produce **no** finding: rename a local / reflow a comment in a sealed file → stays `sealed`; benign rename through `critic` → no deterministic hard-block; the fully-governed `python/pnl/aggregator.py` → not listed by `coverage`; a clean `check` run on the untouched repo → exit 0, empty DRIFT.

## 6. Non-negotiables / constraints

- **Style/patterns:** runner is **Python ≥ 3.11, stdlib-only** (matches Fux's zero-runtime-dep rule; `tomllib` ok). Mirror the existing `tests/` idioms.
- **Use:** the installed `fux` console script + `--json` flags; `git worktree`/`stash` for isolation; `subprocess` with captured pipes.   **Avoid:** any third-party test/runtime dependency; do **not** curl/wget to "verify" $0 (the point is *no* network).
- **Compliance/safety:** deterministic only — the harness itself makes no model calls. Money/PII rules in the fixture are synthetic; no real PII.
- **Do not touch:** the `fux/` engine source, `tests/`, or any existing doc except the additive new ones in §9.5. The harness must not edit the engine to turn a finding green.
- **`$0` proof:** maintenance sweep must pass with network disabled.

## 7. Dependencies & prerequisites

- A working `fux` install on PATH (editable/dev install via `install.sh`, or `pip install -e .`).
- Optional extras installed *only* for the steps that need them: `[ast]` (extractor-drift probe), `[pdf]`/`[scrape]` (ingest/fetch paths). Each step records whether its extra was present.
- Go and Rust toolchains are **not** required — fux's non-Python extraction is brace-heuristic by default; the `[ast]` tree-sitter extra is the only upgrade. Record which backend was active.
- No secrets, no network, no remote.

## 8. Edge cases & risks

- **Cross-language `references` may be empty or noisy** → probe and record the actual edges; don't fail the suite on it, flag it in `FINDINGS.md` as a fux design question.
- **`ratify` PR-routing** triggers only on a protected branch with a remote → run with `--no-pr` locally; record the remote path as untestable.
- **Golden brittleness** (timestamps, abs paths, ordering) → normalize before diff; `check` output is documented as canonically sorted, lean on that.
- **State bleed** between traps → fresh worktree per mutating trap; assert a clean baseline before each.
- **Offline sweep false-failure** if a command legitimately reads `~/.claude` → bind-mount/point `CLAUDE_CONFIG_DIR` at a local fixture, not the network.

## 9. Testing & validation

- What must be tested: every registry command (positive), the negative guards, the offline `$0` sweep, the error-contract cases (exit `0/1/2/130`, terse `error:`, fail-open hooks, `FUX_DEBUG=1`).
- Verify locally: `python run_lab.py` (full sweep, writes `FINDINGS.md`); `python run_lab.py --coverage-only` (manifest vs registry); the existing engine suite still green via `python -m pytest -q`.
- Manual check: open `fux-lab/.fux/out/graph.html`, confirm the visual signals (drifted rule pulses red, constitutional crown, Coverage lens warmth) match what `check` reported.

## 9.5 Documentation impact

- [ ] **README** — N/A (test harness, no public-behavior change to the engine).
- [ ] **CLAUDE.md / AGENTS.md** — *Propose only.* Add a short "Lab harness" note pointing to `run_lab.py` and how to regenerate goldens; surface the edit for Arpit's review, do not silently rewrite.
- [ ] **docs/fux-implementation.md** — required: add the harness to the status tracker / test count.
- [ ] **docs/fux-test-repo-plan.md** — required: mark it superseded-by / refined-by this handoff.
- [ ] **New: `fux-lab/README.md`** — required: how to run, how goldens are regenerated, how to read `FINDINGS.md`.
- [ ] **CHANGELOG / ADR** — N/A (internal tooling, not user-facing).

## 10. Open questions

- OPEN QUESTION: **Where does `fux-lab` live** — a sibling external repo (clean isolation, but not in CI) or `tests/lab/` inside the engine repo (CI-runnable, but a fixture repo nested in a real repo needs `.gitignore`/submodule care)? Recommendation: `tests/lab/` as a fixture with its own nested `.fux/`, runner wired into CI as a separate job. Needs Arpit's call.
- OPEN QUESTION: **Golden regeneration policy** — commit goldens and diff (catches regressions, but goldens drift with intended changes) vs. snapshot-on-first-run. Recommendation: commit + a `--bless` flag to regenerate intentionally, mirroring the existing skillgen `--bless` pattern.
- OPEN QUESTION: **How strict is the offline sweep** — `unshare -n` (Linux-only) vs. a deny-all `HTTPS_PROXY` env (portable, weaker). Recommendation: `unshare -n` in CI, proxy fallback locally.
