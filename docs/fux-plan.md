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

### Constitution layer (tiered governance)

Fux's substrate gains an optional, additive **governance tier** layered on the §6
schema. Every rule carries a `tier` — `constitutional` | `standard` (default) |
`advisory` — fixing how hard it bites, orthogonal to *coverage* (how much of the
project is governed):

- **Constitutional** — the thin apex of must-never-break invariants (determinism,
  money/PII, audit, and the amendment process itself). Ratified, supersession-only,
  blocks unconditionally regardless of `mode`.
- **Standard** (default) — conventions, ADRs, domain rules. Kind-based blocking, but
  only under `strict` (the project `mode`); change via normal PR + `fux check`.
- **Advisory** — style nudges and memories. Warn only.

The layer is purely additive and a no-op until opted in: `tier` defaults to
`standard`, upgrading promotes nothing, and every existing rule stays valid unchanged.

**Enforcement (`fux/findings.py::blocking`, deterministic, `$0`).** A finding blocks by
the tier of the rule it is raised against:

| tier | blocks when |
|---|---|
| `constitutional` | **any** finding, in **any** `mode` (this also makes `unsealed` block for the apex) |
| `standard` | `kind ∈ BLOCKING` **and** `mode == "strict"` |
| `advisory` | never |

`fux gate` reads the project `mode` and applies this matrix — so constitutional rules
are the only ones that block a non-`strict` tree.

**Migration guard (§5b, transient).** Adopting the layer on a repo that already has rules
must change nothing until opted in. `fux check --baseline-write <file>` snapshots current
findings (canonical order: kind, rule_id, message); `fux gate --baseline <file>` re-runs
and exits 2 only on findings *new* since the snapshot — pre-existing findings and all
advisories are tolerated. Captured pre-upgrade and committed to the upgrade PR, it makes
"no surprise breakage" CI-testable. A small `fux/baseline.py` helper reuses the `Finding`
serialization, and `fux check` output is canonically sorted so the diff is meaningful.
This is a transient upgrade check, **not** a permanent regression subsystem.

**Tamper-evidence (`fux/constitution.py`, deterministic, `$0`).** A ratified
constitutional rule is made tamper-evident with two independent seals, both recomputed by
`fux check` and surfaced as an always-blocking `tampered` finding (any tier/mode):

- `ratification.content_seal` — a hash of the rule's normalized body + governing
  frontmatter (volatile `seal`/`ratification`/`updated` excluded). `check_tamper`
  recomputes it and compares to the stamped value, catching an in-place body/meaning edit.
- `.fux/constitution.lock` — a committed `{id: content_seal}` manifest of every ratified
  constitutional rule. `check_lock` compares it to the live set, catching a rule **added,
  deleted, or re-stamped outside the ritual**. To fake an edit you must change both the
  rule and the lock — and the lock is only ever written by `fux ratify`, so it shows in the
  PR diff.

`fux ratify <id>` (deterministic, no LLM) is the **only path into the constitutional
tier**: it stamps `ratification.{by,date,content_seal,debate_hash?}`, freezes the code seal,
and rewrites the lock. Tamper/lock checks apply to **ratified constitutional rules only** —
un-ratified rules and every non-constitutional rule are untouched, so adoption stays a no-op
until you opt in by ratifying.

**Debate engine (§7b — agent-driven, `$0` to Fux).** How a principle *becomes* law: the
`/fux debate "<rule>"` skill drives the **host** session (the tokens you already pay for) to
spawn **two sub-agents**, both fluent in building *and* selling, with **no assigned sides**.
Each forms its position **blind** (without seeing the other), then they reveal and debate
under anti-sycophancy gates: each must surface ≥ 1 concrete objection; convergence counts
only after both tried to break the rule; instant agreement on a constitutional rule forces
one extra adversarial round. Non-convergence **escalates to the human**, who is the
tie-breaker and ratifier. Fux's only *code* role is the deterministic harness: the transcript
is captured to `.fux/debates/<id>.md`, and `fux ratify … --debate <file>` hashes it into
`ratification.debate_hash` — so the *reasoning*, not just the verdict, is auditable. Fux
makes no API call; the maintenance path stays model-free (guarded by a test, plan §0).

The meta-rule that governs the layer itself is
[`con-amendment`](../.fux/rules/con-amendment.md): a constitutional rule is created or
changed only via **propose → debate → ratify**, changes only by **supersession** (never
in-place edit), and ratification needs a named human ratifier plus a recorded debate. Tier
blocking + migration guard ship in Phase 1; tamper-evidence + `fux ratify` in Phase 2; the
two-agent debate that stamps `ratification.debate_hash` in Phase 3.

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
    comparison (optionally for a specific query), reported in **tokens and dollars**
    (configurable `usd_per_mtok`, default = Claude Opus 4.8's $5/M input rate).
    Deterministic, `$0`, no LLM: it makes the ROI argument auditable instead of
    asserted.

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

16. **Reviewable graph.** The interactive `graph.html` is the **"Solar Terminal"**
    viewer (a Claude Design handoff): a three-rail instrument layout where **code
    desaturates to graphite dust, knowledge nodes ignite incandescent amber, and
    the rare `governs` edges stream across as glowing threads** — so the brief's
    function-soup and knowledge↔code problems are solved by the visual language
    itself. Left rail: stats, search→clickable hits, a Lens grid
    (Knowledge/Communities/Heat/Path), per-type meters-as-filters, and an inspector
    that surfaces "governed by" first. Centre: the canvas, a Micro/Macro mode pill,
    an edge-language legend, a zoom well. Right rail: a live **minimap** and a
    **governance ledger** of every knowledge→code link with "copy governed
    subgraph" export. Underneath: bounded inverse-square repulsion + community
    centroid pull (spreads + clusters, no hairball), percentile `fit`, **semantic
    zoom** to community super-nodes you can drill into, centrality-driven size +
    hub halos, a knowledge lens, and BFS **path mode** — all still offline,
    dependency-free, system-font, and **agent-exportable as markdown**.

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
the honest signal. It also prices every figure in **dollars** at a configurable
`usd_per_mtok` (default = Claude Opus 4.8's $5/M input rate; the win is on input
tokens, so the input price is the right one — model-agnostic, set per project). See
§10 item 12.)*

*(Opt-in `cost_tracking` ([costledger.py](../fux/costledger.py)) goes further: it
records **every** `fux recall` lookup's measured savings into `.fux/cost.json` —
a cumulative lifetime total (tokens-without/with/saved, shown in tokens *and*
dollars) rather than a single estimate. The ledger stores only tokens, so a price
change re-prices history without a rewrite. Only code-bound matches count, so the
running multiplier stays honest; `fux savings` prints it and `fux savings --reset`
clears it. Still `$0`.)*

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
   `graphify-out/` + the migrated docs; handle memory last. The engine work that
   makes each step possible (and the gate measurable) is **items 13–17 below**.

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

### Unblocking decommission (parity engine work)

> The 2026-06-04 readiness check (§17.9) found the decommission isn't blocked by
> *policy* but by **missing engine capability** — Fux can't yet *match* the stores
> it claims to replace, so retiring them would lose data. Each blocker maps to a
> concrete feature; with these built, "parity signed off" is now **measurable** via
> `fux parity`. All `$0`, deterministic. **Status: shipped — the remaining work is
> running them against Anton (item 7).**

13. ✅ **Full-repo graph coverage.** `graph_globs` ([config.py](../fux/config.py)) is
    decoupled from `important_globs` — `fux build` graphs the broad set, `coverage`
    keeps the narrow one; `fux build --full` widens to every non-ignored file
    ([graph.py](../fux/graph.py) `_iter_sources` skips `.fux/`/`.git/`).
14. ✅ **`fux import <path…>` — docs → `narrative`.** [importer.py](../fux/importer.py)
    `import_docs` ingests markdown files/dirs as `narrative` entries (frontmatter
    stamped, body preserved); skips existing without `--force`.
15. ✅ **Narrative rendering.** [narrative.py](../fux/narrative.py) renders a
    `NARRATIVE.md` (TOC + bodies) on `fux build`, linked from `fux serve`.
16. ✅ **`fux import-memory`.** `importer.import_memory` mirrors home-dir
    `~/.claude/.../memory/*.md` into `.fux/memory/<scope>/`, normalising
    `subtype`/`scope` and skipping the `MEMORY.md` index.
17. ✅ **`fux parity` (measurable gate).** [parity.py](../fux/parity.py) asks the
    question that matters — *is any current source file invisible to the graph?*
    (coverage of `graph_globs` files, not a node-count match against a possibly
    **stale** `graphify-out/`) — plus `docs/` not yet `narrative` (excluding
    `conventions`/`guardrails` and any `parity_stay`) and home-memory not yet
    imported. `READY`/`NOT READY`, exit 1 until ready. It also flags a stale legacy
    graph. **This is the gate that says when it is safe to delete.**

> **Order to retire Anton's stores (now tool-backed):** `fux build --full` until
> `fux parity` graph ✓ → `fux import docs/` + rebuild until docs ✓ →
> `fux import-memory` until memory ✓ → then §17.9's retirement is a green-light.

### Best-in-class (the three pillars to SOTA — `$0`, high-ROI)

> Beyond the planned roadmap, but *not* speculative: push the three things Fux
> already does — **retrieve**, **stay-correct**, **integrate** — to best-in-class,
> all within the existing constraints. These are the highest-ROI "more" because they
> raise quality on the surface agents hit every turn. **Status: 18, 19 & 20 shipped
> (19: centrality + the optional `[ast]` tree-sitter extra, default still stdlib-only);
> 21 deferred (needs agent runs).**

18. ✅ **Retrieval to SOTA.** Recall is what agents hit most — today BM25-lite +
    opt-in trigram + graph RRF ([recall.py](../fux/recall.py), [hybrid.py](../fux/hybrid.py)),
    validated on one small paraphrase set. Three `$0` lifts: **(a) real BM25F** —
    proper per-field length normalization + saturation, which beats the lite scorer
    on short frontmatter fields; **(b) deterministic query expansion** — expand a
    query with `glossary` synonyms and **1-hop graph neighbours** before scoring (the
    graph is the most under-used asset — recall touches it only as one RRF list);
    **(c) a benchmark worth quoting** — grow [test_recall_eval.py](../tests/test_recall_eval.py)
    to a **50–100 query** set with **hard negatives** and add a **recall@k/MRR
    regression gate** in CI ([bench.py](../fux/bench.py)). Turns "recall@1 = 1.0 on a
    toy set" into a credible recall@k curve. **Shipped:** true per-field BM25F
    ([recall.py](../fux/recall.py) `_bm25f`); opt-in `expand_terms` (glossary + 1-hop
    `related`) via `recall_expand` / `--expand`; eval grown to 24 queries with hard
    negatives + a `test_recall_regression_gate` (recall@1 0.875 / recall@3 1.0 /
    MRR 0.931).
19. ✅ **Graph to exact.** Non-Python extraction is a brace-matched heuristic — the
    honest ceiling on graph quality. **(a) Optional `tree-sitter` extra** (same
    opt-in pattern as `[embeddings]`): default stays `$0`/hand-rolled, but
    `pip install fux-engine[ast]` yields real call graphs for JS/TS/Go/Rust
    ([astextract.py](../fux/astextract.py)). **(b) Centrality beyond
    degree** — `GRAPH_REPORT.md` ranks god-nodes by raw degree; add deterministic
    **PageRank / betweenness** (pure stdlib, ~40 lines, [community.py](../fux/community.py)/
    [graph.py](../fux/graph.py)) to find architectural chokepoints degree misses, and
    feed the score back into recall ranking. Makes the graph *trustworthy*, not just
    "good enough." **(b) shipped:** deterministic PageRank ([graphquery.py](../fux/graphquery.py)
    `pagerank`/`chokepoints`), stored as `centrality` on every node and surfaced in a
    `GRAPH_REPORT.md` "Chokepoints" section. **(a) shipped:** the optional `[ast]`
    extra ([astextract.py](../fux/astextract.py) `_treesitter`/`_ts_parser`) swaps the
    regex/brace heuristic for real ASTs on JS/TS/Go/Rust when
    `tree-sitter`+`tree-sitter-language-pack` are installed — **same node/edge schema**,
    just more accurate (e.g. Go structs become `class` nodes the heuristic missed).
    The default stays stdlib-only; tree-sitter is never required, never an LLM, still
    deterministic. To keep the graph **reproducible across machines**, `graph.build`
    stamps `meta.extractor` with the active backend + grammar versions
    (`backend_fingerprint()`), and `fux check` raises a non-blocking `extractor-drift`
    finding when a committed graph was built with a different backend than the one
    present locally — divergence is *auditable*, not silent. Richer import/type edges
    are deliberately **not** added to the stored substrate (kept for the report layer)
    so the graph never diverges by more than the heuristic already does.
20. ✅ **Verification hardening (the moat).** Verify is the thing competitors don't
    have, so SOTA matters most here. **(a) Property/example fuzzing** — `examples:`
    run fixed inputs; deterministically generate boundary inputs (zero, negative,
    currency edges) against `check:` invariants, reproducible under a fixed seed
    ([vexamples.py](../fux/vexamples.py)). **(b) Contradiction & supersession
    auto-suggest** — flag when a new `memory`/rule overlaps an existing rule's
    `code_refs` and disagrees, drafting a `contradicts:`/`supersedes:` edge (closes
    "stale knowledge silently lies"; the [governance.py](../fux/governance.py) follow-up
    already noted in §4). **(c) Usage-weighted decay** — TTL is time-only; log which
    rules `recall`/`context` actually serve, then decay *unused* knowledge and surface
    *hot* knowledge — a feedback signal nothing else in the space has. **Shipped:**
    (a) `fux verify --fuzz` ([vexamples.py](../fux/vexamples.py) `fuzz_examples`) flags
    unguarded div-by-zero at numeric boundaries; (b) `overlap-unlinked` lint finding
    ([lint.py](../fux/lint.py) `_overlaps`) for two unlinked rules over the same code
    span; (c) opt-in `usage_tracking` ([usage.py](../fux/usage.py)) feeds
    [governance.py](../fux/governance.py) — a memory served within the TTL window stays
    alive, an unused one still decays.
21. ⬜ **Automated value proof.** *(Deferred — needs live agent task runs, so it can't
    be a `$0` unit-tested engine feature; tracked for a separate harness.)* `fux
    savings` measures *token cost*; the stronger
    claim is *task quality*. Build an **A/B harness** that runs the same agent task
    with and without Fux context and diffs the outcome — the experiment that lets the
    README say "Fux makes the agent measurably *more correct*," not just cheaper.
    Composes the existing `$0` surfaces ([savings.py](../fux/savings.py), [bench.py](../fux/bench.py));
    no maintenance-path LLM (the task runs are the experiment, not a Fux dependency).

### Frontier (research-grade, still `$0` and deterministic)

> Bets that push *what a knowledge engine is*, not just do the known things better.
> Each leans on an asset only Fux has — a single versioned frontmatter substrate, a
> rule⊕code graph, git underneath, and an **agent** (not a human) as the consumer.
> All stay stdlib-only, `$0`, no maintenance-path LLM. **Status: 22–25 shipped; 26
> deferred (needs MCP-runtime logging); 27 undecided** (stretches §3 self-contained).

22. ✅ **Proof-carrying rules (AST seals).** Drift today is git-log on `code_refs`
    (§8) — coarse: a whitespace edit trips it, a semantic change inside an untouched
    signature does not. Bind each rule to a **normalized-AST fingerprint** of the
    symbol it governs (names/literals folded) computed on author, recomputed on
    `fux build`. When the structure diverges, the rule's **seal breaks** — a new
    `unsealed` finding ([findings.py](../fux/findings.py)) — until a human
    re-affirms. Whitespace/comment edits don't break it; a flipped comparison or a
    changed branch does. Upgrades drift from *the file's mtime moved* to *the thing
    I claimed about structurally changed*. Touches [astextract.py](../fux/astextract.py)
    (fingerprint), [schema.json](../schema.json) (a `seal:` field), [drift.py](../fux/drift.py)/
    [check.py](../fux/check.py). Python first (real `ast`); other languages ride the
    brace-matcher span hash. **Shipped:** [seal.py](../fux/seal.py) (normalized-AST
    skeleton fingerprint), a `seal:` field, `fux seal [ids] [--all]`, and the advisory
    `unsealed` finding in [check.py](../fux/check.py).
23. ✅ **Deterministic rule mining.** Authored-only knowledge bases die of
    cold-start — only the rules someone bothered to write exist. Invert it:
    Daikon-style static + fixture-driven invariant detection over the code (an arg
    never null, a return always positive, a constant repeated across N sites, a
    normalization that always precedes a sum) surfaces **candidate** `invariant`/
    `convention` entries for human confirmation — the same draft-only, never-auto-
    authored pattern as `capture` → `distill` (§17.2). A new `fux mine`. Turns Fux
    from "a notebook you must fill" into "it points at the knowledge already latent
    in the code." `$0`, no LLM. **Shipped (first miner):** [mine.py](../fux/mine.py) +
    `fux mine` surface magic numbers repeated across ≥N sites as draft `convention`
    candidates (Python via `ast`, others via the sanitized digit scan). Richer
    invariants (null/positivity/ordering) are the next miners.
24. ✅ **Knowledge archaeology (temporal *why*).** The substrate is git-versioned, so
    every *why* has a history nobody can see today. Build the time axis over
    `.fux/rules/` ([gitutil.py](../fux/gitutil.py)): `fux why <id> --history` walks
    how an understanding evolved, which decisions were reversed (`supersedes:` chains
    over time), which rule last changed before an incident. Git-blame for *reasons*,
    not lines — a capability that can't exist where the *why* isn't a first-class
    versioned object. **Shipped:** `fux why <id> --history` ([explain.py](../fux/explain.py)
    `render_history` over [gitutil.py](../fux/gitutil.py) `file_history`, `--follow`).
25. ✅ **Optimal context packing (knapsack).** SessionStart injects the whole INDEX
    and recall picks top-N — both heuristics. Fux already measures tokens precisely
    ([savings.py](../fux/savings.py)). Treat assembly as a budgeted **knapsack**:
    given `context_budget_tokens` and a query, select the rule subset maximizing
    relevance-per-token. Context injection becomes a *provably-optimal* pack, not a
    vibe — a flagship claim for an agent-first tool. Touches [context.py](../fux/context.py)
    + the recall scorer; default (no budget set) path unchanged. **Shipped:** a real
    0/1 knapsack DP ([pack.py](../fux/pack.py)) gated on `context_budget_tokens`
    (default 0 ⇒ inject everything), wired into [context.py](../fux/context.py).
26. ⬜ **Self-densifying graph.** *(Deferred — requires logging agent traversals at MCP
    runtime, not a deterministic build-time path; tracked separately.)* Today the
    agent *reads* the graph; close the loop.
    When Claude walks it to answer something (via MCP `fux_trace`, [mcpserver.py](../fux/mcpserver.py)),
    record the **traversal path as a candidate `narrative` entry** — human-confirmed,
    never auto-authored (the `capture` → `distill` discipline, §17.2). The agent's
    exploration becomes durable knowledge, so the next session starts denser: a base
    that gets *more* complete the more it's used, with **knowledge-entropy-over-
    sessions** as a metric no competitor can even define.
27. ⬜ **Federated knowledge mesh** *(stretches §3 "self-contained" — **undecided**;
    maybe we build it, maybe not; build last if ever)*. Generalize `packs`
    ([loader.py](../fux/loader.py)) from a static overlay into a **local filesystem
    federation** across the sibling repos (Anton/Wagner/Bach/…): query knowledge
    across projects, detect when one repo violates a decision another recorded,
    propagate a `supersedes:`. Strictly **local-FS, read-only, no network service** —
    keeps the §15 non-goal (not a networked memory vendor) intact while turning a
    per-repo tool into shared infrastructure. The riskiest to the brand; the only
    item here we may deliberately *never* ship.

### Explicitly *not* doing

- Becoming a conversational-memory vendor (Mem0/Zep/Letta). Fux may *interoperate*
  with such a backend for raw episodic recall, but the authored-rule + graph +
  verify layer is the product.
- Any mandatory LLM call in a maintenance path (§3, §15) — the capture hook (item 2)
  rides the current session and only drafts; it never spends in the background.

---

## 18. Fux as Anton's brain — two consumers, one substrate

> **Status: the full on-the-fly pipeline is shipped.** Engine: `fux impact`
> ([impact.py](../fux/impact.py)), `fux components` ([components.py](../fux/components.py)),
> `fux validate-spec` ([uispec.py](../fux/uispec.py)), `fux feedback`
> ([feedback.py](../fux/feedback.py)) — all exposed over MCP. Anton: a `/concierge/compose`
> endpoint generates a declarative UISpec, Fux validates it, and a whitelisted
> `DynamicRenderer` mounts it; the `ui-component-contract` rule governs the loop.
> **Guiding principle held:** Fux is the *read/validate* brain — it never executes.
> Orff emits a **declarative spec, never code**; Anton renders from a fixed whitelist.

The earlier sections frame Fux as a knowledge engine read by **Claude Code at
dev-time**. The target is bigger: Fux becomes the brain serving **two consumers
through one interface** —

| Consumer | When | Reads Fux for | Interface |
|---|---|---|---|
| **Claude Code** | dev-time | maintain + write code against the rules/graph | CLI + hooks |
| **Orff concierge** | **runtime** | build components on the fly, bound to real data | **`fux mcp`** |

The unifying decision (already half-built): the **MCP server (§17.5) is the shared
brain interface**. Orff already does parallel tool execution + RAG; Fux is one more
tool it calls. Everything below is exposed there, so dev-time and runtime read the
*same* substrate instead of forking into two systems.

### 18.1 Maintain code — `fux impact <file>` ✅

The "what will I break?" query, before an edit. Pure `$0` traversal of the merged
graph ([impact.py](../fux/impact.py)): given a file it returns

- **Invariants that must still hold** — governing rules carrying a `check:`, with
  the assertion shown → run `fux verify`.
- **Governing rules whose *why* may go stale** → the `doc-per-code-change` target,
  made concrete.
- **Downstream callers** (precise `calls`) split from **possibly-affected**
  (loose `references`, INFERRED) — honouring the graph's own confidence model so
  generic names like `value`/`total` don't drown the real dependents.

Exposed as `fux_impact` in [mcpserver.py](../fux/mcpserver.py). Proven on Anton:
editing `aggregator.py` surfaces `day-pnl` + `holdings-sum-equals-total` to
re-verify, the two governing formulas to refresh, and 5 precise callers (the route
handlers, the broker test, and `fux_totals_probe.py`).

### 18.2 Write code — born-compliant generation ⬜

- **Populate the `examples:` field** (schema §6, currently empty) with canonical
  patterns — "a new `BrokerSource` looks like this," "a query hook looks like this"
  — so generation copies, not invents.
- **Machine-readable contracts.** The `dump_utils` CSV contract / `BrokerSource`
  interface become `convention` rules holding *interface + invariants*; the agent
  generates against them and `fux check` validates before they land.

### 18.3 Orff builds components on the fly — the runtime leap

Three things Fux must expose so Orff composes instead of hallucinating:

1. ✅ **A component registry** (`fux components`). Each TS/TSX source is scanned
   for the `<Name>Props` convention; Fux emits every component with its **prop
   fields** (name, type, optional) — backend-independent (works with or without
   tree-sitter). On Anton: 68 components (41 in `packages/solar-ui`), with full
   prop lists. The prerequisite for safe runtime generation, shipped in
   [components.py](../fux/components.py).
2. ✅ **A data-binding catalog.** The same command surfaces the **data hooks**
   (`use*`, e.g. `useHoldings`) and **DTOs** (`*DTO`, e.g. `HoldingDTO`) — 37 + 19
   on Anton — so Orff binds to the real data layer instead of refetching. `--json`
   output is what `fux_components` returns over MCP for Orff to consume.
3. ✅ **Mount-time enforcement** (`fux validate-spec`). The model emits a declarative
   UISpec, never code; [uispec.py](../fux/uispec.py) validates it against the registry
   (unknown component / undeclared prop / unknown data hook / illegal children →
   rejected) before the client sees it, and the client `DynamicRenderer` *re-gates*
   against a whitelist. This is the safe-by-construction answer to "execute generated
   UI": there is **no code path that runs model output** — the worst a bad model emits
   is a spec the validator rejects. The `ui-component-contract` rule (in Anton's
   `.fux/`) governs the loop; new primitives become composable just by being exported
   + whitelisted (they then appear in `fux components` automatically).

### 18.4 Feedback loop — the brain learns ✅

Every compose outcome (valid / rejected / repaired, with the violations) is appended
by `fux feedback` ([feedback.py](../fux/feedback.py)); `fux feedback` reports the
acceptance rate and the top rejection reasons — so a recurring failure (a component
the model keeps reaching for that isn't whitelisted) surfaces as a concrete registry
or contract gap. Deterministic, `$0`, no `memory` writes — telemetry that closes the
loop without the "captured-not-authored" compromise.

### The end-to-end flow (Anton)

```
prompt → /concierge/compose → fux components (vocabulary) → LLM emits UISpec JSON
       → fux validate-spec (reject/repair, 1 retry) → ComposeResponse
       → <DynamicRenderer> mounts from the whitelist → fux feedback records outcome
```

`compose_service.py` + `fux_bridge.py` (backend) talk to the brain over the `fux`
CLI; `DynamicRenderer.tsx` + `compose.registry.ts` (frontend) render only whitelisted
primitives. Every brain step is `$0` and deterministic; the only LLM call is the
generation itself, which rides the user's request (no background spend).

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
