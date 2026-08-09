# Pre-registration v2 — M1-rerun, the pruning gate made decidable

**Frozen before the first gating number exists.** `git log` on this file is the
evidence: it is committed *before* any arm runs on the gating corpus. Metric,
slices, arms, rungs, gold labels, validity checks and the PASS/PARTIAL/FAIL/VOID
rule are all fixed here.

Supersedes [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md) (v1) for the pruning
question. v1 was not wrong so much as *inapplicable*: its threshold assumed a
treatment the corpora could not deliver. [ADR-0017](../../docs/adr/0017-pruning-eval-gate.md)
is the record of that, and it stands unmodified.

---

## 1. The question, restated

Can the committed index be small — i.e. does keeping ~6 % of postings preserve
Fux's ability to **put the right document in front of the re-score stage**?

Three changes from v1, each answering a specific defect ADR-0017 named:

| v1 | v2 | why |
|---|---|---|
| gate on the index's own **hit@5** | gate on **recall@20** of the candidate set | The index is a *candidate generator*: Fux ranks, fetches top-k, then re-scores passages on the fetched bytes. A document falling from rank 1 to rank 8 costs nothing. Mackenzie et al. (SIGIR '24) measure this directly — pruning's recall reductions produce "no significant differences" once a re-rank stage runs. |
| fixed **k = 128** | matched **term retention** (6/15/30 %) | "Keep the top 128" meant *nothing* on a 32-term document and *everything* on a 2 000-term one. Retention makes the treatment mean the same thing everywhere — and comparing criteria at a fixed k would repeat v1's error one level up. |
| one criterion (**KL**) | **five arms** | The k=64 failure catalogue implicated the criterion, not pruning: KL rewards terms rare *across the collection*, so in a homogeneous corpus it deleted `webhook` from `webhooks.md`. Re-running KL alone would burn a corpus to re-learn a known defect. |

## 2. The corpus gate — run first, and it already disqualified one corpus

**Threshold: median ≥ 500 distinct terms per document.** Below it a 6 % budget
is dominated by the floor rather than by the criterion, and the cell measures
nothing. This is ADR-0017's lesson promoted to a hard gate.

Measured **before** any arm ran (`corpus_gate.py`):

| corpus | documents | median | p90 | p99 | max | terms kept @6 % (median doc) | gate |
|---|---|---|---|---|---|---|---|
| **rfc** | **8 872** | **967** | 1 850 | 3 236 | 28 461 | 58 | **PASS — the gating corpus** |
| repodocs | 201 | **425** | 867 | 1 917 | 3 140 | 26 | **FAIL — not gating** |
| acme | 877 | 32 | 81 | 156 | 407 | 8 | FAIL — not gating |
| orbit | 892 | 36 | 89 | 150 | 432 | 8 | FAIL — not gating |

**The RFC corpus clears the gate with room to spare** and sits in the regime the
paper's size model assumes: a median document carries 967 distinct terms, so a
6 % budget keeps 58 of them and discards 94 %. That is a real treatment — the
thing ADR-0017's corpora could not deliver. Corpus integrity verified: 8 872
documents, 0 sha256 mismatches against the manifest.

**This resolves handoff §10's open question mechanically, not by preference.**
"Both must pass" was the recommended weighting; `repodocs` fails the corpus
gate at 425, so it *cannot* gate. **The RFC corpus is the sole gating corpus**;
`repodocs`, `acme` and `orbit` are reported as secondary evidence. If the RFC
corpus also fails the gate, the run is **VOID** and no verdict is issued.

**`repodocs`' median of 425 is itself a finding**, and it is recorded here
before any result can make it convenient: the paper's §5 size model assumes
~2 000 distinct terms per document. The actual target domain — this repo's own
long-form documentation — has a median of 425. That gap belongs in ADR-0018
regardless of which way the gate falls.

## 3. The five arms

Every arm is scored by the **archived v0.26 BM25F** (`Searcher.search`),
unmodified. Arms differ only in which terms the index keeps.

| arm | rules | ranking | question |
|---|---|---|---|
| 1 | — | KL divergence | continuity with ADR-0017 |
| 2 | B | max BM25F impact | is KL the defect, or pruning itself? |
| 3 | A + B | impact, heading spine kept | does the heading floor alone fix it? |
| 4 | **A + B + C** | impact + spine + per-term sweep | **the proposed selector** |
| 5 | — | none (no pruning) | the quality ceiling / fallback |

Rules, per [`pruning-criterion.compare.md` §7](../../docs/compare/pruning-criterion.compare.md):

- **A — heading spine:** every term in the title or any heading survives.
- **B — impact budget:** fill `max(floor, ⌈share × |vocab(d)|⌉)` by max BM25F
  contribution.
- **C — per-term backstop:** after every document's local pass, each term is
  force-kept in its top-δ documents by impact.

**Parameters:** `floor = 8`, `δ = 3` requested. Selection uses the **unpruned**
collection model (it must — you cannot rank by impact against statistics that
depend on the ranking); the built index then **recomputes `df`, `n` and
field-length sums over the final kept postings**, after Rule C. Two-pass by
design, never borrowed.

## 4. Retention — the matched axis

Retention = kept `(document, term)` pairs ÷ total pairs, the quantity the
paper's §5 size model is denominated in. Rungs: **6 %, 15 %, 30 %**.

Each arm's budget share is **calibrated by binary search** to hit the rung.
**Validity bar: actual retention within ±1 pt of the rung.** A cell outside
that is *not comparable* and is excluded from the gate readout.

**Rule C has a structural floor cost** — it keeps δ postings for every distinct
term in the collection, i.e. `δ × |vocabulary| ÷ |postings|`, which grows as the
corpus shrinks. Where even δ=1 exceeds the rung, arm 4 is **infeasible at that
rung**; the cell is flagged `infeasible` and excluded from the gate rather than
silently degenerated into arm 3. δ steps down 3→2→1 to fit and the chosen value
is reported per cell.

## 5. Metrics and slices

**Gate metric: `recall@20`** — the fraction of queries whose gold document
reaches the top 20, i.e. the candidate set the refer plane would fetch and
re-score. With one gold document per query this equals hit@20; it is named
*recall* because that is the quantity that matters.

**Diagnostics only, never gating:** recall@10, recall@50, hit@5, P@10, MRR,
prune coverage, per-cell failure catalogue with classified causes.

**The gate is read on the `abstract` slice.** Queries come in two kinds:

| kind | source | bias |
|---|---|---|
| **`abstract`** | a sentence from the document's abstract / opening prose | **body text — no rule guarantees these terms.** Neutral across arms. **The gate is registered on this slice.** |
| `heading` | a section heading | Rule A keeps every heading term *by construction*, so arms 3 and 4 are flattered. **Diagnostic only.** |

Both are reported for every cell. Registering the gate on the unbiased slice —
before seeing either — is the point.

**Eval set:** up to one query of each kind per document, drawn with a fixed seed
(`20260809`) in sorted document order; gold = the source document; structural
boilerplate ("Introduction", "Security Considerations", …) excluded; queries
must be 4–16 tokens. No filtering depends on retrieval results.

**Known limitation, stated up front:** queries are derived from the documents
themselves, because no human relevance judgments exist for these corpora. This
is a known-item task, not a topical-relevance task. It measures *"can the index
still find the document this text came from"* — the right question for a
candidate generator, but not a substitute for judged relevance.

## 6. The pre-registered rule

Read on the **gating corpus (rfc)**, **`recall@20`**, **`abstract` slice**,
**6 % retention**, against **arm 5 (no pruning)**:

| outcome | condition | action |
|---|---|---|
| **PASS** | best arm within **2 pts** of arm 5 | selector decided; W-01 unblocks |
| **PARTIAL** | best arm within 2 pts at **15 % or 30 %** but not 6 % | re-budget the paper's §5 size model at that retention; W-01 unblocks with the amended number |
| **FAIL** | no arm within 2 pts of arm 5 at **any** rung | option E — index is 0.6–1.5 GB; partial clone + external-shards-only become mandatory; `storage-architecture.compare.md` takes a size amendment |
| **VOID** | the corpus gate fails, or prune coverage < 50 % of documents at 6 %, or no arm achieves matched retention | the run is not evidence; say so and issue no verdict |

**The threshold does not move after numbers exist.** An ambiguous result is
written up as ambiguous. ADR-0017 is the precedent and it was the right call.

## 7. Pre-registered prediction

From [`pruning-criterion.compare.md` §5](../../docs/compare/pruning-criterion.compare.md),
recorded so a miss is visible as a miss:

> **Arm 4 lands within noise of arm 5 on recall@20 at 6 % retention; arm 1 is
> the outlier.**

Secondary expectation: arm 2 > arm 1 (impact beats divergence on a homogeneous
corpus), and arm 3 > arm 2 (the spine helps).

*Recorded counter-signal:* on the **non-gating** `repodocs` smoke run, arm 1
(KL) **beat** arms 2 and 3 at every rung, and every arm lost 15–38 pts against
the ceiling. If the RFC corpus reproduces that ordering, the compare doc's
central hypothesis is wrong and ADR-0018 must say so plainly.

## 8. Validity checks — all must pass before any verdict

1. **Ceiling identity** — 100 % retention reproduces the unpruned index exactly,
   for every arm (asserted in `tests/test_rerun.py`).
2. **Retention matched** — every gating cell within ±1 pt of its rung, or
   flagged and excluded.
3. **Reproducibility** — two runs produce byte-identical `report.md`.
4. **Determinism** — preparation is invariant under document reordering; Rule C
   is invariant under term-iteration order (both asserted in tests).
5. **Prune coverage** — reported per cell; < 50 % of documents at 6 % ⇒ VOID.
6. **Corpus integrity** — the RFC corpus verifies against its sha256 manifest.

## 9. Declared limitations

- Known-item eval, not judged relevance (§5).
- One gating corpus. `repodocs` failed the corpus gate; `acme`/`orbit` are far
  below it. A single corpus is thin evidence and ADR-0018 must say so.
- Document-level impact (a document's field counts aggregated over its chunks),
  because production prunes a document's index entry, not a chunk's.
- Only `δ ∈ {1,2,3}` and `floor = 8` explored; no wider sweep.
- Lexical only — dense and graph retrievers are out of scope, since P1 is a
  claim about **postings**.
