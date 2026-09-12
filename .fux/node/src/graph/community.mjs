/** Label propagation, determinized. Twin of `src/fux/graph/community.py`.
 *
 * An isolated node is its own community — honest rather than tidy: it says
 * *this document stands alone*, which is a fact a reader wants, and it costs
 * one entry.
 */
import { cmpCodePoints } from "../compat/pyfloat.mjs";

export const MAX_SWEEPS = 20;

/** Rename raw labels to `c0`, `c1`, … by (size desc, smallest member).
 *  Without this, a community's id is whichever node won the propagation —
 *  stable for one corpus, and liable to rename every community when a single
 *  document is added. */
function canonicalize(labels) {
  const members = new Map();
  for (const [node, label] of labels) {
    if (!members.has(label)) members.set(label, []);
    members.get(label).push(node);
  }
  for (const group of members.values()) group.sort(cmpCodePoints);

  const ordered = [...members.values()].sort((a, b) => {
    if (a.length !== b.length) return b.length - a.length;
    return cmpCodePoints(a[0], b[0]);
  });
  const out = new Map();
  ordered.forEach((group, i) => { for (const node of group) out.set(node, `c${i}`); });
  return out;
}

export function assign(graph) {
  if (!graph.nodes.length) return new Map();

  const labels = new Map(graph.nodes.map((n) => [n, n]));

  for (let sweep = 0; sweep < MAX_SWEEPS; sweep++) {
    let changed = false;
    for (const node of graph.nodes) {   // sorted: the visit order IS the determinism
      const neighbours = graph.neighbours(node);
      if (!neighbours.length) continue;
      const weightByLabel = new Map();
      for (const [neighbour, grade] of neighbours) {
        const label = labels.get(neighbour);
        weightByLabel.set(label, (weightByLabel.get(label) ?? 0) + grade);
      }
      // Heaviest label wins; ties go to the SMALLEST id, never to chance.
      let best = null, bestWeight = -Infinity;
      for (const [label, weight] of weightByLabel) {
        if (weight > bestWeight || (weight === bestWeight && cmpCodePoints(label, best) < 0)) {
          best = label; bestWeight = weight;
        }
      }
      if (best !== labels.get(node)) { labels.set(node, best); changed = true; }
    }
    if (!changed) break;
  }
  return canonicalize(labels);
}
