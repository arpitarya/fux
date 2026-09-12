/** The graph plane, rebuilt IN MEMORY. Twin of `src/fux/graph/plane.py`.
 *
 * 🔴 **Node does not read Python's `.fux/runtime/graph.json`** — it is a
 * derived file and Node's contract is the committed plane. It rebuilds the
 * same graph from the same records and **its digest must equal Python's**,
 * which is W-107's N2 gate. Reading the derived file instead would prove
 * nothing about whether the two agree.
 */
import { createHash } from "node:crypto";
import { Graph, edgesFromRecords } from "./model.mjs";
import { assign } from "./community.mjs";
import { cmpCodePoints } from "../compat/pyfloat.mjs";

export const SCHEMA = "fux.graph.v1";
export const GRAPH_NAME = "graph.json";

export class GraphPlane {
  constructor(graph, communities) { this.graph = graph; this.communities = communities; }
  communityOf(node) { return this.communities.get(node) ?? null; }
  members(label) {
    return [...this.communities].filter(([, c]) => c === label).map(([n]) => n).sort(cmpCodePoints);
  }
}

export function buildPlane(records) {
  const graph = new Graph(edgesFromRecords(records));
  return new GraphPlane(graph, assign(graph));
}

/** The exact bytes Python's `build_plane` writes, so the digests can be
 *  compared without either side reading the other's file.
 *
 *  A list of lists rather than a list of objects: machine-written and
 *  machine-read, and four values per edge beats four repeated keys at a
 *  million of them. */
export function planeBytes(plane) {
  const communities = {};
  for (const node of [...plane.communities.keys()].sort(cmpCodePoints)) {
    communities[node] = plane.communities.get(node);
  }
  const payload = {
    schema: SCHEMA,
    edges: plane.graph.edges.map((e) => [e.src, e.kind, e.dst, e.grade]),
    communities,
  };
  return JSON.stringify(payload) + "\n";
}

export function planeDigest(plane) {
  return createHash("sha256").update(planeBytes(plane), "utf8").digest("hex");
}
