✓ **W-79 closed — the dead fusion code is deleted.** `query/hybrid.py` gone, `[fuse]` out of ADR-TUNE's schema, `explain --no-tune` removed, `playground_grade.py` repointed at `run_query`. ADR-TUNE, ADR-CLI, ADR-ASK, ADR-T1-ACCELERATOR amended in the same change. Full suite green (1355 passed).

→ **Queue is four.** W-78 (both rulings now have evidence they lacked) · W-77 · W-74 · W-75.

⚠ **Owed on Arpit's machine (carried forward, unrelated to W-79):** `fux ingest --full && fux build` on fux; the same on **fux-playground**, whose committed index is still `fux.index.v1`. Its `[ranking]` -> `.fux/tune.toml` migration is applied there but uncommitted. **The `supersedes:` declaration is applied only in the cloud copy** — it is a fixture change and is proposed, not committed.
