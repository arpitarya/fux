/** The graph's shape. Twin of `src/fux/graph/model.py`.
 *
 * **Every accessor returns SORTED lists, and that is L3, not tidiness.**
 * Community assignment and PPR both accumulate over neighbours, and float
 * accumulation is not associative — an unsorted traversal makes the same
 * corpus produce different bytes on different runs.
 */
import { cmpCodePoints } from "../compat/pyfloat.mjs";

export const TAG_PREFIX = "tag:";

/** Python sorts an `Edge` dataclass field-by-field in declaration order:
 *  `(src, kind, dst, grade)`. Strings by code point, ints numerically. */
function cmpEdge(a, b) {
  let c = cmpCodePoints(a.src, b.src); if (c) return c;
  c = cmpCodePoints(a.kind, b.kind); if (c) return c;
  c = cmpCodePoints(a.dst, b.dst); if (c) return c;
  return a.grade - b.grade;
}

/** Python sorts a `(str, int)` tuple the same way. */
function cmpNeighbour(a, b) {
  const c = cmpCodePoints(a[0], b[0]);
  return c !== 0 ? c : a[1] - b[1];
}

export class Graph {
  constructor(edges) {
    this.edges = [...edges].sort(cmpEdge);
    this._out = new Map();
    this._both = new Map();
    const nodes = new Set();
    for (const edge of this.edges) {
      nodes.add(edge.src); nodes.add(edge.dst);
      if (!this._out.has(edge.src)) this._out.set(edge.src, []);
      this._out.get(edge.src).push(edge);
      if (!this._both.has(edge.src)) this._both.set(edge.src, []);
      this._both.get(edge.src).push([edge.dst, edge.grade]);
      if (!this._both.has(edge.dst)) this._both.set(edge.dst, []);
      this._both.get(edge.dst).push([edge.src, edge.grade]);
    }
    this.nodes = [...nodes].sort(cmpCodePoints);
    for (const adjacency of this._both.values()) adjacency.sort(cmpNeighbour);
  }

  /** Outbound edges, canonically ordered. `path` and `explain` read this. */
  outEdges(node) { return [...(this._out.get(node) ?? [])]; }
  /** Undirected `[neighbour, grade]` pairs. Community and PPR read this. */
  neighbours(node) { return [...(this._both.get(node) ?? [])]; }
  /** Nodes that are documents — everything that is not a tag. */
  documents() { return this.nodes.filter((n) => !n.startsWith(TAG_PREFIX)); }
  get length() { return this.nodes.length; }
}

/** Lift the committed `edges` arrays into edges. They are already resolved and
 *  already dropped if dangling, so there is nothing to validate — only lift. */
export function edgesFromRecords(records) {
  const out = [];
  for (const record of records) {
    for (const edge of record.edges || []) {
      out.push({ src: record.id, kind: edge.kind, dst: edge.dst, grade: Number(edge.grade) });
    }
  }
  return out.sort(cmpEdge);
}

export { cmpEdge };
