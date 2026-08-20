# W-24 — M4: the refer plane

**Status:** OPEN
**Blocked by:** — (W-22 was M2, the T1 accelerator; it **shipped as `v0.32.0`** on 2026-08-12. Stale blocker cleared 2026-08-19)

> **2026-08-18 — M4 has no live build spec.** The `v0.33.0` handoff/prompt pair
> written for it was archived with the whole handoff directory, and an archived
> doc may not ground live work. Whoever starts M4 **writes a fresh spec into
> this file**; the archived pair
> (`archive/handoff/v0.33.0-m4-refer-plane-*.md`) may be read for ideas and
> named, never cited. The Opus-writes-the-spec rule below still holds.
**Spec:** this file — see §Scope below (migrated from the retired `PLAN.md`, 2026-08-18)
**Closes with:** **`ADR-REFER`** (reserved) · prediction **R4**. **Reserved by NAME, never by number** — a number is a filename ordinal assigned when the record is written (Arpit, 2026-08-19, closing W-33).
**Model:** **Sonnet** to build against this spec — *but the handoff itself
must be written by Opus*, because two proposals graduate into it and the
API shape they set is expensive to retrofit.

## The spec — written 2026-08-20 (Opus), and this file is now it

> The 2026-08-18 note below said M4 had no live build spec and that whoever
> started it had to write one. **This section is that spec.** The archived
> handoff pair was read for ideas and is named, never cited.

### The decision that shapes everything else: fux still does not fetch

The obvious reading of "HTTP + Confluence adapters" is *put an HTTP client in
`src/fux/refer/`*. **That is wrong, and it would breach three things at once**
— L1 (`$0`, stdlib-only runtime), L4 (offline by default), and the adapter cap.

The engine already solved this once. [ADR-FETCHER](../../docs/adr/0019_fetcher.md)
established that **the consumer owns the fetcher file** and fux loads it by
path and calls `fetch(url) -> str`; `src/fux/` holds zero network lines, and
`ingest/urlsrc.py` is fux's half of that contract.

**M4 reuses that contract rather than inventing a second one.** So:

| the old plan said | M4 actually ships |
|---|---|
| an HTTP adapter in core | the **already-shipped** `.fux/fetchers/http.py`, called through the same contract |
| a Confluence adapter in core | a third **template** in `src/fux/templates/`, written into the consumer's repo by `fux setup` |
| network in the refer plane | `refer/` loads a fetcher and calls it; it imports no transport |

**This is the single most important line in this spec.** A second fetch
mechanism inside the refer plane would make ADR-FETCHER's veto fire on its own
successor, and it is exactly the kind of thing that looks like progress.

### What lands, in dependency order

**1. `refer/source.py` — where a document's bytes come from.**
Resolve a doc id to a *fetch strategy*: `file:` ids read the local checkout
(free, offline, always available); `url:` ids go through the consumer fetcher
contract. This is also where **[ADR-URL-INGEST](../../docs/adr/0008_url-ingest.md)'s
recorded debt is paid** — the verify-time fetch path for `src:"url"` documents,
which that record deferred and this milestone must decide. **Decide it as: the
same fetcher the URL was ingested with**, resolved from `.fux/sources/urls`,
because a document fetched two different ways is two different documents.

**2. `refer/freshness.py` — the caller's policy, not the engine's.**
Graduating [`../proposals/caller-set-freshness-policy.md`](../proposals/caller-set-freshness-policy.md).
Two integers and one sentinel, and **the surface is closed at that**:

- `max_age_seconds` — below it, answer from the index; above it, fetch.
- `timeout_seconds` — bounds the fetch; on expiry, **degrade with disclosure**.
- `never` — forbid fetching outright. **This is the row that matters**: it is
  what makes a replayed answer reproducible, and it is what `--audit` and CI
  use.

**Age is computed against the ledger's recorded provenance, never wall clock
at query time.** The no-wall-clock law binds here or the whole plane stops
being deterministic. A third knob means the policy belongs in config, not in
the query — that is the knob-sprawl hazard, and it is a hard stop.

**3. `refer/arc.py` — the content cache, keyed `(loc, sha)`.**
ARC is already decided ([cache-policy compare doc](../compare/cache-policy.compare.md));
this builds it. Byte-budgeted, recency by **monotonic counter** rather than
clock, and **results-neutral by construction** — the same differential
discipline M2 established for the accelerator. The DoD's differential test is
*cached vs uncached answers byte-identical*, and it is not optional.

**4. `refer/chunk.py` — heading-aware chunking on the fetched bytes.**
Transient: chunks are never written anywhere (L2). The chunker is the reason
the byte budget can be honest — it knows the *real* size of every candidate at
assembly time rather than estimating from index statistics.

**5. `refer/rescore.py` — passage scoring on fetched bytes.**
Reuse `query/bm25f.py`'s saturation; do **not** write a second scorer. BM25F
means weight-then-saturate once, never a per-field sum.

**6. `refer/assemble.py` — the byte budget.**
Graduating [`../proposals/token-budget-retrieval.md`](../proposals/token-budget-retrieval.md).
Greedy by score-per-byte under a byte budget, with `k` demoted to a secondary
cap. **Byte budget, never token budget** — carrying a tokenizer per model
family violates L1, and that is not a preference.

Three properties are mandatory, not nice-to-have:
- **Deterministic ties** — equal score-per-byte resolves by `(score, sha,
  locator)`, never by set iteration order.
- **A per-citation floor**, so a short high-scoring passage cannot crowd out
  the one long passage that answers the question. This needs a real test, not
  an assertion in a docstring.
- **A per-document cap**, so one document cannot consume the whole budget.

### The three open design calls, decided

The record must decide these deliberately rather than let the code decide them:

1. **A timed-out fetch degrades, it does not fail** — *by default*. But
   `--audit` wants the opposite, which means the honest answer is
   **"policy, per caller"**: the timeout branch is part of the freshness policy
   the caller sets, and **the policy taken is recorded in the answer bundle**.
   A replay that silently used a different policy is the failure this closes.
2. **The byte budget bounds the whole rendered answer**, not just the
   citations — headers, locators and the ranking explanation included. That is
   the honest reading of *"fits in my context"*, and it is the harder one.
3. **Verify-time fetch for `src:"url"` docs** — decided in component 1 above.

### Definition of done (supersedes the list below where they differ)

- [ ] `refer/` implements components 1–6; **no network import anywhere in
      `src/fux/`** — the existing import-fence test must still pass unchanged.
- [ ] **ARC differential test**: cached and uncached answers byte-identical.
- [ ] **Offline degradation is honest**: `file:` sources keep full function;
      external sources return a *declared* staleness, never stale bytes
      presented as fresh.
- [ ] The freshness policy taken is **in the answer bundle**, per citation.
- [ ] The per-citation floor has a test that fails without it.
- [ ] **R4 measured** on a mock-server bench: cold k=10 ≤ **3 s**, warm ≤
      **300 ms**. ⚠ **See the blocker below.**
- [ ] R4's bench run at three `max_age` settings, showing the policy moves the
      index-vs-fetch mix. **If it does not, the knob is decoration and gets
      dropped** — say so rather than shipping it.
- [ ] The budget sweep reports answer-quality-per-byte. Flat across budgets ⇒
      the greedy assembler is not earning its complexity and plain top-k with
      truncation wins.
- [ ] `ADR-REFER` written and accepted.

### ⚠ Blocker on the measurement half

**R4 runs in `fux-lab`, and `fux-lab` does not exist** —
[W-56](W-56-sibling-environments-missing.md), 2026-08-20. The *build* is
unblocked; the *gate* is not. Under the plan's own sequencing rule a milestone
does not start while its gating prediction is unmeasured — **R4 gates M5, not
M4**, so building M4 is legal and closing it is not.

Consequence for whoever picks this up: **build components 1–6 and their tests,
write `ADR-REFER` as `proposed` with `built: partial`, and leave R4 filed.**
Do not write an accepted record for a plane whose gate has not run.

### Model

**Sonnet to build components 1–6** against this spec — it is detailed enough
to be executable, which is itself the signal that the design phase is done.
**Opus for the R4 verdict** if the numbers land ambiguous, because that is a
gate call.

---

## Read before writing the handoff — non-negotiable

Both proposals graduate here, by their own graduation triggers, and both
shape the refer API's **first** surface:

- [`../proposals/caller-set-freshness-policy.md`](../proposals/caller-set-freshness-policy.md)
  — staleness tolerance becomes a caller parameter (`max_age_seconds`,
  `timeout_seconds`), not engine policy. The `never` sentinel is what makes
  a replayed answer reproducible; it is the row that matters.
- [`../proposals/token-budget-retrieval.md`](../proposals/token-budget-retrieval.md)
  — the primary limit is a **byte budget** the assembler fills, with `k`
  demoted to a secondary cap. Byte budget, never token budget: carrying a
  tokenizer per model family violates the `$0`/stdlib law.

Evidence base for both: [`../proposals/agent-search-landscape.md`](../proposals/agent-search-landscape.md).
Read its **"Benchmark caution"** section before importing any framing from
it — the idea can be right and the vendor evidence for it self-serving at
the same time.

## What lands

- **HTTP (conditional GET) + Confluence adapters — and the cap holds.**
  Core ships exactly these two. More systems arrive through
  [`../proposals/mcp-adapters.md`](../proposals/mcp-adapters.md), not code.
- ARC cache keyed `(loc, sha)`, **results-neutral by construction** — the
  same differential discipline W-22 establishes for the accelerator.
- Transient convert + heading-aware chunker + passage re-score on the
  fetched bytes.
- Freshness: every answer stamped; live verification behind
  `[freshness] verify`, fenced network, **default off**.
- **A fetch path for `src:"url"` documents** — this is the debt
  [ADR-URL-INGEST](../../archive/adr/0010_url-source-consumer-middleware.md) recorded when
  the URL source landed early. Verify-time fetch for a fetcher-sourced
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
- [ ] `ADR-REFER` written and accepted.

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

---

## Scope — M4 — the refer plane

*Migrated verbatim from `PLAN.md` §M4 on 2026-08-18, when
that document was archived. **This file is now the spec**; there is no other.*

> **Scope note (2026-08-10):** a `url` *source* landed early via a
> consumer-owned fetcher file (ADR-URL-INGEST). The adapter cap below is
> untouched — core ships no URL adapter, all network lives in the consumer's
> file — but this milestone's refer plane must decide the verify-time fetch
> path for `src:"url"` documents.

HTTP (conditional GET) + Confluence adapters — **the cap holds**; more systems
arrive via [`../proposals/mcp-adapters.md`](../proposals/mcp-adapters.md), not
code. ARC cache keyed `(loc, sha)`, results-neutral by construction. Transient
convert + chunker + passage re-score on fetched bytes. Freshness: every answer
stamped; live verification behind `[freshness] verify` (fenced network,
default off).

**DoD:** R4 mock-server bench (cold k=10 ≤ 3 s, warm ≤ 300 ms); ARC
differential test; offline degradation honest (git sources full function,
external → declared staleness); a record for the refer plane.
