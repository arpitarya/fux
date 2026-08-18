# ANALYSIS — M1-rerun, the pruning gate made decidable

**Run date:** 2026-08-09 · **Verdict:** **FAIL** →
[ADR-0003](../../adr/0003-pruning-criterion-rerun.md) ·
**Pre-registration:** [`PRE-REGISTRATION-v2.md`](../../../tools/pruning-eval/PRE-REGISTRATION-v2.md)
(commit `3892c55`, **before** the first gating number)

This run answers the one [ADR-0002](../../adr/0002-pruning-eval-gate.md) asked
for: a corpus whose documents are long enough that pruning is a real treatment.

---

## Reproduce

```bash
# 1. acquire the corpus once — a LAB activity, pinned by sha256 manifest
archive/v0.26/.venv/bin/python tools/pruning-eval/fetch_rfc.py \
    --out ~/my_programs/fux-lab/rfc --workers 5

# 2. the corpus gate — must pass BEFORE any arm runs
archive/v0.26/.venv/bin/python tools/pruning-eval/corpus_gate.py \
    --corpus rfc repodocs acme orbit \
    --out docs/conformance/2026-08-09-pruning-rerun/evidence/corpus-gate.json

# 3. the experiment — 5 arms × 3 rungs, retention-matched
archive/v0.26/.venv/bin/python tools/pruning-eval/run2.py \
    --corpus rfc --limit 2000 \
    --out docs/conformance/2026-08-09-pruning-rerun/evidence

# 4. diagnostics behind the ADR
archive/v0.26/.venv/bin/python tools/pruning-eval/spine_diag.py --corpus rfc \
    --out docs/conformance/2026-08-09-pruning-rerun/evidence/spine-diagnostic.json
archive/v0.26/.venv/bin/python tools/pruning-eval/arm_audit.py --corpus rfc \
    --out docs/conformance/2026-08-09-pruning-rerun/evidence/arm-audit.json
archive/v0.26/.venv/bin/python tools/pruning-eval/arm_recheck.py --corpus rfc \
    --out docs/conformance/2026-08-09-pruning-rerun/evidence/arm-recheck.json

# harness contract
archive/v0.26/.venv/bin/python -m pytest tools/pruning-eval/tests -q   # 50 tests
```

**Runtime on the bench machine:** corpus fetch ~35 min (8 872 documents,
510 MB); ingest ~25 min; the 13-cell run ~2 h 15 m at ~3.5 GB peak RSS.

## Result

| | |
|---|---|
| gating corpus | **rfc** — 8 872 documents, median **967** distinct terms/doc |
| gate metric | recall@20, abstract-derived queries (n = 703) |
| ceiling (arm 5, no pruning) | **0.986** |
| best arm @ 6 % retention | arm 1 (KL) **0.627** → **−35.9 pts** |
| best arm @ 15 % | 0.755 → −23.0 pts |
| best arm @ 30 % | 0.859 → −12.7 pts |
| pre-registered bar | within **2 pts** → **FAIL** |

| arm | rules | 6 % | 15 % | 30 % |
|---|---|---|---|---|
| **5 — no pruning** | — | **0.986** | 0.986 | 0.986 |
| 1 — KL only | — | 0.627 | 0.755 | 0.859 |
| 2 — impact only | B | 0.489 | 0.615 | 0.774 |
| 3 — A + B | A+B | 0.209 | 0.340 | 0.521 |
| 4 — A + B + C | A+B+C | 0.208 | 0.354 | 0.531 |

Standard error 1.3–1.9 pts; the gaps are 7–27× that.

## Validity — every check passed

| check | threshold | result |
|---|---|---|
| corpus gate | median ≥ 500 distinct terms | **967** ✅ |
| corpus integrity | sha256 manifest | 8 872 checked, **0** mismatches ✅ |
| retention matched | ±1 pt of rung | all 12 cells, worst 0.12 pts ✅ |
| prune coverage @6 % | ≥ 50 % of documents (else VOID) | **100 %** ✅ |
| ceiling identity | 100 % retention = no-op | passes per arm ✅ |
| determinism | reordering + term-iteration invariance | 50 tests ✅ |

No VOID condition fired. **The run is evidence.**

## Diagnosis

### 1. The predicted result did not happen, and the opposite did

Pre-registered: *"arm 4 lands within noise of arm 5 at 6 %; arm 1 is the
outlier."* Measured: **arm 4 is 77.8 pts below arm 5; arm 1 is the best arm at
every rung.** Both secondary expectations (impact > KL, spine helps) also
failed. The `repodocs` counter-signal recorded in the pre-registration
reproduced on a completely different corpus.

**KL divergence is not the defect** the compare doc took it to be.

### 2. Two hypothesised mechanisms were measured and falsified

| hypothesis | prediction | measured | verdict |
|---|---|---|---|
| the unbounded spine swallows the budget | many documents keep only headings | **1 document of 8 872**; spine is 0.13 % of vocabulary, median size **1** | **falsified** |
| impact ranking is heading-dominated | heading terms fill the top-6 % | **1.65 %** of the top-6 % are heading terms (KL: 2.05 %) | **falsified** |

Cause: **plain-text RFCs carry no Markdown headings**, so the archived chunker
gives the heading field only the title — a single token. **Rule A is therefore
nearly inert on this corpus and is effectively untested here.**

### 3. The arm 2 / 3 gap is a *competition* effect, not a per-document one

Arms 2 and 3 keep **identical postings for 93.4 %** of documents (mean
symmetric difference 0.877 terms of 65.72), and only **28 of 393** gold
documents differ — yet they score 27 pts apart. A per-document explanation is
arithmetically impossible.

**The direct test settles it.** Restricting to the 372 of 400 queries whose
gold document keeps *byte-identical* postings under both arms:

| arm | recall@20 on the unchanged-gold slice |
|---|---|
| 2 — impact only | **0.441** |
| 3 — A + B | **0.298** |

A 14-point loss on queries where the correct document's index entry did not
change at all. The damage is entirely in the *rest* of the index: the 6.6 % of
documents with large forced spines (up to 113 terms) keep **heading-field**
postings, which BM25F weights ×3.0, so they become spurious high scorers across
unrelated queries and displace correct answers from the top-20.

**The lesson generalises past Rule A:** a rule that forces heavily-weighted
postings into a minority of documents can degrade the whole index, and a
per-document evaluation would never see it.

**Scope limit:** RFCs give Rule A a one-term spine, so this measures the effect
of the *minority* of documents that do carry large headings. On a corpus of
genuinely structured documents the spine would be larger and more meaningful,
and the sign could differ. Rule A is implicated here, not disproven.

### 4. The losses are dominated by the query workload

Every failure in every catalogue classifies as `term-pruned`, and the lost
terms are ordinary: `a`, `b`, `and`, `or`, `on`, `low`, `storage`, `space`,
`references`. Queries are verbatim 8–16 token sentences, so a document is found
only if *that sentence's* terms survive. At 6 % retention the median document
keeps 58 of 967 terms.

**This makes the eval close to a worst case for pruning** — the strongest
argument that the verdict is too harsh, and the first thing a follow-up must
test.

## Specific changes this run calls for

| # | change | why | status |
|---|---|---|---|
| 1 | **Do not build on aggressive static pruning.** Option E: committed index 0.6–1.5 GB; partial clone + external-shards-only become mandatory. | No arm within 2 pts at any rung. | **done** — [ADR-0003](../../adr/0003-pruning-criterion-rerun.md) |
| 2 | **`pruning-criterion.compare.md` → amended, not accepted.** Prediction falsified; the three-rule selector remains *untested* (Rule A inert here). | Honesty about what was and was not measured. | **done** |
| 3 | **Re-measure with a realistic query workload** (short, salient, keyword-style — what an agent actually sends), with a fresh pre-registration. | The single most likely way this verdict is too harsh. | **open — highest priority** |
| 4 | **Re-derive paper §5's size model** at a retention that holds quality, or at no pruning. | Its ~6 % assumption is now *measured as quality-destroying*, not merely unvalidated. | **open** (M7 owns the numbers; flag owed now) |
| 5 | **`storage-architecture.compare.md` takes a size amendment.** | Its reopen-trigger fired, but index-and-refer is not what failed — only the "small index by pruning" claim. | **done** |
| 6 | **Test Rule A on a corpus with real headings** before accepting or rejecting it. | RFCs give it a 1-term spine; it is untested, not disproven. | **open** |

## Unresolved

- **Whether a realistic query workload changes the verdict.** Not tested here.
- **Whether the competition effect (§3) generalises** to corpora where the
  spine is large *and* meaningful. On RFCs it is driven by a 6.6 % minority;
  the sign could differ where headings are informative.
- **The three-rule selector's actual merit.** Rule A was inert; Rule C was
  infeasible at the 6 % rung (its floor cost, `δ × |vocabulary| / |postings|`,
  consumed 4.3 % of a 6 % budget) and had to run at δ=1.

## Evidence index

| file | what it is |
|---|---|
| `evidence/report.md` | the harness's own output, unedited |
| `evidence/results.json` | per-cell metrics, retention, coverage, failure catalogues |
| `evidence/corpus-gate.json` | the four corpora's vocabulary distributions and gate outcomes |
| `evidence/spine-diagnostic.json` | spine sizes; impact/KL top-6 % composition |
| `evidence/arm-audit.json` | kept-set overlap between arms |
| `evidence/arm-recheck.json` | independent re-measurement + the competition test |

**Known cosmetic defect:** the `lost` column in `report.md` shows the
catalogue's display cap (60) rather than the true count. The true counts are in
`results.json` (`lost_total`: 555 / 1002 / 1327 / 1310 at the 6 % rung). No
number in the ADR is taken from that column.
