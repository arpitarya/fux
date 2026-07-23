# Fux conformance — acme-payments realistic repo — 2026-07-22

Version under test: **fux 0.23.0** (PyPI, pinned in `fux-lab/acme/VERSION`).

The discriminating run. A ~1 000-document repo with **genuine prose diversity**
(real ADRs, runbooks, postmortems, RFCs, guides, API refs), not the one-paragraph
template the synthetic tiers use. Built to settle engine-weakness (A) vs
corpus-artifact (B) for the hybrid degradation recorded in
`docs/proposals/hybrid-degrades-at-scale.md`.

- Corpus: 929 files on disk · **877 ingested** (216 md · 595 code · 27 json ·
  17 yaml · 22 image-stubs; 1 binary skipped; vendor PDF/DOCX + `_web/` not in the
  configured source roots).
- Eval set: **59 typed pairs** — factual 12 · why 11 · how-to 8 · cross-doc 6 ·
  stale-vs-current 12 · zero-overlap 6 · unanswerable 4.
- Generator: `fux-lab/shared/generate/make_repo.py` (stdlib, deterministic —
  `diff -r` between two runs is empty). Suite: `fux-lab/shared/regress/run.py`.
- repro: `cd fux-lab/acme && ./setup.sh && ./run.sh`

## Scorer sanity-checked first (TEST-PLAN §0b corollary)

`_score_pairs()` matches on `path.endswith(pair["doc"])`. Hand-verified on one
known-good hit before trusting any number: `find --lexical-only` for the ADR-0002
question returns `docs/adr/0002-tokenize-pan-at-the-edge.md` at **rank 1**, and
the matcher scores it a hit. The matcher is correct.

## Headline — the A-vs-B question is settled toward **B** (corpus artifact)

The synthetic 4× hybrid collapse **does not reproduce** on realistic prose.

| metric | synthetic 1k | **acme-payments (~1k realistic)** |
|---|---|---|
| lexical hit@1 / hit@5 / MRR | .364 / .818 / .576 | **.527 / .873 / .669** |
| hybrid hit@1 / hit@5 / MRR | .091 / **.182** / .136 | **.491 / .855 / .659** |
| hybrid ÷ lexical (hit@5) | 0.22× (4.5× worse) | **0.98× (parity)** |
| zero-overlap dense rescue (hybrid) | 0/2 | **0/6** |

- Hybrid hit@5 recovers **.182 → .855** on realistic text — a ~4.7× jump.
- Hybrid now **tracks lexical** (.855 vs .873), instead of collapsing 4× below it.
- Conclusion: the hybrid degradation was **corpus-induced**. Near-identical
  template prose made the dense ranking arbitrary and RRF fused noise; genuine
  prose gives the dense plane real signal, so fusion stops hurting.
- Therefore the four frozen mitigations aimed at "hybrid degrades" (dense
  admission threshold, confidence-weighted RRF, size-aware default) are **not
  justified by this corpus for that purpose** — the thing they target is a
  synthetic artifact. They remain candidates only for the residual findings below.

repro: `cd fux-lab/acme && ./run.sh` · metrics block in
`evidence/suite-report-raw.md`.

## Per-kind quality — never an aggregate alone (TEST-PLAN §4.4)

Hybrid unless noted. The aggregate `.855` hides a wide spread.

| kind | n | lexical hit@5 | hybrid hit@5 | hybrid hit@1 | note |
|---|---|---|---|---|---|
| why | 11 | 1.00 | **1.00** | .909 | ADR rationale — Fux's strongest surface |
| how-to | 8 | 1.00 | **1.00** | .875 | runbook/guide retrieval |
| factual | 12 | 1.00 | **1.00** | .333 | answer in top-5 always; rank-1 weaker |
| cross-doc | 6 | 1.00 | .833 | .5 | two-doc questions |
| stale-vs-current | 12 | .833 | **.833** | .167 | current doc *reachable* — but see inversions |
| zero-overlap | 6 | .167 | **.167** | .167 | dense rescue fails (below) |

- **why / how-to / factual are excellent** — hit@5 = 1.00. On realistic prose
  the engine reliably surfaces the right decision/procedure/fact into the top-5.
- **factual hit@1 is only .333** (hit@5 1.00): the right doc is always in the
  top-5 but frequently not rank-1, because short legacy twins compete (see
  staleness). Precision, not recall, is the gap.
- repro: `fux find "<question>" --json --top 5 [--lexical-only]`

## Finding 1 — staleness: Fux returns the **superseded** answer (9/12 inversions)

The actual product test — *does Fux surface the answer that is still true?* — and
the answer here is **usually no**.

- The **current** (still-true) doc is in top-5 for **10/12** pairs (recall is fine).
- But the **superseded** doc **outranks** it in **9/12** pairs — almost always the
  stale doc at rank 1, current at rank 2. An agent taking top-1 gets the *wrong,
  retired* answer 9 times in 12.
- All three supersession markers lose equally: `superseded_by` frontmatter, a
  dated inline "*Superseded …*" note, and no marker. **Retrieval has no notion of
  currency** — the markers are just text it ranks by term frequency.
- Mechanism (from `evidence/why-*` + `trace-staleness-settlement.txt`): the terse
  legacy doc scores *higher* on BM25F (length normalization favors the shorter,
  denser doc), and the dense plane can't break the tie because the two docs are
  topically near-identical. Fused margin is razor-thin — settlement: stale
  rrf 0.04892 vs current 0.04813 (Δ 0.00079).

Named inversions (all 9): settlement window · idempotency-key TTL · API rate limit
· auth method · refund window · PAN storage · chargeback deadline · webhook retry
window · reconciliation cadence. Each with both docs in
`evidence/staleness-inversions.json`.

repro: `fux find "What is the card settlement window today?" --json --top 10`
→ `docs/adr/0006-…-t-plus-three.md` (stale) rank 1, `…-0018-…-t-plus-two.md`
(current) rank 2.

## Finding 2 — zero-overlap dense rescue fails even when the answer *dominates*

Designed to remove the synthetic run's escape hatch. Each zero-overlap answer is
the **whole** of a short doc, so the doc vector is **not** diluted (the failure
mechanism ANALYSIS blamed at 10k). It still fails.

- **Clean dense rescues: 0/6.** hit@5 shows 1/6, but that one
  ("what technology keeps information after the power goes off?") also has
  **lexical rank 4** — it came through BM25F, not a dense rescue. Remove it and
  hybrid rescued **zero**.
- So doc-level dense on 0.23.0 does not surface a zero-vocabulary-overlap answer
  **even when the answer is the entire document**. This is *not* the dilution
  story — it is the dense plane itself.
- Corroborates and **strengthens** the scaling run's 0/14 and narrows ADR 0010's
  rescue claim further: rescue is not reliable even in the favorable case.

repro: `fux find "How do we stop strangers from draining an account?" --json`
(hybrid) → `docs/notes/access-revocation.md` absent from top-10.
evidence: `evidence/zero-overlap.json`

## Finding 3 — honest-decline fails on **well-formed** unanswerable questions (0/4)

The engine declines gibberish but **fabricates** on plausible out-of-scope
questions.

- Gibberish control **passes**: `answer "xyzzy plugh …"` → `answer=null`, 0
  sources. (This is the only decline case the synthetic gate ever tested.)
- The 4 typed unanswerable questions (crypto policy, k8s autoscaler, GraphQL SLA,
  SMS-OTP vendor) **all fabricate**: `answer` returns a confident extractive
  answer with 1–5 sources drawn from unrelated docs. E.g. *"What is Acme's policy
  on cryptocurrency…?"* → an answer quoted from `0005-store-amounts-in-minor-units`
  with 5 sources.
- Cause: a well-formed question shares enough incidental vocabulary with *some*
  passage that the extractive threshold admits it. The single-gibberish gate
  (zero lexical overlap) can never surface this — a corpus-scale blind spot.

repro: `fux answer "What is Acme's policy on cryptocurrency and stablecoin
settlement?" --json` → non-null answer + 5 sources.
evidence: `evidence/unanswerable-fabrication.json` · `evidence/gibberish-control-answer.json`

## What passed (this is not a broken engine)

- Determinism: double-ingest byte-identical (`state 8c4b70da…`, `lock b703e9ef…`);
  all three drift classes distinguishable with correct `--strict` exit 2.
- Fresh clone answers from committed state, **top-1 parity** (tail re-ranked —
  same INFO as every prior tier; the README/CHANGELOG "same rankings *and scores*"
  wording is inaccurate again — see the proposal + the doc fixes in this change).
- Citations resolve; `--lexical-only` stable across runs.
- Sizes at 929 docs: state 256 · index 1970 · cache 877 · lock 220 B/doc.
  Latency (cloud): ask/find cold ~0.35 s · answer ~0.48 s · ingest 1.0 s —
  same order as the cloud 1k anchor (~0.36 s), i.e. realism did not change the cost.

## Verdict

- **A vs B: settled toward B for the headline.** The 4× hybrid collapse is a
  synthetic-corpus artifact; on realistic prose hybrid ≈ lexical. The default
  path is not shipping broken in the way the 1k numbers implied.
- **But the harness earned its keep three more times.** Realistic prose exposed
  three real, corpus-independent gaps the synthetic tiers and the 21-pair gate
  both missed: staleness inversions (9/12), zero-overlap dense rescue (0/6 clean),
  and honest-decline on well-formed out-of-scope questions (0/4).
- **Caveat: one corpus is one corpus.** These are evidence, not proof. No ranking
  or fusion behaviour change ships off this run; findings graduate through
  proposals and an ADR (see `ANALYSIS.md`).
