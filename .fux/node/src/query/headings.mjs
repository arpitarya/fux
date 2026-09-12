/** Which of a record's headings match the query — DISPLAY ONLY.
 *
 * Twin of `headings.py`. Runs after `run_query` returns, over the record's
 * committed `phrases`, so it can never reach a score. `[]` for a missing
 * record, a `hashed` one, or a query no heading matches.
 */
import { tokenize } from "./tokenize.mjs";

export const MAX_HEADINGS = 3;

export function headingsFor(record, query, limit = MAX_HEADINGS) {
  if (!record) return [];
  const phrases = record.phrases || [];
  if (!phrases.length) return [];

  const wanted = new Set(tokenize(query));
  if (!wanted.size) return [];

  const scored = [];
  for (let position = 0; position < phrases.length; position++) {
    const phrase = phrases[position];
    if (typeof phrase !== "string") continue;   // a record is data, not a promise
    let matches = 0;
    for (const t of new Set(tokenize(phrase))) if (wanted.has(t)) matches++;
    if (matches) scored.push([-matches, position, phrase]);
  }
  // `position` ascending is the tie-break, so the key sorts directly.
  scored.sort((a, b) => (a[0] - b[0]) || (a[1] - b[1]));
  return scored.slice(0, limit).map((s) => s[2]);
}
