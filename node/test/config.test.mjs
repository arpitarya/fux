/** The config readers — `.fux/tune.toml`, `.fux/output.toml`, `.fux/sources/dirs`.
 *  Run with `node --test` from `node/`.
 *
 * **These run with no Python at all**, which is the point: the differential arm
 * answers *"do the two readers agree on this corpus?"*, and it cannot answer
 * *"does this reader refuse the file Python refuses?"* on a corpus where no
 * such file exists. Every refusal below is a case the arm structurally cannot
 * reach, because a repository carrying it never gets as far as a query.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { parseToml, wasFloat } from "../src/config/toml.mjs";
import { loadTune, DEFAULT_TUNE } from "../src/config/tune.mjs";
import { loadOutput, BUILT_IN } from "../src/config/output.mjs";
import { parseDirs } from "../src/ingest/sourcelist.mjs";
import { globMatch, isAlreadyText, PROSE_TYPES } from "../src/decode/registry.mjs";
import { FuxError } from "../src/errors.mjs";

/** A throwaway repo root with the given `.fux/` files. */
function repo(files) {
  const root = mkdtempSync(join(tmpdir(), "fux-node-"));
  mkdirSync(join(root, ".fux", "sources"), { recursive: true });
  for (const [rel, body] of Object.entries(files)) {
    const path = join(root, rel);
    mkdirSync(join(path, ".."), { recursive: true });
    writeFileSync(path, body);
  }
  return root;
}

// -- the TOML subset ---------------------------------------------------------

test("TOML: tables, dotted keys, arrays, inline tables, every string form", () => {
  const d = parseToml(`
# a comment
bare = 1
[a]
b.c = "x"
list = [1, 2, [3]]
inline = { k = "v" }
lit = 'raw \\n not an escape'
multi = """
one
two"""
`, "<t>");
  assert.equal(d.bare, 1);
  assert.equal(d.a.b.c, "x");
  assert.deepEqual(d.a.list, [1, 2, [3]]);
  assert.equal(d.a.inline.k, "v");
  assert.equal(d.a.lit, "raw \\n not an escape");
  assert.equal(d.a.multi, "one\ntwo");
});

test("TOML: integer-ness survives, because `tune.py` refuses a float where it wants an int", () => {
  const d = parseToml("[g]\nint = 3\nfloat = 3.0\nexp = 1e2\n", "<t>");
  assert.equal(d.g.int, 3);
  assert.equal(d.g.float, 3);           // the same double...
  assert.equal(wasFloat(d.g, "int"), false);
  assert.equal(wasFloat(d.g, "float"), true);   // ...and NOT the same TOML value
  assert.equal(wasFloat(d.g, "exp"), true);
});

test("TOML: a date is refused BY NAME, not mis-parsed as a subtraction", () => {
  assert.throws(() => parseToml("d = 2026-09-12\n", "<t>"), /dates and times are not a fux value/);
});

test("TOML: the float-keys record is invisible to every consumer", () => {
  const d = parseToml("[a]\nx = 1.5\n", "<t>");
  assert.deepEqual(Object.keys(d.a), ["x"]);
  assert.equal(JSON.stringify(d.a), '{"x":1.5}');
});

// -- tune --------------------------------------------------------------------

test("tune: an absent file is every default, and --no-tune never reads one", () => {
  const root = repo({});
  assert.equal(loadTune(root).rerankWeight, DEFAULT_TUNE.rerankWeight);
  const tuned = repo({ ".fux/tune.toml": "[ranking]\nrerank_weight = 0.3\n" });
  assert.equal(loadTune(tuned).rerankWeight, 0.3);
  assert.equal(loadTune(tuned, { enabled: false }).rerankWeight, 0.0);
  rmSync(root, { recursive: true, force: true });
  rmSync(tuned, { recursive: true, force: true });
});

test("tune: an unknown table and an unknown key are REFUSALS, not shrugs", () => {
  const a = repo({ ".fux/tune.toml": "[nope]\nx = 1\n" });
  assert.throws(() => loadTune(a), /unknown table/);
  const b = repo({ ".fux/tune.toml": "[ranking]\nrerank_weightt = 0.3\n" });
  assert.throws(() => loadTune(b), /unknown key/);
});

test("tune: the alpha.1 field spelling names its replacement", () => {
  const root = repo({ ".fux/tune.toml": "[bm25f]\nheading_weight = 3.0\n" });
  assert.throws(() => loadTune(root), /lost the `_weight` suffix/);
});

test("tune: [dense] names what happened to it", () => {
  const root = repo({ ".fux/tune.toml": "[dense]\nmode = \"on\"\n" });
  assert.throws(() => loadTune(root), /REMOVED on 2026-08-25/);
});

test("tune: a REMOVED key is named as removed, not reported as unknown", () => {
  // All three document priors went on 2026-09-13 (W-151, W-152), and `fux
  // setup` had written every one of them into the consumer's file.
  for (const key of ["superseded_weight", "archived_weight", "recency_half_life_days"]) {
    const root = repo({ ".fux/tune.toml": `[ranking]\n${key} = 0.5\n` });
    assert.throws(() => loadTune(root), /REMOVED on 2026-09-13/, key);
  }
});

test("tune: a whole-number key refuses a float, exactly as tune.py does", () => {
  const root = repo({ ".fux/tune.toml": "[graph]\niterations = 3.0\n" });
  assert.throws(() => loadTune(root), /must be a whole number/);
});

test("tune: semantic errors are COLLECTED, not reported one at a time", () => {
  const root = repo({
    ".fux/tune.toml": "[ranking]\nrerank_weight = -1\nexpand_weight = -2\n",
  });
  try {
    loadTune(root);
    assert.fail("expected a refusal");
  } catch (err) {
    assert.ok(err instanceof FuxError);
    assert.match(err.message, /rerank_weight/);
    assert.match(err.message, /expand_weight/);
  }
});

test("tune: an unresolved merge conflict is named, not reported as bad TOML", () => {
  const root = repo({ ".fux/tune.toml": "<<<<<<< HEAD\n[ranking]\n=======\n>>>>>>> x\n" });
  assert.throws(() => loadTune(root), /unresolved merge conflict/);
});

test("tune: [priority] is sorted longest-key-first so the first match wins", () => {
  const root = repo({
    ".fux/tune.toml": '[priority]\n"docs" = 1.5\n"docs/adr" = 2.0\n',
  });
  assert.deepEqual(loadTune(root).priority, [["docs/adr", 2.0], ["docs", 1.5]]);
});

// -- output ------------------------------------------------------------------

test("output: an ABSENT file resolves to the built-ins and is not an error", () => {
  const root = repo({});
  const cfg = loadOutput(root);
  assert.equal(cfg.absent, true);
  assert.equal(cfg.resolve("find", "top"), BUILT_IN.top);
});

test("output: a PRESENT file that omits a key REFUSES — it is the sole source", () => {
  const root = repo({ ".fux/output.toml": "[cli]\nband = false\n" });
  const cfg = loadOutput(root);
  assert.equal(cfg.resolve("find", "band"), false);
  assert.throws(() => cfg.resolve("find", "top"), /does not set `top`/);
});

test("output: the precedence chain is flag -> json.verb -> json -> verb -> cli", () => {
  const root = repo({
    ".fux/output.toml":
      "[cli]\nband = false\ntop = 5\n[cli.find]\ntop = 7\n[cli.json]\nenabled = false\ntop = 9\n",
  });
  const cfg = loadOutput(root);
  assert.equal(cfg.resolve("find", "top"), 7);                      // per-verb
  assert.equal(cfg.resolve("find", "top", null, { asJson: true }), 9);  // json wins
  assert.equal(cfg.resolve("find", "top", 3), 3);                   // a flag wins
});

test("output: a verb-only key is refused at the SHARED level, by name", () => {
  const root = repo({ ".fux/output.toml": "[cli]\nhops = 3\n" });
  assert.throws(() => loadOutput(root), /belongs to one verb only \(path\)/);
});

test("output: `[mcp]` inherits nothing from `[cli]`", () => {
  const root = repo({ ".fux/output.toml": "[cli]\ntop = 9\n[mcp]\ntop = 3\n" });
  assert.equal(loadOutput(root).resolveMcp("top"), 3);
});

test("output: `[mcp] band` is refused by name, with the reason", () => {
  const root = repo({ ".fux/output.toml": "[mcp]\nband = true\n" });
  assert.throws(() => loadOutput(root), /UNCONDITIONAL, by name/);
});

test("output: `top = true` is refused — a bool is not a whole number", () => {
  const root = repo({ ".fux/output.toml": "[cli]\ntop = true\n" });
  assert.throws(() => loadOutput(root), /must be a whole number/);
});

// -- the dirs list -----------------------------------------------------------

test("dirs: `#` starts a comment only at line start or after whitespace", () => {
  const entries = parseDirs("docs\nwork#notacomment\na # yes\n", "<d>");
  assert.deepEqual(entries.map((e) => e.value), ["a", "docs", "work#notacomment"]);
});

test("dirs: archived=true is the declaration, and `!` subtracts", () => {
  const entries = parseDirs("archive archived=true\ndocs\n!docs/x\n", "<d>");
  const archived = entries.filter((e) => !e.exclude && e.attrs.archived === "true");
  assert.deepEqual(archived.map((e) => e.value), ["archive"]);
  assert.equal(entries[entries.length - 1].exclude, true);   // exclusions sort last
});

test("dirs: an unknown attribute, `!!`, and an exclusion with attributes all refuse", () => {
  assert.throws(() => parseDirs("docs mata=plain\n", "<d>"), /unknown attribute/);
  assert.throws(() => parseDirs("!!docs\n", "<d>"), /not an un-exclude/);
  assert.throws(() => parseDirs("!docs archived=true\n", "<d>"), /carries no attributes/);
});

test("dirs: a duplicate that DISAGREES names both lines", () => {
  assert.throws(
    () => parseDirs("docs archived=true\ndocs archived=false\n", "<d>"),
    /appears twice with conflicting attributes/,
  );
});

// -- the decode boundary -----------------------------------------------------

test("decode: `*` does not cross a `/`, and a pattern with no `/` matches the basename", () => {
  assert.equal(globMatch("*.md", "a/b/c.md"), true);
  assert.equal(globMatch("docs/*/x.md", "docs/a/x.md"), true);
  assert.equal(globMatch("docs/*/x.md", "docs/a/b/x.md"), false);
  assert.equal(globMatch("docs/**/x.md", "docs/a/b/x.md"), true);
});

test("decode: prose is referable and a decoded type is NOT", () => {
  const root = repo({});   // no formats.toml -> the built-in default
  assert.equal(isAlreadyText(root, "docs/a.md"), true);
  assert.equal(isAlreadyText(root, "docs/a.rst"), true);
  // 🔴 The whole reason this module exists: Node has no decoder for these, so
  // chunking their raw bytes would cite line numbers into text the index never
  // held.
  assert.equal(isAlreadyText(root, "data/a.csv"), false);
  assert.equal(isAlreadyText(root, "data/a.xlsx"), false);
  assert.equal(isAlreadyText(root, "data/a.pdf"), false);
});

test("decode: `.fux/formats.toml` REPLACES the default when it is there", () => {
  const root = repo({ ".fux/formats.toml": 'include = ["*.txt"]\n[decoders]\n".csv" = "csv"\n' });
  assert.equal(isAlreadyText(root, "a.txt"), true);
  assert.equal(isAlreadyText(root, "a.md"), false);   // not declared -> not prose here
  assert.deepEqual(PROSE_TYPES.includes("*.md"), true);
});
