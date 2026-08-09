---
name: fux-propose-rules
description: "propose durable Fux rules-with-why automatically — forward (as you build) and retroactively (over shipped code) — as drafts you only ratify"
trigger: /fux propose-rules
---

# /fux propose-rules — the agent proposes rules-with-why; you only ratify

Closes the authoring loop (rule-proposer.md): the agent that wrote the code
**proposes** the rules-with-why, landing them as drafts in `.fux/CANDIDATES.md`
for you to triage. **The automation is the drafting; the gate stays human.**

## Hard lines (non-negotiable)

- **Drafts auto · ratification human · constitution NEVER auto.** Every proposal is
  `status: draft`, `tier: standard` — never active, never constitutional.
- **No recoverable why → no draft.** The value is the *why*. A genuine invariant
  with no written why may draft `why: TODO` (low-trust, sorted last); a pure
  restatement of code with no invariant and no why is **dropped**.
- **Dedup against existing rules + the queue** — never re-propose an active rule.
- **Agent proposes, fux governs.** Reading diffs and drafting prose is *your* tokens.
  The engine's gate/dedup/file step is `$0`/deterministic and calls no model.

## Two surfaces

### A. Forward — capture as you build (the high-value one)

Run after a meaningful change (PR, or an opt-in SessionEnd nudge):

1. **Resolve `$FUX`** as in `skills/fux/SKILL.md` Step 1.
2. **Read the change + its rationale** — the diff, the commit message / PR
   description, and the session you just had. The why is *freshest now*.
3. **Apply the §4 gate to each candidate.** Is it a *rule* (a non-obvious invariant
   or convention governing important code) **and** is a why recoverable?
   - not a rule, or pure code-restatement → **drop it** (don't draft).
   - a rule with a why → draft it *with the why*.
   - a genuine invariant with no recoverable why → draft with `"invariant": true`
     and no `why` (the engine flags it `why: TODO`).
4. **File the drafts** — write a JSON list and hand it to the engine, which gates,
   dedups (vs existing rules + the queue), caps, and appends to `.fux/CANDIDATES.md`:
   ```bash
   cat > /tmp/drafts.json <<'JSON'
   [{"kind": "convention", "title": "avg-cost, never FIFO, for lot accounting",
     "why": "FIFO double-counts wash sales; chosen in PR #41",
     "why_source": "PR #41", "code_refs": ["ledger/cost.py"]}]
   JSON
   $FUX propose-rules --from /tmp/drafts.json
   ```
   Each item: `{kind, title, why?, why_source?, code_refs?, invariant?}`. Omit `why`
   only for a true invariant; otherwise no-why ⇒ dropped.

### B. Retroactive — bootstrap shipped code (one-shot, $0)

```bash
$FUX propose-rules --retro
```
Pure engine: `fux mine` surfaces latent invariants from the AST and recovers the
why from git commit subjects touching each site. Bounded — capped per run, deduped,
why-density-sorted. No LLM. Eyeball the drafts; that ratify-rate is the MVP metric.

## Triage → ratify

```bash
$FUX candidates --pending          # review the surface (or --why-todo)
$FUX candidates accept <id>        # promote one draft to an active, standard rule
$FUX candidates reject <id>        # drop it (recorded so it isn't re-proposed)
```
A constitutional candidate is **never** accepted here — route it through
`/fux debate` → `fux ratify` (human only). `.fux/CANDIDATES.md` never blocks;
`fux check` / `fux stats` only print a one-line pointer to it.
