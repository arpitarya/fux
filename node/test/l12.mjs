/** The config a hand-built Node test repo needs — L12 (W-225).
 *
 * Twin of `tests/l12_fixtures.py`: the engine holds no value in code, so a test
 * that writes `.fux/tune.toml` writes the packaged template with the few keys it
 * is about changed — never a partial file whose missing keys would be the
 * error the test reports instead of the one it is about.
 */
import { readFileSync } from "node:fs";

export const TUNE_TEMPLATE = readFileSync(
  new URL("../../src/fux/templates/tune.toml.txt", import.meta.url), "utf8",
);

function toml(value) {
  if (typeof value === "string") return JSON.stringify(value);
  return String(value);
}

/** The template with some keys changed: `tuneText({ ranking: { rerank_weight: 0.3 } })`.
 *  A table the template lacks, or `[priority]` entries, are appended. */
export function tuneText(overrides = {}) {
  const pending = Object.fromEntries(
    Object.entries(overrides).map(([t, keys]) => [t, { ...keys }]),
  );
  let table = null;
  const out = [];
  for (let line of TUNE_TEMPLATE.split("\n")) {
    const s = line.trim();
    if (s.startsWith("[") && s.includes("]") && !s.startsWith("#")) {
      table = s.slice(1, s.indexOf("]"));
    } else if (table in pending && s.includes("=") && !s.startsWith("#")) {
      const key = s.split("=")[0].trim();
      if (key in pending[table]) {
        line = `${key} = ${toml(pending[table][key])}`;
        delete pending[table][key];
      }
    }
    out.push(line);
  }
  for (const [t, keys] of Object.entries(pending)) {
    const rest = Object.entries(keys);
    if (!rest.length) continue;
    if (!TUNE_TEMPLATE.includes(`[${t}]`)) out.push(`[${t}]`);
    for (const [k, v] of rest) out.push(`${JSON.stringify(k)} = ${toml(v)}`);
  }
  return out.join("\n") + "\n";
}
