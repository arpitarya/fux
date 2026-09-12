/** The reference scan — the DEFAULT path, and the one a bug report reproduces
 *  against. Twin of `src/fux/query/scan.py`.
 *
 * Every line in the corpus is touched; only a line whose raw bytes contain a
 * query hash is parsed. `flen` and `mtime` are read by regex from the bytes on
 * every line, candidate or not, because parsing every record to sum a length
 * is exactly what the prefilter exists to avoid.
 */
import { rawRecordLines, iterShardPaths } from "../store/reader.mjs";
import { termHash, TF_FIELDS } from "../store/format.mjs";
import { DEFAULT_SCORING, deriveWlen } from "./bm25f.mjs";
import { Corpus, rank } from "./rank.mjs";
import { tokenize } from "./tokenize.mjs";

//: The byte-level oracle, over per-field counts. `wlen` is DERIVED from `flen`
//: at the weights in force, so this parses the array and applies `deriveWlen`
//: — the same function the scorer and the refer plane use, so they cannot drift.
const FLEN_RE = /"flen":\[([0-9,\s]*)\]/;
const MTIME_RE = /"mtime":(\d+)/;

function flenFromLine(text) {
  const m = FLEN_RE.exec(text);
  if (!m) return null;
  const inner = m[1].trim();
  if (!inner) return [];
  return inner.split(",").map((p) => parseInt(p, 10));
}

/** Query terms as index hashes, deduped, ORDER PRESERVED.
 *  Order is load-bearing: `rank()` sums BM25F contributions in it, so both
 *  candidate generators must derive it identically from the same string. */
export function queryTermHashes(query) {
  const seen = new Set();
  const out = [];
  for (const t of tokenize(query)) {
    const h = termHash(t);
    if (!seen.has(h)) { seen.add(h); out.push(h); }
  }
  return out;
}

/** The B2 pass: candidate records, `df`, and the corpus statistics. */
export function scanCandidates(root, queryHashes, { scoring = DEFAULT_SCORING } = {}) {
  const patterns = queryHashes.map((h) => Buffer.from(`"${h}"`, "ascii"));

  let totalDocs = 0;
  // Per-field totals, summed raw and weighted ONCE at the end. Summing
  // `deriveWlen` per record would bake the weights into a running total the
  // moment anything cached it — the accelerator's stats plane made exactly
  // that mistake (ADR-TUNE, 2026-08-24).
  const totalFlen = new Array(TF_FIELDS.length).fill(0);
  let newestMtime = 0;
  const df = {};
  for (const h of queryHashes) df[h] = 0;
  const candidates = [];

  for (const path of iterShardPaths(root)) {
    const [, lines] = rawRecordLines(path);
    for (const line of lines) {
      totalDocs++;
      // latin1 keeps this a byte view: the regexes are ASCII-only and this
      // avoids decoding UTF-8 for every line in the corpus.
      const text = line.toString("latin1");
      const flen = flenFromLine(text);
      if (flen !== null) for (let i = 0; i < flen.length; i++) totalFlen[i] += flen[i];
      const mt = MTIME_RE.exec(text);
      if (mt !== null) {
        const value = parseInt(mt[1], 10);
        if (value > newestMtime) newestMtime = value;
      }
      // The substring check is a PREFILTER only: a query hash can appear as a
      // literal 16-hex string outside `terms` (a title, an id, a sha) without
      // the document containing that term. Once a line is worth parsing, `df`
      // is counted from the parsed record's own `terms` keys, which is exact.
      let hit = false;
      for (const p of patterns) { if (line.includes(p)) { hit = true; break; } }
      if (!hit) continue;

      const record = JSON.parse(line.toString("utf8"));
      const recordTerms = record.terms || {};
      for (const h of queryHashes) if (h in recordTerms) df[h]++;
      candidates.push(record);
    }
  }

  return [candidates, df, new Corpus(totalDocs, deriveWlen(totalFlen, scoring), newestMtime)];
}

/** The reference path. */
export function ask(root, query, top = 5, opts = {}) {
  const { weighting = null, scoring = DEFAULT_SCORING, statsOut = null, expansion = null } = opts;
  const queryHashes = queryTermHashes(query);
  if (!queryHashes.length) {
    // A query that tokenizes to nothing still owes the caller its corpus
    // statistics, or confidence cannot tell "no terms" from "not run".
    if (statsOut !== null) {
      if (!("df" in statsOut)) statsOut.df = {};
      if (!("n" in statsOut)) statsOut.n = 0;
    }
    return [];
  }
  const collect = expansion ? expansion.hashes : queryHashes;
  const [candidates, df, corpus] = scanCandidates(root, collect, { scoring });
  if (statsOut !== null) { statsOut.df = df; statsOut.n = corpus.n; }
  return rank(candidates, collect, df, corpus, top, { weighting, scoring, statsOut, expansion });
}
