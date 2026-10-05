/** `manifest.json` — the per-shard content-sha fingerprint.
 *  Twin of `src/fux/derive/manifest.py` (W-261).
 *
 * **Owned by [SR-RUNTIME-MANIFEST](../../../records/0123_runtime-manifest.md)** with its Python twin: a pure
 * move out of `build.mjs`, which still decides when this file is written.
 * Python's bytes, byte for byte.
 */
import { join } from "node:path";
import { SCHEMA_ID, ANALYZER_VERSION } from "../store/format.mjs";
import * as fmt from "./format.mjs";

/** `manifest.json` for one build; only the sha of each `shardStamp` row is its. */
export function write(directory, { docs, terms, blocks, shardStamp }) {
  fmt.writeJson(join(directory, fmt.MANIFEST_NAME), {
    schema: fmt.RUNTIME_SCHEMA,
    index_schema: SCHEMA_ID,
    analyzer: ANALYZER_VERSION,
    block_size: fmt.BLOCK_SIZE,
    docs_fields: [...fmt.DOCS_FIELDS],
    docs,
    terms,
    blocks,
    shards: Object.fromEntries(shardStamp.map(([name, sha]) => [name, sha])),
  });
}
