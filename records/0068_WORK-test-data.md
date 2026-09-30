---
type: Standing Record
kind: process
name: SR-WORK-TESTDATA
title: "SR-WORK-TESTDATA (0068) — the source of what test data must carry and how it is authored: checklist T, authoring rules A, feature recipes R; prompts are disposable copies"
description: "The one maintained source for golden test data — what every seed document, question set and rung must carry (T1–T14), how it is authored (A1–A24), and the input each ranking feature needs (R1–R10). Prompts are written from it when new data is needed, link it, and are deleted once their data lands."
status: accepted
date: 2026-09-22
amended: 2026-09-30
feature: the test-data source — what a seed document, a question set or a rung must contain, how it is authored, and the input each ranking feature needs
owns: [tests/test_test_data_prompts.py@a84a10681d8b, tools/golden-history@b6156bbc0ceb, tests/test_golden_history.py@ffae3050d744]
laws: [L0, L11]
timestamp: 2026-09-22T00:00:00Z
content_sha: 0afe3bd869ee15f8e0b5f29463c336ce6eaeacd0c77df7d080ee868efe8db475
ratifies: "Arpit, 2026-09-22 — 'note it down that this is also one of the cases that need to be tested. So in future, the prompt or test data creation should account for this use case … create a work document which will just have pointers what all things test data creation should have … keep everything precise … I was talking about SR work document' · Arpit, 2026-09-27 — 'prompts can have copy of those but sr should be the source and should be maintained … delete them and when a new test data needs to be created create new prompts'\"
---

<!-- COMPONENTS-START — GENERATED from records/README.md's OWNERSHIP and DESCRIBES tables by scripts/gen-components.py. Do not edit by hand: change the table, then run `python scripts/gen-components.py --write`. -->

**Owns** — the components this record decides:

- [`tests/test_golden_history.py`](../tests/test_golden_history.py) · file
- [`tests/test_test_data_prompts.py`](../tests/test_test_data_prompts.py) · file
- [`tools/golden-history/`](../tools/golden-history) · dir

<!-- COMPONENTS-END -->

# SR-WORK-TESTDATA — what test data must carry, and how it is authored

## §1 — For humans

**This record is the one list of what test data must have.** Every seed
document, question set and rung is authored against it. It is **maintained
here and nowhere else**.

**Prompts are copies, and they are thrown away.** When new test data is needed,
a new prompt is written *from this record*, run once, and deleted when its data
lands. On any disagreement between a prompt and this record, **the record
wins**. The thirteen prompts that authored generations 1–3 were deleted on
2026-09-27; everything they knew that was worth keeping is below.

**Three parts:**

- **The checklist, `T1…T14`** — *what* the data must contain (decision 2).
- **The authoring rules, `A1…A24`** — *how* a set, a document or a rung is
  written: custody, format, hardness, naming (decision 7).
- **The feature recipes, `R1…R10`** — for each ranking feature, the exact
  input the documents must carry and the questions that exercise it
  (decision 8).

---

## §2 — For agents

### Context

On 2026-09-22 two measurements
([the step-input run](../work/regression/2026-09-22-w168-step-inputs/report.md),
[the anchor census](../work/regression/2026-09-22-anchor-input-census/report.md))
found that **four of W-168's eight remaining ranking steps had no input in the
seed at all**. The rules that would have caught it were scattered across SR-RS,
SR-WORK-GOLDEN, the golden README and thirteen prompts. This record gathered
the checklist on 2026-09-22; on 2026-09-27 it absorbed the prompts too.

### Decision

1. **This record IS the source of what test data must have.** An item whose
   rule lives in another record links that record and restates nothing
   ([SR-LAW-0](0002_LAW-0-authority.md) decision 1). Everything else about
   authoring test data is stated here, once.

2. **The checklist.** Every seed document, question set and rung is authored
   against it. **An item a piece of test data does not carry is named as
   *not carried* in its prompt and its report — never silently skipped.**

   | # | the data must carry | home |
   |---|---|---|
   | **T1** | **The input each feature under test acts on.** A missing input is a data defect, not a null | [SR-RS](0133_predictions.md) d23 · recipes R1–R10 |
   | **T2** | **One coverage tag per feature, named for the step it gates** — not a tag that merely resembles it (`link_dependent` is multi-hop; `vocabulary_gap` is paraphrase) | [SR-RS](0133_predictions.md) d23c · A15 |
   | **T3** | **Headroom** — questions today's engine does not already answer, made hard *by construction* (a count of discriminations), **never** by consulting the engine's results | [SR-WORK-GOLDEN](0066_WORK-golden.md) d13 · [SR-RS](0133_predictions.md) d19 · A13 |
   | **T4** | **Anchor-only vocabulary** | **stated here** — decision 3 · R1 |
   | **T5** | **Abbreviation and glossary pairs** | **stated here** — decision 3 · R2 |
   | **T6** | **Identifiers of the failing shape** — shared prefix + short number, near neighbours, in the body **and** as `doc_id:`, with ≥ 1 id-query each | [SR-RANKING](0111_ranking.md) d9 · [SR-INGEST](0106_ingest.md) d23d · R3 |
   | **T7** | **Link-bearing documents** — inline links that resolve to another ingested document, plus questions answerable only by following one | [`work/golden/README.md`](../work/golden/README.md) §Feature coverage · A22 · R4 |
   | **T8** | **Superseding pairs, archived documents and recency** — including cases where the **older** document is correct | [`work/golden/README.md`](../work/golden/README.md) §Feature coverage · R5 |
   | **T9** | **Unanswerable near-misses** at ~10 %, permuted so no id band carries a type | A7 · A11 |
   | **T10** | **Heading-matched distractors** — so no question is answerable by heading alone | [`work/golden/README.md`](../work/golden/README.md) §Feature coverage, `heading` row · A10 |
   | **T11** | **A corpus with real git history** | **stated here** — decision 3 · R9 |
   | **T12** | **Additions only** — an existing seed document is never edited; new documents rebuild the ladder | A20 · [`work/golden/README.md`](../work/golden/README.md) phase 4 |
   | **T13** | **Custody and naming** — one designated session per set, `set-<gen>-<claude\|codex>`, and `informed` for every agent-authored set | [L11](0013_LAW-11-sealed-answer-key.md) · [SR-WORK-GOLDEN](0066_WORK-golden.md) d14 · A1–A5 |
   | **T14** | **At most 10 000 documents** on any rung | [SR-WORK-SCALE](0057_WORK-scale.md) |

3. **The three checklist items stated here.**

   - **T4 — anchor-only vocabulary.** At least one document must be findable
     **only** through the words *other* documents use when they link to it: a
     house nickname or acronym the target never uses about itself. Plus **a
     hub** — one document linked from many others in unrelated words. Plus
     **questions phrased in the linker's words**, never the target's.
     *Why:* the 2026-09-22 census found **one** anchor-distinctive term in the
     whole seed, and it was a filename.
   - **T5 — abbreviation and glossary pairs.** `Term (ABBR)` pairs, glossary
     lines of the form `term — definition`, and `aliases:` front matter, with
     questions that use **one** form while the answering document spells out
     the **other**. *Why:* measured `0` / `1` (a false positive) / `3` on one
     document — corpus-mined expansion (step 4) had nothing to mine.
   - **T11 — git history.** A feature that reads commit history is measured on
     a corpus that **has** history — several authors and commits over time —
     never on a synthetic ladder rebuilt at one stamp. **How it is carried
     (Arpit, 2026-09-25: *extend the seed, rebuild the ladder*):** earlier
     revisions of a seed document are rows in `work/golden/seed-history.tsv`,
     their full text in `work/golden/seed-history/`, and the rung builder
     replays them through
     [`tools/golden-history/replay.py`](../tools/golden-history/replay.py),
     which states the format. The document's **last** commit stays on its
     `seed-dates.tsv` date, so `mtime` and the recency prior do not move.

4. 🔴 **A new failure class becomes a new item here, in the same change that
   finds it.** A measurement that comes back empty because the data lacked an
   input adds a `T`-row naming that input, with the measured count that proved
   it missing — and, when a feature is involved, an `R`-row saying how to
   carry it. **That is how T4 and T5 arrived.**

5. 🔴 **Prompts are disposable copies; this record is the source** (Arpit,
   2026-09-27: *"prompts can have copy of those but sr should be the source and
   should be maintained … prompts aren't going to be needed anymore since the
   test data is already created so delete them and when a new test data needs
   to be created create new prompts"*).

   - **No test-data prompt is kept in the repository once its data lands.**
     Every prompt under `work/golden/prompts/` was deleted on 2026-09-27; git
     history holds them.
   - **A new prompt is written when new test data is needed**, from this record:
     it copies the `T`, `A` and `R` rows it needs, **links this record**, names
     the rows it carries and the ones it does **not**, and is **deleted in the
     change that commits its data**.
   - **A prompt never adds a rule.** A rule a prompt needs that is not here is
     added **here first**, then copied.
   - Run-and-score procedure is not test data and is not here: it is
     [`work/golden/README.md`](../work/golden/README.md) phases 5 and 6, under
     [SR-WORK-GOLDEN](0066_WORK-golden.md).

6. **Enforcement:** [`tests/test_test_data_prompts.py`](../tests/test_test_data_prompts.py)
   fails when a prompt file under `work/golden/prompts/` does not link this
   record, and when the `T`, `A` or `R` rows stop being numbered `1…n` without
   a gap — so no row is dropped silently.

7. **The authoring rules.** A prompt copies the ones it needs; a report says
   which it met.

   **Custody — who writes, and what they may read**

   | # | rule |
   |---|---|
   | **A1** | 🔴 **One designated session per set, and it then leaves.** A fresh session — for Claude, a plain claude.ai chat with no repository, tools or project memory, the seed corpus attached as one file marked `===== FILE: <path> =====`. **A session that has read `work/golden/questions/`, run a rung, seen a score, or authored an earlier set never authors one.** From the handoff on, the set is closed to that session like any other ([L11](0013_LAW-11-sealed-answer-key.md) decision 6) |
   | **A2** | 🔴 **An author reads the seed and nothing else** — `work/golden/seed/`, `seed/archive/`, `seed-dates.tsv`, `seed-history.tsv`, plus named `work/golden/README.md` sections when it runs in the repo. **Never `work/golden/questions/`, never `golden-answers/` or its singular spelling, never a recursive search over `work/` without excluding `work/golden/`.** No web search, no recall of an earlier set |
   | **A3** | 🔴 **An author writes no file.** Its whole output is fenced blocks in its final message: new documents · `seed-dates.tsv` rows · history rows and revisions · **released questions** · **the key**. The key block is Arpit's hand only; every other block he commits. An instruction to write the key to disk, or to repeat it in a later turn, is void — the author says so and stops |
   | **A4** | **Naming.** Sets are `set-<gen>-<claude\|codex>` by author; the file is `work/golden/questions/set-<gen>-<author>.jsonl`. **Ids carry a prefix unique to the set and are never reused** — a prediction file names ids and nothing else, so one collision silently scores the wrong set ([SR-WORK-GOLDEN](0066_WORK-golden.md) decision 8). The author states the set name in its first line |
   | **A5** | ⚠ **Every Claude-authored set is `informed`, permanently** — its author and its runner are one model family. The author states it in its report; every number on it carries the label |

   **A question set**

   | # | rule |
   |---|---|
   | **A6** | **Size and mix.** ~80–125 questions. Type shares ±5 points: `lookup` 30 % · `paraphrase` 20 % · `multi-doc` 20 % · `temporal` 15 % · `unanswerable` 10 % · `negation` 5 % |
   | **A7** | **Unanswerable questions sound answerable** from this corpus — a near-miss a real person would ask; an id-shaped token the corpus does not contain counts. Shape: `answerable: false`, `relevant: []`, `primary: null`, `answer: ""` |
   | **A8** | 🔴 **Ask in the asker's words** — a warehouse temp, a new driver, an auditor, a finance analyst. Short, vague and typo-prone is welcome. **Never quote the document**; a `paraphrase` question shares no content word with its evidence |
   | **A9** | 🔴 **Every answer is backed by a verbatim quote** in `evidence`, from a file the author actually read (matched with runs of whitespace collapsed). **No quote, no answer — the question is unanswerable.** `relevant` lists every document that helps; `primary` is the best and sits inside `relevant`. When documents conflict, the question fixes the time frame or is `temporal` |
   | **A10** | 🔴 **No heading-only questions.** At larger rungs the corpus is padded with decoys that reuse seed headings with every number changed; anchor each question on a value, name, rule or relationship only the real document has |
   | **A11** | 🔴 **Permute the rows, then number them**, so no id band carries a type, a feature or the sealed subset |
   | **A12** | **20 % `"sealed": true`**, spread across types and features; `"key_version": 1` |
   | **A13** | 🔴 **Hard by construction, never by guess.** No `difficulty` field — it is computed by `tools/golden-difficulty/`. The author counts `d` per question: +1 each for `multi_doc` (≥ 2 docs; +1 again at ≥ 3) · `no_lexical_overlap` · `retired_competitor` (a superseded or archived doc also matches and is wrong) · `buried_value` · `negation` · `unanswerable`. **Aim for ≥ 60 % at `d ≥ 3`** and report the distribution |
   | **A14** | **Row format** — [`work/golden/README.md`](../work/golden/README.md) §The answer file format, plus `"intent": "current" \| "history" \| "neutral"` and `"exercises"`. Feature-specific fields (`scattered`, `facets`) are in their recipe |
   | **A15** | 🔴 **`exercises` names the feature the question gates** — one recipe's tag, or `other` — never a description of the question. **Only `step9_intent` questions may open with an intent cue** (*how do I, steps to, why did we, what is, define*). Feature words — *superseded, archived, latest* — appear in at most a third of that feature's questions |
   | **A16** | 🔴 **Released block = `{"id", "question"}` and nothing else.** Any other field — `type`, `answerable`, `relevant`, `evidence`, `intent`, `exercises`, `sealed`, `difficulty` — lets a runner score without retrieving |

   **Seed documents**

   | # | rule |
   |---|---|
   | **A17** | **Same world, same voice.** Quillfern Cold Logistics (fictional Indian cold chain: Pune HQ, Nagpur/Guwahati/Coimbatore DCs, pharma/dairy/frozen). **Front matter matches the neighbours** — `title`, `doc_id`, `owner`, `department`, `status`, `effective_date`, plus any field they use |
   | **A18** | **Messy on purpose.** Formats (`.md` `.txt` `.yaml` `.eml` `.html`), sizes, authors and quality vary; spread the hazards — the same fact stated two ways, inconsistent names (`Nagpur DC` / `NGP hub`), mixed date formats, undefined acronyms, a paragraph pasted between two docs, a fact needing two docs together, stale text that contradicts a newer value. The author invents every fact |
   | **A19** | **No new document states a fact about an existing seed entity** — released questions were written without it. New subjects only, unless the point *is* the old entity's history (R9) |
   | **A20** | 🔴 **Additions only.** Never edit, rename, re-date or delete a seed file: every rung manifest is frozen against `seed/`. New files take the next number `NN-<type>-<slug>.<ext>`; archived ones `aNN-` under `seed/archive/`. Each new file gets a `seed/<file>\tYYYY-MM-DD` row in `seed-dates.tsv` — its **final** commit date |
   | **A21** | **Supersession** is a `supersedes:` key in the **newer** Markdown document's front matter, listing rung-root paths (`seed/05-….md`), and only when the newer document **changes a fact** a question asks about. Never prose alone |
   | **A22** | **Links** are inline Markdown links in a **`.md`** body — the link text is the anchor, the target a **bare sibling filename** that resolves to an ingested document; `#fragment` is stripped. Reference-style links, HTML anchors, bare URLs and links in `.txt` / `.html` files are **not** extracted. A link that does not resolve is dropped silently |

   **Rungs and the report**

   | # | rule |
   |---|---|
   | **A23** | **A rung build reads `seed/` only** and says so in its report; it **verifies the eight manifests first** and rebuilds only what a changed seed invalidates. **A rebuilt ladder is a new baseline** — numbers on the old one are not compared with numbers on the new one. Mechanics: [`work/golden/README.md`](../work/golden/README.md) phase 4 |
   | **A24** | **The author's report**, before its blocks: that it read the attachment or `seed/` alone and wrote no file; per recipe, how many documents carry the input and their **file names only**; counts per `exercises`, per `type`, sealed; the `d` distribution; the history census when R9 applies; the `T` rows **not carried**; and the A5 label |

8. **The feature recipes.** What the documents must carry for each ranking
   feature, and the questions that exercise it. The tag is the `exercises`
   value (A15).

   | # | feature · tag | the documents carry | the questions |
   |---|---|---|---|
   | **R1** | anchor text · `step1_anchor` (T4) | ≥ 3 targets that **never** use their house nickname (title, headings, body or front matter); ≥ 3 linking docs per target using the nickname as link text (A22); **one hub** linked from ≥ 5 docs in different words, none its title. A nickname guessable from the target's title is replaced | ≥ 20, phrased in the **linker's** words, answered by the target |
   | **R2** | corpus-mined expansion · `step4_expansion` (T5) | ≥ 8 `Full Term (ABBR)` pairs, each defined once and used **bare** elsewhere; one glossary doc of ≥ 10 `term — definition` lines; ≥ 3 docs with `aliases:`. For every pair, some doc has **only** the abbreviation and some **only** the full term | ≥ 20, using **one** form, answered by a doc with the **other** |
   | **R3** | identifiers · `step2_identifier` (T6) | ≥ 2 families of near-neighbour ids — shared prefix + short number (`CR-201 / CR-202`), **new prefixes only** — each in the body **and** as `doc_id:`; siblings on one template, confusable | ≥ 15 asking by id where a sibling is the wrong answer; spread across shapes (hyphenated, underscored, ids in > 1 doc); ≥ 4 unanswerable plausible ids. **Never invent an id for an answerable question** |
   | **R4** | links / graph (T7) | inline links among `.md` seeds, ≥ 6 distinct sources and ≥ 6 targets; **one cluster of 4+ docs** linking in more than one direction, so *coherent* is distinguishable from *no graph*. Change no fact while adding a link | questions answerable **only** by following a link. The author reports the `ref` edges it expects; the census checks it |
   | **R5** | `superseded_weight` · `archived_weight` · `recency` (T8) | ≥ 4 superseding pairs (A21), ≥ 2 retiring a base seed; ≥ 4 archived docs in `seed/archive/`, ≥ 2 competing with a current seed in topic and vocabulary; dates spread over years, newer after what they retire | ≥ 8 superseded (current-seeking and history-seeking), ≥ 8 archived (half where the archived doc is the tempting wrong answer), ≥ 6 recency with **≥ 2 where the older doc is correct** |
   | **R6** | intent prior · `step9_intent` | ≥ 5 topic **triples** — `-procedure-`, `-decision-`, `-reference-` in the **file name only**, never those words in title, headings or body; each member a plausible wrong answer to the other two intents | ≥ 25, opening with the matching cue (*how do I* → procedure, *why did we* → decision, *what is / define* → reference) |
   | **R7** | term proximity · `step6_proximity` | ≥ 8 docs where one passage holds 3–4 key words **together** and answers, and another passage scatters the same words over something else | ≥ 20 using those words; the row carries `"scattered": {"doc", "section"}` |
   | **R8** | diversity · `step7_diversity` | ≥ 3 facet clusters, each ≥ 3 facets; one facet **crowded** with 3–4 near-duplicate docs (none superseded or archived), the rest one doc each | ≥ 15 about the topic **as a whole**; the row carries `"facets": [[…], […]]`, every relevant doc in exactly one group |
   | **R9** | git authority · `step8_authority` (T11) | ≥ 12 docs with history, ≥ 5 authors on the company domain; ≥ 5 **authority pairs** — a maintained doc (≥ 3 authors, ≥ 4 commits, correct) and a one-person doc (1 author, 1 commit, plausible but wrong), same `status`, neither superseded nor archived, no *draft / unofficial / old* wording; in ≥ half, the one-person doc is **newer**. Revisions are full text, consecutive ones differ, the final is the committed text; `seed-history.tsv` rows `path · date · Name <email> · revision` with exactly one `final` per doc, dated as in `seed-dates.tsv` | ≥ 15 answered by the maintained doc, quoted from its final text |
   | **R10** | section scoring · `step10_section` | ≥ 4 long docs (≥ 3 000 words, ≥ 8 headed sections, most sections off-question); ≥ 2 short (< 400 words) wrong competitors per long doc; the answering section's heading does not repeat the question's words. ⚠ **The competitor must be able to win at document level:** it carries the question's distinctive words in its **title or a heading**, while the long doc carries them in the answering section's **body** and elsewhere only scattered. A long doc that also matches in its title or headings ranks first on its own and the question never enters the pool (set-4-claude: 1 of 15, 2026-09-28) | ≥ 15 answered by one section of a long doc; the row carries `"competitor": "seed/…"`, the short doc built to beat it, never in `relevant` |

### Consequences

- **One list to check against, and it cannot drift from a prompt** — there is no
  standing prompt to drift from. A prompt lives for one run.
- **The cost:** writing a new prompt means copying from here each time. That is
  the point — the copy is made from the current rules, not from an old prompt
  that has fallen behind them.
- **The test binds prompts, not data.** Nothing checks that a document *actually*
  carries T4; the census in each run catches that, after the fact.
- **T3 stays the hardest item to meet and the easiest to fake.** Hard by
  construction is checkable; *the engine fails it* is not allowed as a
  definition, because every claim built on it becomes circular.

### Alternatives considered

- **Keep the prompts as the source, with the SR as an index.** Rejected
  (Arpit, 2026-09-27): thirteen prompts restated the same rules in thirteen
  shapes, and a rule changed in one was stale in the rest.
- **Put the list in `work/golden/README.md`.** Rejected: the README documents
  the benchmark process, and a list there has no owner a change can demand.
- **Restate every other record's rule here in full.** Rejected: second copies
  that can disagree with their home — the thing L0 forbids. Rules owned
  elsewhere stay pointers.

### Reference (required)

- [the step-input run](../work/regression/2026-09-22-w168-step-inputs/report.md)
  and [the anchor census](../work/regression/2026-09-22-anchor-input-census/report.md)
  — the measured counts behind T4, T5 and T11.
- [W-215](../archive/open/W-215-generation-2-corpus.md) — the generation-2
  specification these items were first listed in.
- The deleted prompts — `git log --diff-filter=D -- work/golden/prompts/`.

### Veto condition

**Reopen this decision if:** a measurement comes back empty because its data
lacked an input that is not a `T`-row here, or a prompt had to state a rule
this record does not hold.

**How to check it:** read the *not carried* line in the run's report; every
input it names must appear in decision 2's table.

---

## References

**Records** — [SR-LAW-0](0002_LAW-0-authority.md) · [L11](0013_LAW-11-sealed-answer-key.md) · [SR-WORK-SCALE](0057_WORK-scale.md) · [SR-WORK-GOLDEN](0066_WORK-golden.md) · [SR-INGEST](0106_ingest.md) · [SR-RANKING](0111_ranking.md) · [SR-RS](0133_predictions.md)

**Work** — [`work/golden/README.md`](../work/golden/README.md) · [W-215](../archive/open/W-215-generation-2-corpus.md)

**Code** — [`tests/test_test_data_prompts.py`](../tests/test_test_data_prompts.py) · [`tools/golden-history/replay.py`](../tools/golden-history/replay.py)
