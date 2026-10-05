/** `docs.jsonl` — the docidx-ordered doc table.
 *  Twin of `src/fux/derive/docstable.py` (W-261).
 *
 * **Owned by [SR-DOCS-TABLE](../../../records/0122_docs-table.md)** with its Python twin: a pure
 * move out of `build.mjs`, which still decides when this file is written.
 * Python's bytes, byte for byte.
 */
import { writeFileSync } from "node:fs";
import { join } from "node:path";
import { pyDumps } from "../compat/pyjson.mjs";
import * as fmt from "./format.mjs";

/** `docs.jsonl`: one docidx-ordered row per document. */
export function write(directory, docs) {
  writeFileSync(
    join(directory, fmt.DOCS_NAME),
    Buffer.from(docs.map((doc) => pyDumps(doc, fmt.DUMPS) + "\n").join(""), "utf8"),
  );
}
