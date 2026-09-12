/** `explain` · `graph` · `path` — the group that does NOT rank.
 *
 * `ask`/`find`/`answer` return documents ordered by relevance; these return
 * **relationships the documents themselves stated**. That is why they are a
 * group rather than three more read verbs.
 *
 * Node rebuilds the plane in memory from the committed records; it does not
 * read Python's derived `.fux/runtime/graph.json`.
 */
import { buildPlane } from "../graph/plane.mjs";
import { iterShardPaths, rawRecordLines } from "../store/reader.mjs";
import { ask as scanAsk } from "../query/scan.mjs";
import { cmpCodePoints } from "../compat/pyfloat.mjs";

function allRecords(root) {
  const out = [];
  for (const path of iterShardPaths(root)) {
    const [, lines] = rawRecordLines(path);
    for (const line of lines) out.push(JSON.parse(line.toString("utf8")));
  }
  return out;
}

/** One document's outbound edges and the community it landed in. */
export function runExplain(root, args) {
  const docId = args._[0];
  if (!docId) { process.stderr.write("error: explain needs a document id\n"); return 1; }
  const plane = buildPlane(allRecords(root));
  const edges = plane.graph.outEdges(docId);
  const community = plane.communityOf(docId);
  const payload = {
    id: docId,
    community,
    members: community ? plane.members(community) : [],
    edges: edges.map((e) => ({ kind: e.kind, dst: e.dst, grade: e.grade })),
  };
  if (args.json) process.stdout.write(JSON.stringify(payload, null, 2) + "\n");
  else {
    process.stdout.write(`${docId}\n  community: ${community ?? "(none)"}\n`);
    for (const e of edges) process.stdout.write(`  ${e.kind} -> ${e.dst} (${e.grade})\n`);
  }
  return 0;
}

/** The neighbourhood around a query's best answers. */
export function runGraph(root, args) {
  const query = args._.join(" ");
  const hops = args.hops ?? 1;
  const plane = buildPlane(allRecords(root));
  const seeds = scanAsk(root, query, args.top ?? 5).map((r) => r.id);

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
  const nodes = [...seen].sort((a, b) => (a[1] - b[1]) || cmpCodePoints(a[0], b[0]))
    .map(([id, distance]) => ({ id, distance, community: plane.communityOf(id) }));

  if (args.json) process.stdout.write(JSON.stringify({ seeds, hops, nodes }, null, 2) + "\n");
  else for (const n of nodes) process.stdout.write(`${"  ".repeat(n.distance)}${n.id}\n`);
  return 0;
}

/** How two documents are connected, most reliable route first.
 *  Breadth-first over the undirected graph, with the highest-grade route
 *  preferred at equal length — a shorter route through a weak edge is not
 *  more reliable than a longer one through strong ones. */
export function runPath(root, args) {
  const [from, to] = args._;
  if (!from || !to) { process.stderr.write("error: path needs two document ids\n"); return 1; }
  const plane = buildPlane(allRecords(root));
  const maxHops = args.hops ?? 6;

  let best = null;
  const queue = [[from, [from], 0]];
  const bestSeen = new Map([[from, 0]]);
  while (queue.length) {
    const [node, route, weight] = queue.shift();
    if (node === to) {
      if (best === null || route.length < best.route.length
          || (route.length === best.route.length && weight > best.weight)) {
        best = { route, weight };
      }
      continue;
    }
    if (route.length > maxHops) continue;
    for (const [neighbour, grade] of plane.graph.neighbours(node)) {
      if (route.includes(neighbour)) continue;
      const prior = bestSeen.get(neighbour);
      if (prior !== undefined && prior < route.length) continue;
      bestSeen.set(neighbour, route.length);
      queue.push([neighbour, [...route, neighbour], weight + grade]);
    }
  }

  const payload = best
    ? { from, to, hops: best.route.length - 1, route: best.route, weight: best.weight }
    : { from, to, hops: null, route: [], weight: 0 };
  if (args.json) process.stdout.write(JSON.stringify(payload, null, 2) + "\n");
  else if (best) process.stdout.write(best.route.join("\n  -> ") + "\n");
  else process.stdout.write(`no route from ${from} to ${to} within ${maxHops} hops\n`);
  return 0;
}
