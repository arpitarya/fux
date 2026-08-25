✓ **The dense lane failed its own pre-registered gate — measured, not argued.** Asked to turn `[dense] mode` on, I ran the bar instead: **>= 3-fixed / 0-broken** required, **0 fixed / 2 broken** delivered, at every setting that fires. [DENSE-CHUNK FAIL](regression/2026-08-24-dense-lane-gate/VERDICT.md).

**The cause is structural and it is the finding of the day.** `embed/model.py` **mean-pools static token vectors** — no layers, no attention — so the dense lane is **as order-blind as BM25F**, and `always` mode breaks **`q015`**, the current-vs-superseded query a semantic lane was most expected to rescue. **Phase 7 was right that per-chunk beats per-document and wrong that the unit was the binding constraint.** The pooling is.

⚠ **Three of the four ways to fix `q015` converge on the same locked door** — reading word order at query time, which is what ADR-RERANK veto 1 condition 2 refuses on cross-machine determinism. **Fux currently cannot represent negation**, and that is now load-bearing rather than a footnote. Not a proposal to unlock it; the determinism argument is a good one.

✓ **W-79 filed** (`agent`) on Arpit's instruction: `query/hybrid.py` is off the live path, its two `[fuse]` keys are unreachable, `explain --no-tune` is inert. ⚠ **`gated` is NOT dead and an earlier reading of mine said it was** — corrected in the record rather than quietly.

Earlier today: ✓ ADR-TUNE built (`v2.0.0-alpha.1`) · ✓ W-77's audit · ✓ W-73 and W-76 closed · ✓ two blind-author runs, confound closed.

→ **Queue is five. Four `arpit`, one `agent`.** W-78 (two rulings) · **W-79** (delete-or-wire-up, agent-executable once ruled) · W-77 · W-74 · W-75.

⚠ **Owed on Arpit's machine:** `fux ingest --full && fux build` on fux; the same on **fux-playground**, whose committed index is still `fux.index.v1` and which the current engine refuses. Its `[ranking]` -> `.fux/tune.toml` migration is applied there but **uncommitted**, alongside another session's untracked goldens and enrichment.
