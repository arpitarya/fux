/** Walking the graph: PPR-lite expansion, and bounded route enumeration.
 *  Twin of `src/fux/graph/walk.py`.
 *
 * ## The walk is LAZY, and a plain one is wrong here
 *
 * A plain random walk on a bipartite-ish graph — which a corpus of documents
 * and tags very much is — **oscillates by parity** when it is stopped after a
 * fixed number of steps. Moving *all* of a node's mass to its neighbours each
 * iteration means that at `ITERATIONS = 3` a node three hops away can outscore
 * a node two hops away purely because 3 has the same parity as the count.
 *
 * Measured on a four-node path `a-b-c-d`, seeded at `a`:
 *
 * | | a | b | c | d |
 * |---|---|---|---|---|
 * | non-lazy walk, 3 iterations | 0.204 | 0.588 | **0.054** | **0.154** |
 * | lazy walk, 3 iterations | 0.446 | 0.406 | 0.129 | 0.019 |
 *
 * `d` outranking `c` is not a tuning preference, it is wrong. Laziness makes
 * the chain aperiodic, which is the textbook device for removing periodic
 * behaviour, and it costs one term (Levin & Peres, *Markov Chains and Mixing
 * Times*, §1.3).
 *
 * The determinism discipline carries over unchanged: a **fixed iteration
 * count** instead of a convergence test, and **sorted traversal** so float
 * accumulation order is stable. Both are L3, not tidiness.
 */
import { cmpCodePoints } from "../compat/pyfloat.mjs";

//: Restart probability is `1 - DAMPING`. PageRank's published default.
export const DAMPING = 0.85;
//: A count, not a convergence test. Three iterations reach two hops of
//: structure, which is the neighbourhood the expansion is for.
export const ITERATIONS = 3;
//: Fraction of a node's mass that stays put each step — what makes the chain
//: aperiodic. 0.5 is the conventional lazy chain.
export const LAZINESS = 0.5;
//: What each additional hop costs a route's reliability. A route that needs two
//: intermediaries is not "slightly" less trustworthy than a direct link.
export const HOP_DECAY = 0.5;

//: `ingest/edges.py`'s `EXTRACTED_GRADE`. Node does not ingest, so the constant
//: is carried rather than the module: a grade arrives on the committed record
//: and this is only the denominator that normalises a direct link to 1.0.
export const EXTRACTED_GRADE = 10;

/** Personalized PageRank, lite — power iteration over the seed neighbourhood.
 *
 * Seeds are personalized **by rank, not by score**: the document the ranker
 * liked most starts with the most mass, so expansion inherits the ranker's
 * opinion instead of flattening it. Rank rather than score because scores are
 * RRF values on one path and raw BM25F on another, and are not comparable.
 *
 * The three parameters are `[graph]`'s. **They are arguments rather than
 * module reads on purpose**: the parity artefact above is a joint property of
 * `iterations` and `laziness`, and a caller that could set one without the
 * other would be able to reintroduce it silently. */
//: **The three walk parameters W-161 will turn on for `ask`, exposed and
//: INERT at their defaults** (W-160). Twin of `walk.py`'s block — see it for
//: why the mechanism lands before the composition that uses it.
//:
//: `ALL_KINDS` is the sentinel for *no selection*, spelled rather than `null`
//: so a call site reads as a choice.
export const ALL_KINDS = null;

//: The edge kinds `ingest/edges.py` mints.
export const EDGE_KINDS = ["ref", "tag", "code", "supersedes"];

/** `graph.neighbours(node)`, optionally narrowed to some edge kinds.
 *
 * ⚠ **`ALL_KINDS` returns `graph.neighbours` UNTOUCHED, not a filtered copy
 * that happens to keep everything.** `neighbours` is pre-sorted and the walk
 * accumulates floats over it in that order; rebuilding the array would be
 * equal today and is one refactor away from not being. */
function narrow(graph, node, kinds) {
  const neighbours = graph.neighbours(node);
  if (kinds === ALL_KINDS) return neighbours;
  const keep = new Set();
  for (const edge of graph.outEdges(node)) if (kinds.has(edge.kind)) keep.add(edge.dst);
  for (const edge of graph.edges) {
    if (edge.dst === node && kinds.has(edge.kind)) keep.add(edge.src);
  }
  return neighbours.filter(([n]) => keep.has(n));
}

/** How many edges point AT each node. The input to `linkIdf`. */
function inDegree(graph) {
  const counts = new Map();
  for (const edge of graph.edges) counts.set(edge.dst, (counts.get(edge.dst) ?? 0) + 1);
  return counts;
}

/** An inbound edge's discount, by how many other documents point at it.
 *
 * `1 / (1 + ln(1 + inDegree))`. **Named after IDF because it is the same
 * idea**, and deliberately not `1/inDegree`, which would make a hub weightless
 * and turn *widely cited* into *ignored*. Twin of `walk.py::link_idf`. */
export function linkIdf(inDeg) {
  return 1.0 / (1.0 + Math.log1p(Math.max(inDeg, 0)));
}

/** Every node within `maxHops` undirected steps of a seed, seeds included.
 *  Over `neighbours`, the same adjacency the walk uses — a bound computed over
 *  `outEdges` would exclude a node the walk can still reach backwards. */
function hopsFromSeeds(graph, seeds, maxHops) {
  let frontier = new Set(seeds);
  const seen = new Set(seeds);
  for (let i = 0; i < Math.max(maxHops, 0); i++) {
    const next = new Set();
    for (const node of [...frontier].sort(cmpCodePoints)) {
      for (const [neighbour] of graph.neighbours(node)) {
        if (!seen.has(neighbour)) { seen.add(neighbour); next.add(neighbour); }
      }
    }
    if (!next.size) break;
    frontier = next;
  }
  return seen;
}

export function ppr(graph, seeds, {
  damping = DAMPING, iterations = ITERATIONS, laziness = LAZINESS,
  kinds = ALL_KINDS, linkIdfOn = false, maxHops = null,
} = {}) {
  if (!seeds.length || !graph.edges.length) return new Map();
  const hopOf = maxHops !== null && maxHops !== undefined
    ? hopsFromSeeds(graph, seeds, maxHops)
    : null;
  const inbound = linkIdfOn ? inDegree(graph) : null;

  const seedMass = new Map();
  seeds.forEach((doc, i) => { if (!seedMass.has(doc)) seedMass.set(doc, 1.0 / (i + 1)); });
  let total = 0.0;
  for (const v of seedMass.values()) total += v;
  for (const [k, v] of seedMass) seedMass.set(k, v / total);

  let scores = new Map(seedMass);
  for (let it = 0; it < iterations; it++) {
    const next = new Map();
    // sorted: reproducible float accumulation, by CODE POINT as Python sorts.
    for (const node of [...scores.keys()].sort(cmpCodePoints)) {
      const mass = scores.get(node);
      // Laziness: part of the mass stays where it is.
      next.set(node, (next.get(node) ?? 0.0) + damping * laziness * mass);
      let neighbours = narrow(graph, node, kinds);
      if (hopOf !== null) neighbours = neighbours.filter(([n]) => hopOf.has(n));
      if (inbound !== null) {
        neighbours = neighbours.map(([n, g]) => [n, g * linkIdf(inbound.get(n) ?? 0)]);
      }
      let outWeight = 0;
      for (const [, grade] of neighbours) outWeight += grade;
      if (!outWeight) continue;
      for (const [neighbour, grade] of neighbours) {
        const share = damping * (1 - laziness) * mass * (grade / outWeight);
        next.set(neighbour, (next.get(neighbour) ?? 0.0) + share);
      }
    }
    for (const [node, mass] of seedMass) {   // restart
      next.set(node, (next.get(node) ?? 0.0) + (1 - damping) * mass);
    }
    scores = next;
  }
  return scores;
}

/** Top non-seed nodes by PPR score. Ties break on id, as everywhere.
 *
 * The walk parameters are forwarded rather than absorbed: `expand` decides how
 * many nodes come back, `ppr` decides what the numbers mean. */
export function expand(graph, seeds, {
  limit, minScore = 0.0, damping = DAMPING, iterations = ITERATIONS, laziness = LAZINESS,
  kinds = ALL_KINDS, linkIdfOn = false, maxHops = null,
} = {}) {
  const seedSet = new Set(seeds);
  const walked = ppr(graph, seeds, {
    damping, iterations, laziness, kinds, linkIdfOn, maxHops,
  });
  const ranked = [...walked].filter(([node, score]) => !seedSet.has(node) && score >= minScore);
  ranked.sort((a, b) => (a[1] !== b[1] ? (a[1] > b[1] ? -1 : 1) : cmpCodePoints(a[0], b[0])));
  return ranked.slice(0, limit);
}

/** Grade product, decayed per extra hop. A direct EXTRACTED link is 1.0.
 *
 * Two properties are load-bearing: it is bounded by 1.0, and it **strictly
 * decreases with distance** — so a reader can tell a stated relationship from
 * an inferred chain of three. The second holds only for `hopDecay < 1.0`, and
 * `tune.toml` accepts 1.0: a consumer who sets it is saying distance should
 * cost nothing, and the cost of saying it is that a three-hop chain can tie a
 * direct link. Stated rather than clamped. */
export function reliability(hops, { hopDecay = HOP_DECAY } = {}) {
  let score = 1.0;
  for (const edge of hops) score *= edge.grade / EXTRACTED_GRADE;
  return score * (hopDecay ** (hops.length - 1));
}

/** Every simple directed route `src` → `dst` of at most `hops` edges.
 *
 * Simple — a node is never revisited within a route — because a cycle adds
 * length without adding evidence, and enumerating cycles is how a bounded
 * search stops being bounded. Depth-first over `outEdges`, which is sorted, so
 * the enumeration order is fixed before the final sort ever runs.
 *
 * `hopDecay` changes the *ordering* of routes and never which routes exist:
 * enumeration is bounded by `hops`, a CLI argument and deliberately not a
 * tunable — a tune file that could widen a search would make `--hops 2` mean
 * different things in two repos. */
export function routes(graph, src, dst, { hops, limit = 10, hopDecay = HOP_DECAY } = {}) {
  if (hops < 1 || src === dst) return [];

  const found = [];
  const walk = (node, trail, seen) => {
    if (trail.length >= hops) return;
    for (const edge of graph.outEdges(node)) {
      if (seen.has(edge.dst)) continue;
      const step = [...trail, edge];
      if (edge.dst === dst) {
        found.push({ hops: step, reliability: reliability(step, { hopDecay }) });
        continue;  // a longer route to the same place is not more evidence
      }
      walk(edge.dst, step, new Set([...seen, edge.dst]));
    }
  };
  walk(src, [], new Set([src]));

  // Most reliable first; ties by the route's own ids, never by walk order —
  // Python compares the `[(kind, dst), ...]` list element by element.
  found.sort((a, b) => {
    if (a.reliability !== b.reliability) return a.reliability > b.reliability ? -1 : 1;
    const n = Math.min(a.hops.length, b.hops.length);
    for (let i = 0; i < n; i++) {
      let c = cmpCodePoints(a.hops[i].kind, b.hops[i].kind); if (c) return c;
      c = cmpCodePoints(a.hops[i].dst, b.hops[i].dst); if (c) return c;
    }
    return a.hops.length - b.hops.length;
  });
  return found.slice(0, limit);
}
