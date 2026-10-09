/** Build the derived T1 accelerator from the committed shards alone.
 *  Twin of `src/fux/derive/_build.py` (W-242 Tier 2).
 *
 * **The output is Python's, byte for byte**, on every file but `stamp.json`
 * (mtimes are not reproducible by construction): every `DETERMINISTIC_FILES`
 * member, every `postings/*.jsonl` and `*.idx`, every `anchors/*.json`. Every
 * serializer below is `json.dumps` with the arguments `_build.py` passes it
 * (`compat/pyjson.mjs`), every sort is by code point, and the files are written
 * in `_build.py`'s order — the stamp after everything else, as there.
 *
 * The committed shards are the ONLY input ([SR-T1-ACCELERATOR](../../../records/0110_accelerator.md)
 * decision 1), and the two build invariants refuse the build exactly as
 * `_assert_invariants` does (decision 7) — never a divergent plane.
 *
 * Owned, with its Python twin, by SR-T1-ACCELERATOR.
 */
import { mkdirSync, readFileSync, readdirSync, statSync, unlinkSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { FuxError } from "../errors.mjs";
import { fixed } from "../config/constants.mjs";
import { cmpCodePoints } from "../compat/pyfloat.mjs";
import { pyDumps } from "../compat/pyjson.mjs";
import { iterSectionPaths, iterShardPaths, rawRecordLines, sectionOrdinal } from "../store/reader.mjs";
import {
  TF_FIELDS, SECTION_SLOTS, contentSha, displayTitle, sectionId, sectionParent,
} from "../store/format.mjs";
import { derivedDir } from "../store/cachedir.mjs";
import { buildPlane, SCHEMA as GRAPH_SCHEMA } from "../graph/plane.mjs";
import * as fmt from "./format.mjs";
import * as docstable from "./docstable.mjs";
import * as manifest from "./manifest.mjs";
import * as stamp from "./stamp.mjs";
import * as statsPlane from "./stats.mjs";

const FIELD_COUNT = TF_FIELDS.length;
const HEADER_LINES = fixed("index", "shard_header_lines");
//: `mx` is a u16 and `mnw` a u32 in the offset table (`format.py::ENTRY_STRUCT`).
const MAX_TF = 2 ** (Uint16Array.BYTES_PER_ELEMENT * 8) - 1;
const MAX_LEN = 2 ** (Uint32Array.BYTES_PER_ELEMENT * 8) - 1;

const QUOTED_HASH_RE = /"([0-9a-f]{16})"/g;
const FLEN_RE = /"flen":\[([0-9,\s]*)\]/;

function regexFlen(text) {
  const m = FLEN_RE.exec(text);
  if (m === null) return null;
  const inner = m[1].trim();
  return inner ? inner.split(",").map((part) => Number(part.trim())) : [];
}

function pyRepr(value) { return JSON.stringify(value) ?? "None"; }

/** `_assert_invariants` — refuse a plane that could disagree with the scan. */
function assertInvariants(path, lineno, text, record) {
  const termKeys = new Set(Object.keys(record.terms ?? {}));
  for (const edge of record.edges ?? []) for (const term of Object.keys(edge.at ?? {})) termKeys.add(term);
  for (const [short, long] of record.abbr ?? []) for (const term of [...short, ...long]) termKeys.add(term);
  const stray = [];
  QUOTED_HASH_RE.lastIndex = 0;
  let m;
  while ((m = QUOTED_HASH_RE.exec(text)) !== null) if (!termKeys.has(m[1])) stray.push(m[1]);
  if (stray.length) {
    const example = stray.sort()[0];
    throw new FuxError(
      `${path}:${lineno}: the quoted 16-hex token '${example}' appears outside \`terms\` in ` +
      `record ${pyRepr(record.id)}. \`query/scan.py\` counts it toward that term's df from ` +
      "the raw bytes, and the accelerator counts from the postings, so the two paths would " +
      "score this corpus differently. Refusing to build a divergent accelerator.",
    );
  }
  for (const edge of record.edges ?? []) {
    const hasAt = edge.at !== undefined && edge.at !== null;
    const hasAl = edge.al !== undefined && edge.al !== null;
    if (hasAt !== hasAl) {
      throw new FuxError(
        `${path}:${lineno}: record ${pyRepr(record.id)} has an edge to ${pyRepr(edge.dst)} carrying ` +
        `${hasAl ? "at" : "al"} without the other. Anchor terms and their token count are ` +
        "written together or not at all. Re-run `fux ingest --full`.",
      );
    }
    if (hasAt) {
      const sum = Object.values(edge.at).reduce((a, b) => a + b, 0);
      if (edge.al !== sum) {
        throw new FuxError(
          `${path}:${lineno}: record ${pyRepr(record.id)} has an edge to ${pyRepr(edge.dst)} with ` +
          `al=${edge.al} but its anchor terms sum to ${sum}. \`query/scan.py\` reads \`al\` off the ` +
          "raw bytes and the accelerator sums `at`; the two feed the same `avg_wlen`. Refusing to build.",
        );
      }
    }
  }
  const fromRegex = regexFlen(text);
  const parsed = "flen" in record ? [...record.flen] : null;
  if (JSON.stringify(fromRegex) !== JSON.stringify(parsed)) {
    throw new FuxError(
      `${path}:${lineno}: record ${pyRepr(record.id)} has flen ${pyRepr(parsed)} but the ` +
      `byte-level regex reads ${pyRepr(fromRegex)}. \`query/scan.py\` derives avg_wlen from the ` +
      "regex and scores from the parse; they must agree. Refusing to build.",
    );
  }
}

/** `_read_committed` — one pass over the shards. */
function readCommitted(root) {
  const records = [];
  let totalDocs = 0;
  const totalFlen = new Array(FIELD_COUNT).fill(0);
  const shardStamp = [];
  for (const path of iterShardPaths(root)) {
    const raw = readFileSync(path);
    const st = statSync(path, { bigint: true });
    shardStamp.push([fmt.stampName(path), contentSha(raw), st.size, st.mtimeNs]);
    const [, lines] = rawRecordLines(path);
    let lineno = HEADER_LINES + 1;
    for (const line of lines) {
      totalDocs++;
      const record = JSON.parse(line.toString("utf8"));
      const text = line.toString("latin1");
      assertInvariants(path, lineno, text, record);
      const flen = regexFlen(text);
      if (flen !== null) flen.forEach((v, i) => { totalFlen[i] += v; });
      records.push(record);
      lineno++;
    }
  }
  records.sort((a, b) => cmpCodePoints(a.id, b.id));
  const sectionLines = readSectionPlane(root, shardStamp);

  const docs = records.map((r) => ({
    id: r.id,
    loc: r.loc,
    title: displayTitle(r),
    flen: [...(r.flen ?? [])],
    archived: Boolean(r.archived),
    superseded: Boolean(r.superseded),
    mtime: r.mtime ?? null,
    // W-236: how many section records this document has; 0 is sectionless.
    // Carried off the record, checked against the plane just below.
    nsec: Number(r.nsec ?? 0),
  }));
  const sections = sectionPlanes(docs, sectionLines);

  const postings = new Map();
  records.forEach((record, docidx) => {
    for (const [term, tf] of Object.entries(record.terms ?? {})) {
      let list = postings.get(term);
      if (list === undefined) { list = []; postings.set(term, list); }
      list.push([docidx, [...tf]]);
    }
  });

  const anchorLen = new Map();
  const anchorPostings = new Map();
  for (const record of records) {
    for (const edge of record.edges ?? []) {
      const at = edge.at;
      if (!at || !Object.keys(at).length) continue;
      anchorLen.set(edge.dst, (anchorLen.get(edge.dst) ?? 0) + Number(edge.al));
      for (const [term, count] of Object.entries(at)) {
        let bag = anchorPostings.get(term);
        if (bag === undefined) { bag = new Map(); anchorPostings.set(term, bag); }
        bag.set(edge.dst, (bag.get(edge.dst) ?? 0) + count);
      }
    }
  }
  for (const doc of docs) doc.alen = anchorLen.get(doc.id) ?? 0;
  const docidxOf = new Map(docs.map((doc, i) => [doc.id, i]));
  const anchors = new Map();
  for (const term of [...anchorPostings.keys()].sort(cmpCodePoints)) {
    const entries = [];
    for (const [dst, count] of anchorPostings.get(term)) {
      if (docidxOf.has(dst)) entries.push([docidxOf.get(dst), count]);
    }
    if (entries.length) {
      entries.sort((a, b) => (a[0] - b[0]) || (a[1] - b[1]));
      anchors.set(term, entries);
    }
  }
  let totalAnchorLen = 0;
  for (const v of anchorLen.values()) totalAnchorLen += v;
  const stats = statsPlane.payload({
    n: totalDocs, totalFlen, totalAnchorLen,
    secUnits: sections.units, secTotalFlen: sections.totalFlen,
  });
  return { docs, postings, anchors, stats, shardStamp, records, sections };
}

/** `_read_section_plane` — every committed section line, as
 *  `[parent, k, flen, terms]`, stamped beside the document shards. Each line's
 *  byte-level `flen` must equal its parsed `flen`, because the scan reads it
 *  off the bytes. */
function readSectionPlane(root, shardStamp) {
  const out = [];
  for (const path of iterSectionPaths(root)) {
    const raw = readFileSync(path);
    const st = statSync(path, { bigint: true });
    shardStamp.push([fmt.stampName(path), contentSha(raw), st.size, st.mtimeNs]);
    const [, lines] = rawRecordLines(path);
    let lineno = HEADER_LINES + 1;
    for (const line of lines) {
      const record = JSON.parse(line.toString("utf8"));
      const fromRegex = regexFlen(line.toString("latin1")) ?? [];
      const parsed = [...(record.flen ?? [])];
      if (FLEN_RE.exec(line.toString("latin1")) === null || JSON.stringify(fromRegex) !== JSON.stringify(parsed)) {
        throw new FuxError(
          `${path}:${lineno}: section ${pyRepr(record.id)} has flen ` +
          `${pyRepr(record.flen ?? null)} but the byte-level regex reads ${pyRepr(fromRegex)}. ` +
          "Refusing to build.",
        );
      }
      out.push([sectionParent(record.id), sectionOrdinal(record.id), fromRegex, record.terms ?? {}]);
      lineno++;
    }
  }
  return out;
}

/** `_section_planes` — the section table, its postings and its statistics,
 *  and the two planes held together: a section line with no parent, or a
 *  document whose `nsec` is not its count of section lines, refuses the build
 *  (SR-SECTIONS decision 9). A SECTIONLESS document counts as its own single
 *  section over its body and heading slots, as the scan sums it. */
function sectionPlanes(docs, sectionLines) {
  const docidxOf = new Map(docs.map((doc, i) => [doc.id, i]));
  const counts = new Map();
  const rows = [];
  for (const [parent, k, flen, terms] of sectionLines) {
    const idx = docidxOf.get(parent);
    if (idx === undefined) {
      throw new FuxError(
        `the section plane holds ${pyRepr(sectionId(parent, k))}, whose document ` +
        `${pyRepr(parent)} is not in the index. The two planes disagree; run \`fux ingest\` ` +
        "to rewrite both. Refusing to build.",
      );
    }
    counts.set(parent, (counts.get(parent) ?? 0) + 1);
    rows.push([idx, k, flen, terms]);
  }
  for (const doc of docs) {
    const held = counts.get(doc.id) ?? 0;
    if (doc.nsec !== held) {
      throw new FuxError(
        `${pyRepr(doc.id)} declares nsec=${doc.nsec} but the section plane holds ` +
        `${held} section(s) for it. The two planes disagree; run ` +
        "`fux ingest` to rewrite both. Refusing to build.",
      );
    }
  }
  rows.sort((a, b) => (a[0] - b[0]) || (a[1] - b[1]));
  const totalFlen = new Array(SECTION_SLOTS).fill(0);
  const postings = new Map();
  rows.forEach(([, , flen, terms], secidx) => {
    for (let i = 0; i < Math.min(flen.length, SECTION_SLOTS); i++) totalFlen[i] += flen[i];
    for (const [term, tf] of Object.entries(terms)) {
      let list = postings.get(term);
      if (list === undefined) { list = []; postings.set(term, list); }
      list.push([secidx, [...tf]]);
    }
  });
  let sectionless = 0;
  for (const doc of docs) {
    if (doc.nsec !== 0) continue;
    sectionless++;
    for (let i = 0; i < Math.min(doc.flen.length, SECTION_SLOTS); i++) totalFlen[i] += doc.flen[i];
  }
  return {
    rows: rows.map(([idx, k, flen]) => [idx, k, [...flen]]),
    postings,
    units: rows.length + sectionless,
    totalFlen,
  };
}

/** `_write_sections` — `sections.json` and `sections/<prefix>.json`. */
function writeSections(root, directory, sections) {
  fmt.writeJson(join(directory, fmt.SECTION_TABLE_NAME), { rows: sections.rows });
  const byPrefix = new Map();
  for (const term of [...sections.postings.keys()].sort(cmpCodePoints)) {
    const prefix = fmt.termPrefix(term);
    if (!byPrefix.has(prefix)) byPrefix.set(prefix, new Map());
    byPrefix.get(prefix).set(term, sections.postings.get(term).map(([secidx, tf]) => [secidx, tf]));
  }
  for (const [prefix, payload] of byPrefix) fmt.writeJson(fmt.sectionPostingsPath(root, prefix), payload);
}

function cmpSide(a, b) {
  const n = Math.min(a.length, b.length);
  for (let i = 0; i < n; i++) { const c = cmpCodePoints(a[i], b[i]); if (c) return c; }
  return a.length - b.length;
}

/** `mined.table_from_records` — the sorted, de-duplicated `(short, long)` set. */
function minedTableFromRecords(records) {
  const seen = new Map();
  for (const record of records) {
    for (const [short, long] of record.abbr ?? []) seen.set(JSON.stringify([short, long]), [[...short], [...long]]);
  }
  return [...seen.values()].sort((a, b) => cmpSide(a[0], b[0]) || cmpSide(a[1], b[1]));
}

function perFieldMax(block) {
  const out = new Array(FIELD_COUNT).fill(0);
  for (const [, tf] of block) tf.forEach((count, i) => { if (count > out[i]) out[i] = count; });
  for (const value of out) {
    if (value > MAX_TF) {
      throw new FuxError(
        `term frequency ${value} exceeds the u16 the offset table packs. ` +
        "A truncated `mx` under-estimates the block bound and loses documents, " +
        "so the build refuses rather than writing one.",
      );
    }
  }
  return out;
}

function perFieldMinLen(block, flens) {
  const out = new Array(FIELD_COUNT).fill(MAX_LEN);
  for (const [docidx] of block) {
    const flen = flens[docidx];
    for (let i = 0; i < FIELD_COUNT; i++) {
      const value = i < flen.length ? flen[i] : 0;
      if (value < out[i]) out[i] = value;
    }
  }
  return out.map((v) => (v === MAX_LEN ? 0 : v));
}

function writePostings(root, postings, flens) {
  const byPrefix = new Map();
  for (const term of [...postings.keys()].sort(cmpCodePoints)) {
    const prefix = fmt.termPrefix(term);
    if (!byPrefix.has(prefix)) byPrefix.set(prefix, []);
    byPrefix.get(prefix).push(term);
  }
  let totalBlocks = 0;
  let totalPostings = 0;
  for (const [prefix, terms] of byPrefix) {
    const lines = [];
    const entries = [];
    let offset = 0;
    for (const term of terms) {
      const list = postings.get(term);
      totalPostings += list.length;
      for (let start = 0, blockNo = 0; start < list.length; start += fmt.BLOCK_SIZE, blockNo++) {
        const block = list.slice(start, start + fmt.BLOCK_SIZE);
        const line = Buffer.from(pyDumps([term, block], { sortKeys: false, ensureAscii: false }), "utf8");
        entries.push(fmt.packEntry(
          term, blockNo, offset, line.length,
          perFieldMax(block), perFieldMinLen(block, flens),
          block[0][0], block[block.length - 1][0], block.length,
        ));
        lines.push(line);
        offset += line.length + 1;
        totalBlocks++;
      }
    }
    const newline = Buffer.from("\n");
    writeFileSync(fmt.postingsPath(root, prefix), Buffer.concat([...lines.flatMap((l) => [l, newline]).slice(0, -1), newline]));
    writeFileSync(fmt.offsetsPath(root, prefix), Buffer.concat(entries));
  }
  return [totalBlocks, totalPostings];
}

function writeAnchors(root, anchors) {
  const byPrefix = new Map();
  for (const term of [...anchors.keys()].sort(cmpCodePoints)) {
    const prefix = fmt.termPrefix(term);
    if (!byPrefix.has(prefix)) byPrefix.set(prefix, new Map());
    byPrefix.get(prefix).set(term, anchors.get(term).map(([idx, count]) => [idx, count]));
  }
  for (const prefix of [...byPrefix.keys()].sort(cmpCodePoints)) fmt.writeJson(fmt.anchorsPath(root, prefix), byPrefix.get(prefix));
}

/** `graph/plane.py::build_plane`'s bytes: `sort_keys=False`, `ensure_ascii=True`. */
function writeGraph(directory, records) {
  const plane = buildPlane(records);
  const communities = new Map();
  for (const node of [...plane.communities.keys()].sort(cmpCodePoints)) communities.set(node, plane.communities.get(node));
  const payload = new Map([
    ["schema", GRAPH_SCHEMA],
    ["edges", plane.graph.edges.map((e) => [e.src, e.kind, e.dst, e.grade])],
    ["communities", communities],
  ]);
  writeFileSync(join(directory, fmt.GRAPH_NAME), Buffer.from(pyDumps(payload, { sortKeys: false, ensureAscii: true }) + "\n", "utf8"));
}

function clear(directory) {
  for (const name of readdirSync(directory)) {
    const path = join(directory, name);
    if (statSync(path).isFile()) unlinkSync(path);
  }
}

/** Materialize `.fux/runtime/` from the committed index. Returns the report. */
export function build(root) {
  const { docs, postings, anchors, stats, shardStamp, records, sections } = readCommitted(root);

  const directory = derivedDir(root, fmt.RUNTIME_DIR);
  const postingsDirectory = join(directory, fmt.POSTINGS_DIR);
  mkdirSync(postingsDirectory, { recursive: true });
  clear(postingsDirectory);
  const anchorsDirectory = join(directory, fmt.ANCHORS_DIR);
  mkdirSync(anchorsDirectory, { recursive: true });
  clear(anchorsDirectory);
  const sectionDirectory = join(directory, fmt.SECTIONS_RT_DIR);
  mkdirSync(sectionDirectory, { recursive: true });
  clear(sectionDirectory);

  docstable.write(directory, docs);
  statsPlane.write(directory, stats);
  fmt.writeJson(join(directory, fmt.MINED_NAME), { pairs: minedTableFromRecords(records) });
  writeGraph(directory, records);

  const [blocks, postingsCount] = writePostings(root, postings, docs.map((d) => d.flen));
  writeAnchors(root, anchors);
  writeSections(root, directory, sections);

  manifest.write(directory, { docs: docs.length, terms: postings.size, blocks, shardStamp });
  // Last, and volatile on purpose: a reader racing this build sees no stamp or
  // the old one, and `isFresh` sends it to the scan rather than a half-plane.
  stamp.write(directory, shardStamp);

  return { docs: docs.length, terms: postings.size, blocks, postings: postingsCount };
}
