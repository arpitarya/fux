---
type: Proposal
title: Cross-model agent guides — branch on what can be checked, never on who the model thinks it is
description: fux's shipped skills, steering, rules, instructions and agent files load the same on every vendor but do not behave the same on every model; proposes deterministic levers instead of an in-file "if you are model X" branch.
status: proposed
timestamp: 2026-09-28T12:50:00+05:30
---

# Cross-model agent guides

**Arpit's ask (2026-09-28, Cowork):** *will the skills work for all kinds of
models — Sonnet, Opus, GPT — in a similar manner? If not, should the script
define criteria: "if you are a model with XYZ parameters, look into this,
otherwise into this"?* Scope confirmed as **the whole agent-facing set** —
skills, steering, rules, instructions and agent files
([SR-AGENT-SURFACES](../../records/0155_agent-surfaces.md)).

**Short answer: no, not in a similar manner — and an in-file model branch is
the wrong fix.** This file argues both halves and parks five levers that
are deterministic and checkable.

## 1 · What is the same on every model

- **Delivery.** `fux setup` renders every guide per vendor surface (Claude,
  Codex, Copilot, Kiro) from `src/fux/templates/agents/`. Which file lands
  where does not depend on the model.
- **The engine side.** CLI verbs, `--json` fields, exit codes and the
  confidence band are identical whatever model reads them.
- **The policy block.** [SR-AGENT-POLICY](../../records/0132_agent-policy.md)'s
  eight rules are asserted byte-equal in every rendering.

## 2 · What is not the same, measured on 2026-09-28

| cause | evidence in this tree | effect |
|---|---|---|
| **Triggering is model judgment** on the `description` alone | 17 skill descriptions, ≤500 chars each | a cross-agent test found Claude most reliable, Codex needing more explicit prompts, Copilot the most conservative |
| **Body length** | skills are **4.8–19.4 KB** each; `SEARCH-SKILL.md` 19 365 B, `FETCHER-SKILL.md` 16 551 B | small models (Haiku, GPT "mini") drop rules that sit deep in the file |
| **Emphasis** | **34 🔴 markers** across the skills (SEARCH 5, FETCHER 6, ENRICH 5), plus caps NEVER/ONLY/MUST | Anthropic's guidance: newer Claude models *overtrigger* on aggressive emphasis; older or smaller models may need it — the same text pulls two directions |
| **Judgment-heavy jobs** | `ENRICH-SKILL.md` (*"You are the model"*), `--expand` passage authoring (SEARCH §5a), stance choice (POLICY) | output quality varies by model; nothing in fux grades it except where a check exists |
| **Pins disagree** | `subagent-fux-researcher.md` `model: sonnet` · `kiro-agent-fux-researcher.md` `model: auto` · Codex/Copilot researcher: no pin | the "same" researcher is a different model on each vendor, chosen by nobody on purpose |

## 3 · Why not "if you are model X, do this"

- **A model cannot reliably tell which model it is.** Routers, `model: auto`,
  fallbacks and identity-withholding harnesses all hide it; parameter counts
  are not published for any of them.
- **It is a probabilistic self-report branch** — untestable, and against the
  determinism the project is built on. A test cannot assert which branch a
  model took.
- **Every model still reads every branch.** More tokens and more confusion,
  landing hardest on the weakest model — the one the branch was for.
- **It rots.** Model names change quarterly; a table of them in a shipped
  guide is a restatement of a vendor's catalogue, stale on release.

## 4 · The proposal — five levers, in order

**A · Measure first (graduates this proposal).** A skill-eval matrix in
**fux-lab** (never fux-playground): a fixed prompt set × {Sonnet, Opus,
Haiku, a GPT via Codex, Copilot}. Two scores per cell:
- **trigger hit-rate** — did the right skill load, and did no wrong one;
- **rule compliance** — deterministic checks on the transcript, e.g. never
  ran `fux correct` / `fux setup` / a committed write unasked; branched on
  `"archived": true`, not prose; passed `--band` before acting.
Transcripts are use records → gitignored only. Without A, B–E are guesses.

**B · Choose the model at setup, not at read time.** Every agent file whose
vendor supports a `model` field gets one, read from a **consumer TOML key**
(the values-in-config law — no pin hard-coded in a template). One key per
vendor surface; a missing key is the hard error that law requires.

**C · Core-first skill shape.** Each skill opens with a **core procedure
≤ ~2 KB** — the commands, the must-not list, when to stop — and everything
else below a single `## Reference` line. Weak models act on the core; strong
models read on. **Same file for every model**; the byte cap is gated in
`tests/test_setup_agents_guides.py` the same way pointer size already is.

**D · De-shout.** Replace 🔴 / caps with a plain imperative plus its reason
("Don't run `fux correct` unasked — it writes committed files"). **The
POLICY verbatim block is untouched.** Lever A decides whether any 🔴 earns
its place back on the models that need it.

**E · Branch on observable facts only.** Where a guide must branch, it
branches on something the agent can check: *shell unavailable → use MCP*,
*`band` is `none` → retry ladder*, *`fux enrich --check` fails → fix before
commit*. Judgment output is then graded by fux, not trusted — model quality
shows up as a pass or a fail.

## 5 · What this proposal is not

- **Not a per-model file set.** One template per guide, as today.
- **Not a model in any fux path.** Everything here is the guides and the
  lab; the engine is untouched.
- **Not a golden-set claim.** The eval prompts are their own fixture, never
  golden questions, and carry no benchmark number.

## 6 · Forks for Arpit

1. **Which models are in the matrix** — and which GPT, since Codex routes
   its own.
2. **Pin or leave `auto`** where a vendor offers `auto` (Kiro) — a pin is
   reproducible, `auto` is what the consumer's plan allows.
3. **C's cap** — 2 KB is a guess; A should set it.
4. **Where the prompt fixture lives** — `tests_e2e/` (runs in CI, needs a
   model: cannot) vs `tools/` (run by hand in fux-lab).

## 7 · Graduation trigger

**Graduates when a consumer — or this repo — files a skill mis-trigger or a
rule broken on a non-Claude or smaller model**, or when Arpit asks for the
lever-A matrix. It then becomes a compare doc for fork 2 and a work item for
A; B–E follow A's numbers.

## References

- [SR-AGENT-SURFACES](../../records/0155_agent-surfaces.md) — the surfaces
  and which carry a `model` field.
- [SR-AGENT-POLICY](../../records/0132_agent-policy.md) — the verbatim block
  lever D must not touch.
- `src/fux/templates/agents/` — the byte and marker counts in §2 (measured
  2026-09-28 with `wc -c` and `grep -c`).
- External: *SKILL.md Cross-Agent Compatibility: Tested Across 6 Agents*
  (agensi.io); Anthropic, *Prompting best practices* (platform.claude.com),
  on overtriggering from aggressive language; VS Code, *Use Agent Skills*.
