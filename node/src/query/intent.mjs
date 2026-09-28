/**
 * W-168 step 9 — a question's intent, and the document type it prefers. Twin
 * of `src/fux/query/intent.py`; the reasons live there and are not repeated.
 *
 * 🔴 The three parity rules, mirrored: ASCII-only case folding and whitespace
 * collapsing; the `s` flag so `.` matches every character, as Python's
 * `re.DOTALL`; JavaScript's `\b` is already ASCII, as Python's `re.ASCII`.
 * Globs are matched by hand over CODE POINTS (`Array.from`), never UTF-16
 * units, so `?` is one character in both readers.
 */

import { fixed, table } from "../config/constants.mjs";

let lexicon = null;

function getLexicon() {
  if (lexicon === null) {
    lexicon = fixed("intent", "order").map((name) => [
      name, fixed("intent", name).map((p) => new RegExp(p, "s")),
    ]);
  }
  return lexicon;
}

/** The types a `[doctype]` entry may declare. */
export function intentTypes() {
  return new Set(Object.values(table("intent.type")));
}

/** ASCII whitespace collapsed to one space and trimmed; ASCII letters lowercased. */
export function prepare(question) {
  return question
    .replace(/[ \t\n\r\f\v]+/g, " ")
    .replace(/^ +| +$/g, "")
    .replace(/[A-Z]/g, (ch) => String.fromCharCode(ch.charCodeAt(0) + 32));
}

/** The first intent in `[intent] order` with a matching cue, or `null`. */
export function intentOf(question) {
  const q = prepare(question);
  for (const [name, patterns] of getLexicon()) {
    if (patterns.some((p) => p.test(q))) return name;
  }
  return null;
}

/** The document type an intent prefers. */
export function typeOfIntent(intent) {
  return table("intent.type")[intent];
}

/** Whole-string wildcard match: `*` any run (including `/`), `?` one character. */
export function globMatch(patternStr, textStr) {
  const pattern = Array.from(patternStr);
  const text = Array.from(textStr);
  let p = 0, t = 0, star = -1, mark = 0;
  while (t < text.length) {
    if (p < pattern.length && (pattern[p] === "?" || (pattern[p] !== "*" && pattern[p] === text[t]))) {
      p += 1; t += 1;
    } else if (p < pattern.length && pattern[p] === "*") {
      star = p; mark = t; p += 1;
    } else if (star >= 0) {
      p = star + 1; mark += 1; t = mark;
    } else {
      return false;
    }
  }
  while (p < pattern.length && pattern[p] === "*") p += 1;
  return p === pattern.length;
}

/** The declared type of a location. `doctype` is sorted longest-first by the loader. */
export function typeFor(loc, doctype) {
  for (const [pattern, kind] of doctype) {
    if (globMatch(pattern, loc)) return kind;
  }
  return null;
}
