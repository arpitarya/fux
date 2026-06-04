# Fux — Plan

> **Status: IMPLEMENTED — engine v0.1.0 (this repo).** This is the design of
> record; see [architecture.md](architecture.md) and [cli.md](cli.md) for what
> shipped, and [implementation-notes.md](implementation-notes.md) for deltas.
> A portable, Claude-aware knowledge engine that **unifies and replaces** three
> things Anton runs separately today — the structural graph (graphify),
> cross-session memory, and the narrative docs — and adds the business-rules
> layer none of them held. One frontmatter-driven substrate with derived index,
> graph, and memory views. Continuously referenced, cheaply maintained.

**Name:** after *Johann Joseph Fux*, author of *Gradus ad Parnassum* (1725) —
the counterpoint treatise every composer (Bach, Mozart, Haydn, Beethoven)
learned the rules from. A tool that codifies and enforces rules, named after the
man who wrote *the* rulebook. Sits beside `wagner`, `bach`, `orff`.

---

## 1. The problem: five fragmented systems

Anton already runs **five** disconnected knowledge stores. They overlap, drift
independently, and *still* leave business rules homeless:

| System | Holds | Lifespan |
|---|---|---|
| `docs/WHAT/WHY/HOW.md` | Product narrative | Stable |
| `docs/architecture.md` | Repo structure, tech | Stable |
| `docs/conventions.md`, `guardrails.md` | Code style, project rules | Stable |
| `graphify-out/` | Structural graph (who-calls-whom) | Auto, $0 |
| `~/.claude/.../memory/` | Claude's cross-session memory | Ephemeral/personal |

The actual business rules live **only as inline comments** in code. Example —
`backend/app/modules/brokers/aggregator.py:43`:

```python
# Today's INR P&L: ∑ (day_change_pct/100 × INR-normalised current_value).
day_pnl = sum(_inr_value(x) * (x.day_change_pct / 100.0) for x in h)
```

The *why* (why current value not invested, why INR-normalize first, what
cost-basis method was chosen) is invisible until someone greps for it. **Fux
replaces all of this with one substrate**: the same frontmatter files become
rules, memory, narrative, and graph nodes — one index, one graph, one source of
truth — and it fills the business-rules gap none of the five covered (see §11).

---

## 2. What Fux is

A **portable tool shaped like graphify**: a global engine + a per-project
footprint + `$0` deterministic maintenance. One command (`fux init`) links it to
any project, regardless of language.

```
fux init · fux build · fux check · fux context · fux why …   # links to any project
```

---

## 3. Core principles

1. **Single source → derived formats.** Humans edit one canonical source; all
   other formats regenerate. Never maintain two copies.
2. **Tiered, lazy reads.** Claude reads a tiny index first, then opens only the
   one relevant rule. Minimal tokens.
3. **$0 deterministic maintenance.** Every update path is shell/AST/parse — no
   LLM calls — exactly like graphify's AST-only model.
4. **Portable & polyglot.** The engine parses frontmatter and checks file paths
   via git; it doesn't care if the project is Python, TS, or anything else.
5. **Configurable enforcement.** Default is **`fix`** — Claude repairs drift
   in-session; `warn` only surfaces it, `strict` hard-blocks — set per project (§8).

---

## 4. Architecture

Global engine, maintained once; per-project footprint, created by `fux init`:

```
GLOBAL (install once, maintained once)          PER-PROJECT (fux init)
~/.claude/skills/fux/SKILL.md     ──/fux──►      anton/.fux/rules/*.md        (source)
~/.claude/fux/engine/             (CLI)          anton/.fux/glossary/*.md     (source)
~/.claude/fux/global/  (git repo, shared         anton/.fux/config.toml       (strictness, etc.)
   best practices — all projects)                anton/.fux/out/INDEX.md      (generated)
~/.claude/fux/packs/*/            (rule packs)   anton/.fux/out/rules.json    (generated)
~/.claude/fux/hooks/*.sh          (hook impls)   anton/.fux/out/graph.html    (generated)
~/.claude/fux/schema.json         (validation)   anton/.fux/out/DRIFT.md      (generated)
                                                 anton/.claude/settings.json  (hooks wired)
```

`fux init` scaffolds the footprint, registers hooks into the project's
`.claude/settings.json`, and drops a Tier-0 pointer into that project's
`CLAUDE.md`. Same one-command adoption as `/graphify`.

### Read tiers (the token-cost win)

```
Tier 0  CLAUDE.md pointer ........... 1 line, always in context
Tier 1  .fux/out/INDEX.md ........... ~1 line/rule, read FIRST        ← cheap
Tier 2  .fux/rules/<id>.md .......... opened ONLY when relevant       ← lazy
Tier 3  .fux/out/rules.json + graph . machine lookup + human browsing
```

---

## 5. Layered rule resolution

The mechanism that makes best practices **maintainable once, referenced
everywhere**:

```
effective ruleset  =  ~/.claude/fux/global/   (cross-project best practices)
                   ⊕  ~/.claude/fux/packs/*   (opt-in shareable domain packs)
                   ⊕  ./.fux/rules/           (this project's domain rules)
```

- **Global layer** — "files ≤100 lines", "no secrets in env", "async
  everywhere", "doc-update per code change". Edit once → every linked project
  inherits. Change a best practice in one place; all repos pick it up.
- **Rule packs** — shareable, versioned bundles (e.g., an `indian-markets-tax`
  pack reusable across finance projects). Opt-in per project.
- **Project layer** — Anton's day-P&L formula, INR normalization, broker quirks.

Precedence: project overrides pack overrides global. **Conflict detection**:
`fux check` flags when a project rule contradicts a global/pack rule (same `id`
or an explicit `contradicts:` edge) instead of silently shadowing it.

---

## 6. Rule file schema

Hybrid: validated YAML frontmatter + prose Markdown body. Mirrors the existing
`memory/` file style so the muscle memory is already there.

```markdown
---
id: day-pnl
domain: portfolio
type: formula            # see taxonomy below
status: active           # draft | active | deprecated
created: 2026-06-01
updated: 2026-06-01
code_refs:
  - backend/app/modules/brokers/aggregator.py#L43-L46
related: [portfolio-valuation, inr-normalization]
edges:                   # optional typed relationships
  depends-on: [inr-normalization]
  supersedes: []
check: "abs(sum(h.day_pnl) - portfolio.day_pnl) < 0.01"   # optional invariant
examples:                # optional, machine-verifiable (see §10)
  - given: "₹1,00,000 holding up 2% today"
    expect: "₹2,000 day P&L"
---
**Rule:** Today's P&L is computed on *current* INR value, not invested cost.

**Formula:** `day_pnl = Σ (inr_value(h) × day_change_pct(h) / 100)`

**Why:** day_change_pct is already relative to *yesterday's close*, so it must
multiply today's market value, not original cost. Using invested cost would
double-count appreciation.

**Edge cases:** `day_pnl_pct = 0` when current value is 0 (avoids div-by-zero).
```

### Rule type taxonomy

| type | Holds | Example |
|---|---|---|
| `rule` | A business rule / policy | "Holdings in foreign currency normalize to INR before aggregation" |
| `formula` | A calculation + worked example | day-pnl, XIRR, cost basis |
| `glossary` | A domain term definition | "READY source", "prime", "holding" |
| `invariant` | A must-always-be-true assertion (machine-checkable) | "Σ holdings == portfolio total" |
| `adr` | An architecture/decision record (the *why*) | "Why we chose avg-cost over FIFO" |
| `edge-case` | A known gotcha | "Broker silently shows zero holdings" |
| `convention` | A code/process convention | "Backend filenames `{domain}_{role}.py`" |
| `regulatory` | An external/legal rule | STCG/LTCG, SEBI, market hours |
| `runbook` | An operational procedure | "How to re-prime a stuck broker source" |
| `narrative` | Long-form prose (replaces WHAT/WHY/HOW + architecture) | "Why Anton exists"; architecture overview |
| `memory` | Cross-session observation (replaces `memory/`) | "User prefers probes over Playwright MCP" |

`narrative` and `memory` entries are exempt from the atomic one-rule-per-file
sizing. `memory` carries a subtype (`user`/`feedback`/`project`/`reference`) and
a `scope`: `personal` (gitignored) or `shared` (committed) — turning today's
home-dir memory into versioned, optionally team-shared institutional knowledge.

---

## 7. The three formats (all derived from §6 source)

1. **Authoring** — Markdown + YAML frontmatter. Humans edit prose; Claude reads
   natively; git diffs cleanly. *Source of truth.*
2. **Index** — auto-generated `INDEX.md` (compact TOC, like `MEMORY.md`) +
   `rules.json` (programmatic lookup; lets a probe/backend assert invariants).
3. **Graph** — `fux build` runs the AST extraction itself (the engine graphify
   used, now **owned by Fux**) and merges code nodes with rule / memory /
   narrative nodes via `code_refs` → one interactive `graph.html` (search,
   per-type color filters, click-through neighbors) + `graph.json`.
   *Replaces `graphify-out/`.* **v0.1.0:** Python symbols + call edges via the
   stdlib `ast`; JS/TS, Go, and Rust get declaration nodes plus **intra- and
   cross-file `calls` edges** via a brace-matched heuristic (symbol→symbol),
   with looser file→symbol `references` as a fallback. The viewer (§10 item 16)
   is filterable, focusable, and agent-exportable
   (see [implementation-notes.md](implementation-notes.md)).

You maintain **only #1**. The other two regenerate on `fux build`.

---

## 8. Hooks

Deterministic shell — `$0` API. Shipped in the global install; projects just
reference them. Three core + one optional.

| Hook event | Runs | Effect | Requirement met |
|---|---|---|---|
| **SessionStart** | `fux context` | Injects the compact INDEX (global ⊕ packs ⊕ project) into context | *Continuously referenced* — every session starts rules-aware, no manual read |
| **PostToolUse** (Edit\|Write) | `fux touch <file>` | If the edited file is in a rule's `code_refs` and that rule wasn't updated this session → reminder to update the rule | *Best practices maintained* — enforces doc-update-per-change at edit time |
| **Stop** | `fux check` | Validates schema + dead `code_refs` + staleness before the turn ends; surfaces drift | *Maintained* — catches rot before it ships |
| **UserPromptSubmit** *(optional)* | `fux recall "<prompt>"` | Keyword-retrieves only the rules relevant to the prompt and injects them | Cheap targeted context instead of loading everything |

### Strictness modes (configurable per project — `.fux/config.toml`)

Default is **`fix`**. Each mode is a superset of the one before it:

| Mode | On drift / violation | Use when |
|---|---|---|
| `off` | Nothing | Spiking, throwaway branches |
| `warn` | Surfaces the issue as `additionalContext` — Claude sees it, you decide | Reviewing unfamiliar code |
| `fix` *(default)* | Claude auto-repairs in-session what's mechanically fixable (bump `updated`, drop dead `code_refs`, re-anchor shifted line ranges, regenerate INDEX); semantic drift is handed to Claude as a scoped edit prompt | Normal development — keeps rules current automatically |
| `strict` | `exit 2` hard-block on violated invariants / dead refs until resolved | CI gate, protected branches |

**Auto-fix split:** mechanical fixes are deterministic (`$0`). Semantic fixes
(rule prose no longer matches code) can't be deterministic, so `fix` mode emits a
tightly-scoped prompt — *"rule [day-pnl] references aggregator.py:43-46 which
changed; here's the diff — update the rule body"* — that Claude resolves inside
the session you're already in. No background LLM spend.

### Hook I/O contract (sketch)

```
stdin  ← JSON event { session_id, cwd, tool_name, tool_input.file_path, … }
stdout → guidance text / JSON additionalContext  (injected into context)
exit 0 → OK   ·   exit 2 → block (only when project opts into strict mode)
```

### settings.json wiring (sketch — written by `fux init`, not hand-edited)

```jsonc
{
  "hooks": {
    "SessionStart": [{ "hooks": [{ "type": "command", "command": "fux context" }] }],
    "PostToolUse":  [{ "matcher": "Edit|Write",
                       "hooks": [{ "type": "command", "command": "fux touch" }] }],
    "Stop":         [{ "hooks": [{ "type": "command", "command": "fux check" }] }]
  }
}
```

---

## 9. CLI surface (mirrors graphify)

```
fux init           # scaffold footprint + register hooks in a project
fux build          # regenerate INDEX.md + rules.json + graph        ($0)
fux check [--fix]  # validate schema/refs/staleness/conflicts; --fix repairs ($0)
fux context        # emit compact INDEX for hook injection            ($0)
fux recall "Q"     # keyword-retrieve relevant rules                  ($0)
fux touch <file>   # map a changed file → affected rules              ($0)
fux why <id>       # explain a rule + rationale + linked code         ($0)
fux refs <file>    # reverse lookup: which rules govern this file     ($0)
fux new <type> <id># scaffold a rule from a template                  ($0)
fux coverage       # % of important code files with a governing rule  ($0)
fux verify         # run invariant/example checks (see §10)           ($0)
fux lint           # rule *quality*: why / code_refs / edges / stub   ($0)
fux stats          # knowledge-health dashboard + weighted score      ($0)
fux savings ["Q"]  # measured token-cost win (see §12)                ($0)
fux gate [--install]# CI / git pre-commit enforcement (exit 2)         ($0)
fux mcp            # serve the substrate to agents over MCP (stdio)   ($0)
fux capture        # session observation queue for `fux distill`      ($0)
fux serve          # local dashboard over the generated views         ($0)
fux recall --hybrid# RRF-fuse lexical + semantic + graph              ($0)
```

Every command is deterministic — the same "no API cost" guarantee that made
graphify trustworthy.

Higher-level **skills** (`plan`, `adr`, `trace`, `savings`, `distill`) layer on
top of these commands — see §16.

---

## 10. Additional capabilities (the "more things")

Beyond the core, these make Fux materially more useful:

1. **Self-verifying rules.** `invariant` rules carry a `check:` assertion and
   `formula` rules carry `examples:` (given → expect). `fux verify` runs them —
   wiring into the existing `probes/` + `just` culture so a rule that drifts from
   the code **fails CI**, not just warns. Living docs that can't silently rot.

2. **Git-aware staleness + DRIFT.md.** `fux check` uses `git log` on each
   `code_refs` path: if the file's last commit is newer than the rule's
   `updated`, the rule is flagged stale. Output collected in
   `.fux/out/DRIFT.md` for a glanceable rot report.

3. **Documented-logic coverage.** `fux coverage` reports the % of "important"
   code files (configurable globs) that have at least one governing rule — like
   test coverage, but for business logic. Surfaces undocumented rules.

4. **Reverse lookup & explain.** `fux refs <file>` answers "what rules govern
   this code?"; `fux why <id>` answers "what is this rule and why?" — both
   $0, both useful to a human or to Claude mid-edit.

5. **Lifecycle & provenance.** `status: draft|active|deprecated` plus
   `created`/`updated`/`author`. Deprecated rules stay for history but are
   excluded from context injection. Trust signals on every rule.

6. **Typed relationships.** Beyond flat `related`, support `depends-on`,
   `supersedes`, `contradicts`, `implements`. Powers conflict detection and a
   richer graph.

7. **Scaffolding.** `fux new formula day-pnl` emits a correctly-shaped stub from
   a template, validated against `schema.json`. Low authoring friction.

8. **Rule packs.** Shareable, versioned domain bundles (e.g.
   `indian-markets-tax`) installable across finance projects. Domain knowledge,
   not just generic best practices, becomes reusable.

9. **CI / `just` gate.** A `just fux-check` recipe fails a PR on dead refs,
   schema errors, conflicts, or failed invariants — fits the existing
   probe + just gating model.

10. **Onboarding view.** `fux tour` emits an ordered `ONBOARDING.md` from the
    rules — a newcomer's reading path, generated from the same source.

11. **Cheap by default, smart if asked.** `recall` is **hybrid, staged**:
    lexical (`$0`) by default, with an opt-in **local** embedding re-rank for
    paraphrase recall — no API spend, honoring the "cheapest" mandate.

12. **Measured cost savings.** `fux savings` turns §12's illustrative table into
    real numbers from this project's file sizes — INDEX + rule-corpus +
    governed-code token totals, and a without-Fux vs with-Fux per-lookup
    comparison (optionally for a specific query). Deterministic, `$0`, no LLM:
    it makes the ROI argument auditable instead of asserted.

13. **Quality lint + health score.** `fux lint` judges whether a rule earns its
    weight (missing **why**, ungrounded, dangling edges, stub body — complementary
    to `check`'s structural validation); `fux stats` folds coverage, verify, drift,
    lint, and savings into one weighted **health score** (0–100). Both `$0`.

14. **Out-of-session enforcement.** `fux gate` is the CI / git-pre-commit backstop
    to the in-session Stop hook: it rebuilds the views and hard-blocks (`exit 2`)
    on blocking `check` findings or failed invariants. `fux gate --install` wires
    the pre-commit hook. Closes the "drift only caught inside a session" gap.

15. **Agent-native access (MCP).** `fux mcp` serves the read paths
    (recall/why/refs/coverage/savings/stats/context) as Model Context Protocol
    tools over stdio — a hand-rolled, **stdlib-only** JSON-RPC server (no new
    dependency) — so any agent queries the substrate directly, not by shelling out.

16. **Reviewable graph.** The interactive `graph.html` carries node/edge-type
    filters, colour-by (type/community/layer/degree), focus + neighbour
    highlighting, directed arrows, a details panel, and **agent export** (copy a
    node's neighbourhood or the visible sub-graph as markdown) — built so a human
    *or* an agent can navigate the merged code⊕knowledge graph.

---

## 11. What Fux replaces

Fux is **not a sixth system** beside the others — it absorbs them. Each former
store becomes a content type or a derived view of the one `.fux/` substrate:

| Replaced system | Becomes, in Fux | How |
|---|---|---|
| **graphify** (`graphify-out/`) | `graph.html` / `graph.json` derived view | Fux owns the AST-extraction engine; code nodes ⊕ knowledge nodes in one graph |
| **memory/** | `type: memory` entries (`user`/`feedback`/`project`/`reference`) | SessionStart hook injects them — same recall, now versioned & code-linked |
| **docs/WHAT/WHY/HOW + architecture** | `type: narrative` entries | Long-form prose authored in `.fux/`, rendered to a browsable view |
| **business rules** (inline comments) | `rule` / `formula` / `invariant` / … entries | The gap none of the above held — now first-class |

**Stays separate:** `conventions.md` / `guardrails.md` *seed* the global layer
(§5), and code-*style* linting stays with ruff/Biome (§15). Everything else
collapses into Fux: one index, one graph, one memory, one source of truth.

---

## 12. Cost analysis — with vs without Fux

**Maintenance cost** — keeping the knowledge current. Every Fux path is
deterministic; none calls an LLM:

| Action | Cost | Mechanism |
|---|---|---|
| Regenerate INDEX + json | $0 | parse frontmatter |
| Rebuild graph | $0 | `fux build` — AST extraction (Fux-owned, was graphify) |
| Detect stale rules | $0 | `git log` on `code_refs` vs rule `updated` |
| Detect dead refs / conflicts | $0 | path existence + id/edge checks |
| Verify invariants/examples | $0 | run assertions via probes/pytest |
| Reference at runtime | low | tiny INDEX injected, full rules lazy-loaded |

No maintenance path requires an LLM call.

**Reference cost** — what Claude spends to *use* the knowledge. Illustrative
token estimates for a typical cross-module question — *"how is day P&L computed,
and why?"*:

| | Without Fux | With Fux |
|---|---|---|
| Find the logic | grep + read `aggregator*.py`, `portfolio_*`, docs | read `INDEX.md`, open 1 rule |
| Tokens to answer | ~8k–40k, **repeated every session** it comes up | ~2k–4k (index + 1–3 rules) |
| Persistence | none — re-derived each time | written once, reused forever |
| Correctness | inline comments may be stale; the *why* is often absent | rule states the *why*; drift is flagged |
| Session ramp | re-discover memory + docs ad hoc | one compact INDEX at SessionStart (~1k–3k) |

**Net:** Fux trades a one-time authoring cost per rule for lookups that are
~5–10× cheaper and more correct on every later session, plus `$0` ongoing
maintenance. Folding graphify, memory, and the narrative docs into one substrate
also removes three separate upkeep paths.

**Break-even:** a rule takes a few minutes to write once and pays back the first
time a question would otherwise re-scan the codebase. Hot paths (valuation, P&L,
broker quirks) cross that line almost immediately; rarely-touched corners may
never need a rule — so **author by demand, not exhaustively**.

*(The ratios above are illustrative. **`fux savings`** now measures the real
figures from this project's file sizes — INDEX + rule-corpus + governed-code token
totals, and a without-Fux vs with-Fux per-lookup comparison — using a transparent
≈4-chars/token heuristic applied identically to both sides, so the multiplier is
the honest signal. See §10 item 12.)*

---

## 13. Rollout phases (when greenlit)

1. **Engine** — global `fux` CLI (`init/build/check/context/touch`) + rule
   schema + frontmatter validator + **AST graph backend** (the graphify engine,
   now Fux's). Standalone, no project yet.
2. **Hooks** — the 3 hook scripts in `~/.claude/fux/hooks/`; `fux init`
   registers them into a project's settings.
3. **Global best-practices seed** — port Anton's "must-know rules" (≤100 lines,
   no secrets, async, doc-per-change) into `~/.claude/fux/global/`.
4. **Anton pilot** — `fux init` in Anton; extract 3 real rules from
   `aggregator.py` (valuation, day-pnl, inr-normalization) with `code_refs`.
   Prove the loop end-to-end.
5. **Verification** — add `fux verify` + `just fux-check`; wire one invariant
   ("Σ holdings == total") to a probe.
6. **Second project** — `fux init` in Wagner to validate portability + global
   inheritance.
7. **Absorb & migrate** — fold the AST-graph engine into `fux build` (retiring
   `graphify-out/`); import `memory/` files as `type: memory`; migrate
   `WHAT/WHY/HOW` + `architecture` as `type: narrative`. Decommission the old
   stores once parity is verified.

---

## 14. Decisions

### Resolved

| Decision | Verdict | Source |
|---|---|---|
| **Hook strictness** | Configurable `off`/`warn`/`fix`/`strict`; **default `fix`** (Claude auto-repairs drift in-session); `warn` surfaces only, `strict` hard-blocks | §8 |
| **Per-project dir name** | **`.fux/`** — one hidden dir; source in `.fux/rules/`, generated in `.fux/out/` | §4 |
| **Global rules home** | **`~/.claude/fux/global/` as its own git repo** (versioned, syncable, PR-reviewable) | [global-rules-home.compare.md](global-rules-home.compare.md) |
| **Recall engine** | **Hybrid** (staged): lexical candidate-gen ships first, local embedding re-rank is the phase-2 upgrade of the same design | [recall-engine.compare.md](recall-engine.compare.md) |
| **Scope / positioning** | Fux **replaces** graphify, memory, and the narrative docs — not a sixth store beside them | §11 |

### Resolved in v0.1.0

These were the three open questions at design time; all are now decided and
implemented (see [implementation-notes.md](implementation-notes.md) §"Decisions taken"):

| Question | Call made |
|---|---|
| **Optional UserPromptSubmit recall** — v1 or later? | Shipped as `fux hook-recall`, **opt-in** via `fux init --recall`; the core 3 hooks are the default. |
| **Generated `.fux/out/` tracking** — git-track or gitignore? | **Gitignored** by default; rebuilt by `fux build` ($0). Drop the ignore line to commit `out/`. |
| **Skills layer (§16)** — `plan` alone or all three? | All three shipped (`plan` flagship + `adr` + `trace`); `plan` is the fleshed-out one. |

---

## 15. Non-goals

- Not a runtime service — it's files + a CLI + hooks.
- No mandatory LLM calls in any maintenance path.
- Not a linter for code *style* (that's ruff/Biome, which Fux does **not**
  replace) — Fux governs *knowledge*: rules, memory, narrative, and the graph.
- Not a new sixth store — it **subsumes** graphify, memory, and the narrative
  docs rather than sitting beside them (§11).

---

## 16. Skills (proposed)

> **Verdict:** Add a **small, curated** skill layer on top of the substrate —
> `plan` (flagship, kiro-style spec-driven), `adr`, and `trace` — and **defer**
> `distill` / `review`, **alias** `tour`. Worth adding *because* the planning
> skill is the capstone of the whole thesis: plan → spec → code → rules → memory,
> all in one substrate.
> **Guardrail:** a skill must read/write durable Fux entries — never orphan
> markdown — or it just recreates the `docs/*-plan.md` sprawl Fux replaces.
> **Confidence:** Medium-High · **Status:** proposed, not yet decided.

### What a Fux skill is

Core commands (§9) are the *nouns* — they build and validate the substrate.
**Skills are the verbs**: higher-level workflows, invoked `fux <skill>` or
`/fux:<skill>`, that read the graph + rules and **write new durable entries**.
They differ from Claude Code's own skills (`/code-review`, `/broker`) by being
*substrate-aware* — every skill consumes and produces Fux knowledge.

### Flagship: `fux plan` — spec-driven, kiro-style

Turns a request into three reviewable stages, each a Fux entry (not a throwaway
doc), mirroring kiro's requirements → design → tasks flow:

1. **Requirements** — user stories + EARS-style acceptance criteria → a `spec` entry.
2. **Design** — components, data flow, and *affected files pulled from the graph*
   → linked via `code_refs`.
3. **Tasks** — an ordered, checkable list → `task` entries carrying `status`.

Why it beats a plain plan doc:

- **Code-linked** — the design stage queries the graph for the *real* affected
  modules, not a guess.
- **Tracked** — `fux check` flags a `task` whose `code_refs` changed while its
  status is still `todo` (drift between plan and code).
- **Durable** — after implementation, design notes graduate into `adr` / `rule`
  entries, so the *why* survives. The plan stops being write-once scaffolding.
- **Gate** — encodes "spec before code," the discipline kiro is built around.

This is the capstone: it closes the loop the rest of Fux only stores.

### Candidate skills

| Skill | What it does | How it helps | Verdict |
|---|---|---|---|
| `plan` | Request → requirements → design → tasks (above) | Spec-driven dev, code-linked & tracked | **Add (flagship)** |
| `adr "<decision>"` | Capture an architecture decision as an `adr` entry | One-step durable *why*; `adr` type already exists (§6) | **Add** |
| `trace "<feature>"` | Walk the graph to explain how a feature spans modules | The graphify-replacement query value, as a workflow | **Add** |
| `savings ["<question>"]` | Interpret the measured token-cost report → a next action | Makes the §12 ROI auditable, not asserted; pure `$0` measurement | **Add** |
| `distill ["<focus>"]` | Capture this session's decisions as `memory`/`adr` entries | Closes the memory-replacement loop; scoped + human-confirmed so it never orphans noise | **Add (shipped)** |
| `review <diff>` | Check a diff against governing rules / invariants only | Useful, but overlaps `/code-review` — better as the `strict` hook (§8) | **Skip (fold into hook)** |
| `tour` | Ordered onboarding reading path | Already core (§10, item 10) | **Alias, don't duplicate** |

### Cost & footprint

`plan` / `adr` are the only skills that *call the LLM* — and they ride the
session you're already in (no background spend), consistent with the `fix`-mode
model (§8). `trace` is pure graph traversal → effectively `$0`. The skill layer
adds two content types to §6: **`spec`** and **`task`**.

### Should it be added? — the honest read

**Yes, but minimally.** The planning skill is the single most valuable addition:
it makes Fux a *workflow*, not just a store, and it directly absorbs your existing
`docs/*-plan.md` habit (this very file included) into something tracked and
code-linked. The risk is skill sprawl and overlap with the strong Claude Code
skill set you already run (`/code-review`, `/verify`, `/broker`). Mitigate by
shipping **only `plan` first**, proving the spec→task→rule loop on one real
feature, then adding `adr` / `trace` on demand. If `plan` doesn't earn its keep,
no other skill will.

A `spec.guide.md` (using the [guide.guide.md](guide.guide.md) pattern) should
define the plan artifact's required sections *before* `plan` is built.

---

## 17. Next steps (roadmap)

> Informed by a competitive scan of the agent-memory field (agentmemory, Mem0,
> Zep, Letta, Cognee) and the Anton pilot context. **Guiding principle:** borrow
> the *retrieval and capture mechanics* those tools do well, but never trade away
> Fux's moat — **authored, code-linked, deterministic, `$0`, verifiable** knowledge
> (the *why* + drift-checking), which none of them have. Compete on knowledge
> engineering, not on conversational recall.
>
> **Status:** the engine items (1–6, 8) are **shipped**; 7 and 9 are operational
> tasks in the Anton repo, not engine code here.

### Near-term (high ROI, on-brand, `$0`)

1. ✅ **RRF hybrid retrieval.** Fuse the three signals Fux already computes — BM25
   ([recall.py](../fux/recall.py)), local embeddings ([embed.py](../fux/embed.py)),
   and graph proximity ([graphquery.py](../fux/graphquery.py)) — with Reciprocal
   Rank Fusion (k=60). Shipped in [hybrid.py](../fux/hybrid.py); opt-in via
   `recall_hybrid` / `fux recall --hybrid`, default path unchanged.
2. ✅ **Opt-in capture → assisted `distill`.** A Stop-hook (behind `capture = true`)
   that records *which* important files changed — split governed vs uncovered, with
   a secret-path filter and SHA-256 dedup — into a queue ([capture.py](../fux/capture.py)),
   **never auto-authored**. The `distill` skill consumes `fux capture --list`. Keeps
   "authored, not captured."
3. ✅ **Memory governance.** TTL decay for `type: memory` only ([governance.py](../fux/governance.py)):
   `fux check` flags `memory-stale` past `memory_ttl_days` and `fux context` excludes
   decayed memories; supersession rides the existing `supersedes:` edge.

### Mid-term (proof & reach)

4. ✅ **A standard recall benchmark.** [bench.py](../fux/bench.py) (recall@k + MRR) over
   an expanded labelled set ([test_recall_eval.py](../tests/test_recall_eval.py)) —
   lexical recall@1 = 1.0 / hybrid recall@3 = 1.0 on the corpus.
5. ✅ **Expanded MCP surface.** `fux_query` / `fux_trace` (graph traversal) and a
   draft-only `fux_new` added to [mcpserver.py](../fux/mcpserver.py). Coordinate
   with Anton's repo-context MCP — distinct concerns; keep separate or merge.
6. ✅ **Live dashboard.** `fux serve` ([serve.py](../fux/serve.py)) serves the
   `stats` health summary + links to `graph.html`/reports over `http.server`.

### Pilot & cleanup

7. ⬜ **Anton brokers pilot.** `fux init` in Anton; ground real rules in
   `backend/app/modules/brokers/` (`day-pnl`, `inr-normalization`, the `dump_utils`
   CSV contract as a `convention`, per-broker quirks as `edge-case`); wire
   `fux verify`/`fux gate` into the existing `probes/` + `just` gate; seed the
   global layer from Anton's `docs/conventions.md` + `guardrails.md`. Measure with
   `fux coverage` + `fux savings`.
8. ✅ **Graph hardening.** A stateful sanitizer ([astextract.py](../fux/astextract.py)
   `sanitize_lines`) makes the brace matcher block-comment- and
   multiline-template-aware before counting braces.
9. ⬜ **Phase-7 decommission.** Retire `graphify-out/`, home-dir `memory/`, and the
   migrated `docs/` in Anton once parity is signed off (§13.7). **Readiness checked
   2026-06-04 — not met; do not delete yet:**
   - `graphify-out/` — **no graph parity**: Anton's Fux graph has 329 nodes vs
     graphify's 1906 (Fux's `important_globs` cover a fraction of the repo). Widen
     Fux graph coverage to match before retiring.
   - `docs/` — only 1 of 18 tracked docs (`anton-overview`) migrated to a `narrative`
     entry; `WHAT/WHY/HOW/architecture/…` still authored only in `docs/`. And
     `conventions.md`/`guardrails.md` **stay** (they seed the global layer, §11).
   - home `memory/` — the 3 project memories *are* mirrored in `.fux/memory/shared/`,
     but they're personal/cross-project; import-then-retire deliberately, not bulk.
   **Gate:** widen graph coverage → migrate the narrative docs → then retire
   `graphify-out/` + the migrated docs; handle memory last.

### Packaging & distribution (PyPI)

> **Why:** Fux is stdlib-only and already shaped as a package
> ([pyproject.toml](../pyproject.toml): dist `fux-engine`, `fux = "fux.cli:main"`,
> `[embeddings]` extra) — the ideal PyPI profile (no runtime deps, tiny wheel). The
> blocker is that the **integration layer lives outside the `fux/` package**, so a
> wheel currently ships only the CLI. Fix that, then `pipx install fux-engine`
> becomes the install path. Constraint: stays stdlib-only — `[embeddings]` remains
> the only (opt-in) extra; no runtime dependency is added.

10. ⬜ **Bundle the data into the package.** Today `package-data` only ships
    `templates/` + `assets/`; `schema.json`, `hooks/`, `global/`, and `skills/` sit
    at the repo root and are absent from a wheel — so `fux init` would fail schema
    validation and ship no `/fux` skill/hooks. Relocate/bundle them as package data
    and resolve `schema.json` from the package first ([paths.py](../fux/paths.py)).
11. ⬜ **`fux setup` command.** Port `install.sh`'s global steps (scaffold
    `~/.claude/fux/{engine,global,packs,hooks}`, install skills, seed the global git
    repo) into an idempotent subcommand sourcing the **bundled** data, so the
    install story is `pipx install fux-engine && fux setup`. `install.sh` becomes
    `pip install -e . && fux setup` for contributors (editable/live-reflect kept).
12. ⬜ **Release workflow.** GitHub Actions + PyPI **Trusted Publishing** (OIDC, no
    token); `python -m build`; tag `vX.Y.Z`. Keep dist name `fux-engine` (the bare
    `fux` name appears unclaimed on PyPI — optionally grab it; the import package
    stays `fux`). Add `pipx`/`uvx` usage to the README.

> **Sequencing:** items 10–11 are the right architecture regardless and remove the
> only blocker — do them first. Gate the **public** `0.1.0` release (12) on the
> Anton pilot (item 7) so the README can lead with measured `fux savings`/`coverage`
> from a real project, not a toy.

### Explicitly *not* doing

- Becoming a conversational-memory vendor (Mem0/Zep/Letta). Fux may *interoperate*
  with such a backend for raw episodic recall, but the authored-rule + graph +
  verify layer is the product.
- Any mandatory LLM call in a maintenance path (§3, §15) — the capture hook (item 2)
  rides the current session and only drafts; it never spends in the background.

---

## Appendix A — worked example rule (grounded in real code)

`.fux/rules/day-pnl.md` — extracted from
`backend/app/modules/brokers/aggregator.py:43-46`:

```markdown
---
id: day-pnl
domain: portfolio
type: formula
status: active
code_refs:
  - backend/app/modules/brokers/aggregator.py#L43-L46
related: [portfolio-valuation, inr-normalization]
check: "abs(sum(h.day_pnl for h in holdings) - portfolio.day_pnl) < 0.01"
examples:
  - given: "₹1,00,000 holding, +2% today"
    expect: "₹2,000"
---
**Rule:** Today's P&L uses *current* INR value, not invested cost.
**Formula:** `day_pnl = Σ (inr_value(h) × day_change_pct(h) / 100)`
**Why:** day_change_pct is relative to yesterday's close, so it must multiply
today's market value; using invested cost double-counts appreciation.
**Edge cases:** `day_pnl_pct = 0` when current value is 0 (div-by-zero guard).
```
