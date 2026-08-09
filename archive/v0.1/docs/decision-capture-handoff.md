# Fux — Debate/Council → Decision Capture Handoff

**Owner:** Arpit · **Repo:** `fux` · **Driving model:** Claude Code.
**Goal:** when a `/fux debate` or decision-council concludes, fux **captures the debate + verdict as a tamper-evident ADR and routes it to the right store by content** — automatically, not by memory. Operationalizes the standing rule (world/code → fux, money → elgar, app → anton) and obeys ADR 0001 (fux never holds money bytes).

---

## 0. Non-negotiables

- `$0`, stdlib, deterministic **capture path**. The *debating* is the host agent's tokens (already true of `/fux debate`); the **capture** — format ADR, classify route, seal, write the link — is deterministic fux harness with no LLM/network.
- **Firewall (ADR 0001):** a money-related decision record is written to **elgar**; fux keeps only an `elgar://decision/<id>` link and **never stores or derives the money content**. fux is decider + link-keeper, not custodian.
- Tamper-evident: every captured decision carries `debate_hash` (transcript) + `content_seal` (record body); `fux check` flags an altered record.
- Files ≤100 lines. No new deps. Docs in the same change.

---

## 1. What it does

On conclusion of a debate/council, produce a decision record (ADR shape) and route it:

| Content of the decision | Store | How fux writes it |
|---|---|---|
| world / code / architecture / tool design | **fux** (`fux/docs/decisions/NNNN-*.md` or `.fux/` `type: adr`) | full ADR, content-sealed |
| Anton-app-specific | **anton** (`anton/.fux/` `type: adr`) | full ADR, content-sealed |
| money / personal figures / portfolio plans | **elgar** (private store) | **agent/elgar writes the record; fux stores only `elgar://decision/<id>`** — never the body |

**Routing is agent-suggested + human-confirmed, and confirmation is MANDATORY when classified money/elgar** (a mis-route of a money decision into the public tree is the firewall failure — never silent).

ADR fields: `id`, `date`, `decided_by`, `method` (`debate`|`decision-council`), `decision`, `why`, `crux`, `strongest_dissent`, `what_would_reverse`, `debate_hash`, `content_seal`.

---

## 2. Changes (file by file)

1. **new** `decisioncapture.py` (≤100) — format the ADR from the agent's transcript+verdict; compute `debate_hash` + `content_seal` (reuse the existing seal/hash helpers); route + write per §1. Deterministic, `$0`.
2. `cli.py` — `fux capture-decision` (manual) + the routing flags; wire it so `/fux debate` and the decision-council skill **call capture on conclusion**.
3. `data/skills/debate/SKILL.md` (+ the council skill doc) — at the end of a debate/council, hand the transcript + verdict to capture; surface the suggested store and **require confirm for money/elgar**.
4. `data/schema.json` — ensure `type: adr` carries `decided_by`, `method`, `debate_hash`, `content_seal` (additive; reuse fields from the ratify work).
5. `check.py` — verify a captured ADR's `content_seal` (tamper finding if altered); **guard: a money/elgar-routed decision in fux must be a link only — flag if a fux-side record contains money content** (firewall check, ADR 0001).
6. Docs — `cli.md` (`capture-decision`, routing, the money-confirm rule), `fux-plan.md` (decision-capture section), `README.md` (one line). Backfill: ADR 0001 already exists at `fux/docs/decisions/0001-fux-elgar-relationship.md` — keep it as the format exemplar.

---

## 3. Acceptance

- Concluding a `/fux debate` or council writes a decision record routed to the correct store by content; the record carries `debate_hash` + `content_seal`.
- A **money-classified** decision routes to **elgar** with fux holding only `elgar://decision/<id>` — fux stores no money body; routing required explicit confirm.
- Editing a captured ADR trips a tamper finding (`content_seal` mismatch).
- The firewall guard flags any fux-side decision record that contains money content.
- `$0`/stdlib/deterministic capture; guard test green (no LLM/network on the capture path); files ≤100 lines; docs in sync.
