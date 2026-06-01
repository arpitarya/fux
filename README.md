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

## Why

The *why* behind a formula — why current value not invested cost, why
INR-normalize first, which cost-basis method — usually lives only as an inline
comment, invisible until someone greps for it. Fux makes that knowledge
**first-class**: one entry, authored once, served back through a tiny index (read
first) plus lazily-opened rules (read only when relevant). Lookups run ~5–10×
cheaper and more correct on every later session.

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
fux why day-pnl                # explain a rule + rationale + linked code
fux refs src/aggregator.py     # which rules govern this file
fux recall "how is day P&L computed"   # keyword-retrieve relevant rules
fux coverage                   # % of important files with a governing rule
fux verify                     # run invariant `check:` assertions
fux tour                       # ordered ONBOARDING.md
```

Full command reference: [docs/cli.md](docs/cli.md). Authoring a rule:
[docs/rule.guide.md](docs/rule.guide.md). Writing a spec: [docs/spec.guide.md](docs/spec.guide.md).

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
