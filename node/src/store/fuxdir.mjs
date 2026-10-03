/** `.fux/<name>/`, created and tagged as a cache directory.
 *  Twin of `src/fux/store/fuxdir.py`, narrowed to `derived_dir` (W-242 Tier 2).
 *
 * Node writes one derived directory, `runtime/`, and only from `fux build`, so
 * this is the one function of `fuxdir.py` it needs. The tag is
 * [SR-CACHEDIR-TAG](../../../records/0121_cachedir-tag.md)'s: written once,
 * never overwritten, from the template Python writes it from — inlined in the
 * bundle (`@fux-inline`), so a consumer's tree needs no Python half.
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fixed } from "../config/constants.mjs";

const FUXDIR = fixed("fuxdir", "dir");
const SIGNATURE = fixed("fuxdir", "cachedir_signature");

const TEMPLATE = /* @fux-inline src/fux/templates/cachedir-tag.txt */ readFileSync(
  new URL("../../../src/fux/templates/cachedir-tag.txt", import.meta.url),
  "utf8",
);

/** The tag's bytes — the template with the spec'd signature in place. */
export function cachedirTag() { return TEMPLATE.replace("{signature}", SIGNATURE); }

export function fuxDir(root) { return join(root, FUXDIR); }

/** `derived_dir` — the directory, created, with its tag written if absent. */
export function derivedDir(root, name) {
  const path = join(fuxDir(root), name);
  mkdirSync(path, { recursive: true });
  const tag = join(path, "CACHEDIR.TAG");
  if (!existsSync(tag)) writeFileSync(tag, Buffer.from(cachedirTag(), "ascii"));
  return path;
}
