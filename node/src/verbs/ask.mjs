/** `fux ask` — a ranked list with scores, which is what you want when you are
 *  judging the engine. A projection of `run_query`, never a second strategy.
 *  Twin of `src/fux/query/__init__.py`'s `ask` half (R4's one-to-many). */
import { runFused } from "../query/run.mjs";
import { headingsFor } from "../query/headings.mjs";
import { recordFor } from "../store/reader.mjs";

export function runAsk(root, args) {
  const query = args._.join(" ");
  const queries = [query, ...(args.q || [])];
  const top = args.top ?? 5;

  const { results, confidence, fused } = runFused(root, queries, top, {
    wantConfidence: true,
  });

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
    // ADR-CONFIDENCE decision 11: present ONLY under --band. **Absent means
    // NOT ASKED FOR — it is never a claim about the answer.**
    if (confidence && args.band) payload.confidence = confidence.asDict();
    // An RRF score and a BM25F score are not comparable, so a consumer must be
    // told which it is holding.
    if (fused) payload.fused = true;
    process.stdout.write(JSON.stringify(payload, null, 2) + "\n");
  } else {
    if (!rows.length) {
      process.stdout.write("No confident matches.\n");
      return 0;
    }
    for (const r of rows) {
      const tie = r.tie ? "  (tie)" : "";
      const arch = r.archived ? " [archived]" : "";
      process.stdout.write(`${r.score.toFixed(4)}${tie}${arch} ${r.title} (${r.loc})\n`);
      for (const h of r.headings || []) process.stdout.write(`    § ${h}\n`);
    }
    if (confidence && args.band) process.stderr.write(`[${confidence.band}] ${confidence.asDict().support} scored\n`);
  }
  return 0;
}
