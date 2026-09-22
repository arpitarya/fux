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

test("every seed identifier survives whole, on this reader too", () => {
  // 🔴 **33 of 33, and it was 0 of 33 until 2026-09-21** (W-205 part 2, family
  // (a) — analyzer v3). `-`, `.` and `/` are now identifier separators exactly
  // as `_` always was.
  //
  // ⚠ **The v2 form of this test would now pass while checking NOTHING.** It
  // asked `out.length === 1 && out[0] === id`, i.e. *the whole token and
  // nothing else* — a spelling that was only adequate while the answer was no
  // for every row. Under v3 the whole form arrives BESIDE its parts, so
  // `length === 1` is never true, the filter is always empty and the assertion
  // is vacuous. Membership is the question now, on both readers.
  const missing = FIXTURE.seed.filter(
    (r) => !analyze(r.identifier).includes(r.identifier.toLowerCase()),
  );
  assert.deepEqual(missing, []);
  assert.equal(FIXTURE.seed.length, 33);
});

test("the three segments Python loses to the stopword list are lost here too", () => {
  // `QCL-IT-ADR-08` still loses `IT`; `TSL-RF-118-A` and `TSL-RF-221-A` still
  // lose `A`. A stopword list that drifted between the readers would show up
  // here and nowhere else — the two lists are separate literals in separate
  // files.
  //
  // 🔴 v3 did not change the stopword class; it changed what it costs. The
  // whole form now carries the dropped segment, so `TSL-RF-118-A` is no longer
  // indistinguishable from `TSL-RF-118` — which is what the v2 rows below
  // showed, byte for byte, and no longer do.
  assert.deepEqual(analyze("QCL-IT-ADR-08"), ["qcl-it-adr-08", "qcl", "adr", "08"]);
  assert.deepEqual(analyze("TSL-RF-118-A"), ["tsl-rf-118-a", "tsl", "rf", "118"]);
  assert.deepEqual(analyze("TSL-RF-221-A"), ["tsl-rf-221-a", "tsl", "rf", "221"]);
});
