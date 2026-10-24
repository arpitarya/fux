/** W-295 -- a policy file at the pre-move address stops the Node reader too, in
 *  Python's words, and BEFORE the PII gate: an un-migrated repo is not a repo
 *  with no redaction policy. `node/fux.mjs` is run as a process, as a consumer does. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const FUX = fileURLToPath(new URL("../fux.mjs", import.meta.url));

function run(root, ...args) {
  return spawnSync(process.execPath, [FUX, ...args], { cwd: root, encoding: "utf8" });
}

function repo() {
  const root = mkdtempSync(join(tmpdir(), "fux-moved-"));
  writeFileSync(join(root, "fux.toml"), "");
  mkdirSync(join(root, ".fux"));
  return root;
}

test("the PII hard stop says the file moved, not that it is missing", () => {
  const root = repo();
  writeFileSync(join(root, ".fux", "pii.toml"), "");
  const r = run(root, "find", "anything");
  assert.equal(r.status, 1);
  assert.match(r.stderr, /`\.fux\/pii\.toml` moved to `\.fux\/config\/pii\.toml`/);
  assert.match(r.stderr, /run `fux setup`/);
  assert.doesNotMatch(r.stderr, /missing/);
});

test("every file at the old address is named", () => {
  const root = repo();
  for (const name of ["tune", "output"]) writeFileSync(join(root, ".fux", `${name}.toml`), "");
  const r = run(root, "ask", "anything");
  assert.equal(r.status, 1);
  assert.match(r.stderr, /`\.fux\/output\.toml` moved to `\.fux\/config\/output\.toml`, `\.fux\/tune\.toml` moved to `\.fux\/config\/tune\.toml`/);
});

test("with the file at the new address the gate is the PII gate again", () => {
  const root = repo();
  const r = run(root, "find", "anything");
  assert.equal(r.status, 1);
  assert.match(r.stderr, /\.fux\/config\/pii\.toml is missing/);
});
