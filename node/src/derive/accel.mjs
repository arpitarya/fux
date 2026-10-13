/** The accelerated candidate generator — same results, less work.
 *  Twin of `src/fux/derive/accel.py` (W-242 Tier 1).
 *
 * It reads `.fux/runtime/` exactly as Python writes it and returns the scan's
 * contract: candidate records, `df`, and the corpus statistics. **It never
 * scores and never sorts** — `query/rank.mjs` does both, for both paths, in
 * query-hash order (SR-T1-ACCELERATOR decision 2). That is what makes the
 * differential law a property of the candidate set rather than a hope about
 * float addition.
 *
 * The skipping argument, the anchor seed and the rounding-aware comparison are
 * `accel.py`'s, transcribed in its order; the proofs live in its docstrings and
 * in the record, and are not restated here.
 *
 * 🔴 **Nothing here outlives a call.** A `Runtime` is made per query and
 * dropped with it: `fux mcp` and a library `Index` outlive the plane they read,
 * and `fux build` rewrites it under them (W-242's one design constraint).
 *
 * Owned, with its Python twin, by [SR-T1-ACCELERATOR](../../../records/0110_accelerator.md).
 */
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { FuxError } from "../errors.mjs";
import { idf, deriveWlen, scoreRecord } from "../query/bm25f.mjs";
import { Corpus, rank, Weighting } from "../query/rank.mjs";
import { queryTermHashes } from "../query/scan.mjs";
import { identifiersFor } from "../query/identifiers.mjs";
import { pyRound9 } from "../compat/pyfloat.mjs";
import * as fmt from "./format.mjs";
import { isFresh, readStamp } from "./fresh.mjs";

// `isFresh` and `readStamp` live in `fresh.mjs` since W-278, so the scan can
// ask whether the runtime is fresh without importing this module, which
// imports the scan (the bundle refuses an import cycle).
export { isFresh, readStamp };

/** Lazily-loaded handle on `.fux/runtime/`, for ONE call. */
export class Runtime {
  constructor(root) {
    this.root = root;
    this.dir = fmt.runtimeDir(root);
    this._docs = null;
    this._stats = null;
    this._offsets = new Map();
    this._postings = new Map();
    this._anchors = new Map();
    this._sectionRows = null;
    this._sectionPostings = new Map();
  }

  get stats() {
    if (this._stats === null) this._stats = JSON.parse(readFileSync(join(this.dir, fmt.STATS_NAME), "utf8"));
    return this._stats;
  }

  get docs() {
    if (this._docs === null) {
      const raw = readFileSync(join(this.dir, fmt.DOCS_NAME), "utf8");
      this._docs = raw.split("\n").filter((line) => line).map((line) => JSON.parse(line));
    }
    return this._docs;
  }

  offsets(prefix) {
    let buf = this._offsets.get(prefix);
    if (buf === undefined) {
      const path = fmt.offsetsPath(this.root, prefix);
      buf = existsSync(path) ? readFileSync(path) : Buffer.alloc(0);
      this._offsets.set(prefix, buf);
    }
    return buf;
  }

  postings(prefix) {
    let buf = this._postings.get(prefix);
    if (buf === undefined) {
      const path = fmt.postingsPath(this.root, prefix);
      buf = existsSync(path) ? readFileSync(path) : Buffer.alloc(0);
      this._postings.set(prefix, buf);
    }
    return buf;
  }

  /** `[docidx, anchor tf]` pairs for one term — W-168 step 1's reverse map. */
  anchorPostings(term) {
    const prefix = fmt.termPrefix(term);
    let table = this._anchors.get(prefix);
    if (table === undefined) {
      const path = fmt.anchorsPath(this.root, prefix);
      table = existsSync(path) ? JSON.parse(readFileSync(path, "utf8")) : {};
      this._anchors.set(prefix, table);
    }
    return (Object.hasOwn(table, term) ? table[term] : []).map(([idx, count]) => [Number(idx), Number(count)]);
  }

  /** `sections.json`'s rows, `[docidx, k, flen]` by secidx — W-236. */
  get sectionRows() {
    if (this._sectionRows === null) {
      this._sectionRows = JSON.parse(readFileSync(join(this.dir, fmt.SECTION_TABLE_NAME), "utf8")).rows;
    }
    return this._sectionRows;
  }

  /** `[secidx, tf]` for one term, off `sections/<prefix>.json` — W-236. */
  sectionPostings(term) {
    const prefix = fmt.termPrefix(term);
    let table = this._sectionPostings.get(prefix);
    if (table === undefined) {
      const path = fmt.sectionPostingsPath(this.root, prefix);
      table = existsSync(path) ? JSON.parse(readFileSync(path, "utf8")) : {};
      this._sectionPostings.set(prefix, table);
    }
    return Object.hasOwn(table, term) ? table[term] : [];
  }

  /** Every block of a term, by one bisect over the fixed-width table. */
  blocksFor(term) {
    const buf = this.offsets(fmt.termPrefix(term));
    if (!buf.length) return [];
    const count = Math.floor(buf.length / fmt.ENTRY_SIZE);
    // first entry whose term >= key — lowercase hex orders as the raw bytes do
    let lo = 0, hi = count;
    while (lo < hi) {
      const mid = (lo + hi) >>> 1;
      if (fmt.entryTermHex(buf, mid) < term) lo = mid + 1; else hi = mid;
    }
    const out = [];
    for (; lo < count; lo++) {
      const raw = fmt.unpackEntry(buf, lo);
      if (raw[0] !== term) break;
      const [, blockNo, offset, length, mx, mnw, firstDoc, lastDoc, n] = raw;
      out.push({ term, blockNo, offset, length, mx, mnw, firstDoc, lastDoc, count: n });
    }
    return out;
  }

  /** Parse one block line into its postings. The only JSON parse on this path. */
  readBlock(block) {
    const buf = this.postings(fmt.termPrefix(block.term));
    const [, entries] = JSON.parse(buf.toString("utf8", block.offset, block.offset + block.length));
    return entries.map((e) => [e[0], e[1]]);
  }
}

/** The largest BM25F contribution any posting in `block` can make. */
export function blockBound(block, df, n, avgWlen, scoring) {
  const weights = scoring.weights;
  let wtf = 0.0;
  for (let i = 0; i < block.mx.length; i++) {
    const value = block.mx[i];
    if (value) wtf += weights[i] * value;
  }
  if (wtf === 0) return 0.0;
  let mnw = 0.0;
  for (let i = 0; i < block.mnw.length; i++) {
    const value = block.mnw[i];
    if (value) mnw += weights[i] * value;
  }
  const { k1, b } = scoring;
  const denom = wtf + k1 * (1 - b + b * mnw / avgWlen);
  return idf(df, n) * wtf * (k1 + 1) / denom;
}

/** W-168 step 4 — the corpus `(short, long)` table, off `mined.json`. */
export function minedTable(root) {
  const raw = JSON.parse(readFileSync(join(fmt.runtimeDir(root), fmt.MINED_NAME), "utf8"));
  return raw.pairs.map(([s, l]) => [[...s], [...l]]);
}

/** Is a plane present AND fresh? The one test `runQuery` makes before `--fast`. */
export function usable(root) {
  return existsSync(join(fmt.runtimeDir(root), fmt.STATS_NAME)) && isFresh(root);
}

/** Candidate records, `df`, and the corpus statistics — the scan's contract. */
export function accelCandidates(runtime, queryHashes, top, { skipping, weighting = null, scoring, expansion = null }) {
  const w = weighting ?? new Weighting();
  const stats = runtime.stats;
  if (!("total_flen" in stats)) {
    throw new FuxError(
      "the accelerator was built by an older fux (no `total_flen` in " +
      "stats.json) -- run `fux build` to rebuild the derived plane. " +
      "Nothing committed changed; the runtime is disposable",
    );
  }
  const corpus = new Corpus(
    stats.n,
    deriveWlen([...stats.total_flen], scoring, Number(stats.total_anchor_len ?? 0)),
  );
  if (corpus.n === 0) {
    const df = {};
    for (const h of queryHashes) df[h] = 0;
    return [[], df, corpus];
  }
  const avgWlen = corpus.avgWlen;
  const docs = runtime.docs;

  const blocks = new Map(queryHashes.map((h) => [h, runtime.blocksFor(h)]));
  const df = {};
  for (const h of queryHashes) df[h] = blocks.get(h).reduce((sum, b) => sum + b.count, 0);

  // Rarest first; ties by hash, as Python's `(df[h], h)` key.
  const order = [...queryHashes].sort((a, b) => (df[a] - df[b]) || (a < b ? -1 : a > b ? 1 : 0));

  // docidx -> {term: per-field tf list}. A Map, because insertion order is
  // Python's dict order and a numeric object key would be re-sorted.
  const hits = new Map();
  const opened = new Set();
  const readBlocks = new Map(queryHashes.map((h) => [h, new Set()]));

  // 🔴 The anchor seed, BEFORE the skipping loop — `accel.py`'s whole
  // correctness argument for anchors: an unseen document then has no anchor
  // contribution, so `blockBound` bounds it exactly as before.
  const anchorTf = new Map();
  if (scoring.anchorOn) {
    for (const term of queryHashes) {
      for (const [docidx, count] of runtime.anchorPostings(term)) {
        let bag = anchorTf.get(docidx);
        if (bag === undefined) { bag = {}; anchorTf.set(docidx, bag); }
        bag[term] = count;
        if (!hits.has(docidx)) hits.set(docidx, {});
      }
    }
  }

  for (const term of order) {
    if (skipping && hits.size && cannotReach(
      runtime, blocks, df, opened, order, hits, docs, corpus, top, avgWlen,
      w, scoring, expansion, anchorTf,
    )) break;
    for (const block of blocks.get(term)) {
      readBlocks.get(term).add(block.blockNo);
      for (const [docidx, tf] of runtime.readBlock(block)) {
        let bag = hits.get(docidx);
        if (bag === undefined) { bag = {}; hits.set(docidx, bag); }
        bag[term] = tf;
      }
    }
    opened.add(term);
  }

  fillDeferred(runtime, blocks, opened, queryHashes, hits, readBlocks);

  const anchorOn = scoring.anchorOn;
  const candidates = [];
  for (const [docidx, terms] of hits) {
    const doc = docs[docidx];
    const termsCopy = {};
    for (const [term, tf] of Object.entries(terms)) termsCopy[term] = [...tf];
    const candidate = {
      id: doc.id,
      loc: doc.loc,
      title: doc.title,
      flen: doc.flen,
      archived: Boolean(doc.archived),
      superseded: Boolean(doc.superseded),
      mtime: doc.mtime ?? null,
      terms: termsCopy,
    };
    candidates.push(candidate);
  }
  if (scoring.sectionOn) attachSections(runtime, queryHashes, candidates, [...hits.keys()], docs);
  if (anchorOn) {
    // On EVERY candidate, matching or not: a linked-to document is a longer
    // document whatever words its linkers used (`accel.py`'s note).
    let i = 0;
    for (const docidx of hits.keys()) {
      candidates[i].atf = anchorTf.get(docidx) ?? {};
      candidates[i].alen = docs[docidx].alen ?? 0;
      i++;
    }
  }
  return [candidates, df, corpus];
}

/** True when no unseen document can enter the top `top` — `_cannot_reach`. */
function cannotReach(
  runtime, blocks, df, opened, order, hits, docs, corpus, top, avgWlen,
  weighting, scoring, expansion, anchorTf,
) {
  const deferred = order.filter((h) => !opened.has(h));
  if (!deferred.length) return true;

  let ceiling = 0.0;
  for (const term of deferred) {
    const termBlocks = blocks.get(term);
    if (!termBlocks.length) continue;
    let bound = -Infinity;
    for (const b of termBlocks) {
      const value = blockBound(b, df[term], corpus.n, avgWlen, scoring);
      if (value > bound) bound = value;
    }
    if (expansion !== null && !expansion.trivial) bound *= expansion.weightOf(term);
    ceiling += bound;
  }

  // W-236 — an unseen document's best section can only match deferred terms
  // too, and one BM25 term contribution is below `idf · (k1 + 1)` at any tf
  // and any length. So `λ · idf(h) · (k1 + 1) · w(h)` per deferred term
  // bounds the section term, before the document weight (SR-SECTIONS d7).
  if (scoring.sectionOn) {
    for (const term of deferred) {
      if (!blocks.get(term).length) continue;
      let bound = scoring.section * idf(df[term], corpus.n) * (scoring.k1 + 1);
      if (expansion !== null && !expansion.trivial) bound *= expansion.weightOf(term);
      ceiling += bound;
    }
  }

  if (!weighting.trivial) ceiling *= weighting.maximum;

  const theta = kthScore(
    hits, docs, order.filter((h) => opened.has(h)), df, corpus, top, avgWlen,
    weighting, scoring, expansion, anchorTf,
  );
  if (theta === null) return false;
  // Rounding-aware: `rank()` compares round(score, 9), so a bound that merely
  // falls below theta could still tie after rounding and win on id.
  return pyRound9(ceiling) < pyRound9(theta);
}

/** The `top`-th best WEIGHTED score among current candidates, or `null`. */
function kthScore(hits, docs, openedOrder, df, corpus, top, avgWlen, weighting, scoring, expansion, anchorTf) {
  const anchorOn = anchorTf !== null && scoring.anchorOn;
  let guarded = [...hits];
  if (expansion !== null && !expansion.trivial) {
    guarded = guarded.filter(([i, t]) => expansion.matches(t, anchorOn ? (anchorTf.get(i) ?? null) : null));
  }
  if (guarded.length < top) return null;
  const termWeights = expansion !== null && Object.keys(expansion.weights).length ? expansion.weights : null;
  const scores = [];
  for (const [docidx, terms] of guarded) {
    const recordTerms = {};
    for (const [term, tf] of Object.entries(terms)) recordTerms[term] = [...tf];
    let s = scoreRecord(
      recordTerms, docs[docidx].flen, openedOrder, df, corpus.n, avgWlen, scoring,
      termWeights,
      anchorOn ? (anchorTf.get(docidx) ?? {}) : null,
      anchorOn ? (docs[docidx].alen ?? 0) : 0,
    );
    if (!weighting.trivial) s *= weighting.of(docs[docidx]);
    scores.push(s);
  }
  scores.sort((a, b) => b - a);
  return scores[top - 1];
}

/** W-236 — each candidate's `nsec`, and its matching sections as `secs`.
 *  `accel.py::_attach_sections`: the scan's shape exactly, `[k, flen, terms]`
 *  per section carrying a query hash, in `k` order, read from the derived
 *  section postings rather than the committed shards (decision 7). */
function attachSections(runtime, queryHashes, candidates, docidxs, docs) {
  const rows = runtime.sectionRows;
  const wanted = new Set(docidxs);
  const bags = new Map();  // docidx -> Map(k -> [flen, terms])
  for (const term of queryHashes) {
    for (const [secidx, tf] of runtime.sectionPostings(term)) {
      const [docidx, k, flen] = rows[secidx];
      if (!wanted.has(docidx)) continue;
      let bag = bags.get(docidx);
      if (bag === undefined) { bag = new Map(); bags.set(docidx, bag); }
      let entry = bag.get(k);
      if (entry === undefined) { entry = [[...flen], {}]; bag.set(k, entry); }
      entry[1][term] = [...tf];
    }
  }
  docidxs.forEach((docidx, i) => {
    candidates[i].nsec = docs[docidx].nsec ?? 0;
    const bag = bags.get(docidx);
    if (bag !== undefined && bag.size) {
      candidates[i].secs = [...bag.keys()].sort((a, b) => a - b).map((k) => [k, ...bag.get(k)]);
    }
  });
}

/** Complete known candidates from the few blocks that actually cover them. */
function fillDeferred(runtime, blocks, opened, queryHashes, hits, readBlocks) {
  if (!hits.size) return;
  const wanted = [...hits.keys()].sort((a, b) => a - b);
  for (const term of queryHashes) {
    if (opened.has(term)) continue;
    for (const block of blocks.get(term)) {
      if (readBlocks.get(term).has(block.blockNo)) continue;
      let lo = 0, hi = wanted.length;
      while (lo < hi) {
        const mid = (lo + hi) >>> 1;
        if (wanted[mid] < block.firstDoc) lo = mid + 1; else hi = mid;
      }
      if (lo >= wanted.length || wanted[lo] > block.lastDoc) continue;
      readBlocks.get(term).add(block.blockNo);
      for (const [docidx, tf] of runtime.readBlock(block)) {
        const bag = hits.get(docidx);
        if (bag !== undefined) bag[term] = tf;
      }
    }
  }
}

/** The accelerated `ask`. Identical output to `query/scan.mjs::ask`, by law. */
export function ask(root, query, top, opts) {
  const { skipping, weighting = null, scoring, statsOut = null, expansion = null } = opts;
  const queryHashes = queryTermHashes(query, identifiersFor(root));
  if (!queryHashes.length) {
    if (statsOut !== null) {
      if (!("df" in statsOut)) statsOut.df = {};
      if (!("n" in statsOut)) statsOut.n = 0;
    }
    return [];
  }
  const runtime = new Runtime(root);
  if (!existsSync(join(runtime.dir, fmt.STATS_NAME))) {
    throw new FuxError("no accelerator built — run `fux ingest` (or `fux build`) first");
  }
  const w = weighting ?? new Weighting();
  const collect = expansion !== null ? [...expansion.hashes] : queryHashes;
  const [candidates, df, corpus] = accelCandidates(runtime, collect, top, {
    skipping, weighting: w, scoring, expansion,
  });
  if (statsOut !== null) { statsOut.df = df; statsOut.n = corpus.n; }
  return rank(candidates, collect, df, corpus, top, { weighting: w, scoring, statsOut, expansion });
}
