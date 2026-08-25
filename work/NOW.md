✓ **Two experiments, one question — can fux fix `q015`? Both ran.**

**Route 4 — is a cross-encoder deterministic across architectures? NO, and now it is measured.** Identical ONNX graph and input bytes, `onnxruntime==1.23.2` on x86_64 and aarch64, single-threaded, sequential, **every graph optimisation disabled** — the most deterministic configuration the runtime offers. **82.9 % of elements differ; max `1.907e-06`**, after **one** encoder block. `rank()` sorts on `round(score, 9)`, so that is **~2000x the rounding**. **ADR-RERANK veto 1 condition 2 was an assumption and is now evidence.** The bar for reopening it is now a number: drift below `5e-10`.

**Route 2 — declare the fact offline, rank on it deterministically. IT WORKS.** `supersedes:` in ADR-0019's frontmatter — the fact an offline model would write — makes `superseded: true` fire for the first time on any fux corpus, and `superseded_weight` demotes it. **`q015` recovers in BOTH blind arms** (33→34 and 31→32 at `w=0.7`), `q016` with it, at three different weights. **The fix never touches condition 2**, because a model that finished thinking before the query arrived has no determinism problem to solve. That is ADR-ENRICH's *"a source, never a step"*, applied to a **fact** instead of prose.

⚠ **Neither unblocks veto 1 condition 2.** Route 4 nailed it shut with evidence; route 2 made it irrelevant *to this failure*. ⚠ Route 2 covers **declared** relations only — *"this was abandoned"*, *"do not use X"* are untouched and **uncounted**. ⚠ The offline declarer is **unbuilt**: this run wrote the frontmatter by hand.

→ **Queue is five.** W-78 (both rulings now have evidence they lacked) · W-79 (`agent`) · W-77 · W-74 · W-75.

⚠ **Owed on Arpit's machine:** `fux ingest --full && fux build` on fux; the same on **fux-playground**, whose committed index is still `fux.index.v1`. Its `[ranking]` -> `.fux/tune.toml` migration is applied there but uncommitted. **The `supersedes:` declaration is applied only in the cloud copy** — it is a fixture change and is proposed, not committed.
