# ANALYSIS — supersession recovery (handoff 0006 DoD 8)

**Diagnosis:** the supersession feature works exactly as the accepted compare-doc
verdict specifies — it **annotates** without reordering, and `answer` **prefers
the successor** when both are retrieved. But its reach is bounded twice over, so
the honest recovery on the original 9/12 `find`-inversions is **partial and
small at the `answer` level: 1 fully corrected, 1 more de-cited.** Do not read
this as "9/12 fixed" — `find` ranking is deliberately unchanged, and only 3 of
those 9 even carry a marker.

## The two bounds on recovery (both are by-design, not bugs)

1. **Marker coverage: 3 of 9.** Only 5 of 12 stale docs carry
   `superseded_by:`, and only 3 of those 5 coincide with a `find`-inversion
   (pairs 0, 5, 11). The other 6 inversions use dated inline prose or no marker.
   A deterministic, no-model engine cannot act on those — the documented,
   accepted limit.

2. **Retrieval must land the successor.** `prefer_current` drops the stale
   chunk only when the resolved successor is **also in the pool `answer`
   actually retrieved** (pool = 10). If the query's own retrieval doesn't
   surface the current doc, there is nothing to prefer. This bites pair 5.

## Pair-by-pair, at the answer level

- **Pair 0 (settlement) — the clean win.** Before, `answer` led with the retired
  T+3 ADR; both docs were in the pool; after, the T+3 chunk is dropped and the
  answer leads with the current T+2 ADR. This is precisely the intended fix and
  it fires end-to-end.

- **Pair 5 (authentication) — partial.** The stale `legacy-api-keys` doc was
  cited only as the 5th source; `prefer_current` removes it. But the answer's
  *lead* source is an unrelated doc (`0007-client-supplied-idempotency-keys`),
  and the current `authentication.md` sits mid-list both before and after. So
  the retired doc stops being served, yet the answer is **not corrected to the
  current policy** — the real defect here is weak retrieval for this query, which
  supersession preference cannot repair.

- **Pair 11 (reconciliation) — already answer-correct.** Despite being a
  `find`-inversion (stale ranked #1), `answer` already led with the current
  doc 0016 before the fix, because the current doc's chunks scored higher at the
  sentence level. `prefer_current` changed nothing. This is the clearest example
  of why `find`-inversions and `answer`-correctness are **different metrics** —
  and why recovering `answer` does not require reordering `find`.

- **Pairs 2, 9 (marked, non-inversions).** Pair 2 improved (stale de-cited)
  though it was never one of the 9. Pair 9 is inert: its stale doc isn't
  retrieved for the query, its marker points at ADR 0011 (not the eval's current
  webhooks.md), and the answer actually serves a *different, unmarked* legacy
  doc — a case no marker on 0004 can touch.

## Specific fux improvements (each graduates to a proposal, not this change)

- **S1 — the residual is a retrieval problem, not a supersession one.** Pairs 5
  and 9 show that even with a correct marker, `answer` can lead with an unrelated
  or differently-retired doc because the current doc never ranks well. The lever
  is the deferred **Finding-2 chunk-level dense codes** (handoff §3), which would
  raise the current doc into the pool. Repro: `evidence/dump_supersession.py`
  prints `current_in_pool` / `target_in_pool` per pair.

- **S2 — inline/dated supersession is the 6-pair residual.** The 6 unmarked
  inversions are unreachable without a model. The only $0 path is authoring
  `superseded_by:` into those legacy docs — a corpus-hygiene action, not an
  engine change. Worth stating in docs as the operator's half of the contract.

- **S3 — this is Option B's (margin/down-rank) reopen-trigger territory, and it
  does NOT fire.** The compare doc defers fusion down-ranking pending a *second
  realistic corpus*. This run is still the first corpus; annotation-not-reorder
  held; nothing here argues for reopening B yet. Record and hold.

## What this run does NOT claim

- It does not claim `find` should have moved. Unchanged ranking is the accepted
  verdict; the byte-identical ranks are a *pass*, not a regression.
- It does not claim 9/12 recovered. The measured answer-level recovery is 1 full
  + 1 partial of 9. Presenting the 5 markers or the 3 marked inversions as "the
  fix" would overstate it — the handoff explicitly warns against exactly that.
- It does not claim a bug in `prefer_current`. Its guard ("successor must be
  present") is correct and is *why* pair 5/9 don't fully resolve — a retrieval
  limit, not a supersession defect.

## References

- `docs/compare/supersession-handling.compare.md` — annotate-not-reorder verdict;
  Option B deferred to a second corpus.
- `docs/conformance/2026-07-22-acme-payments/evidence/staleness-inversions.json`
  — the original 9/12 `find`-inversion measurement this run recovers against.
- Handoff `docs/handoff/0006-trust-currency-handoff.md` DoD 8 — "recovery is
  expected to be partial … report the real number; do not present partial
  recovery as a fix."
- ADR 0010 (fuxvec binary dense) — the chunk-level-code path (S1) that would
  raise current docs into the answer pool.
