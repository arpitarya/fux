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
 * not a shared read — ADR-MCP decision 11 states why, and what that leaves
 * unguarded once this file ships to npm on its own.
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { createInterface } from "node:readline";
import { ask as scanAsk } from "../query/scan.mjs";
import { recordFor } from "../store/reader.mjs";
import { buildPlane } from "../graph/plane.mjs";
import { iterShardPaths, rawRecordLines } from "../store/reader.mjs";
import { chunk } from "../refer/chunk.mjs";

export const PROTOCOL_VERSION = "2024-11-05";
const HERE = dirname(fileURLToPath(import.meta.url));

let TOOLS = null;
function tools(top) {
  if (TOOLS === null) {
    TOOLS = JSON.parse(readFileSync(join(HERE, "..", "..", "mcp-tools.json"), "utf8")).tools;
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

function allRecords(root) {
  const out = [];
  for (const path of iterShardPaths(root)) {
    const [, lines] = rawRecordLines(path);
    for (const line of lines) out.push(JSON.parse(line.toString("utf8")));
  }
  return out;
}

function fuxSearch(root, args, top) {
  const results = scanAsk(root, args.query ?? "", args.top ?? top);
  return { results: results.map((r) => ({ id: r.id, loc: r.loc, title: r.title, score: r.score, archived: r.archived })) };
}

function fuxPassage(root, args) {
  const record = recordFor(root, args.id);
  if (!record) return { passages: [] };
  // Node never fetches: a `url:` document has no local bytes to chunk.
  if (!record.id.startsWith("file:")) return { passages: [], note: "node never fetches" };
  const { readFileSync: rf, existsSync } = { readFileSync, existsSync: (p) => { try { rf(p); return true; } catch { return false; } } };
  let text;
  try { text = readFileSync(join(root, record.loc), "utf8"); }
  catch { return { passages: [], note: "not in the working tree" }; }
  return {
    passages: chunk(text).map((p) => ({
      loc: p.line_start ? `${record.loc}:L${p.line_start}-L${p.line_end}` : `${record.loc}#p${p.ordinal}`,
      heading: p.heading, text: p.text, ordinal: p.ordinal,
    })),
  };
}

function fuxRelated(root, args) {
  const plane = buildPlane(allRecords(root));
  const id = args.id;
  const community = plane.communityOf(id);
  return {
    id, community,
    members: community ? plane.members(community) : [],
    edges: plane.graph.outEdges(id).map((e) => ({ kind: e.kind, dst: e.dst, grade: e.grade })),
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
      serverInfo: { name: "fux", version: "2.0.0-alpha.7" },
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
  const top = args.top ?? 5;
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
