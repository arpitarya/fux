/** The reference scan — the DEFAULT path, and the one a bug report reproduces
 *  against. Twin of `src/fux/query/scan.py`.
 *
 * Every line in the corpus is touched; only a line whose raw bytes contain a
 * query hash is parsed. `flen` is read by regex from the bytes on every line,
 * candidate or not, because parsing every record to sum a length is exactly
 * what the prefilter exists to avoid. (`mtime` was read the same way until
 * 2026-09-13, for the corpus-wide `newestMtime` the recency prior normalised
 * against; the prior went (W-152) and the regex with it. A candidate's own
 * `mtime` comes off the parsed record, like every other per-document fact.)
 */
import { rawRecordLines, iterShardPaths, recordFor } from "../store/reader.mjs";
import { termHash, TF_FIELDS } from "../store/format.mjs";
import { DEFAULT_SCORING, deriveWlen } from "./bm25f.mjs";
import { Corpus, rank } from "./rank.mjs";
import { tokenize } from "./tokenize.mjs";

//: The byte-level oracle, over per-field counts. `wlen` is DERIVED from `flen`
//: at the weights in force, so this parses the array and applies `deriveWlen`
//: — the same function the scorer and the refer plane use, so they cannot drift.
const FLEN_RE = /"flen":\[([0-9,\s]*)\]/;

//: W-168 step 1 — one `ref` edge's anchor length and its target, off the raw
//: bytes. Key order is `canonical_dumps`'s (sorted), so `al` precedes `dst`,
//: and `at` is a flat hash -> int map with no nested object. Global, because
//: a line carries many edges. Compiled always, matched only when the anchor
//: field is switched on.
const EDGE_ANCHOR_RE = /"al":(\d+),"at":\{[^}]*\},"dst":"([^"]+)"/g;

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
  // W-168 step 1. Nothing below costs anything when the field is off, which
  // is the default: the three `anchorOn` branches are not taken and this
  // function does exactly the work it did before anchor text existed.
  const anchorOn = scoring.anchorOn;
  const wanted = new Set(queryHashes);
  const anchorTf = new Map();   // doc id -> { hash: count }, over the query only
  const anchorLen = new Map();  // doc id -> anchor token total
  let totalAnchorLen = 0;

  let totalDocs = 0;
  // Per-field totals, summed raw and weighted ONCE at the end. Summing
  // `deriveWlen` per record would bake the weights into a running total the
  // moment anything cached it — the accelerator's stats plane made exactly
  // that mistake (SR-TUNE, 2026-08-24).
  const totalFlen = new Array(TF_FIELDS.length).fill(0);
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
      // The substring check is a PREFILTER only: a query hash can appear as a
      // literal 16-hex string outside `terms` (a title, an id, a sha) without
      // the document containing that term. Once a line is worth parsing, `df`
      // is counted from the parsed record's own `terms` keys, which is exact.
      if (anchorOn) {
        // Every line, candidate or not: a document's own anchor LENGTH belongs
        // in its `wlen` whether or not it matches, and `avgWlen` needs the
        // corpus total.
        EDGE_ANCHOR_RE.lastIndex = 0;
        let m;
        while ((m = EDGE_ANCHOR_RE.exec(text)) !== null) {
          const length = parseInt(m[1], 10);
          const dst = m[2];
          anchorLen.set(dst, (anchorLen.get(dst) ?? 0) + length);
          totalAnchorLen += length;
        }
      }
      let hit = false;
      for (const p of patterns) { if (line.includes(p)) { hit = true; break; } }
      if (!hit) continue;

      const record = JSON.parse(line.toString("utf8"));
      const recordTerms = record.terms || {};
      for (const h of queryHashes) if (h in recordTerms) df[h]++;
      if (anchorOn) {
        // This line was parsed because a query hash appears somewhere in it —
        // and an `at` key IS such an appearance, so a document that merely
        // LINKS using the word is parsed here for free. That is why anchor
        // terms are committed as hashes.
        for (const edge of record.edges || []) {
          const at = edge.at;
          if (!at) continue;
          for (const term of Object.keys(at)) {
            if (!wanted.has(term)) continue;
            let bag = anchorTf.get(edge.dst);
            if (bag === undefined) { bag = {}; anchorTf.set(edge.dst, bag); }
            bag[term] = (bag[term] ?? 0) + at[term];
          }
        }
      }
      candidates.push(record);
    }
  }

  if (anchorOn) {
    // 🔴 The RETRIEVAL half. A document whose only match is a linker's wording
    // carries none of the query's hashes on its own line, so the prefilter
    // above never parsed it and it is not a candidate at all — a scoring fold
    // alone would change nothing for exactly the documents this feature is
    // for. `recordFor` reads the one shard `shardFor(id)` names.
    const seen = new Set(candidates.map((r) => r.id));
    for (const docId of [...anchorTf.keys()].sort()) {
      if (seen.has(docId)) continue;
      const record = recordFor(root, docId);
      // ⚠ `df` is deliberately NOT counted here: a document whose own `terms`
      // carry the hash was already counted above, and one that does not carry
      // it must not be — anchor terms are in no committed posting, so they are
      // in no `df`, on either reader or either Python path.
      if (record !== null) candidates.push(record);
    }
    for (const record of candidates) {
      record.atf = anchorTf.get(record.id) ?? {};
      record.alen = anchorLen.get(record.id) ?? 0;
    }
  }

  return [
    candidates,
    df,
    new Corpus(totalDocs, deriveWlen(totalFlen, scoring, totalAnchorLen)),
  ];
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
