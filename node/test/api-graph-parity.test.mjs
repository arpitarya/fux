/** W-262 — the library's `explain` / `graph` / `path` return what `--json` prints.
 *
 * Arpit, 2026-10-04, W-251 #4: library → CLI shape. `index.mjs` used to mirror
 * `api.py`'s older helpers (`{id, community, members, edges}`, a breadth-first
 * best route, a walk seeded off the BOOSTED ranking) and both differed from
 * both CLIs. The CLI's shapes carry rulings — SR-CLI decision 13, SR-GRAPH
 * decision 13 (lexical seeds), `truncated` on `path` — so the library moved to
 * them. This file holds `open().explain|graph|path` equal to the parsed stdout
 * of `runExplain|runGraph|runPath --json` on the same root; the Python pair is
 * `tests_e2e/test_relational.py`, and Python-vs-Node is the differential arm's
 * `api` lane.
 */
import { test, after } from "node:test";
import assert from "node:assert/strict";
import { copyFileSync, cpSync, mkdirSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { build } from "../src/derive/build.mjs";
import { buildPlane } from "../src/graph/plane.mjs";
import { graphRecords, indexDir, iterShardPaths } from "../src/store/reader.mjs";
import { runExplain, runGraph, runPath } from "../src/verbs/graph.mjs";
import { open } from "../src/index.mjs";
import { FuxError } from "../src/errors.mjs";

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");

/** A root with sixteen real shards and this repo's config, planed by Node. */
function fixture() {
  const root = mkdtempSync(join(tmpdir(), "fux-api-graph-"));
  mkdirSync(indexDir(root), { recursive: true });
  for (const path of iterShardPaths(REPO).slice(0, 16)) {
    copyFileSync(path, join(indexDir(root), basename(path)));
  }
  copyFileSync(join(REPO, "fux.toml"), join(root, "fux.toml"));
  for (const name of ["tune.toml", "output.toml", "identifiers.toml", "formats.toml", "pii.toml"]) {
    copyFileSync(join(REPO, ".fux", name), join(root, ".fux", name));
  }
  cpSync(join(REPO, ".fux", "sources"), join(root, ".fux", "sources"), { recursive: true });
  build(root);
  return root;
}

const ROOT = fixture();
after(() => rmSync(ROOT, { recursive: true, force: true }));

/** Parsed stdout of one CLI verb run in-process. */
function cli(fn) {
  const write = process.stdout.write;
  let out = "";
  process.stdout.write = (chunk) => { out += chunk; return true; };
  try {
    assert.equal(fn(), 0);
  } finally {
    process.stdout.write = write;
  }
  return JSON.parse(out);
}

/** A document with outbound edges to another DOCUMENT, so `path` has a route. */
function linkedPair() {
  const records = graphRecords(ROOT);
  const held = new Set(records.map((r) => r.id));
  const plane = buildPlane(records);
  for (const node of plane.graph.nodes) {
    if (!held.has(node)) continue;
    const dst = plane.graph.outEdges(node).find((e) => held.has(e.dst));
    if (dst) return [node, dst.dst];
  }
  throw new Error("fixture holds no document-to-document edge");
}

const [SRC, DST] = linkedPair();

test("explain: the library returns the CLI payload", async () => {
  const ix = await open(ROOT);
  assert.deepEqual(await ix.explain(SRC), cli(() => runExplain(ROOT, { _: [SRC], json: true })));
  // The `loc` a human types resolves exactly as the CLI resolves it.
  const loc = SRC.slice("file:".length);
  assert.deepEqual(await ix.explain(loc), cli(() => runExplain(ROOT, { _: [loc], json: true })));
});

test("graph: the library returns the CLI payload, query and seed forms", async () => {
  const ix = await open(ROOT);
  assert.deepEqual(
    await ix.graph("graph plane"),
    cli(() => runGraph(ROOT, { _: ["graph", "plane"], json: true })),
  );
  assert.deepEqual(
    await ix.graph(null, { seed: [SRC], kinds: ["ref"] }),
    cli(() => runGraph(ROOT, { _: [], seed: [SRC], kinds: "ref", json: true })),
  );
});

test("path: the library returns the CLI payload, `truncated` always present", async () => {
  const ix = await open(ROOT);
  const got = await ix.path(SRC, DST, { hops: 3 });
  assert.deepEqual(got, cli(() => runPath(ROOT, { _: [SRC, DST], hops: 3, json: true })));
  assert.equal(typeof got.truncated, "boolean");
  assert.ok(got.paths.length > 0);
});

test("the library refuses what the CLI refuses", async () => {
  const ix = await open(ROOT);
  await assert.rejects(ix.explain("docs/does-not-exist.md"), FuxError);
  await assert.rejects(ix.path("docs/does-not-exist.md", DST, { hops: 2 }), FuxError);
  await assert.rejects(ix.graph("rollback", { seed: [SRC] }), FuxError);
});
