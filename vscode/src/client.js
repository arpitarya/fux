// The LSP client the extension speaks to `fux lsp` with (W-286, SR-VSCODE).
//
// Hand-rolled, dependency-free, and free of any `vscode` import so it can be
// unit-tested under plain Node. It is SR-MCP decision 1's reasoning one
// protocol over: LSP's base protocol is a `Content-Length` header and a JSON
// body, and `fux lsp` serves four features — a library would bring every
// feature LSP has to map four of them (work/compare/editor-and-llms-surfaces).
"use strict";

const { spawn } = require("child_process");
const { EventEmitter } = require("events");

const HEADER = "Content-Length";
const SEPARATOR = "\r\n\r\n";
const METHOD_NOT_FOUND = -32601;

// Splits a byte stream into framed messages. Buffers across chunks, because a
// pipe delivers whatever it has — half a header, or three messages at once.
class Framer {
  constructor() {
    this.buffer = Buffer.alloc(0);
  }

  push(chunk) {
    this.buffer = Buffer.concat([this.buffer, chunk]);
    const out = [];
    for (;;) {
      const end = this.buffer.indexOf(SEPARATOR);
      if (end < 0) return out;
      const head = this.buffer.subarray(0, end).toString("ascii");
      const match = new RegExp(`^${HEADER}:\\s*(\\d+)`, "im").exec(head);
      if (!match) throw new Error(`a message with no ${HEADER} header`);
      const start = end + SEPARATOR.length;
      const length = Number(match[1]);
      if (this.buffer.length < start + length) return out;
      out.push(JSON.parse(this.buffer.subarray(start, start + length).toString("utf8")));
      this.buffer = this.buffer.subarray(start + length);
    }
  }
}

function frame(message) {
  const body = Buffer.from(JSON.stringify(message), "utf8");
  return Buffer.concat([Buffer.from(`${HEADER}: ${body.length}${SEPARATOR}`, "ascii"), body]);
}

// One server process. `transport` is injectable — `{ write(buf), onData(fn),
// onExit(fn), kill() }` — so the routing is tested without a subprocess.
class LspClient extends EventEmitter {
  constructor(transport) {
    super();
    this.transport = transport;
    this.framer = new Framer();
    this.nextId = 1;
    this.pending = new Map();
    this.exited = false;
    transport.onData((chunk) => {
      let messages;
      try {
        messages = this.framer.push(chunk);
      } catch (err) {
        this.emit("log", `fux lsp: ${err.message}`);
        return;
      }
      for (const message of messages) this.dispatch(message);
    });
    transport.onExit((code) => {
      this.exited = true;
      for (const { reject } of this.pending.values()) reject(new Error(`fux lsp exited (${code})`));
      this.pending.clear();
      this.emit("exit", code);
    });
  }

  static spawn(command, args, cwd) {
    const child = spawn(command, args, { cwd, stdio: ["pipe", "pipe", "pipe"] });
    const client = new LspClient({
      write: (buf) => child.stdin.write(buf),
      onData: (fn) => child.stdout.on("data", fn),
      onExit: (fn) => {
        child.on("exit", fn);
        child.on("error", (err) => fn(err.message));
      },
      kill: () => child.kill(),
    });
    child.stderr.on("data", (chunk) => client.emit("log", chunk.toString("utf8").trimEnd()));
    return client;
  }

  dispatch(message) {
    const isResponse = message.id !== undefined && message.method === undefined;
    if (isResponse) {
      const waiter = this.pending.get(message.id);
      if (!waiter) return;
      this.pending.delete(message.id);
      if (message.error) waiter.reject(new Error(message.error.message));
      else waiter.resolve(message.result === undefined ? null : message.result);
      return;
    }
    if (message.id !== undefined) {
      // A request FROM the server. fux sends none today; answer rather than
      // stay silent, because a server waiting on a reply would hang.
      this.write({ jsonrpc: "2.0", id: message.id, error: { code: METHOD_NOT_FOUND, message: "unsupported" } });
      return;
    }
    this.emit(message.method, message.params);
  }

  write(message) {
    if (!this.exited) this.transport.write(frame(message));
  }

  request(method, params) {
    if (this.exited) return Promise.reject(new Error("fux lsp is not running"));
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.write({ jsonrpc: "2.0", id, method, params });
    });
  }

  notify(method, params) {
    this.write({ jsonrpc: "2.0", method, params });
  }

  async start(rootUri, clientInfo) {
    const result = await this.request("initialize", {
      processId: process.pid,
      clientInfo,
      rootUri,
      capabilities: { general: { positionEncodings: ["utf-16"] } },
    });
    this.notify("initialized", {});
    return result;
  }

  async stop() {
    if (this.exited) return;
    try {
      await this.request("shutdown", null);
      this.notify("exit", null);
    } catch {
      this.transport.kill();
    }
  }
}

module.exports = { Framer, LspClient, frame };
