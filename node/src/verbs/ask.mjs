/** `fux ask` — a ranked list with scores, which is what you want when you are
 *  judging the engine. A projection of `runQuery`, never a second strategy.
 *  Twin of `src/fux/query/__init__.py`'s `ask` half (R4's one-to-many).
 *
 * 🔴 **This is also `fux lexical`'s handler, and on this reader that is one
 * FUNCTION rather than one test.** `fux lexical` is BM25F alone, frozen
 * byte-identical to `ask` (W-160, SR-CLI decision 12). On the Python side the
 * two are separate entry points held equal by
 * `tests_e2e/test_relational.py::test_lexical_is_byte_identical_to_ask`; here
 * `fux.mjs` dispatches both cases to `runAsk`, so they agree by construction.
 *
 * ⚠ **W-161 was the change that split them, and the split is one argument.**
 * `compose: false` forces the graph tier off, which is what `fux lexical` is —
 * the lexical core, frozen — and `compose: true` is `ask`. Forcing it here
 * rather than trusting the caller not to ask means a repository whose
 * `tune.toml` turns the tier on cannot make the frozen baseline verb stop
 * being a baseline, which is the whole value of having the verb.
 */
import { runFused } from "../query/run.mjs";
import { headingsFor } from "../query/headings.mjs";
import { recordFor } from "../store/reader.mjs";
import { declareArchived, declareConfidence, declareFloorOff, decline } from "./find.mjs";

export const ARCHIVED_MARKER = "[archived]";

//: W-162 — a document a human pinned to this exact question. Same shape as the
//: archived marker and for the same reason: a pinned row's score is still its
//: own score (`0.0` when the ranking never scored it), so without the marker
//: the list reads as a ranking that had gone wrong. Twin of
//: `query/__init__.py::PINNED_MARKER`.
export const PINNED_MARKER = "[pinned]";
export const SECTION_MARKER = "§";

//: W-161 — what precedes the Tier B block. It says *related*, never *results*
//: or *also*: the word is the whole contract. Twin of
//: `query/__init__.py::RELATED_HEADING`.
export const RELATED_HEADING = "related (linked from the answers, no query word matched):";

//: W-161 — the per-row arrow. ASCII, like every other note fux prints.
export const RELATED_MARKER = "<-";

/** The Tier B block, **on stdout and under the results**.
 *
 * 🔴 This one is stdout, and it is the exception to the `declare*` family.
 * Those go to stderr because they are things fux says *about* an answer;
 * `related` is part of the answer. What keeps that safe is the same thing that
 * keeps `headings` safe: `find` is the verb for piping bare paths, and `find`
 * has no tier.
 *
 * The walk mass is deliberately NOT printed: it is a statistic on a scale
 * nothing else here shares, and a float in the score column's position would
 * be read as a score by every reader who did not stop to check — the one
 * confusion this tier exists to avoid. `--json` carries it. */
export function declareRelated(related) {
  if (!related || related.length === 0) return;
  process.stdout.write("\n");
  process.stdout.write(`${RELATED_HEADING}\n`);
  for (const row of related) {
    const mark = row.archived ? `${ARCHIVED_MARKER} ` : "";
    process.stdout.write(`  ${RELATED_MARKER} ${mark}${row.title}  (${row.loc})  ${row.route}\n`);
  }
}

export function runAsk(root, args, { compose = true } = {}) {
  const query = args._.join(" ");
  const queries = [query, ...(args.q || [])];
  const top = args.top ?? 5;

  const { results, related, confidence, fused, tune } = runFused(root, queries, top, {
    useTune: args.noTune !== true,
    wantConfidence: true,
    expand: args.expand ?? "",
    // `--no-related` is the per-call opt-out; `[graph] ask_related` is the
    // per-repository one. `undefined` here means *the tune decides*.
    compose,
    related: args.related,
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
    // W-161. **Its own key, never merged into `results`** — a document with no
    // lexical match sitting among real matches *looks like* a match. Absent
    // means the tier did not run (`--no-related`, `[graph] ask_related =
    // false`, or `fux lexical`); `[]` is what *no neighbours* looks like.
    if (related !== null && related !== undefined) {
      payload.related = related.map((r) => ({
        id: r.id, title: r.title, loc: r.loc, mass: r.mass,
        archived: r.archived, route: r.route,
      }));
    }
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
  for (const [i, r] of rows.entries()) {
    const tie = r.tie ? "  (tie)" : "";
    let mark = r.archived ? `${ARCHIVED_MARKER} ` : "";
    if (r.pinned) mark = `${PINNED_MARKER} ` + mark;
    // W-161 — the MOVED rows carry their move. A bare `(graph)` on every row
    // cannot do the job the marker exists for: on a query where the walk
    // reaches all five, a reader seeing 5.93 above 6.36 still has nothing to
    // read it by. A row the walk reached but did not move keeps the bare
    // marker — the case where the links agreed with the words.
    let boost = "";
    if (r.boosted) {
      const moved = r.route && !r.route.startsWith(`#${i + 1} ->`);
      boost = moved ? `  (graph ${r.route.split(" via ")[0]})` : "  (graph)";
    }
    process.stdout.write(`${r.score.toFixed(4)}${tie}${boost}  ${mark}${r.title}  (${r.loc})\n`);
    for (const h of r.headings || []) process.stdout.write(`        ${SECTION_MARKER} ${h}\n`);
  }
  declareRelated(related);
  declarePinned(results);
  declareArchived(results);
  declareConfidence(confidence, args.band);
  return 0;
}

/** Say out loud that a person decided the first row. stderr, once.
 *
 * Twin of `query/__init__.py::_declare_pinned`. Printed under `--json` too,
 * exactly as the archived note is, because *a human overrode the ranking* is
 * the single thing a reader most needs and least expects. */
export function declarePinned(results) {
  const pinned = results.filter((r) => r.pinned);
  if (!pinned.length) return;
  process.stderr.write(
    `note: ${pinned[0].loc} is PINNED to this exact question by a human ` +
    "(.fux/eval/corrections.tsv) - its position is a person's decision, not " +
    "this ranking's. `fux correct --list` shows every pin.\n",
  );
}
