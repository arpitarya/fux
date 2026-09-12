/** `fux find` — ranked document locations, one per line, for pipes.
 *  A projection of `ask`, not a second strategy: same `runQuery`, same `rank()`.
 *  Twin of `src/fux/query/__init__.py`'s `find` half (R4's one-to-many).
 *
 * 🔴 **It goes through `runQuery`, not `scan.ask`.** That is the whole of
 * [ADR-NODE-SEARCH](../../../docs/adr/0155_node-search.md) decision 8 at the
 * call site: `scan.ask` skips `.fux/tune.toml`, the archived weighting and the
 * reranker, and calling it here is what made a tuned repo answer differently in
 * the two runtimes.
 *
 * **stdout is BARE PATHS.** No `[archived]` marker, no filter note, no band —
 * `find` exists to be piped, and anything else on stdout is read by `xargs` as
 * a filename (ADR-DIR-LIST decision 12). Every note goes to stderr; the flags
 * are carried in `--json`, which is where a machine reader should look.
 */
import { runFused } from "../query/run.mjs";
import { headingsFor } from "../query/headings.mjs";
import { recordFor } from "../store/reader.mjs";
import { queryTermHashes } from "../query/scan.mjs";
import { analyze } from "../query/analyzer.mjs";
import { phrasePresent, readLocalText } from "../query/rerank.mjs";

/** `find`'s three precision controls. W-111.
 *
 * **Post-filters on the ranked list, and they retrieve nothing.** A document
 * the ranking did not place in `--top` cannot be filtered *into* the answer —
 * raising `--top` is what widens the pool, and that is stated rather than
 * worked around. Retrieving deeper and truncating after would make `support` in
 * the confidence block describe a depth the caller never asked for.
 *
 * ⚠ **The band is computed on the UNFILTERED ranking**, because it is a claim
 * about the corpus's answer to the question, not about the subset a caller
 * asked to see. */
function filtered(root, results, query, args) {
  const { under, phrase } = args;
  const requireAll = Boolean(args.all);
  if (!under && !phrase && !requireAll) return [results, 0];

  const before = results.length;
  let kept = results;

  if (under) {
    // Plain prefix on `loc`, the same shape `Weighting.priorityFor` matches on.
    // A trailing slash is NOT appended: `docs/a` matching `docs/ab.md` is what
    // a prefix means, and inventing a component boundary here would disagree
    // with `priorityFor`.
    kept = kept.filter((r) => r.loc === under || r.loc.startsWith(under));
  }

  if (requireAll) {
    // Over the COMMITTED record's terms — never fetched text. `find` is an
    // offline verb and the whole point of `--all` is that it is cheap.
    const wanted = queryTermHashes(query);
    kept = kept.filter((r) => {
      const terms = recordFor(root, r.id)?.terms ?? {};
      return wanted.every((h) => h in terms);
    });
  }

  if (phrase) {
    const terms = analyze(phrase);
    kept = kept.filter((r) => {
      const text = readLocalText(root, r.id, r.loc);
      // ⚠ **A `url:` document is KEPT, never dropped.** Offline it has no text
      // to test, and dropping it would report *"this page does not contain the
      // phrase"* on the strength of not having looked.
      if (text === null) return true;
      return phrasePresent(terms, text);
    });
  }

  return [kept, before - kept.length];
}

/** What a filter removed, on **stderr**, so stdout stays a bare path list. */
function declareFilters(args, dropped) {
  if (!dropped) return;
  const names = [
    ["--phrase", args.phrase], ["--under", args.under], ["--all", args.all],
  ].filter(([, on]) => on).map(([name]) => name);
  process.stderr.write(
    `[filter] ${names.join(" ")} removed ${dropped} of the ranked results; ` +
    "the confidence band describes the ranking before filtering\n",
  );
}

/** ADR-ARCHIVED-CONTENT decision 7: a response-level note when any archived
 *  document is returned. **stderr, never stdout.** ASCII only — a Windows
 *  console's default codepage cannot encode a fancy dash and the process
 *  crashes on write rather than degrading. */
export function declareArchived(results, weight) {
  const n = results.filter((r) => r.archived).length;
  if (!n) return;
  const demoted = weight !== 1.0 ? ` (demoted, weight ${weight.toFixed(2)})` : "";
  process.stderr.write(
    `note: ${n} of ${results.length} results are from archived sources${demoted}` +
    " - retired from the live corpus. An archived document records what was" +
    " true when it was retired, not what is true now.\n",
  );
}

/** ADR-CONFIDENCE decision 4: the band on stderr, never stdout, and only under
 *  `--band` — under which `grounded` prints too, because a flag that goes quiet
 *  exactly when the answer is good reads as broken. */
export function declareConfidence(block, show) {
  if (block === null || block === undefined || !show) return;
  process.stderr.write((block.line() || `confidence: ${block.band}.`) + "\n");
}

export function runFind(root, args) {
  const query = args._.join(" ");
  const queries = [query, ...(args.q || [])];
  const top = args.top ?? 5;

  const { results: ranked, confidence, fused, tune } = runFused(root, queries, top, {
    useTune: args.noTune !== true, wantConfidence: true, expand: args.expand ?? "",
  });
  const [results, dropped] = filtered(root, ranked, query, args);
  declareFilters(args, dropped);

  if (args.json) {
    const payload = {
      results: results.map((r) => ({ ...r, headings: headingsFor(recordFor(root, r.id), query) })),
    };
    if (fused) payload.fused = true;
    // ADR-CONFIDENCE decision 11: present ONLY under --band. **Absent means
    // NOT ASKED FOR — it is never a claim about the answer.**
    if (confidence && args.band) payload.confidence = confidence.asDict();
    process.stdout.write(JSON.stringify(payload, null, 2) + "\n");
    declareArchived(results, tune.archivedWeight);
    return 0;
  }

  if (!results.length) {
    process.stdout.write("No confident matches.\n");
    declareConfidence(confidence, args.band);
    return 0;
  }
  for (const r of results) process.stdout.write(`${r.loc}\n`);
  declareArchived(results, tune.archivedWeight);
  declareConfidence(confidence, args.band);
  return 0;
}
