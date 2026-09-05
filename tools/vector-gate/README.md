# `tools/vector-gate/` — W-106, the vector gate

**Scratch instrumentation, not engine code.** It answers one question:

> Does a **contextual**, locally-run, int8-quantised embedder fused with today's
> BM25F by RRF fix the vocabulary-gap failures the lexical lane cannot reach?

The dense lane was **deleted** on 2026-08-25 after
[DENSE-CHUNK](../../work/regression/2026-08-24-dense-lane-gate/VERDICT.md)
measured 0 fixed / 2 broken with a **static mean-pooled** model. A contextual
model had never been measured here. This measures one.

## The rules this obeys

- 🔴 **`src/fux/` never imports anything here, and nothing here is installed by
  the runtime.** `@huggingface/transformers` and `sentence-transformers` live
  in a scratch directory outside the repo; the import fence
  (`tests/test_import_fence.py`) is unaffected because the dependency runs the
  other way — this reads fux, fux never reads this.
- **The chunker is fux's own** (`fux.refer._chunk.chunk`). A dense lane that
  chunked differently would measure a corpus fux does not have.
- **The lexical ranks come from the shipped CLI** (`fux ask --json`), never
  re-implemented.
- **Graded on RANK, never score** — `fux-playground/check.py`'s rule.
- **No default is proposed and no switch is flipped.** The output is a count.

## The four files

| file | does |
|---|---|
| `prepare.py` | chunks the corpus with fux's chunker; emits chunks + queries |
| `embed_node.mjs` | arm 1 — `@huggingface/transformers`, ONNX, in Node. `pooling` and `dtype` are arguments |
| `embed_py.py` | arm 2 — `sentence-transformers`, the same model, in Python |
| `gate.py` | int8 (`127/max|x|`, per vector) → max-sim per document → RRF `k = 60` with today's BM25F ranks → grade → per-query rows |
| `cross_arm.py` | do two implementations of one model produce the same vector? The question W-112 rests on and retrieval cannot answer |

## 🔴 `pooling` defaults to `cls`, and W-106's DoD said `mean`

`BAAI/bge-small-en-v1.5` declares `pooling_mode: cls`. Mean-pooling it in the
Node arm computes a **different function** from the one the Python arm computes,
so the two would not be two implementations of one model. Measured: cross-arm
cosine **0.909 (mean) → 0.996 (cls)**.

**The misconfigured arm is kept runnable and is part of the evidence** — it
scored *better* on retrieval than either correctly configured arm, which is
exactly how a misconfiguration gets adopted as a result.

## Running it

```bash
S=/tmp/vecgate && mkdir -p $S && cd $S
npm init -y && npm install @huggingface/transformers@3.7.6
uv venv .venv-st && VIRTUAL_ENV=$S/.venv-st uv pip install sentence-transformers

G=~/my_programs/fux/tools/vector-gate
Q=~/my_programs/fux-playground/goldens/queries.jsonl
python $G/prepare.py <corpus> $Q $S/prepared.json

cp $G/embed_node.mjs $S/            # node resolves modules beside the script
cd $S && node embed_node.mjs prepared.json vec-node.json      # cls / q8
./.venv-st/bin/python $G/embed_py.py prepared.json vec-py.json

python $G/gate.py <corpus> $S/prepared.json $S/vec-node.json $Q $S/rows.csv ~/my_programs/fux/src
python $G/cross_arm.py $S/prepared.json $S/vec-node.json $S/vec-py.json
```

Filed run: [`work/regression/2026-09-05-vector-gate/`](../../work/regression/2026-09-05-vector-gate/report.md).
