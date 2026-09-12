/** `fux answer` — one passage, cited, with its footing stated every time.
 *  Twin of `src/fux/query/__init__.py`'s `answer` half (R4's one-to-many).
 *
 * Ranks exactly as `ask` does with `top = 3`, then reads the cited documents
 * back from the source and says whether they still say what the index thinks.
 *
 * 🔴 **It never fetches.** A `url:` document reads `.fux/acquired/` or the
 * answer falls back to `source: "index"` — so this verb can emit
 * `as-ingested` and `unverified`, and never `current` or `stale`, for a URL.
 */
import { runQuery } from "../query/run.mjs";
import { recordFor } from "../store/reader.mjs";
import { chunk } from "../refer/chunk.mjs";
import { rescore } from "../refer/rescore.mjs";
import { assemble, CITATION_OVERHEAD } from "../refer/assemble.mjs";
import { Verdict } from "../refer/freshness.mjs";
import { resolve, readLocal, fromAcquired, GIT } from "../refer/source.mjs";

/** `answer` refers the top 3 — W-108. One question and no `-q`: an RRF score
 *  would make the three incomparable. */
export const ANSWER_TOP = 3;

function obtain(root, record) {
  const indexedSha = record.sha || "";
  const [kind, target] = resolve(record.id);
  if (kind === GIT) {
    try {
      const [raw, sha] = readLocal(root, target);
      // Decoded documents carry no line numbers — a `.docx`'s Markdown exists
      // nowhere on disk, so a line number would be a confident lie.
      return { text: raw.toString("utf8"), verdict: Verdict.verify(indexedSha, sha), lineNumbers: true };
    } catch (err) {
      return { text: null, verdict: Verdict.unverified(indexedSha, String(err.message)), lineNumbers: true };
    }
  }
  const blob = fromAcquired(root, indexedSha);
  if (blob === null) {
    return { text: null, verdict: Verdict.unverified(indexedSha, "node never fetches; nothing retained"), lineNumbers: false };
  }
  return {
    text: blob[0].toString("utf8"),
    verdict: Verdict.asIngested(indexedSha, blob[1], "read from .fux/acquired/"),
    lineNumbers: false,
  };
}

export function runAnswer(root, args) {
  const query = args._.join(" ");
  const { results, confidence } = runQuery(root, query, ANSWER_TOP, { wantConfidence: true });

  if (!results.length) {
    const payload = { answer: null, citation: null, source: "index" };
    if (confidence && args.band) payload.confidence = confidence.asDict();
    if (args.json) process.stdout.write(JSON.stringify(payload, null, 2) + "\n");
    else process.stdout.write("No confident matches.\n");
    return 0;
  }

  // --no-refer: skip reading the source entirely. `verified` STAYS
  // "unverified" — deliberately not upgraded, because nothing was checked.
  if (args.noRefer) {
    const top = results[0];
    const record = recordFor(root, top.id);
    const payload = {
      answer: { passages: [{ id: top.id, loc: top.loc, heading: top.title,
                             text: (record?.phrases || []).join("\n"), score: top.score }] },
      citation: { id: top.id, loc: top.loc, sha: record?.sha ?? "", freshness: "unverified" },
      source: "index",
    };
    if (confidence && args.band) payload.confidence = confidence.asDict();
    process.stdout.write(JSON.stringify(payload, null, 2) + "\n");
    return 0;
  }

  const candidates = [];
  const verdicts = new Map();
  for (const r of results) {
    const record = recordFor(root, r.id);
    if (!record) continue;
    const got = obtain(root, record);
    verdicts.set(r.id, got.verdict);
    if (got.text === null) continue;
    candidates.push([r.id, r.loc, record.sha || "",
                     chunk(got.text, { lineNumbers: got.lineNumbers })]);
  }

  if (!candidates.length) {
    const top = results[0];
    const payload = {
      answer: null, citation: { id: top.id, loc: top.loc, sha: "", freshness: "unverified" },
      source: "index",
    };
    if (confidence && args.band) payload.confidence = confidence.asDict();
    process.stdout.write(JSON.stringify(payload, null, 2) + "\n");
    return 0;
  }

  const scored = rescore(query, candidates);
  const bundle = assemble(scored, { overhead: CITATION_OVERHEAD });

  if (!bundle.citations.length) {
    process.stdout.write(JSON.stringify({ answer: null, citation: null, source: "refer" }, null, 2) + "\n");
    return 0;
  }

  // The verdict of the document behind the WINNING citation, not documents[0].
  const winner = bundle.citations[0];
  const verdict = verdicts.get(winner.doc_id);
  const freshness = verdict ? verdict.label : "unverified";

  const payload = {
    answer: {
      passages: bundle.citations.map((c) => ({
        id: c.doc_id, loc: c.locator, sha: c.sha,
        heading: c.heading, text: c.text, score: c.score,
      })),
    },
    citation: { id: winner.doc_id, loc: winner.locator, sha: winner.sha, freshness },
    source: "refer",
  };
  // The band is raised to the winning document's verdict — one function, one
  // place, because the printer and the receipt disagreed once in production.
  if (confidence && args.band) payload.confidence = confidence.withVerified(freshness).asDict();
  if (args.audit) {
    payload.audit = {
      documents: [...verdicts].map(([id, v]) => ({
        id, freshness: v.label, indexed_sha: v.indexedSha,
        fetched_sha: v.fetchedSha, strategy: "local", note: v.note,
      })),
      budget: bundle.budget, used: bundle.used, dropped: bundle.dropped,
    };
  }

  if (args.json) {
    process.stdout.write(JSON.stringify(payload, null, 2) + "\n");
  } else {
    for (const p of payload.answer.passages) {
      process.stdout.write(`${p.loc}  [${freshness}]\n`);
      if (p.heading) process.stdout.write(`§ ${p.heading}\n`);
      process.stdout.write(p.text + "\n\n");
    }
  }
  return 0;
}
