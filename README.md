# Fux

> A portable, Claude-aware **knowledge engine**. One frontmatter substrate →
> derived **index**, **graph**, and **memory** views. `$0` deterministic
> maintenance — no mandatory LLM calls. Continuously referenced, cheaply
> maintained.

Named after *Johann Joseph Fux*, author of *Gradus ad Parnassum* (1725) — the
counterpoint treatise every composer learned the rules from. A tool that codifies
and enforces rules, named after the man who wrote *the* rulebook. Sits beside
`wagner`, `bach`, `orff`.

Fux **unifies and replaces** three things a project usually runs separately — the
structural graph (graphify), cross-session memory, and the narrative docs — and
adds the **business-rules layer** none of them held. See [docs/fux-plan.md](docs/fux-plan.md).

## In plain words (the 5-year-old version)

Think of your code as a big LEGO city. The *reasons* things are built a certain
way — why the bridge is red, why you add the towers before the walls — usually
live only in one builder's head. When they go home, nobody remembers why.

**Fux is a notebook for those reasons.** You write each important rule down once —
*what* it is and *why* — and Fux sticks a tiny one-line list on the cover so your
helper (Claude) can flip straight to the right page instead of searching the whole
city every time. Fux also **draws a map** showing which notes belong to which
buildings, and **checks** that the notes still match the city — and it does all of
that for free, without phoning anyone for help.

So: write the *why* down once → it's found fast, stays correct, and never gets lost.

## Why

The *why* behind a formula — why current value not invested cost, why
INR-normalize first, which cost-basis method — usually lives only as an inline
comment, invisible until someone greps for it. Fux makes that knowledge
**first-class**: one entry, authored once, served back through a tiny index (read
first) plus lazily-opened rules (read only when relevant). Lookups run ~5–10×
cheaper and more correct on every later session — and you don't have to take that
on faith: **`fux savings`** measures the multiplier from your own file sizes.

## Install

```bash
git clone git@github.com:arpitarya/fux.git && cd fux
./install.sh          # → ~/.claude/fux/{engine,global,packs,hooks} + /fux skill
fux --version
```

Requires Python ≥ 3.11 (stdlib only — zero third-party dependencies).

## Use

```bash
cd your-project
fux init                       # scaffold .fux/ + wire 3 hooks + CLAUDE.md pointer
fux new formula day-pnl        # scaffold a rule; fill **Rule:/Why:/Edge cases:**
fux build                      # regenerate INDEX.md + rules.json + graph   ($0)
fux check --fix                # validate; repair mechanical drift           ($0)
fux why day-pnl [--history]    # explain a rule (+ how its *why* evolved, via git)
fux refs src/aggregator.py     # which rules govern this file
fux recall "how is day P&L computed" --hybrid  # BM25F; RRF-fuse lexical+semantic+graph
fux seal --all                 # bind rules to an AST fingerprint of their code
fux coverage                   # % of important files with a governing rule
fux verify --fuzz              # run invariant `check:`; boundary-fuzz for div-by-zero
fux mine                       # surface candidate rules latent in the code (drafts)
fux savings "how is day P&L computed"  # measured token-cost win (+ cumulative ledger)
fux lint                       # rule *quality*: missing why / code_refs / edges
fux stats                      # knowledge-health dashboard + score
fux gate --install             # wire a git pre-commit enforcement hook
fux mcp                        # serve the substrate to agents over MCP (stdio)
fux capture                    # queue this session's changes for `fux distill`
fux serve                      # local dashboard over the generated views
fux import docs/               # migrate existing markdown → narrative entries
fux parity                     # is it safe to retire the old graph/docs/memory?
fux tour                       # ordered ONBOARDING.md
```

**Complete, example-driven guide to everything Fux does:
[docs/guide.md](docs/guide.md).** Full command reference: [docs/cli.md](docs/cli.md).
Authoring a rule: [docs/rule.guide.md](docs/rule.guide.md). Writing a spec:
[docs/spec.guide.md](docs/spec.guide.md).

## How it works

```
Tier 0  CLAUDE.md pointer ........ 1 line, always in context
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
`GRAPH_REPORT.md`. The interactive `graph.html` is built for review *and* agents:
node/edge-type filters, colour-by (type/community/layer/degree), focus +
neighbour highlighting, a details panel, and one-click **markdown export** of a
node's neighbourhood or the visible sub-graph.

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

## Guarantee

Every maintenance command is shell/AST/parse — **no LLM calls**. The only paths
that call the LLM are the `plan` / `adr` skills, and they ride the session you are
already in (no background spend). The same "$0, deterministic" promise that made
graphify trustworthy.

## License

MIT — see [LICENSE](LICENSE).
