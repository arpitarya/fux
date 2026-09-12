/** The proximity reranker. Twin of `src/fux/query/rerank.py`.
 *
 * BM25F is a **bag of words**: it knows how often each query term occurs and
 * how long the document is, and nothing whatever about *where* the terms are.
 * Two documents with identical term counts score identically even when one
 * says the query back as a sentence and the other scatters the same words
 * across four unrelated sections.
 *
 * Three signals BM25F structurally cannot compute, over the **same analyzed
 * token stream the index was built from**:
 *
 * | signal | what it catches | what BM25F does instead |
 * |---|---|---|
 * | **coverage** | all query terms present, once each | sums per term, so 5x one term beats 1x five |
 * | **min span** | the terms occur *together* | ignores position entirely |
 * | **adjacency** | query bigrams occur as bigrams | ignores order entirely |
 *
 * ## Why it is in the Node reader at all
 *
 * It is the second half of [ADR-NODE-SEARCH](../../../docs/adr/0155_node-search.md)
 * decision 8. `[ranking] rerank_weight` ships at `0.0`, so this is dead code on
 * an untuned repo — and fux's own `.fux/tune.toml` sets `0.3`, which is exactly
 * why 90 of 174 comparisons were discordant there and 0 of 174 with
 * `--no-tune`. A reader that honours every tune key except the one a consumer
 * actually turned on is not a reader that honours tune.
 *
 * ## The rules it obeys, unchanged from Python
 *
 * - **It re-orders; it never retrieves.** The candidate set is exactly what the
 *   ranker produced. A document BM25F did not find cannot be rescued here.
 * - **Same analyzer, by construction** — `analyze()`, the one the index was
 *   built with. A reranker with its own notion of a token is a second scorer
 *   that will disagree with the first.
 * - **Deterministic**, and the sort key is `(-round(score, 9), id)` — never
 *   iteration order, and `id` by CODE POINT (W-107 hazard H1).
 * - **A document it cannot read is left alone.** Node never fetches
 *   (decision 3), so a `url:` document keeps its BM25F score rather than being
 *   demoted for being unreachable — which is what Python's offline default
 *   does too.
 */
import { readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { analyze } from "./analyzer.mjs";
import { chunk } from "../refer/chunk.mjs";
import { cmpCodePoints, pyRound9 } from "../compat/pyfloat.mjs";

//: How far down the ranking to reorder. W-76's gate is phrased
//: `top-20 -> top-5`, and this is the 20.
export const DEPTH = 20;

//: The maximum fraction a perfect proximity match may add to a BM25F score — a
//: **bounded multiplicative uplift**. Tunable via `[ranking] rerank_weight`.
export const WEIGHT = 1.0;

//: How hard a **missing** query term is punished. Coverage is raised to this
//: before it multiplies, so a passage covering 4 of 5 query terms keeps 64 %
//: of its proximity rather than 80 %.
export const COVERAGE_POWER = 2;

//: Below two distinct query terms there is no proximity to measure — one term
//: is always perfectly covered, adjacent to nothing, and spans itself.
const MIN_TERMS = 2;

/** Distinct, in query order — Python's `dict.fromkeys`. */
function distinct(terms) { return [...new Set(terms)]; }

/** `[coverage, span, adjacency]`, each in `[0, 1]`, over analyzed positions. */
export function signals(queryTerms, docTerms) {
  const wanted = distinct(queryTerms);
  if (!wanted.length || !docTerms.length) return [0.0, 0.0, 0.0];

  const wantedSet = new Set(wanted);
  const positions = new Map();
  for (let i = 0; i < docTerms.length; i++) {
    const term = docTerms[i];
    if (!wantedSet.has(term)) continue;
    let slot = positions.get(term);
    if (slot === undefined) { slot = []; positions.set(term, slot); }
    slot.push(i);
  }

  const present = wanted.filter((t) => positions.has(t));
  const coverage = present.length / wanted.length;
  if (present.length < MIN_TERMS) {
    // One term (or none) — coverage is the only honest signal, and there is no
    // window to measure. A span here would reward a single-term document for a
    // proximity it never demonstrated.
    return [coverage, 0.0, 0.0];
  }
  return [coverage, spanSignal(positions, present), adjacencySignal(positions, wanted)];
}

/** How tightly the matched terms cluster, at their tightest.
 *
 * The **minimum window** containing one occurrence of every present term, found
 * by advancing the earliest pointer — the standard linear sweep, not an
 * all-pairs product: a common term in a long document has thousands of
 * positions and the quadratic version is what makes naive proximity scoring too
 * slow to ship.
 *
 * Normalised as `k / window`, so a window exactly as wide as the number of
 * terms (they are adjacent) scores 1.0 and one twice that scores 0.5. */
function spanSignal(positions, present) {
  const k = present.length;
  const cursors = new Map(present.map((t) => [t, 0]));
  let best = null;
  for (;;) {
    let low = Infinity, lowTerm = null, high = -Infinity;
    for (const t of present) {
      // ⚠ `min` over `(position, term)` PAIRS in Python — the term breaks a
      // positional tie, and two terms cannot share a position, so comparing
      // positions alone is the same function. The first minimum wins either
      // way because `present` is iterated in one fixed order.
      const p = positions.get(t)[cursors.get(t)];
      if (p < low) { low = p; lowTerm = t; }
      if (p > high) high = p;
    }
    const width = high - low + 1;
    if (best === null || width < best) best = width;
    cursors.set(lowTerm, cursors.get(lowTerm) + 1);
    if (cursors.get(lowTerm) >= positions.get(lowTerm).length) break;
  }
  return best ? k / best : 0.0;
}

/** Fraction of query bigrams that occur as bigrams in the document.
 *  Ordered and immediate: `a b` counts only where `b` follows `a` directly. */
function adjacencySignal(positions, wanted) {
  const pairs = [];
  for (let i = 0; i < wanted.length - 1; i++) pairs.push([wanted[i], wanted[i + 1]]);
  if (!pairs.length) return 0.0;
  let hits = 0;
  for (const [first, second] of pairs) {
    if (!positions.has(first) || !positions.has(second)) continue;
    const later = new Set(positions.get(second));
    if (positions.get(first).some((p) => later.has(p + 1))) hits++;
  }
  return hits / pairs.length;
}

/** Does every bigram of `phraseTerms` occur as a bigram in `text`? W-111.
 *
 * `find --phrase "…"`'s post-filter, reusing `adjacencySignal` rather than
 * writing a second notion of adjacency. A **single-term** phrase has no bigram,
 * so it degrades to *is the term present at all* rather than to `false`. */
export function phrasePresent(phraseTerms, text) {
  const terms = analyze(text);
  if (!phraseTerms.length) return true;
  if (phraseTerms.length === 1) return terms.includes(phraseTerms[0]);
  const positions = new Map();
  for (let i = 0; i < terms.length; i++) {
    let slot = positions.get(terms[i]);
    if (slot === undefined) { slot = []; positions.set(terms[i], slot); }
    slot.push(i);
  }
  return adjacencySignal(positions, [...phraseTerms]) === 1.0;
}

/** One passage's proximity score in `[0, 1]`.
 *
 * **Coverage multiplies rather than adds**, and that is the whole difference
 * between a reranker that works and one that does not: with coverage as a
 * weighted addend the reranker moved 2 of 50 golden queries, because every
 * candidate in a corpus about one subject scores 0.85-1.0 and an 8 % spread
 * cannot overcome a BM25F gap. */
export function passageBoost(queryTerms, passageTerms) {
  const [coverage, span, adjacency] = signals(queryTerms, passageTerms);
  if (coverage <= 0) return 0.0;
  return (coverage ** COVERAGE_POWER) * (0.55 + 0.30 * span + 0.15 * adjacency);
}

/** A document scores as its BEST passage, never its average one.
 *
 * Measured over whole documents every candidate in a corpus about one subject
 * reaches coverage 1.0 somewhere and the signal flattens to noise. A document
 * that answers the question in one section and discusses nine other things is
 * exactly what should win, and averaging is how it loses.
 *
 * Chunking is the refer plane's, deliberately — one chunker, so a passage the
 * reranker scored is a passage `answer` can cite. */
export function boost(queryTerms, text) {
  let best = 0.0;
  for (const passage of chunk(text)) {
    const score = passageBoost(queryTerms, analyze(passage.text));
    if (score > best) best = score;
  }
  return best;
}

/** Local file text, or `null` for anything that would need the network.
 *  Exported because `find --phrase` needs exactly this reader — Python's
 *  `_filtered` reaches into `rerank._read_local_text` for the same reason. */
export function readLocalText(root, docId, loc) {
  if (!docId.startsWith("file:")) return null;
  const path = join(root, loc);
  try {
    if (!statSync(path).isFile()) return null;
    return readFileSync(path, "utf8");
  } catch {
    return null;
  }
}

/** Reorder the top `depth` results by proximity. Never adds or drops one.
 *
 * `read` is **injected, never imported** — the same rule `refer/source.mjs`
 * follows for fetchers. It takes `(root, docId, loc)` and returns text, or
 * `null` when the document cannot be read. */
export function rerank(root, query, results, { depth = DEPTH, weight = WEIGHT, read = null } = {}) {
  if (weight <= 0 || depth <= 0 || results.length < 2) return [...results];

  const queryTerms = analyze(query);
  if (distinct(queryTerms).length < MIN_TERMS) {
    // A one-term query has no proximity. Reranking it would be arithmetic on a
    // signal that is constant across every candidate.
    return [...results];
  }

  const reader = read ?? readLocalText;
  const head = results.slice(0, depth);
  const tail = results.slice(depth);

  const rescored = head.map((result) => {
    const text = reader(root, result.id, result.loc);
    if (text === null || text === undefined) return [result.score, result];
    return [result.score * (1.0 + weight * boost(queryTerms, text)), result];
  });

  rescored.sort((a, b) => {
    const ra = -pyRound9(a[0]), rb = -pyRound9(b[0]);
    if (ra !== rb) return ra < rb ? -1 : 1;
    return cmpCodePoints(a[1].id, b[1].id);
  });

  return [...rescored.map(([score, r]) => ({ ...r, score })), ...tail];
}
