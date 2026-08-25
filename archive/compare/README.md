# `archive/compare/` — forks that are closed AND cannot reopen

**How to use this file.** A compare doc lives in
[`work/compare/`](../../work/compare/README.md) while its fork is live — and a
*decided* fork is still live there, because the doc carries the verdict **and
the reopen-trigger** that would bring it back. A doc moves here only when
**both** are spent: the fork is closed, and the trigger can no longer fire.

**Archive is not evidence.** These docs may be *named* — "the wire format was
decided in `wire-format.compare.md`" — but never cited as backing a live claim.
Repoint any live citation at the record that carries the decision now. See
[`../README.md`](../README.md) §Archive is not evidence.

## Moving a doc here

In one change: `git mv`, add a row below saying **why the trigger cannot fire**,
delete its row from `work/compare/README.md`, and bump the DOC-REGISTRY. A doc
moved without that sentence is indistinguishable from one filed by mistake.

| doc | closed | why the trigger can no longer fire |
|---|---|---|
| [`wire-format.compare.md`](wire-format.compare.md) | 2026-08-25 | Decided 2026-08-09 and then **superseded the same day** by `index-format` for the committed plane. Its chosen artifact — the BIC wire format — **was never built**, and the doc survived only on "survives inside tier T2". **T2 was measured and declined**: [R9-T2-AT-10K](../../work/regression/2026-08-22-r9-t2-at-10k/VERDICT.md) PASS at 12.46 ms against a 150 ms bar, 12x inside it. The compact encoding it describes lives on as a live proposal inside [ADR-POSTINGS](../../docs/adr/0013_postings.md), which is where a reader should go |
| [`keyspace-unification.compare.md`](keyspace-unification.compare.md) | 2026-08-25 | Verdict "one MST keyspace", **superseded the same day (2026-08-09)** — git itself provides the Merkle tree. No MST exists anywhere in `src/`. Its reopen-trigger is *"T2 needs a content-defined chunk store"*, and **T2 was declined on measurement**, so the trigger's precondition can never arrive |
| [`pruning-criterion.compare.md`](pruning-criterion.compare.md) | 2026-08-25 | `status: rejected`. The prediction was **falsified** by P1-RERUN, and option E — full postings, permanently — shipped. **Reopening is not merely unlikely, it is forbidden**: [ADR-POSTINGS](../../docs/adr/0013_postings.md) decision 8 states *"Postings are never pruned"* and bars pruning work outside a dedicated item; that item was W-38, **dropped on Arpit's instruction** 2026-08-22. `CLAUDE.md`: *"the pruned-index design is dead, not deferred"* |
| [`r7-size-budget.compare.md`](r7-size-budget.compare.md) | 2026-08-25 | `status: retired`. It forked over what **shape** R7's committed-size budget should have — and **R7 itself was retired with no successor** by Arpit on 2026-08-22, so there is no budget to shape. Recorded in [ADR-POSTINGS](../../docs/adr/0013_postings.md) and [ADR-INDEX-LIFECYCLE](../../docs/adr/0009_index-lifecycle.md). The size checks survive as prints, not gates — the ruled outcome. ⚠ Its README row still read *"⏳ awaiting Arpit"* for three days after the retirement |
