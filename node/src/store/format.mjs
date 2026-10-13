/** Constants and address functions for the committed store.
 *  Twin of `src/fux/store/format.py`. Pure and dependency-free. *
 * Owned, with its Python twin, by [SR-INDEX-LIFECYCLE](../../../records/0108_index-lifecycle.md).
 */
import { blake2bHex } from "../hash/blake2b.mjs";
import { fixed } from "../config/constants.mjs";

export const INDEX_DIR = fixed("index", "dir");
export const SCHEMA_ID = fixed("index", "schema");
export const ANALYZER_VERSION = fixed("index", "analyzer");

/** **Order is load-bearing** — body first, trailing zeros omitted on the wire.
 *  Reordering this changes every record and is a format bump, not a refactor. */
export const TF_FIELDS = fixed("index", "tf_fields");

const TERM_HASH_BYTES = fixed("index", "term_hash_bytes");
const CONTENT_SHA_BYTES = fixed("index", "content_sha_bytes");

const enc = new TextEncoder();

/** 16-hex (8-byte) blake2b digest of a term — the postings key. */
export function termHash(term) { return blake2bHex(enc.encode(term), TERM_HASH_BYTES); }

/** 40-hex (20-byte) blake2b digest of raw file bytes — the ledger `sha`. */
export function contentSha(bytes) { return blake2bHex(bytes, CONTENT_SHA_BYTES); }

/** 2-hex (1-byte) blake2b digest of the doc id — its shard bucket. */
export function shardFor(docId) { return blake2bHex(enc.encode(docId), 1); }

/** The title a verb shows.
 *
 * ⚠ **W-194, 2026-09-20 — this used to be the interesting function here.** It
 * carried the fallback a `meta: hashed` record needed: the title when plain,
 * else the display cache's materialised title, else a labelled opaque hash.
 * `meta`, `title_h` and the cache are deleted (since `_format` `v4`), so every
 * record carries a readable `title`. Kept as a function, with its Python twin,
 * because both candidate generators feed the same `rank()` and a display rule
 * implemented at each call site is a differential-law failure waiting to
 * happen. */
export function displayTitle(record) {
  return record.title ?? "";
}

// -- W-236: the section plane (SR-SECTIONS) -----------------------------------
//
// `.fux/index/sections/xx.jsonl`, one canonical line per section record, in the
// shard its PARENT document lives in (decision 4). A subdirectory rather than
// extra lines in the document shards, so every reader that lists `??.jsonl`
// under `.fux/index/` is untouched by construction (decision 1).

export const SECTIONS_DIR = fixed("index", "sections_dir");
export const SECTION_SEP = fixed("index", "section_sep");
/** The slots a section carries: a prefix of `TF_FIELDS` (SR-SECTIONS d3). */
export const SECTION_FIELDS = fixed("index", "section_fields");
export const SECTION_SLOTS = SECTION_FIELDS.length;
if (SECTION_FIELDS.some((f, i) => TF_FIELDS[i] !== f)) {
  throw new Error("section_fields must prefix tf_fields");
}

/** `<document id>#s<k>`, 1-based — the separator is appended LAST. */
export function sectionId(parent, k) { return `${parent}${SECTION_SEP}${k}`; }

/** The parent document id — Python's `rsplit(SECTION_SEP, 1)[0]`, so a `url:`
 *  id holding `#` still parses. */
export function sectionParent(secId) {
  const cut = secId.lastIndexOf(SECTION_SEP);
  return cut < 0 ? secId : secId.slice(0, cut);
}
