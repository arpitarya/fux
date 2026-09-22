/** RM3 pseudo-relevance feedback — twin of `src/fux/query/rm3.py`. W-168 step 5.
 *
 * The top `FB_DOCS` documents of a first pass give up their `FB_TERMS`
 * highest-RM1 term hashes — `Σ_d P(t|d) · P(q|d)`, with `P(t|d)` the weighted
 * tf over `wlen` and `P(q|d)` the first-pass score normalised over the set —
 * excluding every term of the original query, ties by ascending hash. The
 * caller scores them through `expand.build` at `[ranking] rm3_weight`.
 *
 * 🔴 **Summed in the Python twin's order** — documents in rank order, terms in
 * ascending hash order — because float addition is not associative and the two
 * readers must pick the same ten terms from the same bits. Hash keys are
 * lowercase hex, so JS's default code-unit sort and Python's `sorted` agree. */

import { recordFor } from "../store/reader.mjs";
import { DEFAULT_SCORING, deriveWlen, weightedTf } from "./bm25f.mjs";

export const FB_DOCS = 10;
export const FB_TERMS = 10;

export function feedbackTerms(root, firstPass, queryHashes, scoring = DEFAULT_SCORING) {
  const docs = firstPass.slice(0, FB_DOCS).filter((r) => r.score > 0);
  let total = 0.0;
  for (const r of docs) total += r.score;
  if (!docs.length || total <= 0) return [];
  const exclude = new Set(queryHashes);
  const weight = new Map();
  for (const r of docs) {
    const record = recordFor(root, r.id);
    if (record === null) continue;
    const wlen = deriveWlen(record.flen ?? [], scoring);
    if (wlen <= 0) continue;
    const pQ = r.score / total;
    const terms = record.terms ?? {};
    for (const h of Object.keys(terms).sort()) {
      if (exclude.has(h)) continue;
      const wtf = weightedTf(terms[h], scoring);
      if (wtf <= 0) continue;
      weight.set(h, (weight.get(h) ?? 0.0) + (wtf / wlen) * pQ);
    }
  }
  const ranked = [...weight.entries()].sort((a, b) => (
    a[1] !== b[1] ? b[1] - a[1] : (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0)
  ));
  return ranked.slice(0, FB_TERMS).map(([h]) => h);
}
