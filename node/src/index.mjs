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
 * ⚠ **`explain`, `graph` and `path` here are `api.py`'s shapes, which are NOT
 * the CLI's.** The Python API grew its own simpler helpers for the graph lane —
 * `{id, community, members, edges}` rather than the CLI's `{doc, edges,
 * community}`, a breadth-first best route rather than every enumerated route.
 * This file mirrors `api.py` because `api.py` is its twin; that the two Python
 * surfaces disagree is `api.py`'s business and is recorded in SR-API decision
 * 6, not smoothed over here.
 */
import { findRoot } from "./config/root.mjs";
import { runQuery, runFused } from "./query/run.mjs";
import { headingsFor } from "./query/headings.mjs";
import { recordFor, iterShardPaths, rawRecordLines } from "./store/reader.mjs";
import { buildPlane } from "./graph/plane.mjs";
import { loadTune } from "./config/tune.mjs";
import { answerPayload } from "./verbs/answer.mjs";
import { cmpCodePoints } from "./compat/pyfloat.mjs";

/** One ranked document. The `--json` `results[]` element, exactly. */
function result(r, headings = []) {
  return {
    id: r.id, loc: r.loc, title: r.title, score: r.score,
    archived: r.archived, tie: r.tie, mtime: r.mtime ?? null,
    // W-162 — a human pinned this document to this exact question, so its
    // position was set after the ranking. Always present; `false` is a claim.
    pinned: Boolean(r.pinned), headings,
  };
}

class Index {
  constructor(root) {
    this.root = root;
    this._planeCache = null;
  }

  /** Ranked document locations. The cheapest verb: no band, no headings. */
  async find(query, { top = 5, under = null } = {}) {
    let results = runQuery(this.root, query, top).results.map((r) => result(r));
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
  async ask(query, { top = 5, band = true, queries = null, sections = true } = {}) {
    // Loaded once and handed to every arm, so a band cannot be explained by a
    // different floor than the one that produced the ranking beside it.
    const tune = loadTune(this.root);
    const { results, confidence, fused } = runFused(
      this.root, [query, ...(queries ?? [])], top, { tune, wantConfidence: band },
    );
    const rows = results.map((r) => result(
      r, sections ? headingsFor(recordFor(this.root, r.id), query) : [],
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
  async answer(query, { band = true, noRefer = false, audit = false } = {}) {
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

  /** One document's outbound edges and the community it landed in. */
  async explain(docId) {
    const plane = this._plane();
    const community = plane.communityOf(docId);
    return {
      id: docId,
      community,
      members: community ? plane.members(community) : [],
      edges: plane.graph.outEdges(docId).map((e) => ({ kind: e.kind, dst: e.dst, grade: e.grade })),
    };
  }

  /** The neighbourhood around a query's best answers. */
  async graph(query, { hops = 1, top = 5 } = {}) {
    const plane = this._plane();
    const seeds = (await this.find(query, { top })).map((r) => r.id);
    const seen = new Map(seeds.map((s) => [s, 0]));
    let frontier = [...seeds];
    for (let depth = 1; depth <= hops; depth++) {
      const next = [];
      for (const node of frontier) {
        for (const [neighbour] of plane.graph.neighbours(node)) {
          if (!seen.has(neighbour)) { seen.set(neighbour, depth); next.push(neighbour); }
        }
      }
      frontier = next;
    }
    const nodes = [...seen]
      .sort((a, b) => (a[1] - b[1]) || cmpCodePoints(a[0], b[0]))
      .map(([id, distance]) => ({ id, distance, community: plane.communityOf(id) }));
    return { seeds, hops, nodes };
  }

  /** How two documents are connected, most reliable route first.
   *
   * Breadth-first, preferring the highest-grade route at equal length: a
   * shorter route through a weak edge is not more reliable than a longer one
   * through strong ones. */
  async path(src, dst, { hops = 6 } = {}) {
    const plane = this._plane();
    let best = null;
    const queue = [[src, [src], 0]];
    const bestSeen = new Map([[src, 0]]);
    while (queue.length) {
      const [node, route, weight] = queue.shift();
      if (node === dst) {
        if (best === null || route.length < best[0].length
            || (route.length === best[0].length && weight > best[1])) {
          best = [route, weight];
        }
        continue;
      }
      if (route.length > hops) continue;
      for (const [neighbour, grade] of plane.graph.neighbours(node)) {
        if (route.includes(neighbour)) continue;
        const prior = bestSeen.get(neighbour);
        if (prior !== undefined && prior < route.length) continue;
        bestSeen.set(neighbour, route.length);
        queue.push([neighbour, [...route, neighbour], weight + grade]);
      }
    }
    if (best === null) return { from: src, to: dst, hops: null, route: [], weight: 0 };
    return { from: src, to: dst, hops: best[0].length - 1, route: best[0], weight: best[1] };
  }

  /** The graph plane, rebuilt from the committed records and cached per Index.
   *
   * Built rather than loaded: `.fux/runtime/graph.json` is derived and
   * gitignored, so a library caller on a fresh clone has none — and Python's
   * CLI REFUSES there while this answers (SR-NODE-SEARCH decision 9). */
  _plane() {
    if (this._planeCache === null) {
      const records = [];
      for (const path of iterShardPaths(this.root)) {
        const [, lines] = rawRecordLines(path);
        for (const line of lines) records.push(JSON.parse(line.toString("utf8")));
      }
      this._planeCache = buildPlane(records);
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
