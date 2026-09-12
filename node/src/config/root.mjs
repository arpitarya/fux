/** Finding the repo root. Twin of `find_root` in `src/fux/config.py`.
 *  Walk up for `fux.toml` or `.git` — the same two tells, in the same order. */
import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";

export const CONFIG_NAME = "fux.toml";

export function findRoot(start = process.cwd()) {
  let here = resolve(start);
  for (;;) {
    if (existsSync(join(here, CONFIG_NAME)) || existsSync(join(here, ".git"))) return here;
    const up = dirname(here);
    if (up === here) return null;
    here = up;
  }
}
