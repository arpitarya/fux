/** `fux ask` — a ranked list with scores, which is what you want when you are
 *  judging the engine. A projection of `runQuery`, never a second strategy.
 *  Twin of `src/fux/query/__init__.py`'s `ask` half (R4's one-to-many).
 */
import { runFused } from "../query/run.mjs";
import { headingsFor } from "../query/headings.mjs";
import { recordFor } from "../store/reader.mjs";
import { declareArchived, declareConfidence, declareFloorOff, decline } from "./find.mjs";

export const ARCHIVED_MARKER = "[archived]";
export const SECTION_MARKER = "§";

export function runAsk(root, args) {
  const query = args._.join(" ");
  const queries = [query, ...(args.q || [])];
  const top = args.top ?? 5;

  const { results, confidence, fused, tune } = runFused(root, queries, top, {
    useTune: args.noTune !== true, wantConfidence: true, expand: args.expand ?? "",
  });
  declareFloorOff(tune, Boolean(args.json));

  // Headings are display-only and are resolved AFTER ranking, exactly like the
  // title fallback — so they can never reach a score.
  const showSections = args.sections !== false;
  const rows = results.map((r) => {
    const out = { ...r };
    if (showSections) out.headings = headingsFor(recordFor(root, r.id), query);
    return out;
  });

  if (args.json) {
    const payload = { results: rows };
    // SR-CONFIDENCE decision 11: present ONLY under --band. **Absent means
    // NOT ASKED FOR — it is never a claim about the answer.**
    if (confidence && args.band) payload.confidence = confidence.asDict();
    // An RRF score and a BM25F score are not comparable, so a consumer must be
    // told which it is holding. Absent means "one question", never "unknown".
    if (fused) payload.fused = true;
    process.stdout.write(JSON.stringify(payload, null, 2) + "\n");
    declareArchived(results);
    return 0;
  }

  if (!rows.length) {
    decline();
    declareConfidence(confidence, args.band);
    return 0;
  }
  // W-84 — the matched headings under each hit, INDENTED and never on the
  // citation line: the `(loc)` a reader copies must stay a bare locator.
  // W-111 — `(tie)` after the score, for the same reason.
  for (const r of rows) {
    const tie = r.tie ? "  (tie)" : "";
    const mark = r.archived ? `${ARCHIVED_MARKER} ` : "";
    process.stdout.write(`${r.score.toFixed(4)}${tie}  ${mark}${r.title}  (${r.loc})\n`);
    for (const h of r.headings || []) process.stdout.write(`        ${SECTION_MARKER} ${h}\n`);
  }
  declareArchived(results);
  declareConfidence(confidence, args.band);
  return 0;
}
