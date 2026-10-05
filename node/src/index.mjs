/** The library surface — the half of `fux-engine` that is not a CLI.
 *
 * Twin of `src/fux/api.py`.
 *
 * Mirrors `fux.api` in Python method for method, argument for argument, and
 * returns the same shapes (W-107 R3). A frontend project wants this; shelling
 * out to a binary is the fallback, not the point.
 *
 *     import { open } from 'fux-engine'
 *     const ix = await open('.')
 *     await ix.find('rollback', { top: 5 })
 *
 * 🔴 **Every ranking method goes through `runQuery`**, which is where
 * `.fux/tune.toml` enters. Calling the scan directly — which this file did
 * until 2026-09-12, and so did `api.py` — returns a different ranking from the
 * CLI on any tuned repo, silently. Three surfaces, one seam, or it is not one
 * API (SR-NODE-SEARCH decision 8; SR-API decision 6).
 *
 * 🔴 **`explain`, `graph` and `path` return what the CLI's `--json` prints**
 * (W-262; Arpit, 2026-10-04, W-251 #4) — computed by `verbs/graph.mjs`'s own
 * payload builders, exactly as `api.py` now calls `fux.graph`'s. Until then
 * both libraries returned older shapes of their own (`{id, community, members,
 * edges}`, a breadth-first best route, a walk seeded off the boosted ranking)
 * and both differed from both CLIs; SR-API decision 1's freeze was reopened for
 * these three and the library moved to the ruled shape.
 */
import { findRoot } from "./config/root.mjs";
import { FuxError } from "./errors.mjs";
import { runQuery, runFused } from "./query/run.mjs";
import { headingsFor } from "./query/headings.mjs";
import { recordFor, graphRecords, Shards } from "./store/reader.mjs";
import { buildPlane } from "./graph/plane.mjs";
import { loadTune } from "./config/tune.mjs";
import { loadOutput } from "./config/output.mjs";
import { answerPayload } from "./verbs/answer.mjs";
import { explainPayload, graphPayload, pathPayload, lazyRecords } from "./verbs/graph.mjs";

/** One ranked document. The `--json` `results[]` element, exactly. */
function result(r, headings = []) {
  return {
    id: r.id, loc: r.loc, title: r.title, score: r.score,
    archived: r.archived, tie: r.tie, mtime: r.mtime ?? null,
    // W-162 — a human pinned this document to this exact question, so its
    // position was set after the ranking. Always present; `false` is a claim.
    pinned: Boolean(r.pinned),
    // W-161 — the graph walk reached this document, and where the boost moved
    // it from. 🔴 **The one reason a `results` list may not be monotone in
    // `score`**: the order is `RRF(lexical rank, PPR rank)` and the number is
    // still BM25F, so a caller re-sorting by `score` is re-deriving the lexical
    // order. Always present; `false`/`null` on an unboosted row.
    boosted: Boolean(r.boosted), route: r.route ?? null,
    headings,
  };
}

class Index {
  constructor(root) {
    this.root = root;
    this._planeCache = null;
  }

  /** `.fux/output.toml`, for the values a caller did not pass — the CLI's own
   *  keys, exactly as `api.py::_output` reads them (L12). */
  _output() { return loadOutput(this.root, { enabled: true }); }

  /** Ranked document locations. The cheapest verb: no band, no headings. */
  async find(query, { top = null, under = null } = {}) {
    if (top === null) top = Number(this._output().resolve("find", "top", null, { asJson: false }));
    let results = runQuery(this.root, query, top, { useTune: true, wantConfidence: false, compose: true, shards: new Shards(this.root) })
      .results.map((r) => result(r));
    if (under !== null) {
      const prefix = under.endsWith("/") ? under : `${under}/`;
      results = results.filter((r) => r.loc === under || r.loc.startsWith(prefix));
    }
    return results;
  }

  /** A ranked list with scores — what you want when judging the engine.
   *
   * `band` defaults TRUE here and false on the CLI, deliberately: a caller in
   * code has already decided to read the object, and the block is the part
   * that says whether to trust it. */
  async ask(query, { top = null, band = null, queries = null, sections = null } = {}) {
    const output = this._output();
    band = Boolean(output.resolveApi("band", band));
    sections = Boolean(output.resolveApi("sections", sections));
    if (top === null) top = Number(output.resolve("ask", "top", null, { asJson: false }));
    const maxHeadings = Number(output.resolve("ask", "max_headings", null, { asJson: false }));
    // Loaded once and handed to every arm, so a band cannot be explained by a
    // different floor than the one that produced the ranking beside it.
    const tune = loadTune(this.root, { enabled: true });
    // W-242 Tier 0 — this call's one read of each shard, never kept on `this`:
    // an `Index` may live as long as its caller, and the index may not.
    const shards = new Shards(this.root);
    const { results, confidence, fused } = runFused(
      this.root, [query, ...(queries ?? [])], top, { tune, useTune: true, wantConfidence: band, compose: true, shards },
    );
    const rows = results.map((r) => result(
      r, sections ? headingsFor(recordFor(this.root, r.id, shards), query, maxHeadings) : [],
    ));
    return {
      results: rows,
      confidence: band && confidence ? confidence.asDict() : null,
      fused,
      /** The `--json` payload, exactly — `AskAnswer.as_dict()`'s twin.
       *  `confidence` is present ONLY when asked for: absent means NOT ASKED
       *  FOR, and is never a claim about the answer. */
      asDict() {
        const out = { results: this.results };
        if (this.confidence !== null) out.confidence = this.confidence;
        if (this.fused) out.fused = true;
        return out;
      },
    };
  }

  /** One passage, cited, with a freshness verdict on the bytes behind it.
   *
   * ⚠ **Read the verdict.** A caller that ignores it has thrown away the only
   * thing separating fux from a stale cache with good manners. */
  async answer(query, { band = null, noRefer = null, audit } = {}) {
    if (audit !== true && audit !== false) throw new FuxError("answer: `audit` is required (true or false)");
    const output = this._output();
    band = Boolean(output.resolveApi("band", band));
    noRefer = Boolean(output.resolveApi("no_refer", noRefer));
    const { payload } = answerPayload(this.root, {
      _: [query], band, noRefer, audit, json: true,
    });
    return {
      passages: payload.answer?.passages ?? [],
      citation: payload.citation ?? null,
      source: payload.source ?? "index",
      confidence: payload.confidence ?? null,
      audit: payload.audit ?? null,
      //: `--receipt` has no Node twin and is out of scope (W-107 R6). `null`
      //: rather than an absent field: a caller must be able to tell "no
      //: receipt was asked for" from "this reader cannot make one", and only
      //: the documented absence says the second.
      receipt: null,
      /** `Answer.as_dict()`'s twin. */
      asDict() {
        const out = {
          answer: this.passages.length ? { passages: this.passages } : null,
          citation: this.citation,
          source: this.source,
        };
        for (const key of ["confidence", "audit", "receipt"]) {
          if (this[key] !== null && this[key] !== undefined) out[key] = this[key];
        }
        return out;
      },
    };
  }

  /** `fux explain --json`: `{doc, edges, community}`. `doc` is an id or the
   *  `loc` a human types; an id the index does not hold throws `FuxError`. */
  async explain(doc) {
    const shards = new Shards(this.root);
    return explainPayload(lazyRecords(this.root, shards), this._plane(), doc);
  }

  /** `fux graph --json`: `{nodes}` — the seeds, then the PPR walk.
   *
   * A query or `seed`, never both. **The query's seeds are `lexical`'s top-k,
   * never `ask`'s boosted list** (SR-GRAPH decision 13). `kinds`, `linkIdf`
   * and `maxHops` are `--kinds`, `--link-idf` and `--max-hops`; the sizes come
   * from `.fux/tune.toml [graph]`, as the CLI's do. */
  async graph(query = null, { seed = null, kinds = null, linkIdf = null, maxHops = null } = {}) {
    const shards = new Shards(this.root);
    const tune = loadTune(this.root, { enabled: true });
    return graphPayload(this.root, lazyRecords(this.root, shards), this._plane(), tune, shards, {
      query: query ?? "", seed: seed ?? [], kinds: kinds && kinds.length ? kinds.join(",") : null,
      linkIdf: linkIdf === true, maxHops,
    });
  }

  /** `fux path --json`: `{from, to, paths, truncated}` — every simple directed
   *  route within `hops`, most reliable first. 🔴 **Read `truncated`.** */
  async path(src, dst, { hops = null } = {}) {
    // R4 (Arpit, 2026-09-27): read `[cli.path] hops` like the CLI.
    if (hops === null) hops = Number(this._output().resolve("path", "hops", null, { asJson: false }));
    const shards = new Shards(this.root);
    const tune = loadTune(this.root, { enabled: true });
    return pathPayload(lazyRecords(this.root, shards), this._plane(), tune, src, dst, hops);
  }

  /** The graph plane, rebuilt from the committed records and cached per Index.
   *
   * Built rather than loaded: `.fux/runtime/graph.json` is derived and
   * gitignored, so a library caller on a fresh clone has none — and Python's
   * CLI REFUSES there while this answers (SR-NODE-SEARCH decision 9). */
  _plane() {
    if (this._planeCache === null) {
      this._planeCache = buildPlane(graphRecords(this.root));
    }
    return this._planeCache;
  }
}

/** Open the index at `root`, or at the first fux root above it. */
export async function open(root = process.cwd()) {
  const resolved = findRoot(root);
  if (resolved === null) {
    throw new Error(`no fux root at or above ${root} — no fux.toml and no .git`);
  }
  return new Index(resolved);
}

export { Index };
