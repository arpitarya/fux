/** Passages, derived from the document's own heading DEPTH.
 *  Twin of `src/fux/refer/_chunk.py`.
 *
 * **There is no strategy parameter and no CHUNK to declare.** What a passage
 * is — a table row, a slide, a prose section, the whole file — falls out of
 * heading depth, so a caller cannot get it wrong because there is nothing to
 * get wrong.
 *
 * Deterministic and TOTAL: every byte lands in exactly one passage, with one
 * documented exception — a banded table repeats its header into every band,
 * because a row whose columns have no names is a citation nobody can read.
 *
 * ⚠ **Transient. Never written.** L2: chunks are re-derived from fetched bytes
 * at answer time and stored nowhere.
 *
 * Owned, with its Python twin, by [SR-CHUNKING](../../../records/0151_chunking.md).
 */
import { headings } from "../decode/markdown.mjs";

export const MIN_PASSAGE_BYTES = 120;
export const MAX_PASSAGE_BYTES = 4000;
/** Measured 2026-09-06: row-per-passage took hit@1 from 0.229 to 0.875. */
export const TABLE_ROWS_PER_PASSAGE = 1;

const TABLE_ROW_RE = /^\s*\|/;
const TABLE_SEP_RE = /^\s*\|[\s:|-]+\|?\s*$/;

const enc = new TextEncoder();
const nbytes = (s) => enc.encode(s).length;
const countNl = (s) => { let n = 0; for (let i = 0; i < s.length; i++) if (s[i] === "\n") n++; return n; };

/** `[heading, level, text, lineStart, lineEnd]`, 1-based and inclusive.
 *  Line numbers are tracked HERE rather than recovered later, because the text
 *  is stripped and the offset would be gone with the blank lines. */
function sections(content) {
  // `split("\n")`, never a line-splitter that also breaks on \r \v \f U+2028:
  // the heading grammar splits the same way, so its line numbers index this
  // list exactly, and any other splitter desynchronises the two.
  const lines = content.split("\n");
  const starts = new Map();
  for (const h of headings(content)) starts.set(h.lineno, h);

  // Level 0 is the preamble — not a heading of level 0, the ABSENCE of one,
  // which is right because nothing can be nested inside it.
  const acc = [["", 0, [], 1]];
  for (let i = 0; i < lines.length; i++) {
    const found = starts.get(i + 1);
    if (found !== undefined) acc.push([found.text, found.level, [lines[i]], i + 1]);
    else acc[acc.length - 1][2].push(lines[i]);
  }

  const out = [];
  for (const [heading, level, ls, start] of acc) {
    const joined = ls.join("\n");
    if (!joined.trim()) continue;
    const leading = ls.length - joined.replace(/^\n+/, "").split("\n").length;
    const text = joined.replace(/^\n+/, "").replace(/\n+$/, "");
    const realStart = start + Math.max(0, leading);
    out.push([heading, level, text, realStart, realStart + countNl(text)]);
  }
  return out;
}

/** Index of the document TITLE section, or -1. Three structural conditions:
 *  first headed section, strictly shallower than every other, and NO BODY of
 *  its own. The third does the work — `# deck.pptx` above a run of slides is a
 *  name for the file; `## Notes` above `### Detail` is a real section. */
function titleIndex(secs) {
  const headed = [];
  for (let i = 0; i < secs.length; i++) if (secs[i][0]) headed.push(i);
  if (headed.length < 2) return -1;
  const first = headed[0];
  const [, level, text] = secs[first];
  if (text.trim() !== text.trim().split("\n")[0].trim()) return -1;  // has a body
  return headed.slice(1).every((i) => secs[i][1] > level) ? first : -1;
}

/** Fold a short section forward **only into a section NESTED INSIDE it**.
 *
 * 🔴 Depth, not size. The old rule folded on size alone, so a short slide
 * between two long ones was cited under its NEIGHBOUR's heading —
 * systematically the wrong attribution, which is worse than a coarse citation
 * because it is confidently wrong. Siblings never fold, so a lone short
 * sibling cannot be absorbed.
 *
 * ⚠ The PARENT's heading survives the fold, with one exception: the document
 * TITLE carries its text but never its name, or `# deck.pptx` ends up cited as
 * the source of slide 1's content. */
function fold(secs, minPassageBytes = MIN_PASSAGE_BYTES) {
  const out = [];
  let carry = [], carryHeading = "", carryLevel = 0, carryStart = 0;
  const title = titleIndex(secs);
  for (let index = 0; index < secs.length; index++) {
    const [heading, level, text, start, end] = secs[index];
    const nxt = index + 1 < secs.length ? secs[index + 1] : null;
    const short = nbytes(text) < minPassageBytes;
    // Strictly deeper: `>` and never `>=` — `>=` is the sibling case, and the
    // sibling case is the defect.
    const nested = nxt !== null && nxt[1] > level;
    if (short && nested) {
      if (!carry.length) carryStart = start;
      if (!carryHeading && index !== title) { carryHeading = heading; carryLevel = level; }
      carry.push(text);
      continue;
    }
    if (carry.length) {
      out.push([carryHeading || heading, carryLevel || level,
                [...carry, text].join("\n\n"), carryStart, end]);
      carry = []; carryHeading = ""; carryLevel = 0;
    } else {
      out.push([heading, level, text, start, end]);
    }
  }
  if (carry.length) {
    // Unreachable — a section only carries when a DEEPER one follows it. Kept
    // total rather than asserted: a chunker that raises loses the document.
    out.push([carryHeading, carryLevel, carry.join("\n\n"), carryStart || 1, secs[secs.length - 1][4]]);
  }
  return out;
}

/** A Markdown table split into row passages, or `null` if not a table.
 *  The header and its separator are repeated into every band. */
function tableBands(paragraph) {
  const lines = paragraph.split("\n");
  if (lines.length < 3) return null;
  for (const line of lines) if (line.trim() && !TABLE_ROW_RE.test(line)) return null;

  const header = lines[0];
  const separator = TABLE_SEP_RE.test(lines[1]) ? lines[1] : null;
  const prefix = separator ? [header, separator] : [header];
  const body = lines.slice(prefix.length);
  if (!body.length) return null;

  const bands = [];
  for (let i = 0; i < body.length; i += TABLE_ROWS_PER_PASSAGE) {
    const rows = body.slice(i, i + TABLE_ROWS_PER_PASSAGE);
    bands.push([[...prefix, ...rows].join("\n"), rows.length]);
  }
  if (bands.length < 2) return null;   // nothing gained; leave it ordinary
  bands[0] = [bands[0][0], bands[0][1] + prefix.length];
  return bands;
}

/** One oversized paragraph -> `[piece, sourceLines, rung]`.
 *
 * **There is no sentence rung.** UAX #29 says plain text gives inadequate
 * information for sentence boundaries; doing it properly needs CLDR locale
 * data — a dependency (L1) — and doing it improperly cuts inside `e.g.`,
 * `Dr.` and `3.5`. So: paragraph -> line -> word, boundaries that need no
 * knowledge of any language. */
function descend(paragraph, maxPassageBytes) {
  const lines = paragraph.split("\n");
  if (lines.length > 1) {
    const out = [];
    let current = [], size = 0;
    for (const line of lines) {
      const lineSize = nbytes(line) + 1;
      if (current.length && size + lineSize > maxPassageBytes) {
        out.push([current.join("\n"), current.length, "line"]);
        current = []; size = 0;
      }
      current.push(line); size += lineSize;
    }
    if (current.length) out.push([current.join("\n"), current.length, "line"]);
    if (out.length > 1) return out;
    // One line's worth after all — fall through to the word rung rather than
    // returning the same oversized piece under a different name.
    paragraph = out.length ? out[0][0] : paragraph;
  }

  const words = paragraph.split(" ");
  if (words.length < 2) return [[paragraph, countNl(paragraph) + 1, ""]];
  const out = [];
  let current = [], size = 0;
  for (const word of words) {
    const wordSize = nbytes(word) + 1;
    if (current.length && size + wordSize > maxPassageBytes) {
      out.push([current.join(" "), 1, "word"]);
      current = []; size = 0;
    }
    current.push(word); size += wordSize;
  }
  if (current.length) out.push([current.join(" "), 1, "word"]);
  return out;
}

/** `[piece, lineOffset, sourceLines, rung]` — the oversized split.
 *  `sourceLines` is tracked separately from a piece's own line count because a
 *  banded table repeats its header: the band holds more lines than it covers. */
function pieces(text, maxPassageBytes = MAX_PASSAGE_BYTES) {
  const out = [];
  let cursor = 0, current = [], size = 0;

  const flush = () => {
    if (!current.length) return;
    const piece = current.join("\n\n");
    const span = countNl(piece) + 1;
    out.push([piece, cursor, span, ""]);
    cursor += span + 1;   // the blank line that separated this piece from the next
    current = []; size = 0;
  };

  for (const paragraph of text.split("\n\n")) {
    const paragraphSize = nbytes(paragraph) + 2;
    // ⚠ Tables split at EVERY size, not only when oversized. A ten-row table
    // is ten answers, and it simply never crossed the byte ceiling to be
    // noticed — that was the coarse-citation defect.
    const bands = tableBands(paragraph);
    if (bands !== null) {
      if (current.length) {
        const [head, span] = bands[0];
        const pending = current.join("\n\n");
        bands[0] = [pending + "\n\n" + head, countNl(pending) + 1 + 1 + span];
        current = []; size = 0;
      }
      for (const [band, span] of bands) { out.push([band, cursor, span, ""]); cursor += span; }
      cursor += 1;   // ...but a blank line does follow the table itself
      continue;
    }
    if (paragraphSize > maxPassageBytes) {
      flush();
      for (const [piece, span, rung] of descend(paragraph, maxPassageBytes)) {
        out.push([piece, cursor, span, rung]);
        cursor += span;
      }
      cursor += 1;
      continue;
    }
    if (current.length && size + paragraphSize > maxPassageBytes) flush();
    current.push(paragraph); size += paragraphSize;
  }
  flush();
  return out;
}

/** Split into passages, in document order.
 *  `lineNumbers=false` suppresses the range for a document whose text was
 *  GENERATED rather than read — a `.docx`'s Markdown exists nowhere on disk,
 *  so a line number would be a confident lie. */
export function chunk(content, {
  minPassageBytes = MIN_PASSAGE_BYTES,
  maxPassageBytes = MAX_PASSAGE_BYTES,
  lineNumbers = true,
} = {}) {
  const merged = fold(sections(content), minPassageBytes);
  const passages = [];
  for (const [heading, , text, start, end] of merged) {
    for (const [piece, offset, span, rung] of pieces(text, maxPassageBytes)) {
      const pieceStart = start + offset;
      passages.push({
        heading,
        text: piece,
        ordinal: passages.length,
        line_start: lineNumbers ? pieceStart : 0,
        line_end: lineNumbers ? Math.min(end, pieceStart + span - 1) : 0,
        cut: rung,
        nbytes: nbytes(piece),
      });
    }
  }
  return passages;
}

export { nbytes };
