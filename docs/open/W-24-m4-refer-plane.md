# W-24 — M4: the refer plane

**Status:** OPEN
**Blocked by:** W-22
**Spec:** [`PLAN.md` §M4](../PLAN.md)
**Closes with:** ADR-0007 (reserved) · prediction **R4**
**Model:** **Sonnet** to build against this spec — *but the handoff itself
must be written by Opus*, because two proposals graduate into it and the
API shape they set is expensive to retrofit.

## Read before writing the handoff — non-negotiable

Both proposals graduate here, by their own graduation triggers, and both
shape the refer API's **first** surface:

- [`proposals/caller-set-freshness-policy.md`](../proposals/caller-set-freshness-policy.md)
  — staleness tolerance becomes a caller parameter (`max_age_seconds`,
  `timeout_seconds`), not engine policy. The `never` sentinel is what makes
  a replayed answer reproducible; it is the row that matters.
- [`proposals/token-budget-retrieval.md`](../proposals/token-budget-retrieval.md)
  — the primary limit is a **byte budget** the assembler fills, with `k`
  demoted to a secondary cap. Byte budget, never token budget: carrying a
  tokenizer per model family violates the `$0`/stdlib law.

Evidence base for both: [`proposals/agent-search-landscape.md`](../proposals/agent-search-landscape.md).
Read its **"Benchmark caution"** section before importing any framing from
it — the idea can be right and the vendor evidence for it self-serving at
the same time.

## What lands

- **HTTP (conditional GET) + Confluence adapters — and the cap holds.**
  Core ships exactly these two. More systems arrive through
  [`proposals/mcp-adapters.md`](../proposals/mcp-adapters.md), not code.
- ARC cache keyed `(loc, sha)`, **results-neutral by construction** — the
  same differential discipline W-22 establishes for the accelerator.
- Transient convert + heading-aware chunker + passage re-score on the
  fetched bytes.
- Freshness: every answer stamped; live verification behind
  `[freshness] verify`, fenced network, **default off**.
- **A fetch path for `src:"url"` documents** — this is the debt
  [ADR-0010](../adr/0010-url-source-consumer-middleware.md) recorded when
  the URL source landed early. Verify-time fetch for a middleware-sourced
  doc is undecided and must be decided here.

## Definition of done

- [ ] **R4 measured** on a mock-server bench: cold k=10 ≤ **3 s**, warm
      ≤ **300 ms**.
- [ ] ARC differential test: cached and uncached answers byte-identical.
- [ ] Offline degradation is **honest** — git sources keep full function;
      external sources return a declared staleness, never stale bytes
      presented as fresh.
- [ ] The freshness policy taken is **recorded in the answer bundle**, or a
      replay silently uses a different one.
- [ ] R4's bench is run at three `max_age` settings and shows the policy
      actually moving the index-vs-fetch mix. **If it does not, the knob is
      decoration and gets dropped** — say so rather than shipping it.
- [ ] The budget sweep reports answer-quality-per-byte. Flat across
      budgets ⇒ the greedy assembler is not earning its complexity and
      plain top-k with truncation wins.
- [ ] ADR-0007 written and accepted.

## Open design calls to make deliberately (not silently)

1. **Does a timed-out fetch fail the query or degrade it?** Degrading is
   right for agents and wrong for `--audit` — which means the answer is
   "policy, per caller", the proposal's own argument one level down.
2. **Does the byte budget bound the citations or the whole rendered
   answer** (headers, locators, ranking explanation)? Bounding the whole
   thing is the honest reading of "fits in my context", and the harder one.
3. The verify-time fetch path for `src:"url"` docs (above).

## Hazards

- Deterministic tie-breaking in the assembler is **mandatory**: equal
  score-per-byte resolves by `(score, sha, locator)`, never by set
  iteration order.
- Age is measured against the ledger's recorded `sha@index` provenance,
  **not wall clock at query time** — the no-wall-clock law still binds.
- Knob sprawl: two integers is the whole freshness surface. A third means
  the policy belongs in config, not in the query.
- A short high-scoring passage crowding out the one long passage that
  answers the question — the per-citation floor stops it and needs a real
  test, not an assertion.
