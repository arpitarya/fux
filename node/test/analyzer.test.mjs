/** W-202 — the Node reader analyzes an identifier exactly as Python does.
 *
 * 🔴 **A MECHANISM PROBE, never a ranking verdict.** It compares nothing, has
 * no arm and no bar. It says what `analyze()` emits; it says nothing about
 * whether that is good.
 *
 * 🔴 **The fixture is the SAME FILE the Python test reads** —
 * `tests/query/identifier-fixture.json`. That is the whole point of this file
 * existing: `node/src/query/analyzer.mjs` is a transcription of
 * `src/fux/query/analyzer.py`, and a one-step divergence between them is a
 * **silent no-match** — the Node reader hashes a string the Python-built index
 * never wrote, and there is no error to see. Two copies of the fixture would
 * let one be updated and the other forgotten, which is the exact drift this
 * guards.
 *
 * ⚠ **So a failure here has two readings and they need different fixes.** If
 * Python's fixture test passes and this one fails, the transcription has
 * drifted and `analyzer.mjs` is wrong. If both fail on the same rows, the
 * analyzer changed on purpose and the fixture is owed an update **with the
 * moving rows named in the item that changed it**.
 *
 * Run: `node --test node/test/analyzer.test.mjs` (⚠ not the bare directory —
 * `work/MACHINE.md` §Two test invocations).
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import { analyze } from "../src/query/analyzer.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const FIXTURE = JSON.parse(
  readFileSync(join(HERE, "..", "..", "tests", "query", "identifier-fixture.json"), "utf8"),
);

test("the fixture is the shared one, and it is populated", () => {
  assert.equal(FIXTURE.seed.length, 33);
  assert.ok(FIXTURE.contrast.length > 0);
  assert.ok(FIXTURE._read_by.includes("node/test/analyzer.test.mjs"));
});

for (const row of FIXTURE.seed) {
  test(`seed identifier ${row.identifier} analyzes as frozen`, () => {
    assert.deepEqual(
      analyze(row.identifier),
      row.tokens,
      `${row.identifier}: the Node analyzer disagrees with the frozen fixture. ` +
        "If the Python fixture test still passes, analyzer.mjs has drifted from " +
        "analyzer.py — fix the transcription, not the fixture.",
    );
  });
}

for (const row of FIXTURE.contrast) {
  test(`contrast ${row.token} analyzes as frozen (${row.why})`, () => {
    assert.deepEqual(analyze(row.token), row.tokens);
  });
}

test("not one seed identifier survives whole, on this reader either", () => {
  const whole = FIXTURE.seed.filter((r) => {
    const out = analyze(r.identifier);
    return out.length === 1 && out[0] === r.identifier.toLowerCase();
  });
  assert.deepEqual(whole, []);
});

test("the three segments Python loses to the stopword list are lost here too", () => {
  // `QCL-IT-ADR-08` loses `IT`; `TSL-RF-118-A` and `TSL-RF-221-A` lose `A`.
  // A stopword list that drifted between the readers would show up here and
  // nowhere else — the two lists are separate literals in separate files.
  assert.deepEqual(analyze("QCL-IT-ADR-08"), ["qcl", "adr", "08"]);
  assert.deepEqual(analyze("TSL-RF-118-A"), ["tsl", "rf", "118"]);
  assert.deepEqual(analyze("TSL-RF-221-A"), ["tsl", "rf", "221"]);
});
