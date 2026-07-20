---
name: fux
description: "portable agent-aware knowledge engine — rules, memory, narrative & graph in one frontmatter substrate; $0 deterministic maintenance"
---

# /fux

Fux unifies three things agent-assisted projects usually run separately — the structural
code graph, cross-session memory, and the narrative docs — and adds the
**business-rules layer** none of them held. One frontmatter substrate in `.fux/`,
with derived **INDEX**, **graph**, and **memory** views. Continuously referenced,
cheaply maintained: every maintenance path is shell/AST/parse — **no LLM calls**.

## Usage

```
/fux                       # in an initialised project: build + report drift
/fux init                  # scaffold .fux/ footprint + agent pointers
/fux build                 # regenerate INDEX.md + rules.json + graph        ($0)
/fux check [--fix]         # validate schema/refs/staleness/conflicts; --fix repairs ($0)
/fux recall "<question>"   # keyword-retrieve the rules relevant to a question ($0)
/fux how "<question>"      # fux explains fux: a question → the exact command  ($0)
/fux why <id>              # explain a rule + rationale + linked code         ($0)
/fux refs <file>           # reverse lookup: which rules govern this file      ($0)
/fux new <type> <id>       # scaffold a rule from a template                   ($0)
/fux coverage              # % of important code files with a governing rule   ($0)
/fux verify                # run invariant/example checks                      ($0)
/fux lint                  # rule *quality*: missing why / code_refs / edges   ($0)
/fux stats                 # knowledge-health dashboard + score                ($0)
/fux savings ["<question>"]# measure the token + dollar cost win (real file sizes)($0)
/fux gate [--install]      # CI/pre-commit enforcement (exit 2 on blocking)    ($0)
/fux mcp                   # serve the substrate to agents over MCP (stdio)    ($0)
/fux capture [--list]      # session change-queue for `fux distill`           ($0)
/fux serve                 # local dashboard over the generated views         ($0)
/fux recall "Q" --hybrid   # RRF-fuse lexical + semantic + graph              ($0)
/fux tour                  # emit an ordered ONBOARDING.md                     ($0)
/fux plan "<request>"      # spec → design → tasks, each a durable Fux entry   (skill)
/fux adr "<decision>"      # capture an architecture decision as an `adr`      (skill)
/fux debate "<rule>"       # two-agent free debate → human ratifies a rule     (skill)
/fux ratify <id>           # ratify a constitutional rule (tamper-evident)     ($0)
/fux critic "<change>"     # critique a change vs principles before it lands   (skill)
/fux trace "<feature>"     # walk the graph to explain how a feature spans modules
/fux savings ["<q>"]       # interpret the cost-savings report → next action   (skill)
/fux distill ["<focus>"]   # capture this session's decisions as memory/adr    (skill)
/fux propose-rules [--retro]# agent proposes rules-with-why → drafts you ratify (skill)
/fux candidates [accept|reject <id>]# triage the proposed-rule review surface   ($0)
/fux fetch-rules <source>  # fetch URL/PDF/txt → extract durable rule entries  (skill)
/fux ingest <url|file>     # agent extracts URL/PDF/Excel/TXT/image → drafts   (skill)
```

## What Fux is for

Reach for Fux when a project's *knowledge* — business rules, the *why* behind a
formula, conventions, cross-session memory, narrative docs, and the code graph —
keeps getting re-derived from scratch each session. Fux writes each fact **once**
as a frontmatter entry and serves it back through a tiny index (read first) plus
lazily-opened rules (read only when relevant), at ~5–10× cheaper lookups.

Three things it does that ad-hoc docs cannot:
1. **One substrate, many views** — the same files are rules, memory, narrative,
   and graph nodes. Edit the source; INDEX / `rules.json` / `graph.html`
   regenerate. Never maintain two copies.
2. **Drift is caught, not discovered** — `fux check` flags dead `code_refs`,
   stale rules (git-aware), and conflicts; `fux verify` runs invariant `check:`
   assertions so a rule that drifts from code **fails**, not just warns.
3. **Layered best practices** — `~/.claude/fux/global/` holds cross-project
   conventions; edit once, every linked project inherits.

## What You Must Do When Invoked

If no argument was given and the cwd is inside a `.fux/` project, treat it as
`/fux build` followed by a drift summary. Do not ask the user for a path.

Follow these steps in order.

### Step 1 — Ensure the engine is installed

```bash
# Resolve a 3.11+ interpreter (tomllib); prefer an installed `fux` binary.
if command -v fux >/dev/null 2>&1; then FUX="fux"; else
  PY="$(command -v python3.14 || command -v python3.13 || command -v python3.12 || command -v python3.11 || command -v python3)"
  "$PY" -c "import fux" 2>/dev/null || "$PY" -m pip install -q --user ~/.claude/fux/engine 2>/dev/null || true
  FUX="$PY -m fux"
fi
$FUX --version || { echo "Fux engine not installed — run install.sh from the fux repo"; exit 1; }
```

If `fux --version` prints, move on. **In every later command, use `$FUX`.**

### Step 2 — Initialise if needed

```bash
# If there is no .fux/ at or above cwd, scaffold one.
$FUX context >/dev/null 2>&1 || $FUX init
```

`fux init` is idempotent: it creates `.fux/{rules,glossary,memory,out}`, writes
`.fux/config.toml` (strictness `fix` by default), wires the 3 core hooks into
`.claude/settings.json`, and drops a Tier-0 pointer into `AGENTS.md`.

### Step 3 — Dispatch the subcommand

| Invocation | Run |
|---|---|
| `/fux` or `/fux build` | `$FUX build` then `$FUX check` and summarise drift |
| `/fux check [--fix]` | `$FUX check [--fix]` |
| `/fux recall "Q"` | `$FUX recall "Q"` — open the top rule(s) with `$FUX why <id>` |
| `/fux how "Q"` | `$FUX how "Q"` — fux explains fux: the right command + a one-line why |
| `/fux why <id>` | `$FUX why <id>` |
| `/fux refs <file>` | `$FUX refs <file>` |
| `/fux new <type> <id>` | `$FUX new <type> <id>` then open the stub and fill the body |
| `/fux coverage` | `$FUX coverage` |
| `/fux verify` | `$FUX verify` |
| `/fux lint` | `$FUX lint` — fix `no-why` / `no-code-refs` before finishing |
| `/fux stats` | `$FUX stats` — summarise the health score + weakest signal |
| `/fux savings ["Q"]` | `$FUX savings ["Q"]` — or follow `skills/savings/SKILL.md` |
| `/fux gate [--install]` | `$FUX gate` (CI) or `$FUX gate --install` (git pre-commit) |
| `/fux mcp` | `$FUX mcp` — run the MCP stdio server (registered via `claude mcp add`) |
| `/fux capture` | `$FUX capture --list` — seed for `/fux distill` |
| `/fux serve` | `$FUX serve` — open the local dashboard |
| `/fux tour` | `$FUX tour` then read `.fux/out/ONBOARDING.md` |
| `/fux plan "<request>"` | follow `skills/plan/SKILL.md` |
| `/fux adr "<decision>"` | follow `skills/adr/SKILL.md` |
| `/fux debate "<rule>"` | follow `skills/debate/SKILL.md` (two-agent debate → human ratifies) |
| `/fux ratify <id>` | `$FUX ratify <id> --by "<name>" [--debate <transcript>]` |
| `/fux critic "<change>"` | follow `skills/critic/SKILL.md` (deterministic pass → self-critique → revise) |
| `/fux trace "<feature>"` | follow `skills/trace/SKILL.md` |
| `/fux distill ["focus"]` | follow `skills/distill/SKILL.md` |
| `/fux propose-rules [--retro]` | follow `skills/propose-rules/SKILL.md` (forward: agent drafts-with-why → `$FUX propose-rules --from`; retro: `$FUX propose-rules --retro`) |
| `/fux candidates [accept\|reject <id>]` | `$FUX candidates` to triage; `accept` → active rule, `reject` → drop (never auto-active) |
| `/fux fetch-rules <src>` | follow `skills/fetch-rules/SKILL.md` |
| `/fux ingest <url\|file>` | follow `skills/ingest/SKILL.md` (agent extracts → drafts; never auto-active) |

### Step 4 — When you author or edit a rule

After `fux new`, **fill the body** (`**Rule:**` / `**Why:**` / `**Edge cases:**`)
and set real `code_refs` to the lines the rule governs (`path#Lstart-Lend`). Then
run `$FUX build`. A rule without a `**Why:**` is half a rule — the *why* is the
whole point (plan §1).

### Step 5 — Reading knowledge (cheap path)

Before grepping the codebase to answer "how/why does X work", read
`.fux/out/INDEX.md` first, then open only the relevant rule via `$FUX why <id>`
or retrieve with `$FUX recall "<question>"`. This is the token-cost win — don't
re-scan files for knowledge a rule already holds.

## Rule types (plan §6)

`rule` · `formula` · `glossary` · `invariant` · `adr` · `edge-case` ·
`convention` · `regulatory` · `runbook` · `narrative` · `memory` · `spec` ·
`task`. `narrative`/`memory` are exempt from atomic sizing; `memory` carries a
`subtype` (`user`/`feedback`/`project`/`reference`) and a `scope`
(`personal` gitignored / `shared` committed).

## Strictness (per project — `.fux/config.toml`)

`off` (nothing) · `warn` (surface only) · **`fix`** (default — the agent
auto-repairs mechanically-fixable drift in-session; semantic drift becomes a
scoped edit prompt) · `strict` (`exit 2` hard-block on blocking findings — CI
gate).

## Guarantee

Every command above is deterministic and `$0` — a genuine "no API cost"
guarantee. The only paths that call the LLM are the `plan` /
`adr` / `debate` skills, and they ride the session you are already in (no background
spend). `fux ratify` is itself `$0`: it only hashes the debate transcript the skill
captured — the *judgement* was the session's tokens, the *record* is deterministic.
