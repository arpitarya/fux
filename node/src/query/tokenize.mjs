/** The tokenizer both sides of a match share — analyzer v2.
 *
 * Twin of `src/fux/query/tokenize.py`. The pipeline lives in `analyzer.mjs`;
 * this is the stable entry point, kept so every caller gets *the same*
 * analysis by construction rather than by review.
 */
import { analyze, analyzePairs, STOPWORDS } from "./analyzer.mjs";
import { EMPTY } from "./identifiers.mjs";

/** `ids` — the repo's identifier families (W-233); `EMPTY` is analyzer v3. */
export function tokenize(text, ids = EMPTY) { return analyze(text, ids); }
export function tokenizePairs(text, ids = EMPTY) { return analyzePairs(text, ids); }
export { STOPWORDS };
