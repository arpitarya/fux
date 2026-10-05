/** `stamp.json` — the cheap size/mtime pre-check, volatile on purpose.
 *  Twin of `src/fux/derive/stamp.py` (W-261).
 *
 * **Owned by [SR-RUNTIME-STAMP](../../../records/0124_runtime-stamp.md)** with its Python twin: a pure
 * move out of `build.mjs`, which still decides when this file is written.
 * Python's bytes, byte for byte.
 */
import { join } from "node:path";
import * as fmt from "./format.mjs";

/** `stamp.json` for one build — written last, so a racing reader falls back to the scan. */
export function write(directory, shardStamp) {
  fmt.writeJson(join(directory, fmt.STAMP_NAME), {
    shards: new Map(shardStamp.map(([name, , size, mtime]) => [name, [size, mtime]])),
  });
}
