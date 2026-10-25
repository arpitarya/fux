/** `pkg:` locations — a pinned package's file, read where it is installed.
 *  Twin of `src/fux/acquire/pkgsrc.py` (W-301).
 *
 * [SR-PKG-INDEX](../../../records/0166_pkg-index.md) decision 11. A hit from a
 * pinned index segment is addressed in the DOCS package the segment's manifest
 * names in `content`: `pkg:<docs package>@<content.version>#<the record's loc>`
 * — the npm name when `content` has one, else the PyPI name, so both runtimes
 * spell the same string. Python reads `content.pypi` through `importlib`; this
 * reads `content.npm` through `createRequire(<repo>/package.json)` — **from the
 * repository root**, never from fux's own install. An installed docs version
 * other than `content.version` is refused, the fragment is contained inside the
 * package root after `..` collapses (`source.mjs::contain`), and the file is
 * read in place and hashed with `contentSha` — never copied (L3).
 *
 * The words are `constants.toml [pkg_location_refusals]`, shared with Python.
 */
import { readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { FuxError } from "../errors.mjs";
import { fixed } from "../config/constants.mjs";
import { indexes, installedVersion, locateIndex, packageDir } from "../config/plugins.mjs";
import { contentSha } from "../store/format.mjs";
import { contain } from "./source.mjs";

function refusal(code, values) {
  return fixed("pkg_location_refusals", code).replace(/\{(\w+)\}/g, (_, key) => String(values[key]));
}

const SCHEME = () => fixed("pkg_location", "scheme");

function readContent(pin, directory) {
  const manifest = fixed("plugins.index", "manifest");
  const bad = () => new FuxError(refusal("content", { index: pin.name, index_version: pin.version, manifest }));
  let data;
  try { data = JSON.parse(readFileSync(join(directory, manifest), "utf8")); } catch { throw bad(); }
  const raw = data !== null && typeof data === "object" && !Array.isArray(data) ? data.content : null;
  if (raw === null || typeof raw !== "object" || Array.isArray(raw)) throw bad();
  const { version, npm = null, pypi = null } = raw;
  const okName = (v) => v === null || (typeof v === "string" && v.length > 0);
  if (!(typeof version === "string" && version) || !okName(npm) || !okName(pypi) || !(npm || pypi)) throw bad();
  return { version, npm, pypi, name: npm || pypi };
}

/** `pkgsrc.segment` — the pin, verified, with its manifest's `content`. */
export function segment(root, pin) {
  return { pin, content: readContent(pin, locateIndex(root, pin)) };
}

/** `pkgsrc.segments` — every pin of `root`, verified, in pin-name order. */
export function segments(root) {
  return [...indexes(root).values()].map((pin) => segment(root, pin));
}

export function isPkg(text) {
  return typeof text === "string" && text.startsWith(SCHEME());
}

/** `pkgsrc.location` — `pkg:<docs package>@<version>#<loc>`. */
export function location(seg, loc) {
  return `${SCHEME()}${seg.content.name}${fixed("pkg_location", "version_sep")}${seg.content.version}`
    + `${fixed("pkg_location", "fragment")}${loc}`;
}

/** `pkgsrc.hit_fields` — the `location` and `package` every rendered hit carries. */
export function hitFields(recordId, loc, seg = null) {
  if (seg === null) return { location: recordId, package: null };
  return { location: location(seg, loc), package: seg.pin.name };
}

/** `pkgsrc.parse` — `[name, version, path]`, or refused. */
export function parse(text) {
  if (!isPkg(text)) throw new FuxError(refusal("malformed", { location: text }));
  const body = text.slice(SCHEME().length);
  const cut = body.indexOf(fixed("pkg_location", "fragment"));
  const spec = cut === -1 ? body : body.slice(0, cut);
  const path = cut === -1 ? "" : body.slice(cut + fixed("pkg_location", "fragment").length);
  const at = spec.lastIndexOf(fixed("pkg_location", "version_sep"));
  const name = at === -1 ? "" : spec.slice(0, at);
  const version = at === -1 ? "" : spec.slice(at + fixed("pkg_location", "version_sep").length);
  if (cut === -1 || !path || at === -1 || !name || !version) {
    throw new FuxError(refusal("malformed", { location: text }));
  }
  return [name, version, path];
}

/** `pkgsrc.find_segment`. */
export function findSegment(root, name, version, text) {
  for (const seg of segments(root)) {
    if (seg.content.version === version && (seg.content.npm === name || seg.content.pypi === name)) return seg;
  }
  throw new FuxError(refusal("not_pinned", { location: text, name, version }));
}

/** `pkgsrc.docs_root` — the installed docs package's root, version-checked. */
export function docsRoot(root, seg) {
  const { content, pin } = seg;
  const manifest = fixed("plugins.index", "manifest");
  if (!content.npm) {
    throw new FuxError(refusal("no_registry", {
      name: content.name, version: content.version, key: "npm", index: pin.name, manifest,
    }));
  }
  const name = content.npm;
  const install = `${fixed("plugins.index", "npm_install")} ${name}@${content.version}`;
  const common = { name, version: content.version, index: pin.name, index_version: pin.version, install };
  const have = installedVersion(root, name);
  if (have === null) throw new FuxError(refusal("missing", common));
  if (have !== content.version) throw new FuxError(refusal("drifted", { ...common, have }));
  const dir = packageDir(root, name);
  if (dir === null) throw new FuxError(refusal("no_root", { ...common, have }));
  return dir;
}

/** `pkgsrc.read` — `{ location, loc, path, content, sha }`, read in place. */
export function read(root, text) {
  const [name, version, fragment] = parse(text);
  const seg = findSegment(root, name, version, text);
  const base = docsRoot(root, seg);
  const target = contain(base, fragment);
  if (target === null) throw new FuxError(refusal("outside", { location: text, name, version }));
  let isFileNow = false;
  try { isFileNow = statSync(target).isFile(); } catch { isFileNow = false; }
  if (!isFileNow) throw new FuxError(refusal("not_file", { location: text, name, version }));
  const raw = readFileSync(target);
  return { location: text, loc: fragment, path: target, content: raw, sha: contentSha(raw) };
}

/** A `pkg:` location, read in place — `[raw, sha]`, like `source.mjs::readLocal`. */
export function readPackage(root, text) {
  const got = read(root, text);
  return [got.content, got.sha];
}

/** `pkgsrc.refuse` — the by-name refusal for a verb that reads only the
 *  repository's own documents. */
export function refuse(given, verb) {
  if (isPkg(given)) throw new FuxError(refusal("refused", { given, verb }));
}
