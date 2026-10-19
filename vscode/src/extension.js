// Fux for VS Code (W-286, SR-VSCODE) — the index in the editor, two ways:
//
// - **MCP.** Every workspace folder holding `.fux/index/` gets `fux mcp`
//   registered through VS Code's own MCP API, so agent mode sees fux_search,
//   fux_passage and fux_related with no `.vscode/mcp.json` to write.
// - **LSP.** The same folders run `fux lsp`: workspace symbols are a fux
//   search, a link shows its target's state on hover, Find All References is
//   the document's backlinks, and a link to an archived or superseded document
//   is a warning.
//
// Neither starts anything fux does not already ship: both are `fux` verbs, so
// the extension holds no index logic and needs `fux` on PATH (`fux.command`).
"use strict";

const fs = require("fs");
const path = require("path");
const vscode = require("vscode");
const { LspClient } = require("./client");

const SECTION = "fux";
const MCP_PROVIDER = "fux";
const MARKDOWN = { scheme: "file", language: "markdown" };

let output;
let diagnostics;
const clients = new Map(); // folder uri string -> LspClient

function settings() {
  const cfg = vscode.workspace.getConfiguration(SECTION);
  return {
    command: cfg.get("command"),
    mcp: cfg.get("mcp.enable"),
    lsp: cfg.get("lsp.enable"),
    debounce: cfg.get("search.debounceMs"),
  };
}

function fuxFolders() {
  return (vscode.workspace.workspaceFolders || []).filter(
    (f) => f.uri.scheme === "file" && fs.existsSync(path.join(f.uri.fsPath, ".fux", "index")),
  );
}

function version(context) {
  return context.extension.packageJSON.version;
}

// -- MCP ----------------------------------------------------------------------

function registerMcp(context) {
  if (!vscode.lm || typeof vscode.lm.registerMcpServerDefinitionProvider !== "function") {
    output.appendLine("this VS Code has no MCP API (1.101 or later) — MCP not registered");
    return;
  }
  const changed = new vscode.EventEmitter();
  context.subscriptions.push(
    changed,
    vscode.lm.registerMcpServerDefinitionProvider(MCP_PROVIDER, {
      onDidChangeMcpServerDefinitions: changed.event,
      provideMcpServerDefinitions: () => {
        const { command, mcp } = settings();
        if (!mcp) return [];
        return fuxFolders().map((folder) => {
          const server = new vscode.McpStdioServerDefinition(
            `fux · ${folder.name}`, command, ["mcp"], {}, version(context),
          );
          server.cwd = folder.uri;
          return server;
        });
      },
      resolveMcpServerDefinition: (server) => server,
    }),
    vscode.workspace.onDidChangeWorkspaceFolders(() => changed.fire()),
    vscode.workspace.onDidChangeConfiguration((e) => {
      if (e.affectsConfiguration(SECTION)) changed.fire();
    }),
  );
}

// -- LSP ----------------------------------------------------------------------

function toRange(r) {
  return new vscode.Range(r.start.line, r.start.character, r.end.line, r.end.character);
}

function toLocation(l) {
  return new vscode.Location(vscode.Uri.parse(l.uri), toRange(l.range));
}

function clientFor(uri) {
  const folder = vscode.workspace.getWorkspaceFolder(uri);
  return folder ? clients.get(folder.uri.toString()) : undefined;
}

function tracked(doc) {
  return doc.uri.scheme === "file" && doc.languageId === "markdown" && clientFor(doc.uri);
}

function open(client, doc) {
  client.notify("textDocument/didOpen", {
    textDocument: { uri: doc.uri.toString(), languageId: doc.languageId, version: doc.version, text: doc.getText() },
  });
}

async function startClient(context, folder) {
  const { command } = settings();
  const client = LspClient.spawn(command, ["lsp"], folder.uri.fsPath);
  client.on("log", (line) => output.appendLine(line));
  client.on("exit", (code) => {
    output.appendLine(`fux lsp (${folder.name}) exited: ${code}`);
    if (clients.get(folder.uri.toString()) === client) clients.delete(folder.uri.toString());
  });
  client.on("textDocument/publishDiagnostics", (p) => {
    diagnostics.set(vscode.Uri.parse(p.uri), p.diagnostics.map((d) => {
      const item = new vscode.Diagnostic(toRange(d.range), d.message, d.severity - 1);
      item.source = d.source;
      return item;
    }));
  });
  clients.set(folder.uri.toString(), client);
  try {
    await client.start(folder.uri.toString(), { name: "fux-vscode", version: version(context) });
  } catch (err) {
    clients.delete(folder.uri.toString());
    output.appendLine(`fux lsp did not start in ${folder.name}: ${err.message} — is \`${command}\` on PATH? (setting fux.command)`);
    return;
  }
  for (const doc of vscode.workspace.textDocuments) {
    if (vscode.workspace.getWorkspaceFolder(doc.uri) === folder && tracked(doc)) open(client, doc);
  }
}

async function startAll(context) {
  if (!settings().lsp) return;
  await Promise.all(fuxFolders().map((f) => startClient(context, f)));
}

async function stopAll() {
  const running = [...clients.values()];
  clients.clear();
  diagnostics.clear();
  await Promise.all(running.map((c) => c.stop()));
}

async function search(query) {
  const all = await Promise.all([...clients.values()].map(
    (c) => c.request("workspace/symbol", { query }).catch(() => []),
  ));
  return all.flat().filter(Boolean);
}

function registerLsp(context) {
  diagnostics = vscode.languages.createDiagnosticCollection(SECTION);
  context.subscriptions.push(
    diagnostics,
    vscode.languages.registerWorkspaceSymbolProvider({
      provideWorkspaceSymbols: async (query) => (await search(query)).map((s) => new vscode.SymbolInformation(
        s.name, vscode.SymbolKind.File, s.containerName || "", toLocation(s.location),
      )),
    }),
    vscode.languages.registerHoverProvider(MARKDOWN, {
      provideHover: async (doc, pos) => {
        const client = clientFor(doc.uri);
        if (!client) return undefined;
        const r = await client.request("textDocument/hover", {
          textDocument: { uri: doc.uri.toString() }, position: { line: pos.line, character: pos.character },
        });
        return r ? new vscode.Hover(new vscode.MarkdownString(r.contents.value), r.range && toRange(r.range)) : undefined;
      },
    }),
    vscode.languages.registerReferenceProvider(MARKDOWN, {
      provideReferences: async (doc, pos) => {
        const client = clientFor(doc.uri);
        if (!client) return [];
        const refs = await client.request("textDocument/references", {
          textDocument: { uri: doc.uri.toString() }, position: { line: pos.line, character: pos.character },
          context: { includeDeclaration: false },
        });
        return (refs || []).map(toLocation);
      },
    }),
    vscode.workspace.onDidOpenTextDocument((doc) => {
      const client = tracked(doc);
      if (client) open(client, doc);
    }),
    vscode.workspace.onDidChangeTextDocument((e) => {
      const client = tracked(e.document);
      if (client) client.notify("textDocument/didChange", {
        textDocument: { uri: e.document.uri.toString(), version: e.document.version },
        contentChanges: [{ text: e.document.getText() }],
      });
    }),
    vscode.workspace.onDidSaveTextDocument((doc) => {
      const client = tracked(doc);
      if (client) client.notify("textDocument/didSave", { textDocument: { uri: doc.uri.toString() } });
    }),
    vscode.workspace.onDidCloseTextDocument((doc) => {
      const client = tracked(doc);
      if (client) client.notify("textDocument/didClose", { textDocument: { uri: doc.uri.toString() } });
    }),
  );
}

// -- commands -----------------------------------------------------------------

function searchCommand() {
  const pick = vscode.window.createQuickPick();
  pick.placeholder = "Search the fux index — a question, not a file name";
  pick.matchOnDescription = true;
  let timer;
  pick.onDidChangeValue((value) => {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      pick.busy = true;
      const found = value.trim() ? await search(value) : [];
      // `alwaysShow`: these are RANKED results, and the quick pick's own fuzzy
      // filter would drop a document whose title does not spell the query.
      pick.items = found.map((s) => ({
        label: s.name, description: s.containerName, alwaysShow: true, location: s.location,
      }));
      pick.busy = false;
    }, settings().debounce);
  });
  pick.onDidAccept(async () => {
    const [item] = pick.selectedItems;
    pick.hide();
    if (!item) return;
    const loc = toLocation(item.location);
    await vscode.window.showTextDocument(loc.uri, { selection: loc.range });
  });
  pick.onDidHide(() => pick.dispose());
  pick.show();
}

async function activate(context) {
  output = vscode.window.createOutputChannel("Fux");
  context.subscriptions.push(output);
  registerMcp(context);
  registerLsp(context);
  context.subscriptions.push(
    vscode.commands.registerCommand("fux.search", searchCommand),
    vscode.commands.registerCommand("fux.restart", async () => {
      await stopAll();
      await startAll(context);
    }),
    vscode.commands.registerCommand("fux.showOutput", () => output.show()),
    vscode.workspace.onDidChangeWorkspaceFolders(async () => {
      await stopAll();
      await startAll(context);
    }),
  );
  await startAll(context);
}

async function deactivate() {
  if (diagnostics) await stopAll();
}

module.exports = { activate, deactivate };
