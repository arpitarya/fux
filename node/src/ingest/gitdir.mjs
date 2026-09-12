/** The committed directory declaration, read. Twin of `src/fux/ingest/gitdir.py`.
 *
 * ⚠ **NARROWED, and `tests/test_node_twins.py` says so.** `gitdir.py` is the
 * git-backed *walk* — what ingest visits, what it excludes, what a document's
 * `mtime` is. Node does not ingest, so none of that crosses. What crosses is
 * the pair of functions the **query** plane calls: which directories a human
 * declared archived, and whether a `loc` falls under one.
 *
 * **The ranking keys off the source list, never a path convention**
 * (ADR-DIR-LIST decision 4), which is why this is read at query time at all
 * rather than trusted to the `archived` property already on each record. The
 * property is stamped at ingest; the declaration is live. They agree until
 * somebody edits the list, and the whole point of the live read is the window
 * in between.
 */
import { readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { readDirs } from "./sourcelist.mjs";
import { parseToml } from "../config/toml.mjs";

//: Where the directory list lives when `fux.toml` does not say otherwise.
export const DEFAULT_DIRS_FILE = ".fux/sources/dirs";

/** `[sources] dirs_file`, or the default.
 *
 * **Tolerant on purpose, exactly as the caller is.** `_archived_ranking`
 * wraps the whole read in a `FuxError` catch and degrades to no archived
 * directories, so `ask`/`find` never fail because ranking metadata is missing.
 * A `fux.toml` this cannot read gets the same treatment. */
export function dirsFile(root) {
  const path = join(root, "fux.toml");
  try {
    if (!statSync(path).isFile()) return DEFAULT_DIRS_FILE;
    const data = parseToml(readFileSync(path, "utf8"), path);
    const value = data?.sources?.dirs_file;
    return typeof value === "string" && value.trim() ? value.trim() : DEFAULT_DIRS_FILE;
  } catch {
    return DEFAULT_DIRS_FILE;
  }
}

/** Included entries declared `archived=true`. Never derived from a path. */
export function archivedDirs(root, relPath = null) {
  return readDirs(root, relPath ?? dirsFile(root))
    .filter((entry) => !entry.exclude && entry.attrs.archived === "true")
    .map((entry) => entry.value);
}

/** `loc` falls under one of `dirs` — a directory entry or an exact single-file
 *  entry, mirroring how the walk resolves an entry against the filesystem.
 *
 *  **The one definition**, imported by `query/rank.mjs` for both the marker and
 *  the demotion. A second copy would let the two disagree about one document. */
export function isArchivedLoc(loc, dirs) {
  for (const d of dirs) {
    if (loc === d || loc.startsWith(d.endsWith("/") ? d : `${d}/`)) return true;
  }
  return false;
}

/** The archived set for this root, or an EMPTY set when it cannot be read.
 *
 * The tolerance `_archived_ranking` extends, in one place so every caller gets
 * it: a corpus with no `fux.toml`, no dirs list, or a malformed one still
 * answers — it simply demotes nothing. **The tune file is NOT covered by this**
 * (`config/tune.mjs`), and the asymmetry is deliberate: an absent dirs list is
 * the normal case for a corpus nobody has declared anything about, while a tune
 * file that exists and will not parse means somebody edited it and got it wrong. */
export function archivedDirSet(root) {
  try {
    return new Set(archivedDirs(root));
  } catch {
    return new Set();
  }
}
