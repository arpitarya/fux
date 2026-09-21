/** Where a document's bytes come from — **the local checkout, and nothing
 *  else.** Twin of the `GIT` half of `src/fux/refer/source.py`.
 *
 * 🔴 **Node never fetches, and this module is where that is enforced.** It
 * imports no transport and has no fetcher seam to inject one through. A `url:`
 * document reads `.fux/acquired/` if the blob is retained, and otherwise the
 * caller falls back to `source: "index"`.
 *
 * ⚠ **The pipe ruling does not reach here, and the reason is that Node does
 * not decode at all.** Python's `from_acquired` and `_fetch_url` now take the
 * `decoder=` stem the committed URL line declares (`urlsrc.declared_decoder`)
 * instead of the response's `Content-Type`; `fromAcquired` below returns the
 * retained **bytes** and never converts them, so there is no decoder for a
 * line to name. Nothing to port — stated rather than left as a silent gap,
 * because `tests/test_node_twins.py` asks the question and the answer is not
 * obvious from the diff.
 *
 * ⚠ **The suffix candidates below are a pre-existing narrowness, unchanged by
 * that ruling.** A retained blob is named by the format it holds, so a `.pdf`
 * or `.xlsx` blob is not among the four tried here and reads as absent. It was
 * equally absent when the name came from the `Content-Type`; the naming rule
 * moved and the gap did not.
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
