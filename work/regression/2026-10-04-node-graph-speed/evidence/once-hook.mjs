// W-259 (b) prototype, harness side: ONE graph-plane build per Node process.
//
// Loaded with `node --import once-hook.mjs`. It rewrites node/src/graph/plane.mjs
// IN MEMORY as the module loads: the shipped `planeFor` is renamed and wrapped
// by a memo keyed like verbs/mcp.mjs::Resident — the digest of stamp.json plus
// every committed shard's name, size and mtime — recomputed on every call and
// dropped when it moves. No engine file on disk changes. With
// FUX_GRAPH_REBUILD=1 (always set in (b)) the inner call is the in-memory
// rebuild, so the process still compares two builders; it just builds once.
import { registerHooks } from "node:module";

const TARGET = "/node/src/graph/plane.mjs";
const SHIPPED = "export function planeFor(root, shards = null) {";

const MEMO = `
import { statSync as __w259Stat, readFileSync as __w259Read } from "node:fs";
import { createHash as __w259Hash } from "node:crypto";
import { iterShardPaths as __w259Shards } from "../store/reader.mjs";
import { STAMP_NAME as __w259Stamp } from "../derive/format.mjs";
let __w259Key = null, __w259Plane = null;
/** Counters the prototype reports: builds made, calls answered from the memo. */
globalThis.__w259 = { builds: 0, hits: 0 };
function __w259StateKey(root) {
  let digest = "none";
  try { digest = __w259Hash("sha256").update(__w259Read(join(runtimeDir(root), __w259Stamp))).digest("hex"); }
  catch (e) { if (e.code !== "ENOENT") throw e; }
  const parts = __w259Shards(root).map((p) => {
    const st = __w259Stat(p, { bigint: true });
    return p + ":" + st.size + ":" + st.mtimeNs;
  });
  return root + "|" + digest + "|" + parts.join(",");
}
export function planeFor(root, shards = null) {
  const key = __w259StateKey(root);
  if (__w259Plane !== null && __w259Key === key) { globalThis.__w259.hits++; return __w259Plane; }
  const plane = __w259PlaneForShipped(root, shards);
  globalThis.__w259.builds++;
  __w259Key = key; __w259Plane = plane;
  return plane;
}
`;

registerHooks({
  load(url, context, nextLoad) {
    const out = nextLoad(url, context);
    if (!url.endsWith(TARGET)) return out;
    const src = String(out.source);
    if (!src.includes(SHIPPED)) throw new Error(`once-hook: ${TARGET} no longer has the planeFor this prototype wraps`);
    return { ...out, source: src.replace(SHIPPED, "function __w259PlaneForShipped(root, shards = null) {") + MEMO };
  },
});
