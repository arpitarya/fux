/** W-249 — `fux mcp` holds its `Shards` across tool calls, keyed on the stamp.
 *
 * Twin of `tests/test_resident.py`'s key tests, against `verbs/mcp.mjs::Resident`
 * directly: two real shards copied out of this repository's committed index
 * into a temporary root, so the key can be moved without touching the repo.
 * What is counted is `Shards.reads` and `Resident.loads` — never timing.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync, utimesSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { Resident, stateKey } from "../src/verbs/mcp.mjs";
import { indexDir, iterShardPaths } from "../src/store/reader.mjs";
import { runtimeDir, STAMP_NAME } from "../src/derive/format.mjs";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");

/** A root holding two of this repo's shards and a stamp. */
function fixture() {
  const root = mkdtempSync(join(tmpdir(), "fux-resident-"));
  mkdirSync(indexDir(root), { recursive: true });
  for (const path of iterShardPaths(ROOT).slice(0, 2)) {
    copyFileSync(path, join(indexDir(root), basename(path)));
  }
  mkdirSync(runtimeDir(root), { recursive: true });
  writeFileSync(join(runtimeDir(root), STAMP_NAME), '{"shards":{}}\n');
  return root;
}

/** One call that reads every shard, as `fux_search`'s scan does. */
const readAll = (shards) => shards.paths().map((p) => shards.lines(p).length);

test("a second call reads nothing from disk", () => {
  const root = fixture();
  try {
    const resident = new Resident(root);
    const first = resident.call(readAll);
    const reads = resident.shards.reads;
    assert.ok(reads > 0);
    assert.deepEqual(resident.call(readAll), first);
    assert.equal(resident.shards.reads, reads);
    assert.equal(resident.loads, 1);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("a stamp rewritten with identical bytes does not reload; a different one does", () => {
  const root = fixture();
  try {
    const resident = new Resident(root);
    resident.call(readAll);
    const stamp = join(runtimeDir(root), STAMP_NAME);
    writeFileSync(stamp, readFileSync(stamp));
    resident.call(readAll);
    assert.equal(resident.loads, 1);
    writeFileSync(stamp, '{"shards":{"00.jsonl":[1,2]}}\n');
    resident.call(readAll);
    assert.equal(resident.loads, 2);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("a shard rewritten without a new stamp reloads — the stamp alone is not the key", () => {
  const root = fixture();
  try {
    const resident = new Resident(root);
    resident.call(readAll);
    const before = stateKey(root);
    const [shard] = iterShardPaths(root);
    utimesSync(shard, new Date(2_000_000_000_000), new Date(2_000_000_000_000));
    assert.notEqual(stateKey(root), before);
    resident.call(readAll);
    assert.equal(resident.loads, 2);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("no .fux/runtime/ is a key, not an error, and the shards are still held", () => {
  const root = fixture();
  try {
    rmSync(runtimeDir(root), { recursive: true, force: true });
    assert.ok(stateKey(root).startsWith("null|"));
    const resident = new Resident(root);
    resident.call(readAll);
    const reads = resident.shards.reads;
    resident.call(readAll);
    assert.equal(resident.shards.reads, reads);
    assert.equal(resident.loads, 1);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
