/** The committed directory declaration, read. Twin of `src/fux/acquire/gitdir.py`.
 *
 * ⚠ **NARROWED, and `tests/test_node_twins.py` says so.** `gitdir.py` is the
 * git-backed *walk* — what ingest visits, what it excludes, what a document's
 * `mtime` is. Node does not ingest, so none of that crosses. What crosses is
 * the pair of functions the **query** plane calls: which directories a human
 * declared archived, and whether a `loc` falls under one.
 *
 * **The ranking keys off the source list, never a path convention**
 * (SR-SOURCES), which is why this is read at query time at all
 * rather than trusted to the `archived` property already on each record. The
 * property is stamped at ingest; the declaration is live. They agree until
 * somebody edits the list, and the whole point of the live read is the window
 * in between.
 */
import { readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { parseSources, legacyMessage } from "./sourcelist.mjs";
import { parseToml } from "../config/toml.mjs";
import { fixed } from "../config/constants.mjs";
import { FuxError } from "../errors.mjs";

//: What a missing key's error tells the reader to do — `config.py`'s sentence.
const FIX_HINT = "`fux doctor --fix` writes every missing key from the template `fux setup` uses";

/** `fux.toml`'s `[sources] sources_file` — `null` when there is no `fux.toml`.
 *
 * SR-LAW-12 leaves no default path: an absent `fux.toml` is `null` (no
 * declaration, so nothing is archived — `_archived_ranking`'s tolerance), and
 * a present one must carry the key. **The two keys it replaced (W-294),
 * `dirs_file` and `urls_file`, are refused by name** with `config.py`'s text,
 * because Python's `config.load` raises on them before its tolerance applies.
 *
 * **Narrowed, and said so:** Python's `config.load` also refuses the other
 * retired and unknown keys and validates every value; this reader checks only
 * the `[sources]` keys it reads or replaced. */
export function sourcesFile(root) {
  const path = join(root, fixed("files", "config"));
  if (!isFile(path)) return null;
  const data = parseToml(readFileSync(path, "utf8"), path);
  const sources = data?.sources ?? {};
  for (const retired of ["dirs_file", "urls_file"]) {
    if (Object.hasOwn(sources, retired)) {
      throw new FuxError(`${path}: ` + fixed("sources_messages", "retired_key").replaceAll("{key}", retired));
    }
  }
  const value = sources.sources_file;
  if (value === undefined) throw new FuxError(`${path}:\n  [sources] sources_file is missing\n  ${FIX_HINT}`);
  if (typeof value !== "string" || !value.trim()) {
    throw new FuxError(`${path}: ` + fixed("sources_messages", "sources_file_type"));
  }
  return value.trim();
}

function isFile(path) {
  try {
    return statSync(path).isFile();
  } catch {
    return false;
  }
}

/** The paths `.fux/sources.yaml` lists under `archived:` — refusing, as
 *  `sourcesfile.read` does, while a pre-W-294 list still exists or when the
 *  manifest is absent. */
export function archivedPaths(root, relPath) {
  for (const legacy of [fixed("files", "dirs_legacy"), fixed("files", "urls_legacy")]) {
    if (isFile(join(root, legacy))) throw new FuxError(legacyMessage(legacy));
  }
  const path = join(root, relPath);
  if (!isFile(path)) throw new FuxError(`${relPath} not found (looked in ${path})`);
  return parseSources(readFileSync(path, "utf8"), path).paths
    .filter((e) => e.attrs.archived === "true")
    .map((e) => e.value);
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
 * it: a corpus with no `fux.toml`, or with no readable `.fux/sources.yaml`, still
 * answers — it simply demotes nothing. ⚠ **A `fux.toml` that is present and
 * lacks `sources_file`, or carries a retired key, throws**, as Python's does. **The tune
 * file is NOT covered by this**
 * (`config/tune.mjs`), and the asymmetry is deliberate: an absent manifest is
 * the normal case for a corpus nobody has declared anything about, while a tune
 * file that exists and will not parse means somebody edited it and got it wrong. */
export function archivedDirSet(root) {
  const relPath = sourcesFile(root);
  if (relPath === null) return new Set();
  try {
    return new Set(archivedPaths(root, relPath));
  } catch {
    return new Set();
  }
}
