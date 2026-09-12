/** The ranking priors' query-time half. Twin of `src/fux/ingest/priors.py`.
 *
 * Only `recencyMultiplier` and `supersededIds` have a Node twin: the git half
 * (`git_commit_times`) is an INGEST concern, and Node does not ingest. `mtime`
 * and `superseded` arrive as committed facts on the record, which is the whole
 * reason they are committed — a derivation from local filesystem state would
 * differ per machine and break L3.
 */

/** A gentle exponential decay, normalised so the newest document is `1.0`.
 *
 * **Bounded to `(0, 1]` by design**: recency can demote an old document and
 * can never promote a new one past a better match. That bound is load-bearing
 * for the accelerator's block bound, not just good manners. */
export function recencyMultiplier(mtime, newest, halfLifeDays) {
  if (halfLifeDays <= 0 || mtime === null || mtime === undefined || newest <= 0) return 1.0;
  const ageDays = Math.max(0.0, (newest - mtime) / 86400.0);
  return Math.pow(0.5, ageDays / halfLifeDays);
}

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
