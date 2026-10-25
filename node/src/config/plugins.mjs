/** `.fux/config/plugins.toml`'s `kind = "index"` rows — the Node half of the
 *  index-package pin. Twin of the index half of `src/fux/plugins.py` (W-299).
 *
 * [SR-PKG-INDEX](../../../records/0166_pkg-index.md) decisions 2–7. A pinned
 * index package is data, never code: this module **locates** it by module
 * resolution from the repository root, **hashes** its segment files and
 * **refuses** a missing, other, drifted or foreign one — in the words
 * `constants.toml [pkg_index_refusals]` holds for both runtimes, in the order
 * Python checks them. Nothing here imports or executes the package.
 *
 * Decoder and fetcher rows are Python's alone (Node decodes nothing); this
 * reader validates only what it reads, and the duplicate-name rule across both.
 *
 * 🔴 **Resolution starts at the repository root** —
 * `createRequire(<root>/package.json)` — never at fux's own install location,
 * so two consumers sharing one global fux resolve their own packages (the
 * item's third hazard).
 */
import { createHash } from "node:crypto";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { createRequire } from "node:module";
import { join } from "node:path";
import { FuxError } from "../errors.mjs";
import { fixed } from "./constants.mjs";
import { parseToml } from "./toml.mjs";

const FILE = fixed("plugins", "file");

function isFile(path) {
  try { return statSync(path).isFile(); } catch { return false; }
}

function isDir(path) {
  try { return statSync(path).isDirectory(); } catch { return false; }
}

/** `[pkg_index_refusals] <code>`, its `{placeholders}` filled — `str.format`'s subset. */
function refusal(code, values) {
  return fixed("pkg_index_refusals", code).replace(/\{(\w+)\}/g, (_, key) => String(values[key]));
}

/** `_parse_index_row` — one `kind = "index"` row, or the same refusal Python raises. */
function parseIndexRow(row, origin, rowKey) {
  const allowed = new Set(fixed("plugins.index", "keys"));
  const name = row.name;
  const label = typeof name === "string" && name ? name : `a \`[[${rowKey}]]\` index row`;
  if (Object.hasOwn(row, "suffixes")) {
    throw new FuxError(
      `${origin}: ${label} is an index package, which reads no format - delete its ` +
      "`suffixes` key (SR-PKG-INDEX d2)",
    );
  }
  const unknown = Object.keys(row).filter((k) => !allowed.has(k)).sort();
  if (unknown.length) {
    throw new FuxError(`${origin}: ${label} carries unknown key(s) ${unknown.join(", ")} (SR-PKG-INDEX d2)`);
  }
  const pattern = fixed("plugins.index", "name_pattern");
  if (typeof name !== "string" || !new RegExp(pattern).test(name)) {
    throw new FuxError(
      `${origin}: an index row's \`name\` must match ${pattern} (got ${JSON.stringify(name ?? null)}) ` +
      "- it names a directory under .fux/runtime/ (SR-PKG-INDEX d2)",
    );
  }
  const version = row.version;
  const digest = row.digest ?? "";
  if (typeof version !== "string" || !version) {
    throw new FuxError(`${origin}: ${name} has no \`version\` - every package is pinned`);
  }
  const prefix = fixed("plugins", "digest_prefix");
  if (typeof digest !== "string" || (digest && !digest.startsWith(prefix))) {
    throw new FuxError(`${origin}: ${name}'s \`digest\` must read \`${prefix}<hex>\``);
  }
  const names = {};
  for (const key of ["npm", "pypi"]) {
    const value = row[key];
    if (value !== undefined && (typeof value !== "string" || !value)) {
      throw new FuxError(`${origin}: ${name}'s \`${key}\` must be a package name`);
    }
    names[key] = value ?? null;
  }
  if (!names.npm && !names.pypi) {
    throw new FuxError(
      `${origin}: ${name} names neither an \`npm\` nor a \`pypi\` package, so nothing can ` +
      "locate it (SR-PKG-INDEX d2)",
    );
  }
  return { name, version, digest, npm: names.npm, pypi: names.pypi };
}

/** `plugins.parse_indexes` — the index rows of a declaration's text, by name, sorted. */
export function parseIndexes(text, origin = FILE) {
  const data = parseToml(text, origin);
  const rowKey = fixed("plugins", "table");
  const rows = data[rowKey] ?? [];
  if (!Array.isArray(rows)) {
    throw new FuxError(`${origin}: \`${rowKey}\` must be an array of tables, written \`[[${rowKey}]]\``);
  }
  const kind = fixed("plugins.index", "kind");
  const seen = new Set();
  const out = new Map();
  for (const row of rows) {
    if (row === null || typeof row !== "object" || Array.isArray(row)) {
      throw new FuxError(`${origin}: every \`[[${rowKey}]]\` entry must be a table`);
    }
    if (!Object.hasOwn(row, "kind")) {
      if (typeof row.name === "string") {
        if (seen.has(row.name)) throw new FuxError(`${origin}: ${row.name} is declared twice`);
        seen.add(row.name);
      }
      continue;
    }
    if (row.kind !== kind) {
      throw new FuxError(
        `${origin}: a \`[[${rowKey}]]\` row's \`kind\` may only be '${kind}' - a ` +
        "decoder, fetcher or extension package's kind is its name (SR-PKG-INDEX d2)",
      );
    }
    const pin = parseIndexRow(row, origin, rowKey);
    if (seen.has(pin.name)) throw new FuxError(`${origin}: ${pin.name} is declared twice`);
    seen.add(pin.name);
    out.set(pin.name, pin);
  }
  return new Map([...out.entries()].sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0)));
}

/** `plugins.indexes` — every index row of `<root>/.fux/config/plugins.toml`; empty without one. */
export function indexes(root) {
  const path = join(root, ...FILE.split("/"));
  if (!isFile(path)) return new Map();
  return parseIndexes(readFileSync(path, "utf8"), FILE);
}

/** RECORD's hash spelling: urlsafe base64 of the sha256, unpadded, CRLF read as LF. */
function recordHash(buffer) {
  const lf = Buffer.from(buffer.toString("latin1").replaceAll("\r\n", "\n"), "latin1");
  return createHash("sha256").update(lf).digest("base64url");
}

/** The files one `[plugins.index] segment` glob names under `directory`.
 *  The globs are a directory part with no wildcard and a last part with `*`. */
function globSegment(directory, pattern) {
  const parts = pattern.split("/");
  const last = parts.pop();
  const base = join(directory, ...parts);
  if (!last.includes("*")) return isFile(join(base, last)) ? [[...parts, last].join("/")] : [];
  if (!isDir(base)) return [];
  const re = new RegExp(`^${last.split("*").map((s) => s.replace(/[.+?^${}()|[\]\\]/g, "\\$&")).join("[^/]*")}$`);
  return readdirSync(base).filter((n) => re.test(n) && isFile(join(base, n))).map((n) => [...parts, n].join("/"));
}

function cmpCodePoints(a, b) { return a < b ? -1 : a > b ? 1 : 0; }

/** `plugins.segment_digest` — `sha256:<hex>` over a segment's files, or `null`. */
export function segmentDigest(directory) {
  const rels = [...new Set(fixed("plugins.index", "segment").flatMap((g) => globSegment(directory, g)))].sort(cmpCodePoints);
  if (rels.length === 0) return null;
  const lines = rels.map((rel) => `${rel},sha256=${recordHash(readFileSync(join(directory, ...rel.split("/"))))}`);
  return fixed("plugins", "digest_prefix") + createHash("sha256").update(Buffer.from(lines.join("\n"), "utf8")).digest("hex");
}

function shardGlob() {
  const suffix = fixed("index", "shard_suffix");
  return fixed("plugins.index", "segment").find((g) => g.endsWith(suffix));
}

/** `plugins.segment_docs` — the document records the shards hold, off the shards. */
export function segmentDocs(directory) {
  const header = fixed("index", "shard_header_lines");
  let total = 0;
  for (const rel of globSegment(directory, shardGlob()).sort(cmpCodePoints)) {
    const lines = readFileSync(join(directory, ...rel.split("/"))).toString("latin1").split("\n").filter((l) => l.trim());
    total += Math.max(0, lines.length - header);
  }
  return total;
}

/** The installed npm package's directory, resolved from the repository root. */
export function packageDir(root, npm) {
  const req = createRequire(join(root, fixed("plugins.index", "npm_manifest")));
  for (const base of req.resolve.paths(npm) ?? []) {
    const candidate = join(base, ...npm.split("/"));
    if (isFile(join(candidate, fixed("plugins.index", "npm_manifest")))) return candidate;
  }
  return null;
}

export function installedVersion(root, npm) {
  const dir = packageDir(root, npm);
  if (dir === null) return null;
  try {
    const version = JSON.parse(readFileSync(join(dir, fixed("plugins.index", "npm_manifest")), "utf8")).version;
    return typeof version === "string" && version ? version : null;
  } catch { return null; }
}

/** `plugins.segment_root` — the segment's directory (the package root), or `null`. */
export function segmentRoot(root, pin) {
  if (!pin.npm) return null;
  const dir = packageDir(root, pin.npm);
  return dir !== null && isFile(join(dir, fixed("plugins.index", "manifest"))) ? dir : null;
}

/** `plugins.index_install_line` for Node. fux never runs it. */
export function indexInstallLine(pin) {
  return `${fixed("plugins.index", "npm_install")} ${pin.npm}@${pin.version}`;
}

function foreign(directory) {
  const want = Object.entries(fixed("plugins.index", "header_keys")).map(([key, source]) => [key, fixed("index", source)]);
  for (const rel of globSegment(directory, shardGlob()).sort(cmpCodePoints)) {
    const raw = readFileSync(join(directory, ...rel.split("/")));
    const nl = raw.indexOf(0x0a);
    let header;
    try { header = JSON.parse(raw.subarray(0, nl === -1 ? raw.length : nl).toString("utf8")); } catch { header = {}; }
    if (header === null || typeof header !== "object" || Array.isArray(header)) header = {};
    for (const [key, value] of want) {
      const got = Object.hasOwn(header, key) ? header[key] : null;
      if (JSON.stringify(got) !== JSON.stringify(value)) {
        return { shard: rel, key, got_value: JSON.stringify(got), want_value: JSON.stringify(value) };
      }
    }
  }
  return null;
}

function manifestDigest(directory) {
  try {
    const data = JSON.parse(readFileSync(join(directory, fixed("plugins.index", "manifest")), "utf8"));
    const value = data !== null && typeof data === "object" ? data.digest : null;
    return typeof value === "string" && value ? value : "no digest";
  } catch { return "no digest"; }
}

/** `plugins._check_index` — `[code, refusal]`, both `null` when the pin can be read. */
export function checkIndex(root, pin) {
  const { name, version } = pin;
  const expected = `pinned ${name} ${version}` + (pin.digest ? ` ${pin.digest}` : "");
  if (!pin.npm) return ["no_registry", refusal("no_registry", { name, key: "npm", expected })];
  const install = indexInstallLine(pin);
  const have = installedVersion(root, pin.npm);
  if (have === null) return ["missing", refusal("missing", { name, expected, install })];
  if (have !== version) return ["other_version", refusal("other_version", { name, have, expected, install })];
  if (!pin.digest) return ["no_digest", refusal("no_digest", { name, version })];
  const manifest = fixed("plugins.index", "manifest");
  const directory = segmentRoot(root, pin);
  if (directory === null) return ["no_segment", refusal("no_segment", { name, have, manifest, install })];
  const got = segmentDigest(directory) ?? "nothing";
  if (got !== pin.digest) return ["drifted", refusal("drifted", { name, have, got, expected, install })];
  const claimed = manifestDigest(directory);
  if (claimed !== got) return ["manifest", refusal("manifest", { name, have, manifest, claimed, got, install })];
  const bad = foreign(directory);
  if (bad !== null) return ["foreign", refusal("foreign", { name, have, ...bad })];
  return [null, null];
}

/** `plugins.verify_index` then the segment's directory — the only way one is read. */
export function locateIndex(root, pin) {
  const [, problem] = checkIndex(root, pin);
  if (problem !== null) throw new FuxError(`${FILE}: ${problem} (SR-PLUGINS P4)`);
  return segmentRoot(root, pin);
}

/** The verb-wide gate: refuse unless every index pin can be read — `plugins.require`'s
 *  index half, run by `fux.mjs` before any verb, beside the PII gate. */
export function requireIndexPackages(root) {
  const problems = [];
  for (const pin of indexes(root).values()) {
    const [, problem] = checkIndex(root, pin);
    if (problem !== null) problems.push(problem);
  }
  if (problems.length) throw new FuxError(`${FILE}: ${problems.join("; ")} (SR-PLUGINS P4)`);
  return indexes(root);
}
