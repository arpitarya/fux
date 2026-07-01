# Fux test-repo plan — `fux-lab`

> **Status: refined-by + realised.** This v1 map was upgraded into a runnable,
> oracle-bearing instrument by [docs/fux-lab-handoff.md](fux-lab-handoff.md) and
> **built** as the external sibling repo `fux-lab/` (polyglot fixture +
> stdlib-only `run_lab.py`). The harness diffs machine output against committed
> goldens (not just liveness), springs worktree-isolated traps and negative
> guards, proves `$0` offline, and writes a ranked `FINDINGS.md`; a
> registry-generated manifest asserts 44/44 commands are accounted for. The
> command-by-command matrix below remains the human-readable coverage map.

A plan for a **polyglot dummy repo** built to exercise the full Fux command
surface end-to-end. The repo is deliberately small but spans **Python, JS/TS, Go,
and Rust** so the multi-language graph extractor (`ast` for Python, brace-heuristic
or tree-sitter for the rest), `references`/`calls` edges, coverage, and the
governance/constitution layer all have something real to bite on.

> This is a **plan only** — no files are created. It specifies the layout, the
> seeded `.fux/` content, and a command-by-command test matrix with the signal to
> assert for each. Every command and flag below is taken verbatim from
> [docs/cli.md](cli.md) and the rule schema in
> [fux/data/schema.json](../fux/data/schema.json) — nothing invented.

---

## 1. Goals

1. **Smoke-test every CLI group** — authoring, verification, governance, runtime,
   graph, hooks, MCP — at least once.
2. **Force every interesting signal to fire**: `unsealed` drift, `tampered`
   constitution finding, a `conflict`, a dead `code_ref`, an `untagged-candidate`
   advisory, a coverage gap, a `verify --fuzz` div-by-zero, `extractor-drift`.
3. **Cover all four agent surfaces** the graph understands (Python / JS-TS / Go /
   Rust) so cross-language `references` edges and PageRank chokepoints appear.
4. **Stay `$0`** — confirm no maintenance command needs a model or network (the
   skill paths that *do* use the session are tested separately and labelled).
5. **Validate the error contract** — exit `0/1/2/130`, terse `error:` rendering,
   fail-open hooks, `FUX_DEBUG=1`.

## 2. Why polyglot (the design bet)

A single-language repo can't trip the most interesting code paths. The polyglot
layout is chosen specifically to exercise:

- **Graph extraction across backends** — Python via stdlib `ast`; JS/TS/Go/Rust via
  the brace heuristic by default, and again via the `[ast]` tree-sitter extra to
  prove the **`extractor-drift`** advisory fires when `graph.json` `meta.extractor`
  changes between machines.
- **`references` (cross-language) vs `calls` (intra-file)** edges — only a
  multi-file, multi-language repo produces both kinds.
- **Coverage as a real finding** — leave one language's module ungoverned so
  `fux coverage` and the gate's report-first coverage warning have something grey
  to surface.
- **Money/PII/numbers governance** — the Python service carries the financial
  invariant (the README's `day-pnl`), which is the natural home for a
  **constitutional** rule, `seal`, `verify --fuzz`, and the deterministic `critic`.

---

## 3. Repo layout — `fux-lab/`

```
fux-lab/
├── python/
│   └── pnl/
│       ├── aggregator.py        # day_pnl(), to_usd() — the money path (governed)
│       ├── corp_actions.py      # split/dividend adjustments (governed, sealed)
│       └── __init__.py
├── web/
│   ├── src/
│   │   ├── format.ts            # formatUsd() — calls into a shared rounding rule
│   │   └── dashboard.tsx        # renders P&L; references the python contract
│   └── package.json
├── svc/                         # Go
│   ├── settle.go                # Settlement(): T+1 invariant (governed)
│   └── go.mod
├── engine/                      # Rust
│   ├── src/lib.rs               # risk_weight() — UNGOVERNED on purpose (coverage gap)
│   └── Cargo.toml
├── docs/
│   ├── adr-0001-postgres.md     # to import via `fux import`
│   └── settlement-policy.md     # to ingest via `fux fetch-rules` / `fux ingest`
├── .fux/                        # created by `fux init`, then seeded (see §4)
├── CLAUDE.md  AGENTS.md  .github/copilot-instructions.md   # agent pointers
└── README.md
```

Keep each source file tiny (one or two functions) — enough for the AST to find
symbols, call edges, and a magic number repeated across ≥3 sites so `fux mine`
has a candidate to surface.

### 3.1 Seeded "traps" (so signals are guaranteed to fire)

| Trap | Where | Command that should catch it |
|---|---|---|
| Magic number `0.15` repeated in `aggregator.py`, `settle.go`, `risk_weight` | 3 sites | `fux mine --min-sites 3` drafts a candidate |
| A `code_ref` pointing at a deleted function | a rule's `code_refs` | `fux check` → dead-ref; `fux check --fix` drops it |
| Restructure `aggregator.py` *after* `fux seal` | python | `fux check` → `unsealed`; graph pulses red |
| Two rules asserting opposite rounding | project vs global | `fux check` → `conflict` |
| Hand-edit a ratified rule body after `fux ratify` | `.fux/rules/` | `fux check` → always-blocking `tampered` |
| Unguarded `/` in a `check:` example input | a formula rule | `fux verify --fuzz` → div-by-zero flag |
| Rust module with no governing rule | `engine/` | `fux coverage` lists it; gate reports it |
| A `check:`/invariant rule with no `principle` tag | a project rule | `fux check` → `untagged-candidate` advisory |

---

## 4. Seeded `.fux/` content

After `fux init`, hand-author a handful of schema-valid rules
([schema.json](../fux/data/schema.json)) so the runtime/verify/governance commands
have substance. Minimum set:

1. **`day-pnl`** — `type: formula`, `tier: constitutional` candidate.
   `code_refs: [python/pnl/aggregator.py#L40-58]`, a `check:` invariant
   (dollar-normalise before summing), two `examples:` (incl. a new-position edge
   case), `Rule:` / `Why:` / `Edge cases:` body. This is the rule taken through
   `seal → debate → ratify`.
2. **`settlement-tplus1`** — `type: invariant`, governs `svc/settle.go`. Carries a
   `check:` and an `examples:` pair to test cross-language `verify`.
3. **`usd-rounding`** — `type: convention`, governs `web/src/format.ts`. A *global*
   variant asserts banker's rounding and a *project* variant asserts half-up → the
   deliberate **conflict**.
4. **`money-never-floats`** — `type: regulatory`, `tier: constitutional`,
   `enforcement: deterministic`, `principle:` set → the constitution's deterministic
   hard-block for the `critic`.
5. **`risk-weight`** — intentionally **absent** for the Rust module (coverage gap).
6. One **untagged** project rule with a `check:` but no `principle` → the
   `untagged-candidate` advisory.

Also stage `docs/` markdown for the `import` / `import-memory` / `fetch-rules` /
`ingest` paths.

---

## 5. Test matrix — command by command

Run from inside `fux-lab/`. Cost column confirms the `$0` guarantee.

### 5.1 Authoring

| Step | Command | Assert | Cost |
|---|---|---|---|
| Scaffold | `fux init --recall` | `.fux/` created, 3 core hooks + recall hook wired in `.claude/settings.json`, pointers dropped | $0 |
| New stub | `fux new formula day-pnl --domain finance` | schema-valid stub in the formula dir | $0 |
| Build | `fux build` then `fux build --full` | `INDEX.md` + `rules.json` + `graph.json` + `NARRATIVE.md` regenerate; `--full` graphs every file | $0 |
| Self-knowledge | `fux self-build` | fux's own self-knowledge bundle regenerates (AST-only) | $0 |
| Import docs | `fux import docs/ --type narrative` | `adr-0001`/policy land as narrative entries | $0 |
| Import memory | `fux import-memory --scope shared` | home-dir memory mirrored into `.fux/memory/shared/` | $0 |
| Fetch rules | `fux fetch-rules docs/settlement-policy.md --raw` | plain text extracted (the `$0` half of the skill) | $0 |
| Ingest (skill) | `fux ingest docs/*.md` | items land `status: draft` in `.fux/ingest/queue.md`; `--queue` shows them | $0 |
| Ingest recheck | `fux ingest <id> --recheck` (needs `[scrape]`) | re-reads `source`, raises `source-drift` if changed | $0 |

### 5.2 Verification

| Step | Command | Assert | Cost |
|---|---|---|---|
| Validate | `fux check` | reports dead-ref, conflict, untagged-candidate, staleness; writes `DRIFT.md` | $0 |
| Auto-fix | `fux check --fix` | drops the dead ref, bumps `updated`; conflict/tamper remain | $0 |
| Baseline | `fux check --baseline-write baseline.json` | snapshots findings, exits | $0 |
| Seal | `fux seal --all` | rules bound to AST fingerprint | $0 |
| Drift | edit `aggregator.py`, then `fux check` | `unsealed` finding on `day-pnl` | $0 |
| Verify | `fux verify` | runs `check:`/`examples:` for `day-pnl` + `settlement-tplus1` | $0 |
| Fuzz | `fux verify --fuzz` | boundary-perturbs inputs; flags unguarded div-by-zero | $0 |
| Lint | `fux lint` then `fux lint --strict` | `no-why`/`no-code-refs`/`verify-source`; `--strict` exits 1 | $0 |
| Coverage | `fux coverage` | lists the ungoverned Rust module | $0 |
| Stats | `fux stats` | weighted health score + corpus breakdown | $0 |
| PII scan | `fux pii-scan` | scans non-plan files for hard PII; blocks gate if found | $0 |
| Mine | `fux mine --min-sites 3` | drafts the `0.15` magic-number candidate | $0 |
| Extractor drift | install `[ast]`, rebuild on one "machine", `fux check` on default | `extractor-drift` advisory | $0 |

### 5.3 Governance / constitution

| Step | Command | Assert | Cost |
|---|---|---|---|
| Propose (retro) | `fux propose-rules --retro` | AST candidates with git-recovered *why* → `.fux/CANDIDATES.md` | $0 |
| Triage | `fux candidates --pending` → `fux candidates accept <id>` | draft promoted to active standard-tier rule | $0 |
| Debate (skill) | `fux debate "day-pnl"` | two-agent transcript at `.fux/debates/day-pnl.md` (uses session tokens) | session |
| Ratify | `fux ratify day-pnl --by "Arpit" --debate .fux/debates/day-pnl.md` | stamps `ratification`, freezes seal, writes `constitution.lock`; routes to a PR branch if on protected branch | $0 |
| Tamper | hand-edit ratified `day-pnl` body, `fux check` | always-blocking `tampered` finding | $0 |
| Constitution | `fux constitution` | apex status + violations grouped by severity; exit 2 if blocking | $0 |
| Critic (det.) | `fux critic "drop the rounding guard"` | deterministic pass hard-blocks (exit 2), no LLM | $0 |
| Critic (judgment) | `fux critic "rename day_pnl"` | lists judgment principles; advisory, does not block | $0 |
| Capture decision | `fux capture-decision use-postgres --route fux --by "Arpit"` | concluded debate → tamper-evident ADR | $0 |
| Gate | `fux gate` then `fux gate --install --strict-lint` | exit 2 on blocking; installs pre-commit; reports coverage | $0 |
| Migration gate | `fux gate --baseline baseline.json` | fails only on findings new since baseline | $0 |

### 5.4 Runtime / retrieval / graph

| Step | Command | Assert | Cost |
|---|---|---|---|
| Why | `fux why day-pnl --history` | rule + why + linked code + edges; `--history` shows git evolution | $0 |
| Refs | `fux refs python/pnl/aggregator.py` | reverse lookup → `day-pnl` | $0 |
| Recall | `fux recall "how is day P&L computed" --hybrid --expand` | BM25F; RRF-fused lexical+semantic+graph | $0 |
| How | `fux how "which rules govern a file"` | returns `fux refs <path>` | $0 |
| Context | `fux context` | emits Tier-1 INDEX (the SessionStart injection) | $0 |
| Query | `fux query "settlement" --depth 2` | graph traversal from matching rules | $0 |
| Path | `fux path web/src/dashboard.tsx python/pnl/aggregator.py` | shortest cross-language path | $0 |
| Explain | `fux explain settlement` | node + community + neighbours | $0 |
| Impact | `fux impact python/pnl/aggregator.py` | blast radius: invariants, stale-why rules, caller files | $0 |
| Savings | `fux savings "how is day P&L computed"` | token + dollar win from real file sizes | $0 |
| Tour | `fux tour` | ordered `ONBOARDING.md` reading path | $0 |
| Report | `fux report` | `GRAPH_REPORT.md`: god nodes + PageRank chokepoints | $0 |
| Serve | `fux serve --port 8765` | local dashboard over generated views | $0 |
| Graph viewer | open `.fux/out/graph.html` | Solar Terminal; Coverage lens warms governed code; drifted `day-pnl` pulses red; constitutional crown | $0 |

### 5.5 Hooks, MCP, setup

| Step | Command | Assert | Cost |
|---|---|---|---|
| Hooks status | `fux hooks status` | reports git/claude/codex/copilot wiring | $0 |
| Hooks install | `fux hooks install --all --recall` | all four surfaces + recall wired; idempotent | $0 |
| SessionStart | trigger `fux context` via hook | INDEX injected to stdout | $0 |
| PostToolUse | edit a governed file mid-session | `fux hook-touch` prints the drift reminder | $0 |
| Stop (strict) | set `mode = strict`, end turn with a blocking finding | `fux hook-check` exits 2 | 2 |
| Fail-open | corrupt `.fux/`, trigger a hook | hook returns 0 (session unbroken); `FUX_DEBUG=1` shows the swallowed trace | $0 |
| MCP | `fux mcp` + `claude mcp add fux -- fux mcp` | publishes `fux_recall/why/refs/coverage/savings/stats/context/query/trace/new` | $0 |
| Setup | `fux setup` | bundled schema/hooks/skills copied to `~/.claude/fux` | $0 |

### 5.6 Error contract (cross-cutting)

| Case | How to trigger | Expect |
|---|---|---|
| OK | any read command | exit `0` |
| Expected error | `fux why no-such-rule` | terse `error: <msg>`, exit `1`, no traceback |
| Unexpected error | force an internal raise | `error: <msg>` + `FUX_DEBUG=1` hint, exit `1` |
| Blocking | strict `gate`/`stop` with a blocking finding | exit `2` |
| Interrupt | `Ctrl-C` mid-run | `aborted.`, exit `130` |
| Debug | re-run any of the above with `FUX_DEBUG=1` | full traceback / swallowed hook trace surfaces |

---

## 6. Execution order (suggested)

1. `init → new → build → seal` (get a clean substrate).
2. Author the 6 seed rules + stage `docs/`; `build` again.
3. Run all **read/verify** commands on the clean state (baseline behaviour).
4. **Spring the traps** (§3.1) one at a time, re-running the catching command.
5. Walk the **governance** flow: `propose → candidates accept → debate → ratify →
   tamper → constitution → critic → gate`.
6. Wire **hooks + MCP**, exercise each event.
7. Sweep the **error contract** cases.
8. Open `graph.html`, confirm the visual signals (red pulse, crown, coverage warmth).

## 7. Done criteria

- Every command in §5 has been run and produced its asserted signal.
- All four languages appear as nodes with at least one cross-language `references`
  edge in `graph.json`.
- At least one of each finding kind observed: `dead-ref`, `conflict`, `unsealed`,
  `tampered`, `untagged-candidate`, coverage gap, fuzz div-by-zero,
  `extractor-drift`.
- The constitution flow ends with `day-pnl` ratified and a `constitution.lock`
  committed; a post-ratify edit is caught as `tampered`.
- No maintenance command made a network or model call (skills excepted and labelled).
- Exit codes `0/1/2/130` all observed.

## 8. Out of scope / notes

- Skills (`debate`, `plan`, `adr`, `critic` judgment half, `distill`) spend the
  **host session's** tokens — they're tested for *wiring and output shape*, not for
  `$0`.
- Optional extras (`[ast]`, `[pdf]`, `[scrape]`, `[embeddings]`, `[critic]`) are
  installed only for the specific steps that need them; the default sweep stays
  stdlib-only.
- Branch protection / the `ai-review` merge wall lives in GitHub and can't be tested
  in a local dummy repo — only `fux gate` (the in-repo half) is exercised here.
