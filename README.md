<img src="https://raw.githubusercontent.com/arpitarya/fux/main/fux/assets/fux-lockup.png" alt="Fux — Alpha Forge Knowledge Index" width="360" />

# Fux

> **Memory tools record what your agent *did*. Fux records *why* your code is the way it is — and checks it's still true.**

[![PyPI](https://img.shields.io/pypi/v/fux-engine.svg)](https://pypi.org/project/fux-engine/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen.svg)](#the-0-guarantee)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

The *why* behind your code — why this formula, why this invariant, why it was done *this* way — usually lives in someone's head and dies when they leave. Fux makes it a first-class, version-controlled thing your agent reads before it touches anything, and tells you the moment the code drifts away from what you wrote. **`$0`, deterministic, zero dependencies, no mandatory LLM calls.**

**Pronounced "fox."** · Python ≥ 3.11 · stdlib only · MIT

<!-- launch: replace the <p> below with the demo GIF — `fux why day-pnl` → rule + why +
     governed code, then the Solar Terminal graph igniting the `governs` links. -->
<p align="center"><em>▶ Demo GIF coming soon.</em></p>

## The story

> *A story? In a README? I know. But here's a fun fact about the human animal: nobody, in the entire history of the species, was ever moved by a bullet point.* We do badges, a wall of CLI flags, and a "Contributing" section nobody's opened since 2019 — and we call it documentation. You will not remember my feature list. You'll remember the pipe. So I wrote the pipe. Ninety seconds, it's about a basement, and — spoiler — you're the idiot in it. Read it. — *Arpit*

You move into an old house. Down in the basement, the previous owner painted one pipe bright red. You have no idea why — so when you renovate, you treat it like any other pipe and reroute it. A week later, the basement floods. That red pipe froze every winter, and the paint was the owner's way of saying *leave this one alone.* They knew. They just never wrote it down, and then they moved out.

That's how almost all important knowledge works. The *reason* behind a choice lives in one person's head, and the day they leave, it's gone — so the next person changes it with complete confidence, and something quietly breaks. (Swap "person" for "AI assistant" and it happens ten times faster.)

**Fux is the note taped to the red pipe.** You write the reason down once, it stays right next to the thing it explains, and whoever comes next — a new owner, a contractor, an AI — reads it *before* they touch anything. And if someone reroutes the pipe anyway, Fux flips the note over: *heads up — this may no longer match what's actually here.* The reason can't vanish, and it can't quietly go out of date.

In code, the red pipe is the one line some genius is always about to "clean up":

```python
def day_pnl(holding):
    # No, this cannot be one tidy line. Normalize each leg to dollars BEFORE
    # summing — percentages double-count during a corporate action.
    # Yes, you have 15 years of experience. So did the last principal who
    # "simplified" this and took prod down on dividend day. (see: day-pnl)
    return sum(to_usd(leg) for leg in holding.legs)
```

Six months later, a Principal Engineer With Opinions skims that comment, concludes whoever wrote it "didn't really understand the domain," deletes it, and ships the one clean line — right before the next corporate action quietly poisons the numbers. The comment was right. It usually is. (We've all been that engineer.) Fux turns it from a comment a confident person can delete into a rule they *can't* — checked, and bound to the exact lines it explains.

## See it

```bash
$ fux why day-pnl
```

```
formula · day-pnl · governs backend/app/aggregator.py#L40-58

  Rule:  Day P&L = current market value − previous close value, per holding,
         summed. Dollar-normalize each leg before summing.
  Why:   Quantity drifts intraday (corporate actions, partial fills); summing
         percentages double-counts. Dollars are the only safe common unit.
  Edge:  New position with no previous close → previous = cost basis, not 0.

  ⚑ unsealed — aggregator.py changed structure since this rule was sealed.
     The logic this rule describes may no longer match. Run `fux why day-pnl --history`.
```

One entry, authored once, answered back with the rule, the reason, the code it governs, and — the part no doc tool does — **a warning that the code moved and the rule might be stale.** That last line is the whole product.

## Quickstart

```bash
pip install fux-engine        # the CLI, zero third-party deps

cd your-project
fux init                      # scaffold .fux/ + agent pointers
fux new formula day-pnl       # scaffold a rule; fill Rule: / Why: / Edge cases:
fux build                     # regenerate INDEX + graph        ($0)
fux why day-pnl               # explain a rule + the code it governs
fux how "which rules govern a file"   # fux explains fux → the exact command ($0)
```

> **Full agent integration** (Claude Code / Codex / Copilot skills + hooks): clone and run `./install.sh` instead — it wires `~/.claude/fux`, the skills, and the SessionStart/PostToolUse/Stop hooks.

Complete, example-driven guide: [docs/guide.md](docs/guide.md) · full command reference: [docs/cli.md](docs/cli.md).

## Explain it like I'm five

Your code is a giant LEGO city. The *reasons* things are built a certain way — why the bridge is red, why the towers go up before the walls — usually live in one builder's head. When they go home, nobody remembers why.

**Fux is a notebook for those reasons.** You write each important one down once, and Fux glues a tiny one-line table of contents to the cover, so your helper can flip straight to the right page instead of searching the whole city. It also draws a map of which notes belong to which buildings — and checks that the notes still match the city, telling you when a building changed but its note didn't. And it does all that for free, without phoning anyone for help.

## Why it's different

It's not another wiki or memory service. The difference is a set of *properties*, not features:

- **Deterministic.** Every maintenance command is shell / AST / parse. Same inputs, same output, every time — your knowledge layer never hallucinates because it never guesses.
- **Verifiable.** `fux seal` binds a rule to an AST fingerprint of its code; `fux check` tells you when the *structure* drifted (not just the mtime). Rules carry `check:` invariants and worked `examples:` that actually run.
- **`$0` and zero-dependency.** Stdlib-only Python, no third-party deps, no API key required to read, write, or serve. Portable as a tarball, auditable line by line.
- **Agent-native.** Typed frontmatter, machine-readable output, an MCP server, and prompt hooks — built so an agent can call it *and verify the result*, not just read prose.

The "so what" chain: deterministic → so your context never hallucinates → so an agent can act on it safely → so you can put the result in front of an auditor. That last clause is the one a memory tool can't say.

## The constitution — rules neither you nor your agent can break by accident

Ordinary rules document and warn. A **constitutional** rule is one a developer *or* an AI agent cannot break without it being caught and named.

- **Debate → ratify.** A principle becomes law through **`/fux debate`** — a skill that spawns two sub-agents to argue it freely (blind first passes, anti-sycophancy gates, no assigned sides) and escalates to **you** as tie-breaker. **`fux ratify`** then makes it tamper-evident: it stamps a `content_seal` + the debate's `debate_hash` and records the rule in a committed **`.fux/constitution.lock`**, so any later in-place edit, add, or delete is an always-blocking `tampered` finding. To change a constitutional rule you must supersede it — the amendment article governs its own amendment, and has already amended *itself*.
- **Critique before it lands.** **`fux critic`** checks a change against the constitution: a deterministic pass first (money / PII / numbers — decided by a `check:` or seal, *never* sent to an LLM, and they hard-block), then the host agent self-critiques the judgment principles (tone, completeness) with its own tokens. The judgment critic is **advisory-first** — a suggestion, not a blocker — so it earns trust before it interrupts.
- **A real wall.** Every merge to `main` requires two checks — `fux gate` (integrity) and `ai-review` (a *separate reviewer identity* that refuses when reviewer == author). New branch → PR → both green → merge is the only path, for everyone including the owner. Branch protection lives outside the repo, so a weekly drift audit fails loudly if it ever changes. ([details](docs/constitution-enforcement-handoff.md))

Crucially, the debates and critiques spend the *host session's* tokens — **Fux's own code never calls an LLM** (a guard test proves it) — and the whole layer is opt-in: `tier` defaults to `standard`, so adopting Fux changes nothing until you ratify your first rule.

> The bet: once verifiable, governed code-context is normal, shipping an AI change against undocumented, unchecked invariants will look as reckless as deploying without tests.

## How it works

You maintain **only** the source frontmatter. Everything else is derived, lazily, for `$0`:

```
Tier 0  agent pointers ........... CLAUDE.md, AGENTS.md, Copilot instructions
Tier 1  .fux/out/INDEX.md ........ ~1 line/rule, read FIRST        ← cheap
Tier 2  .fux/rules/<id>.md ....... opened ONLY when relevant       ← lazy
Tier 3  .fux/out/{rules,graph}.json  machine lookup + browsing
```

Your agent reads the one-line index first and opens a full rule only when it's relevant, so lookups run **~5–10× cheaper and more correct** on every later session — and you don't take that on faith: `fux savings` prices the win in real dollars from your own file sizes. Three hooks keep it live: SessionStart injects the index, PostToolUse warns when an edited file's rule drifted, Stop validates before the turn ends.

The **graph** merges your rules with code symbols and call edges across **Python** (stdlib `ast`) and **JS/TS, Go, Rust** (brace-heuristic, or real tree-sitter ASTs via the optional `[ast]` extra), with community clustering and **PageRank centrality** for architectural chokepoints. The interactive `graph.html` "Solar Terminal" viewer desaturates code to graphite while knowledge nodes ignite amber and `governs` links stream across as glowing threads — so *which rule governs which code* is impossible to miss. It stays smooth at thousands of nodes (a hand-rolled Barnes–Hut layout, viewport culling, pre-rendered glow), collapses each community into one labelled blob when you zoom out, and a **Coverage** lens warms the governed code so the ungoverned grey is the finding. Rules whose **AST seal has drifted pulse red** and constitutional rules wear a crown — straight from `fux check`, never invented. Still one self-contained offline file, zero dependencies.

<details>
<summary><strong>The full command surface</strong> (authoring · verification · governance · runtime)</summary>

```bash
fux check --fix                # validate; repair mechanical drift           ($0)
fux why day-pnl --history      # how a rule's *why* evolved, via git
fux refs src/aggregator.py     # which rules govern this file
fux recall "how is day P&L computed" --hybrid  # BM25F; RRF-fuse lexical+semantic+graph
fux seal --all                 # bind rules to an AST fingerprint of their code
fux debate "<rule>" (skill)    # two-agent free debate → you ratify the result
fux ratify <id> --by Arpit     # ratify a constitutional rule (tamper-evident)
fux constitution               # status: what's law, what it governs, debates, violations
fux critic "<change>"          # critique a change vs principles before it lands ($0)
fux coverage                   # % of important files with a governing rule
fux verify --fuzz              # run invariant `check:`; boundary-fuzz div-by-zero
fux mine                       # surface candidate rules latent in the code (drafts)
fux propose-rules --retro      # agent proposes rules-with-why → drafts you ratify ($0 retro)
fux candidates accept <id>     # triage .fux/CANDIDATES.md: promote a draft → active rule
fux savings "how is day P&L computed"  # measured token + dollar cost win
fux lint                       # rule quality: missing why / code_refs / edges
fux stats                      # knowledge-health dashboard + score
fux gate --install             # wire a git pre-commit enforcement hook
fux mcp                        # serve the substrate to agents over MCP (stdio)
fux serve                      # local dashboard over the generated views
fux import docs/               # migrate existing markdown → narrative entries
fux query / path / explain     # graph traversal: "how does X relate to Y"
```
</details>

### Layered rules — maintain once, inherit everywhere

```
effective ruleset = ~/.claude/fux/global/   (cross-project best practices)
                  ⊕ ~/.claude/fux/packs/*    (opt-in shareable domain packs)
                  ⊕ ./.fux/rules/            (this project's domain rules)
```

`project` overrides `pack` overrides `global`, and `fux check` flags conflicts instead of silently shadowing. Packs are optional — a single project can keep everything version-controlled in its own `.fux/`, beside the code it governs.

## The `$0` guarantee

Every maintenance command is shell / AST / parse — **no LLM calls, ever.** The only paths that touch a model are the authoring skills (`debate`, `plan`, `adr`, and the judgment critic), and they ride the session you're already in — no background spend. The headless AI critic ships behind an opt-in `[critic]` extra; the default install stays model-free.

**Honest limits.** Fux doesn't write your rules for you — `fux mine` drafts candidates, but the *why* is yours. The constitution governs where trust lives (money, PII, audit), not every line — making everything constitutional would crush your velocity, and the design says so. And branch protection lives in GitHub, so Fux can *watch* it but can't *seal* it; that one link is honest about being outside its reach.

## Editing the agent skills (contributors)

The per-host skill artifacts — the Claude `SKILL.md`, the Codex copy, the Copilot prompt, and the generic `AGENTS.md` target — are **generated**, not hand-authored. Edit the fragments under [tools/skillgen/fragments/](tools/skillgen/fragments/), then run `python -m tools.skillgen` to re-render and `python -m tools.skillgen --bless` to refresh the snapshots. A hand-edit to a rendered file fails `python -m tools.skillgen --check` in CI and pre-commit. Build-time, stdlib-only, never shipped in the wheel — details in [docs/skillgen.md](docs/skillgen.md).

## What's new

**Latest — v0.17.0:** Error-handling hardening — fux gets one CLI error boundary (terse `error: <msg>`, never a raw traceback), a documented exit-code contract (`0` ok · `1` error · `2` blocking · `130` interrupted), and genuinely **fail-open hooks** (a hook error never breaks an agent session; the strict `stop`→`2` is preserved). One thin `FuxError`; every swallowed exception surfaces under `FUX_DEBUG=1` (fail-open ≠ fail-silent). `$0`/stdlib, no behaviour change to checks or views.
Full release history → **[docs/whats-new.md](docs/whats-new.md)**.

## The name

Named after *Johann Joseph Fux*, author of *Gradus ad Parnassum* (1725) — the counterpoint treatise every composer learned the rules from. A tool that codifies and enforces rules, named after the man who wrote *the* rulebook. The name is deliberate (yes, I kept it). Sits beside `wagner`, `bach`, `orff`.

Fux **unifies and replaces** three things a project usually runs separately — the structural graph, cross-session memory, and the narrative docs — and adds the **business-rules and governance layer** none of them held. See [docs/fux-plan.md](docs/fux-plan.md).

---

If the red-pipe problem is real in your codebase, try Fux on one rule — `pip install fux-engine`.

## License

MIT — see [LICENSE](LICENSE).
