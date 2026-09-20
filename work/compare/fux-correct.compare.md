---
type: Compare Doc
title: "`fux correct` — when the wrong document was served, how does a human fix it durably?"
description: "For a question the corpus answers, fux served the wrong document. Four ways to correct that: an editorial pin (Solr elevate), human document expansion (a question line on the document's enrichment record), Rocchio-style relevance feedback (session-only), or click/log learning (forbidden by L3 and L8). Accepted by Arpit 2026-09-13: a human-authored question line in the document's existing enrichment file, marked as human, surviving regeneration, reported-never-refused by `--check`, doubling as an eval row; a rare `--pin`; negative corrections refused. Plus the guide skill and agent steering that make it usable."
status: accepted
timestamp: 2026-09-13T00:00:00Z
filed: 2026-09-13
accepted: 2026-09-13
---

# `fux correct` — fixing the wrong answer, durably

**Model: Opus** — the mechanism touches L3 (no model), L8 (no use record) and
SR-ENRICH's contract; the wrong shape is a per-query rule that rots silently.

**Found:** Arpit, 2026-09-13 — *"I believe for the question that was asked a
different document should have been served. How can I correct that?"*
**Owning records:** [SR-ENRICH](../../records/0137_enrich.md) (the enrichment
file, `ctx`, `--check`), [SR-EXPAND](../../records/0149_expand.md) (the
refusal), [SR-PROVENANCE](../../records/0142_provenance.md).
**Item:** **W-162 — SHIPPED 2026-09-14.** What was built is
[SR-ENRICH](../../records/0137_enrich.md) decisions 19, 19a and 19b;
[`work/IMPLEMENTATION.md`](../IMPLEMENTATION.md) §2026-09-14 W-162 is the
account of what shipping it found. 🔴 **§6's generalisation measurement was
NOT done** and is [W-175 → W-204](../open/W-204-golden-outputs-scoring-and-version-benchmark.md) — the
one claim that made (b) beat (a) is still unmeasured, and this doc's §5
reopen trigger is what fires if it fails.

---

## Verdict block

| | |
|---|---|
| **status** | **accepted** — Arpit, 2026-09-13 |
| **the call** | **(b) human document expansion, as an addition to doc2query enrichment** — `fux correct "<question>" <doc>` appends one human-authored question line to the document's existing `.fux/enrich/<sha>.md`; same file, same `ctx` field, different author. **Plus** a rare, explicit `--pin`. **Negative corrections refused.** |
| **also ruled** | ship the guide skill, agent steering, `--json` provenance, doctor rows and glossary entries with it — *"skills, steering documents, whatever could help the end user or the AI agent"* |
| **confidence** | high on the mechanism (it is the field `enrich` already indexes); the *gain* is measured per correction by the eval row it creates |

---

## 1 · The options

| | option | precedent | fits fux? |
|---|---|---|---|
| (a) | **Editorial pin** — exact query → doc forced to #1 | Solr `QueryElevationComponent` (`elevate.xml`, a committed file); Elasticsearch pinned queries; SharePoint promoted results | yes, but brittle — one phrasing fixed, the next still wrong. Kept as the rare `--pin` |
| (b) | **Human document expansion** — add the words people *ask with* to the document's index record | the deterministic cousin of doc2query (Nogueira et al. 2019); a subject heading on a catalogue card | **best fit** — generalises across phrasings, deterministic, degrades gracefully |
| (c) | **Relevance feedback (Rocchio 1971)** — move the query toward the chosen doc | SMART; RM3 is its no-human descendant | query-time only; nothing persists. It *is* what `--expand` does by hand |
| (d) | **Click/log learning** | every web engine | **out** — L8 forbids a committed use record, L3 forbids a model in the path |
| (e) | **Fix the source** — edit the document so it says the words | fux's own philosophy | always the first suggestion; fails when the user does not own the doc |

## 2 · Why (b) is an addition, not a new mechanism

- fux **already has doc2query**: `fux enrich` writes 5–10 model-written
  questions to `.fux/enrich/<source sha>.md`, indexed as **`ctx`**, pinned to
  the document's content sha, self-retrieval-checked by `--check`
  ([SR-ENRICH](../../records/0137_enrich.md) decisions 15–16; built and
  unproven).
- A correction is **the eleventh line, in a human's handwriting** — the
  question that actually failed, which is the highest-value question the file
  can hold. No new directory, no new field, no new ranking code.
- **Two things are new:** authorship provenance (human lines survive
  regeneration and are visible in provenance), and the eval row.

## 3 · The design

1. `fux correct "<question>" <doc>` appends `<question>` to the doc's
   enrichment body, marked human (a line marker or a `corrections:` frontmatter
   list — W-162 decides the spelling with SR-ENRICH's frontmatter rule in view:
   frontmatter is stripped before indexing, so the *marker* must not be what
   carries the text).
2. **Human lines survive `fux enrich` regeneration**; model lines may be
   overwritten.
3. **`--check` reports a human line, never refuses it.** A correction is by
   definition a question that failed retrieval; failing self-retrieval is the
   case it exists for.
4. **Every correction is an eval row** in a local set (never the sealed golden
   — that stays Arpit's). A later ranking change that breaks it fails a check.
5. **`--pin` (opt-in, rare):** exact question → doc at #1, labelled `pinned`
   in output and receipt; `fux doctor` suspends a pin whose document's content
   sha changed until re-affirmed. The vocabulary effect never suspends.
6. **Negative corrections are refused** with a pointer: "don't serve X" is a
   supersession or archive problem — `supersedes` edge or `archived=`,
   corpus-wide.
7. **Provenance:** `via: ctx (human)` vs `ctx (model)` in `--why`, `--json`
   and the receipt.
8. **PII:** the question text passes `pii.toml` like any enrichment body.

## 4 · Law check

- **L2** — a human note; no content copied. **L3** — the file is a source
  input; nothing dated enters the index. **L8** — a signed human decision
  committed in a PR is not a use record, but it *does* reveal that a question
  was asked; the record says so plainly rather than pretending otherwise.

## 5 · Reopen trigger

- If human lines measurably fail to generalise (corrections fix only their
  exact phrasing on the eval set), (a) is the honest mechanism and (b) is
  withdrawn.
- If `ctx`'s weight has to be raised for corrections to bite, that is a
  ranking change and goes through W-156's rule, not through this record.

## 6 · What is tested, what is measured, and the keep/remove call

**Order: implement → test → measure the generalisation claim → call.** The
mechanism is small enough to build first; what must be *measured* is the one
claim the pin cannot make — that a human line helps phrasings other than its
own.

| | how | keep if | remove if |
|---|---|---|---|
| the verb writes and preserves human lines | unit tests: append, regeneration preserves, marker survives, `--check` reports-never-refuses | tests hold | — |
| the eval row | each correction's own question retrieves its document at top-3 after ingest; the check runs in the suite | holds for every filed correction | a correction that cannot retrieve its own document is *reported* (that is what the eval row is for), never silently dropped |
| **generalisation** (the reason (b) beat (a)) | pre-registered on golden: for N corrections, M held-out paraphrases per correction, written blind by Codex; measure top-3 retrieval of the corrected document on the paraphrases, before vs after | paraphrase retrieval gain clears the SR-RS d19 floor, **and** no golden answerable question loses its top-1 (the tilt check) | fails → human lines are **no longer indexed into `ctx`** (they share the field with model lines, so there is no per-author weight to turn down); they stay as eval rows, and exact-question `--pin` becomes the default effect |
| `--pin` | tests: exact-match only, suspended on sha change, labelled everywhere | tests hold | — (it is opt-in and rare by design) |
| the guide skill and steering | the `test_setup_agents` renderings equal the templates; a proposal-not-write assertion in the policy test | tests hold | — |

- **Do not measure with the 20 blind unanswerables** or the sealed key's
  questions as the correction source — corrections must come from real
  failures on a corpus the measurer did not grade.
- **Ambiguous → Arpit**, per-query rows filed.

## Reference

- Rocchio — *Relevance feedback in information retrieval*, in Salton (ed.),
  *The SMART Retrieval System*, 1971.
- Nogueira, Yang, Lin, Cho — *Document expansion by query prediction*, 2019.
- Apache Solr — `QueryElevationComponent` documentation; Elasticsearch —
  *Pinned query*.
- Live: [SR-ENRICH](../../records/0137_enrich.md) decisions 15–17;
  [`src/fux/enrich.py`](../../src/fux/enrich.py).
