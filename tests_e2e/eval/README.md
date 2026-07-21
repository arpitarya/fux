---
type: Reference
title: Eval harness — the engine's quality gate
description: Committed Q→passage pairs + hit@1/hit@5/MRR runner; the gate for hybrid v2 and the reopen-instrument for the reranker decision.
timestamp: 2026-07-21T00:00:00Z
---

# Eval harness

`pairs.jsonl` holds committed "question → expected passage" pairs against the
fixture corpus (`tests_e2e/corpus/`). Each line:

```json
{"q": "how quickly can we revert a failed release", "file": "docs/guide.md", "heading": "Deploy"}
```

`heading` is optional — when present, the matching result must also contain it
(in its heading path or text). Run:

```bash
uv run python tests_e2e/eval/run_eval.py                 # default engine
uv run python tests_e2e/eval/run_eval.py --lexical-only  # v1 BM25F baseline
```

Reports `hit@1`, `hit@5`, `MRR`, and the missed questions. The e2e suite runs
the same metrics (`test_eval.py`); the v2 ship gate is hybrid ≥ lexical on
hit@5 and MRR (numbers recorded in ADR 0006).

## Evaluating on Anton (private pairs — do not commit)

1. Write an `anton-pairs.jsonl` in the Anton repo (same shape; `file` paths are
   Anton source paths as they appear in `fux ask --json` output).
2. Make sure Anton is ingested (`fux ingest` in the Anton root).
3. Run the harness against it:

   ```bash
   uv run python tests_e2e/eval/run_eval.py \
       --project ~/my_programs/anton --pairs ~/my_programs/anton/anton-pairs.jsonl
   ```

Anton numbers are the ones that matter (litmus: "is it relevant to Anton?");
the committed fixture pairs exist so CI has a deterministic gate. If Anton
evidence ever contradicts the fixture gate (e.g. paraphrase recall is still
poor), that is the recorded reopen-trigger for the no-reranker decision —
see `docs/compare/query-engine.compare.md`.
