/** W-242 Tier 2 — `compat/pyjson.mjs` writes what CPython's `json.dumps` writes.
 *
 * The expected strings were printed by `json.dumps` itself, with the arguments
 * `derive/_build.py` and `graph/plane.py` pass. They cover the three
 * differences from `JSON.stringify` that a byte-identical plane cannot have:
 * code-point key order, `ensure_ascii` (astral characters as surrogate pairs,
 * DEL escaped), and integers past 2^53.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { pyDumps } from "../src/compat/pyjson.mjs";

const VALUE = new Map([
  ["z", 1],
  ["a", ["é😀\u007f\n\t\"\\", null, true]],
  ["é", new Map([["b", 2], ["B", 3]])],
  ["😀", 0],
]);

test("sort_keys=True, ensure_ascii=False — the docs table, stats, manifest", () => {
  assert.equal(
    pyDumps(VALUE, { sortKeys: true, ensureAscii: false }),
    "{\"a\":[\"é😀\u007f\\n\\t\\\"\\\\\",null,true],\"z\":1,\"é\":{\"B\":3,\"b\":2},\"😀\":0}",
  );
});

test("sort_keys=False, ensure_ascii=True — graph.json", () => {
  assert.equal(
    pyDumps(VALUE, { sortKeys: false, ensureAscii: true }),
    "{\"z\":1,\"a\":[\"\\u00e9\\ud83d\\ude00\\u007f\\n\\t\\\"\\\\\",null,true],\"\\u00e9\":{\"b\":2,\"B\":3},\"\\ud83d\\ude00\":0}",
  );
});

test("an integer past 2^53 is written exactly — a stamp's mtime_ns", () => {
  assert.equal(pyDumps({ n: 1791044792539219327n }, { sortKeys: true, ensureAscii: false }), "{\"n\":1791044792539219327}");
});

test("a float is refused rather than written in the wrong repr", () => {
  assert.throws(() => pyDumps({ x: 0.5 }, { sortKeys: true, ensureAscii: false }), /integers only/);
});
