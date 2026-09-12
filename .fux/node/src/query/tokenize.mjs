/** The tokenizer both sides of a match share — analyzer v2.
 *
 * Twin of `src/fux/query/tokenize.py`. The pipeline lives in `analyzer.mjs`;
 * this is the stable entry point, kept so every caller gets *the same*
 * analysis by construction rather than by review.
 */
import { analyze, analyzePairs, STOPWORDS } from "./analyzer.mjs";

export function tokenize(text) { return analyze(text); }
export function tokenizePairs(text) { return analyzePairs(text); }
export { STOPWORDS };
