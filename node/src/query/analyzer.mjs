/** Analyzer v2 — the pipeline both ingest and query run, in this order:
 *
 *     split identifiers  ->  lower  ->  stopwords  ->  stem  ->  (caller hashes)
 *
 * Twin of `src/fux/query/analyzer.py`. The order is the whole design; two
 * steps are load-bearing in a way that is easy to get backwards:
 *
 * 1. **Splitting happens BEFORE lowercasing** — case is the only signal that a
 *    boundary was there, so lowercasing first destroys `camelCase`.
 * 2. **Stemming happens BEFORE hashing**, and the hash is of the final
 *    analyzed token. A one-step divergence between the two sides produces a
 *    silent no-match: the query hashes a string the index never wrote, and
 *    there is no error to see.
 */

import { stem } from "./stem.mjs";

/** Matched against the ORIGINAL text, not a lowercased copy. Hyphen is absent
 *  from the class, so `kebab-case` splits here for free. */
const WORD_RE = /[A-Za-z0-9_]+/g;

/** The three places a real identifier boundary can sit:
 *    `_`                      snake_case
 *    lower/digit -> upper     getUser, bm25F
 *    upper -> upper+lower     HTTPServer
 *  A token with none of these is left whole — `sha256`, `utf8`, `k1`. */
const BOUNDARY_RE = /_+|(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])/;

const STOPWORDS = new Set(
  `a an and are as at be but by for from has have how i if in into is it its
   of on or that the their then there these this to was were what when where
   which who why will with you your we our not can may`.split(/\s+/),
);

/** The parts of one raw token, or `[]` when there is no boundary in it. */
export function splitIdentifier(raw) {
  const parts = raw.split(BOUNDARY_RE).filter((p) => p);
  if (parts.length < 2) return [];
  return parts.filter((p) => p.length > 1);
}

/** Text to final analyzed terms, in document order, WITH duplicates.
 *  Duplicates are the point: the caller counts them into a term frequency. */
export function analyze(text) {
  const out = [];
  const matches = text.match(WORD_RE);
  if (!matches) return out;
  for (const raw of matches) {
    for (const token of [raw, ...splitIdentifier(raw)]) {
      const lowered = token.toLowerCase();
      if (STOPWORDS.has(lowered)) continue;
      out.push(stem(lowered));
    }
  }
  return out;
}

/** `[surface, analyzed]` for every term `analyze` produces, same order.
 *
 *  The surface is the pre-lowercase, pre-stem token — what the user actually
 *  typed. `confidence` reports that, not the stem the index is keyed by,
 *  because *"`mtl` is not in this corpus"* is worse than saying nothing.
 *
 *  ⚠ Duplicates `analyze`'s loop deliberately, exactly as Python does, and for
 *  the same reason: `analyze` runs over every token at ingest, and allocating
 *  a pair per token to serve a per-query diagnostic is the wrong trade. */
export function analyzePairs(text) {
  const out = [];
  const matches = text.match(WORD_RE);
  if (!matches) return out;
  for (const raw of matches) {
    for (const token of [raw, ...splitIdentifier(raw)]) {
      const lowered = token.toLowerCase();
      if (STOPWORDS.has(lowered)) continue;
      out.push([token, stem(lowered)]);
    }
  }
  return out;
}

export { STOPWORDS };
