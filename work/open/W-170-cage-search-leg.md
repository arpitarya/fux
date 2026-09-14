---
type: Handoff
name: W-170
description: "`.fux/observers/` — a third consumer extension point beside decoders and fetchers: after a verb renders, fux hands every observer one counts-only fact record (verb, args_hash, band, answerable, result/related counts, refer verdicts, latency, --expand/-q used). Observe-only, fail-open, wall-clock-capped; no question text, no document ids. Cage is the first subscriber — its `cage setup` drops the observer that writes cage's ledger. Ruled by Arpit 2026-09-14 as the mechanism; whether cage's leg ships is cage's open verdict."
item: W-170
filed: 2026-09-14
ball: arpit
---

# W-170 — `.fux/observers/`, the observe-only hook (cage subscribes)

**Model: Opus for the seam** (a consumer extension point that must never be able to reach
the answer) **and the L10 amendment; Sonnet for the dispatcher and tests.**

**Ruled 2026-09-14 (Arpit):** the fux half of cage's search leg is **an extension point fux
exposes, not an emitter fux ships** — *"a middleware that fux exposes and cage can
intercept"*, narrowed in the same conversation to **observe-only**. Supersedes the emit
design in [`proposals/cage-search-leg.md`](../proposals/cage-search-leg.md) §1–§4 (kept
as the record of what was replaced). **Still blocked on Arpit:** cage's verdict on
`cage/work/compare/fux-search-leg.compare.md` decides whether anyone subscribes; the
L10 exemption (below) is a Law change and needs his ruling **named in the record**.

## Definition of done

1. **The extension point.** `.fux/observers/*.py` (Python) and, on the Node reader,
   `.fux/observers/*.mjs` — or Node declared out of scope in SR-NODE-SEARCH. Readable
   source by contract, like decoders and fetchers. Scaffolded empty by `fux setup`.
2. **The event, and when.** After a verb has fully rendered (stdout flushed), fux calls
   each observer's `observe(record)` with **one** record: `verb · args_hash · band ·
   answerable · n_results · n_related · refer_verdicts{} · ms · expand_used · q_arms ·
   fux_version`. **Never** the question, expansion text, a document id or path, or the
   answer — a test greps the record schema and every emitted record for the forbidden
   classes.
3. **Observe-only, structurally.** The dispatcher runs after render, receives a frozen
   copy, and has no return path: nothing an observer does can change stdout, exit code,
   the index or the next run. A test asserts `ask`/`answer` output is byte-identical with
   zero, one and a misbehaving observer installed.
4. **Fail-open, bounded.** An observer that raises is skipped for that run with a
   `FUX_DEBUG` line naming it; a wall-clock cap (`[observe] max_ms`, default small)
   kills a slow one the same way. Determinism (L3) is untouched — nothing flows back.
5. **`args_hash`** is computed by fux from its normalised argv — **the contract shared
   with cage's transcript classifier**, fixture-tested on quoted/escaped commands on both
   sides. First line of work.
6. **Liveness.** `fux doctor` lists observers and whether each ran on the last
   invocation; a present-but-never-firing observer is a row.
7. **cage's template** is cage's to ship (`cage setup` writes `.fux/observers/cage.py`,
   which appends to `<resolved cage ledger>/ledger/fux/`). fux carries **no** cage
   knowledge — a test asserts `src/fux` imports and names nothing cage-shaped.
8. **Records.** A new **SR-OBSERVE** (the seam, the record schema, observe-only, the
   cap); **SR-LAW-10 amended by Arpit** — the exemption table gains `.fux/observers/*`;
   SR-CLI (the dispatch point); SR-LAW-8 (a Consequences note: a counts record handed to
   a consumer's code is not a use record, and nothing here reaches a commit); SR-DOCTOR;
   SR-NODE-SEARCH; SR-AGENT-POLICY (`fux-usage` gains one line; a `fux-observer` guide is
   **not** written until a second subscriber exists). Ownership + `test_sr_ownership.py`.

## Out of scope

- Any pre-verb hook, filter, or rewrite — refused by design, not deferred.
- Cage's reader and view (`cage insights search`) — cage's items.
- A second built-in observer.

## Verification, and the keep/remove call

Order: **L10 ruling → `args_hash` contract → implement → test → measure the cap → call.**

- Tests per DoD 2–7. The byte-identity test with a *misbehaving* observer (raises,
  sleeps, writes to stdout) is the load-bearing one.
- **Measured:** p50 `ask` latency with no observer vs cage's observer, on this repo and
  the largest golden rung, filed as a surface capture. **Keep** if the delta stays under
  the cap and the byte-identity holds. **Remove the dispatcher** (leave the empty
  directory documented as reserved) if an observer can be shown to alter any output or
  if the cap cannot be enforced on a platform — a seam that can leak is worse than none.
- If cage's join reaches < 50 % on real data, the `args_hash` contract is revisited on
  both sides; the seam itself is unaffected.

## Records this will touch

SR-OBSERVE (new) · SR-LAW-10 (Arpit) · SR-CLI · SR-LAW-8 · SR-DOCTOR · SR-NODE-SEARCH ·
SR-AGENT-POLICY · SR-WORK-OWNERSHIP (the table).
