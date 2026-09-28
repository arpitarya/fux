/** Analyzer v3 — the pipeline both ingest and query run, in this order:
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
import { fixed } from "../config/constants.mjs";
import { EMPTY } from "./identifiers.mjs";

/** Matched against the ORIGINAL text, not a lowercased copy.
 *
 *  🔴 **v3 (W-205 part 2, family (a)): `-`, `.` and `/` join `_` inside a
 *  token.** Under v2 the class was `[A-Za-z0-9_]+`, so `RF-118` arrived as two
 *  raw tokens and the module's own promise — whole AND parts are both emitted —
 *  held for `snake_case` and silently failed for every other separator.
 *
 *  The trailing-run requirement is what stops sentence punctuation being glued
 *  on: in `finished. Next` the `.` is not followed by an alphanumeric run. */
const WORD_RE = /[A-Za-z0-9_]+(?:[-./][A-Za-z0-9_]+)*/g;

/** The three places a real identifier boundary can sit:
 *    `_` `-` `.` `/`          snake_case, kebab-case, dotted, pathlike
 *    lower/digit -> upper     getUser, bm25F
 *    upper -> upper+lower     HTTPServer
 *  A token with none of these is left whole — `sha256`, `utf8`, `k1`.
 *
 *  🔴 v3 adds `-`, `.` and `/` to the `_` alternative. The PARTS were already
 *  emitted for those separators (WORD_RE split on them); what was missing was
 *  the WHOLE, and that is the whole of family (a). */
const BOUNDARY_RE = /[_\-./]+|(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])/;

//: `constants.toml [analyzer] stopwords` — the Python twin reads the same key.
const STOPWORDS = new Set(fixed("analyzer", "stopwords"));

/** The parts of one raw token, or `[]` when there is no boundary in it. */
export function splitIdentifier(raw) {
  const parts = raw.split(BOUNDARY_RE).filter((p) => p);
  if (parts.length <= 1) return [];
  return parts.filter((p) => p.length > 1);
}

/** Text to final analyzed terms, in document order, WITH duplicates.
 *  Duplicates are the point: the caller counts them into a term frequency.
 *
 *  `ids` — the repo's identifier families (W-233): each match adds ONE
 *  canonical term beside everything below. With none this is the v3 loop,
 *  byte for byte. */
export function analyze(text, ids = EMPTY) {
  if (ids.rules.length) return withFamilies(text, ids).map((p) => p[1]);
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
export function analyzePairs(text, ids = EMPTY) {
  if (ids.rules.length) return withFamilies(text, ids);
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

/** `[surface, analyzed]` for v3's terms plus one canonical term per family
 *  match. Twin of Python's `_with_families`, and the placement rule is the
 *  one both readers must agree on: a canonical term goes immediately before
 *  the first raw token that starts at or after the match's start, or after
 *  the last token when none does. A match adds nothing when v3 already emitted
 *  the same term for the same span. Never stopworded, never stemmed. */
function withFamilies(text, ids) {
  const raws = [];
  const rx = new RegExp(WORD_RE.source, "g");
  let m;
  while ((m = rx.exec(text)) !== null) raws.push([m.index, m.index + m[0].length, m[0]]);
  // What v3 actually EMITTED for each whole raw token — its stem, or nothing
  // for a stopword — never the raw spelling (an all-letter canonical term
  // whose v3 whole form was stemmed away must still be added).
  const spans = new Map(
    raws.map(([s, e, r]) => [`${s}:${e}`, STOPWORDS.has(r.toLowerCase()) ? null : stem(r.toLowerCase())]),
  );
  const extras = ids
    .matches(text)
    .filter(([s, e, c]) => spans.get(`${s}:${e}`) !== c)
    .map(([s, e, c]) => [s, text.slice(s, e), c]);
  const out = [];
  let k = 0;
  for (const [start, , raw] of raws) {
    while (k < extras.length && extras[k][0] <= start) {
      out.push([extras[k][1], extras[k][2]]);
      k += 1;
    }
    for (const token of [raw, ...splitIdentifier(raw)]) {
      const lowered = token.toLowerCase();
      if (STOPWORDS.has(lowered)) continue;
      out.push([token, stem(lowered)]);
    }
  }
  for (; k < extras.length; k += 1) out.push([extras[k][1], extras[k][2]]);
  return out;
}

export { STOPWORDS };
