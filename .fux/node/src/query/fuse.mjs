/** Reciprocal-rank fusion for `-q` — several phrasings, one ranked list.
 *  Twin of `fuse.py`. */
import { pyRound9, cmpCodePoints } from "../compat/pyfloat.mjs";

/** Cormack et al. 2009's constant. **Not tuned here and not a tune.toml key** —
 *  a knob on it would be a knob on a published constant measured on TREC
 *  collections, with nothing in this repo able to beat it at 10 documents. */
export const K = 60;

/** `id -> fused score`, from ranked id lists. Rank 0 is best.
 *  A document absent from a list contributes nothing — **not a penalty**. */
export function rrf(rankLists, k = K) {
  const scores = {};
  for (const ranks of rankLists) {
    for (let i = 0; i < ranks.length; i++) {
      scores[ranks[i]] = (scores[ranks[i]] ?? 0.0) + 1.0 / (k + i + 1);
    }
  }
  return scores;
}

/** Fuse several ranked result lists into one, by rank.
 *
 * **The result object comes from the arm that ranked it best**, so its `loc`,
 * `title` and `archived` are a real document's view, not a merge of several.
 * Only `score` is replaced. Ordered by the same key `rank()` uses, so a fused
 * list is as reproducible as an unfused one. */
export function fuseResults(resultLists, top, k = K) {
  if (!resultLists.length) return [];
  if (resultLists.length === 1) return resultLists[0].slice(0, top);

  const scores = rrf(resultLists.map((rs) => rs.map((r) => r.id)), k);

  const bestSeen = new Map();
  for (const results of resultLists) {
    for (let i = 0; i < results.length; i++) {
      const cur = bestSeen.get(results[i].id);
      if (cur === undefined || i < cur[0]) bestSeen.set(results[i].id, [i, results[i]]);
    }
  }

  const ordered = Object.keys(scores).sort((a, b) => {
    const ra = -pyRound9(scores[a]), rb = -pyRound9(scores[b]);
    if (ra !== rb) return ra < rb ? -1 : 1;
    return cmpCodePoints(a, b);
  });

  return ordered.slice(0, top).map((id) => ({ ...bestSeen.get(id)[1], score: scores[id] }));
}
