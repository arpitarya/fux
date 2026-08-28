---
type: Run Report
run: 2026-08-28-annotator-agreement
classification: blind
date: 2026-08-28
---

# Two blind annotators, κ = 0.96: the goldens' relevance sets are incomplete

**The gating item for W-87 P2's schema decision.**
[The 2026-08-28 blind run](../2026-08-28-blind-unanswerable/report.md) found one
annotator judging 25 of 50 goldens to have more than one genuinely relevant
document, and said plainly that **one reader is one opinion**. This is the
second reader.

**They agree, and the agreement is near-perfect.**

## Authorship — classification `blind`

| artifact | author | could reach |
|---|---|---|
| annotator 1 | a fresh session, 2026-08-28 | the ten corpus documents + a **stripped** query list (`id` + `q` only) |
| annotator 2 | a **different** fresh session, same day | identical inputs — **and explicitly forbidden annotator 1's output** |
| this analysis | Claude Code (informed) | everything |

**What was withheld from both, and why each item was withheld:**

- `goldens/queries.jsonl` — it is the answer key under examination.
- **`known_failure` text** — it *describes ranking behaviour* ("ranks 4, behind
  three documents that merely mention a freeze"), so it is score-derived and
  would leak the engine's results into a relevance judgment.
- Any run report, per-query score, or the `fux` command itself. Both were told
  not to run it: *if you see which document the engine ranks first, your
  judgment bends toward agreeing with it.*
- **Annotator 2 was additionally forbidden annotator 1's answers**, and told
  why — the entire value of a second reader is agreement reached *without*
  coordination.

⚠ **The orchestrating session is informed and authored no judgment.** It wrote
the stripping harness and this analysis; every relevance call came from a
session that had seen no scores and no other annotator.

## The result

| | annotator 1 | annotator 2 |
|---|---:|---:|
| exactly one relevant document | 25 | 24 |
| **more than one** | **25** | **26** |
| zero | 0 | 0 |
| low confidence | 3 | 1 |

| agreement measure | value |
|---|---:|
| agree on *is it multi-document?* | **49 / 50 (98 %)** |
| **Cohen's κ** on that judgment | **0.960** |
| agree on the **exact document set** | 43 / 50 (86 %) |
| mean Jaccard over all 50 | **0.943** |
| questions **both** independently call multi-document | **25** |

**The single disagreement is `q050`** — *"a hazard we wrote down but never
actually fixed"*. Annotator 2 included both runbooks for their live *Known gaps*
sections; annotator 1 did not. Both agree the postmortem answers it.

## What this establishes 🔴

**`recall@k` ≠ `hit@k` on this corpus, confirmed by two independent blind
readers.** The committed goldens assert **one** document for all 50 questions.
Two readers who could not see each other's work, the answer key, or any score
**both** judged **25 of those 50** to have more than one genuinely relevant
document — and agreed on *which* 25, at κ = 0.96.

**So `expect`/`doc` is a rank contract, not a relevance set**, and the
distinction is no longer a hypothesis about the schema. It is measured.

**The 2026-08-28 field-count inference stays withdrawn.**
`relevance_audit.py` established the file holds one scalar `doc` per query and
the same-day conclusion drawn from it — *"`recall@k` over this set IS
`hit@k`"* — was about the file's **shape**. The audit's own output said no count
could settle completeness. Two readers have now settled it the other way.

⚠ **No filed number is invalidated.** Every past run measured *"did the asserted
document come back"* — that is `hit@k`, and it was reported as `hit@k`. What
changes is that **it may not be called `recall@k`**.

## One incidental finding, worth the row

**Annotator 1's set omits the golden's own asserted document on `q027`.**
Annotator 2's never does. That is a single reader's miss rather than a defect in
the goldens — but it is the kind of thing only a second annotator surfaces, and
it is the concrete argument for having run one.

## What this does NOT establish

- **It does not decide the schema.** Whether `expect` becomes a list, and
  whether the rank contract and the relevance set split into two fields, is an
  **ADR** — this run supplies its evidence, not its verdict.
- **It does not make either annotator authoritative.** Two agreeing readers are
  strong evidence about *this* corpus; κ is a measure of agreement, never of
  correctness. Both could share a blind spot.
- **It computes no `recall@k` number.** Doing so would require ruling on the
  disputed row and adopting one annotator's sets as ground truth, which is the
  decision above.
- **Ten documents, fifty queries** — three orders of magnitude below the design
  point, and CLAUDE.md §Litmus governs what that can generalise to.

## Evidence

- [`evidence/per-query.csv`](evidence/per-query.csv) — **one row per query**:
  what the golden asserts, both annotators' full sets, both confidences, and
  the two agreement flags. Every number above is derivable from it.
- [`evidence/annotator-1.jsonl`](evidence/annotator-1.jsonl) ·
  [`evidence/annotator-2.jsonl`](evidence/annotator-2.jsonl) — the raw judgments.
- [`evidence/queries-as-given-to-annotators.jsonl`](evidence/queries-as-given-to-annotators.jsonl)
  — **the stripped input, exactly as handed over**, so the blindness claim is
  checkable rather than asserted.

## Reproduce

The annotations are static artifacts of two sessions; re-deriving them means
running **new** blind sessions, which is a new run with its own directory —
never an edit to this one. The agreement statistics recompute from the evidence:

```bash
python3 - <<'EOF'
import json
d="work/regression/2026-08-28-annotator-agreement/evidence"
a={json.loads(l)['id']:json.loads(l) for l in open(f"{d}/annotator-1.jsonl") if l.strip()}
b={json.loads(l)['id']:json.loads(l) for l in open(f"{d}/annotator-2.jsonl") if l.strip()}
ids=sorted(a); n=len(ids)
A=[len(a[i]['relevant'])>1 for i in ids]; B=[len(b[i]['relevant'])>1 for i in ids]
both=sum(x and y for x,y in zip(A,B)); neither=sum(not x and not y for x,y in zip(A,B))
po=(both+neither)/n; pa=sum(A)/n; pb=sum(B)/n; pe=pa*pb+(1-pa)*(1-pb)
print(f"both multi {both}  kappa {(po-pe)/(1-pe):.3f}")
EOF
```
