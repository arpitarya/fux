/** `fux find` — ranked document locations, one per line, for pipes.
 *  A projection of `ask`, not a second strategy: same scan, same rank().
 *  Twin of `src/fux/query/__init__.py`'s `find` half (R4's one-to-many). */
import { ask } from "../query/scan.mjs";
import { pyRepr } from "../compat/pyfloat.mjs";

export function runFind(root, args) {
  const query = args._.join(" ");
  const top = args.top ?? 5;
  let results = ask(root, query, top);

  if (args.under) {
    const p = args.under.endsWith("/") ? args.under : args.under + "/";
    results = results.filter((r) => r.loc === args.under || r.loc.startsWith(p));
  }

  if (args.json) {
    process.stdout.write(JSON.stringify({ results }, null, 2) + "\n");
  } else {
    for (const r of results) {
      process.stdout.write(`${r.loc}${r.archived ? "  [archived]" : ""}\n`);
    }
  }
  return 0;
}
