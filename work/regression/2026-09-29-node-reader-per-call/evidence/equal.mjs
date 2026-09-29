// graphRecords(root) must equal a full JSON.parse reduced to {id, edges},
// record for record, and give the same plane digest.   node equal.mjs FUX_CHECKOUT CORPUS_ROOT
import { pathToFileURL } from "node:url";
const [fux, root] = process.argv.slice(2);
const r = await import(pathToFileURL(`${fux}/node/src/store/reader.mjs`));
const p = await import(pathToFileURL(`${fux}/node/src/graph/plane.mjs`));
const full = [];
for (const path of r.iterShardPaths(root)) {
  const [, lines] = r.rawRecordLines(path);
  for (const l of lines) full.push(JSON.parse(l.toString("utf8")));
}
let t = performance.now(); const lean = r.graphRecords(root); t = performance.now() - t;
const key = (x) => JSON.stringify({ id: x.id, edges: x.edges });
const mismatched = full.filter((x, i) => key(x) !== key(lean[i])).length;
console.log({ records: full.length, mismatched, leanMs: Math.round(t),
  sameDigest: p.planeDigest(p.buildPlane(full)) === p.planeDigest(p.buildPlane(lean)) });
