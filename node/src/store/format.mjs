/** Constants and address functions for the committed store.
 *  Twin of `src/fux/store/format.py`. Pure and dependency-free. */
import { blake2bHex } from "../hash/blake2b.mjs";

export const INDEX_DIR = ".fux/index";
export const SCHEMA_ID = "fux.index.v2";
export const ANALYZER_VERSION = "v2";

/** **Order is load-bearing** — body first, trailing zeros omitted on the wire.
 *  Reordering this changes every record and is a format bump, not a refactor. */
export const TF_FIELDS = ["body", "heading", "title", "path", "ctx"];

export const TITLE_HASH_PREFIX = "h:";

const enc = new TextEncoder();

/** 16-hex (8-byte) blake2b digest of a term — the postings key. */
export function termHash(term) { return blake2bHex(enc.encode(term), 8); }

/** 40-hex (20-byte) blake2b digest of raw file bytes — the ledger `sha`. */
export function contentSha(bytes) { return blake2bHex(bytes, 20); }

/** 2-hex (1-byte) blake2b digest of the doc id — its shard bucket. */
export function shardFor(docId) { return blake2bHex(enc.encode(docId), 1); }

/** The title a verb shows. `rank()`'s call site passes no cache, so that path
 *  always returns the bare hash — ranking stays a pure function of the record. */
export function displayTitle(record, cache = null) {
  const title = record.title;
  if (title !== undefined && title !== null) return title;
  let hexpart = record.title_h || "";
  if (hexpart.startsWith(TITLE_HASH_PREFIX)) hexpart = hexpart.slice(TITLE_HASH_PREFIX.length);
  if (cache === null) return hexpart;
  const materialised = cache.get(record.sha || "");
  if (materialised !== null && materialised !== undefined) return materialised;
  return `${hexpart} (uncached — title unavailable)`;
}
