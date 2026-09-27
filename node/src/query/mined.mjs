/** Corpus-mined expansion — the read-time fold. Twin of `src/fux/query/mined.py`.
 *
 * W-168 step 4. A document that writes "Mean Kinetic Temperature (MKT)" has
 * declared the two spellings the same; ingest (Python only) commits that as
 * hashes on the document's own record, `abbr: [[short], [long]]`. This module
 * builds the corpus table from the shards and folds it into a query. Mining is
 * not here: the Node reader never ingests.
 *
 * Default `MINED_WEIGHT` (0.5), measured and ratified PASS on 2026-09-27.
 * Off at `mined_weight = 0.0`, and off reads no pair.
 *
 * Owned, with its Python twin, by [SR-EXPAND](../../../records/0149_expand.md).
 */
import { rawRecordLines, iterShardPaths } from "../store/reader.mjs";

//: The `[ranking] mined_weight` default — W-168 step 4's measured value.
//: Twin of `MINED_WEIGHT` in `src/fux/query/mined.py`, held equal by a test.
export const MINED_WEIGHT = 0.5;

//: `abbr` sorts first among a record's keys, so it can only open the line.
//: Latin-1 view of the raw bytes; every element is a quoted 16-hex hash.
const ABBR_RE = /^\{"abbr":(\[(?:\[\[[^[\]]*\],\[[^[\]]*\]\],?)+\])/;

/** Python's tuple ordering over arrays of strings: element-wise, and a proper
 *  prefix sorts first. The hashes are ASCII hex, so code-unit order is
 *  code-point order. */
function cmpSide(a, b) {
  const n = Math.min(a.length, b.length);
  for (let i = 0; i < n; i++) {
    if (a[i] < b[i]) return -1;
    if (a[i] > b[i]) return 1;
  }
  return a.length - b.length;
}

function cmpPair(a, b) {
  return cmpSide(a[0], b[0]) || cmpSide(a[1], b[1]);
}

/** The committed `abbr` of one raw shard line, or `[]`. */
export function pairsFromLine(line) {
  const m = ABBR_RE.exec(line.toString("latin1"));
  return m ? JSON.parse(m[1]) : [];
}

/** The corpus table, de-duplicated and sorted exactly as `table_from_shards`. */
export function tableFromShards(root) {
  const seen = new Map();
  for (const path of iterShardPaths(root)) {
    const [, lines] = rawRecordLines(path);
    for (const line of lines) {
      for (const pair of pairsFromLine(line)) seen.set(JSON.stringify(pair), pair);
    }
  }
  return [...seen.values()].sort(cmpPair);
}

/** The hashes the corpus adds to a query. For each pair `(A, B)` in sorted
 *  order: `A ⊆ Q` and `B ⊄ Q` adds `B \ Q`; the reverse adds `A \ Q`. Added
 *  hashes are de-duplicated first-seen. */
export function fold(table, queryHashes) {
  const q = new Set(queryHashes);
  const added = new Set();
  for (const [short, long] of table) {
    const sIn = short.every((h) => q.has(h));
    const lIn = long.every((h) => q.has(h));
    let side;
    if (sIn && !lIn) side = long;
    else if (lIn && !sIn) side = short;
    else continue;
    for (const h of side) if (!q.has(h)) added.add(h);
  }
  return [...added];
}
