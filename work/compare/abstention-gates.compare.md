---
type: Compare Doc
title: "Abstention — which gates decide `answerable`, and how the signals combine"
description: "Graduates option C of the abstention-gate proposal. fux says `answerable: true` on all 20 blind-authored unanswerable questions because the boolean is false only when nothing scores. Nine candidate mechanisms in two gates — a retrieval gate (IDF-weighted coverage, QPP, graph coherence, identifier hard-fail) and an answer gate (passage co-occurrence, answer-type check, verification floor) — plus C2 and consumer steering. Ruled by Arpit 2026-09-13: the verdict is a GATE CHAIN, never a blended number, and every independent signal is RETURNED as its own field, visibility set in output.toml. Which gates ship, and their floors, is proposed, not accepted."
status: proposed
timestamp: 2026-09-13T00:00:00Z
filed: 2026-09-13
---

# Abstention — the gates, and how they combine

**Model: Opus** — calling a gate on a class of question that scores *something*
by construction; a floor fitted to the wrong 20 questions is the
moving-threshold failure in its purest form.

**Graduates:** [`proposals/abstention-gate.md`](../proposals/abstention-gate.md)
option **C** (build abstention, measure in fux-lab). Options **A** and **B**
there are untouched by this doc and still owed a ruling.
**Owning records:** [SR-CONFIDENCE](../../records/0141_confidence.md),
[SR-REFER-PLANE](../../records/0127_refer-plane.md),
[SR-OUTPUT-DEFAULTS](../../records/0143_output-defaults.md),
[SR-RS](../../records/0133_predictions.md) (the measurement rules).
**Item:** none yet — one is filed per gate when Arpit picks it.

---

## Verdict block

| | |
|---|---|
| **status** | **proposed** on *which* gates and their floors; **two things are already ruled** (Arpit, 2026-09-13) and are recorded here as rulings, not proposals |
| **ruled 1** | **the verdict is a gate chain — weakest link — never a blended number.** `answerable` = every gate passed; `band` = how comfortably. One failed gate ⇒ `answerable: false`, and the output names *which* gate and why |
| **ruled 2** | **every independent signal is returned as its own field** — NQC, clarity, coherence, IDF-coverage, co-occurrence, answer-type — with visibility configured in **`.fux/output.toml`**, the surface the band uses today |
| **proposed** | ship **C2 (1) and consumer steering (9) first** — no measurement needed; then **answer-type (4) and passage co-occurrence (3)** as the first measured gates, because they alone reach the u017 class; QPP (5) and coherence (6) after the graph plane lands in `ask` |
| **confidence** | high on the shape; the floors are **unmeasured** and stay provisional until the golden key carries enough unanswerable questions to clear a net of 6 |

---

## 1 · The finding, restated once

- `answerable` is `false` **only when nothing scores above zero**
  (SR-CONFIDENCE decision 3). A question built from the corpus's own words —
  *"the names of all four regions"*, where the corpus says *four regions* and
  never names them — always scores something and can never abstain.
- 20 of 20 blind unanswerables answered, twice, fourteen days apart; five
  ranking changes in between moved none of them
  ([2026-08-28](../regression/2026-08-28-blind-unanswerable/report.md),
  [2026-09-11](../regression/2026-09-11-blind-unanswerable-rerun/report.md)).
- **Reframing that drives everything below:** today's band answers *did
  something match?* Arpit wants *does the matched text contain the answer?*
  The second is decidable only in the refer plane, on fetched bytes.

---

## 2 · Two gates in series

```
retrieval gate   the index has something FOCUSED
                 IDF-coverage ≥ floor  AND  QPP focus ≥ floor  AND  coherence ≠ scattered  AND  id-present
answer gate      the fetched text HAS the answer
                 content terms co-occur in one passage  AND  the expected answer type is present  AND  passage re-score ≥ floor
verdict          answerable = every gate passed;   band = margin by which they passed
```

A question must pass both. Today only a crippled retrieval gate exists.

---

## 3 · The candidate mechanisms

| # | mechanism | gate | catches | deterministic | cost | needs measurement |
|---|---|---|---|---|---|---|
| 1 | **`weak` ⇒ `answerable: false`** (proposal's C2) | verdict | the standing contradiction: band says *do not answer*, boolean says go | yes | tiny | **no** — a rule |
| 2 | **IDF-weighted coverage** — `missing` weights rare terms, ignores stopwords | retrieval | *names* is the rare missing term in the u017 question | yes | small | yes |
| 3 | **Passage co-occurrence** (C3) — content terms together inside one passage window of the fetched doc | answer | document-level match, passage-level absence | yes | small — refer holds the bytes; shares code with SDM | yes |
| 4 | **Answer-type check** — opener ⇒ expected type: *how many* → number, *when* → date, *who* → capitalised name, *names of all N* → list ≥ N; checked in the passage near the terms | answer | **the u017 class** — the only mechanism that reaches a question assembled from the corpus's own words | yes — openers + token classes | medium | yes |
| 5 | **QPP** — NQC (spread of top-k scores / corpus score) and Clarity (KL of top-k vocabulary vs corpus) | retrieval | a flat list of equally mediocre matches | yes — index stats only | medium | yes |
| 6 | **Graph coherence** — edge density among the top-k, largest-community share, PPR self-mass | retrieval | five hits from five unrelated corners | yes | small once W-161 lands | yes; degrades to *unknown* on a link-poor corpus, never to *unanswerable* |
| 7 | **Identifier hard-fail** — the query carries an id no document has as an exact token | retrieval | id questions about things that don't exist | yes | tiny; rides on the identifier field ([search-improvements #3](../proposals/search-improvements-v3.md)) | yes, small |
| 8 | **Verification floor** — `answer` whose passage re-score on the bytes falls below a floor abstains | answer | index says yes, bytes say no | yes | small | yes |
| 9 | **Consumer steering** — MCP descriptions and guide skills: `answerable: false` or `weak` ⇒ *the documents don't say*, show `missing`; never paraphrase a weak hit | outside the engine | the agent answering anyway | n/a | text | **no** |

**Why not one number.** A single `0.73` averages independent failure modes: a
perfect passage in a scattered list and a scattered passage in a tight list
average the same and mean the opposite. An agent handed `0.73` hedges in prose;
an agent handed `answerable: false` stops — SR-CONFIDENCE already rests on that
asymmetry. And a weight vector cannot be defended at ~10 golden unanswerables;
one signal, one floor, one two-sided measurement can.

---

## 4 · What is returned — the output surface (ruled)

- Each signal is its own key in the confidence block: `nqc`, `clarity`,
  `coherence`, `idf_coverage`, `cooccurrence`, `answer_type` (with `expected`
  and `found`), `verification`. `band` and `answerable` stay.
- A failed gate is named: `failed: ["answer_type"]`, with the reason beside it.
- **`output.toml` decides which appear**, per verb, exactly as it decides the
  band today ([SR-OUTPUT-DEFAULTS](../../records/0143_output-defaults.md)).
  `--json` carries all of them regardless; the prose surface is the
  configurable one.
- Node returns the same keys, byte-equal.

---

## 5 · Sequencing, and the measurement rules that bind it

1. **1 + 9 now** — a rule and text; no measurement owed. They remove a
   contradiction and a consumer failure, not a ranking behaviour.
2. **4 + 3** — the first measured gates; both live in refer and reach the u017
   class.
3. **2, 7** — cheap retrieval-side signals.
4. **5, 6, 8** — after W-161 (coherence needs the plane in `ask`) and after
   the answer gate exists (8 is its floor).

Binding on every measured gate:

- **Pre-register both directions** (SR-RS decision 22): more abstentions on
  unanswerable questions **and** no new abstentions on answerable ones.
- **Power:** ~10 golden unanswerables cannot clear the net-6 floor (SR-RS
  decision 19). The key needs more — **a Codex task, never Claude's**.
- **Never tune on the 20.** They are a frozen control.
- **One gate per measurement.** Two gates in one arm cannot attribute the
  delta.

---

## 6 · What each gate would touch

| # | records | code |
|---|---|---|
| 1 | SR-CONFIDENCE d3 | `query/confidence.py` |
| 2 | SR-CONFIDENCE | `query/confidence.py` |
| 3 | SR-REFER-PLANE, SR-CHUNKING, SR-CONFIDENCE | `refer/` |
| 4 | SR-CONFIDENCE, SR-REFER-PLANE, a new section on answer types | `refer/`, `query/confidence.py` |
| 5 | SR-CONFIDENCE, SR-RUNTIME-STATS | `query/confidence.py`, `derive/` |
| 6 | SR-CONFIDENCE, SR-GRAPH | `graph/`, `query/confidence.py` |
| 7 | SR-CONFIDENCE, SR-RANKING | `query/analyzer.py`, `query/confidence.py` |
| 8 | SR-ANSWER, SR-REFER-PLANE | `refer/`, `query/refer_answer.py` |
| 9 | SR-AGENT-POLICY, SR-MCP | `templates/agents/`, `mcp.py` |
| all | SR-OUTPUT-DEFAULTS, SR-NODE-SEARCH | `output_config.py`, `node/` |

---

## 7 · Reopen trigger

- If a measured gate abstains on answerable golden questions above its
  pre-registered ceiling, that gate is withdrawn, not loosened.
- If the golden key cannot be made to carry enough unanswerable questions for
  a decidable verdict, the gates stay opt-in and unproven, and the headline
  quality number keeps *"abstains 0 of N"* beside it (option **B** of the
  proposal).

## Reference

- Cronen-Townsend, Zhou, Croft — *Predicting query performance*, SIGIR 2002
  (Clarity).
- Shtok, Kurland, Carmel, Raiber, Markovits — *Predicting query performance by
  query-drift estimation*, TOIS 2012 (NQC).
- Harabagiu, Moldovan et al. — *FALCON: boosting knowledge for answer
  engines*, TREC-9 2000 (answer-type matching).
- Jardine & van Rijsbergen — the cluster hypothesis, 1971.
- Metzler & Croft — SDM, SIGIR 2005 (the co-occurrence window).
- Live: [`src/fux/query/confidence.py`](../../src/fux/query/confidence.py);
  the two blind runs above.
