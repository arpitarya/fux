/** `graphRecords` — the graph plane's input, skimmed off raw bytes (W-235).
 *
 * The skim parses only `id` and `edges` and never materialises `terms`. Its
 * whole contract is that the result equals a full `JSON.parse` of each line,
 * reduced to those two fields — these are the lines most likely to break a
 * hand-written walk: escaped quotes and brackets inside strings, keys out of
 * order, whitespace, a record with no edges, and a line it cannot skim.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { graphRecords } from "../src/store/reader.mjs";
import { INDEX_DIR, SCHEMA_ID, ANALYZER_VERSION, TF_FIELDS } from "../src/store/format.mjs";

const HEADER = JSON.stringify({ _format: SCHEMA_ID, analyzer: ANALYZER_VERSION, tf_fields: TF_FIELDS });

const LINES = [
  // The writer's own shape: sorted keys, `terms` after `id`.
  '{"archived":false,"edges":[{"dst":"file:b.md","grade":10,"kind":"ref"}],"flen":[1],"id":"file:a.md","terms":{"aa":[1]}}',
  // Quotes, brackets, braces and a backslash inside strings.
  '{"edges":[{"at":{"x]":1},"dst":"file:we\\"ird]}.md","grade":5,"kind":"ref"}],"id":"file:c\\\\d.md","terms":{}}',
  // Keys out of order: `terms` first, so the skim must walk past it.
  '{"terms":{"k":[1,2,{"n":"]"}]},"id":"file:e.md","edges":[{"dst":"file:a.md","grade":1,"kind":"code"}]}',
  // Whitespace between tokens.
  '{ "edges" : [ ] , "id" : "file:f.md" }',
  // No edges at all.
  '{"id":"file:g.md","terms":{}}',
  // An escaped key that means `id` — the skim decodes keys, not bytes.
  '{"edges":[],"i\\u0064":"file:h.md"}',
];

function withIndex(lines, fn) {
  const root = mkdtempSync(join(tmpdir(), "fux-graph-records-"));
  try {
    mkdirSync(join(root, INDEX_DIR), { recursive: true });
    writeFileSync(join(root, INDEX_DIR, "00.jsonl"), [HEADER, ...lines].join("\n") + "\n");
    return fn(root);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
}

test("graphRecords equals a full parse reduced to id and edges", () => {
  withIndex(LINES, (root) => {
    const got = graphRecords(root).map((r) => ({ id: r.id, edges: r.edges }));
    const want = LINES.map((l) => JSON.parse(l)).map((r) => ({ id: r.id, edges: r.edges }));
    assert.deepEqual(got, want);
  });
});

test("graphRecords never parses terms", () => {
  // A `terms` value no JSON parser accepts: reaching it would throw, so a
  // passing test proves the skim stopped at `id`.
  withIndex(['{"edges":[],"id":"file:a.md","terms":{NOT JSON'], (root) => {
    assert.deepEqual(graphRecords(root), [{ edges: [], id: "file:a.md" }]);
  });
});
