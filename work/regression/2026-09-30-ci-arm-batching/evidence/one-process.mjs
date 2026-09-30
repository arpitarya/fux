// Spike: N comparisons in ONE Node process vs N processes. Calls the verb
// handlers the CLI dispatches to, with stdout swallowed.
const ENGINE = process.argv[2];
const { runFind } = await import(ENGINE + "/node/src/verbs/find.mjs");
const { runAsk } = await import(ENGINE + "/node/src/verbs/ask.mjs");
const { findRoot } = await import(ENGINE + "/node/src/config/root.mjs");
const { loadOutput, applyOutputDefaults } = await import(ENGINE + "/node/src/config/output.mjs");
const qs = JSON.parse(process.argv[3]);
const root = findRoot(process.cwd());
const w = process.stdout.write.bind(process.stdout);
const t0 = performance.now();
const per = [];
for (const [verb, q, top] of qs) {
  const s = performance.now();
  const args = { _: [q], json: true, top, noTune: true, band: verb === "ask" ? true : undefined };
  const cfg = loadOutput(root, { enabled: true }); applyOutputDefaults(verb, args, cfg); args.outputConfig = cfg;
  process.stdout.write = () => true;
  verb === "find" ? runFind(root, args) : runAsk(root, args, { compose: true });
  process.stdout.write = w;
  per.push(performance.now() - s);
}
w(JSON.stringify({ total: performance.now() - t0, per }) + "\n");
