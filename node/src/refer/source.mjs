/** Where a document's bytes come from — **the local checkout, and nothing
 *  else.** Twin of the `GIT` half of `src/fux/refer/source.py`.
 *
 * 🔴 **Node never fetches, and this module is where that is enforced.** It
 * imports no transport and has no fetcher seam to inject one through. A `url:`
 * document reads `.fux/acquired/` if the blob is retained, and otherwise the
 * caller falls back to `source: "index"`.
 *
 * Owned, with its Python twin, by [SR-URL-FRESHNESS](../../../records/0147_url-freshness.md).
 */
import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { contentSha } from "../store/format.mjs";

export const GIT = "git";
export const URL = "url";

export function resolve(docId) {
  if (docId.startsWith("file:")) return [GIT, docId.slice(5)];
  if (docId.startsWith("url:")) return [URL, docId.slice(4)];
  return [GIT, docId];
}

/** Read a document from the working tree. **Reading your own checkout is not
 *  a fetch**, so this happens under every policy. */
export function readLocal(root, relPath) {
  const path = join(root, relPath);
  if (!existsSync(path)) {
    throw new Error(`cited document is no longer in the working tree: ${relPath}`);
  }
  const raw = readFileSync(path);
  return [raw, contentSha(raw)];
}

/** The retained bytes for a URL, from `.fux/acquired/`, or `null`.
 *  NOT rebuildable — only re-acquirable, and only while the source still
 *  exists, which is why the acquired plane has its own kind in `.fux/`. */
export function fromAcquired(root, sha) {
  const path = join(root, ".fux", "acquired", "objects", sha.slice(0, 2), sha);
  for (const candidate of [path, path + ".md", path + ".txt", path + ".html"]) {
    if (existsSync(candidate)) {
      const raw = readFileSync(candidate);
      return [raw, contentSha(raw)];
    }
  }
  return null;
}
