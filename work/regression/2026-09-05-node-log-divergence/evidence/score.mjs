// W-107 Phase 0 — the same BM25F arithmetic in Node, over Python's own inputs.
//
// A TRANSCRIPTION, not a reimplementation: the loop order, the accumulation
// order and the expression shape are `query/bm25f.py::score_record`'s, because
// float addition is not associative and a "cleaner" reduce would introduce a
// second source of divergence on top of the one being measured.
import { readFileSync, writeFileSync } from "node:fs";

const idf = (df, n) => Math.log((n - df + 0.5) / (df + 0.5) + 1);

function weightedTf(tf, weights) {
  let total = 0.0;
  for (let i = 0; i < tf.length; i++) if (tf[i]) total += weights[i] * tf[i];
  return total;
}

function deriveWlen(flen, weights) {
  let total = 0.0;
  for (let i = 0; i < flen.length; i++) if (flen[i]) total += weights[i] * flen[i];
  return total;
}

function scoreRecord(tfByHash, flen, hashes, df, n, avgWlen, k1, b, weights) {
  if (n <= 0 || avgWlen <= 0) return 0.0;
  const wlen = deriveWlen(flen, weights);
  let total = 0.0;
  for (const h of hashes) {
    const tf = tfByHash[h];
    if (tf === undefined) continue;
    const wtf = weightedTf(tf, weights);
    if (wtf === 0) continue;
    const denom = wtf + k1 * (1 - b + (b * wlen) / avgWlen);
    total += idf(df[h] ?? 0, n) * wtf * (k1 + 1) / denom;
  }
  return total;
}

const path = process.argv[2];
const rows = JSON.parse(readFileSync(path, "utf-8"));
for (const row of rows) {
  for (const doc of row.docs) {
    doc.node = scoreRecord(
      doc.tf, doc.flen, row.hashes, row.df, row.n, row.avg_wlen,
      row.k1, row.b, row.weights,
    );
  }
}
writeFileSync(process.argv[3], JSON.stringify(rows));
console.log(`node ${process.version}: scored ${rows.reduce((a, r) => a + r.docs.length, 0)} documents`);
