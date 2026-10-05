/** The committed directory declaration, read. Twin of `src/fux/ingest/gitdir.py`.
 *
 * ⚠ **NARROWED, and `tests/test_node_twins.py` says so.** `gitdir.py` is the
 * git-backed *walk* — what ingest visits, what it excludes, what a document's
 * `mtime` is. Node does not ingest, so none of that crosses. What crosses is
 * the pair of functions the **query** plane calls: which directories a human
 * declared archived, and whether a `loc` falls under one.
 *
 * **The ranking keys off the source list, never a path convention**
 * (SR-DIR-LIST decision 4), which is why this is read at query time at all
 * rather than trusted to the `archived` property already on each record. The
 * property is stamped at ingest; the declaration is live. They agree until
 * somebody edits the list, and the whole point of the live read is the window
 * in between.
 */
import { readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { archivedDirs } from "./dirlist.mjs";
import { parseToml } from "../config/toml.mjs";
import { fixed } from "../config/constants.mjs";
import { FuxError } from "../errors.mjs";

//: What a missing key's error tells the reader to do — `config.py`'s sentence.
const FIX_HINT = "`fux doctor --fix` writes every missing key from the template `fux setup` uses";

/** `fux.toml`'s `[sources] dirs_file` — `null` when there is no `fux.toml`.
 *
 * ⚠ **It fell back to `.fux/sources/dirs` until W-225 stage 3b**, on an absent
 * file, an absent key, or a file it could not parse. SR-LAW-12 leaves no
 * default path: an absent `fux.toml` is `null` (no declaration, so nothing is
 * archived — `_archived_ranking`'s tolerance), and a present one must carry
 * the key.
 *
 * **Narrowed, and said so:** Python's `config.load` also refuses retired and
 * unknown keys and validates every value; this reader checks only that
 * `[sources] dirs_file` is present, the one key it reads. */
export function dirsFile(root) {
  const path = join(root, fixed("files", "config"));
  let isFile = false;
  try {
    isFile = statSync(path).isFile();
  } catch {
    isFile = false;
  }
  if (!isFile) return null;
  const data = parseToml(readFileSync(path, "utf8"), path);
  const value = data?.sources?.dirs_file;
  if (value === undefined) throw new FuxError(`${path}:\n  [sources] dirs_file is missing\n  ${FIX_HINT}`);
  if (typeof value !== "string" || !value.trim()) {
    throw new FuxError(`${path}: [sources] dirs_file must be a path to a line-oriented directory list`);
  }
  return value.trim();
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
 * it: a corpus with no `fux.toml`, or with no readable dirs list, still
 * answers — it simply demotes nothing. ⚠ **A `fux.toml` that is present and
 * lacks `dirs_file` throws** (W-225 stage 3b), as Python's does. **The tune
 * file is NOT covered by this**
 * (`config/tune.mjs`), and the asymmetry is deliberate: an absent dirs list is
 * the normal case for a corpus nobody has declared anything about, while a tune
 * file that exists and will not parse means somebody edited it and got it wrong. */
export function archivedDirSet(root) {
  const relPath = dirsFile(root);
  if (relPath === null) return new Set();
  try {
    return new Set(archivedDirs(root, relPath));
  } catch {
    return new Set();
  }
}
