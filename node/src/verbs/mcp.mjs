/** `fux mcp` — the index over the Model Context Protocol, on stdio.
 *  Twin of `src/fux/mcp.py`'s protocol half.
 *
 * Newline-delimited JSON-RPC: `initialize` -> `notifications/initialized`,
 * `tools/list`, `tools/call`, and a notification (no `id`) is never answered.
 *
 * ⚠ **The tool DESCRIPTIONS are the one thing that must not be transcribed.**
 * A description is what an agent reads to decide whether to call a tool, so
 * two hand-maintained copies would drift into two different products wearing
 * one name. This half loads them from `mcp-tools.json`.
 *
 * 🔴 **`src/fux/mcp.py` does NOT read that file — it still carries its own
 * literal, and the drift was real**: measured 2026-09-12, this side emitted
 * `"default": "5"` (a STRING) where Python emits `5` (an integer), on a
 * property declared `"type": "integer"`. What holds them equal is
 * `tests/test_mcp.py::test_the_node_tool_file_matches_the_python_literal`,
 * not a shared read — SR-MCP decision 11 states why, and what that leaves
 * unguarded once this file ships to npm on its own.
 */
import { readFileSync, statSync } from "node:fs";
import { dirname, isAbsolute, join, relative, resolve as resolvePath, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { createInterface } from "node:readline";
import { runQuery } from "../query/run.mjs";
import { headingsFor } from "../query/headings.mjs";
import { iterShardPaths, rawRecordLines } from "../store/reader.mjs";
import { contentSha } from "../store/format.mjs";
import { cmpCodePoints, pyRound } from "../compat/pyfloat.mjs";
import { loadOutput } from "../config/output.mjs";
import { Graph, edgesFromRecords } from "../graph/model.mjs";
import { FuxError } from "../errors.mjs";

export const PROTOCOL_VERSION = "2024-11-05";
const HERE = dirname(fileURLToPath(import.meta.url));

/** `mcp-tools.json`, found from whichever shape this code is running in.
 *
 * 🔴 **Two shapes, one source file, so the path cannot be a constant.** In this
 * repository the module sits at `node/src/verbs/` and the descriptions are two
 * directories up; in the published bundle everything is one file at the package
 * root and they are beside it (L10 — the consumer gets build output). Hard-coding
 * either spelling makes `fux mcp` work in one shape and throw `ENOENT` in the
 * other, and the bundle is the shape a consumer actually runs.
 *
 * Candidates in order, first hit wins; the list is short and closed on purpose —
 * an upward search would find another package's file in a monorepo.
 */
function toolsPath() {
  for (const candidate of [join(HERE, "mcp-tools.json"), join(HERE, "..", "..", "mcp-tools.json")]) {
    try {
      if (statSync(candidate).isFile()) return candidate;
    } catch {
      // not here; try the next shape
    }
  }
  throw new FuxError("mcp-tools.json is missing from this installation of the Node reader");
}

let TOOLS = null;
function tools(top) {
  if (TOOLS === null) {
    TOOLS = JSON.parse(readFileSync(toolsPath(), "utf8")).tools;
  }
  // The only per-connection substitution: the resolved `[mcp] top` appears in
  // the `top` property's description so an agent sees the real default.
  //
  // ⚠ **The QUOTED form is replaced first, and un-quoted.** `"{{TOP}}"` is a
  // JSON *number* on the Python side (`"default": 5`); a naive `replaceAll`
  // over the serialized text leaves it a string, which is an `inputSchema`
  // that contradicts its own `"type": "integer"`. Found 2026-09-12 by the
  // equality test, not by a client complaining.
  const text = JSON.stringify(TOOLS)
    .replaceAll('"{{TOP}}"', String(top))
    .replaceAll("{{TOP}}", String(top));
  return JSON.parse(text);
}

const ok = (id, result) => ({ jsonrpc: "2.0", id, result });
const err = (id, code, message) => ({ jsonrpc: "2.0", id, error: { code, message } });

/** Every committed record, keyed by id — `store.read_index`'s shape. */
function recordsById(root) {
  const out = new Map();
  for (const path of iterShardPaths(root)) {
    const [, lines] = rawRecordLines(path);
    for (const line of lines) {
      const record = JSON.parse(line.toString("utf8"));
      out.set(record.id, record);
    }
  }
  return out;
}

/** Python's `str.splitlines()` — which splits on more than `\n`, and returns
 *  `[]` rather than `[""]` for an empty string. Line NUMBERS come out of this,
 *  so an off-by-one here is a citation pointing at the wrong line. */
function splitLines(text) {
  if (text === "") return [];
  const out = text.split(/\r\n|[\n\r\u000b\u000c\u001c\u001d\u001e\u0085\u2028\u2029]/);
  if (out.length && out[out.length - 1] === "") out.pop();
  return out;
}

/** 🔴 **The argument names are the SCHEMA's, not this file's.** Until
 *  2026-09-12 these three handlers read `args.id` where `mcp-tools.json`
 *  advertises `path`, so every conformant client got an empty answer from a
 *  server that reported success — shipped to npm and caught by comparing the
 *  handlers with `src/fux/mcp.py` rather than by a client complaining. */
function fuxSearch(root, args, top) {
  const query = args.query ?? "";
  // `[mcp] top` is this surface's default, because a tool call has no flags.
  // An explicit `k` still wins, exactly as a CLI flag does. ⚠ There is no
  // `[mcp] band`: the confidence block below is UNCONDITIONAL here.
  const k = Number(args.k || top);
  // W-109. Same slot as the CLI's `--expand`, same weight, same guard: a
  // document matching only expansion terms is dropped in `rank()`.
  const expand = String(args.expand ?? "");
  // W-161 — this surface takes BOTH tiers. An agent is the reader the related
  // tier was built for: it cannot run `fux graph` as a follow-up the way a
  // person can, and `next` has been telling it to call `fux_related` for
  // neighbours since the tool existed.
  const { results, related, confidence } = runQuery(root, query, k, {
    wantConfidence: true, expand,
  });
  const records = results.length ? recordsById(root) : new Map();
  const out = results.map((r) => {
    const record = records.get(r.id) ?? {};
    return {
      path: r.loc,
      title: r.title,
      score: pyRound(r.score, 6),
      // The hash the ranking was computed against. An agent that reads the
      // file and gets a different sha knows the index is behind WITHOUT having
      // to trust it — the whole premise of ranking from an index and fetching
      // from the owner.
      sha: record.sha ?? "",
      archived: r.archived,
      superseded: Boolean(record.superseded ?? false),
      // W-153 — the committed git timestamp in whole unix seconds, or `null`
      // for a document outside git history. Always present; `null` is a claim.
      mtime: record.mtime ?? null,
      // W-84 — free here: the record is already in hand for `sha`. Always
      // present, `[]` when nothing matches, because an absent key would be
      // indistinguishable from an older server.
      headings: headingsFor(record, query),
    };
  });
  return {
    results: out,
    // 🔴 **Its own key, never merged into `results`.** These documents matched
    // NO query word; they are here because the documents above link to them.
    // An agent reading them as matches cites a document the question's own
    // words never reached — with a real path and a real sha beside it, which
    // is the most convincing shape a wrong answer has.
    //
    // **Unconditional, like `confidence`:** a tool call cannot pass a flag, so
    // an absent key could only mean *this server predates the tier* (W-48).
    // NOT `score` — a related document has none, and naming the walk mass
    // `score` would make every agent that sorts on it interleave the lists.
    related: (related ?? []).map((r) => ({
      path: r.loc, title: r.title, mass: pyRound(r.mass, 6),
      archived: r.archived, route: r.route,
    })),
    // Node has no accelerator; the scan is the only path, and saying anything
    // else would be a lie about which one answered.
    ranked_by: "scan",
    // **The single most important key on this surface**: an agent handed a
    // ranked list cannot otherwise tell "these documents answer your question"
    // from "these are the closest things in a corpus that never discusses it".
    confidence: confidence ? confidence.asDict() : null,
    next: "call fux_passage with a path to read a span, or fux_related for neighbours. "
      + "`related` here is already the neighbourhood of THIS query's answers -- "
      + "documents no query word matched, so never cite one as a match without "
      + "reading it with fux_passage first",
  };
}

function fuxPassage(root, args) {
  const rel = args.path ?? "";
  // Refuse to escape the repo. `resolve` collapses `..` BEFORE the check, so a
  // traversal cannot slip through by being spelled differently.
  const target = resolvePath(root, rel);
  const base = resolvePath(root);
  // 🔴 `relative`, not `startsWith(base + "/")` — the separator is `\` on
  // Windows, so the prefix test matched NOTHING there and `fux_passage`
  // refused every path in the repository, including the one it had just cited.
  // Python's twin used `Path.is_relative_to` and was always correct; the
  // differential arm caught the divergence on its first Windows run.
  const inside = relative(base, target);
  if (inside !== "" && (isAbsolute(inside) || inside.split(sep)[0] === "..")) {
    throw new FuxError(`'${rel}' resolves outside the repository`);
  }
  let raw;
  try {
    if (!statSync(target).isFile()) throw new Error("not a file");
    raw = readFileSync(target);
  } catch {
    throw new FuxError(`'${rel}' is not a file in this repository`);
  }
  const lines = splitLines(raw.toString("utf8"));
  const start = Math.max(1, Number(args.line_start || 1));
  const end = Math.min(lines.length, Number(args.line_end || lines.length));
  return {
    path: rel,
    line_start: start,
    line_end: end,
    sha: contentSha(raw),
    text: lines.slice(start - 1, end).join("\n"),
  };
}

/** One document's edges, both directions.
 *
 * 🔴 **Not a seeded walk**, though W-160's gap-check row asked for it to be
 * *"re-implemented over `graph --seed` (same output, one code path)"*. A PPR
 * neighbourhood returns ranked nodes the document never mentioned; this
 * returns the edges the document states. The output cannot be both.
 *
 * **The row's second half stands and is done here**: the inbound scan lifts
 * `Edge`s through `edgesFromRecords` and reads `Graph`'s own adjacency, so
 * *what points at this* has ONE definition rather than a third comprehension
 * beside the plane and the verbs. Twin of `mcp.py::_related`; built in memory,
 * never from `.fux/runtime/graph.json`, because MCP answers in a clone with no
 * build. */
function fuxRelated(root, args) {
  const rel = args.path ?? "";
  const docId = rel.startsWith("file:") || rel.startsWith("url:") ? rel : `file:${rel}`;
  const records = recordsById(root);
  const record = records.get(docId);
  if (record === undefined) throw new FuxError(`'${rel}' is not in the index`);

  const graph = new Graph(edgesFromRecords([...records.values()]));
  const inbound = graph.edges
    .filter((e) => e.dst === docId && records.has(e.src))
    .map((e) => ({ path: records.get(e.src).loc, kind: e.kind }));
  inbound.sort((a, b) => (a.kind < b.kind ? -1 : a.kind > b.kind ? 1
    : cmpCodePoints(a.path, b.path)));
  return {
    path: record.loc,
    title: record.title ?? "",
    archived: Boolean(record.archived ?? false),
    superseded: Boolean(record.superseded ?? false),
    outbound: (record.edges ?? []).map((e) => ({
      path: e.dst.startsWith("file:") ? e.dst.slice(5) : e.dst, kind: e.kind,
    })),
    inbound,
  };
}

export function handle(root, message, top) {
  const method = message.method;
  const id = message.id;
  // A notification has no id and MUST NOT be answered.
  if (id === undefined || id === null) return null;

  if (method === "initialize") {
    return ok(id, {
      protocolVersion: PROTOCOL_VERSION,
      capabilities: { tools: {} },
      serverInfo: { name: "fux", version: "3.0.0-alpha.5" },
    });
  }
  if (method === "tools/list") return ok(id, { tools: tools(top) });
  if (method === "tools/call") {
    const params = message.params || {};
    const handlers = {
      fux_search: (r, a) => fuxSearch(r, a, top),
      fux_passage: fuxPassage,
      fux_related: fuxRelated,
    };
    const handler = handlers[params.name];
    if (handler === undefined) return err(id, -32602, `unknown tool ${JSON.stringify(params.name)}`);
    let payload;
    try { payload = handler(root, params.arguments || {}); }
    catch (e) {
      // A tool-level failure is reported INSIDE the result with `isError`, not
      // as a JSON-RPC error: the agent should see it as a tool that answered
      // "no", which it can act on, rather than as a transport fault, which it
      // usually cannot. Only an EXPECTED failure — anything else is a bug and
      // must not be dressed up as an answer.
      if (!(e instanceof FuxError)) throw e;
      return ok(id, { content: [{ type: "text", text: String(e.message) }], isError: true });
    }
    return ok(id, {
      content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
      structuredContent: payload,
    });
  }
  return err(id, -32601, `unknown method ${JSON.stringify(method)}`);
}

export function runMcp(root, args) {
  // `[mcp] top` is resolved ONCE here, at start-up, and threaded into every
  // message handled on this connection — never re-read per search, in a warm
  // process whose entire premise is staying resident.
  const cfg = args.outputConfig ?? loadOutput(root, { enabled: args.noOutputConfig !== true });
  const top = Number(cfg.resolveMcp("top", args.top ?? null));
  const rl = createInterface({ input: process.stdin, terminal: false });
  rl.on("line", (line) => {
    if (!line.trim()) return;
    let message;
    try { message = JSON.parse(line); }
    catch { process.stdout.write(JSON.stringify(err(null, -32700, "parse error")) + "\n"); return; }
    const response = handle(root, message, top);
    if (response !== null) process.stdout.write(JSON.stringify(response) + "\n");
  });
  return 0;
}
