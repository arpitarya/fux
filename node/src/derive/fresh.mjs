/** Is the derived plane fresh? And the scan's section attachment from it.
 *
 * Twin of `src/fux/derive/accel.py`: its `is_fresh` and
 * `attach_sections_by_id`. Split out of
 * `accel.mjs` (W-278) because the scan needs both, and `accel.mjs` imports the
 * scan: the bundle refuses an import cycle. `accel.mjs` re-exports `isFresh`
 * and `readStamp`, so no caller moved.
 *
 * Owned, with `accel.mjs`, by [SR-T1-ACCELERATOR](../../../records/README.md).
 */
import { existsSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { iterSectionPaths, iterShardPaths } from "../store/reader.mjs";
import * as fmt from "./format.mjs";

//: One `"name":[size,mtime_ns]` pair of `stamp.json`'s `shards`, kept as text.
//: 🔴 **Never `JSON.parse` the stamp.** `mtime_ns` is ~1.79e18, past 2^53, so a
//: `Number` rounds it, the check never matches, and Node would scan forever
//: while every test still passed (W-242 step 6).
const STAMP_PAIR_RE = /"([^"\\]+)":\[(\d+),(\d+)\]/g;

/** `{name: [size, mtimeNs]}` as BigInts, or `null` on a stamp this cannot read. */
export function readStamp(text) {
  const start = text.indexOf("\"shards\":{");
  if (start < 0) return null;
  const out = new Map();
  STAMP_PAIR_RE.lastIndex = start;
  let m;
  while ((m = STAMP_PAIR_RE.exec(text)) !== null) {
    const [, name, size, mtime] = m;
    out.set(name, [BigInt(size), BigInt(mtime)]);
  }
  return out;
}

/** Cheap staleness check: shard sizes and mtimes against the build stamp.
 *  `accel.py::is_fresh`, exactly — and anything it cannot read is NOT fresh. */
export function isFresh(root) {
  const directory = fmt.runtimeDir(root);
  const stampPath = join(directory, fmt.STAMP_NAME);
  const manifestPath = join(directory, fmt.MANIFEST_NAME);
  if (!existsSync(stampPath) || !existsSync(manifestPath)) return false;
  let manifest, stamp;
  try {
    manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
    stamp = readStamp(readFileSync(stampPath, "utf8"));
  } catch {
    return false;
  }
  if (stamp === null || manifest === null || typeof manifest !== "object") return false;
  if (manifest.schema !== fmt.RUNTIME_SCHEMA) return false;
  const fields = Array.isArray(manifest.docs_fields) ? manifest.docs_fields : [];
  if (fields.length !== fmt.DOCS_FIELDS.length || fields.some((f, i) => f !== fmt.DOCS_FIELDS[i])) return false;

  // W-236: the section shards are stamped beside the document shards, under
  // `sections/<name>`, so a commit that rewrote only a section shard is seen.
  const paths = [...iterShardPaths(root), ...iterSectionPaths(root)];
  if (paths.length !== stamp.size) return false;
  for (const path of paths) {
    const entry = stamp.get(fmt.stampName(path));
    if (entry === undefined) return false;
    const st = statSync(path, { bigint: true });
    if (st.size !== entry[0] || st.mtimeNs !== entry[1]) return false;
  }
  return true;
}

//: A doc-table line's id, by pattern: `docs.jsonl` is canonical JSON with
//: sorted keys, and `id` is the first key named `id` (`accel.py::_DOC_ID_RE`).
const DOC_ID_RE = /"id":"((?:[^"\\]|\\.)*)"/;

/** The SCAN's section attachment, read from the derived plane (W-278 DoD 2) —
 *  `accel.py::attach_sections_by_id`. When the runtime is fresh, each
 *  sectioned candidate gets the `secs` the committed plane would give it, from
 *  `sections.json` and the per-term section postings. **Returns false,
 *  attaching nothing, when the runtime is stale or absent**; the scan then
 *  reads the committed plane itself. */
export function attachSectionsById(root, candidates, queryHashes) {
  const byId = new Map();
  for (const record of candidates) if (record.nsec) byId.set(record.id, record);
  if (byId.size === 0) return true;
  if (!isFresh(root)) return false;
  const directory = fmt.runtimeDir(root);
  const rows = JSON.parse(readFileSync(join(directory, fmt.SECTION_TABLE_NAME), "utf8")).rows;
  const lines = readFileSync(join(directory, fmt.DOCS_NAME), "utf8").split("\n");
  const ids = new Map();
  const byPrefix = new Map();
  const bags = new Map();
  for (const term of queryHashes) {
    const prefix = fmt.termPrefix(term);
    if (!byPrefix.has(prefix)) {
      const path = fmt.sectionPostingsPath(root, prefix);
      byPrefix.set(prefix, existsSync(path) ? JSON.parse(readFileSync(path, "utf8")) : {});
    }
    for (const [secidx, tf] of byPrefix.get(prefix)[term] ?? []) {
      const [docidx, k, flen] = rows[secidx];
      let docId = ids.get(docidx);
      if (docId === undefined) {
        const raw = DOC_ID_RE.exec(lines[docidx])[1];
        docId = raw.includes("\\") ? JSON.parse(`"${raw}"`) : raw;
        ids.set(docidx, docId);
      }
      if (!byId.has(docId)) continue;
      let bag = bags.get(docId);
      if (bag === undefined) { bag = new Map(); bags.set(docId, bag); }
      let entry = bag.get(k);
      if (entry === undefined) { entry = [[...flen], {}]; bag.set(k, entry); }
      entry[1][term] = [...tf];
    }
  }
  for (const [docId, bag] of bags) {
    byId.get(docId).secs = [...bag.keys()].sort((a, b) => a - b).map((k) => [k, ...bag.get(k)]);
  }
  return true;
}
