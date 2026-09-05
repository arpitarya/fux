// The Node half of the `log` probe. Reads the exact doubles Python wrote.
import { readFileSync } from "node:fs";

const toF64 = (hex) => {
  const b = Buffer.from(hex, "hex");
  return b.readDoubleLE(0);
};
const toHex = (x) => {
  const b = Buffer.alloc(8);
  b.writeDoubleLE(x, 0);
  return b.toString("hex");
};

const data = JSON.parse(readFileSync(process.argv[2], "utf-8"));
console.log(`node ${process.version} on ${process.platform}/${process.arch}`);
for (const [name, rows] of Object.entries(data)) {
  let differ = 0, maxRel = 0, differR9 = 0;
  for (const row of rows) {
    const x = toF64(row.hex);
    const mine = Math.log(x);
    const theirs = toF64(row.py);
    if (toHex(mine) !== row.py) {
      differ++;
      const rel = theirs === 0 ? Math.abs(mine) : Math.abs(mine - theirs) / Math.abs(theirs);
      if (rel > maxRel) maxRel = rel;
      if (Number(mine.toFixed(9)) !== Number(theirs.toFixed(9))) differR9++;
    }
  }
  const pct = ((differ / rows.length) * 100).toFixed(4);
  console.log(
    `${name.padEnd(5)}: ${differ}/${rows.length} differ (${pct} %)` +
    `  max rel ${maxRel.toExponential(3)}  differing at round(9): ${differR9}`,
  );
}
