---
type: Proposal
title: Answer provenance — emit, don't retain
description: "The researched successor to `audit-evidence-trail`: how the returned output got generated, as a derivation, a receipt and a four-state verification."
status: graduated
timestamp: 2026-08-27T00:00:00Z
tags: [provenance, audit, compliance, explainability]
---

# Answer provenance — emit, don't retain

> **GRADUATED 2026-08-27 → [ADR-PROVENANCE](../../docs/adr/0046_provenance.md),
> built the same day** ([W-91](../open/W-91-the-provenance-plane.md)).
> Kept for the **survey, the prior art, and the forks as they were put** — the
> record carries the decisions, this file carries the reasoning that produced
> them and the four alternatives that were rejected on the way.
>
> **Supersedes** [`audit-evidence-trail.md`](audit-evidence-trail.md)
> (filed 2026-07-21), which sketched `fux answer --audit` and parked it on *"needs
> a paying context to shape it"*. The trigger it was waiting for never fired;
> Arpit asked the question directly instead.

## Signal

Arpit, 2026-08-27, in Cowork: *"Is there a way to build an audit trail for how
the returned output got generated?"*

Three surfaces already describe an answer and **none of them explains it**:

| surface | says | cannot say |
|---|---|---|
| the citation | which bytes, by `sha`, and their freshness | why this document |
| [ADR-CONFIDENCE](../../docs/adr/0045_confidence.md) | how much of the query the corpus covers | which term, which field, which weight |
| `ask --explain` | which code path ran | anything about ranking |

## The reframe that made it buildable

**The words *audit trail* imply a log kept over time.** L8 — written the
morning of 2026-08-27 — forbade exactly that. The version that survives is the
same move index-and-refer already makes about content:

> **Fux does not hold the trail. It makes one derivable.**

Because fux is deterministic (L3) and content-addressed throughout, a receipt
naming the index digest, the tune digest, the engine and the cited bytes is not
a story about the past — it is a **re-runnable claim**. Retention becomes the
caller's, which is where the compliance obligation already sits.

⚠ **The reframe did not survive contact intact.** Arpit **reverted L8 the same
day**: *"we should be able to keep logs of the questions as well as answer. it
should never be maintained in git so having it in git ignore is fine."* So a
plaintext local journal is now legal — and the emit-don't-retain design was
kept anyway, because it is the better default even when the stricter one is
gone. The journal ships **off**, behind `--journal`. See
[ADR-LAWS](../../docs/adr/0001_laws.md) decision 8 for what the reversal trades
away.

## The one thing no competitor has

**The committed index is in git.** `git show <commit>:.fux/index/…` already
answers *"what did the index say about this document last Tuesday"* with no
logging at all. Every RAG-provenance product on the market logs *what the model
was shown*; fux can show *what the index actually held at a commit*, because it
is in the history. Naming a commit-stable index digest in a receipt is what
turns that from a curiosity into a checkable claim.

## Prior art, and what was taken from each

| source | taken | left |
|---|---|---|
| [Lucene / Elasticsearch `_explain`](https://www.elastic.co/search-labs/blog/elasticsearch-scoring-and-explain-api) | the shape of a score breakdown **and its cost discipline** — an explanation is a second query against one document, never a tax on the first | the nested explanation tree; it is unreadable |
| [SLSA v1.0 attestations](https://slsa.dev/spec/v1.0/attestation-model) | envelope → statement → predicate; the **subject named by digest**; the verifier checks the predicate against its own policy | the signing infrastructure — a public-key signature needs a dependency L1 forbids |
| [W3C PROV-O](https://www.w3.org/TR/prov-o/) | naming discipline for *derived-from* | the RDF/JSON-LD weight |
| [OTel GenAI conventions](https://opentelemetry.io/blog/2026/genai-observability/) | the **emit-vs-store boundary**: the tool emits, the collector retains | span plumbing (L1) |
| [EU AI Act Art. 12](https://artificialintelligenceact.eu/article/12/) | the record-keeping duty falls on **providers and deployers of a system**, not on a library — the whole argument for emit-don't-retain | building a log ourselves |
| Certificate Transparency / Merkle logs | a hash chain over receipts, **if** non-repudiation is ever wanted | not built; nobody has asked |

## The two assets that already existed and reached nobody

1. **`refer.Bundle.as_record()`** — docstring: *"everything needed to reproduce
   or audit it"*. Built on every `fux answer` since M4, **called by nothing**.
   `--audit` is that record reaching a caller, and it was the cheapest phase by
   an order of magnitude.
2. **`stats_out`** — `df` and `n`, added the previous day for ADR-CONFIDENCE.
   The derivation reads the same numbers rather than computing its own, so two
   blocks about one corpus cannot disagree.

## What was built

Four phases, all landed 2026-08-27 — see
[ADR-PROVENANCE](../../docs/adr/0046_provenance.md) for the decisions and
[W-91](../open/W-91-the-provenance-plane.md) for the state.

| phase | surface | what it answers |
|---|---|---|
| 1 | `answer --audit` | what the refer plane looked at, both shas, budget spent and dropped |
| 2 | `ask --why` | matched terms per document, the four gates, the cut line, rerank and tune deltas |
| 3 | `answer --receipt` · `--journal` · `fux verify` | does this answer still reproduce, and if not what moved |
| 4 | the declared shapes | `audit_record`, `derivation`, `receipt` in `output.schema.json` |

## Alternatives rejected, and why they stay rejected

- **Instrument the scorer and emit a real score tree.** Puts a diagnostic on the
  hot path, and any per-term contribution reaching the output invites a
  recomputed total that disagrees with the score beside it —
  [ADR-RANKING](../../docs/adr/0012_ranking.md)'s own module warns that
  re-deriving a score term-by-term yields different low-order bits.
- **Keep a durable answer log inside fux.** Rejected before the L8 reversal
  because the law forbade it; **still** rejected after, because it makes fux the
  data controller for query text at a corporate corpus and duplicates a tool —
  every enterprise already owns a log sink.
- **A boolean `verified` on the receipt.** Three prior defects in this repo are
  the argument: `max_age_seconds`, a `cached` verdict reported as `current`, and
  a line range for `ask` computed at ingest. All three were a field reporting
  confidently on something it no longer knew.
- **Sign the receipt.** L1 forbids the dependency; stdlib `hmac` gives a keyed
  digest, which is a *different* security claim. Reopening it is a
  key-management decision, not a format one.

## The forks still open

**None of these was decided by building.** Listed here as put, so a later
session inherits the question rather than the answer:

1. **Always-on journalling** needs a `.fux/tune.toml` key — an
   [ADR-TUNE](../../docs/adr/0038_tuning.md) change deliberately not made. A
   flag satisfies *"we should be able to keep logs"*; a default does not follow
   from it.
2. **Receipt scope** — the returned set only, or the whole `depth` window? The
   negative space is the audit-valuable half *and* the expensive half.
3. **`verify` and the network.** `file:` verifies offline; `url:` forces a
   fetch, which makes verification network-dependent — the same asymmetry that
   refused line-level `ask`.
4. **Signing.** Recomputable hash (today) vs. a keyed HMAC vs. a real signature.
   Different security claims; L1 rules out the third.
5. **MCP.** `fux_search` and friends carry no derivation. ⚠ W-84's finding
   applies: MCP tool descriptions are documentation **no gate reads**, so
   whatever is added there must be checked against what the handlers return in
   the same change.

## Graduation trigger

**Already fired.** This file is retained for the survey and the five open forks;
it moves to `archive/proposals/` when fork 1 is ruled and the last of the four
phases has a regression run behind it.

# Citations

[1] Elastic — *Elasticsearch scoring and the Explain API*: https://www.elastic.co/search-labs/blog/elasticsearch-scoring-and-explain-api
[2] SLSA v1.0 — *Software attestations*: https://slsa.dev/spec/v1.0/attestation-model
[3] W3C — *PROV-O: The PROV Ontology*: https://www.w3.org/TR/prov-o/
[4] EU AI Act — Article 12, *Record-keeping*: https://artificialintelligenceact.eu/article/12/
[5] OpenTelemetry — *Inside the LLM Call: GenAI Observability*: https://opentelemetry.io/blog/2026/genai-observability/
[6] Internal: [ADR-QUALITY](../../docs/adr/0044_quality-contract.md) — the four-gate funnel this reuses rather than reinventing.
