/** Identifier families — `.fux/identifiers.toml`, matched on both sides (W-233).
 *
 * Twin of `src/fux/query/identifiers.py`. A family (a template such as
 * `RF-{n}`, or a guarded `[user]` regex) is matched against the TEXT, and each
 * match adds ONE term — its canonical form — beside analyzer v3's own terms.
 * With no families nothing changes, byte for byte.
 *
 * 🔴 A divergence from the Python twin is a silent no-match: the query writes a
 * canonical term the index never did. `tests/query/identifiers-fixture.json`
 * is read by both readers' tests from one file.
 */

import { readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { FuxError } from "../errors.mjs";
import { BOM, parseToml } from "../config/toml.mjs";
import { fixed } from "../config/constants.mjs";
import { cmpCodePoints } from "../compat/pyfloat.mjs";

//: `constants.toml [identifiers] flexible_separators` — the Python twin reads the same key.
const FLEX = fixed("identifiers", "flexible_separators");
export const IDENTIFIERS_FILE = fixed("files", "identifiers");

const escClass = (c) => (/[-\\\]^]/.test(c) ? `\\${c}` : c);
const FLEX_CLASS = `[${FLEX.map(escClass).join("")}]`;
const EDGE = `[A-Za-z0-9${FLEX.filter((c) => c !== " ").map(escClass).join("")}]`;
const LEAD = `(?<!${EDGE})(?<![A-Za-z0-9]\\.)`;
const TRAIL = `(?!${EDGE})(?!\\.[A-Za-z0-9])`;
const RUN_OF_FLEX = new RegExp(`${FLEX_CLASS}+`, "g");

const isAsciiAlpha = (c) => /^[A-Za-z]$/.test(c);
const isAsciiAlnum = (c) => /^[A-Za-z0-9]$/.test(c);
const kindOf = (c) => (/[0-9]/.test(c) ? "d" : "a");
const escRe = (c) => c.replace(/[.*+?^${}()|[\]\\/\-:]/g, "\\$&");

/** `RF-{n}` → a rule. Throws `FuxError` naming the problem. Grammar: compare doc S2. */
export function parseTemplate(src) {
  const where = `identifier template ${JSON.stringify(src)}`;
  if (typeof src !== "string" || !src) throw new FuxError(`${where}: must be a non-empty string`);
  if (!isAsciiAlpha(src[0])) {
    throw new FuxError(`${where}: must start with a literal letter (e.g. RF-{n}), so that prose like 'step 4' cannot match it`);
  }
  const elems = [];
  let i = 0;
  while (i < src.length) {
    const m = /^\{([A-Za-z]+)\}/.exec(src.slice(i));
    if (m) {
      if (m[1] !== "n" && m[1] !== "X") throw new FuxError(`${where}: unknown placeholder {${m[1]}} - only {n} and {X}`);
      elems.push([m[1]]);
      i += m[0].length;
      continue;
    }
    const ch = src[i];
    if (isAsciiAlnum(ch)) elems.push(["lit", ch]);
    else if (ch === "-" || ch === "_") elems.push(["sep", ch]);
    else if (ch === "." || ch === "/" || ch === ":") elems.push(["punct", ch]);
    else {
      throw new FuxError(`${where}: ${JSON.stringify(ch)} is not allowed - letters, digits, - _ . / : and {n} {X} only; use a [user] regex for anything else`);
    }
    i += 1;
  }
  if (!elems.some((e) => e[0] === "n" || e[0] === "X")) {
    throw new FuxError(`${where}: has no {n} or {X} - a fixed string is not a family`);
  }
  const side = (e) => (e[0] === "lit" ? kindOf(e[1]) : e[0] === "n" ? "d" : e[0] === "X" ? "a" : null);
  const parts = [];
  const plan = [];
  elems.forEach((e, idx) => {
    const prev = idx ? elems[idx - 1] : null;
    if ((e[0] === "n" || e[0] === "X") && prev && ["lit", "n", "X"].includes(prev[0]) && side(prev) === side(e)) {
      throw new FuxError(`${where}: {${e[0]}} directly after a same-kind element is ambiguous - put a separator between them`);
    }
    if (e[0] === "lit") { parts.push(escRe(e[1])); plan.push(["lit", e[1].toLowerCase()]); }
    else if (e[0] === "punct") { parts.push(escRe(e[1])); plan.push(["lit", e[1]]); }
    else if (e[0] === "n") { parts.push("([0-9]+)"); plan.push(["n"]); }
    else if (e[0] === "X") { parts.push("([A-Za-z]+)"); plan.push(["X"]); }
    else {
      const nxt = idx + 1 < elems.length ? elems[idx + 1] : null;
      if (!prev || !nxt || ["sep", "punct"].includes(prev[0]) || ["sep", "punct"].includes(nxt[0])) {
        throw new FuxError(`${where}: a separator must sit between two letters, digits or placeholders`);
      }
      parts.push(FLEX_CLASS + (side(prev) !== side(nxt) ? "?" : ""));
      plan.push(["sep", e[1]]);
    }
  });
  return { source: src, kind: "template", pattern: parts.join(""), plan };
}

// ---- the regex guard (F3) — the same walk as Python's `check_regex` ----------

const CLASS_ESC = { d: "0-9", w: "A-Za-z0-9_" };
const PLAIN_ESC = new Set([..."tnr", ..."\\.-/()[]{}*+?|^$#:, "]);

/** Validate a [user] regex; return its flavour-neutral source, or throw. */
export function checkRegex(src) {
  const where = `identifier regex ${JSON.stringify(src)}`;
  if (typeof src !== "string" || !src) throw new FuxError(`${where}: must be a non-empty string`);
  const out = [];
  let depth = 0;
  let inClass = false;
  let prevQuant = false;
  let i = 0;
  const n = src.length;
  const refuse = (why) => { throw new FuxError(`${where}: refused - ${why}`); };
  while (i < n) {
    const ch = src[i];
    if (ch === "\\") {
      if (i + 1 >= n) throw new FuxError(`${where}: ends in a lone backslash`);
      const e = src[i + 1];
      if (e in CLASS_ESC) { out.push(inClass ? CLASS_ESC[e] : `[${CLASS_ESC[e]}]`); i += 2; }
      else if (e === "b" && !inClass) { out.push("\\b"); i += 2; }
      else if (e === "x" || e === "u") {
        const width = e === "x" ? 2 : 4;
        const hex = src.slice(i + 2, i + 2 + width);
        if (hex.length !== width || !/^[0-9a-fA-F]+$/.test(hex)) refuse(`\\${e} needs exactly ${width} hex digits`);
        out.push(src.slice(i, i + 2 + width));
        i += 2 + width;
      } else if (PLAIN_ESC.has(e)) { out.push(src.slice(i, i + 2)); i += 2; }
      else {
        refuse(`the escape \\${e} is not portable between Python and JS (allowed: \\d \\w \\b \\t \\n \\r \\xhh \\uhhhh and escaped punctuation)`);
      }
      prevQuant = false;
      continue;
    }
    if (inClass) {
      if (ch === "]") inClass = false;
      else if (ch === "[" || ["&&", "--", "~~", "||"].some((op) => src.startsWith(op, i))) {
        refuse("a nested '[' or a set operation inside a class");
      }
      out.push(ch);
      i += 1;
      continue;
    }
    if (ch === "[") {
      inClass = true;
      out.push(ch);
      if (src.startsWith("[^", i)) { out.push("^"); i += 1; }
      i += 1;
      prevQuant = false;
      continue;
    }
    if (ch === "^" || ch === "$") refuse("an anchor (^ or $); multiline semantics differ between the readers, and the engine adds its own boundaries");
    if (ch === ".") refuse("an unescaped '.' matches different sets in Python and JS; write \\. or a class");
    if (ch === "(") {
      if (src.startsWith("(?", i)) {
        if (!src.startsWith("(?:", i)) refuse("'(?' other than '(?:' (lookaround, named groups, inline flags, atomic groups) is flavour-dependent");
        i += 3;
      } else i += 1;
      out.push("(?:");
      depth += 1;
      prevQuant = false;
      continue;
    }
    if (ch === ")") {
      depth -= 1;
      if (depth < 0) throw new FuxError(`${where}: unbalanced ')'`);
      out.push(ch);
      i += 1;
      if (i < n && "*+?{".includes(src[i])) refuse("a quantifier on a group can backtrack catastrophically; quantify single characters or classes only");
      prevQuant = false;
      continue;
    }
    if ("*+?".includes(ch) || ch === "{") {
      if (ch === "{") {
        const close = src.indexOf("}", i);
        const body = close > 0 ? src.slice(i + 1, close) : "";
        if (close < 0 || !/^[0-9]+(,[0-9]*)?$/.test(body)) refuse("'{' must be a quantifier {m}, {m,} or {m,n}; escape a literal brace");
        out.push(src.slice(i, close + 1));
        i = close + 1;
      } else {
        if (prevQuant && ch !== "?") refuse("a stacked or possessive quantifier");
        out.push(ch);
        i += 1;
      }
      if (i < n && src[i] === "+") refuse("a possessive quantifier (Python only)");
      prevQuant = true;
      continue;
    }
    out.push(ch);
    i += 1;
    prevQuant = false;
  }
  if (depth || inClass) throw new FuxError(`${where}: unbalanced group or class`);
  const body = out.join("");
  let compiled;
  try {
    compiled = new RegExp(`^(?:${body})$`, "i");
  } catch (err) {
    throw new FuxError(`${where}: invalid regex (${err.message})`);
  }
  if (compiled.test("")) refuse("it can match the empty string");
  return body;
}

export function parseRegex(src) {
  return { source: src, kind: "regex", pattern: checkRegex(src), plan: [] };
}

const groupCount = (pattern) => new RegExp(`${pattern}|`).exec("").length - 1;

/** The effective, ordered rules and their combined matcher. */
export class IdentifierRules {
  constructor(rules) {
    this.rules = rules;
    const groups = [];
    let g = 1;
    for (const r of rules) {
      const count = groupCount(r.pattern);
      groups.push([r, g, count]);
      g += 1 + count;
    }
    this.groups = groups;
    this.rx = rules.length
      ? new RegExp(`${LEAD}(?:${rules.map((r) => `(${r.pattern})`).join("|")})${TRAIL}`, "gi")
      : null;
  }

  get empty() {
    return this.rules.length === 0;
  }

  /** `[start, end, canonical]` for every match, in text order. */
  matches(text) {
    if (!this.rx) return [];
    const out = [];
    this.rx.lastIndex = 0;
    let m;
    while ((m = this.rx.exec(text)) !== null) {
      for (const [rule, g0, count] of this.groups) {
        if (m[g0] === undefined) continue;
        const captured = [];
        for (let k = 0; k < count; k += 1) captured.push(m[g0 + 1 + k]);
        out.push([m.index, m.index + m[0].length, canonical(rule, m[g0], captured)]);
        break;
      }
    }
    return out;
  }
}

/** The one term a match adds. Template: the plan instantiated. Regex: the
 *  match lowercased with every run of flexible separators read as `-`. */
export function canonical(rule, whole, captured) {
  if (rule.kind === "regex") return whole.toLowerCase().replace(RUN_OF_FLEX, "-");
  const out = [];
  let k = 0;
  for (const step of rule.plan) {
    if (step[0] === "lit" || step[0] === "sep") out.push(step[1]);
    else if (step[0] === "n") { out.push(captured[k].replace(/^0+/, "") || "0"); k += 1; }
    else { out.push(captured[k].toLowerCase()); k += 1; }
  }
  return out.join("");
}

/** `(detected − drop) ∪ keep`, sorted by code point, then the regexes in file order. */
export function build(detected, keep, drop, regex) {
  const dropped = new Set(drop);
  const templates = [...new Set([...detected, ...keep])].filter((t) => !dropped.has(t)).sort(cmpCodePoints);
  const rules = templates.map(parseTemplate);
  for (const t of drop) parseTemplate(t);
  for (const r of regex) rules.push(parseRegex(r));
  return new IdentifierRules(rules);
}

function strings(table, key, where) {
  const value = table[key] ?? [];
  if (!Array.isArray(value) || !value.every((v) => typeof v === "string")) {
    throw new FuxError(`${where} ${key}: must be a list of strings`);
  }
  return value;
}

export function parse(data, origin) {
  const unknown = Object.keys(data).filter((k) => k !== "user" && k !== "detected").sort();
  if (unknown.length) throw new FuxError(`${origin}: unknown table(s) ${JSON.stringify(unknown)} - only [user] and [detected]`);
  const user = data.user ?? {};
  const detected = data.detected ?? {};
  if (typeof user !== "object" || Array.isArray(user) || typeof detected !== "object" || Array.isArray(detected)) {
    throw new FuxError(`${origin}: [user] and [detected] must be tables`);
  }
  const bad = [
    ...Object.keys(user).filter((k) => !["keep", "drop", "regex"].includes(k)),
    ...Object.keys(detected).filter((k) => k !== "families").map((k) => `detected.${k}`),
  ].sort();
  if (bad.length) throw new FuxError(`${origin}: unknown key(s) ${JSON.stringify(bad)}`);
  return build(
    strings(detected, "families", `${origin}: [detected]`),
    strings(user, "keep", `${origin}: [user]`),
    strings(user, "drop", `${origin}: [user]`),
    strings(user, "regex", `${origin}: [user]`),
  );
}

/** Parse `.fux/identifiers.toml`. **Absent throws** (L12); empty sections are fine. */
export function loadIdentifiers(root) {
  const path = join(root, IDENTIFIERS_FILE);
  let raw;
  try {
    if (!statSync(path).isFile()) throw new Error("not a file");
    raw = readFileSync(path, "utf8");
  } catch {
    throw new FuxError(`${path} is missing - run \`fux setup\` to write it (both sections may stay empty)`);
  }
  if (raw.startsWith(BOM)) raw = raw.slice(BOM.length);
  return parse(parseToml(raw, path), path);
}

export const EMPTY = new IdentifierRules([]);

//: `identifiersFor`'s cache, keyed by path, mtime and size — Python's `for_root`.
const BY_ROOT = new Map();

/** `loadIdentifiers(root)`, cached on the file's stat. Throws exactly as it does. */
export function identifiersFor(root) {
  const path = join(root, IDENTIFIERS_FILE);
  let st;
  try {
    st = statSync(path);
  } catch {
    return loadIdentifiers(root);
  }
  const key = `${path}\u0000${st.mtimeMs}\u0000${st.size}`;
  let hit = BY_ROOT.get(key);
  if (hit === undefined) {
    hit = loadIdentifiers(root);
    BY_ROOT.set(key, hit);
  }
  return hit;
}
