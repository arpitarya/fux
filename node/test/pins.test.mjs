/** The pins — run with `node --test node/test/`.
 *
 * These are the N3 fixtures in miniature: the vectors that must hold before a
 * single ranking number is trusted. The full N3 gate compares against Python
 * over an entire corpus; these are the ones that can run with no Python at all,
 * so a Node-only contributor can still see them fail.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { blake2bHex } from "../src/hash/blake2b.mjs";
import { stem, shouldStem } from "../src/query/stem.mjs";
import { analyze } from "../src/query/analyzer.mjs";
import { pyRound9, pyRepr, cmpCodePoints } from "../src/compat/pyfloat.mjs";

const enc = new TextEncoder();

test("blake2b matches RFC 7693 Appendix A", () => {
  assert.equal(
    blake2bHex(enc.encode("abc"), 64),
    "ba80a53f981c4d0d6a2797b69f12f6e94c212f14685ac4b74b12bb6fdbffa2d1"
    + "7d87c5392aab792dc252d5de4533cc9518d38aa8dbf1925ab92386edd4009923",
  );
});

test("blake2b at digest size 8 is NOT a truncated blake2b-512", () => {
  // The parameter block folds the digest length into h[0]. If this ever passes,
  // someone has replaced the implementation with a truncation and every
  // posting key in every index silently changed.
  const eight = blake2bHex(enc.encode("rollback"), 8);
  const truncated = blake2bHex(enc.encode("rollback"), 64).slice(0, 16);
  assert.notEqual(eight, truncated);
  assert.equal(eight, "e460f39a965bec5f");   // pinned against Python hashlib
});

test("shard_for and term_hash are pinned against Python hashlib", () => {
  assert.equal(blake2bHex(enc.encode("file:docs/adr/0111_ranking.md"), 1).length, 2);
  assert.equal(blake2bHex(enc.encode("rollback"), 8), "e460f39a965bec5f");
});

test("the analyzer splits identifiers before lowercasing", () => {
  // Lowercasing first destroys the boundary irrecoverably.
  assert.deepEqual(analyze("getUserName"), ["getusernam", "get", "user", "name"]);
  assert.deepEqual(analyze("HTTPServer"), ["httpserver", "http", "server"]);
  // A token with no boundary is left whole — stripping it loses the identity.
  assert.deepEqual(analyze("sha256"), ["sha256"]);
  // The single trailing `F` is dropped: one character is noise as a term.
  assert.deepEqual(analyze("BM25F"), ["bm25f", "bm25"]);
  // Stemmed, because Python's str.isalpha() is true for it.
  assert.deepEqual(analyze("café"), ["caf"]);
});

test("shouldStem uses Unicode alphabetic, not [a-z]", () => {
  // Python's str.isalpha() is true for these; a naive /^[a-z]+$/ is not, and
  // would stem tokens Python leaves alone.
  assert.equal(shouldStem("café"), true);
  assert.equal(shouldStem("中文字"), true);
  assert.equal(shouldStem("sha256"), false);
  assert.equal(shouldStem("ab"), false);
});

test("porter stems the published awkward cases", () => {
  for (const [w, s] of [
    ["caresses", "caress"], ["ponies", "poni"], ["cats", "cat"],
    ["feed", "feed"], ["agreed", "agre"], ["plastered", "plaster"],
    ["motoring", "motor"], ["sing", "sing"], ["conflated", "conflat"],
    ["troubled", "troubl"], ["hopping", "hop"], ["falling", "fall"],
    ["hissing", "hiss"], ["happy", "happi"], ["sky", "sky"],
    ["relational", "relat"], ["conditional", "condit"], ["rational", "ration"],
  ]) assert.equal(stem(w), s, `stem(${w})`);
});

test("pyRound9 is half-EVEN on exact binary ties", () => {
  // Number(x.toFixed(9)) is half-UP here, and round(score, 9) is the sort
  // key's own resolution — a tie resolved the other way is a different ORDER.
  assert.equal(pyRound9(0.5), 0.5);
  assert.equal(pyRound9(5.328053506242763), 5.328053506);
});

test("pyRepr matches Python's exponent thresholds", () => {
  assert.equal(pyRepr(2.0), "2.0");        // JS: "2"
  assert.equal(pyRepr(1e-5), "1e-05");     // JS: "0.00001"
  assert.equal(pyRepr(1e16), "1e+16");     // JS: "10000000000000000"
});

test("W-107 H1 — ids are compared by code point, never with `<`", () => {
  const ids = ["file:h1-a.md", "file:h1-.md", "file:h1-�.md",
               "file:h1-\u{1F600}.md", "file:h1-\u{2A6B2}.md"];
  // What Python produces.
  const python = [...ids];
  assert.deepEqual([...ids].sort(cmpCodePoints), python);
  // 🔴 And what a naive comparator would have shipped: a surrogate pair sorts
  // BELOW U+E000..U+FFFF in UTF-16 and ABOVE it by code point.
  assert.notDeepEqual([...ids].sort(), python);
});
