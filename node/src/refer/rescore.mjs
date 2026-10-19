/** Re-score fetched passages with the SAME BM25F scorer, over the passage
 *  set's own corpus statistics. Twin of `src/fux/refer/_rescore.py`.
 *
 * A passage is a **two-field document**: its own heading and its own text.
 * `title`, `path` and `ctx` are document-level and would add a constant to
 * every passage of a document — longer vectors, identical ordering.
 */
import { scoreRecord, deriveWlen, Scoring } from "../query/bm25f.mjs";
import { queryTermHashes } from "../query/scan.mjs";
import { termHash, TF_FIELDS } from "../store/format.mjs";
import { tokenize } from "../query/tokenize.mjs";
import { analyze } from "../query/analyzer.mjs";
import { cmpCodePoints } from "../compat/pyfloat.mjs";
import { fixed } from "../config/constants.mjs";

const BODY_I = TF_FIELDS.indexOf("body");
const HEADING_I = TF_FIELDS.indexOf("heading");
const CTX_I = TF_FIELDS.indexOf("ctx");
const WIDTH = TF_FIELDS.length;

//: W-287 C3 — the extensions the `.xlsx` decoder claims; a row there is cited
//: `book.xlsx#Sheet!R12`. Twin of `_rescore.py::_SHEET_SUFFIXES`.
const SHEET_SUFFIXES = fixed("decoders.xlsx", "extensions");

/** A citable address an agent can act on: `path:L12-L40`.
 *
 * Falls back to `path#pN` when a passage carries no line range — which is the
 * case for GENERATED text, where a `.docx`'s Markdown exists nowhere on disk.
 * **A wrong line number is worse than an honest ordinal.** */
export function locatorOf(loc, passage) {
  const row = passage.row;
  if (row && SHEET_SUFFIXES.some((suffix) => loc.toLowerCase().endsWith(suffix))) {
    return `${loc}#${row.label}!R${row.ordinal}`;
  }
  return orderKeyOf(loc, passage);
}

/** What a tie between equal scores is broken on: the POSITIONAL locator, for
 *  every passage — never the displayed one, which C3 changed for a sheet row.
 *  Twin of `ScoredPassage.order_key`. */
export function orderKeyOf(loc, passage) {
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

/** `scoring` with the column-name field (the `ctx` slot) at `columnWeight`.
 *  Twin of `_rescore.py::_with_columns`: a non-row passage has no `ctx` count,
 *  so nothing placed there can move its score. */
function withColumns(scoring, columnWeight) {
  const weights = scoring.weights.map((w, i) => (i === CTX_I ? columnWeight : w));
  return new Scoring(scoring.k1, scoring.b, weights, scoring.anchor, scoring.section);
}

/** A ROW passage's terms on three fields — heading (+ key value), column
 *  names (the `ctx` slot), body (the text less the header line). Twin of
 *  `_rescore.py::_row_terms` (W-287 B2, B4, B5). */
function rowTerms(passage) {
  const row = passage.row;
  const heading = tokenize(passage.heading);
  if (row.key >= 0) heading.push(...tokenize(row.values[row.key]));
  const names = row.record ? tokenize(row.values[0]) : tokenize(row.columns.join(" "));
  const body = new Map();
  for (const word of tokenize(passage.text)) body.set(word, (body.get(word) ?? 0) + 1);
  const removed = tokenize(row.columns.join(" "));
  if (row.record) removed.push(...names);
  for (const word of removed) if ((body.get(word) ?? 0) > 0) body.set(word, body.get(word) - 1);

  const terms = {};
  const add = (word, field, count) => {
    const h = termHash(word);
    if (!(h in terms)) terms[h] = new Array(WIDTH).fill(0);
    terms[h][field] += count;
  };
  for (const word of heading) add(word, HEADING_I, 1);
  for (const word of names) add(word, CTX_I, 1);
  let bodyLen = 0;
  for (const [word, count] of body) { if (count) { add(word, BODY_I, count); bodyLen += count; } }
  const flen = new Array(WIDTH).fill(0);
  flen[HEADING_I] = heading.length;
  flen[CTX_I] = names.length;
  flen[BODY_I] = bodyLen;
  return [terms, flen];
}

/** `[bonus, columnsMatched]` — the column selector (W-287 B3). Twin of
 *  `_rescore.py::_selector`. */
function selector(row, hashes, df, n, avgWlen, scoring) {
  const names = row.record ? [row.values[0]] : row.columns;
  const cells = row.record ? [row.values[1]] : row.values;
  const wanted = new Set(hashes);
  const selected = [];
  const named = new Set();
  names.forEach((name, i) => {
    const hit = tokenize(name).map(termHash).filter((h) => wanted.has(h));
    if (hit.length) { selected.push(i); for (const h of hit) named.add(h); }
  });
  if (!selected.length) return [0.0, []];
  const matched = selected.map((i) => names[i]);
  const remaining = hashes.filter((h) => !named.has(h));
  if (!remaining.length) return [0.0, matched];
  const words = tokenize(selected.filter((i) => i < cells.length).map((i) => cells[i]).join(" "));
  const terms = {};
  for (const word of words) {
    const h = termHash(word);
    if (!(h in terms)) terms[h] = new Array(WIDTH).fill(0);
    terms[h][BODY_I] += 1;
  }
  const flen = new Array(WIDTH).fill(0);
  flen[BODY_I] = words.length;
  return [scoreRecord(terms, flen, remaining, df, n, avgWlen, scoring), matched];
}

/** The bounded MULTIPLICATIVE uplift, or the score untouched.
 *
 * ⚠ The early return is not an optimisation — it is the byte-identity
 * guarantee. At `weight <= 0` this is the identity on `score` with **no float
 * arithmetic performed at all**, so no last-bit difference can enter a bundle
 * on a repo that never turned the reranker on. */
function uplift(score, queryTerms, passage, weight, boostFn, proximity) {
  if (weight <= 0) return score;
  return score * (1.0 + weight * boostFn(queryTerms, analyze(passage.text), proximity));
}

/** Score every passage of every fetched document against the query.
 *  `candidates` is `[docId, loc, sha, passages]` per fetched document.
 *  Sorted `(-score, order_key)` — ties break on the POSITIONAL locator, never on iteration
 *  order, because the assembler downstream promises byte-identical output.
 *
 *  **One constant, not a second knob**: `weight` is `[ranking] rerank_weight`,
 *  the same value the document reranker uses. Two knobs for one signal is how
 *  they drift, and the day they disagree `answer` cites a passage the ranking
 *  did not prefer for a reason nobody can name. `scoring` is the repo's
 *  `[bm25f]`, so a passage is scored exactly as its document was. */
export function rescore(query, candidates, { scoring, weight, proximity, columnWeight, boostFn = null }) {
  const hashes = queryTermHashes(query);
  if (!hashes.length) return [];
  const queryTerms = weight > 0 ? analyze(query) : [];
  // W-287 stage B — `0.0` is OFF and takes the old path untouched.
  if (typeof columnWeight !== "number") throw new Error("rescore needs columnWeight — [ranking] table_column_weight");
  const tables = columnWeight > 0;
  if (tables) scoring = withColumns(scoring, columnWeight);

  const rows = [];
  const df = {};
  let totalWlen = 0;
  for (const [docId, loc, sha, passages] of candidates) {
    for (const passage of passages) {
      const [terms, flen] = tables && passage.row ? rowTerms(passage) : termsOf(passage);
      rows.push([docId, loc, sha, passage, terms, flen]);
      totalWlen += deriveWlen(flen, scoring);
      for (const term of Object.keys(terms)) df[term] = (df[term] ?? 0) + 1;
    }
  }
  if (!rows.length) return [];

  const n = rows.length;
  const avgWlen = totalWlen / n;
  const scored = rows.map(([docId, loc, sha, passage, terms, flen]) => {
    let score = scoreRecord(terms, flen, hashes, df, n, avgWlen, scoring);
    let matched = [];
    if (tables && passage.row) {
      const [bonus, cols] = selector(passage.row, hashes, df, n, avgWlen, scoring);
      matched = cols;
      if (bonus) score += bonus;
    }
    return {
      doc_id: docId, loc, sha, passage,
      score: uplift(score, queryTerms, passage, weight, boostFn || (() => 0), proximity),
      columns_matched: matched,
      get nbytes() { return this.passage.nbytes; },
      get locator() { return locatorOf(this.loc, this.passage); },
      get order_key() { return orderKeyOf(this.loc, this.passage); },
    };
  });

  scored.sort((a, b) => {
    if (a.score !== b.score) return a.score > b.score ? -1 : 1;
    return cmpCodePoints(a.order_key, b.order_key);
  });
  return scored;
}
