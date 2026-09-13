/** The five verdicts, and what each actually claims.
 *  Twin of `src/fux/refer/freshness.py`, minus everything that fetches.
 *
 * 🔴 **Node never fetches** (W-107 R6), so only three of the five are
 * reachable here: `current`/`stale` from reading the local checkout, and
 * `as-ingested`/`unverified` for a `url:` document. `cached` requires a TTL
 * fetch cache, which requires fetching.
 *
 * Owned, with its Python twin, by [SR-URL-FRESHNESS](../../../records/0147_url-freshness.md).
 */

export const CURRENT = "current";
export const STALE = "stale";
export const CACHED = "cached";
export const AS_INGESTED = "as-ingested";
export const UNVERIFIED = "unverified";

export class Verdict {
  constructor({ indexedSha = "", fetchedSha = null, current = null,
                fromAcquired = false, ageSeconds = null, note = "" } = {}) {
    Object.assign(this, { indexedSha, fetchedSha, current, fromAcquired, ageSeconds, note });
    Object.freeze(this);
  }

  /** Checked in this order — each answers a different question, and folding
   *  any two of them together loses the distinction that makes it useful. */
  get label() {
    if (this.ageSeconds !== null) return CACHED;         // we looked RECENTLY
    if (this.fromAcquired) return AS_INGESTED;           // we could not look, but the index is self-consistent
    if (this.current === null) return UNVERIFIED;        // we did not look
    return this.current ? CURRENT : STALE;
  }

  /** The source matched the index, or it did not. */
  static verify(indexedSha, fetchedSha, note = "") {
    if (fetchedSha === null) return new Verdict({ indexedSha, note });
    return new Verdict({ indexedSha, fetchedSha, current: fetchedSha === indexedSha, note });
  }

  /** We could not reach the source; the bytes came from `.fux/acquired/`.
   *  A mismatch HERE is an index defect, not a stale source. */
  static asIngested(indexedSha, blobSha, note = "") {
    return new Verdict({
      indexedSha, fetchedSha: blobSha, current: blobSha === indexedSha,
      fromAcquired: true, note,
    });
  }

  /** We did not look at all. */
  static unverified(indexedSha, note = "") {
    return new Verdict({ indexedSha, note });
  }
}
