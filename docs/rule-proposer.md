# Fux — Rule Proposer (final spec)

**Owner:** Arpit · **Repo:** `fux` · **Driving model:** Claude Code.
**Status:** canonical. Supersedes `rule-proposer-handoff.md` + `rule-proposer-prompt.md` (the execution prompt is §9 below — one self-contained doc).

---

## 0. Why this is worth building (product + trajectory)

**The wedge.** Fux's whole bet is "agents author, humans ratify, everything's sealed." Today the *authoring* is manual — you stop and write rules. The Rule Proposer closes the loop: **the agent that wrote the code proposes the rules-with-why; you only ratify.** That turns fux from "a knowledge tool you maintain" into "a substrate that fills itself and asks permission" — the difference between a tool people *should* use and one that earns its keep on autopilot. It's also the demoable moment that sells the suite: *watch the agent propose, watch the human ratify, watch it get sealed.*

**Where it's heading (signal, not hype).** Every team now ships agent-generated code faster than anyone can document *why*. The why is evaporating at machine speed — the exact problem fux exists for, now arriving 10× faster. In 18 months, "my agent proposes knowledge and I ratify it" will be a primitive serious agent codebases assume. The Proposer is how fux is *early* to that — and the human-ratify gate is the moat (anyone can auto-generate drafts; almost nobody makes them trustworthy).

---

## 0b. MVP first — prove the bet before building the loop (product-builder review)

The full spec (§3–§7) is the *destination*, not the first ship. The whole bet rides on **draft quality** — if the auto-proposed rules are noise, the human-ratify gate becomes an abandoned chore. So prove that *first*, cheaply:

- **MVP (1 week):** just `fux propose-rules --retro` over **one** repo → drafts-with-why appended to `.fux/CANDIDATES.md` → you eyeball them. No SessionEnd hook, no `accept/reject` commands, no queue unification yet.
- **The metric that decides everything — ratify-rate:** of the first ~20 proposed drafts, what fraction would you actually ratify? That single number tells you whether to build the loop.
- **Falsifier:** low ratify-rate ⇒ the gate/why-heuristic is the problem — fix §4's gate, do **not** build the forward hook / triage / unification on top of a junk generator.
- **Strategic role:** the Proposer is the **cold-start killer** (a knowledge substrate nobody fills is dead) and the **adoption wedge for the paid governance/audit layer** — its job is to make the substrate *full*, so the trust layer has something to govern. It is not a revenue line; it is customer acquisition for one.

Build §3–§7 only after the MVP clears a decent ratify-rate on a real repo.

## 1. What it does

Claude **proposes** fux rules automatically — **forward** (as you build) and **retroactively** (over code already shipped) — landing them as drafts in a persistent review surface (`.fux/CANDIDATES.md`) that you triage and ratify. The automation is the *drafting*; the gate stays human.

---

## 2. Non-negotiables (hard lines)

- **Drafts auto · ratification human · constitution NEVER auto.** Every proposal is `status: draft`, `tier: standard` — never active, never constitutional (`con-amendment` forbids auto-constitution; that line is sacred).
- **No recoverable why → no draft.** The value is the *why*. A genuine invariant with no written why may draft with a flagged `why: TODO` (low-trust, sorted last); a pure restatement of code with no invariant and no why is **dropped**.
- **Dedup against existing rules, not just the queue.** Never re-propose something that's already an active rule (match by `code_refs` + content).
- **Agent proposes, fux governs.** Reading diffs, extracting the why, drafting prose = the host agent's tokens (like `/fux distill`). fux's harness — `fux mine` (AST), the candidates surface, dedup — is `$0`/stdlib/deterministic; the engine calls no LLM (guard test).
- Drafts capped per run; the forward hook is **opt-in** (config), never nags. Files ≤100 lines. Docs in the same change.

---

## 3. Two surfaces

**A. Forward — capture as you build (the high-value one).** An opt-in SessionEnd / per-PR pass: the agent reviews the diff **plus its rationale** (PR description, commit message, the session it just had) and proposes candidate rules **with their why**, applying §2. Captures the why *at decision-time, while it's fresh* — which `fux mine` structurally can't.

**B. Retroactive — bootstrap shipped code (one-time, bounded).** A one-shot pass over the existing repos (anton/fux/siblings): `fux mine` surfaces latent invariants from the AST (`$0`), and the agent pulls the why from **git history + PR descriptions** where it exists. Bounded: capped per run, prioritized by why-density, queued for triage.

---

## 4. Flow + the gate

1. **Source candidates** — forward: diff + session/PR rationale; retro: `fux mine` AST drafts + git-history why-extraction.
2. **Quality gate:** is it a *rule* (a non-obvious invariant/convention governing important code) **and** is a why recoverable? If not a rule → drop. If a rule but no why → draft `why: TODO` (flagged). Pure code-restatement → drop.
3. **Dedup** — against the existing rule set *and* the queue (by `code_refs` + content). Skip duplicates.
4. **Draft** — `status: draft`, `tier: standard`, provenance: `source: session|mine|git`, `why_source`, `code_refs` to the governed lines.
5. **Queue** — append to `.fux/CANDIDATES.md` with triage state `pending`; cap per run; sort why-density (drafts-with-why first, `why: TODO` last).
6. **Triage → ratify** — you accept (→ active rule) or reject; constitutional candidates go through `/fux debate` → `fux ratify` (human only).

---

## 5. Where drafts land — `.fux/CANDIDATES.md`, NOT `DRIFT.md`

Two surfaces, two lifecycles, kept separate:

| | `DRIFT.md` | `.fux/CANDIDATES.md` |
|---|---|---|
| Lifecycle | derived, regenerated every `fux check` | **persistent** — survives sessions |
| Nature | corrective ("this drifted, fix it") | generative ("consider this candidate") |
| Gate | **can block** | **never blocks** |
| Holds | drift/dead-ref/conflict findings | drafts awaiting triage + ratify, with `pending\|accepted\|rejected` state |

`.fux/CANDIDATES.md` is the **single review surface** for all drafts — proposed rules + ingested drafts + mined candidates (generalize the ingest queue into it; don't make a third surface). `DRIFT.md` and `fux stats` print a one-line pointer — "N drafts pending review → `.fux/CANDIDATES.md`" — so it's one glance, two docs.

---

## 6. Triage commands

- `fux candidates` — show the review surface (filter `--pending`/`--why-todo`).
- `fux candidates accept <id>` — promote a draft to an active rule (or open the `/fux debate → ratify` path if it's marked constitutional-candidate).
- `fux candidates reject <id>` — drop it (records the rejection so it isn't re-proposed).

---

## 7. Changes (file by file)

1. **new** skill `data/skills/propose-rules/SKILL.md` — the agent-driven forward pass (diff + rationale → drafts-with-why, §4 gate) and the retro mode (mine + git-history why-extraction). Wire into `install.sh` + skills index.
2. `fux mine` — reuse for AST candidates; ensure draft frontmatter is queue-compatible.
3. `ingestqueue.py` → generalize into the shared **candidates surface** (`.fux/CANDIDATES.md`): persistent triage state, dedup vs existing rules + queue, per-run cap, why-density sort, **never blocks**. ≤100 lines.
4. `cli.py` — `fux propose-rules [--retro]` + `fux candidates [accept|reject]` + the **opt-in** SessionEnd/per-PR hook (config-gated).
5. `check.py` / `stats` — print the "N drafts pending review →" pointer (read-only; the candidates surface never enters the blocking path).
6. `data/schema.json` — additive: `source` (session|mine|git), `why_source`; reuse `status: draft`. No new required fields.
7. Tests — a build session with a real decision proposes a draft-with-why; a trivial restatement proposes nothing; a genuine invariant with no why → `why: TODO`; a candidate duplicating an existing rule is skipped; retro run capped + deduped; **nothing auto-activates or auto-promotes to constitutional**; guard test — no LLM/network on the harness path.
8. Docs — `cli.md`, `fux-plan.md`, `README.md` (one line).

---

## 8. Acceptance

- A build session/PR proposes drafts-with-why into `.fux/CANDIDATES.md`; a change with no recoverable why proposes nothing.
- `fux propose-rules --retro` over a repo yields capped, deduped, why-density-sorted drafts sourced from `mine` + git history.
- Drafts carry provenance + triage state in the persistent candidates surface; `DRIFT.md` cross-links; the surface never blocks the gate.
- The gate works: not-a-rule and pure-restatement dropped; invariant-without-why → `why: TODO`; existing-rule duplicate skipped.
- Every proposal is `status: draft`, `tier: standard` — nothing auto-active, nothing auto-constitutional.
- `$0`/stdlib/deterministic harness; guard test green; opt-in forward hook; files ≤100 lines; docs in sync.

---

## 9. Execution prompt (paste into Claude Code, fux repo)

```
Build the Rule Proposer per docs/rule-proposer.md. Read it plus the existing `fux mine`, ingestqueue.py,
the distill skill, cli.py, fux/hooks.py, fux/check.py, and fux/data/schema.json first. Plan briefly, show
me the plan, then implement.

HARD LINES: drafts auto, ratification human, CONSTITUTION NEVER auto (every proposal status: draft, tier:
standard). NO recoverable why → NO draft (genuine invariant may draft why: TODO flagged; pure restatement
dropped). Dedup against EXISTING rules + the queue. Agent proposes (host tokens); fux harness ($0/stdlib/
deterministic) calls NO LLM (guard test). Forward hook is OPT-IN (config). Files ≤100 lines. Docs in change.

DO (per §3–§7):
1. new skill data/skills/propose-rules/SKILL.md — FORWARD (diff + PR/commit/session rationale → drafts-
   with-why, §4 gate) and RETRO (`fux propose-rules --retro`: fux mine + git-history why-extraction,
   bounded/capped). Wire into install.sh + skills index.
2. Generalize ingestqueue.py into the shared candidates surface `.fux/CANDIDATES.md` (NOT DRIFT.md):
   persistent pending|accepted|rejected state, dedup vs existing rules + queue, per-run cap, why-density
   sort, NEVER blocks. Add a "N drafts pending review → .fux/CANDIDATES.md" pointer in DRIFT.md (check.py)
   + fux stats.
3. cli.py — `fux propose-rules [--retro]`, `fux candidates [accept|reject] <id>`, opt-in SessionEnd/per-PR
   hook (config-gated).
4. schema.json — additive source (session|mine|git), why_source; reuse status: draft.

TESTS: real decision → draft-with-why; trivial restatement → nothing; invariant w/o why → why:TODO;
existing-rule duplicate skipped; retro run capped+deduped; NOTHING auto-active/constitutional; drafts in
.fux/CANDIDATES.md w/ triage state, not DRIFT.md, never blocks; GUARD — no LLM/network on the harness path.
Run `python -m pytest -q`, paste output, update cli.md/fux-plan/README.
```
