/** The committed FACTS ranking reads. Twin of `src/fux/ingest/priors.py`.
 *
 * Only `supersededIds` has a Node twin: the git half (`git_commit_times`) is an
 * INGEST concern, and Node does not ingest. `mtime` and `superseded` arrive as
 * committed facts on the record, which is the whole reason they are committed —
 * a derivation from local filesystem state would differ per machine and break L3.
 *
 * 🔴 **`recencyMultiplier` lived here until 2026-09-13** and went with
 * `recency_half_life_days` (W-152), as `supersededWeight` went with W-151.
 * Neither fact lost anything: both still break a tie in `query/rank.mjs`.
 */

/** Doc ids that some other document DECLARES it supersedes.
 *  Declared, never inferred — nothing guesses from titles, numbering or dates. */
export function supersededIds(records) {
  const out = new Set();
  const known = new Set(records.map((r) => r.id));
  for (const record of records) {
    for (const edge of record.edges || []) {
      if (edge.kind === "supersedes") {
        const dst = edge.dst;
        if (known.has(dst) && dst !== record.id) out.add(dst);
      }
    }
  }
  return out;
}
