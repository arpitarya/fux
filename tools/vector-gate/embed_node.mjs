// W-106 arm 1 — `@huggingface/transformers` (transformers.js), q8, in Node.
//
// The arm a CONSUMER would actually run: a Node host with no Python, an ONNX
// model, int8 weights, no service. It is one of two implementations of the
// same model on purpose -- if two runtimes' vectors disagree, the pinned
// `.fux/vectors/` W-112 proposes is not reproducible and the design is wrong
// before it is built.
//
// Usage: node embed_node.mjs <prepared.json> <out.json> [model] [pooling] [dtype]
//
// 🔴 **`pooling` DEFAULTS TO `cls`, and W-106's own DoD said `mean`.**
// `BAAI/bge-small-en-v1.5` declares `pooling_mode: cls` in its
// sentence-transformers config, so mean-pooling it computes a different
// function from the one the Python arm computes -- the two arms would not be
// two implementations of one model, and every cross-arm number would be
// measuring a misconfiguration. Measured: mean-vs-cls drops cross-arm cosine
// from 0.996 to 0.909. Both are runnable here because the misconfigured arm is
// part of the evidence, not a mistake to be hidden.
import { readFileSync, writeFileSync } from "node:fs";
import { pipeline, env } from "@huggingface/transformers";

const MODEL = process.argv[4] ?? "Xenova/bge-small-en-v1.5";
const POOLING = process.argv[5] ?? "cls";
const DTYPE = process.argv[6] ?? "q8";
env.allowLocalModels = false;

const data = JSON.parse(readFileSync(process.argv[2], "utf-8"));
const fe = await pipeline("feature-extraction", MODEL, { dtype: DTYPE });

async function embed(texts) {
  const out = [];
  const BATCH = 16;
  for (let i = 0; i < texts.length; i += BATCH) {
    const t = await fe(texts.slice(i, i + BATCH), { pooling: POOLING, normalize: true });
    const [n, d] = t.dims;
    for (let r = 0; r < n; r++) out.push(Array.from(t.data.slice(r * d, (r + 1) * d)));
  }
  return out;
}

const chunkVecs = await embed(data.chunks.map((c) => c.text));
// bge asks for an instruction prefix on the QUERY side only. Using it is the
// model's documented usage; not using it would measure a misconfigured model
// and blame the architecture.
const PREFIX = "Represent this sentence for searching relevant passages: ";
const queryVecs = await embed(data.queries.map((q) => PREFIX + q.q));

writeFileSync(process.argv[3], JSON.stringify({
  arm: `huggingface-transformers-js/${POOLING}/${DTYPE}`,
  model: MODEL,
  runtime: `node ${process.version} ${process.platform}/${process.arch}`,
  dims: chunkVecs[0].length,
  chunks: chunkVecs,
  queries: queryVecs,
}));
console.log(`${chunkVecs.length} chunk vectors + ${queryVecs.length} query vectors (${chunkVecs[0].length}d) -> ${process.argv[3]}`);
