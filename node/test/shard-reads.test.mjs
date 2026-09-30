/** W-242 Tier 0 — a Node query reads each committed shard AT MOST ONCE.
 *
 * The spy is on `fs.readFileSync` itself, installed through
 * `syncBuiltinESMExports` so the reader's own `import { readFileSync }` binding
 * sees it: nothing in the reader was changed to make it countable, so a pass
 * that bypasses `Shards` is counted exactly like one that uses it.
 *
 * Run against this repository's committed index, whose `.fux/tune.toml` turns
 * on the graph tier and the mined table — the two passes that used to read
 * every shard a second and third time. Before Tier 0 this test failed at 3.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { syncBuiltinESMExports } from "node:module";
import { join, resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { runFind } from "../src/verbs/find.mjs";
import { runAsk } from "../src/verbs/ask.mjs";
import { runAnswer } from "../src/verbs/answer.mjs";
import { graphRecords, indexDir } from "../src/store/reader.mjs";
import { applyOutputDefaults, loadOutput } from "../src/config/output.mjs";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const SHARDS = indexDir(ROOT);

/** Run `fn` with `readFileSync` spied; return `Map(shard path -> reads)`. */
function countShardReads(fn) {
  const real = fs.readFileSync;
  const counts = new Map();
  fs.readFileSync = function spied(path, ...rest) {
    const p = String(path);
    if (p.startsWith(SHARDS) && p.endsWith(".jsonl")) counts.set(p, (counts.get(p) ?? 0) + 1);
    return real.call(this, path, ...rest);
  };
  syncBuiltinESMExports();
  const write = process.stdout.write;
  process.stdout.write = () => true;
  try {
    fn();
  } finally {
    process.stdout.write = write;
    fs.readFileSync = real;
    syncBuiltinESMExports();
  }
  return counts;
}

/** The verb's args exactly as `fux.mjs::main` hands them over. */
function argsFor(verb, argv) {
  const args = { _: [argv[0]], json: true, ...argv[1] };
  applyOutputDefaults(verb, args, loadOutput(ROOT, { enabled: true }));
  return args;
}

const CELLS = [
  ["find", () => runFind(ROOT, argsFor("find", ["rollback", { top: 5 }]))],
  ["ask", () => runAsk(ROOT, argsFor("ask", ["rollback", { top: 20, band: true }]), { compose: true })],
  ["answer", () => runAnswer(ROOT, argsFor("answer", ["rollback", {}]))],
  // `-q` fusion: a second phrasing is a second query over the SAME read.
  ["ask -q", () => runAsk(ROOT, argsFor("ask", ["rollback", { top: 5, q: ["revert"] }]), { compose: true })],
];

for (const [name, run] of CELLS) {
  test(`${name}: at most one read of each shard per query`, () => {
    const counts = countShardReads(run);
    const over = [...counts].filter(([, n]) => n > 1);
    assert.deepEqual(over, [], `shards read more than once: ${over.map(([p, n]) => `${p} x${n}`).join(", ")}`);
    // Non-vacuous: the graph tier is on in this repo's tune, so every shard IS read.
    assert.ok(counts.size > 0, "no shard was read at all — the spy is not seeing the reader");
  });
}

test("the spy sees a second pass — so a pass round `Shards` cannot hide", () => {
  const counts = countShardReads(() => { graphRecords(ROOT); graphRecords(ROOT); });
  assert.ok([...counts.values()].every((n) => n === 2), "two uncached passes must count 2 each");
});

test("nothing outlives a call: two queries read each shard twice between them", () => {
  const counts = countShardReads(() => { CELLS[0][1](); CELLS[0][1](); });
  assert.ok(counts.size > 0);
  assert.ok([...counts.values()].every((n) => n === 2), "a shard read once across two calls is a module-level cache");
});

test("the spied paths are the index's own shards", () => {
  assert.ok(fs.existsSync(join(SHARDS)), `${SHARDS} is missing — the test cannot measure anything`);
});
