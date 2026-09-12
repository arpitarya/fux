/** Re-score fetched passages with the SAME BM25F scorer, over the passage
 *  set's own corpus statistics. Twin of `src/fux/refer/_rescore.py`.
 *
 * A passage is a **two-field document**: its own heading and its own text.
 * `title`, `path` and `ctx` are document-level and would add a constant to
 * every passage of a document — longer vectors, identical ordering.
 */
import { scoreRecord, deriveWlen } from "../query/bm25f.mjs";
import { queryTermHashes } from "../query/scan.mjs";
import { termHash, TF_FIELDS } from "../store/format.mjs";
import { tokenize } from "../query/tokenize.mjs";
import { analyze } from "../query/analyzer.mjs";
import { cmpCodePoints } from "../compat/pyfloat.mjs";

const BODY_I = TF_FIELDS.indexOf("body");
const HEADING_I = TF_FIELDS.indexOf("heading");
const WIDTH = TF_FIELDS.length;

/** A citable address an agent can act on: `path:L12-L40`.
 *
 * Falls back to `path#pN` when a passage carries no line range — which is the
 * case for GENERATED text, where a `.docx`'s Markdown exists nowhere on disk.
 * **A wrong line number is worse than an honest ordinal.** */
export function locatorOf(loc, passage) {
  if (passage.line_start && passage.line_end) {
    return `${loc}:L${passage.line_start}-L${passage.line_end}`;
  }
  return `${loc}#p${passage.ordinal}`;
}

function termsOf(passage) {
  const terms = {};
  const headingTokens = tokenize(passage.heading);
  for (const word of headingTokens) {
    const h = termHash(word);
    if (!(h in terms)) terms[h] = new Array(WIDTH).fill(0);
    terms[h][HEADING_I] += 1;
  }
  const body = tokenize(passage.text);
  for (const word of body) {
    const h = termHash(word);
    if (!(h in terms)) terms[h] = new Array(WIDTH).fill(0);
    terms[h][BODY_I] += 1;
  }
  const flen = new Array(WIDTH).fill(0);
  flen[HEADING_I] = headingTokens.length;
  flen[BODY_I] = body.length;
  return [terms, flen];
}

/** The bounded MULTIPLICATIVE uplift, or the score untouched.
 *
 * ⚠ The early return is not an optimisation — it is the byte-identity
 * guarantee. At `weight <= 0` this is the identity on `score` with **no float
 * arithmetic performed at all**, so no last-bit difference can enter a bundle
 * on a repo that never turned the reranker on. */
function uplift(score, queryTerms, passage, weight, boostFn) {
  if (weight <= 0) return score;
  return score * (1.0 + weight * boostFn(queryTerms, analyze(passage.text)));
}

/** Score every passage of every fetched document against the query.
 *  `candidates` is `[docId, loc, sha, passages]` per fetched document.
 *  Sorted `(-score, locator)` — ties break on the locator, never on iteration
 *  order, because the assembler downstream promises byte-identical output.
 *
 *  **One constant, not a second knob**: `weight` is `[ranking] rerank_weight`,
 *  the same value the document reranker uses. Two knobs for one signal is how
 *  they drift, and the day they disagree `answer` cites a passage the ranking
 *  did not prefer for a reason nobody can name. It defaults to OFF. */
export function rescore(query, candidates, { weight = 0.0, boostFn = null } = {}) {
  const hashes = queryTermHashes(query);
  if (!hashes.length) return [];
  const queryTerms = weight > 0 ? analyze(query) : [];

  const rows = [];
  const df = {};
  let totalWlen = 0;
  for (const [docId, loc, sha, passages] of candidates) {
    for (const passage of passages) {
      const [terms, flen] = termsOf(passage);
      rows.push([docId, loc, sha, passage, terms, flen]);
      totalWlen += deriveWlen(flen);
      for (const term of Object.keys(terms)) df[term] = (df[term] ?? 0) + 1;
    }
  }
  if (!rows.length) return [];

  const n = rows.length;
  const avgWlen = totalWlen / n;
  const scored = rows.map(([docId, loc, sha, passage, terms, flen]) => ({
    doc_id: docId, loc, sha, passage,
    score: uplift(
      scoreRecord(terms, flen, hashes, df, n, avgWlen),
      queryTerms, passage, weight, boostFn || (() => 0),
    ),
    get nbytes() { return this.passage.nbytes; },
    get locator() { return locatorOf(this.loc, this.passage); },
  }));

  scored.sort((a, b) => {
    if (a.score !== b.score) return a.score > b.score ? -1 : 1;
    return cmpCodePoints(a.locator, b.locator);
  });
  return scored;
}
