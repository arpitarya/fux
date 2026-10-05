/** `.fux/<name>/`, created and tagged as a cache directory.
 *  Twin of `src/fux/store/cachedir.py` (W-261; W-242 Tier 2 before it).
 *
 * The tag is [SR-CACHEDIR-TAG](../../../records/0121_cachedir-tag.md)'s, and
 * that record owns both halves: written once, never overwritten, from the
 * template Python writes it from — inlined in the bundle (`@fux-inline`), so a
 * consumer's tree needs no Python half.
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fixed } from "../config/constants.mjs";
import { fuxDir } from "./fuxdir.mjs";

const SIGNATURE = fixed("fuxdir", "cachedir_signature");

const TEMPLATE = /* @fux-inline src/fux/templates/cachedir-tag.txt */ readFileSync(
  new URL("../../../src/fux/templates/cachedir-tag.txt", import.meta.url),
  "utf8",
);

/** The tag's bytes — the template with the spec'd signature in place. */
export function cachedirTag() { return TEMPLATE.replace("{signature}", SIGNATURE); }

/** `derived_dir` — the directory, created, with its tag written if absent. */
export function derivedDir(root, name) {
  const path = join(fuxDir(root), name);
  mkdirSync(path, { recursive: true });
  const tag = join(path, "CACHEDIR.TAG");
  if (!existsSync(tag)) writeFileSync(tag, Buffer.from(cachedirTag(), "ascii"));
  return path;
}
