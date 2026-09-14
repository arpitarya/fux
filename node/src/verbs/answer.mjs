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
import { passageBoost } from "../query/rerank.mjs";
import { alreadyTextGlobs, isAlreadyText } from "../decode/registry.mjs";
import { decline } from "./find.mjs";

/** `answer` refers the top 3 — W-108. One question and no `-q`: an RRF score
 *  would make the three incomparable. */
export const ANSWER_TOP = 3;

function obtain(root, record, textGlobs) {
  const indexedSha = record.sha || "";
  const [kind, target] = resolve(record.id);
  if (kind === GIT) {
    // 🔴 **A document Node cannot DECODE is declined, not guessed at.** Python
    // runs the bytes back through the decoder plane before chunking, so a
    // `.csv` is re-scored as the Markdown table ingest indexed; Node has no
    // decoders and would chunk the raw bytes, producing a `path:L20-L28` that
    // points into text the index never held. Declining is the same move the
    // never-fetch rule makes for an unreachable URL, for the same reason —
    // `decode/registry.mjs`, SR-NODE-SEARCH decision 11.
    if (!isAlreadyText(root, target, textGlobs)) {
      return {
        text: null,
        verdict: Verdict.unverified(indexedSha, "node has no decoder for this type"),
        lineNumbers: true,
      };
    }
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

/** `answer`'s payload, assembled and NOT printed.
 *
 * Split out so `src/index.mjs` can return the object rather than parse the
 * CLI's own stdout back — which is what `api.py::_answer_from` still has to do
 * on the Python side, and is why [SR-API](../../../records/0154_api.md)
 * records the renderer split as deliberately staged. This verb is small
 * enough that the split costs nothing, so it is taken here.
 *
 * Returns `{ payload, freshness, results }`; the renderer decides what a
 * person sees. */
export function answerPayload(root, args) {
  const query = args._.join(" ");
  // ⚠ **`answer` takes ONE question and no `-q`** (SR-ANSWER decision 4): the
  // verb means one answer. `--expand` applies exactly as it does to `ask`,
  // because expanding a question is not asking a second one.
  const { results, confidence, tune } = runQuery(root, query, ANSWER_TOP, {
    useTune: args.noTune !== true, wantConfidence: true, expand: args.expand ?? "",
  });
  const band = (block, freshness) => {
    if (!block || !args.band) return undefined;
    return freshness ? block.withVerified(freshness).asDict() : block.asDict();
  };

  if (!results.length) {
    const payload = { answer: null, citation: null, source: "index" };
    const b = band(confidence);
    if (b) payload.confidence = b;
    return { payload, freshness: null, results };
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
    const b = band(confidence);
    if (b) payload.confidence = b;
    return { payload, freshness: "unverified", results };
  }

  const candidates = [];
  const verdicts = new Map();
  // Resolved ONCE per answer, not once per candidate: it is a committed file
  // read, and three candidates is three reads of the same bytes.
  const textGlobs = alreadyTextGlobs(root);
  for (const r of results) {
    const record = recordFor(root, r.id);
    if (!record) continue;
    const got = obtain(root, record, textGlobs);
    verdicts.set(r.id, got.verdict);
    if (got.text === null) continue;
    candidates.push([r.id, r.loc, record.sha || "",
                     chunk(got.text, {
                       lineNumbers: got.lineNumbers,
                       minPassageBytes: tune.minPassageBytes,
                       maxPassageBytes: tune.maxPassageBytes,
                     })]);
  }

  if (!candidates.length) {
    const top = results[0];
    const payload = {
      answer: null, citation: { id: top.id, loc: top.loc, sha: "", freshness: "unverified" },
      source: "index",
    };
    const b = band(confidence);
    if (b) payload.confidence = b;
    return { payload, freshness: "unverified", results };
  }

  // `[ranking] rerank_weight`, not a second `[refer]` knob — the same constant
  // that reordered the DOCUMENTS now scores their passages, and neither may be
  // turned on without the other (`refer/_rescore.py::rescore`).
  const scored = rescore(query, candidates, {
    weight: tune.rerankWeight, boostFn: passageBoost,
  });
  const bundle = assemble(scored, {
    overhead: CITATION_OVERHEAD, budget: tune.budget, perDocFraction: tune.perDocFraction,
  });

  if (!bundle.citations.length) {
    return { payload: { answer: null, citation: null, source: "refer" }, freshness: null, results };
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
        // SR-REFER decision 17 / SR-ANSWER decision 9. Additive: no key
        // removed or repurposed.
        ordinal: c.ordinal,
      })),
    },
    citation: { id: winner.doc_id, loc: winner.locator, sha: winner.sha, freshness },
    source: "refer",
  };
  // The band is raised to the winning document's verdict — one function, one
  // place, because the printer and the receipt disagreed once in production.
  const b = band(confidence, freshness);
  if (b) payload.confidence = b;
  if (args.audit) {
    payload.audit = {
      documents: [...verdicts].map(([id, v]) => ({
        id, freshness: v.label, indexed_sha: v.indexedSha,
        fetched_sha: v.fetchedSha, strategy: "local", note: v.note,
      })),
      budget: bundle.budget, used: bundle.used, dropped: bundle.dropped,
    };
  }
  return { payload, freshness, results };
}

export function runAnswer(root, args) {
  const { payload, freshness } = answerPayload(root, args);

  if (args.json || payload.answer === null) {
    if (!args.json && payload.answer === null) {
      decline();
      return 0;
    }
    process.stdout.write(JSON.stringify(payload, null, 2) + "\n");
    return 0;
  }

  for (const p of payload.answer.passages) {
    process.stdout.write(`${p.loc}  [${freshness}]\n`);
    if (p.heading) process.stdout.write(`§ ${p.heading}\n`);
    process.stdout.write(p.text + "\n\n");
  }
  return 0;
}
