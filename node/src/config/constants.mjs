/** `src/fux/constants.toml` — the engine's fixed values. Twin of `src/fux/constants.py`.
 *
 * SR-LAW-12 decision 2 and SR-CONSTANTS: one file, read by both planes, so a
 * schema id or an artefact name has one home instead of two literals kept equal
 * by hand (decision 4).
 *
 * 🔴 **In a checkout this reads the file; in the bundle the file is INLINED.**
 * The `@fux-inline` marker below is the bundler's cue
 * (`src/fux/store/nodebundle.py`): it replaces the `readFileSync(...)` call with
 * the file's text as a string literal, so the one artefact a consumer runs
 * carries its constants and reads nothing from a path that does not exist in
 * their tree (L10).
 *
 * Missing is an error, always, and the sentence is the Python twin's.
 */
import { readFileSync } from "node:fs";
import { FuxError } from "../errors.mjs";
import { parseToml } from "./toml.mjs";

export const LABEL = "src/fux/constants.toml";

const TEXT = /* @fux-inline src/fux/constants.toml */ readFileSync(
  new URL("../../../src/fux/constants.toml", import.meta.url),
  "utf8",
);

const DATA = parseToml(TEXT, LABEL);

/** The table `name` (dotted for a nested one), whole. */
export function table(name) {
  let node = DATA;
  for (const part of name.split(".")) {
    if (node === null || typeof node !== "object" || !Object.hasOwn(node, part)) {
      throw new FuxError(`${LABEL}: [${name}] is missing`);
    }
    node = node[part];
  }
  if (node === null || typeof node !== "object" || Array.isArray(node)) {
    throw new FuxError(`${LABEL}: [${name}] is not a table`);
  }
  return node;
}

/** `[name] key` — a missing table or key throws, naming both. */
export function fixed(name, key) {
  const t = table(name);
  if (!Object.hasOwn(t, key)) throw new FuxError(`${LABEL}: [${name}] ${key} is missing`);
  return t[key];
}
