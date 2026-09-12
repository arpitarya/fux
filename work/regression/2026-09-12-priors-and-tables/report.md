---
type: Report
description: "Five open items measured on the frozen golden ladder: the four ranking priors answer NO, the heading control's mechanism is not established, tables move ranking, and W-115's instrument still does not exist."
items: W-143, W-97, W-142, W-144, W-115
run: 2026-09-12-priors-and-tables
classification: informed
engine: fux-engine 2.0.0-alpha.7
engine_sha: 676e973
pre_registration: work/regression/2026-09-12-priors-and-tables/PRE-REGISTRATION.md
filed: 2026-09-12
---

# Priors, tables and headroom — five items on the golden ladder

**Every endpoint here is key-free.** No arm reads the golden answer key, so
none of these results waits on [W-145](../../open/W-145-codex-regenerates-the-key.md).

⚠ **Read [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md) §0 first.** The `0 broken`
bar is Arpit's and predates this session; the probe set was authored before the
first number but **committed after it**, and git cannot prove that half.

---

## Authorship

| artifact | author | could reach the queries? | could reach the answers? |
|---|---|---|---|
| the `0 broken` bar, the intent-split requirement | **Arpit**, 2026-09-11 | n/a | n/a |
| `priors-probes.jsonl` (26 probes) | Claude, this session | wrote them | **wrote them** — truth is mechanical from declarations |
| the four sweep grids, the pairwise criterion | Claude, this session | — | — |
| `table_flen.py`, `heading_control.py`, `priors_sweep.py` | Claude, this session | — | — |
| the golden ladder | Claude, 2026-09-12, built blind | no | no |
| the golden answer key | Claude (stopgap, W-145) | — | **not read by any arm here** |
| this analysis | Claude, this session | yes | no |

**`informed`.** No delta against any other run is stated.

---

## 1. W-143 / W-97 — the four ranking priors: the answer is **NO**

**Arpit's question, 2026-09-11:** *does any single global value clear a
`0 broken` bar?* **No. Not one, for any of the four knobs, on any rung.**

26 probes, 13 current-seeking and 13 history-seeking, truth read off the
`supersedes:` and `archived=true` declarations.

### `superseded_weight` — `rung-seed`

| value | right | fixed | broken | current | history |
|---:|---:|---:|---:|---:|---:|
| **1.0** (shipped) | 21 / 26 | — | — | 12 / 13 | 9 / 13 |
| 0.9 | 21 / 26 | 1 | **1** | 13 / 13 | 8 / 13 |
| 0.75 | 19 / 26 | 1 | **3** | 13 / 13 | 6 / 13 |
| 0.5 | 18 / 26 | 1 | **4** | 13 / 13 | 5 / 13 |
| 0.25 | 18 / 26 | 1 | **4** | 13 / 13 | 5 / 13 |
| 0.1 | 18 / 26 | 1 | **4** | 13 / 13 | 5 / 13 |
| **0.0** | 18 / 26 | 1 | **4** | 13 / 13 | 5 / 13 |

**Read the last two columns, not the first.** Every value below 1.0 drives
current-seeking to a **perfect 13/13** and takes history-seeking apart in the
same step. The knob does exactly what it is built to do, and the cost is
one-for-one.

**This is `P-SUPERSEDE`'s failure reproduced on purpose-built data with the
mechanism now visible.** W-143 predicted it in words — *"supersession belongs to
the query's intent, not to the document; a per-document multiplier cannot
express that"* — and this is that sentence as a table.

### All four knobs, every rung — the candidates that "clear"

| knob | rung-seed | rung-00100 | rung-01000 |
|---|---|---|---|
| `superseded_weight` | 0.9 **breaks 1** (`p07`) | 0.9 clears, **net +1** | 0.9 **breaks 1** (`p15`) |
| `archived_weight` | 0.75 **breaks 1** (`p20`) | 0.75 **breaks 1** (`p20`) | 0.9 / 0.75 clear, **net +1 / +2** |
| `recency_half_life_days` | 365 **breaks 9** | 365 **breaks 8** | 365 **breaks 8** |
| `rerank_weight` | 0.25+ **breaks 1** (`p07`) | no effect at any value | 0.25+ clears, **net +1** |

🔴 **Not one candidate survives two tests.**

1. **Every value that clears on one rung breaks on another**, and on a
   *different probe* each time (`p07`, `p15`, `p20`). A value that clears on one
   rung has found a corpus, not a default — which the pre-registration fixed as
   a rule before these numbers existed.
2. **Every clearing net is +1 or +2**, and ADR-RS decision 19 puts the floor of
   all floors at **6**. A net of 1 or 2 cannot clear α = 0.05 at any discordant
   count, so even read alone it is *no detected change*.

### `recency_half_life_days` is the sharpest case

| value | current | history |
|---:|---:|---:|
| 0 (off, shipped) | 11–12 / 13 | 8–9 / 13 |
| 730 | **13 / 13** | 1 / 13 |
| 365 and below | **13 / 13** | **0 / 13** |

At any half-life of a year or less, history-seeking scores **zero**. The prior
does not degrade that slice; it **erases** it.

### Headroom (ADR-RS decision 22b), observed

Improvement 5–7 of 26 · regression 19–21 of 26, per rung. **Both directions have
headroom, so neither is Inconclusive** — the answer `NO` is a measured negative,
not an absence of measurement.

---

## 2. W-142 — the `heading` control: its mechanism is **not established**

C4 asked a boolean about an event that never happens. This asks a **count**, and
carries its own feature-off arm: `bm25f.heading` at 3.0 (shipped), 1.0 and 0.0
(*ignore this field*), over all 124 questions at `rung-01000`, k = 5.

| heading weight | sibling hits in top-5 | seed hits | queries with ≥ 1 sibling |
|---:|---:|---:|---:|
| **3.0** (shipped) | 256 | 272 | 90 / 124 |
| 1.0 | 265 | 259 | 92 / 124 |
| **0.0** (off) | 258 | 259 | 90 / 124 |

Paired over queries, 3.0 against 0.0: `b = 16`, `c = 21`, **discordant 37, net 5**.

🔴 **Below the floor of 6, so the mechanism is not established — and the finding
is more interesting than a pass would have been.** Switching the heading field
off **entirely** barely changes how many heading-matched distractors sit in the
window. **They are not winning on headings; they are winning on body
similarity.** The control as C4 conceived it tests a mechanism that is not the
one operating, and any claim resting on it is unsupported.

⚠ The distractors are genuinely heading-matched — 392 `ext/sibling/` documents
reuse the seed documents' headings and document types verbatim. **The corpus is
not the problem this time.** The endpoint is.

---

## 3. W-144 — tables do inflate `flen`, and it moves ranking

**Verification gate passed first:** the tool's recomputed `flen[body]` equals the
committed value for **every** document on every rung, so it is measuring the
shipped pipeline. (It failed on four documents until PII redaction was applied
before extraction, as ingest does — a 48-token gap on the `.eml`.)

### Headroom — large, and concentrated

| rung | any table token | **share ≥ 10 %** | median share | max share | median `Δwlen` | max `Δwlen` |
|---|---:|---:|---:|---:|---:|---:|
| `rung-seed` | 11 / 20 | **7 (35 %)** | 0.344 | 0.616 | 0.252 | 0.513 |
| `rung-00100` | 39 / 100 | **34 (34 %)** | — | — | — | — |
| `rung-01000` | 318 / 1000 | **313 (31 %)** | — | 0.804 | — | 0.579 |

A third of the corpus, and the most table-heavy document's length normaliser
would fall by **58 %**. `avg_wlen` at rung 1 000 moves 151.5 → 133.8.

### The ranking arm — it moves, in the predicted direction

| rung | top-1 changes | top-10 changes | new top-1 is **more** table-heavy | less |
|---|---:|---:|---:|---:|
| `rung-seed` | 12 / 124 | 76 / 124 | **11 / 12** | 0 |
| `rung-00100` | 16 / 124 | 100 / 124 | **14 / 16** | 1 |
| `rung-01000` | 16 / 124 | 82 / 124 | **16 / 16** | 0 |

**41 of 44 top-1 changes promote a more table-heavy document, 1 goes the other
way.** The proposal's mechanism is real and one-directional. **This is not a
null**, and W-144's *"a null closes this item"* clause is not reached.

### The quality endpoint saturates — Inconclusive, not a null

A query built from a `df == 1` term in a table-heavy document's **prose** — the
proposal's own sentence, with mechanical truth:

| dilution | probes | `hit@1` shipped | `hit@1` no-table-`flen` | discordant |
|---:|---:|---:|---:|---:|
| 0 | 12 | 12 / 12 | 12 / 12 | **0** |
| 4 | 12 | 12 / 12 | 12 / 12 | **0** |
| 8 | 12 | 12 / 12 | 12 / 12 | **0** |
| 16 | 12 | 12 / 12 | 12 / 12 | **0** |

🔴 **Zero headroom at every dilution → Inconclusive in both directions (22d).** A
`df == 1` term's idf dominates so completely that length normalisation cannot
reach it; adding sixteen of the document's commonest prose terms does not dent
it. **The endpoint with mechanical truth has no headroom, and the endpoint with
headroom (the 124 questions) has no truth.** That is W-115's problem in a
different costume, and it is the honest state of W-144.

---

## 4. W-115 — the golden ladder is the **third** corpus that cannot see it

Two arms of `extract_fields` + `parse_document` — `94231b2` (pre-W-115) and
`676e973` (HEAD) — over the same 994 `rung-01000` documents (the 6 with PII hits
are excluded so redaction cannot confound the arms).

| field | documents differing |
|---|---:|
| `title` | **0 / 994** |
| `flen` | **0 / 994** |
| `terms` hash | **0 / 994** |
| term count | **0 / 994** |
| `phrases` | 1 / 994 |

**The single `phrases` difference is not W-115.** `seed/01-sop-temperature-excursion.md`
has 13 headings; the old tree hard-codes `max_phrases = 12` and HEAD defaults to
32, so the old list is an exact prefix of the new one. That is **W-116's**
change, de-confounded here the same way W-116's own report used a third arm.

🔴 **So W-115 moves 0 of 994 documents on the golden ladder.**

| corpus | grades? | headroom? |
|---|---|---|
| fux-playground | yes | 🔴 none — byte-identical index |
| fux's own repo | 🔴 none | yes — 304 documents moved |
| **the golden ladder** | yes (phase 5) | 🔴 **none — 0 of 994** |

**And now the reason is named rather than guessed.** W-115 changed heading
grammar for `.rst`/`.adoc`/`.org`, citation-path decoding, table banding for
CSV/XLSX row chunking, and heading skeletons. **The ladder carries `.md`, `.txt`,
`.yaml`, `.eml` and `.html` and none of the rest.** W-115 stays unmeasured for
quality — but it is now unmeasured for a **measured, specific, fixable** reason.

---

## 5. What this run does not do

- It files **no verdict that changes a default.** W-97's output is a candidate
  table with **no recommendation**; any default change is Arpit's ADR-TUNE
  amendment.
- It states **no delta against another run**.
- It says nothing about rungs above 1 000, which do not exist.
- It does not close W-144 — the mechanism is confirmed, the quality question is
  Inconclusive.
- It does not close W-115 — it closes *"is the ladder the instrument?"* with a
  **no**.

---

## Reference

- [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md) — and §0 on what git can prove here
- [`ANALYSIS.md`](ANALYSIS.md) — the repro commands and what each item owes next
- [`VERDICT-W143.md`](VERDICT-W143.md) — the adjudication of Arpit's question
- The corpus: [the golden ladder run](../2026-09-12-golden-ladder/report.md)
- [ADR-RS](../../../docs/adr/0133_predictions.md) decisions 13, 15, 19, 22, 23 ·
  [ADR-TUNE](../../../docs/adr/0135_tuning.md) ·
  [ADR-ARCHIVED-CONTENT](../../../docs/adr/0134_archived-content.md)
