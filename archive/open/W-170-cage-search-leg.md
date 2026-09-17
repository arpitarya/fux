---
type: Handoff
name: W-170
description: "`.fux/observers/` — a third consumer extension point beside decoders and fetchers: after a verb renders, fux hands every observer one counts-only fact record (verb, args_hash, band, answerable, result/related counts, refer verdicts, latency, --expand/-q used). Observe-only, fail-open, wall-clock-capped; no question text, no document ids. Cage is the first subscriber — its `cage setup` drops the observer that writes cage's ledger. Ruled by Arpit 2026-09-14 as the mechanism; whether cage's leg ships is cage's open verdict."
item: W-170
filed: 2026-09-14
ball: agent
---

# W-170 — `.fux/observers/`, the observe-only hook (cage subscribes)

**Model: Opus for the seam** (a consumer extension point that must never be able to reach
the answer) **and the L10 amendment; Sonnet for the dispatcher and tests.**

**Ruled 2026-09-14 (Arpit):** the fux half of cage's search leg is **an extension point fux
exposes, not an emitter fux ships** — *"a middleware that fux exposes and cage can
intercept"*, narrowed in the same conversation to **observe-only**. Supersedes the emit
design in `archive/proposals/cage-search-leg.md` §1–§4 (archived 2026-09-14, kept
as the record of what was replaced). **Both rulings taken 2026-09-14 (Arpit):**
(1) cage's `work/compare/fux-search-leg.compare.md` — **option C** (both halves, A first,
B is the observer hook); cage's half A shipped the same day. (2) **observers get their
own record** — [SR-OBSERVE](../../records/0157_observe.md) is filed `proposed` with the
seam, the schema and the cap, and [SR-LAW-10](../../records/0011_LAW-10-bundled-output.md)
decision 2 now names `.fux/observers/` as the third exemption with his ruling in it.
**Nothing blocks the build.** Landing it flips SR-OBSERVE to `accepted`, fills its
`owns`, and deletes the `SR-OBSERVE` pin in `tests/test_sr_ownership.py`.

## ✅ BUILT 2026-09-15 — `fd674584`

DoD 1–8 are done on the Python reader. **Two things are NOT, and both are
stated rather than quietly closed:**

1. 🟡 **Node's half is declared OUT OF SCOPE**, which DoD 1 explicitly allows
   (*"or Node declared out of scope in SR-NODE-SEARCH"*) —
   [decision 18](../../records/0153_node-search.md). Python has one post-render
   dispatch point for every verb and the hook's guarantee comes from sitting
   there; this reader has none, so hosting it would mean five call sites where
   *after everything* becomes five things to keep true. ⚠ **A repo with
   observers records its Python runs and not its Node runs.**
2. 🟡 **The latency capture is not filed.** The keep/remove call wants p50 `ask`
   with no observer against one with a subscriber's, on this repo and the
   largest golden rung. **The byte-identity half is discharged by test** — the
   load-bearing one, with a hostile observer — and the latency half needs a
   real subscriber's observer, which is the consumer's to write (DoD 7), and a
   golden rung, which is `fux-lab`'s.

**Three defects the build found in itself:**

- 🔴 **An observer's `print` reached the answer.** The first dispatcher left
  fux's own `sys.stdout` in place, so `ask --json` emitted valid JSON followed
  by the observer's line — consumer code on stdout, which DoD 3 forbids. Fixed
  structurally: stdout is taken away for the whole dispatch. **Found by the
  hostile test**, which is the one thing in this item that had to be written to
  fail.
- ⚠ **The cap ABANDONS a thread; it cannot kill one.** SR-OBSERVE decision 6
  said *killed* and that word was wrong — Python cannot safely interrupt
  arbitrary consumer code. Corrected in decision 10b: what the cap guarantees
  is that a consumer's analytics cannot make `fux ask` slow, only itself.
- ⚠ **fux named a subscriber**, in the new module's own docstring, by quoting
  the ruling verbatim. DoD 7's grep caught it.

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
8. **Records.** **SR-OBSERVE exists (`proposed`) and SR-LAW-10 is amended** — the
   build flips the status, fills `owns`, and adds the ownership row;
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
