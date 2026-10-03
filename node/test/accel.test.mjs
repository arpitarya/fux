/** W-242 Tier 1 — the offset table, decoded by Node from the file Python packed.
 *
 * `tests/derive/idx-fixture.idx` is three entries `derive/format.py::pack_entry`
 * wrote; `idx-fixture.json` is what they decode to. `test_idx_fixture.py` reads
 * the same two files in Python. A transposed field in either decoder is a
 * silent miss at query time, so this is the one place it can fail loudly. The
 * rows carry an offset past 2^32 and the u16/u32 maxima.
 *
 * The stamp parser is here too: `mtime_ns` is past 2^53, and reading it as a
 * `Number` is the bug that would make Node scan forever with every test green.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { ENTRY_SIZE, unpackEntry, packEntry } from "../src/derive/format.mjs";
import { readStamp } from "../src/derive/accel.mjs";

const ENGINE = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const FIXTURE = resolve(ENGINE, "tests", "derive");

test("the shared fixture decodes to its rows", () => {
  const buf = readFileSync(resolve(FIXTURE, "idx-fixture.idx"));
  const expected = JSON.parse(readFileSync(resolve(FIXTURE, "idx-fixture.json"), "utf8"));
  assert.equal(ENTRY_SIZE, expected.entry_size);
  assert.equal(buf.length, ENTRY_SIZE * expected.rows.length);
  expected.rows.forEach((row, i) => assert.deepEqual(unpackEntry(buf, i), row, `entry ${i}`));
});

test("packing the rows reproduces the file Python wrote", () => {
  const expected = JSON.parse(readFileSync(resolve(FIXTURE, "idx-fixture.json"), "utf8"));
  const packed = Buffer.concat(expected.rows.map((r) => packEntry(...r)));
  assert.deepEqual(packed, readFileSync(resolve(FIXTURE, "idx-fixture.idx")));
});

test("the stamp keeps every nanosecond a Number would round away", () => {
  // One past a multiple of 256: doubles are 256 apart here, so +0 and +1 from
  // this value are one double.
  const exact = 1791044792539219201n;
  const stamp = readStamp(`{"shards":{"00.jsonl":[4096,${exact}],"ff.jsonl":[1,${exact + 1n}]}}\n`);
  assert.equal(stamp.get("00.jsonl")[1], exact);
  assert.equal(stamp.get("ff.jsonl")[1], exact + 1n);
  assert.notEqual(stamp.get("00.jsonl")[1], stamp.get("ff.jsonl")[1]);
  assert.equal(Number(exact), Number(exact + 1n), "the hazard: as Numbers these are one value");
});

test("a stamp without a shards table is unreadable, never empty", () => {
  assert.equal(readStamp("{}"), null);
});
