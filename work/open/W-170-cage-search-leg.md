---
type: Handoff
name: W-170
description: "fux's half of cage's search leg: one counts-only fact row per verb invocation (verb, args_hash, band, answerable, result/related counts, refer verdicts, latency, --expand/-q used) pushed fail-open to the resolved cage ledger's ledger/fux/. No question text, no document ids. Blocked on Arpit's verdict on cage's compare doc, which fixes the row shape and the args_hash contract."
item: W-170
filed: 2026-09-14
ball: arpit
---

# W-170 — the fux emitter for cage's search leg

**Model: Sonnet once the shape is ruled** — small, fail-open, dictated from cage's side.

**Promoted 2026-09-14 by Arpit** from [`proposals/cage-search-leg.md`](../proposals/cage-search-leg.md),
which stays the spec (row shape §1, laws §2, what it is not §3, order and keep/remove §4).
**Blocked on Arpit:** the verdict on `cage/work/compare/fux-search-leg.compare.md`
(sibling repo — named, not linked) decides whether half B exists and what row it emits.

## Definition of done

1. The `args_hash` contract: one normalisation of argv, shared by fixture with cage,
   tested on quoted/escaped commands — **first line of work, before any emit.**
2. Emit one row per verb run to `<resolved cage ledger>/ledger/fux/`, resolved the way
   cage's own shims resolve it; off when no ledger resolves; fail-open; `FUX_DEBUG`
   logs the skip reason. Gate: `[cage] emit` in `.fux/output.toml`, default on when a
   ledger resolves.
3. Fields exactly as the proposal's §1 table; **never** the question, expansion text,
   a document id or path, or the answer — a test greps every emitted row for the
   forbidden classes.
4. `ask`/`answer` stdout byte-identical with emit on and off (the emitter cannot touch
   output); both readers, or Node declared out of scope in SR-NODE-SEARCH.
5. Records: SR-CLI (the emit point), SR-LAW-8 (a Consequences note: why this is not a
   use record — a counts row outside the repo), SR-PROVENANCE (relation to the journal),
   SR-OUTPUT-DEFAULTS (the key). Guide skill `fux-usage` gains one line.

## Keep / remove

Keep if cage's join reaches ≥ 50 % on one real chat. Remove the join key, keep the rows,
if not.

## Records this will touch

SR-CLI · SR-LAW-8 · SR-PROVENANCE · SR-OUTPUT-DEFAULTS · SR-NODE-SEARCH.
