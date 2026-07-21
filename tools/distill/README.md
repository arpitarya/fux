# tools/distill — the bundled-model build pipeline (dev-only)

Produces `src/fux/embed/data/model.bin` (+ `model.json` metadata) and the
runtime test fixtures in `tests/data/embed_reference.json`. Heavy dependencies
are allowed **here and only here** — the runtime never imports any of this.

## Reproduce

```bash
uv venv /tmp/distill --python 3.12
uv pip install --python /tmp/distill/bin/python model2vec
/tmp/distill/bin/python tools/distill/distill.py
```

## Recipe (pinned)

- **Teacher:** `minishlab/potion-base-8M` (Model2Vec static embeddings distilled
  from `baai/bge-base-en-v1.5`; MIT license — checked by the script against the
  model card). 29,528-token WordPiece vocab (BertNormalizer: lowercase +
  accent-strip), 256 dims, float32.
- **Quantization:** int8 per-vector symmetric, `scale = max|v| / 127`
  (zero vectors get scale 1). No vocab trimming needed — the packed bundle is
  ~7.8 MB, inside the 10 MB budget.
- **Determinism:** the pack is a pure function of the teacher weights; the
  bundle sha256 is recorded in `model.json` and asserted by the runtime tests.
  The teacher itself is deterministic per released revision — if upstream ever
  rewrites the repo, the sha mismatch will say so loudly.

## Format (`model.bin`)

```
8s   magic  "FUXEMB1\0"
<III version=1, vocab_size, dim
vocab_size × (<H len + utf-8 token bytes)
vocab_size × <f4 per-vector scale
vocab_size × dim × int8 vectors
```

Read by `src/fux/embed/model.py` (stdlib `struct` only).

## Open question 1 (handoff 0003): re-pack vs distill-our-own

Shipping re-packed `potion-base-8M` was chosen; distilling a docs-flavored
model of our own needs a large in-domain corpus we don't have yet (Anton's is
the future candidate). Eval numbers for the shipped bundle are in ADR 0006 —
re-open when an Anton-scale corpus exists to distill against.
