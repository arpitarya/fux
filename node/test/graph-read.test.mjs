/** W-259 (Fork A) — Node reads `.fux/runtime/graph.json` when it is fresh.
 *
 * Three things are held here, on a temporary root built from sixteen of this
 * repository's committed shards and planed by Node's own `fux build`:
 *
 * 1. **The read is the rebuild.** `planeFor` on a fresh plane returns the bytes
 *    `buildPlane(graphRecords(...))` returns, and every degraded state — stale,
 *    absent, torn, a foreign schema, no runtime at all — is a rebuild that
 *    answers the same, never an error (SR-NODE-SEARCH decision 9).
 * 2. **The switch is the arm's guarantee.** With `FUX_GRAPH_REBUILD=1` no verb
 *    that touches the graph opens `graph.json` — find, ask, explain, graph,
 *    path and both MCP tools — so the differential arm, which sets it on every
 *    Node process, never compares Python's plane with itself (N2).
 * 3. **The read is real.** Without the switch, `ask` and `explain` DO open the
 *    file, and their stdout equals the switched run byte for byte. A spy that
 *    counted nothing would make test 2 pass vacuously.
 *
 * The spy is `fs.readFileSync` itself through `syncBuiltinESMExports`, the
 * `shard-reads.test.mjs` pattern: nothing in the reader changed to be countable.
 */
import { test, after } from "node:test";
import assert from "node:assert/strict";
import fs, {
  copyFileSync, cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, utimesSync, writeFileSync,
} from "node:fs";
import { syncBuiltinESMExports } from "node:module";
import { tmpdir } from "node:os";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { build } from "../src/derive/build.mjs";
import { runtimeDir, GRAPH_NAME } from "../src/derive/format.mjs";
import { buildPlane, planeBytes, planeFor, REBUILD_ENV } from "../src/graph/plane.mjs";
import { graphRecords, indexDir, iterShardPaths } from "../src/store/reader.mjs";
import { applyOutputDefaults, loadOutput } from "../src/config/output.mjs";
import { runFind } from "../src/verbs/find.mjs";
import { runAsk } from "../src/verbs/ask.mjs";
import { runExplain, runGraph, runPath } from "../src/verbs/graph.mjs";
import { handle } from "../src/verbs/mcp.mjs";

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");

/** A root with sixteen real shards, this repo's config, and a fresh plane. */
function fixture() {
  const root = mkdtempSync(join(tmpdir(), "fux-graph-read-"));
  mkdirSync(indexDir(root), { recursive: true });
  for (const path of iterShardPaths(REPO).slice(0, 16)) {
    copyFileSync(path, join(indexDir(root), basename(path)));
  }
  copyFileSync(join(REPO, "fux.toml"), join(root, "fux.toml"));
  // This repo's tune turns the graph tier on, which is what makes `ask` read.
  for (const name of ["tune.toml", "output.toml", "identifiers.toml", "formats.toml"]) {
    copyFileSync(join(REPO, ".fux", name), join(root, ".fux", name));
  }
  cpSync(join(REPO, ".fux", "sources"), join(root, ".fux", "sources"), { recursive: true });
  build(root);
  return root;
}

const ROOT = fixture();
after(() => rmSync(ROOT, { recursive: true, force: true }));
const GRAPH = join(runtimeDir(ROOT), GRAPH_NAME);
const RUNTIME = basename(runtimeDir(ROOT));

/** Run `fn` with `readFileSync` spied; return `{reads, out}` — graph.json opens and stdout. */
function spied(fn) {
  const real = fs.readFileSync;
  let reads = 0;
  fs.readFileSync = function spy(path, ...rest) {
    const p = String(path);
    if (basename(p) === GRAPH_NAME && basename(dirname(p)) === RUNTIME) reads++;
    return real.call(this, path, ...rest);
  };
  syncBuiltinESMExports();
  const write = process.stdout.write;
  let out = "";
  process.stdout.write = (chunk) => { out += chunk; return true; };
  try {
    fn();
  } finally {
    process.stdout.write = write;
    fs.readFileSync = real;
    syncBuiltinESMExports();
  }
  return { reads, out };
}

/** `fn` with the harness switch set, then restored. */
function switched(fn) {
  const before = process.env[REBUILD_ENV];
  process.env[REBUILD_ENV] = "1";
  try { return fn(); } finally {
    if (before === undefined) delete process.env[REBUILD_ENV]; else process.env[REBUILD_ENV] = before;
  }
}

const rebuilt = (root) => planeBytes(buildPlane(graphRecords(root)));

test("the switch is the name constants.toml gives it", () => {
  assert.equal(REBUILD_ENV, "FUX_GRAPH_REBUILD");
});

test("a fresh plane is READ, once, and equals the rebuild byte for byte", () => {
  const { reads } = spied(() => {
    assert.equal(planeBytes(planeFor(ROOT)), rebuilt(ROOT));
  });
  assert.equal(reads, 1);
  // And the file is what `fux build` wrote — the read is not reserializing itself.
  assert.equal(readFileSync(GRAPH, "utf8"), rebuilt(ROOT));
});

test("with the switch set, the plane is rebuilt and graph.json is never opened", () => {
  const { reads } = spied(() => switched(() => {
    assert.equal(planeBytes(planeFor(ROOT)), rebuilt(ROOT));
  }));
  assert.equal(reads, 0);
});

/** A throwaway copy of the fixture, freshly planed, for the states that damage it.
 *  Re-built rather than trusted: a copy's mtimes are not the stamp's. */
function copyOf() {
  const root = mkdtempSync(join(tmpdir(), "fux-graph-read-copy-"));
  cpSync(ROOT, root, { recursive: true });
  build(root);
  assert.equal(spied(() => planeFor(root)).reads, 1, "the copy's plane is not fresh — nothing below would be tested");
  return root;
}

const DEGRADED = [
  ["a stale plane (a shard's mtime moved)", (root) => {
    const [shard] = iterShardPaths(root);
    utimesSync(shard, new Date(2_000_000_000_000), new Date(2_000_000_000_000));
  }, 0],
  ["an absent graph.json", (root) => rmSync(join(runtimeDir(root), GRAPH_NAME)), 1],
  ["a torn graph.json (a prefix, as a reader sees mid-rewrite)", (root) => {
    const path = join(runtimeDir(root), GRAPH_NAME);
    const bytes = readFileSync(path);
    writeFileSync(path, bytes.subarray(0, bytes.length >> 1));
  }, 1],
  ["a foreign graph schema", (root) => {
    const path = join(runtimeDir(root), GRAPH_NAME);
    writeFileSync(path, readFileSync(path, "utf8").replace(/"schema":"[^"]*"/, '"schema":"fux.graph.v0"'));
  }, 1],
  ["no runtime directory at all", (root) => rmSync(runtimeDir(root), { recursive: true }), 0],
];

for (const [name, damage, opens] of DEGRADED) {
  test(`${name} is a rebuild, never an error`, () => {
    const root = copyOf();
    try {
      damage(root);
      const { reads } = spied(() => {
        assert.equal(planeBytes(planeFor(root)), rebuilt(root));
      });
      // Stale and absent-runtime are refused BEFORE the file is opened.
      assert.equal(reads, opens);
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });
}

/** Every Node verb that touches the graph, as `fux.mjs::main` hands it over. */
function argsFor(verb, rest) {
  const args = { _: rest._, json: true, ...rest };
  applyOutputDefaults(verb, args, loadOutput(ROOT, { enabled: true }));
  return args;
}

const [DOC_A, DOC_B] = (() => {
  const ids = graphRecords(ROOT).filter((r) => (r.edges ?? []).length).map((r) => r.id).sort();
  return [ids[0].slice("file:".length), ids[ids.length - 1].slice("file:".length)];
})();

const mcpCalls = () => {
  const out = [];
  for (const [name, args] of [
    ["fux_search", { query: "graph plane", k: 5 }],
    ["fux_related", { path: DOC_A }],
  ]) {
    out.push(JSON.stringify(handle(ROOT, {
      jsonrpc: "2.0", id: out.length + 1, method: "tools/call", params: { name, arguments: args },
    }, 5, 3)));
  }
  process.stdout.write(out.join("\n"));
};

const VERBS = [
  ["find", () => runFind(ROOT, argsFor("find", { _: ["graph plane"], top: 5 }))],
  ["ask", () => runAsk(ROOT, argsFor("ask", { _: ["graph plane"], top: 5, band: true }), { compose: true })],
  ["explain", () => runExplain(ROOT, { _: [DOC_A], json: true })],
  ["graph", () => runGraph(ROOT, { _: ["graph plane"], json: true })],
  ["graph --seed", () => runGraph(ROOT, { _: [], seed: [DOC_A], json: true })],
  ["path", () => runPath(ROOT, { _: [DOC_A, DOC_B], json: true, hops: 3 })],
  ["mcp fux_search + fux_related", mcpCalls],
];

for (const [name, run] of VERBS) {
  test(`${name}: the switch opens graph.json zero times, and the read answers the same bytes`, () => {
    const off = spied(() => switched(run));
    assert.equal(off.reads, 0, `${name} read graph.json with ${REBUILD_ENV}=1`);
    const on = spied(run);
    assert.equal(on.out, off.out, `${name}: stdout differs between the read and the rebuild`);
    assert.ok(on.out.length > 0, `${name} printed nothing — the comparison would be vacuous`);
  });
}

test("the read path is real: ask and explain open graph.json once without the switch", () => {
  for (const [name, run] of VERBS.filter(([n]) => n === "ask" || n === "explain")) {
    assert.equal(spied(run).reads, 1, `${name} did not read the fresh plane`);
  }
});
