# Pre-registration — CSV chunk granularity (written before any number existed)

**Question.** For a `.csv`, does one passage per ROW answer better than the
band-of-rows the engine produces today?

**Instrument.** The real `fux.refer` pipeline — `chunk` -> `rescore` ->
`assemble` — on a decoded CSV. Chunking is a **refer-plane** concern: `extract.py`
indexes the whole decoded document either way, so the index is identical across
arms and only the retrieval unit *within* a document changes. Measuring the
index would measure nothing.

**Shape.** One candidate document per query — the shape `query/refer_answer.py`
actually ships (`_assemble`: "the cap does not apply when there is only one
candidate document").

**Arms** — one constant, `_chunk.MAX_TABLE_BAND_BYTES`; no other code differs:
| arm | value | what it is |
|---|---|---|
| `band-4000` | 4000 | pre-W-120: the prose ceiling, ~58 rows |
| `band-900` | 900 | W-120 as written, ~11 rows |
| `row` | 1 | one row per passage, header repeated |

**Metrics, defined now:**
- `hit@1` — the TOP citation contains the answering row (primary)
- `hit@3`, `mrr` — over citations in returned order
- `noise_ratio` — mean over hits of `(bytes_returned - len(answer_row)) / bytes_returned`
- `bytes_returned`, `passages_per_doc`
- `chunk_ms` / `rescore_ms` / `assemble_ms`, p50 and p95

**What this run may NOT do.** It is `informed` under RUN-CLASSIFICATION — the
same author wrote the corpus generator and the queries — so it **supplies no
delta for a shipping decision**. It is a number, and per TEST-PLAN §0a a number
is not a grade. Latency is single-surface and not comparable off it (§2).
