/** Corrections and pins, READ. Twin of `src/fux/correct.py`'s read half.
 *
 * 🔴 **This reader never writes one.** `fux correct` writes committed files
 * and the Node plane only reads (SR-NODE-SEARCH) — so `fux correct` is
 * Python-only as a verb, and what has to cross is the effect: a pin filed by a
 * human must move the same document to #1 on both readers, or the same
 * repository answers two different ways.
 *
 * The vocabulary effect needs nothing here at all: a correction is a body line
 * in `.fux/enrich/<sha>.md`, indexed as `ctx` by ingest, so both readers see it
 * as ordinary index statistics. **Only the pin needs code**, because a pin is
 * applied at query time rather than at ingest.
 */
import { readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { tokenize } from "./query/tokenize.mjs";
import { iterShardPaths, rawRecordLines } from "./store/reader.mjs";

export const CORRECTIONS_FILE = ".fux/eval/corrections.tsv";

/** The analyzed form of a question — what a pin matches on.
 *
 * **The ANALYZER, not `toLowerCase().trim()`.** A pin has to fire for "How do
 * I roll back a release?" and "how do i roll back releases" alike, and the
 * analyzer is the only thing here that already knows those are the same
 * question. Twin of `correct.py::normalise`. */
export function normalise(question) {
  return tokenize(question).join(" ");
}

/** Every filed correction, in file order. `[]` when there is no file.
 *
 * **Never throws** — a malformed row is skipped. This is read on the query
 * path, and a hand-edited tab would otherwise take out `fux ask` for everyone
 * in the repository. */
export function loadCorrections(root) {
  const path = join(root, CORRECTIONS_FILE);
  let text;
  try {
    if (!statSync(path).isFile()) return [];
    text = readFileSync(path, "utf8");
  } catch {
    return [];
  }
  const out = [];
  for (const line of text.split("\n")) {
    if (!line.trim() || line.startsWith("#")) continue;
    const parts = line.split("\t");
    if (parts.length < 4) continue;
    const [question, docId, loc, sourceSha] = parts;
    out.push({ question, docId, loc, sourceSha, pin: parts.length > 4 && parts[4].trim() === "1" });
  }
  return out;
}

/** The doc id pinned to this exact question, or `null`.
 *
 * ⚠ **A pin whose document's content sha has moved is SUSPENDED, not
 * applied** — the person pinned a question to a version of a document, and a
 * rewritten one may no longer answer it. Python's `fux doctor` reports every
 * suspended pin; this reader has no `doctor`, so it applies the same rule
 * silently and says nothing, exactly as Python's query path does.
 *
 * Twin of `correct.py::pinned_for`. */
export function pinnedFor(root, query, records = null) {
  const pins = loadCorrections(root).filter((c) => c.pin);
  if (!pins.length) return null;
  const wanted = normalise(query);
  if (!wanted) return null;
  const byId = records ?? recordsById(root);
  for (const correction of pins) {
    if (normalise(correction.question) !== wanted) continue;
    const record = byId.get(correction.docId);
    if (record === undefined) continue;         // the document left the corpus
    if ((record.sha ?? "") !== correction.sourceSha) continue;  // suspended
    return correction.docId;
  }
  return null;
}

/** Every committed record, keyed by id. Read only when a pin might apply. */
function recordsById(root) {
  const out = new Map();
  try {
    for (const path of iterShardPaths(root)) {
      const [, lines] = rawRecordLines(path);
      for (const line of lines) {
        const record = JSON.parse(line.toString("utf8"));
        out.set(record.id, record);
      }
    }
  } catch {
    return out;
  }
  return out;
}

/** Move a pinned document to #1 for this exact question.
 *
 * **After the ranking and after the reranker**, so the pin sits on top of the
 * ranking rather than inside it. A pinned document the ranking did not return
 * is INSERTED with `score: 0` — the honest number, because the ranking never
 * scored it — and the list is re-truncated. Twin of
 * `query/__init__.py::_apply_pin`. */
export function applyPin(root, query, results, top) {
  let docId;
  try {
    docId = pinnedFor(root, query);
  } catch {
    return results;
  }
  if (docId === null) return results;
  const kept = results.filter((r) => r.id !== docId);
  let found = results.find((r) => r.id === docId);
  if (found === undefined) {
    const record = recordsById(root).get(docId);
    if (record === undefined) return results;
    found = {
      id: docId,
      title: record.title ?? "",  // W-194: `title_h` no longer exists
      loc: record.loc ?? "",
      score: 0.0,
      archived: Boolean(record.archived ?? false),
      tie: false,
      mtime: record.mtime ?? null,
    };
  }
  return [{ ...found, pinned: true }, ...kept].slice(0, top);
}
