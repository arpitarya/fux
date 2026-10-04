// W-259 (b): N comparisons in ONE Node process, the plane built once (with
// once-hook.mjs loaded). Same calls as 2026-09-30-ci-arm-batching's
// one-process.mjs, but stdout is CAPTURED per comparison, not swallowed, so its
// sha256 can be held to the bytes `node fux.mjs` printed for the same job.
import { createHash } from "node:crypto";
const ENGINE = process.argv[2];
const { runFind } = await import(ENGINE + "/node/src/verbs/find.mjs");
const { runAsk } = await import(ENGINE + "/node/src/verbs/ask.mjs");
const { findRoot } = await import(ENGINE + "/node/src/config/root.mjs");
const { loadOutput, applyOutputDefaults } = await import(ENGINE + "/node/src/config/output.mjs");
const qs = JSON.parse(process.argv[3]);
const root = findRoot(process.cwd());
const w = process.stdout.write.bind(process.stdout);
const t0 = performance.now();
const per = [], shas = [];
for (const [verb, q, top] of qs) {
  const s = performance.now();
  const args = { _: [q], json: true, top, noTune: true, band: verb === "ask" ? true : undefined };
  const cfg = loadOutput(root, { enabled: true }); applyOutputDefaults(verb, args, cfg); args.outputConfig = cfg;
  const chunks = [];
  process.stdout.write = (c) => { chunks.push(Buffer.from(c)); return true; };
  try { verb === "find" ? runFind(root, args) : runAsk(root, args, { compose: true }); }
  finally { process.stdout.write = w; }
  per.push(performance.now() - s);
  shas.push(createHash("sha256").update(Buffer.concat(chunks)).digest("hex"));
}
w(JSON.stringify({ total: performance.now() - t0, per, shas, memo: globalThis.__w259 ?? null }) + "\n");
