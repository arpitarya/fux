/** The fux YAML subset, read. Twin of `src/fux/acquire/yamlsubset.py`.
 *
 * **Owned by [SR-SOURCES](../../../records/0116_sources.md)** (W-294). L2 rules
 * out a YAML package on either plane, so this is hand-rolled, as
 * `config/toml.mjs` is. `tests/test_sources_yaml_differential.py` feeds this
 * reader and the Python one the same fixtures and requires the same tree, or
 * the same refusal in the same words.
 *
 * - **Read:** block maps, block lists, plain / single-quoted / double-quoted
 *   scalars, and `#` comments at a line's start or after a space.
 * - **Refused, `file:line`:** flow `{}` / `[]`, anchors, aliases, tags,
 *   `---` / `...`, `%` directives, block scalars, a `?` complex key, tab
 *   indentation, a duplicate key, and a plain value holding `: `.
 *
 * 🔴 **Typing is the schema's.** Every scalar is TEXT; nothing here turns `no`
 * or `010` into a boolean or a number. The refusal texts are
 * `constants.toml [yaml_subset]`, the table the Python reader formats.
 */
import { FuxError } from "../errors.mjs";
import { table } from "../config/constants.mjs";

const TEXTS = table("yaml_subset");

//: The c-indicators that cannot start a plain scalar, each with its refusal.
const START = {
  "{": "flow", "}": "flow", "[": "flow", "]": "flow",
  "&": "anchor", "*": "alias", "!": "tag",
  "|": "block", ">": "block",
  "@": "reserved", "`": "reserved", ",": "reserved", "%": "reserved",
};

const SPACE = " ";
const COMMENT = "#";
const ITEM = "- ";
const COLON = ":";
const ESCAPES = ["\\", "\"", "/"];
const DOC_MARKERS = ["---", "..."];

/** Python's `str.format` for the `{name}` fields these texts use. */
function format(text, fill) {
  return text.replace(/\{(\w+)\}/g, (_m, name) => String(fill[name]));
}

/** `origin:line: <text>` — the one shape every refusal takes, both planes. */
export function message(name, origin, line, fill = {}) {
  return `${origin}:${line}: ` + format(TEXTS[name], fill);
}

function fail(name, origin, line, fill = {}) {
  return new FuxError(message(name, origin, line, fill));
}

function isItem(content) {
  return content === ITEM.trim() || content.startsWith(ITEM);
}

function stripPlainComment(text) {
  if (text.startsWith(COMMENT)) return "";
  for (let i = 1; i < text.length; i++) {
    if (text[i] === COMMENT && text[i - 1] === SPACE) return text.slice(0, i);
  }
  return text;
}

function lstripChars(text, chars) {
  let i = 0;
  while (i < text.length && chars.includes(text[i])) i++;
  return text.slice(i);
}

function rstripChars(text, chars) {
  let i = text.length;
  while (i > 0 && chars.includes(text[i - 1])) i--;
  return text.slice(0, i);
}

function splitLines(text, origin) {
  const out = [];
  const raws = text.split("\n");
  for (let idx = 0; idx < raws.length; idx++) {
    const no = idx + 1;
    let raw = raws[idx];
    if (raw.endsWith("\r")) raw = raw.slice(0, -1);
    const stripped = lstripChars(raw, " \t");
    if (!stripped || stripped.startsWith(COMMENT)) continue;
    const lead = raw.slice(0, raw.length - stripped.length);
    if (lead.includes("\t")) throw fail("tab", origin, no);
    const indent = lead.length;
    if (indent === 0) {
      for (const marker of DOC_MARKERS) {
        if (stripped === marker || stripped.startsWith(marker + SPACE)) {
          throw fail("document", origin, no, { token: marker });
        }
      }
      if (stripped.startsWith("%")) throw fail("directive", origin, no);
    }
    out.push({ no, indent, content: stripped });
  }
  return out;
}

function keySplit(content) {
  if (content[0] === "'" || content[0] === "\"") return null;
  const body = rstripChars(stripPlainComment(content), " \t\n\r\f\v");
  for (let i = 0; i < body.length; i++) {
    if (body[i] === COLON && (i + 1 === body.length || body[i + 1] === SPACE)) {
      return [rstripChars(body.slice(0, i), " \t\n\r\f\v"), i + 1];
    }
  }
  return null;
}

function checkKey(key, origin, line) {
  if (!key) throw fail("key", origin, line, { token: ":" });
  if (key.startsWith("? ") || key === "?") throw fail("complex_key", origin, line);
  const first = key[0];
  if (Object.hasOwn(START, first)) throw fail(START[first], origin, line, { token: first });
}

function quoted(text, quote, origin, line) {
  const out = [];
  let i = 1;
  while (i < text.length) {
    const ch = text[i];
    if (quote === "'") {
      if (ch === "'") {
        if (text[i + 1] === "'") { out.push("'"); i += 2; continue; }
        return [out.join(""), i + 1];
      }
    } else {
      if (ch === "\\") {
        const nxt = text.slice(i + 1, i + 2);
        if (!ESCAPES.includes(nxt)) throw fail("escape", origin, line, { token: "\\" + nxt });
        out.push(nxt);
        i += 2;
        continue;
      }
      if (ch === "\"") return [out.join(""), i + 1];
    }
    out.push(ch);
    i += 1;
  }
  throw fail("unclosed", origin, line);
}

function scalar(content, line, offset, origin) {
  const col = line.indent + offset;
  const text = content.slice(offset);
  const first = text.slice(0, 1);
  if (first === "\"" || first === "'") {
    const [value, used] = quoted(text, first, origin, line.no);
    const rest = text.slice(used);
    const tail = lstripChars(rest, SPACE);
    if (tail && !(tail.startsWith(COMMENT) && tail.length < rest.length)) {
      throw fail("after_quote", origin, line.no);
    }
    return { kind: "scalar", text: value, line: line.no, col, end: col + used, quoted: true, last: line.no };
  }
  if (Object.hasOwn(START, first)) throw fail(START[first], origin, line.no, { token: first });
  if (text.startsWith(ITEM) || text === ITEM.trim()) {
    throw fail("reserved", origin, line.no, { token: ITEM.trim() });
  }
  if (text.startsWith("? ")) throw fail("complex_key", origin, line.no);
  const value = rstripChars(stripPlainComment(text), SPACE);
  if (value.includes(COLON + SPACE) || value.endsWith(COLON)) throw fail("colon_space", origin, line.no);
  return { kind: "scalar", text: value, line: line.no, col, end: col + value.length, quoted: false, last: line.no };
}

class Parser {
  constructor(lines, origin) {
    this.lines = lines;
    this.origin = origin;
    this.i = 0;
  }

  peek() {
    return this.i < this.lines.length ? this.lines[this.i] : null;
  }

  block(indent) {
    const line = this.peek();
    if (isItem(line.content)) return this.seq(indent, false);
    return this.map(indent, null);
  }

  nested(indent, allowCompact) {
    this.i += 1;
    const nxt = this.peek();
    if (nxt !== null && nxt.indent > indent) return this.block(nxt.indent);
    if (allowCompact && nxt !== null && nxt.indent === indent && isItem(nxt.content)) {
      return this.seq(indent, true);
    }
    return null;
  }

  expectNoDeeper(indent) {
    const nxt = this.peek();
    if (nxt !== null && nxt.indent > indent) throw fail("indent", this.origin, nxt.no);
  }

  seq(indent, compact) {
    const items = [];
    const start = this.peek().no;
    let last = start;
    let line;
    while ((line = this.peek()) !== null && line.indent === indent) {
      if (!isItem(line.content)) {
        if (compact) break;
        throw fail("mixed", this.origin, line.no);
      }
      const restAt = line.content.length - lstripChars(line.content.slice(1), SPACE).length;
      const rest = line.content.slice(restAt);
      let child;
      if (!stripPlainComment(rest).trim()) {
        child = this.nested(indent, false);
        if (child === null) throw fail("empty_item", this.origin, line.no);
      } else if (keySplit(rest) !== null) {
        child = this.map(line.indent + restAt, { no: line.no, indent: line.indent + restAt, content: rest });
      } else {
        child = scalar(rest, { no: line.no, indent: line.indent + restAt, content: rest }, 0, this.origin);
        this.i += 1;
        this.expectNoDeeper(indent);
      }
      items.push(child);
      last = child.last;
    }
    return { kind: "seq", items, line: start, last };
  }

  map(indent, first) {
    const pairs = new Map();
    let line = first !== null ? first : this.peek();
    const start = line.no;
    let last = start;
    for (;;) {
      const content = line.content;
      if (isItem(content)) throw fail("mixed", this.origin, line.no);
      const split = keySplit(content);
      if (split === null) {
        throw fail("key", this.origin, line.no, { token: stripPlainComment(content).trim() });
      }
      const [key, after] = split;
      checkKey(key, this.origin, line.no);
      if (pairs.has(key)) {
        throw fail("duplicate", this.origin, line.no, { key, first: pairs.get(key).line });
      }
      const rest = content.slice(after);
      const offset = after + (rest.length - lstripChars(rest, SPACE).length);
      let value;
      if (!stripPlainComment(content.slice(offset)).trim()) {
        value = this.nested(indent, true);
        if (value === null) value = { kind: "null", line: line.no, last: line.no };
      } else {
        value = scalar(content, line, offset, this.origin);
        this.i += 1;
        this.expectNoDeeper(indent);
      }
      pairs.set(key, { key, line: line.no, value });
      last = value.last;
      const nxt = this.peek();
      if (nxt === null || nxt.indent !== indent) break;
      line = nxt;
    }
    return { kind: "map", pairs, line: start, last };
  }
}

/** The document's root node — `{kind: "map"|"seq"|"scalar", ...}` — or `null`
 *  when the file holds nothing but comments and blank lines. */
export function parseYamlSubset(text, origin) {
  const lines = splitLines(text, origin);
  if (!lines.length) return null;
  const parser = new Parser(lines, origin);
  const root = parser.block(lines[0].indent);
  const leftover = parser.peek();
  if (leftover !== null) {
    throw fail(leftover.indent < lines[0].indent ? "dedent" : "indent", origin, leftover.no);
  }
  return root;
}
