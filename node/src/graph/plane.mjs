/** The graph plane — read from `.fux/runtime/graph.json` when that file is
 *  fresh, rebuilt IN MEMORY otherwise. Twin of `src/fux/graph/plane.py`.
 *
 * **Fork A, ruled 2026-10-04 (Arpit; W-259, SR-NODE-SEARCH decision 9).** A
 * Node query used to rebuild the same graph from the committed records every
 * time — `buildPlane` + `assign`, ~55 of 383 ms on this repo — while the plane
 * sat on disk already built. `planeFor` now reads `graph.json` when the SAME
 * freshness test the accelerator uses says the plane is current
 * (`derive/accel.mjs::isFresh`, the transcription of `accel.py::is_fresh` that
 * `plane.py::load` also reuses), and rebuilds exactly as before otherwise.
 *
 * - **Never required.** No plane, a stale one, an unreadable or torn file, or
 *   a foreign schema is a rebuild, never an error: this reader exists for a
 *   clone where no `fux build` has run.
 * - 🔴 **The differential arm must never take this path.** Both builders write
 *   this file, and Node reading Python's would compare Python with Python and
 *   pass — W-107's N2 gate would prove nothing. `FUX_GRAPH_REBUILD=1`
 *   (`[env] graph_rebuild`) forces the rebuild, and `tools/differential/`
 *   sets it on every Node process it starts.
 * - **A read taken mid-rewrite cannot be kept.** Both `fux build`s rewrite this
 *   file IN PLACE (not by rename) and write `stamp.json` after it. Under a stamp
 *   that matches the shards, the bytes being written are the bytes already
 *   there (L4), so the only thing a concurrent reader can see is a PREFIX of a
 *   JSON object, which does not parse — and a parse failure is a rebuild. A
 *   stamp that does not match is a rebuild before anything is read.
 *
 * Owned, with its Python twin, by [SR-GRAPH](../../../records/0126_graph.md).
 */
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { Graph, edgesFromRecords } from "./model.mjs";
import { assign } from "./community.mjs";
import { cmpCodePoints } from "../compat/pyfloat.mjs";
import { fixed } from "../config/constants.mjs";
import { isFresh } from "../derive/accel.mjs";
import { runtimeDir } from "../derive/format.mjs";
import { graphRecords } from "../store/reader.mjs";

export const SCHEMA = fixed("graph", "schema");
export const GRAPH_NAME = fixed("graph", "file");

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

/** `[env] graph_rebuild` — the harness switch. Set to `1`, the read is skipped. */
export const REBUILD_ENV = fixed("env", "graph_rebuild");

/** The plane `graph.json` holds, or `null` when it cannot be trusted or read.
 *
 * `plane.py::load`'s checks — freshness by `accel.is_fresh`, then the schema
 * id — with one difference that is the whole of decision 9: where Python
 * REFUSES, this returns `null` and the caller rebuilds. Freshness is asked
 * FIRST, before the file is opened, so a stale plane costs a `stat` per shard
 * and not a read of the largest file `fux build` writes. */
export function loadFresh(root) {
  if (!isFresh(root)) return null;
  let payload;
  try {
    payload = JSON.parse(readFileSync(join(runtimeDir(root), GRAPH_NAME), "utf8"));
  } catch {
    return null; // absent, unreadable, or a prefix of a file being rewritten
  }
  if (payload === null || typeof payload !== "object" || payload.schema !== SCHEMA) return null;
  const { edges, communities } = payload;
  if (!Array.isArray(edges) || communities === null || typeof communities !== "object"
      || Array.isArray(communities)) return null;
  try {
    // The same `{src, kind, dst, grade}` objects `edgesFromRecords` makes, in
    // the order `build_plane` wrote them; `Graph` sorts again regardless.
    const lifted = edges.map(([src, kind, dst, grade]) => ({ src, kind, dst, grade }));
    return new GraphPlane(new Graph(lifted), new Map(Object.entries(communities)));
  } catch {
    return null;
  }
}

/** The plane for one call: `graph.json` when fresh, else rebuilt from the
 *  committed records through the caller's `Shards` (W-242 Tier 0).
 *
 *  Never throws for want of a plane — a rebuild is always possible. */
export function planeFor(root, shards = null) {
  if (process.env[REBUILD_ENV] !== "1") {
    const read = loadFresh(root);
    if (read !== null) return read;
  }
  return buildPlane(graphRecords(root, shards));
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
