/** The scan's section attachment — SR-SECTIONS decision 7 (W-278).
 *
 * Twin of `src/fux/query/sections.py`. Attaches `secs` to each sectioned
 * candidate; scores nothing (`rank.mjs` does). The derived plane when the
 * runtime is fresh, the committed plane by pattern otherwise; one result.
 *
 * Owned by [SR-SECTIONS](../../../records/0161_sections.md).
 */
import { existsSync, readFileSync } from "node:fs";
import { basename, join } from "node:path";
import { iterSectionPaths, sectionOrdinal, shardsFor } from "../store/reader.mjs";
import { sectionParent, shardFor } from "../store/format.mjs";
import * as fmt from "../derive/format.mjs";
import { isFresh } from "../derive/fresh.mjs";

//: A line's id, off the raw text — a section line and a `docs.jsonl` line
//: alike (`sections.py::_ID_RE`). Global, so a search can start at an offset.
const ID_RE = /"id":"((?:[^"\\]|\\.)*)"/g;
//: A line's `flen` (`sections.py::_FLEN_RE`), global for the same reason.
const FLEN_AT_RE = /"flen":\[([0-9,\s]*)\]/g;

/** Attach `secs` to every sectioned candidate: the derived plane when fresh,
 *  the committed plane otherwise. `shards` is the call's set (W-242 Tier 0), so
 *  a `-q` fusion's second phrasing reads no section shard a second time. */
export function attach(root, candidates, queryHashes, shards = null) {
  if (!fromRuntime(root, candidates, queryHashes)) fromCommitted(root, candidates, queryHashes, shardsFor(root, shards));
}

/** `sections.py::_from_runtime` (W-278 DoD 2). When the runtime is fresh, each
 *  sectioned candidate gets the `secs` the committed plane would give it, from
 *  `sections.json` and the per-term section postings. **Returns false,
 *  attaching nothing, when the runtime is stale or absent**; the scan then
 *  reads the committed plane itself. */
function fromRuntime(root, candidates, queryHashes) {
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
        ID_RE.lastIndex = 0;
        const raw = ID_RE.exec(lines[docidx])[1];
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

/** `sections.py::_from_committed`. Only the section shards that hold a
 *  sectioned candidate's sections are read; each query term's `"<hash>":[`
 *  entry is found in the shard's text directly, so a line with no query term
 *  is never visited, and one that does yields its id, `flen` and the query's
 *  own `terms` entries by position — never a whole-line parse. */
function fromCommitted(root, candidates, queryHashes, set) {
  const byId = new Map();
  for (const record of candidates) if (record.nsec) byId.set(record.id, record);
  if (byId.size === 0) return;
  const shards = new Set([...byId.keys()].map((id) => shardFor(id)));
  const keys = queryHashes.map((h) => [h, `"${h}":[`]);
  const bags = new Map();
  for (const path of iterSectionPaths(root)) {
    if (!shards.has(basename(path, ".jsonl"))) continue;
    const lines = set.lines(path);
    const data = lines.map((line) => line.toString("utf8")).join("\n");
    const found = new Map();
    for (const [h, key] of keys) {
      let at = data.indexOf(key);
      while (at !== -1) {
        const start = data.lastIndexOf("\n", at) + 1;
        const open = at + key.length;
        const close = data.indexOf("]", open);
        let hits = found.get(start);
        if (hits === undefined) { hits = {}; found.set(start, hits); }
        hits[h] = data.slice(open, close).split(",").map(Number);
        at = data.indexOf(key, close);
      }
    }
    for (const [start, hits] of found) {
      ID_RE.lastIndex = start;
      const raw = ID_RE.exec(data)[1];
      const secId = raw.includes("\\") ? JSON.parse(`"${raw}"`) : raw;
      const parent = sectionParent(secId);
      if (!byId.has(parent)) continue;
      FLEN_AT_RE.lastIndex = start;
      const inner = FLEN_AT_RE.exec(data)[1].trim();
      const flen = inner ? inner.split(",").map(Number) : [];
      const terms = {};
      for (const h of queryHashes) if (h in hits) terms[h] = hits[h];
      let bag = bags.get(parent);
      if (bag === undefined) { bag = []; bags.set(parent, bag); }
      bag.push([sectionOrdinal(secId), flen, terms]);
    }
  }
  for (const [parent, bag] of bags) {
    bag.sort((a, b) => a[0] - b[0]);
    byId.get(parent).secs = bag;
  }
}
