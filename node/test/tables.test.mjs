/** W-287 — a table row as a record, in Node alone.
 *
 * `tests/refer/test_table_twins.py` holds Node and Python equal on chunking and
 * scoring. These are the pieces that can fail with no Python installed: the
 * cell splitter, the row metadata, and the order an answer prints a record in.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { chunk, splitRow, cellsOf } from "../src/refer/chunk.mjs";
import { recordOf } from "../src/refer/assemble.mjs";

const BOUNDS = { minPassageBytes: 1, maxPassageBytes: 4000, tableRowsPerPassage: 1, lineNumbers: true };

test("a row's cells: edge pipes off, an escaped pipe kept as a character", () => {
  assert.deepEqual(splitRow("| INC2 | Bob \\| B | open |"), ["INC2", "Bob | B", "open"]);
  assert.deepEqual(splitRow("web-1 | Alice | eu"), ["web-1", "Alice", "eu"]);
});

test("a pipe-less GFM table is split one row per passage, each with its row", () => {
  const md = "# Hosts\n\nhost | owner\n--- | ---\nweb-1 | Alice\nweb-2 | Bob\n";
  const rows = chunk(md, BOUNDS).filter((p) => p.row);
  assert.equal(rows.length, 2);
  assert.deepEqual(cellsOf(rows[1].row), [["host", "web-2"], ["owner", "Bob"]]);
  assert.equal(rows[1].row.ordinal, 2);
  assert.equal(rows[1].row.key, 0);
});

test("a Field | Value table is a record: each row names its own field", () => {
  const md = "# Service\n\n| Field | Value |\n|---|---|\n| Owner | Erin |\n| Pager | sre |\n";
  const rows = chunk(md, BOUNDS).filter((p) => p.row);
  assert.ok(rows.every((p) => p.row.record));
  assert.deepEqual(cellsOf(rows[1].row), [["Pager", "sre"]]);
});

test("a record prints the asked cell first and leaves out empty cells", () => {
  const citation = {
    cells: [["Ticket", "INC2"], ["Owner", "Bob"], ["Status", ""], ["Notes", "none"]],
    columns_matched: ["Owner"],
  };
  assert.deepEqual(recordOf(citation), [["Owner", "Bob", true], ["Ticket", "INC2", false], ["Notes", "none", false]]);
  assert.deepEqual(recordOf({ cells: null, columns_matched: [] }), []);
});
