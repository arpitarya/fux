<img src="fux/assets/fux-lockup.svg" alt="Fux — Alpha Forge Knowledge Index" width="360" />

# Fux

> **Fux records *why* your code is the way it is — and checks it's still true.**
> A portable, agent-aware knowledge engine: one frontmatter substrate → derived
> **index**, **graph**, and **memory** views. `$0` and deterministic — zero
> third-party deps, no mandatory LLM calls. Author each rule once; your agent
> reads a cheap one-line index first and opens the full rule only when it's
> relevant — and `fux seal` lets `fux check` tell you when the governed code
> drifted out from under it.

> **New in v0.5.0 — advisory-first critic + the first constitutional amendment.** The judgment
> critic now **suggests, not blocks**, by default (only deterministic money/PII/audit invariants
> block — escalate a trusted judgment principle with `critic_block_judgment`); **`fux constitution`**
> gains recent debates + violations grouped by severity; and the amendment article itself was
> amended **by supersession** (`con-amendment` → `con-amendment-v2`, adding the "is this
> constitutional?" authoring test) — the rule proving it binds its own author.
>
> **v0.4.0 — the constitutional-app engine.** Govern where trust lives, opt-in and
> `$0`: give a rule a `tier` (`constitutional` · `standard` · `advisory`); author principles
> by two-agent **`/fux debate`**; **`fux ratify`** a rule into a tamper-evident constitution
> (sealed in **`.fux/constitution.lock`** — any later edit/add/delete is an always-blocking
> `tampered` finding); critique changes against the constitution with **`fux critic`** before
> they land (deterministic pass first, no LLM); and **`fux gate`** reports every ungoverned
> path (report-first, never blocks). The AI self-critique ships behind an opt-in **`[critic]`**
> extra — the default install stays model-free. Adopting it changes nothing until you opt in.

<!-- launch: replace the line below with the demo GIF — `fux why day-pnl` → rule + why +
     governed code, then the Solar Terminal graph igniting the `governs` links.
     Storyboard + capture script: docs/launch/gif-storyboard.md -->
<p align="center"><em>▶ demo GIF goes here — see <a href="docs/launch/gif-storyboard.md">docs/launch/gif-storyboard.md</a></em></p>

**Pronounced "fox."** (Say it like the animal — *fux* → *fox*.)

Named after *Johann Joseph Fux*, author of *Gradus ad Parnassum* (1725) — the
counterpoint treatise every composer learned the rules from. A tool that codifies
and enforces rules, named after the man who wrote *the* rulebook. (The name is
deliberate.) Sits beside `wagner`, `bach`, `orff`.

Fux **unifies and replaces** three things a project usually runs separately — the
structural graph (graphify), cross-session memory, and the narrative docs — and
adds the **business-rules layer** none of them held. See [docs/fux-plan.md](docs/fux-plan.md).

## In plain words (the 5-year-old version)

Think of your code as a big LEGO city. The *reasons* things are built a certain
way — why the bridge is red, why you add the towers before the walls — usually
live only in one builder's head. When they go home, nobody remembers why.

**Fux is a notebook for those reasons.** You write each important rule down once —
*what* it is and *why* — and Fux sticks a tiny one-line list on the cover so your
helper can flip straight to the right page instead of searching the whole city
every time. Fux also **draws a map** showing which notes belong to which
buildings, and **checks** that the notes still match the city — and it does all
of that for free, without phoning anyone for help.

So: write the *why* down once → it's found fast, stays correct, and never gets lost.

## Why

The *why* behind a formula — why current value not invested cost, why
dollar-normalize first, which cost-basis method — usually lives only as an inline
comment, invisible until someone greps for it. Fux makes that knowledge
**first-class**: one entry, authored once, served back through a tiny index (read
first) plus lazily-opened rules (read only when relevant). Lookups run ~5–10×
cheaper and more correct on every later session — and you don't have to take that
on faith: **`fux savings`** measures the multiplier from your own file sizes and
prices the win in **real dollars** (configurable `usd_per_mtok`, default = Claude
Opus 4.8's $5/M input rate), per lookup and as a cumulative ledger.

## Install

```bash
git clone git@github.com:arpitarya/fux.git && cd fux
./install.sh          # → ~/.claude/fux + Claude skills + ~/.codex/skills/fux*
fux --version
```

Requires Python ≥ 3.11 (stdlib only — zero third-party dependencies).

## Use

```bash
cd your-project
fux init                       # scaffold .fux/ + Claude/Codex/Copilot pointers
fux new formula day-pnl        # scaffold a rule; fill **Rule:/Why:/Edge cases:**
fux build                      # regenerate INDEX.md + rules.json + graph   ($0)
fux check --fix                # validate; repair mechanical drift           ($0)
fux why day-pnl [--history]    # explain a rule (+ how its *why* evolved, via git)
fux refs src/aggregator.py     # which rules govern this file
fux recall "how is day P&L computed" --hybrid  # BM25F; RRF-fuse lexical+semantic+graph
fux seal --all                 # bind rules to an AST fingerprint of their code
fux debate "<rule>" (skill)    # two-agent free debate → you ratify the result
fux ratify <id> --by Arpit     # ratify a constitutional rule (tamper-evident; the only path)
fux constitution               # status view: what's law, what it governs, recent debates, violations by severity
fux critic "<change>"          # critique a change vs principles before it lands (deterministic pass; $0)
fux coverage                   # % of important files with a governing rule
fux verify --fuzz              # run invariant `check:`; boundary-fuzz for div-by-zero
fux mine                       # surface candidate rules latent in the code (drafts)
fux savings "how is day P&L computed"  # measured token + dollar cost win (+ cumulative ledger)
fux lint                       # rule *quality*: missing why / code_refs / edges
fux stats                      # knowledge-health dashboard + score
fux gate --install             # wire a git pre-commit enforcement hook
fux mcp                        # serve the substrate to agents over MCP (stdio)
fux capture                    # queue this session's changes for `fux distill`
fux serve                      # local dashboard over the generated views
fux import docs/               # migrate existing markdown → narrative entries
fux parity                     # is it safe to retire the old graph/docs/memory?
fux tour                       # ordered ONBOARDING.md

# Runtime consumers (agents + apps, e.g. Anton's Orff concierge)
fux components [--scope dir]   # component/hook registry for on-the-fly UI generation
fux validate-spec              # validate a declarative UISpec against the registry
fux feedback                   # record rejected specs as candidate vocabulary gaps
fux hook-recall                # stdin-JSON recall for agent prompt hooks
fux query / path / explain     # graph traversal: cross-module "how does X relate to Y"
```

**Complete, example-driven guide to everything Fux does:
[docs/guide.md](docs/guide.md).** Full command reference: [docs/cli.md](docs/cli.md).
Authoring a rule: [docs/rule.guide.md](docs/rule.guide.md). Writing a spec:
[docs/spec.guide.md](docs/spec.guide.md).

## How it works

```
Tier 0  agent pointers ............ CLAUDE.md, AGENTS.md, Copilot instructions
Tier 1  .fux/out/INDEX.md ........ ~1 line/rule, read FIRST        ← cheap
Tier 2  .fux/rules/<id>.md ....... opened ONLY when relevant       ← lazy
Tier 3  .fux/out/{rules,graph}.json  machine lookup + browsing
```

You maintain **only** the source frontmatter. INDEX, `rules.json`, and the
interactive `graph.html` regenerate on `fux build`. Three hooks keep it live:
SessionStart injects the INDEX, PostToolUse reminds you when an edited file's rule
drifted, Stop validates before the turn ends.

The **graph** merges your rules with code symbols and call edges extracted across
**Python** (via the stdlib `ast`) and **JS/TS, Go, and Rust** (a brace-matched
heuristic by default, or **real tree-sitter ASTs** with the optional
`pip install fux-engine[ast]` extra — same schema, more accuracy, still $0 by
default), now including **cross-file** `calls` (symbol→symbol) — one navigable
map of *which rule governs which code*, with community clustering, **PageRank
centrality** (architectural chokepoints, not just raw degree), and a
`GRAPH_REPORT.md`. The interactive `graph.html` is the **"Solar Terminal"** viewer,
built for review *and* agents: code desaturates to graphite dust while knowledge
nodes ignite amber and the rare `governs` links stream across as glowing threads,
so *which rule governs which code* is impossible to miss. A three-rail layout adds
a search-with-clickable-hits Lens grid, per-type filter meters, a live minimap, a
**governance ledger** of every knowledge→code link, semantic-zoom community
super-nodes, BFS path mode, and one-click **markdown export** of a node's
neighbourhood, the visible sub-graph, or the governed subgraph.

`fux recall` is lexical **BM25F** (`$0`) by default, with opt-in **query expansion**
(glossary synonyms + 1-hop graph neighbours), an opt-in **local** re-rank, and an
opt-in **RRF hybrid** that fuses lexical ⊕ local-semantic ⊕ graph proximity (no
API); `fux verify [--fuzz]` runs a rule's invariant `check:` and worked `examples:`,
optionally boundary-fuzzing for unguarded div-by-zero. **Proof-carrying rules:**
`fux seal` binds a rule to a normalized-AST fingerprint of its code, so `fux check`
flags `unsealed` when the governed code changes *structure* (not just its mtime).
Beyond authoring, Fux **enforces and reports**: `fux lint` grades rule quality,
`fux stats` scores knowledge health, `fux gate` blocks drift at commit/CI time,
and `fux mcp` exposes the whole substrate to agents over MCP.

**Constitutional tier (opt-in):** a rule's `tier` (`constitutional` · `standard` ·
`advisory`) sets how hard it bites — constitutional rules block in any mode. A principle
*becomes* law through `/fux debate "<rule>"` — a skill that spawns **two sub-agents** (no
assigned sides, blind first passes, anti-sycophancy gates) and escalates to **you** as
tie-breaker — then `fux ratify` makes it tamper-evident: it stamps a `content_seal` (and the
debate's `debate_hash`) and records the rule in a committed `.fux/constitution.lock`, so any
in-place edit, add, or delete becomes an always-blocking `tampered` finding. The debate is
the *host session's* tokens; Fux's own code never calls an LLM (a guard test proves the
maintenance path is model-free). All deterministic and `$0`. Default behaviour is unchanged
until you ratify (`tier` defaults to `standard`).

Each principle is tagged `enforcement: deterministic` (money/PII/numbers — decided by a
`check:`/seal, **never** sent to the AI critic) or `judgment` (tone/completeness — decided
by AI self-critique, **never** faked as a machine check); the split is enforced structurally
by a `$0` router, and `fux check` flags untagged rules that look like principles so backfill
is guided, not guessed.

At the action boundary (PreToolUse / pre-commit), `fux critic "<change>"` runs the
**deterministic pass first** (hard-invariant fails block, no LLM), then the host agent
self-critiques the `judgment` principles with its own tokens (the `critic` skill drives the
bounded revise / escalate / `/fux debate` loop); verdicts land in `.fux/out/critic.jsonl`,
and `fux gate` reports any ungoverned `important_globs` path (report-first, never blocks).
The judgment critic is **advisory-first**: a judgment fail is a *suggestion*, not a blocker,
so it earns trust before it interrupts — only deterministic hard-invariants block by default,
and you escalate a trusted judgment principle to blocking with `critic_block_judgment` in
`.fux/config.toml`. A headless AI critic for no-session/runtime use ships behind an opt-in
`[critic]` extra (mirroring `[embeddings]`) — the default install stays model-free.

For cross-session memory it stays **authored, not captured**: an opt-in `capture`
hook queues *which* files changed for `fux distill` (human-confirmed) rather than
auto-summarising, and `type: memory` entries **decay** after a TTL so stale notes
stop costing context — with opt-in **usage-weighted decay** (a memory still being
recalled stays alive; an unused one decays). Every path `$0` and deterministic.

### Layered rules (maintain once, inherit everywhere)

```
effective ruleset = ~/.claude/fux/global/   (cross-project best practices)
                  ⊕ ~/.claude/fux/packs/*    (opt-in shareable domain packs)
                  ⊕ ./.fux/rules/            (this project's domain rules)
```

`project` overrides `pack` overrides `global`. `fux check` flags conflicts
instead of silently shadowing.

> Packs are optional. A single-project setup can keep `packs = []` and hold all
> authored knowledge in the repo's own `.fux/` — version-controlled with the code
> it governs (see Anton's `knowledge-location` rule for the reasoning). Global
> rules are seeded from this repo's `fux/data/global/`, so they stay versioned
> tool code, not loose documents.

## Guarantee

Every maintenance command is shell/AST/parse — **no LLM calls**. The only paths
that call the LLM are the `plan` / `adr` skills, and they ride the session you are
already in (no background spend). The same "$0, deterministic" promise that made
graphify trustworthy.

## License

MIT — see [LICENSE](LICENSE).
