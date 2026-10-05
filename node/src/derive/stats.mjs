/** `stats.json` — the corpus-wide numbers BM25F reads, stored RAW.
 *  Twin of `src/fux/derive/stats.py` (W-261).
 *
 * **Owned by [SR-RUNTIME-STATS](../../../records/0125_runtime-stats.md)** with its Python twin: a pure
 * move out of `build.mjs`, which still decides when this file is written.
 * Python's bytes, byte for byte.
 */
import { join } from "node:path";
import * as fmt from "./format.mjs";

/** The plane's content: raw totals, never weighted. */
export function payload({ n, totalFlen, totalAnchorLen }) {
  return { n, total_flen: totalFlen, total_anchor_len: totalAnchorLen };
}

/** `stats.json` for one build. */
export function write(directory, stats) {
  fmt.writeJson(join(directory, fmt.STATS_NAME), stats);
}
