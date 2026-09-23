#!/usr/bin/env node
/** `fux` — the Node read plane. Reads an index Python wrote; never writes.
 *
 * npm package `fux-engine`, command `fux`, vendored by `fux setup` into
 * `.fux/fux.mjs` so a clone with no Python still answers (W-107 R1/R2).
 */
import { existsSync, realpathSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { findRoot } from "./src/config/root.mjs";
import { runFind } from "./src/verbs/find.mjs";
import { runAsk } from "./src/verbs/ask.mjs";
import { runAnswer } from "./src/verbs/answer.mjs";
import { runExplain, runGraph, runPath } from "./src/verbs/graph.mjs";
import { runMcp } from "./src/verbs/mcp.mjs";
import { FuxError } from "./src/errors.mjs";
import { applyOutputDefaults, loadOutput } from "./src/config/output.mjs";
// 🔴 **The library surface travels with the CLI, and that is what makes ONE
// bundle possible** (L10, records/0011_LAW-10-bundled-output.md). `exports`
// and `bin` in `package.json` both name this file, so `import { open } from
// "fux-engine"` and `fux ask` reach the same artefact. The twin of this
// re-export is `src/fux/__init__.py`'s, and it is deliberately thin: the
// shapes are authored in `src/index.mjs`, which stays `api.py`'s twin.
import { open, Index } from "./src/index.mjs";

const VERSION = "3.0.0-alpha.4";

/** The PII gate's path, spelled here the way `cli.py` and `api.py` spell it.
 *
 * 🔴 **W-107 O1, ruled by Arpit 2026-09-12: Node enforces it identically.**
 * Python refuses every non-exempt verb without `.fux/pii.toml`
 * (SR-PII decision 17). The gate exists because the committed index is
 * redacted, so a Node reader that answered where Python refuses would be a
 * divergence in the PRODUCT, not merely in the code — and this runtime cannot
 * import the Python that carries the rule, so it carries the path itself.
 * `tests/test_cli.py::test_the_node_reader_gates_on_the_same_file` holds this
 * literal equal to the two Python copies. The WORDING below is a
 * transcription of `pii.require`'s, which stays the one place it is authored.
 */
const PII_RULES = [".fux", "pii.toml"];

/** Every verb here reads the index, so every verb is gated. There is no Node
 *  twin of Python's `PII_EXEMPT` — `setup`, `tune`, `output` and `doctor` are
 *  all in `WRITE_VERBS` and never reach this point. */
function requirePiiRules(root) {
  const path = join(root, ...PII_RULES);
  if (existsSync(path) && statSync(path).isFile()) return true;
  process.stderr.write(
    `error: ${PII_RULES.join("/")} is missing, and fux will not run without it ` +
    `(SR-PII decision 17).\n` +
    `       Run \`fux setup\` to write the starter, then review its rules; to redact\n` +
    `       nothing, keep the file with no [[rule]] entries.\n`,
  );
  return false;
}

/** Verbs that exist in Python fux and deliberately not here. A person typing
 *  one has a specific wrong model and deserves the specific correction. */
const WRITE_VERBS = {
  ingest: "writes the index", build: "writes the derived accelerator",
  add: "writes a source line", remove: "writes a source line",
  update: "re-fetches sources", enrich: "writes enrichment",
  setup: "writes .fux/", doctor: "reports on a tree Node cannot fully see",
  hooks: "installs git hooks", daemon: "runs a background re-index",
  tune: "prints or writes tunables", output: "prints or writes output defaults",
  verify: "not implemented until Phase 2 earns the digest path",
};

function parseArgs(argv) {
  // `undefined` means THE FLAG WAS NOT PASSED, which is what lets
  // `.fux/output.toml` supply the default. `false` here would be a claim.
  const out = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--json") out.json = true;
    else if (a === "--top") out.top = parseInt(argv[++i], 10);
    else if (a === "--under") out.under = argv[++i];
    else if (a === "--phrase") out.phrase = argv[++i];
    else if (a === "--all") out.all = true;
    else if (a === "--band") out.band = true;
    else if (a === "--no-sections") out.sections = false;
    // SR-TUNE decision 11: `.fux/tune.toml` is not read AT ALL, so the answer
    // is the engine's own. The "is it me or the config?" switch, and it has to
    // exist in both runtimes or the question can only be asked of one of them.
    else if (a === "--no-tune") out.noTune = true;
    // The same loop one level up: `.fux/output.toml` may not decide whether
    // `.fux/output.toml` is read, so this is a flag and never a key.
    else if (a === "--no-output-config") out.noOutputConfig = true;
    else if (a === "-q") (out.q ||= []).push(argv[++i]);
    else if (a === "--expand") out.expand = argv[++i];
    else if (a === "--no-refer") out.noRefer = true;
    else if (a === "--audit") out.audit = true;
    else if (a === "--hops") out.hops = parseInt(argv[++i], 10);
    // W-160's second atom. Repeatable, and ARGUMENT ORDER is the mass order —
    // the same rank-mass rule the query form applies to top-k.
    else if (a === "--seed") (out.seed ||= []).push(argv[++i]);
    else if (a === "--kinds") out.kinds = argv[++i];
    else if (a === "--link-idf") out.linkIdf = true;
    else if (a === "--max-hops") out.maxHops = parseInt(argv[++i], 10);
    else if (a.startsWith("--")) { out.unknown = a; }
    else out._.push(a);
  }
  return out;
}

function main(argv) {
  const [verb, ...rest] = argv;

  if (verb === "--version" || verb === "-V") {
    // 🔴 The runtime is NAMED. Python fux installs a binary called `fux` too,
    // so on a machine with both, this one line is what makes any bug report
    // unambiguous about which reader answered (W-107 R1a).
    process.stdout.write(`fux ${VERSION} (node ${process.versions.node})\n`);
    return 0;
  }
  if (!verb || verb === "--help" || verb === "-h") {
    process.stdout.write(
      `fux ${VERSION} (node ${process.versions.node}) — the read plane\n\n` +
      `  fux find <query> [--json] [--top N] [--under DIR] [--phrase P] [--all]\n` +
      `  fux ask|lexical|answer|explain|graph|path|mcp      (Phases 2-3)\n` +
      `  fux graph --seed <id> [--seed <id>...]     walk from documents you name\n\n` +
      `Reads an index Python wrote. It never writes and never fetches.\n`,
    );
    return verb ? 0 : 1;
  }
  if (verb in WRITE_VERBS) {
    process.stderr.write(
      `error: \`${verb}\` ${WRITE_VERBS[verb]} — this is fux-engine (node), which only reads.\n` +
      `       Install Python fux and run \`fux ${verb}\`, or see .fux/README.md.\n`,
    );
    return 1;
  }

  const args = parseArgs(rest);
  const root = findRoot(process.cwd());
  if (root === null) {
    process.stderr.write("error: no fux root here — no fux.toml and no .git above this directory.\n");
    return 1;
  }
  // Before dispatch and before anything reads the repository, exactly where
  // `cli.py::main` puts it, so no verb handler has to remember.
  if (!requirePiiRules(root)) return 1;

  // `.fux/output.toml` is folded into `args` ONCE, here, before dispatch —
  // exactly where `cli.py::_apply_output_defaults` does it, so no verb handler
  // has to know the precedence chain exists (W-107 R5).
  try {
    const cfg = loadOutput(root, { enabled: args.noOutputConfig !== true });
    applyOutputDefaults(verb, args, cfg);
    args.outputConfig = cfg;
  } catch (err) {
    if (err instanceof FuxError) {
      process.stderr.write(`error: ${err.message}\n`);
      return err.exitCode;
    }
    throw err;
  }

  // The error contract: internals keep throwing, and the BOUNDARY renders.
  // One `catch` here rather than a `try` per verb — a malformed `.fux/tune.toml`
  // must print the same one-line refusal whichever verb tripped over it.
  try {
    switch (verb) {
      case "find":
        return runFind(root, args);
      case "ask":
        return runAsk(root, args, { compose: true });
      // **W-160's first atom, and W-161 is the change that split it.**
      // `fux lexical` is the lexical core — BM25F, the proximity reranker and
      // `-q` fusion, and NO graph stage, ever (SR-CLI decision 12). It was the
      // same call as `ask` until `ask` grew a tier; now it is the same
      // function with the tier forced off, which is the narrowest possible
      // parting and keeps the freeze checkable in one argument rather than in
      // a second handler that could drift.
      case "lexical":
        return runAsk(root, args, { compose: false });
      case "answer":
        return runAnswer(root, args);
      case "explain":
        return runExplain(root, args);
      case "graph":
        return runGraph(root, args);
      case "path":
        return runPath(root, args);
      case "mcp":
        return runMcp(root, args);
      default:
        process.stderr.write(`error: unknown verb \`${verb}\`. Try \`fux --help\`.\n`);
        return 1;
    }
  } catch (err) {
    if (err instanceof FuxError) {
      process.stderr.write(`error: ${err.message}\n`);
      return err.exitCode;
    }
    throw err;
  }
}

/** Run the CLI only when this file IS the program.
 *
 * 🔴 **Unconditional invocation was safe while the library lived in a separate
 * file and became a BUG the moment one bundle served both** — `import
 * "fux-engine"` would have parsed a caller's `process.argv` and set their exit
 * code. The check is the standard ESM one: compare the resolved entry path
 * with this module's own, through `realpath` so a package manager's `.bin`
 * symlink (npm, pnpm and yarn all make one) resolves to the same file.
 */
function invokedDirectly() {
  const entry = process.argv[1];
  if (entry === undefined) return false;
  const real = (p) => {
    try {
      return realpathSync(p);
    } catch {
      return p;
    }
  };
  return real(entry) === real(fileURLToPath(import.meta.url));
}

if (invokedDirectly()) process.exitCode = main(process.argv.slice(2));

export { open, Index };
