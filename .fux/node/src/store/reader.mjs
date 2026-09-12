/** Reading the committed shards. Twin of `src/fux/store/reader.py`.
 *
 * 🔴 **Shards are read as Buffers and never as strings.** The scan's prefilter
 * is a substring match on RAW BYTES, and a line is JSON-parsed only on a hit.
 * `readFileSync().toString().split("\n")` allocates ~10 MB of UTF-16 per query
 * at 10 000 documents — that is how W-107's N4 fence (p95 <= 150 ms) gets
 * blown by a transcription that is otherwise perfectly correct.
 */
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { join } from "node:path";
import { INDEX_DIR, SCHEMA_ID, ANALYZER_VERSION, TF_FIELDS, shardFor } from "./format.mjs";

const NL = 0x0a;

export function indexDir(root) { return join(root, INDEX_DIR); }

/** Shard paths in sorted order — order is load-bearing for `df` determinism. */
export function iterShardPaths(root) {
  const dir = indexDir(root);
  if (!existsSync(dir)) return [];
  return readdirSync(dir).filter((f) => f.endsWith(".jsonl")).sort().map((f) => join(dir, f));
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
  let start = 0;
  for (let i = 0; i < buf.length; i++) {
    if (buf[i] === NL) {
      if (i > start) lines.push(buf.subarray(start, i));
      start = i + 1;
    }
  }
  if (start < buf.length) lines.push(buf.subarray(start));
  if (!lines.length) throw new IndexFormatError(`${path}: empty shard, no header line`);
  const header = checkHeader(JSON.parse(lines[0].toString("utf8")), path);
  return [header, lines.slice(1)];
}

/** One record by id, from its own shard. Display-time only — `rank()` never
 *  calls this, because ranking must stay a pure function of the record it was
 *  already handed. */
export function recordFor(root, docId) {
  const shard = shardFor(docId);
  const path = join(indexDir(root), `${shard}.jsonl`);
  if (!existsSync(path)) return null;
  const [, lines] = rawRecordLines(path);
  const needle = Buffer.from(JSON.stringify(docId), "utf8");
  for (const line of lines) {
    if (!line.includes(needle)) continue;
    const record = JSON.parse(line.toString("utf8"));
    if (record.id === docId) return record;
  }
  return null;
}
