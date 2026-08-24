---
type: Proposal
title: 50 candidate goldens for the fux-playground corpus — drafted from the corpus, awaiting ratification
description: "GRADUATED 2026-08-24 — Arpit waived the human-author rule and the set is installed. Baseline 28/50; reranker 32; enrichment 38; both 41. The playground had graded nothing since W-56 lost queries.jsonl on 2026-08-20, and the README refuses to let the engine invent replacements. These 50 candidates were written by reading the ten documents and deciding what each question's right answer is, before any fux command ran. They are NOT installed: a golden set an agent installed for itself is the same green tick the README rejects. Arpit ratifies, then it becomes goldens/queries.jsonl."
status: graduated
timestamp: 2026-08-24T00:00:00Z
---

# Candidate goldens for the playground

> **GRADUATED 2026-08-24.** Arpit: *"you will have to create the goldens if
> needed. You will have to test them and then build out the reranker. All is on
> you."* The set is installed at `fux-playground/goldens/queries.jsonl` with
> its provenance recorded in that directory's README, and the run is filed at
> [`../regression/2026-08-24-rerank-and-goldens/`](../regression/2026-08-24-rerank-and-goldens/).
>
> **The §1 procedure was followed exactly**: installed with all nine
> `known_failure` predictions stripped, run once, and the result recorded as a
> measurement. **Baseline 28/50.** Of the nine predictions, five were right and
> four were wrong — every wrong one was a "vocabulary gap" I expected to fail
> and which passed. Seventeen failures were not predicted at all.
>
> **The section below is preserved as written, predictions included**, because
> a proposal edited after its measurement to look prescient is worthless as a
> record. Read §2's `known_failure` strings as *what I guessed*, not as what
> happened.

**Not installed. Deliberately.** This file is a proposal; the artefact it
proposes is `fux-playground/goldens/queries.jsonl`.

## §0 — Why this is a proposal and not a commit

`goldens/README.md` states the rule that makes the playground worth having:

> *"A playground whose goldens were invented by the engine under test is worse
> than no playground, because it produces a green tick that means nothing."*

An agent that drafts goldens **and installs them** has re-derived that failure
one level up. The engine did not invent these, but the thing that operates the
engine did, and nobody with an independent view of the corpus ever agreed that
`q014`'s right answer is `reference-deployment-tiers.md`.

There is a precedent for accepting agent-authored ground truth here —
`work/regression/2026-08-22-graph-acceptance/` — and it is a precedent for
**asking**: it was accepted on Arpit's direct instruction, on the stated
grounds that ground truth was *"fixed by construction before any fux command
ran."* That is the same standard, and the same permission is what is missing.

**Graduation trigger:** Arpit ratifies the set (whole, or query by query).
Ratified lines are written to `fux-playground/goldens/queries.jsonl`, this
proposal's status becomes `graduated`, and W-57 is re-scoped from the dead ids
`q005/q009/q011/q015` to the phenomenon tags in §3.

## §1 — How these were written, and the one contamination

**Rule 1 held.** Every query below was written after reading the ten documents
and before running any fux command in this session. The order is checkable:
the corpus was read in full, then the set was drafted; no `fux ask` was invoked
between those two acts.

**⚠ Three phrasings are contaminated and are NOT used.** In an earlier session
I ran three sanity queries against a copy of this corpus before deciding to
draft goldens:

- `how do I roll back the gateway`
- `which tiers are still on the legacy mesh`
- `data retention policy`

Those three phrasings — and near-variants of them — are excluded from this set,
because I know how the engine answers them and cannot un-know it. `q001`
deliberately reaches the same document by a different route
(*"steps to revert a bad calder gateway release"*).

**Rule 2 held.** Every expectation is a rank. No score appears anywhere.

**Rule 4 held.** Queries are phrased as a person types them, including the
ungrammatical ones. `q043` is *"we had a different retry policy in every
service"*, not `retry implementations ADR-0007`.

### The one field that may legitimately be set from a run

`known_failure` is **not ground truth**. `q`, `doc` and `max_rank` are claims
about the corpus and must precede the engine. `known_failure` is a claim about
*the engine's current state*, and recording it from a run does not violate
rule 1 — the golden it annotates was already fixed.

This matters practically: the nine `known_failure` entries below are
**predictions made by reading the corpus**, not observations. Some will be
wrong. A prediction that is wrong in the optimistic direction is invisible
(the golden simply passes); a prediction that is wrong in the pessimistic
direction **reddens the suite on day one as XPASS**, which is the mechanism
working exactly as designed but is a poor first impression of a new suite.

**Recommended ratification procedure:**

1. Arpit ratifies `q` / `doc` / `max_rank` — the ground truth. This is the
   part only a human can supply.
2. The set is installed **with the `known_failure` fields stripped**.
3. `python check.py` runs once. Whatever fails, fails honestly.
4. The `known_failure` fields are re-added **only** to the entries that
   actually failed, each with the reason observed rather than predicted.

Step 2 is the important one. It means the first run's red is a measurement,
and the `known_failure` set afterwards is a record rather than a guess.

## §2 — The set

50 queries. Ratify whole, or line by line; `#` comments are for this document
only and are not valid JSONL.

```jsonl
{"id": "q001", "q": "steps to revert a bad calder gateway release", "doc": "docs/runbook-gateway-rollback.md", "max_rank": 1}
{"id": "q002", "q": "how to roll back a helix mesh sidecar release", "doc": "docs/runbook-mesh-rollback-legacy.md", "max_rank": 1}
{"id": "q003", "q": "what replaced helix mesh", "doc": "docs/adr-0019-calder-gateway.md", "max_rank": 1}
{"id": "q004", "q": "why did we adopt a service mesh in the first place", "doc": "docs/adr-0007-helix-mesh.md", "max_rank": 1}
{"id": "q005", "q": "how long do we keep customer order history", "doc": "docs/policy-data-retention.md", "max_rank": 1}
{"id": "q006", "q": "what happened during the checkout outage", "doc": "docs/postmortem-checkout-outage.md", "max_rank": 1}
{"id": "q007", "q": "how many reviewers does a tier 1 deploy need", "doc": "docs/reference-deployment-tiers.md", "max_rank": 1}
{"id": "q008", "q": "who do I page when traffic between services is failing", "doc": "docs/guide-oncall-rota.md", "max_rank": 1}
{"id": "q009", "q": "I am shipping my first service where do I start", "doc": "docs/guide-onboarding.md", "max_rank": 1}
{"id": "q010", "q": "what does calderctl exit code 3 mean", "doc": "docs/reference-calderctl.md", "max_rank": 1}
{"id": "q011", "q": "what is the soak period for the revenue path tier", "doc": "docs/reference-deployment-tiers.md", "max_rank": 1}
{"id": "q012", "q": "how do I freeze an in flight rollout", "doc": "docs/reference-calderctl.md", "max_rank": 2}
{"id": "q013", "q": "am I allowed to be on call two weeks in a row", "doc": "docs/guide-oncall-rota.md", "max_rank": 1}
{"id": "q014", "q": "does an internal service page anyone overnight", "doc": "docs/reference-deployment-tiers.md", "max_rank": 2}
{"id": "q015", "q": "what is the current decision for east west traffic", "doc": "docs/adr-0019-calder-gateway.md", "max_rank": 1}
{"id": "q016", "q": "which proxy do we run between services today", "doc": "docs/adr-0019-calder-gateway.md", "max_rank": 1}
{"id": "q017", "q": "why did we move away from sidecars", "doc": "docs/adr-0019-calder-gateway.md", "max_rank": 1}
{"id": "q018", "q": "how much memory did the sidecar actually use", "doc": "docs/adr-0019-calder-gateway.md", "max_rank": 1, "known_failure": "predicted: sidecar is far denser in ADR-0007 and the legacy runbook; the MEASURED figure exists only in the superseding record"}
{"id": "q019", "q": "is helix mesh still in use anywhere", "doc": "docs/adr-0019-calder-gateway.md", "max_rank": 2}
{"id": "q020", "q": "which rollback do I use for a tier that has not migrated", "doc": "docs/runbook-mesh-rollback-legacy.md", "max_rank": 1, "known_failure": "predicted: ADR-0019 states this fact in prose and will outrank the runbook that IS the answer"}
{"id": "q021", "q": "why is the soak fourteen days now instead of two", "doc": "docs/reference-deployment-tiers.md", "max_rank": 2}
{"id": "q022", "q": "can I start new work against helix mesh", "doc": "docs/adr-0007-helix-mesh.md", "max_rank": 1}
{"id": "q023", "q": "what max surge should I use rolling back the node proxy", "doc": "docs/runbook-gateway-rollback.md", "max_rank": 1}
{"id": "q024", "q": "what max surge for a sidecar rollback", "doc": "docs/runbook-mesh-rollback-legacy.md", "max_rank": 1}
{"id": "q025", "q": "verify per node after rolling back", "doc": "docs/runbook-gateway-rollback.md", "max_rank": 1}
{"id": "q026", "q": "verify per service after rolling back", "doc": "docs/runbook-mesh-rollback-legacy.md", "max_rank": 1}
{"id": "q027", "q": "the rollback failed should I try it again", "doc": "docs/postmortem-checkout-outage.md", "max_rank": 3, "known_failure": "predicted: both runbooks carry the instruction near-verbatim and will occupy ranks 1-2; the postmortem is the only document that prices it at 18 minutes"}
{"id": "q028", "q": "how long does a gateway rollback take", "doc": "docs/runbook-gateway-rollback.md", "max_rank": 1}
{"id": "q029", "q": "how long does a mesh rollback take", "doc": "docs/runbook-mesh-rollback-legacy.md", "max_rank": 1}
{"id": "q030", "q": "pods skipped silently during a rollback", "doc": "docs/runbook-mesh-rollback-legacy.md", "max_rank": 2}
{"id": "q031", "q": "is the legacy runbook still valid", "doc": "docs/runbook-mesh-rollback-legacy.md", "max_rank": 2}
{"id": "q032", "q": "does the superseded networking ADR still apply anywhere", "doc": "docs/adr-0007-helix-mesh.md", "max_rank": 2}
{"id": "q033", "q": "why keep a superseded record in the repository", "doc": "docs/adr-0007-helix-mesh.md", "max_rank": 1}
{"id": "q034", "q": "my alert paged at 3am but my service is internal", "doc": "docs/guide-oncall-rota.md", "max_rank": 2}
{"id": "q035", "q": "I added a retry and things got worse", "doc": "docs/guide-onboarding.md", "max_rank": 1, "known_failure": "predicted: retry is dense throughout ADR-0007's context section; the diagnosis of DOUBLE retries is only in the onboarding guide"}
{"id": "q036", "q": "who approves a change to the revenue path", "doc": "docs/reference-deployment-tiers.md", "max_rank": 1}
{"id": "q037", "q": "what does the incident lead actually do", "doc": "docs/guide-oncall-rota.md", "max_rank": 1}
{"id": "q038", "q": "where do I record my service data class", "doc": "docs/guide-onboarding.md", "max_rank": 2}
{"id": "q039", "q": "what happens if I never state a classification", "doc": "docs/policy-data-retention.md", "max_rank": 2}
{"id": "q040", "q": "how long are backups kept", "doc": "docs/policy-data-retention.md", "max_rank": 1}
{"id": "q041", "q": "can I delete a customer record out of the backups", "doc": "docs/policy-data-retention.md", "max_rank": 1}
{"id": "q042", "q": "why is having two rollback procedures dangerous", "doc": "docs/adr-0019-calder-gateway.md", "max_rank": 2, "known_failure": "predicted: the calderctl reference calls the flag pair the most dangerous in the tool and will contest rank 1; both statements are true and about different things"}
{"id": "q043", "q": "we had a different retry policy in every service", "doc": "docs/adr-0007-helix-mesh.md", "max_rank": 1}
{"id": "q044", "q": "why not use ebpf instead of a proxy", "doc": "docs/adr-0019-calder-gateway.md", "max_rank": 1}
{"id": "q045", "q": "what is the cheapest tier to start on", "doc": "docs/guide-onboarding.md", "max_rank": 2, "known_failure": "predicted: pure vocabulary gap. cheapest and start on share no term with the corpus; the answer is most first services are tier 3"}
{"id": "q046", "q": "how do we stop a slow dependency taking down checkout", "doc": "docs/adr-0007-helix-mesh.md", "max_rank": 2, "known_failure": "predicted: the phrase appears in three documents with near-identical wording; the DECISION that addresses it is only in ADR-0007"}
{"id": "q047", "q": "blast radius of a bad config push", "doc": "docs/adr-0019-calder-gateway.md", "max_rank": 1}
{"id": "q048", "q": "how do I tell if someone else is mid incident before I deploy", "doc": "docs/reference-calderctl.md", "max_rank": 2, "known_failure": "predicted: vocabulary gap. the answer is exit code 3, which the reference explains as someone else is mid-incident, but incident is dense in the postmortem and the rota"}
{"id": "q049", "q": "what did we promise to fix after the outage and did we", "doc": "docs/postmortem-checkout-outage.md", "max_rank": 1}
{"id": "q050", "q": "a hazard we wrote down but never actually fixed", "doc": "docs/postmortem-checkout-outage.md", "max_rank": 2, "known_failure": "predicted: vocabulary gap. known gaps sections exist in both runbooks and the calderctl reference; only the postmortem draws the lesson"}
```

## §3 — Phenomenon coverage, for W-57's re-scoping

W-57 named `q005`, `q009`, `q011`, `q015` from the destroyed set. Those ids are
unrecoverable. **The replacement acceptance target is a phenomenon and a
count**, which survives renumbering:

| phenomenon | ids | count | what a failure means |
|---|---|---|---|
| **baseline retrieval** | q001–q014 | 14 | the engine cannot find a document by an ordinary question. Any red here is a bug, not a gap |
| **supersession** | q015–q022 | 8 | the superseded document outranks the one that replaced it. **This is the graph lane's target** |
| **near-duplication** | q023–q030 | 8 | the two ~80 %-identical runbooks are not discriminated. Step 3 is the only real difference; q023–q026 key on it directly |
| **staleness** | q031–q033 | 3 | *current* is treated as *correct*. The legacy runbook is still right for un-migrated tier 1 |
| **cross-document routing** | q034–q039 | 6 | the question is answered by the document that mentions the topic rather than the one that owns it |
| **vocabulary gap** | q045, q046, q048, q050 | 4 | the searcher's words are not the document's words. **This is the `ctx` field's and the dense lane's target**, and is why these four exist |

**W-57 acceptance, proposed:** the supersession band (q015–q022) reaches
8/8 with at most 1 `known_failure`, and no baseline query regresses.

**W-76 Phase 7 acceptance, proposed:** the vocabulary-gap band goes from
*n* passing with `--hybrid off` to *≥ n* with the dense lane on, and **nothing
in the baseline band breaks**. That is the same *fixes ≥ 3 / breaks = 0* shape
the phase gate already carries, expressed against queries that exist.

**W-76 Phase 8 acceptance, proposed:** the same four vocabulary-gap queries,
with `docs/` declared `enrich=true` and enrichment generated. This is the
cleanest measurement of enrichment in the repository, because these four
queries were written *specifically* to have no lexical route to their answer.

## §4 — What I am NOT claiming

- **Not that these are the right goldens.** They are one reading of the corpus
  by one reader. `q014`, `q021`, `q027`, `q038` and `q039` are genuine
  judgement calls where two documents could defensibly be the answer; they
  carry `max_rank: 2` or `3` for that reason rather than because the engine
  is expected to struggle.
- **Not that the nine `known_failure` predictions are correct.** See §1.
- **Not that 50 is enough.** The destroyed set was ~50 against a different
  corpus; matching the count is a coincidence of ambition, not a target.
- **Not that this is a substitute for graded relevance.** Every entry here is
  binary — one document, one rank bound. The old set's value came partly from
  a human having *graded* results, and that is not reconstructible.

## §5 — Reference

- The rules these follow — [`fux-playground/goldens/README.md`](../../archive/v0.30-rev1-planning/README.md)
- The harness — `fux-playground/check.py`
- The loss — W-56, 2026-08-20
- The precedent for agent-authored ground truth accepted on instruction —
  [`work/regression/2026-08-22-graph-acceptance/`](../regression/2026-08-22-graph-acceptance/)
- W-76 Phases 7 and 8 — closed 2026-08-24; the outcome is [`IMPLEMENTATION.md`](../IMPLEMENTATION.md)'s W-76 row
