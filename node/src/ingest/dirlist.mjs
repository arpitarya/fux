/** The committed directory list, read. Twin of `src/fux/ingest/dirlist.py`.
 *
 * **Owned by [SR-DIR-LIST](../../../records/0120_dir-list.md)** since
 * 2026-10-05 (W-261): a pure move of `readDirs` out of `sourcelist.mjs` and
 * `archivedDirs` out of `gitdir.mjs`. Node does not ingest, so it carries the
 * one fact the query plane reads — which directories a human declared
 * `archived=true` — and not `source_dirs`, `source_excludes` or `enrich_dirs`.
 * The grammar itself (`parseDirs`) stays `sourcelist.mjs`'s.
 */
import { readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { FuxError } from "../errors.mjs";
import { parseDirs } from "./sourcelist.mjs";

/** Read and parse one `dirs` list, or fail loudly naming the path. */
export function readDirs(root, relPath) {
  const path = join(root, relPath);
  try {
    if (!statSync(path).isFile()) throw new Error("absent");
  } catch {
    throw new FuxError(
      `${relPath} not found (looked in ${path}) — create it with one directory or ` +
      "file per line (a line may carry `archived=true`), or run `fux setup` to write a starter",
    );
  }
  return parseDirs(readFileSync(path, "utf8"), path);
}

/** Included entries declared `archived=true`. Never derived from a path. */
export function archivedDirs(root, relPath) {
  return readDirs(root, relPath)
    .filter((entry) => !entry.exclude && entry.attrs.archived === "true")
    .map((entry) => entry.value);
}
