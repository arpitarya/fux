/** Fill a byte budget with the highest-value passages that fit.
 *  Twin of `src/fux/refer/_assemble.py`.
 *
 * Greedy by **score per byte** — the question is not "what scores highest" but
 * "what is the most answer per byte of the caller's window".
 */
import { cmpCodePoints } from "../compat/pyfloat.mjs";

export const DEFAULT_BUDGET = 8000;
export const PER_DOC_FRACTION = 0.5;
/** Charged per citation, so the budget bounds the RENDERED answer and not
 *  merely its payload. */
export const CITATION_OVERHEAD = 80;

const enc = new TextEncoder();

export function assemble(scored, {
  budget = DEFAULT_BUDGET, k = null, source = "fetched",
  overhead = 0, perDocFraction = PER_DOC_FRACTION,
} = {}) {
  if (budget <= 0) throw new RangeError("budget must be positive");

  const candidates = scored.filter((s) => s.score > 0);
  if (!candidates.length) return { citations: [], budget, used: overhead, dropped: 0 };

  const cmp = (a, b) => {
    if (a.score !== b.score) return a.score > b.score ? -1 : 1;
    const s = cmpCodePoints(a.sha, b.sha);
    return s !== 0 ? s : cmpCodePoints(a.locator, b.locator);
  };

  // The floor: the best answer by ABSOLUTE score is seated first, so greedy
  // score-per-byte cannot crowd it out with cheaper fragments.
  let best = candidates[0];
  for (const s of candidates) if (cmp(s, best) < 0) best = s;

  const rest = candidates.filter((s) => s !== best);
  rest.sort((a, b) => {
    const ra = -(a.score / Math.max(a.nbytes, 1));
    const rb = -(b.score / Math.max(b.nbytes, 1));
    if (ra !== rb) return ra < rb ? -1 : 1;
    const s = cmpCodePoints(a.sha, b.sha);
    return s !== 0 ? s : cmpCodePoints(a.locator, b.locator);
  });

  // **The cap protects against competition, so with no competition there is
  // nothing to protect.** Keyed on the candidates' own documents, not on `k`
  // or the caller's intent.
  const single = new Set(candidates.map((s) => s.doc_id)).size <= 1;
  const perDocCap = single ? budget : Math.floor(budget * perDocFraction);

  let used = overhead, dropped = 0;
  const perDoc = new Map();
  const chosen = [];

  for (const s of [best, ...rest]) {
    if (k !== null && chosen.length >= k) { dropped++; continue; }
    const text = s.passage.text;
    const citation = {
      doc_id: s.doc_id, locator: s.locator, sha: s.sha,
      heading: s.passage.heading, text, score: s.score, source,
      // ⚠ The overhead is part of a citation's OWN size, not a separate line
      // item: the locator line and separator will be rendered around every
      // passage, so the budget bounds the rendered answer rather than the
      // payload. Charging it here is what makes `used` mean what it says.
      nbytes: enc.encode(text).length + CITATION_OVERHEAD,
    };
    const spent = perDoc.get(s.doc_id) ?? 0;
    // A document's FIRST citation is exempt: the cap exists to stop a document
    // DOMINATING, not to stop it appearing.
    const capped = perDoc.has(s.doc_id) && spent + citation.nbytes > perDocCap;
    if (used + citation.nbytes > budget || capped) { dropped++; continue; }
    chosen.push(citation);
    used += citation.nbytes;
    perDoc.set(s.doc_id, spent + citation.nbytes);
  }

  // Presented in SCORE order — the caller reads the best answer first, even
  // though selection ran on score-per-byte.
  chosen.sort(cmp);
  return { citations: chosen, budget, used, dropped };
}
