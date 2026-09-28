/** Which documents Node can read back as the index saw them.
 *  The reader's half of `src/fux/decode/__init__.py`.
 *
 * 🔴 **Node has no decoders, and until 2026-09-12 it did not know that.**
 * Python's refer plane runs a cited document's bytes back through the decoder
 * plane before chunking, so a `.csv` is re-scored as the Markdown table ingest
 * indexed. Node chunked the RAW bytes and cited `path:L20-L28` into them —
 * a locator that points at a real line of a file whose text the index never
 * contained. Found by comparing the two library surfaces on this repo:
 * `answer("rollback")` returned a different document, a different passage and
 * a different locator in each runtime.
 *
 * **Porting the decoders is not the fix and never will be.** A consumer
 * decoder is arbitrary Python in `.fux/decoders/`, loaded by path
 * ([SR-DECODE]'s whole boundary), and there is no Node twin of a file the
 * consumer wrote in another language. Nor can a built-in be transcribed
 * safely: `xlsx`, `pdf` and `docx` are format work where a near-miss produces
 * plausible text.
 *
 * **So Node declines, in the shape it already uses for the network.** A
 * document whose type goes through a decoder is skipped by `answer`, exactly
 * as an unreachable `url:` is, and the verb falls back rather than citing
 * something it cannot reproduce ([SR-NODE-SEARCH](../../../records/0153_node-search.md)
 * decision 11). **Under-claiming is the only safe direction here**: a document
 * wrongly treated as plain text is a wrong citation, while one wrongly skipped
 * is an answer from the next candidate.
 *
 * ## The question is asked the RIGHT way round
 *
 * Not *"does a decoder claim this extension?"* — which would need the built-in
 * registry, every `.fux/decoders/*.py`, and their precedence, all mirrored in
 * JS and all able to drift. Instead: *"is this document ALREADY TEXT?"*, which
 * `.fux/formats.toml`'s `include` list answers in committed bytes, written by
 * the consumer and read by both runtimes. A bound extension is never repeated
 * in `include` (SR-TYPES decision 12), so the two sets do not overlap and the
 * complement is exact.
 */
import { readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { parseToml } from "../config/toml.mjs";
import { fixed } from "../config/constants.mjs";

//: The built-in `include` default, for a repo with no `.fux/formats.toml` —
//: `ingest/gitdir.py::_PROSE_TYPES`. **Held equal to Python's by
//: `tests/test_node_decode_boundary.py`**: a format that becomes prose on one
//: side and not the other is a silent citation defect, which is the whole
//: reason this module exists.
export const PROSE_TYPES = fixed("decoders", "prose_types");

/** Does `path` match `pattern`, with `*` **not** crossing a `/`?
 *
 * `fnmatch` semantics are deliberately not used on either side: its `*`
 * matches `/`. A pattern with no `/` matches the **basename**, which is what
 * makes `*.md` mean "any markdown file anywhere". Twin of
 * `ingest/sourcelist.py::glob_match`. */
export function globMatch(pattern, path) {
  const subject = pattern.includes("/") ? path : path.split("/").pop();
  let out = "";
  for (let i = 0; i < pattern.length; i++) {
    const ch = pattern[i];
    if (ch === "*") {
      if (pattern.startsWith("**", i)) { out += ".*"; i++; continue; }
      out += "[^/]*";
    } else if (ch === "?") {
      out += "[^/]";
    } else {
      out += ch.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }
  }
  return new RegExp(`^${out}$`).test(subject);
}

/** The `include` globs in force for this repo: `.fux/formats.toml`'s if it has
 *  one, the built-in default otherwise.
 *
 *  **An absent file never means "everything" and never means "nothing".**
 *  ⚠ Since W-225 stage 4a SR-TYPES makes the file REQUIRED and `fux ingest`
 *  stops without it; this read stays tolerant because it is on the QUERY path,
 *  where the cost of the fallback is a conservative skip, never a wrong
 *  citation — the same tolerance Python's answer path extends. */
export function alreadyTextGlobs(root) {
  const path = join(root, fixed("files", "formats"));
  try {
    if (!statSync(path).isFile()) return PROSE_TYPES;
    const data = parseToml(readFileSync(path, "utf8"), path);
    const include = data.include;
    if (!Array.isArray(include) || !include.length) return PROSE_TYPES;
    return include.filter((g) => typeof g === "string");
  } catch {
    // Tolerant, like every other ranking-metadata read on the query path: a
    // formats file this cannot parse falls back to the default rather than
    // failing a query. The cost is a conservative skip, never a wrong citation.
    return PROSE_TYPES;
  }
}

/** Can Node reproduce this document's text as the index holds it?
 *
 * `true` only when the document is already prose. Everything else went through
 * a decoder Node does not have. */
export function isAlreadyText(root, loc, globs = null) {
  const patterns = globs ?? alreadyTextGlobs(root);
  return patterns.some((g) => globMatch(g, loc));
}
