/** `.fux/` — the directory every derived plane nests under.
 *  Twin of `src/fux/store/fuxdir.py`, narrowed to `fux_dir` (W-242 Tier 2).
 *
 * Node writes one derived directory, `runtime/`, and only from `fux build`.
 * Creating and tagging it is `cachedir.mjs`'s
 * ([SR-CACHEDIR-TAG](../../../records/0121_cachedir-tag.md), W-261); this
 * file keeps the one path both it and the lock need.
 */
import { join } from "node:path";
import { fixed } from "../config/constants.mjs";

const FUXDIR = fixed("fuxdir", "dir");

export function fuxDir(root) { return join(root, FUXDIR); }
