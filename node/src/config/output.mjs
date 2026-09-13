/** `.fux/output.toml`, read — HOW a result is shown, never which documents
 *  come back. Twin of `src/fux/output_config.py`.
 *
 * 🔴 **W-107 R5's last unbuilt read-path row**, and it is not cosmetic. Python
 * folds this file into `args` once, before dispatch, so `fux find rollback`
 * with no flags returns `[cli] top` results and Node returned five. Worse, the
 * file is the **SOLE SOURCE** of every key once it exists: Python **refuses**
 * when the file is present and does not set the key a verb asked for. A Node
 * reader that quietly used a built-in there would answer where Python refuses
 * — a divergence in which repositories WORK, which is the same class of defect
 * as the tune gap and harder to notice.
 *
 * ## The precedence chain, in one place
 *
 *     a CLI flag  ->  [cli.json.<verb>]  ->  [cli.json]  ->  [cli.<verb>]  ->  [cli]
 *     a tool arg  ->  [mcp]                                          (MCP inherits NOTHING)
 *
 * `json` is resolved FIRST and separately, because it selects which chain
 * every other key walks.
 *
 * ⚠ **A MISSING file is not an error** (SR-OUTPUT decision 20): it returns the
 * absent sentinel, which resolves every key to the built-in. The file is
 * write-if-missing, so it reaches new repos only, and refusing without it would
 * break every repo that predates it. *"Once it is in effect"* is the rule that
 * survives — a file that does not exist is not in effect.
 */
import { readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { FuxError } from "../errors.mjs";
import { parseToml, wasFloat } from "./toml.mjs";

export const OUTPUT_NAME = ".fux/output.toml";

const MAX_REPORTED = 10;
const ROOTS = ["cli", "mcp"];

//: The closed key set per verb. ⚠ **`graph` has no `top` key** — it has no
//: `--top` flag and reads `seed_depth`/`expand_limit` from `.fux/tune.toml`
//: instead; truncating a graph walk is a ranking change, which this file may
//: not make. `json` is absent from every tuple: it is not a `[cli]` key, it is
//: the question of WHICH chain the others walk.
export const CLI_VERBS = {
  ask: ["band", "top", "explain", "sections"],
  find: ["band", "top"],
  answer: ["band", "no_refer", "journal"],
  explain: [],
  graph: [],
  path: ["hops"],
  doctor: [],
  hooks: [],
  daemon: [],
  update: [],
};

//: `[mcp]`'s closed key set. `top` only. No `json` (an MCP result is always
//: JSON) and no `band` (the confidence block is unconditional there).
export const MCP_KEYS = ["top"];

/** Every key reachable from more than one verb — what a SHARED table may hold.
 *  A key unique to one verb is refused at the shared level by name. */
const SHARED_CLI_KEYS = (() => {
  const counts = new Map();
  for (const keys of Object.values(CLI_VERBS)) {
    for (const k of keys) counts.set(k, (counts.get(k) ?? 0) + 1);
  }
  return [...counts].filter(([, n]) => n > 1).map(([k]) => k).sort();
})();

//: The engine's own defaults, per key, as they appear on `args`.
export const BUILT_IN = {
  json: false, band: false, top: 5, explain: false,
  sections: true, no_refer: false, hops: 2, journal: false,
};

//: Type per key, as spelled IN THE FILE (`enabled`, not `json`).
const TYPES = {
  band: "bool", explain: "bool", sections: "bool", no_refer: "bool",
  journal: "bool", enabled: "bool", top: "int", hops: "int",
};

//: Refused by NAME with the reason, rather than reported as unknown.
const REFUSED = {
  no_tune: "`--no-tune` is the *'is it me or the config?'* switch. A config file " +
    "that can turn off config-reading defeats the one flag whose entire job is " +
    "to answer that question",
  tune: "`--no-tune` is the *'is it me or the config?'* switch. A config file " +
    "that can turn off config-reading defeats the one flag whose entire job is " +
    "to answer that question",
  no_output_config: "the same loop one level up — this file may not decide whether this " +
    "file is read. Pass `--no-output-config` on the command line",
  fast: "`--fast` and `--scan` choose a candidate path, not an output shape, " +
    "and the two are asserted byte-identical — so this is not an output key",
  scan: "`--fast` and `--scan` choose a candidate path, not an output shape, " +
    "and the two are asserted byte-identical — so this is not an output key",
  no_progress: "progress is stderr-only and already TTY-gated. Use `--no-progress`",
  json: "`json` is spelled `enabled` and lives only under `[cli.json]`",
};

const MCP_REFUSED = {
  band: "the confidence block is UNCONDITIONAL over MCP (SR-CONFIDENCE " +
    "decision 11) — a tool call cannot pass a flag",
  json: "an MCP result is always JSON — there is no rendering to switch",
};

class Collector {
  constructor(label) { this.label = label; this.errors = []; }
  add(m) { this.errors.push(m); }
  raiseIfAny() {
    if (!this.errors.length) return;
    const shown = this.errors.slice(0, MAX_REPORTED);
    const more = this.errors.length - shown.length;
    throw new FuxError(`${this.label}:\n  ` + shown.join("\n  ") +
      (more > 0 ? `\n  ... and ${more} more` : ""));
  }
}

/** Resolved output defaults. Frozen, like `Tune`, so a caller can never hand
 *  two code paths a block that drifted between them. */
export class OutputDefaults {
  constructor({
    cliShared = {}, cliVerb = {}, jsonShared = {}, jsonVerb = {},
    mcp = {}, bypass = false, absent = false,
  } = {}) {
    Object.assign(this, { cliShared, cliVerb, jsonShared, jsonVerb, mcp, bypass, absent });
    Object.freeze(this);
  }

  /** The JSON-rendering switch — resolved FIRST, before any other key, because
   *  it selects which chain the others walk. */
  resolveJson(verb, cliValue = null) {
    if (!(verb in CLI_VERBS)) {
      throw new FuxError(`no output defaults are declared for \`${verb}\` — known: ${Object.keys(CLI_VERBS).sort().join(", ")}`);
    }
    if (cliValue !== null && cliValue !== undefined) return Boolean(cliValue);
    if (this.bypass) return Boolean(BUILT_IN.json);
    const perVerb = this.jsonVerb[verb] ?? {};
    if ("enabled" in perVerb) return Boolean(perVerb.enabled);
    if ("enabled" in this.jsonShared) return Boolean(this.jsonShared.enabled);
    throw new FuxError(
      `${OUTPUT_NAME} does not set \`enabled\` for the JSON rendering — ` +
      `add \`enabled = ${BUILT_IN.json}\` under \`[cli.json]\` ` +
      `(or \`[cli.json.${verb}]\` for \`${verb}\` only). Run \`fux output\` to ` +
      "see every key, or pass --no-output-config to bypass this file.",
    );
  }

  /** One precedence chain: **flag → json-verb → json-shared → cli-verb →
   *  cli-shared → bypass → error.** Raises on a verb/key pair `CLI_VERBS` does
   *  not grant, so a typo in a CALLER is caught too. */
  resolve(verb, key, cliValue = null, { asJson = false } = {}) {
    const allowed = CLI_VERBS[verb];
    if (allowed === undefined) {
      throw new FuxError(`no output defaults are declared for \`${verb}\` — known: ${Object.keys(CLI_VERBS).sort().join(", ")}`);
    }
    if (!allowed.includes(key)) {
      throw new FuxError(`\`${key}\` is not an output key for \`${verb}\` — it has: ${[...allowed].sort().join(", ")}`);
    }
    if (cliValue !== null && cliValue !== undefined) return cliValue;
    if (this.bypass) return BUILT_IN[key];
    if (asJson) {
      const perVerb = this.jsonVerb[verb] ?? {};
      if (key in perVerb) return perVerb[key];
      if (key in this.jsonShared) return this.jsonShared[key];
    }
    const perVerb = this.cliVerb[verb] ?? {};
    if (key in perVerb) return perVerb[key];
    if (key in this.cliShared) return this.cliShared[key];
    const where = asJson
      ? `[cli.json.${verb}], [cli.json], [cli.${verb}] or [cli]`
      : `[cli.${verb}] or [cli]`;
    throw new FuxError(
      `${OUTPUT_NAME} does not set \`${key}\` for \`${verb}\` — add it under ` +
      `${where} (e.g. \`${key} = ${JSON.stringify(BUILT_IN[key])}\`). Run \`fux output\` to ` +
      "see every key, or pass --no-output-config to bypass this file.",
    );
  }

  /** `[mcp]`'s own chain: **tool arg → `[mcp]` → bypass → error.**
   *  `[mcp]` inherits nothing from `[cli]` — the whole reason for two roots. */
  resolveMcp(key, toolValue = null) {
    if (!MCP_KEYS.includes(key)) {
      throw new FuxError(`\`${key}\` is not an output key for \`mcp\` — it has: ${[...MCP_KEYS].sort().join(", ")}`);
    }
    if (toolValue !== null && toolValue !== undefined) return toolValue;
    if (this.bypass) return BUILT_IN[key];
    if (key in this.mcp) return this.mcp[key];
    throw new FuxError(
      `${OUTPUT_NAME} does not set \`${key}\` under [mcp] — add ` +
      `\`${key} = ${JSON.stringify(BUILT_IN[key])}\`. Run \`fux output\` to see every key, ` +
      "or pass --no-output-config to bypass this file.",
    );
  }
}

//: `--no-output-config`, or no repo root at all.
export const DEFAULT_OUTPUT = new OutputDefaults({ bypass: true });
//: A repo root exists and `.fux/output.toml` does not. Resolves exactly as the
//: bypass sentinel does; `absent` is what keeps "the consumer asked to bypass"
//: and "there is nothing to bypass" distinguishable.
export const ABSENT_OUTPUT = new OutputDefaults({ bypass: true, absent: true });

function repr(v) {
  if (typeof v === "string") return `'${v}'`;
  if (v === true) return "True";
  if (v === false) return "False";
  return String(v);
}

/** Validate one key/value against `TYPES`. Returns `undefined` when rejected. */
function checked(c, table, key, value, raw) {
  if (TYPES[key] === "bool") {
    if (typeof value !== "boolean") {
      c.add(`[${table}] ${key} must be true or false (got ${repr(value)})`);
      return undefined;
    }
    return value;
  }
  // ⚠ `bool` is checked FIRST everywhere: `isinstance(True, int)` is true in
  // Python, so an unguarded check accepts `top = true` and silently means 1.
  if (typeof value !== "number" || !Number.isInteger(value) || wasFloat(raw, key)) {
    c.add(`[${table}] ${key} must be a whole number (got ${repr(value)})`);
    return undefined;
  }
  if (value < 1) {
    c.add(
      `[${table}] ${key} must be at least 1 — at zero the verb returns nothing, ` +
      `which is a broken setting rather than an aggressive one (got ${value})`,
    );
    return undefined;
  }
  return value;
}

/** The single verb `key` belongs to, if exactly one does. */
function verbOwning(key) {
  const owners = Object.entries(CLI_VERBS).filter(([, keys]) => keys.includes(key)).map(([v]) => v);
  return owners.length === 1 ? owners[0] : null;
}

const isTable = (v) => v !== null && typeof v === "object" && !Array.isArray(v);

function parseCliScalars(c, label, scope, out, verb) {
  const inJson = label.includes("json");
  const allowed = new Set(verb !== null ? CLI_VERBS[verb] : SHARED_CLI_KEYS);
  if (inJson) allowed.add("enabled");
  for (const [key, value] of Object.entries(scope)) {
    if (isTable(value)) continue;   // a subtable — the caller handles it
    if (key in REFUSED) { c.add(`[${label}] \`${key}\` is refused: ${REFUSED[key]}`); continue; }
    if (key === "enabled" && !inJson) {
      c.add(`[${label}] \`enabled\` only applies inside \`[cli.json]\` — it is not a \`[cli]\` key`);
      continue;
    }
    if (!allowed.has(key)) {
      const owner = verbOwning(key);
      if (owner && verb !== null && verb !== owner) {
        c.add(`[${label}] \`${key}\` is a key of ${owner}, not of \`${verb}\``);
      } else if (owner && verb === null) {
        c.add(`[${label}] \`${key}\` belongs to one verb only (${owner}) — write it under [cli.${owner}] or [cli.json.${owner}]`);
      } else {
        c.add(`[${label}] unknown key \`${key}\` — known: ${[...allowed].sort().join(", ")}`);
      }
      continue;
    }
    const value2 = checked(c, label, key, value, scope);
    if (value2 !== undefined) out[key] = value2;
  }
}

function parseCliRoot(c, label, table, sharedOut, verbOut) {
  parseCliScalars(c, label, table, sharedOut, null);
  for (const [key, value] of Object.entries(table)) {
    if (key === "json") continue;      // `[cli.json]` — parsed by the caller
    if (!isTable(value)) continue;     // scalar — already handled above
    if (!(key in CLI_VERBS)) {
      c.add(`[${label}] \`${key}\` is not a known verb — known: ${Object.keys(CLI_VERBS).sort().join(", ")}`);
      continue;
    }
    const inner = {};
    parseCliScalars(c, `${label}.${key}`, value, inner, key);
    if (Object.keys(inner).length) verbOut[key] = inner;
  }
}

/** A merged-but-unresolved file is a parse error with a useless message. */
function rejectConflictMarkers(label, text) {
  for (const marker of ["<<<<<<<", "=======", ">>>>>>>"]) {
    if (text.split("\n").some((line) => line.startsWith(marker))) {
      throw new FuxError(
        `${label}: unresolved merge conflict markers — resolve the conflict before fux reads it`,
      );
    }
  }
}

/** Read `.fux/output.toml`. `enabled=false` is `--no-output-config`. */
export function loadOutput(root, { enabled = true } = {}) {
  if (!enabled) return DEFAULT_OUTPUT;

  const path = join(root, ".fux", "output.toml");
  let text;
  try {
    if (!statSync(path).isFile()) return ABSENT_OUTPUT;
    text = readFileSync(path, "utf8");
  } catch {
    return ABSENT_OUTPUT;
  }

  const label = `${root}/${OUTPUT_NAME}`;
  rejectConflictMarkers(label, text);
  const data = parseToml(text, label);
  const c = new Collector(label);

  // A file in the OLD flat layout parses cleanly under this grammar and would
  // mean something else — named, not shrugged at.
  if ("defaults" in data && !isTable(data.cli)) {
    c.add("[defaults] is the old layout — output keys now live under [cli] (shared) or [cli.<verb>] (per verb). Run `fux output` for the new specimen.");
  }
  for (const legacy of Object.keys(CLI_VERBS)) {
    if (legacy in data && !isTable(data.cli)) {
      c.add(`[${legacy}] at the top level is the old layout — move it to [cli.${legacy}]. Run \`fux output\` for the new specimen.`);
    }
  }

  for (const [key, value] of Object.entries(data)) {
    if (ROOTS.includes(key)) continue;
    if (key === "defaults" || key in CLI_VERBS) continue;   // reported above
    if (!isTable(value)) {
      if (SHARED_CLI_KEYS.includes(key) || key === "enabled") {
        c.add(`\`${key}\` is a key, not a table — did you mean \`[cli]\\n${key} = ...\`?`);
      } else {
        c.add(`\`${key}\` is not a known key at all — known tables: ${[...ROOTS].sort().join(", ")}`);
      }
      continue;
    }
    c.add(`unknown table \`[${key}]\` — known: ${[...ROOTS].sort().join(", ")}`);
  }

  const cliShared = {}, cliVerb = {}, jsonShared = {}, jsonVerb = {}, mcpOut = {};

  const cliTable = data.cli;
  if (cliTable !== undefined) {
    if (!isTable(cliTable)) {
      c.add("`cli` must be a table — write `[cli]`, not `cli = ...`");
    } else {
      parseCliRoot(c, "cli", cliTable, cliShared, cliVerb);
      const jsonTable = cliTable.json;
      if (jsonTable !== undefined) {
        if (!isTable(jsonTable)) c.add(`[cli] \`json\` is refused: ${REFUSED.json}`);
        else parseCliRoot(c, "cli.json", jsonTable, jsonShared, jsonVerb);
      }
    }
  }

  const mcpTable = data.mcp;
  if (mcpTable !== undefined) {
    if (!isTable(mcpTable)) {
      c.add("`mcp` must be a table — write `[mcp]`, not `mcp = ...`");
    } else {
      for (const [key, value] of Object.entries(mcpTable)) {
        if (key in MCP_REFUSED) {
          c.add(`[mcp] \`${key}\` is refused: ${MCP_REFUSED[key]} — UNCONDITIONAL, by name`);
          continue;
        }
        if (!MCP_KEYS.includes(key)) {
          c.add(`[mcp] unknown key \`${key}\` — known: ${[...MCP_KEYS].sort().join(", ")}`);
          continue;
        }
        const value2 = checked(c, "mcp", key, value, mcpTable);
        if (value2 !== undefined) mcpOut[key] = value2;
      }
    }
  }

  c.raiseIfAny();
  return new OutputDefaults({ cliShared, cliVerb, jsonShared, jsonVerb, mcp: mcpOut, bypass: false });
}

/** Fold the resolved defaults into `args`, ONCE, before dispatch.
 *
 * **Done here rather than at each consumer, deliberately** — the same place
 * `cli.py::_apply_output_defaults` does it. Downstream code then reads a plain
 * boolean or number off `args` exactly as it did before this file existed, so
 * the blast radius of a rendering config is this function and nothing else.
 *
 * `undefined` on the way in means *the flag was not passed*. A verb this file
 * declares no keys for still gets `json` resolved, which is why an empty key
 * list in `CLI_VERBS` is a declaration rather than an absence. */
export function applyOutputDefaults(verb, args, cfg) {
  if (!(verb in CLI_VERBS)) return args;
  const asJson = cfg.resolveJson(verb, args.json === true ? true : null);
  args.json = asJson;
  for (const key of CLI_VERBS[verb]) {
    const passed = args[OUT_KEY_TO_ARG[key] ?? key];
    args[OUT_KEY_TO_ARG[key] ?? key] = cfg.resolve(verb, key, passed ?? null, { asJson });
  }
  return args;
}

//: File spelling -> the name this reader's `parseArgs` puts on `args`. Only
//: the two that differ are listed; everything else is spelled the same.
const OUT_KEY_TO_ARG = { no_refer: "noRefer" };
