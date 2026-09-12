/** The library surface — the half of `fux-engine` that is not a CLI.
 *
 * Mirrors `fux.api` in Python method for method, argument for argument, and
 * returns the same shapes the `--json` payload carries (W-107 R3). A frontend
 * project wants this; shelling out to a binary is the fallback, not the point.
 *
 *     import { open } from 'fux-engine'
 *     const ix = await open('.')
 *     await ix.find('rollback', { top: 5 })
 */
import { findRoot } from "./config/root.mjs";
import { ask as scanAsk } from "./query/scan.mjs";

class Index {
  constructor(root) { this.root = root; }

  /** Ranked document locations. */
  async find(query, { top = 5 } = {}) {
    return scanAsk(this.root, query, top);
  }

  async ask() { throw new Error("ask lands in W-107 Phase 2"); }
  async answer() { throw new Error("answer lands in W-107 Phase 2"); }
  async explain() { throw new Error("explain lands in W-107 Phase 3"); }
  async graph() { throw new Error("graph lands in W-107 Phase 3"); }
  async path() { throw new Error("path lands in W-107 Phase 3"); }
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
