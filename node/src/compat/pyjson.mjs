/** CPython's `json.dumps`, for the bytes the derived plane is made of.
 *
 * W-242 Tier 2: a Node-built `.fux/runtime/` must equal a Python-built one byte
 * for byte, and `JSON.stringify` differs from `json.dumps` in three ways that
 * matter here:
 *
 * - **key order** — `sort_keys=True` orders by CODE POINT. A JS object keeps
 *   insertion order, except that integer-like keys jump to the front;
 * - **`ensure_ascii=True`** (`graph/plane.py` keeps Python's default) escapes
 *   every character outside `' '..'~'` as `\uXXXX`, astral ones as a surrogate
 *   pair, lowercase hex; `JSON.stringify` writes them raw;
 * - **integers past 2^53** — a stamp's `mtime_ns`. Pass a `BigInt`.
 *
 * Floats are refused rather than guessed at: nothing the plane writes is a
 * float, and a float written by the wrong `repr` would be one byte that a
 * differential arm reads as a disagreement about the engine.
 *
 * Exempt from the twin map (`tests/test_node_twins.py`): CPython's `json`
 * module IS the twin, and it is stdlib.
 */
import { cmpCodePoints } from "./pyfloat.mjs";

//: The one escape set both modes share: quote, backslash and the C0 controls.
const SHORT = new Map([["\"", "\\\""], ["\\", "\\\\"], ["\n", "\\n"], ["\r", "\\r"], ["\t", "\\t"], ["\b", "\\b"], ["\f", "\\f"]]);
const PRINTABLE_LO = " ".codePointAt(0);
const PRINTABLE_HI = "~".codePointAt(0);
const HEX = 16;
const UNIT_WIDTH = 4;

function u(code) { return "\\u" + code.toString(HEX).padStart(UNIT_WIDTH, "0"); }

function encodeString(s, ensureAscii) {
  let out = "\"";
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    const short = SHORT.get(ch);
    if (short !== undefined) { out += short; continue; }
    const code = s.charCodeAt(i);
    if (code < PRINTABLE_LO) { out += u(code); continue; }
    // `ensure_ascii` escapes everything past `~`, one UTF-16 unit at a time —
    // which is exactly Python's surrogate-pair output for an astral character.
    if (ensureAscii && code > PRINTABLE_HI) { out += u(code); continue; }
    out += ch;
  }
  return out + "\"";
}

/** `json.dumps(value, separators=(",", ":"), sort_keys=sortKeys, ensure_ascii=ensureAscii)`.
 *  A `Map` keeps its own order (for `sort_keys=False` payloads built in order). */
export function pyDumps(value, { sortKeys, ensureAscii }) {
  const enc = (v) => {
    if (v === null || v === undefined) return "null";
    if (v === true) return "true";
    if (v === false) return "false";
    if (typeof v === "bigint") return v.toString();
    if (typeof v === "number") {
      if (!Number.isSafeInteger(v)) throw new TypeError(`pyDumps writes integers only, got ${v}`);
      return String(v);
    }
    if (typeof v === "string") return encodeString(v, ensureAscii);
    if (Array.isArray(v)) return "[" + v.map(enc).join(",") + "]";
    const entries = v instanceof Map ? [...v.entries()] : Object.entries(v);
    if (sortKeys) entries.sort(([a], [b]) => cmpCodePoints(a, b));
    return "{" + entries.map(([k, x]) => encodeString(String(k), ensureAscii) + ":" + enc(x)).join(",") + "}";
  };
  return enc(value);
}
