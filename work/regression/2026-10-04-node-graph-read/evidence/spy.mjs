// Preload: count readFileSync calls on .fux/runtime/graph.json; report on stderr at exit.
import fs from "node:fs";
import { syncBuiltinESMExports } from "node:module";
const real = fs.readFileSync;
let n = 0;
fs.readFileSync = function spied(path, ...rest) {
  if (String(path).endsWith("/.fux/runtime/graph.json")) n++;
  return real.call(this, path, ...rest);
};
syncBuiltinESMExports();
process.on("exit", () => { process.stderr.write(`GRAPHJSON_READS=${n}\n`); });
