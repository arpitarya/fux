/** `--expand` — extra vocabulary the CALLER supplies. Twin of `expand.py`.
 *
 * Fux never invents terms: no model sits anywhere on the query path, so an
 * expansion arrives from whoever asked. What this module owns is the rule that
 * an expansion is a *supplement* — it may lift a document, never define one.
 *
 * Owned, with its Python twin, by [SR-EXPAND](../../../records/0149_expand.md).
 */

/** Every hash to score (originals first), what the user actually asked for,
 *  and at what weight. */
export class Expansion {
  constructor(hashes, required, weights = {}) {
    this.hashes = hashes;
    this.required = required;     // Set — the ORIGINAL query's hashes
    this.weights = weights;       // hash -> multiplier, expansion-only
    Object.freeze(this);
  }
  /** True when this changes nothing — the `Scoring.trivial` precedent. */
  get trivial() { return Object.keys(this.weights).length === 0; }

  /** The identity: every hash required, nothing weighted. */
  static none(queryHashes) {
    const hashes = [...queryHashes];
    return new Expansion(hashes, new Set(hashes), {});
  }

  /** 🔴 The hallucinated-citation guard. A record matching ONLY expansion
   *  terms is not a weak answer to rank low — it is an answer to a question
   *  nobody asked, and `rank()` drops it outright. */
  /** W-168 step 1: an ANCHOR match is a match. A document reachable only by
   *  what its linkers called it carries none of the query's hashes in its own
   *  `terms`, so this guard would drop it before it was ever scored. It is not
   *  a hallucination — `--expand` hands fux words a MODEL invented; an anchor
   *  term is a word a human linker wrote in a committed document. */
  matches(terms, anchorTf = null) {
    for (const h of this.required) if (h in terms) return true;
    if (anchorTf !== null) { for (const h of this.required) if (h in anchorTf) return true; }
    return false;
  }

  weightOf(h) { return this.weights[h] ?? 1.0; }
}

/** Combine the query's hashes with an expansion's, at `weight`.
 *
 * **A hash the original query already carries stays at 1.0**, even when the
 * expansion repeats it — otherwise a caller could quietly demote their own
 * query by mentioning one of its own words. `weight <= 0` is off, and off must
 * be reachable by configuration as well as by omission. */
export function build(queryHashes, expansionHashes, weight) {
  if (weight <= 0 || !expansionHashes || !expansionHashes.length) {
    return Expansion.none(queryHashes);
  }
  const original = [...new Set(queryHashes)];
  const required = new Set(original);
  const extra = [...new Set(expansionHashes)].filter((h) => !required.has(h));
  if (!extra.length) return Expansion.none(original);

  const weights = {};
  for (const h of extra) weights[h] = weight;
  return new Expansion([...original, ...extra], required, weights);
}
