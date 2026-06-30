# Fux — the complete guide (what it does, with examples)

> A worked, example-driven tour of **everything Fux does**. For the one-line command
> table see [cli.md](cli.md); for the design rationale see [fux-plan.md](fux-plan.md);
> for status see [fux-implementation.md](fux-implementation.md). Every command here is
> `$0` and deterministic — no LLM, no network — unless explicitly noted.

All example output below is real, taken from the Anton pilot project.

---

## 1. The mental model

Fux turns the *why* behind your code into a **first-class, versioned substrate**, then
derives cheap views from it. You maintain **only** the source frontmatter; everything
else regenerates on `fux build`.

```
Tier 0  CLAUDE.md pointer ........ 1 line, always in Claude's context
Tier 1  .fux/out/INDEX.md ........ ~1 line/rule, read FIRST            ← cheap
Tier 2  .fux/rules/<id>.md ....... opened ONLY when relevant           ← lazy
Tier 3  .fux/out/{rules,graph}.json  machine lookup + browsing
```

One substrate → three derived views: an **index** (fast lookup), a **graph** (rule⊕code
map), and **memory/narrative** (cross-session knowledge). On top of that sit
verification, quality/health, cost measurement, and agent integration.

---

## 2. The substrate: a rule file

Each entry is a markdown file with YAML frontmatter + a prose body. Example —
`.fux/rules/day-pnl.md`:

```markdown
---
id: day-pnl
domain: portfolio
type: formula
status: active
created: 2026-06-03
updated: 2026-06-03
code_refs:
  - backend/app/modules/brokers/aggregator.py#L43-L46
related: [inr-normalization, portfolio-valuation]
check: "abs(day_pnl - sum(v * (p / 100.0) for v, p in zip(inr_values, day_change_pcts))) < 0.01"
examples:
  - given: "inr_values=[100000], day_change_pcts=[2], day_pnl=2000"
    expect: "true"
seal: 4669fe7da358d347
---
**Rule:** Today's P&L is computed on *current* INR value, not invested cost…
**Why:** `day_change_pct` is already relative to yesterday's close…
**Edge cases:** brokers that don't populate `day_change_pct` contribute `0`…
```

- **`type`** — one of `rule`/`formula`/`glossary`/`invariant`/`adr`/`edge-case`/
  `convention`/`regulatory`/`runbook`/`narrative`/`memory` (+ skill types `spec`/`task`).
- **`code_refs`** — the code this governs (`file#Lstart-Lend`); powers `refs`, the graph
  `governs` edge, drift, and savings.
- **`check`/`examples`** — the executable invariant and worked cases (`fux verify`).
- **`seal`** — an AST fingerprint of the governed code (`fux seal`; §7.3).
- **`related`/`edges`** — typed links (`depends-on`/`supersedes`/`contradicts`/`implements`).

Author a stub with the right template:

```bash
fux new formula day-pnl --domain portfolio   # → .fux/rules/day-pnl.md to fill in
```

---

## 3. Lifecycle: init → build → check

```bash
cd your-project
fux init                 # scaffold .fux/ + wire 3 hooks + a CLAUDE.md pointer
fux build                # regenerate INDEX.md + rules.json + graph + NARRATIVE.md
fux check --fix          # validate; repair mechanical drift
```

`fux build` output:

```
✔ Built: 24 active rules · 340 code files · 6800 edges · 144 communities → .fux/out
```

`fux build --full` widens the graph to every non-ignored file (a whole-repo scan).

---

## 4. Reading the knowledge

### `fux context` — what Claude sees at SessionStart
Emits the Tier-1 INDEX (one line/rule, grouped by domain). Injected automatically by the
SessionStart hook. With `context_budget_tokens > 0` it **knapsack-packs** the optimal
subset under the budget (for very large corpora).

### `fux recall` — find the relevant rule(s)
Lexical **BM25F** (per-field length-normalised) by default:

```bash
$ fux recall "how is day P&L computed" --top 3
 1.474  day-pnl (formula) — Today's P&L is computed on current INR value, not invested cost
 1.381  portfolio-valuation (formula) — Portfolio totals over INR-normalised holdings
 0.996  broker-csv-dumps (narrative) — Broker CSV Dump Convention
```

Two opt-in widenings (both still `$0`):
- `--hybrid` — RRF-fuse lexical ⊕ local-semantic ⊕ graph-proximity.
- `--expand` — add glossary synonyms + 1-hop `related` neighbours before scoring.

### `fux why <id>` — explain a rule
```bash
$ fux why day-pnl
# day-pnl (formula) · portfolio · active · [project]

**Governs:** backend/app/modules/brokers/aggregator.py#L43-L46
**Related:** inr-normalization, portfolio-valuation
**Invariant:** `abs(day_pnl - sum(v * (p / 100.0) for v, p in zip(...))) < 0.01`

**Rule:** Today's P&L is computed on *current* INR value, not invested cost…
**Why:** `day_change_pct` is already relative to yesterday's close…
```

### `fux why <id> --history` — how the *why* evolved (knowledge archaeology)
Git-blame for *reasons*, not lines:

```bash
$ fux why day-pnl --history
# day-pnl — history

- `2026-06-04` fix: clarify div-by-zero guard in day_pnl_pct (a1b2c3d)
- `2026-06-03` chore: pilot fux knowledge engine into anton (97491ef)
```

### `fux refs <file>` — reverse lookup
```bash
$ fux refs backend/app/modules/brokers/aggregator.py
day-pnl (formula) — Today's P&L is computed on current INR value, not invested cost
holdings-sum-equals-total (invariant) — The portfolio's current_value total must equal…
inr-normalization (rule) — Every holding's monetary fields are converted to INR…
portfolio-valuation (formula) — Portfolio totals over INR-normalised holdings…
```

---

## 5. The graph (rule ⊕ code map)

`fux build` extracts symbols and call edges across **Python** (stdlib `ast`) and
**JS/TS/Go/Rust** (a brace-matched heuristic), merges them with rule nodes, clusters into
communities, and ranks centrality.

### `fux query` — traverse from rules matching a question
```bash
$ fux query "day pnl" --depth 1
# portfolio-valuation (formula)
  → aggregator.py (code-file)
  → day-pnl (formula)
  → holdings-sum-equals-total (invariant)
  → inr-normalization (rule)
```

### `fux explain <term>` — a node + its neighbours
```bash
$ fux explain aggregator.py
# aggregator.py (code-file)
file: backend/app/modules/brokers/aggregator.py
community: 0
neighbors:
  · HoldingsAggregator (class)
  · _inr_value (function)
  · all_holdings (function)
```

### `fux path <a> <b>` — shortest path between two nodes.
### `fux report` — `GRAPH_REPORT.md`: node types, **god nodes (degree)**, **chokepoints (PageRank centrality)**, and communities.

PageRank finds *architectural* chokepoints a raw degree count misses; every node also
carries a `centrality` score in `graph.json`, and the interactive `graph.html` lets you
colour by type / community / layer / degree and **export** a node's neighbourhood as
markdown for an agent prompt.

---

## 6. Coverage

```bash
$ fux coverage
Documented-logic coverage: 4% (2/51 important files)
  ✗ backend/app/modules/brokers/__init__.py
  ✗ backend/app/modules/brokers/_cdp.py
```

% of "important" code files (config `important_globs`) that have at least one governing
rule. Low is expected early — **author by demand, not exhaustively**.

---

## 7. Staying correct (the moat)

### 7.1 `fux check [--fix]` — drift & validity
Validates schema, dead `code_refs`, git-staleness, and conflicts; writes `DRIFT.md`.
`--fix` applies mechanical repairs (drop dead refs, bump `updated`, regenerate INDEX).
Findings: `schema`, `dead-ref`, `stale`, `plan-drift`, `conflict`, `invariant`,
`memory-stale`, `unsealed`.

### 7.2 `fux verify [--fuzz]` — run the invariants
```bash
$ fux verify
· day-pnl no verification data       # skip — never a false fail
✔ day-pnl[ex1]                       # worked example passes against check:
✔ holdings-sum-equals-total
```

`check:` is eval'd in a restricted namespace; data comes from `verify_cmd:` (a shell
command printing JSON), `.fux/verify/<id>.json`, or `.fux/out/verify_context.json`. No
data → **skip** (never a false failure).

`--fuzz` perturbs numeric example inputs to boundaries (0, ±1, ±1e9) and flags an
unguarded division:

```bash
$ fux verify --fuzz
✗ day-pnl[fuzz base=0] check divides by zero at the boundary — add a guard
```

### 7.3 `fux seal` — proof-carrying rules (AST seals)
Bind a rule to a **normalized-AST fingerprint** of the code its `code_refs` point at —
names and literals folded, so it tracks *structure*, not text.

```bash
$ fux seal --all
✔ sealed day-pnl, holdings-sum-equals-total, inr-normalization, portfolio-valuation
```

Now `fux check` recomputes the fingerprint each run. A whitespace edit, a comment, or a
*rename* does **not** break the seal; a flipped comparison or an added branch does:

```bash
$ fux check
[unsealed] day-pnl: governed code changed structurally since sealed — review,
           then `fux seal day-pnl` to re-affirm
```

It's **advisory** (never auto-fixed) — a human re-affirms by re-running `fux seal`. This
upgrades drift from "the file's mtime moved" to "the thing I *claimed about* changed."

---

## 8. Quality, health & enforcement

### `fux lint` — does each rule earn its weight?
```bash
$ fux lint
[no-why] capital-gains-equity: no **Why:** in the body — the why is the point
[stub-body] anton-overview: body looks like an unfilled stub
[overlap-unlinked] rule-a: governs the same code as 'rule-b' but they are unlinked…
```

Kinds: `no-why`, `no-code-refs`, `dangling-edge`, `no-provenance`, `stub-body`, and
**`overlap-unlinked`** (two rules over the same code span with no `supersedes:`/
`contradicts:` edge — the "stale knowledge silently lies" guard). Advisory; `--strict`
exits 1.

### `fux stats` — one-glance health score
```bash
$ fux stats
fux stats — health 53/100  (D)  ███████████░░░░░░░░░

Score components
  coverage       4   █░░░░░░░░░░░░░░░░░░░
  verify       100   ████████████████████
  authoring     71   ██████████████░░░░░░

Signals
  coverage:  4%  (49 important file(s) uncovered)
  verify:    skip 1, pass 2
  drift:     none   (blocking: 0)
  lint:      no-why 2, stub-body 4, overlap-unlinked 1
  savings:   ~5.5× cheaper per documented lookup
  graph:     1383 nodes · 6800 edges · 161 communities
```

### `fux gate [--install] [--strict-lint]` — CI / pre-commit enforcement
Rebuilds views, then **exit 2** on blocking `check`/`verify` findings (lint advisory
unless `--strict-lint`). `--install` writes a git pre-commit hook. The Stop hook catches
drift mid-session; the gate catches it at commit/CI time.

---

## 9. Cost: `fux savings` + the cumulative ledger

This is how Fux *proves* its value instead of asserting it. All `$0`, measured from your
real file sizes with a transparent ≈4-chars/token heuristic applied identically to both
sides — so the **ratio** is the honest signal.

### 9.1 Per-lookup / aggregate estimate
```bash
$ fux savings "how is day P&L computed"
fux savings — token estimate ($0, heuristic ≈4 chars/token)

Corpus
  active rules:        24
  INDEX (Tier-1):           413 tok   ← injected once per session
  avg rule (Tier-2):        280 tok   ← opened only when relevant
  governed code:          2,278 tok across 2 files

Per lookup — "how is day P&L computed"
  matched rules:       day-pnl, portfolio-valuation
  without Fux:          1,291 tok   (read governed file(s))
  with Fux (1st):         693 tok   → 1.9× cheaper
  with Fux (later):       280 tok   → 4.6× cheaper (INDEX already in context)

Across 4 documented topic(s), per lookup (avg)
  without Fux:          1,538 tok
  with Fux (later):       280 tok   → 5.5× cheaper
```

**Reading it:** *without Fux*, answering means reading the whole governed file(s)
because you don't know the lines; *with Fux*, the rule points you straight there. The
first lookup in a session also pays the INDEX once; later lookups don't (it's already in
context), hence the bigger later-multiplier.

### 9.2 The cumulative cost ledger (track every instance)

A snapshot answers "how much does *this* lookup save?" The **ledger** answers "how much
has Fux saved *in total*, across every lookup?" Turn it on:

```toml
# .fux/config.toml
cost_tracking = true
```

Now **every** `fux recall` records its measured savings into `.fux/cost.json`. The file:

```json
{
  "lookups": 6,
  "tokens_without": 7442,
  "tokens_with": 1571,
  "tokens_saved": 5871,
  "first": "2026-06-05",
  "last": "2026-06-05",
  "recent": [
    { "date": "2026-06-05", "query": "day pnl",
      "served": ["portfolio-valuation", "anton-overview"],
      "without": 1291, "with": 263, "saved": 1028 }
  ]
}
```

- **`tokens_without`** — cumulative cost of reading the governed source file(s) for the
  matched rules.
- **`tokens_with`** — cumulative cost of the matched Tier-2 rule(s) only (the realistic
  *later-lookup* cost; the INDEX is injected once per session, not per lookup).
- **`tokens_saved`** = `without − with`, summed over every lookup.
- **`recent`** — the last 50 lookups (query + which rules served + per-lookup numbers).

`fux savings` then prints a cumulative block automatically:

```bash
$ fux savings
…(the per-lookup/aggregate sections above)…

Cumulative (tracked across 6 lookup(s) since 2026-06-05)
  tokens without Fux:       7,442 tok
  tokens with Fux:          1,571 tok
  tokens saved:             5,871 tok   → 4.7× overall
```

Clear the ledger any time:

```bash
$ fux savings --reset
✔ cost ledger cleared
```

**Honesty guard:** only **code-bound** matches count toward the ledger — exactly like the
aggregate "topics" restriction. A matched `narrative`/`glossary` with no governed file
would otherwise charge its whole body to `with` against a `without` of `0`, making
"savings" negative and meaningless. So the running multiplier stays trustworthy.

`.fux/cost.json` (and `.fux/usage.json`) are **gitignored** by `fux init` — they're
machine-local runtime ledgers, not shared state.

---

## 10. Cross-session memory

Fux keeps memory **authored, not captured** — it never auto-summarises a session.

- **`fux capture [--list] [--clear]`** — when `capture = true`, the Stop hook records
  *which* important files changed (governed vs uncovered), with a secret-path filter and
  SHA-256 dedup, into a queue. The `fux-distill` skill (human-confirmed) turns the queue
  into durable `memory`/`adr` entries. Never auto-authors.
- **Governance / decay** — `type: memory` entries decay after `memory_ttl_days` (default
  180): `fux check` emits `memory-stale` and `fux context` excludes them from injection
  (kept on disk). **Rules never decay.**
- **Usage-weighted decay** — with `usage_tracking = true`, each `recall`/`why` records
  served ids in `.fux/usage.json`; a memory *served* within the TTL window stays alive,
  an unused one decays — a signal time-only TTL misses.

---

## 11. Mining candidate rules

```bash
$ fux mine
# Mined candidates (81) — drafts only, confirm before authoring
## magic numbers
- **86400** (12×) — name it as a `convention`? sites: app/scheduler.py:14, app/jobs.py:7 …
```

Authored-only knowledge bases die of cold-start. `fux mine` is a deterministic first pass
that **points at knowledge already latent in the code** (first miner: magic numbers
repeated across ≥N sites) as **draft candidates** — never auto-authored, the same
discipline as capture → distill.

---

## 12. Agent integration & dashboard

- **`fux mcp`** — a stdlib-only MCP server over stdio. Publishes the read paths as tools:
  `fux_recall` / `fux_why` / `fux_refs` / `fux_coverage` / `fux_savings` / `fux_stats` /
  `fux_context` + graph `fux_query` / `fux_trace` + draft-only `fux_new`. Register with
  `claude mcp add fux -- fux mcp`.
- **`fux serve [--port N]`** — a local `http.server` dashboard: the `stats` health summary
  + links to `graph.html` and the reports.

---

## 13. Migration & decommission

For absorbing what a project already runs separately (a code-graph tool, docs, scattered memory):

- **`fux import <path…>`** — ingest existing markdown as `narrative` entries (frontmatter
  stamped, body preserved). The one-pass `docs/` migration.
- **`fux import-memory [--scope]`** — mirror Claude's home-dir `memory/*.md` into
  `.fux/memory/<scope>/`.
- **`fux tour`** — emit an ordered `ONBOARDING.md` reading path from the rules.

---

## 14. The always-on loop (hooks)

`fux init` wires three hooks so the substrate stays live without you thinking about it:

| Event | Does |
|---|---|
| **SessionStart** | inject the Tier-1 INDEX (`fux context`) |
| **PostToolUse** (Edit\|Write) | remind you when an edited file's rule drifted (`fux hook-touch`) |
| **Stop** | validate before the turn ends (`fux hook-check`); in `fix` mode, emit a scoped edit prompt with the actual `git diff` of changed `code_refs` |

Opt-in extras: **UserPromptSubmit** recall (`fux init --recall`) and the **capture** Stop
hook (`capture = true`). Strictness modes: `off` / `warn` / `fix` (default) / `strict`.

---

## 15. Layered rules (maintain once, inherit everywhere)

```
effective ruleset = ~/.claude/fux/global/   (cross-project best practices)
                  ⊕ ~/.claude/fux/packs/*    (opt-in shareable domain packs)
                  ⊕ ./.fux/rules/            (this project's domain rules)
```

`project` overrides `pack` overrides `global`; `fux check` flags conflicts (same `id` or
explicit `contradicts:`) instead of silently shadowing.

---

## 16. Config reference (`.fux/config.toml`)

| Key | Default | Effect |
|---|---|---|
| `mode` | `fix` | enforcement strictness: `off`/`warn`/`fix`/`strict` |
| `packs` | `[]` | opt-in domain packs from `~/.claude/fux/packs/` |
| `use_global` | `true` | inherit `~/.claude/fux/global/` |
| `important_globs` | py/ts/tsx/go/rs | files `fux coverage` expects to be governed |
| `graph_globs` | broad code set | files `fux build` graphs (broader than coverage) |
| `ignore_globs` | node_modules/.venv/… | excluded everywhere (add `**/.next/**`, `**/*.min.js`) |
| `recall_rerank` | `false` | opt-in local embedding re-rank |
| `recall_hybrid` | `false` | opt-in RRF fusion (lexical⊕semantic⊕graph) |
| `recall_expand` | `false` | opt-in query expansion (glossary + 1-hop graph) |
| `capture` | `false` | opt-in Stop-hook session capture for `distill` |
| `memory_ttl_days` | `180` | `type: memory` decay window |
| `usage_tracking` | `false` | record served rules → usage-weighted decay |
| `cost_tracking` | `false` | accumulate each lookup's savings → `.fux/cost.json` |
| `context_budget_tokens` | `0` | `>0` ⇒ knapsack-pack the SessionStart INDEX |

---

## 17. The `$0` guarantee

Every maintenance command is shell / AST / parse — **no LLM calls, no network**. The only
paths that call the LLM are the `plan` / `adr` / `distill` skills, and they ride the
session you're already in (no background spend). Graph extraction, recall, check/fix,
verify, seals, mining, savings, and the cost ledger are all deterministic and
reproducible. The same "$0, deterministic" promise end to end.
