---
name: fux-distill
description: "turn this session's decisions into durable Fux memory/adr entries — the memory-replacement loop, scoped so it never orphans noise"
trigger: /fux distill
---

# /fux distill — capture what this session decided

Closes the memory-replacement loop (fux-plan.md §11): the durable conclusions of a
working session — a user preference, a settled approach, a "why we did it this way"
— become first-class `memory` / `adr` entries in `.fux/`, versioned and
code-linked, instead of evaporating when the session ends. Scoped deliberately:
**capture decisions, not chatter.**

## Inputs

```
/fux distill                 # review the session and propose entries
/fux distill "<focus>"       # bias toward one thread, e.g. "the caching decision"
```

## What to capture (and what to skip)

**Capture** — durable, reusable knowledge:
- a **preference** the user stated ("always prefer probes over the Playwright MCP") → `memory` (`subtype: user` or `feedback`).
- a **decision with a why** ("we chose avg-cost over FIFO because…") → `adr`.
- a **discovered rule / gotcha** that governs code → `rule` / `edge-case` with `code_refs`.

**Skip** — transient or already-stored:
- step-by-step narration, debugging dead-ends, anything tied to this task only.
- facts already in a rule, in git history, or derivable from the code.
- secrets, tokens, or machine-specific paths.

> Guardrail (plan §16): a distilled entry must be a *durable Fux entry*, never
> orphan markdown. If it isn't worth recalling next month, don't write it.

## Procedure

1. **Resolve `$FUX`** exactly as in `skills/fux/SKILL.md` Step 1.
2. **Read the capture queue (if enabled).** Run `$FUX capture --list` — when
   `capture = true`, the Stop hook has already queued the important files that
   changed this session, split into *uncovered* (candidate new rules) and
   *governed* (a rule's **why** may need updating). Use it as the seed for what to
   distill; combine with what you remember from the session.
3. **Propose first.** List the 1–5 candidate entries — for each: type, a kebab `id`,
   a one-line summary, and (for code-bound ones) the `code_refs`. **Ask the user to
   confirm/trim** before writing. Don't bulk-author.
4. **Scaffold + fill.** For each confirmed item:
   ```bash
   $FUX new memory <id>      # or: $FUX new adr <id> / $FUX new rule <id>
   ```
   Fill the body — `**Observation:** / **Why:** / **How to apply:**` for `memory`,
   `**Decision:** / **Context:** / **Consequences:**` for `adr`. Set `scope:`
   (`personal` gitignored vs `shared` committed) and real `code_refs`.
5. **Link.** Add `related:` / typed `edges:` to neighbouring entries so the new
   knowledge joins the graph rather than floating.
6. **Rebuild, lint, clear.** `$FUX build && $FUX lint` — fix `no-why` /
   `no-code-refs` findings before finishing (a memory without a **Why:** is noise).
   Then `$FUX capture --clear` to empty the queue you just distilled.

## Why a skill, not a hook

Distillation is a *judgement* call — which decisions are durable — so it must stay
human-confirmed and in-session, not fire automatically on Stop. It rides the
session you're already in (no background spend); only the authoring `$FUX new`
calls touch disk, all `$0`.
