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
