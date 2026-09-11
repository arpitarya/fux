#!/usr/bin/env node
// W-107 Phase 0, glibc addendum — the Node half of the exhaustive idf domain probe.
// Reads the hex doubles `idfdomain.py` wrote, applies Math.log, and compares
// against Python's answer bit-for-bit and at the sort key's resolution.
import { readFileSync } from 'node:fs';

const hexToF64 = (h) => {
  const b = Buffer.from(h, 'hex');
  return b.readDoubleLE(0);
};
const f64ToHex = (x) => {
  const b = Buffer.alloc(8);
  b.writeDoubleLE(x, 0);
  return b.toString('hex');
};

const data = JSON.parse(readFileSync(process.argv[2], 'utf8'));
console.log(`node ${process.version} on ${process.platform}/${process.arch}`);
for (const [name, rows] of Object.entries(data)) {
  let differ = 0, r9 = 0, maxRel = 0;
  for (const row of rows) {
    const x = hexToF64(row.hex);
    const py = hexToF64(row.py);
    const js = Math.log(x);
    if (f64ToHex(js) !== row.py) {
      differ += 1;
      const rel = py === 0 ? Math.abs(js) : Math.abs((js - py) / py);
      if (rel > maxRel) maxRel = rel;
      if (Math.round(js * 1e9) / 1e9 !== Math.round(py * 1e9) / 1e9) r9 += 1;
    }
  }
  const pct = ((differ / rows.length) * 100).toFixed(4);
  console.log(
    `${name.padEnd(10)}: ${differ}/${rows.length} differ (${pct} %)  max rel ${maxRel.toExponential(3)}  differing at round(9): ${r9}`
  );
}
