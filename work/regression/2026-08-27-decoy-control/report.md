---
type: Report
title: The decoy control's first run — one of fifteen unanswerable questions is reported `grounded`
description: "14/15 behave correctly and name their missing terms. One reports coverage 1.0, missing [], separation 0.58 and band `grounded` for a question no document discusses, because coverage is corpus-wide rather than per-document."
classification: informed
timestamp: 2026-08-27T17:45:00Z
---

# The decoy control — first run

**Apparatus:** [`tools/quality-controls/decoys.jsonl`](../../../tools/quality-controls/decoys.jsonl),
built 2026-08-27 as one of [ADR-RS](../../../docs/adr/0036_predictions.md)
decision 15's three owed controls.
**Corpus:** `fux-playground`, 10 documents, enriched, reranker on — the state it
normally grades in.

> **A SURFACE CAPTURE of a control's own behaviour.** It gates no prediction,
> pre-registers no threshold and states no delta between arms.

## What a decoy is, and why an agent could author these

Fifteen questions **plausible for the playground's domain** — key rotation,
SLAs, cluster provisioning, DR plans, parental leave — that its ten documents
**do not answer**.

⚠ **A decoy is the one kind of evaluation material an agent can write without
contaminating anything: it has no correct answer, so there is nothing to fit.**
That is why these were authored here while the goldens were not — the playground
README refuses an agent-installed golden set, and rightly.

## Result

| band | n |
|---|---:|
| `partial` | **14** |
| `grounded` | **1** |
| `weak` · `none` | 0 |

**`answerable: true` for 15/15** — which is correct and not the finding.
`answerable` is `band != none`, and `none` means `support == 0`; something always
scores. It is a very weak claim by design ([ADR-CONFIDENCE](../../../docs/adr/0045_confidence.md)
decision 5), not a statement that the corpus answers the question.

**The fourteen `partial` results are the system working.** `partial` fires when a
query term is in no document, and `missing` carries those terms — the field
`confidence.py` says an agent *"should read first."*

## The one that is not working

`d02` — **"what is the SLA we publish for the payments API"**

```json
{"band": "grounded", "answerable": true, "coverage": 1.0,
 "separation": 0.5808, "support": 3, "missing": []}
```

top hit: `policy-data-retention.md` (6.783), then `adr-0007-helix-mesh.md` (2.843).

**No document in the corpus discusses SLAs for a payments API.**

### The mechanism, verified term by term

`coverage` and `missing` are computed **corpus-wide, not per-document**. Every
term occurs — in four *different* files:

| term | where it occurs |
|---|---|
| `sla` | `policy-data-retention.md` |
| `publish` | `policy-data-retention.md` |
| `payments` | `postmortem-checkout-outage.md`, `reference-deployment-tiers.md` |
| `api` | `adr-0007-helix-mesh.md` |

So `missing` is empty, `coverage` is `1.0`, and the band falls past both
fact-based clauses to the `separation` test — which `0.58` clears.

**This is the failure `confidence.py`'s own opening paragraph names**: an agent
cannot tell *"these documents answer your question"* from *"these documents are
the closest thing in a corpus that does not discuss this at all."* Here the
block asserts the first.

## ⚠ It is not a threshold-value problem

`separation` is **0.5808**, above the **0.5** that R10's selection rule would
have chosen ([R10 verdict](../2026-08-27-r10-separation-floor/VERDICT.md)).
**Raising the floor to 0.5 would not have caught this.** Whichever way R10 is
ruled, this case survives it — which is worth knowing *before* ruling R10.

## Not fixed

**Per-document coverage is a design change to an accepted record** and is not an
agent's call. Named in `OPEN-WORK.md` §Blocked on Arpit — decisions and in
ADR-CONFIDENCE.

⚠ **No test was added pinning this as expected behaviour.** Pinning a defect is
how it becomes the contract.

## Authorship

| artifact | author | could reach |
|---|---|---|
| the 15 decoys | Claude Code (Opus 5), 2026-08-27 | the corpus. **No correct answers exist to have been fitted to** |
| the validation harness, this report | the same session | the corpus and the decoy set |

`informed`; states no delta between arms.

## Reproduce

```bash
python3 work/regression/2026-08-27-decoy-control/evidence/validate.py \
        tools/quality-controls/decoys.jsonl
```
