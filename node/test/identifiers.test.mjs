/** W-233 — the Node reader matches identifier families exactly as Python does.
 *
 * 🔴 **The fixture is the SAME FILE the Python test reads** —
 * `tests/query/identifiers-fixture.json`. `node/src/query/identifiers.mjs` is
 * a transcription of `src/fux/query/identifiers.py`, and a divergence is a
 * silent no-match: the query writes a canonical term the index never did.
 *
 * ⚠ If Python's `tests/query/test_identifiers.py` passes and this fails, the
 * transcription drifted — fix `identifiers.mjs` or `analyzer.mjs`, not the
 * fixture.
 *
 * Run: `node --test node/test/identifiers.test.mjs`.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { readFileSync } from "node:fs";

import { analyze, analyzePairs } from "../src/query/analyzer.mjs";
import { EMPTY, build, checkRegex, loadIdentifiers, parseTemplate } from "../src/query/identifiers.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const FIXTURE = JSON.parse(
  readFileSync(join(HERE, "..", "..", "tests", "query", "identifiers-fixture.json"), "utf8"),
);
const RULES = build(FIXTURE.families.templates, [], [], FIXTURE.families.regex);

test("the fixture is the shared one, and it is populated", () => {
  assert.ok(FIXTURE.analysis.length > 20);
  assert.ok(FIXTURE._read_by.includes("node/test/identifiers.test.mjs"));
});

for (const row of FIXTURE.analysis) {
  test(`families: ${JSON.stringify(row.text)} analyzes as frozen`, () => {
    assert.deepEqual(analyze(row.text, RULES), row.terms);
    assert.deepEqual(analyzePairs(row.text, RULES).map((p) => p[1]), row.terms);
  });
  test(`no families: ${JSON.stringify(row.text)} is v3 byte for byte`, () => {
    assert.deepEqual(analyze(row.text, EMPTY), analyze(row.text));
  });
}

for (const src of FIXTURE.templates_accepted) {
  test(`template accepted: ${src}`, () => assert.equal(parseTemplate(src).kind, "template"));
}
for (const src of FIXTURE.templates_refused) {
  test(`template refused: ${JSON.stringify(src)}`, () => assert.throws(() => parseTemplate(src), { name: "FuxError" }));
}
for (const row of FIXTURE.regex_accepted) {
  test(`regex accepted: ${row.regex}`, () => assert.equal(checkRegex(row.regex), row.normalised));
}
for (const src of FIXTURE.regex_refused) {
  test(`regex refused: ${src}`, () => assert.throws(() => checkRegex(src), { name: "FuxError" }));
}

test("a canonical term is never stemmed, even an all-letter one", () => {
  const rules = build([], [], [], ["[A-Z]{3}ING"]);
  assert.ok(analyze("see ABCING now", rules).includes("abcing"));
});

test("drop beats keep and detected; rules sort by code point", () => {
  const r = build(["RF-{n}"], ["RF-{n}", "ADR-{n}"], ["RF-{n}"], []);
  assert.deepEqual(r.rules.map((x) => x.source), ["ADR-{n}"]);
});

test("loadIdentifiers: missing is an error, empty sections are valid, [user] only is valid", () => {
  const root = mkdtempSync(join(tmpdir(), "fux-ids-"));
  assert.throws(() => loadIdentifiers(root), /identifiers\.toml is missing/);
  mkdirSync(join(root, ".fux"));
  writeFileSync(join(root, ".fux", "identifiers.toml"), "[user]\nkeep = []\n\n[detected]\nfamilies = []\n");
  assert.ok(loadIdentifiers(root).empty);
  writeFileSync(join(root, ".fux", "identifiers.toml"), '[user]\nkeep = ["RF-{n}"]\n');
  assert.deepEqual(loadIdentifiers(root).rules.map((r) => r.source), ["RF-{n}"]);
  writeFileSync(join(root, ".fux", "identifiers.toml"), '[user]\nkeeps = ["RF-{n}"]\n');
  assert.throws(() => loadIdentifiers(root), { name: "FuxError" });
});
