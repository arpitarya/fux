/** The Node half of the index-package pin (W-299, SR-PKG-INDEX) — run with
 *  `node --test node/test/plugins-index.test.mjs`.
 *
 * No Python here: the segment is hand-made (a header-only shard is a legal
 * segment for verification), installed under a temporary consumer's
 * `node_modules/`. The full round trip — an ingested segment, inflated by both
 * runtimes to identical bytes — is `tests/test_pkg_index.py`'s differential.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, writeFileSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fixed } from "../src/config/constants.mjs";
import {
  checkIndex, indexes, locateIndex, parseIndexes, requireIndexPackages, segmentDigest, segmentDocs,
} from "../src/config/plugins.mjs";
import { FuxError } from "../src/errors.mjs";

const NAME = "acme-docs-index";

function header(change = {}) {
  return JSON.stringify({
    _format: fixed("index", "schema"), analyzer: fixed("index", "analyzer"),
    tf_fields: fixed("index", "tf_fields"), ...change,
  });
}

/** A consumer with the segment installed at `node_modules/acme-docs-index/`. */
function consumer({ shardHeader = header(), version = "1.0.0" } = {}) {
  const root = mkdtempSync(join(tmpdir(), "fux-pkg-index-"));
  const pkg = join(root, "node_modules", NAME);
  mkdirSync(join(pkg, "index"), { recursive: true });
  writeFileSync(join(pkg, "index", "00.jsonl"), `${shardHeader}\n{"id":"file:a.md"}\n`);
  writeFileSync(join(pkg, "identifiers.toml"), "");
  writeFileSync(join(pkg, "package.json"), JSON.stringify({ name: NAME, version }));
  const digest = segmentDigest(pkg);
  writeFileSync(join(pkg, fixed("plugins.index", "manifest")), JSON.stringify({ digest }));
  return { root, pkg, digest };
}

function declare(root, row) {
  const file = join(root, ...fixed("plugins", "file").split("/"));
  mkdirSync(join(file, ".."), { recursive: true });
  writeFileSync(file, row);
}

function row(digest, extra = "") {
  return `[[package]]\nname = "${NAME}"\nkind = "index"\nversion = "1.0.0"\ndigest = "${digest}"\nnpm = "${NAME}"\n${extra}`;
}

test("an index row is parsed; a decoder row beside it is not returned", () => {
  const pins = parseIndexes(`[[package]]\nname = "fux-decoder-json"\nversion = "1"\n${row("sha256:ab")}`);
  assert.deepEqual([...pins.keys()], [NAME]);
  assert.equal(pins.get(NAME).npm, NAME);
});

test("a malformed index row is refused by name", () => {
  for (const [text, words] of [
    [row("", 'suffixes = [".md"]\n'), "delete its `suffixes` key"],
    [row("", 'colour = "red"\n'), "unknown key(s) colour"],
    [row("") + row(""), "is declared twice"],
    ['[[package]]\nname = "x"\nkind = "decoder"\nversion = "1"\n', "may only be 'index'"],
  ]) {
    assert.throws(() => parseIndexes(text), (err) => err instanceof FuxError && err.message.includes(words));
  }
});

test("a good pin verifies, locates from the repo root and counts its documents", () => {
  const { root, pkg, digest } = consumer();
  declare(root, row(digest));
  const pin = indexes(root).get(NAME);
  assert.deepEqual(checkIndex(root, pin), [null, null]);
  assert.equal(locateIndex(root, pin), pkg);
  assert.equal(segmentDocs(pkg), 1);
  rmSync(root, { recursive: true, force: true });
});

test("drift, another version and a foreign header refuse with the npm install line", () => {
  const { root, pkg, digest } = consumer();
  declare(root, row(digest));
  const shard = join(pkg, "index", "00.jsonl");
  writeFileSync(shard, readFileSync(shard, "utf8") + "\n");
  const [code, message] = checkIndex(root, indexes(root).get(NAME));
  assert.equal(code, "drifted");
  assert.ok(message.includes(`npm install ${NAME}@1.0.0`));
  assert.throws(() => requireIndexPackages(root), /has drifted/);
  rmSync(root, { recursive: true, force: true });

  const other = consumer({ version: "2.0.0" });
  declare(other.root, row(other.digest));
  assert.equal(checkIndex(other.root, indexes(other.root).get(NAME))[0], "other_version");
  rmSync(other.root, { recursive: true, force: true });

  const alien = consumer({ shardHeader: header({ analyzer: "v0" }) });
  declare(alien.root, row(alien.digest));
  const [fcode, fmessage] = checkIndex(alien.root, indexes(alien.root).get(NAME));
  assert.equal(fcode, "foreign");
  assert.ok(fmessage.includes('analyzer "v0"'));
  rmSync(alien.root, { recursive: true, force: true });
});

test("another identifiers digest is not refused (W-300 hashes per digest)", () => {
  const { root, digest } = consumer({ shardHeader: header({ identifiers: "0".repeat(32) }) });
  declare(root, row(digest));
  assert.deepEqual(checkIndex(root, indexes(root).get(NAME)), [null, null]);
  rmSync(root, { recursive: true, force: true });
});

test("a row with no npm name cannot be read by Node", () => {
  const { root, digest } = consumer();
  declare(root, row(digest).replace(`npm = "${NAME}"\n`, `pypi = "${NAME}"\n`));
  assert.equal(checkIndex(root, indexes(root).get(NAME))[0], "no_registry");
  rmSync(root, { recursive: true, force: true });
});
