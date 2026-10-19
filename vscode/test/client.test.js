// The extension's LSP client (W-286, SR-VSCODE): framing across chunk
// boundaries, request/response routing, notifications, a server-sent request,
// and what an exited server does to pending requests. A fake transport, so
// no `fux` and no VS Code are needed.
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { Framer, LspClient, frame } = require("../src/client");

function fakeTransport() {
  const t = { written: [], data: null, exit: null, killed: false };
  t.write = (buf) => t.written.push(...new Framer().push(buf));
  t.onData = (fn) => { t.data = fn; };
  t.onExit = (fn) => { t.exit = fn; };
  t.kill = () => { t.killed = true; };
  return t;
}

test("a framer reassembles messages split anywhere, including inside a multibyte character", () => {
  const bytes = Buffer.concat([frame({ id: 1, result: "café" }), frame({ method: "x", params: {} })]);
  const framer = new Framer();
  const got = [];
  for (let i = 0; i < bytes.length; i += 3) got.push(...framer.push(bytes.subarray(i, i + 3)));
  assert.deepEqual(got, [{ id: 1, result: "café" }, { method: "x", params: {} }]);
});

test("Content-Length counts bytes, not characters", () => {
  const head = frame({ r: "é" }).toString("utf8").split("\r\n")[0];
  assert.equal(head, `Content-Length: ${Buffer.byteLength(JSON.stringify({ r: "é" }))}`);
});

test("a request resolves with its own response, whatever the order", async () => {
  const t = fakeTransport();
  const client = new LspClient(t);
  const a = client.request("workspace/symbol", { query: "a" });
  const b = client.request("textDocument/hover", {});
  const [ra, rb] = t.written;
  t.data(frame({ jsonrpc: "2.0", id: rb.id, result: null }));
  t.data(frame({ jsonrpc: "2.0", id: ra.id, result: [{ name: "A" }] }));
  assert.deepEqual(await a, [{ name: "A" }]);
  assert.equal(await b, null);
});

test("an error response rejects", async () => {
  const t = fakeTransport();
  const client = new LspClient(t);
  const p = client.request("nope", {});
  t.data(frame({ jsonrpc: "2.0", id: t.written[0].id, error: { code: -32601, message: "unknown" } }));
  await assert.rejects(p, /unknown/);
});

test("a notification is emitted by method name", () => {
  const t = fakeTransport();
  const client = new LspClient(t);
  let seen;
  client.on("textDocument/publishDiagnostics", (p) => { seen = p; });
  t.data(frame({ jsonrpc: "2.0", method: "textDocument/publishDiagnostics", params: { uri: "u", diagnostics: [] } }));
  assert.deepEqual(seen, { uri: "u", diagnostics: [] });
});

test("a request from the server is answered, never left hanging", () => {
  const t = fakeTransport();
  new LspClient(t);
  t.data(frame({ jsonrpc: "2.0", id: 42, method: "workspace/configuration", params: {} }));
  assert.equal(t.written[0].id, 42);
  assert.equal(t.written[0].error.code, -32601);
});

test("start sends initialize, then the initialized notification", async () => {
  const t = fakeTransport();
  const client = new LspClient(t);
  const started = client.start("file:///repo", { name: "test" });
  assert.equal(t.written[0].method, "initialize");
  assert.equal(t.written[0].params.rootUri, "file:///repo");
  t.data(frame({ jsonrpc: "2.0", id: t.written[0].id, result: { capabilities: {} } }));
  await started;
  assert.equal(t.written[1].method, "initialized");
  assert.equal(t.written[1].id, undefined);
});

test("an exited server rejects what was pending and refuses what comes next", async () => {
  const t = fakeTransport();
  const client = new LspClient(t);
  const p = client.request("workspace/symbol", { query: "x" });
  t.exit(1);
  await assert.rejects(p, /exited/);
  await assert.rejects(client.request("workspace/symbol", {}), /not running/);
});

test("stop is shutdown then exit", async () => {
  const t = fakeTransport();
  const client = new LspClient(t);
  const stopped = client.stop();
  assert.equal(t.written[0].method, "shutdown");
  t.data(frame({ jsonrpc: "2.0", id: t.written[0].id, result: null }));
  await stopped;
  assert.equal(t.written[1].method, "exit");
});
