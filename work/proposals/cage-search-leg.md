---
type: Proposal
title: "fux emits one fact row per invocation to cage — the fux half of cage's search leg"
description: "Cage is proposing a leg that classifies every searchable moment in agent transcripts (fux vs grep vs Read) and joins it to what fux itself did. This is fux's half: one JSON row per verb run — verb, args_hash, band, answerable, result and related counts, refer verdicts, latency, whether --expand/-q were used — pushed fail-open to the resolved cage ledger. No question text, no document ids: L8 and cage's counts-never-content law agree. Proposed 2026-09-14; nothing built."
status: graduated
timestamp: 2026-09-14T00:00:00Z
filed: 2026-09-14
---

**Graduated 2026-09-14 → [W-170](../open/W-170-cage-search-leg.md)** (Arpit). This file stays the spec the item points at.

# fux's half of cage's search leg

**Model: Sonnet once cage's compare doc is accepted** — the emitter is small, fail-open,
and its shape is dictated from the other side.

**Found:** Arpit, 2026-09-14 — cage should tell us *in what cases fux gets triggered and
in what cases it doesn't*. The cage side is
[`cage/work/compare/fux-search-leg.compare.md`](../../../cage/work/compare/fux-search-leg.compare.md)
(a sibling repo; named, not a live link this bundle can resolve). **Owning records when
built:** [SR-CLI](../../records/0101_cli-surface.md) (the emit point sits at the CLI
boundary), [SR-LAW-8](../../records/0010_LAW-8-use-record.md) (why this is not a use
record), [SR-LAW-4](../../records/0006_LAW-4-offline-by-default.md) (a local file write,
no network), [SR-PROVENANCE](../../records/0142_provenance.md).

## 1 · What fux would emit

One row per verb invocation, appended to `<resolved cage ledger>/ledger/fux/` — the
directory cage already reserves for fux and receives nothing in:

| field | value | why cage wants it |
|---|---|---|
| `verb` | `ask`/`find`/`answer`/`lexical`/`graph`/`path`/`explain`/`correct`/MCP tool | which surface was used |
| `args_hash` | hash of the normalised argv, **the contract shared with cage** | the join key to the agent's transcript row |
| `band`, `answerable` | from the confidence block | "called and abstained" vs "called and answered" |
| `n_results`, `n_related` | counts | was there anything to use |
| `refer` | verdict histogram (`current`/`stale`/…) | freshness at answer time |
| `ms` | wall time of the run | latency the agent felt |
| `expand_used`, `q_arms` | booleans/counts | did the agent use the vocabulary slot |
| `fux_version` | `fux.__version__` | which build |

**Never:** the question, the expansion text, a document id or path, the answer.

## 2 · Laws

- **L8** governs *commits*: this file lives in cage's ledger, outside the repo. A row with
  no text is not a use record in the sense L8 protects, and it is not committed anyway.
- **L4** — a local append; no network.
- **L3** — nothing here reaches the index; the emitter runs after the answer is rendered.
- **Fail-open, off by default until cage is detected** — the graphify shim's pattern:
  if no cage ledger resolves, nothing is written and nothing is printed.

## 3 · What it is not

- Not the journal (`--journal`, SR-PROVENANCE decision 10) — that holds plaintext and
  lives under `.fux/runtime/`; this holds counts and lives under cage.
- Not a second confidence surface — it *copies* the block's verdict, never recomputes.

## 4 · Order, tests, and the keep/remove call

1. **Wait for cage's verdict** on the compare doc; the row shape is theirs to accept.
2. **`args_hash` contract first**: one normalisation, fixture-tested on both sides with
   quoted/escaped commands.
3. Implement behind `[cage] emit = true` in `.fux/output.toml` (default: on when a cage
   ledger resolves), fail-open, `FUX_DEBUG`-logged.
4. Tests: a row per verb on the golden repo; no forbidden field ever present (grep the
   row); byte-identical `ask` output with emit on/off (the emitter cannot touch stdout).
5. **Keep** if cage's join reaches ≥ 50 % on one real chat. **Remove the join key**,
   keep the rows, if it does not — the facts stand alone.

## 5 · Graduation trigger

Cage accepts option C → this becomes a `W-nn` here with the hash contract as its first
line of definition-of-done.
