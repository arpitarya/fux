/** A pinned index package's runtime: `.fux/runtime/pkg/<name>@<version>/` (W-299).
 *  Twin of `src/fux/derive/segments.py`.
 *
 * [SR-PKG-INDEX](../../../records/0166_pkg-index.md) decision 8. The segment is
 * verified first (`locateIndex` refuses a missing, other or drifted one before
 * a byte of it is read), then laid out as a repository — the shards in
 * `.fux/index/`, `identifiers.toml` in `.fux/config/`, `.fux/runtime/` built by
 * `build.mjs`, and a `pin` stamp holding the pin digest, written last — so the
 * bytes are Python's for the same pin. Rebuilt when the pin digest changes,
 * untouched when it does not; a directory no pin names is removed.
 *
 * `build` is the plane builder, passed in by `build.mjs` itself: importing
 * it here would be a cycle, and the bundler refuses one.
 */
import { copyFileSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fixed } from "../config/constants.mjs";
import { indexes, locateIndex } from "../config/plugins.mjs";
import { fuxDir } from "../store/fuxdir.mjs";
import { RUNTIME_DIR } from "./format.mjs";

function exists(path) {
  try { statSync(path); return true; } catch { return false; }
}

/** `.fux/runtime/pkg/`. */
export function packagesDir(root) {
  return join(fuxDir(root), RUNTIME_DIR, fixed("plugins.index", "runtime_child"));
}

/** `.fux/runtime/pkg/<name>@<version>/` for one pin. */
export function segmentDir(root, pin) {
  return join(packagesDir(root), `${pin.name}@${pin.version}`);
}

/** Was this pin's runtime built from exactly this pin digest? */
export function isCurrent(root, pin) {
  try {
    return Boolean(pin.digest) &&
      readFileSync(join(segmentDir(root, pin), fixed("plugins.index", "pin_stamp")), "utf8").trim() === pin.digest;
  } catch { return false; }
}

function copySegment(source, target) {
  const suffix = fixed("index", "shard_suffix");
  const indexDir = join(target, ...fixed("index", "dir").split("/"));
  const configDir = dirname(join(target, ...fixed("files", "identifiers").split("/")));
  for (const pattern of fixed("plugins.index", "segment")) {
    const destination = pattern.endsWith(suffix) ? indexDir : configDir;
    const parts = pattern.split("/");
    const last = parts.pop();
    const base = join(source, ...parts);
    const re = new RegExp(`^${last.split("*").map((s) => s.replace(/[.+?^${}()|[\]\\]/g, "\\$&")).join("[^/]*")}$`);
    let names = [];
    try { names = readdirSync(base); } catch { names = []; }
    for (const name of names.filter((n) => re.test(n)).sort()) {
      const from = join(base, name);
      if (!statSync(from).isFile()) continue;
      mkdirSync(destination, { recursive: true });
      copyFileSync(from, join(destination, name));
    }
  }
}

/** Verify `pin`, then build its runtime unless it is current. True if built. */
export function inflate(root, pin, build) {
  const source = locateIndex(root, pin); // refuses before anything is read
  if (isCurrent(root, pin)) return false;
  const target = segmentDir(root, pin);
  if (exists(target)) rmSync(target, { recursive: true, force: true });
  copySegment(source, target);
  build(target);
  writeFileSync(join(target, fixed("plugins.index", "pin_stamp")), `${pin.digest}\n`, "utf8");
  return true;
}

/** Every pinned segment, verified and current; stale children removed. */
export function inflateAll(root, build) {
  const pins = [...indexes(root).values()];
  const built = pins.filter((pin) => inflate(root, pin, build)).map((pin) => `${pin.name}@${pin.version}`);
  const wanted = new Set(pins.map((pin) => `${pin.name}@${pin.version}`));
  const directory = packagesDir(root);
  let children = [];
  try { children = readdirSync(directory).sort(); } catch { children = []; }
  for (const child of children) {
    const path = join(directory, child);
    if (statSync(path).isDirectory() && !wanted.has(child)) rmSync(path, { recursive: true, force: true });
  }
  return built.sort();
}
