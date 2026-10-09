/** Reading the committed shards. Twin of `src/fux/store/reader.py`.
 *
 * 🔴 **Shards are read as Buffers and never as strings.** The scan's prefilter
 * is a substring match on RAW BYTES, and a line is JSON-parsed only on a hit.
 * `readFileSync().toString().split("\n")` allocates ~10 MB of UTF-16 per query
 * at 10 000 documents — that is how W-107's N4 fence (p95 <= 150 ms) gets
 * blown by a transcription that is otherwise perfectly correct.
 *
 * Owned, with its Python twin, by [SR-INDEX-LIFECYCLE](../../../records/0108_index-lifecycle.md).
 */
import { readFileSync, readdirSync, existsSync, statSync } from "node:fs";
import { join } from "node:path";
import {
  INDEX_DIR, SCHEMA_ID, ANALYZER_VERSION, TF_FIELDS, SECTIONS_DIR, sectionParent, shardFor,
} from "./format.mjs";

const NL = "\n".charCodeAt(0);

//: The whole shard-name grammar, suffix included — `reader.py::_SHARD_NAME_RE`.
//: ⚠ Was `endsWith(".jsonl")` until W-242: a stray `notes.jsonl` beside the
//: shards was scanned here and not by Python, and the derived plane's stamp
//: counts shards, so the two runtimes must agree on WHICH files are shards.
const SHARD_NAME_RE = /^[0-9a-f]{2}\.jsonl$/;

export function indexDir(root) { return join(root, INDEX_DIR); }

/** Shard paths in sorted order — order is load-bearing for `df` determinism. */
export function iterShardPaths(root) {
  const dir = indexDir(root);
  if (!existsSync(dir)) return [];
  return readdirSync(dir)
    .filter((f) => SHARD_NAME_RE.test(f) && statSync(join(dir, f)).isFile())
    .sort()
    .map((f) => join(dir, f));
}

/** `.fux/index/sections/` — W-236's plane (SR-SECTIONS decision 1). */
export function sectionsDir(root) { return join(root, INDEX_DIR, SECTIONS_DIR); }

/** The section plane's shard files, sorted — `reader.py::iter_section_paths`.
 *  Its own function, deliberately NOT folded into `iterShardPaths`: the plane
 *  lives in a subdirectory so that every document reader stays blind to it. */
export function iterSectionPaths(root) {
  const dir = sectionsDir(root);
  if (!existsSync(dir) || !statSync(dir).isDirectory()) return [];
  return readdirSync(dir)
    .filter((f) => SHARD_NAME_RE.test(f) && statSync(join(dir, f)).isFile())
    .sort()
    .map((f) => join(dir, f));
}

/** `k` in `<parent>#s<k>` — `reader.py::section_ordinal`, whose
 *  `lstrip("#s")` strips any run of `#` and `s` before the digits. */
export function sectionOrdinal(secId) {
  return Number(secId.slice(sectionParent(secId).length).replace(/^[#s]+/, ""));
}

/** The committed shards, each read AT MOST ONCE, for the life of ONE call.
 *
 * 🔴 **W-242 Tier 0.** A Node query read every shard three times — the scan,
 * `graphRecords` and `tableFromShards` each opened all of them, and every
 * `recordFor` opened one more (769 opens for 257 shards on this repo). One of
 * these is made where a call starts — a verb, a library method, one MCP tool
 * call — and handed down, so every consumer reads the same Buffers.
 *
 * ⚠ **Never module-level, and never outliving the call that made it — with
 * one owner who re-keys it.** `fux mcp` is long-lived and `ingest` rewrites the
 * index under it, so a set kept across calls would answer from an index that
 * no longer exists. Since W-249 the MCP server keeps ONE set across tool calls
 * through `verbs/mcp.mjs::Resident`, which re-keys it on `stamp.json` and every
 * shard's size and mtime before each call and drops it when either moves
 * (SR-MCP decision 13). Nothing else does. Lines stay raw Buffers (see the
 * header above), and `recordFor` re-parses on every call, so no caller can
 * mutate a record another caller holds.
 *
 * Node-only: `reader.py` has no twin because Python's graph lane reads
 * `graph.json` and its mined table has one reader per path, so it never had
 * the three-pass shape this removes (SR-NODE-SEARCH decision 24). */
export class Shards {
  constructor(root) {
    this.root = root;
    this._paths = null;
    this._lines = new Map();
    /** Disk reads made filling this set — a long-lived owner re-keys after a
     *  call that moved it (W-249). */
    this.reads = 0;
  }

  /** `iterShardPaths(root)`, listed once. */
  paths() {
    if (this._paths === null) {
      this._paths = iterShardPaths(this.root);
      this.reads += 1;
    }
    return this._paths;
  }

  /** `rawRecordLines(path)[1]`, read once per path. */
  lines(path) {
    let entry = this._lines.get(path);
    if (entry === undefined) {
      entry = rawRecordLines(path);
      this._lines.set(path, entry);
      this.reads += 1;
    }
    return entry[1];
  }
}

/** The caller's shard set, or a fresh one for a caller that brought none. */
export function shardsFor(root, shards) {
  return shards ?? new Shards(root);
}

export class IndexFormatError extends Error {}

/** The header line, refused rather than guessed at.
 *
 * A v1 shard silently mixed into a v2 read corrupts every `df` and is
 * undetectable at query time, so this is a REFUSAL. The message names both
 * versions because the fix ("upgrade the reader" vs "re-ingest") depends on
 * which way round they are. */
export function checkHeader(header, path) {
  if (header._format !== SCHEMA_ID) {
    throw new IndexFormatError(
      `${path}: index format is ${JSON.stringify(header._format)}, this reader speaks ` +
      `${JSON.stringify(SCHEMA_ID)}. Upgrade fux-engine, or re-ingest with a matching fux.`,
    );
  }
  if (header.analyzer !== ANALYZER_VERSION) {
    throw new IndexFormatError(
      `${path}: analyzer is ${JSON.stringify(header.analyzer)}, this reader speaks ` +
      `${JSON.stringify(ANALYZER_VERSION)}. Two analyzers in one index corrupt every df.`,
    );
  }
  const tf = header.tf_fields;
  if (!Array.isArray(tf) || tf.length !== TF_FIELDS.length || tf.some((f, i) => f !== TF_FIELDS[i])) {
    throw new IndexFormatError(
      `${path}: tf_fields is ${JSON.stringify(tf)}, expected ${JSON.stringify(TF_FIELDS)}. ` +
      `Field ORDER is load-bearing — a reordered tf array scores the wrong field.`,
    );
  }
  return header;
}

/** `[header, lines]` — the header parsed, the records left as raw Buffers. */
export function rawRecordLines(path) {
  const buf = readFileSync(path);
  const lines = [];
  // `indexOf`, not a JS loop over every byte: native, and on this repo's index
  // the loop was ~120 ms of every query (W-235).
  let start = 0;
  for (let i = buf.indexOf(NL, start); i !== -1; i = buf.indexOf(NL, start)) {
    if (i > start) lines.push(buf.subarray(start, i));
    start = i + 1;
  }
  if (start < buf.length) lines.push(buf.subarray(start));
  if (!lines.length) throw new IndexFormatError(`${path}: empty shard, no header line`);
  const header = checkHeader(JSON.parse(lines[0].toString("utf8")), path);
  return [header, lines.slice(1)];
}

/** One record by id, from its own shard. Display-time only — `rank()` never
 *  calls this, because ranking must stay a pure function of the record it was
 *  already handed. `shards` is the call's `Shards` (W-242 Tier 0). */
export function recordFor(root, docId, shards = null) {
  const shard = shardFor(docId);
  const path = join(indexDir(root), `${shard}.jsonl`);
  const set = shardsFor(root, shards);
  if (!set.paths().includes(path)) return null;
  const lines = set.lines(path);
  const needle = Buffer.from(JSON.stringify(docId), "utf8");
  for (const line of lines) {
    if (!line.includes(needle)) continue;
    const record = JSON.parse(line.toString("utf8"));
    if (record.id === docId) return record;
  }
  return null;
}

const QUOTE = 0x22, BACKSLASH = 0x5c, COLON = 0x3a, COMMA = 0x2c;
const LBRACE = 0x7b, RBRACE = 0x7d, LBRACK = 0x5b, RBRACK = 0x5d;
const WANTED = new Set(["id", "edges"]);

function skipWs(buf, i) {
  while (i < buf.length && (buf[i] === 0x20 || buf[i] === 0x09 || buf[i] === 0x0a || buf[i] === 0x0d)) i++;
  return i;
}

/** Index of the quote that closes the string opening at `i`. */
function stringEnd(buf, i) {
  let j = i + 1;
  for (;;) {
    const k = buf.indexOf(QUOTE, j);
    if (k === -1) throw new IndexFormatError("unterminated string");
    let slashes = 0;
    while (buf[k - 1 - slashes] === BACKSLASH) slashes++;
    if (slashes % 2 === 0) return k;
    j = k + 1;
  }
}

/** Index just past the JSON value starting at `i`. */
function valueEnd(buf, i) {
  let depth = 0;
  for (; i < buf.length; i++) {
    const c = buf[i];
    if (c === QUOTE) {
      i = stringEnd(buf, i);
      if (depth === 0) return i + 1;
    } else if (c === LBRACE || c === LBRACK) {
      depth++;
    } else if (c === RBRACE || c === RBRACK) {
      if (depth === 0) return i;
      if (--depth === 0) return i + 1;
    } else if (depth === 0 && c === COMMA) {
      return i;
    }
  }
  return i;
}

/** `{id, edges}` from one raw record line, parsing those two values alone.
 *  Returns `null` when the line is not the flat object this expects. */
function skimGraphFields(line) {
  const out = {};
  let found = 0;
  let i = skipWs(line, 0);
  if (line[i] !== LBRACE) return null;
  i = skipWs(line, i + 1);
  while (i < line.length && line[i] !== RBRACE) {
    if (line[i] !== QUOTE) return null;
    const keyEnd = stringEnd(line, i);
    const key = JSON.parse(line.toString("utf8", i, keyEnd + 1));
    i = skipWs(line, keyEnd + 1);
    if (line[i] !== COLON) return null;
    const start = skipWs(line, i + 1);
    const end = valueEnd(line, start);
    if (WANTED.has(key)) {
      out[key] = JSON.parse(line.toString("utf8", start, end));
      if (++found === WANTED.size) return out;
    }
    i = skipWs(line, end);
    if (line[i] === COMMA) i = skipWs(line, i + 1);
  }
  return "id" in out ? out : null;
}

/** Every committed record, reduced to the two fields the graph plane reads:
 *  `id` and `edges`.
 *
 * 🔴 **Why not `JSON.parse` every line.** The plane needs every record, and a
 * record is ~95 % `terms` by bytes. Materialising those maps for 13 000
 * records, then collecting them, was ~80 % of a Node `find` on this repo
 * (W-235). The writer sorts keys, so `edges` and `id` sit before `terms` and
 * the skim stops there; an unsorted line is still read correctly, only slower.
 * A line the skim does not recognise falls back to a full parse, so the result
 * never differs from `JSON.parse` — only its cost does. */
export function graphRecords(root, shards = null) {
  const out = [];
  const set = shardsFor(root, shards);
  for (const path of set.paths()) {
    const lines = set.lines(path);
    for (const line of lines) {
      let record = null;
      try { record = skimGraphFields(line); } catch { record = null; }
      if (record === null) {
        const full = JSON.parse(line.toString("utf8"));
        record = { id: full.id, edges: full.edges };
      }
      out.push(record);
    }
  }
  return out;
}
