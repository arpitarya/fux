/** On-disk shapes for the derived T1 accelerator. Twin of `src/fux/derive/format.py`.
 *
 * Everything here lives under `.fux/runtime/` — derived, gitignored, rebuildable
 * from the committed shards alone. **Python's layout is the contract** (W-242):
 * no file, field or schema string is Node's to change, and every name below is
 * read from `src/fux/constants.toml`, the file `format.py` reads (L12).
 *
 * The offset table's 62-byte entry is `<8sHQI` + `5H` + `5I` + `IIH`,
 * little-endian, no padding — `format.py`'s `ENTRY_STRUCT`. It is decoded with a
 * `DataView`, field by field in that order. ⚠ **A transposed field is a silent
 * miss, not an error**, which is why both suites read one committed fixture
 * (`tests/derive/idx-fixture.*`).
 *
 * Owned, with its Python twin, by [SR-T1-ACCELERATOR](../../../records/0110_accelerator.md).
 */
import { join } from "node:path";
import { fixed } from "../config/constants.mjs";

export const RUNTIME_DIR = fixed("runtime", "dir");
export const BLOCK_SIZE = fixed("runtime", "block_size");
export const RUNTIME_SCHEMA = fixed("runtime", "schema");
export const DOCS_FIELDS = fixed("runtime", "docs_fields");
export const DOCS_NAME = fixed("runtime", "docs");
export const ANCHORS_DIR = fixed("runtime", "anchors_dir");
export const STATS_NAME = fixed("runtime", "stats");
export const MINED_NAME = fixed("runtime", "mined");
export const MANIFEST_NAME = fixed("runtime", "manifest");
export const STAMP_NAME = fixed("runtime", "stamp");
export const POSTINGS_DIR = fixed("runtime", "postings_dir");
export const GRAPH_NAME = fixed("graph", "file");
/** Files whose bytes must be identical across two builds — `stamp.json` excluded. */
export const DETERMINISTIC_FILES = [DOCS_NAME, STATS_NAME, MINED_NAME, MANIFEST_NAME, GRAPH_NAME];

const FIELD_COUNT = fixed("index", "tf_fields").length;
export const TERM_BYTES = fixed("index", "term_hash_bytes");
const PREFIX_CHARS = fixed("radix", "hex_digits_per_byte");

//: Byte widths of the struct codes `format.py` packs with: `s` per byte, `H`,
//: `I`, `Q`. They are the codes' definitions in Python's `struct` module, so
//: they move only if the layout string does.
const U16 = Uint16Array.BYTES_PER_ELEMENT;
const U32 = Uint32Array.BYTES_PER_ELEMENT;
const U64 = BigUint64Array.BYTES_PER_ELEMENT;

/** `ENTRY_STRUCT.size` — 62 at five fields and eight-byte hashes. */
export const ENTRY_SIZE = TERM_BYTES + U16 + U64 + U32 + FIELD_COUNT * U16 + FIELD_COUNT * U32 + U32 + U32 + U16;

const FUXDIR = fixed("fuxdir", "dir");

export function runtimeDir(root) { return join(root, FUXDIR, RUNTIME_DIR); }
export function postingsDir(root) { return join(runtimeDir(root), POSTINGS_DIR); }
export function anchorsDir(root) { return join(runtimeDir(root), ANCHORS_DIR); }
export function anchorsPath(root, prefix) { return join(anchorsDir(root), `${prefix}.json`); }
export function postingsPath(root, prefix) { return join(postingsDir(root), `${prefix}.jsonl`); }
export function offsetsPath(root, prefix) { return join(postingsDir(root), `${prefix}.idx`); }

/** Postings shard for a term — its hash's first byte, as hex. */
export function termPrefix(termHash) { return termHash.slice(0, PREFIX_CHARS); }

/** The raw term key of entry `index`, as hex — what `blocks_for` bisects on. */
export function entryTermHex(buf, index) {
  const at = buf.byteOffset + index * ENTRY_SIZE;
  return Buffer.from(buf.buffer, at, TERM_BYTES).toString("hex");
}

/** `unpack_entry`: `[termHex, blockNo, offset, length, mx, mnw, first, last, count]`.
 *
 * `offset` is a `u64` and is returned as a `Number`: a postings shard past
 * 2^53 bytes is not a file this format writes, and `slice` takes a `Number`. */
export function unpackEntry(buf, index) {
  const view = new DataView(buf.buffer, buf.byteOffset + index * ENTRY_SIZE, ENTRY_SIZE);
  let at = 0;
  const term = Buffer.from(buf.buffer, buf.byteOffset + index * ENTRY_SIZE, TERM_BYTES).toString("hex");
  at += TERM_BYTES;
  const blockNo = view.getUint16(at, true); at += U16;
  const offset = Number(view.getBigUint64(at, true)); at += U64;
  const length = view.getUint32(at, true); at += U32;
  const mx = [];
  for (let i = 0; i < FIELD_COUNT; i++) { mx.push(view.getUint16(at, true)); at += U16; }
  const mnw = [];
  for (let i = 0; i < FIELD_COUNT; i++) { mnw.push(view.getUint32(at, true)); at += U32; }
  const first = view.getUint32(at, true); at += U32;
  const last = view.getUint32(at, true); at += U32;
  const count = view.getUint16(at, true);
  return [term, blockNo, offset, length, mx, mnw, first, last, count];
}

/** `pack_entry` — the inverse, for the Node build (Tier 2). */
export function packEntry(termHex, blockNo, offset, length, mx, mnw, first, last, count) {
  const out = Buffer.alloc(ENTRY_SIZE);
  const view = new DataView(out.buffer, out.byteOffset, ENTRY_SIZE);
  Buffer.from(termHex, "hex").copy(out, 0);
  let at = TERM_BYTES;
  view.setUint16(at, blockNo, true); at += U16;
  view.setBigUint64(at, BigInt(offset), true); at += U64;
  view.setUint32(at, length, true); at += U32;
  for (let i = 0; i < FIELD_COUNT; i++) { view.setUint16(at, mx[i], true); at += U16; }
  for (let i = 0; i < FIELD_COUNT; i++) { view.setUint32(at, mnw[i], true); at += U32; }
  view.setUint32(at, first, true); at += U32;
  view.setUint32(at, last, true); at += U32;
  view.setUint16(at, count, true);
  return out;
}
