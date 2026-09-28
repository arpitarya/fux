/** The ONE Markdown heading grammar, shared by ingest and the chunker.
 *  Twin of `src/fux/decode/_markdown.py`.
 *
 * **A fenced code block is content, not structure** — a `# comment` inside a
 * ``` block is not a heading, and treating it as one splits a document where
 * its author did not.
 *
 * Owned, with its Python twin, by [SR-DECODE](../../../records/0139_decode.md).
 */

const HEADING_RE = /^(?<hashes>#{1,6})\s+(?<text>.*?)\s*#*\s*$/;
/** Up to three leading spaces per CommonMark; a fourth makes it an indented
 *  code block, which cannot contain a heading anyway. */
const FENCE_RE = /^ {0,3}(?<fence>`{3,}|~{3,})(?<info>.*)$/;

/** `[lineno, line, fenced]` per line, `lineno` 1-based.
 *
 * The open fence is tracked as its DELIMITER STRING, not a boolean, so a
 * closing fence must match its opener in both character and length: ``` inside
 * a ~~~ block is content, and a shorter run of backticks does not close a
 * longer one. */
export function* walk(markdown) {
  let fence = null;
  const lines = markdown.split("\n");
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const lineno = i + 1;
    const match = FENCE_RE.exec(line);
    if (fence === null) {
      if (match) { fence = match.groups.fence; yield [lineno, line, true]; }
      else yield [lineno, line, false];
      continue;
    }
    const closes = match !== null
      && match.groups.fence[0] === fence[0]
      && match.groups.fence.length >= fence.length
      // A closing fence carries no info string.
      && match.groups.info.trim() === "";
    if (closes) fence = null;
    yield [lineno, line, true];
  }
}

/** Every ATX heading outside a code fence, in document order.
 *  `lineno` is 1-based, matching the `path:L12-L40` citation format. */
export function headings(markdown) {
  const found = [];
  for (const [lineno, line, fenced] of walk(markdown)) {
    if (fenced) continue;
    const match = HEADING_RE.exec(line);
    if (match) found.push({ lineno, level: match.groups.hashes.length, text: match.groups.text.trim() });
  }
  return found;
}
