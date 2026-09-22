---
type: Index
description: "Index of the sealed golden benchmark: the three question sets, the seed corpus, the prompts, the difficulty rubric, and the one rule."
---

# `work/golden/` — the sealed golden benchmark

**The test data for `fux-lab` — and only for `fux-lab`, per [SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md): seed documents written by
Codex, THREE question sets over them — one Codex-authored, two Claude-authored —
whose answers no agent ever reads, and a corpus ladder Claude grows from 10 to
10 000 documents without ever seeing a question.**

Ruled by Arpit, 2026-09-11. Tracked as [W-136 → W-204](../regression/2026-09-22-golden-final-score/FINAL-SCORE.md).

---

## 🔴 The one rule

🔴 **It is LAW — [L11](../../records/0012_LAW-11-sealed-answer-key.md)**, stated
once there (Arpit, 2026-09-11; made law 2026-09-15) and carried into `CLAUDE.md`
§Non-negotiable constraints. **Read it before you touch anything in this
directory.** The guards and what Claude MAY read are
[SR-WORK-GOLDEN](../../records/0066_WORK-golden.md) decision 2. This file states
neither, and says only what each guard stops:

| guard | stops |
|---|---|
| `.gitignore` | the key reaching git history or a remote; `rg` and Claude's Grep skipping it by default |
| `!work/golden` in `.fux/sources/dirs` | the key's vocabulary landing in fux's own **committed** index |
| `permissions.deny` in `.claude/settings.json` | Claude Code's Read / Edit / Grep / Glob on the folder |
| `.claude/hooks/guard-golden-answer.sh` | any Claude Code tool call — Bash included — that **targets** the folder by path. ⚠ Its Bash branch misses a bare `golden-answers/…`, and it refuses every edit to itself, which is why there is a sixth guard rather than a one-line fix |
| `.claude/hooks/guard-sealed-key.sh` | the same, with the plural spelling closed on the shell surface too |
| `tests/test_golden_key_guards.py` · `tests/test_golden_key_never_committed.py` | a guard quietly narrowing, and a key — or a fragment of one — reaching a **committed** byte |
| `tests/test_golden_hook_prose.py` | the hooks being narrowed *or* widened on the prose question — see the convention below |
| `CLAUDE.md` §Non-negotiable constraints — L11's generated view | everything above cannot reach: **Cowork**, and a recursive `grep` that never names the folder |

🔴 **A key may be on this machine, and the guards are the defence again.** L11
decision 3 (Arpit, 2026-09-18) permits one — at `golden-answers/`, gitignored,
closed to every agent on both spellings. Between 2026-09-15 and that date this
paragraph said the guards defended an empty room. **They do not.** 🔴 **Three
routes none of them covers**, all three prose in the law: a **paste**, a
**Cowork session's mount** — it reaches the folder with a plain shell call no
deny rule or hook sees — and a recursive `grep` that never names the folder.

⚠ **Writing about this directory has one convention, and it is not stated here:**
[SR-WORK-GOLDEN](../../records/0066_WORK-golden.md) decision 7 (Arpit,
2026-09-21). Read it before writing any document that has to spell a key path —
including this one.

🔴 **LOCKED is a STATE now, and the switch is Arpit's hand.** Since 2026-09-22
the guards above come down by one command and go back by another:

```console
$ just golden-state         # locked | unlocked — safe for anyone, opens nothing
$ just golden-unlock        # ARPIT ONLY: the read guards come down
$ just golden-retire set-1  # questions AND answers -> retired/, open test data
$ just golden-lock          # every guard back, byte-identically
```

**The rule is [L11](../../records/0012_LAW-11-sealed-answer-key.md) decision 14
and this file states none of it**; the mechanics are
[SR-WORK-GOLDEN](../../records/0066_WORK-golden.md) decision 15. What matters
here is the *process* shape: the lift is **per generation of test data**, not
once and for ever — a scored set retires into ordinary reusable data and the
next generation is authored sealed as `set-<gen>-<x|u>`. ⚠ **The paste route is
retired**, and **every golden number is `informed` permanently from the first
unlock.**

### 🔴 The 2026-09-15 reset, and the three sets written after it

**Arpit deleted the provisional Claude-authored key and the 124 released
questions**, together with the singular-spelled key directory L11 decision 5
closes. **The seed corpus and the eight ladder rungs survived** — they are the
golden data set and nothing about them changed.

⚠ **The deletion stands as history; it is not undone by the 2026-09-18
permission.** A key directory is allowed again, at the one address L11 names, and
nothing that was deleted came back.

⚠ **This section said *both question sets are still unwritten* until 2026-09-21,
and it was five days out of date.** Prompts 2 and 3 were run on **2026-09-16**
(`742e1aa9`), and prompt 3 again for set 3 on **2026-09-21**:

| | authored | released file | questions |
|---|---|---|---:|
| set 1 | Codex, 2026-09-16 | `questions/set-1.jsonl` | 125 |
| set 2 | Claude, 2026-09-16 | `questions/set-2.jsonl` | 124 |
| set 3 | Claude, 2026-09-21 | `questions/set-3.jsonl` | 125 |

🔴 **What has NOT come back is a key**, and that is the part of the reset still in
force: every answer half is Arpit's, in the chat, at his choice.

- **Every id from the old set (`g001…`) is orphaned and never reused.** Filed
  predictions and regression rows keyed to them stay as history and **may not be
  compared** with anything scored on set 1, set 2 or set 3.
- **Prompt 1 is not needed** — it rebuilds the corpus from nothing. The live
  entry point is [prompt 4](prompts/4-claude-corpus.md) whenever `seed/` changes,
  and [prompt 5](prompts/5-claude-run.md) to run the sets.


### Custody — Arpit holds both sets; one guarded directory, his alone (2026-09-18)

**Arpit, 2026-09-15:** *"answers, be it generated by Claude, be it generated by
Codex, can never be accessed by any of the agents. I'll go ahead and paste it in
the chat, or I'll have Codex review the answers."* That is
[L11](../../records/0012_LAW-11-sealed-answer-key.md) and this section states
none of it — what follows is only what it means for a run.

**Amended by Arpit, 2026-09-18**, on [W-197](../../archive/open/W-197-stray-key-directory.md):
*"Yes — keep them; amend L11 to allow a local guarded key dir"*, and *"wherever
we have golden-answer or golden-answers change it to golden-answers but add
similar restriction to both."*

- **No agent writes a key file, and no agent reads one.** The old per-run
  question — *"(1) the file, or (2) the chat?"* — is **deleted from prompts 1, 3
  and 5** and stays deleted. The route to a scoring turn is the chat, always.
- **`work/golden/golden-answers/` is the one address a key may live at**, on
  Arpit's machine, gitignored, never committed. **Permission for it to exist is
  not permission to reach it**: it is closed to every agent under L11 decision 5,
  on both spellings, for listing and hashing as much as for reading.
- ⚠ **No Claude session creates, empties or removes either directory** —
  deleting a thing is a tool call that reaches into it. **Arpit does it
  himself**, and a directory's existence authorizes nothing about opening it.
- ⚠ **RETIRED 2026-09-21: *"scoring is a chat Arpit is present for"*.** That
  bullet described the paste route — he pasted a run's rows into a Codex chat and
  Codex returned per-query results. **It is gone.** Scoring now happens inside the
  repository while the tree is unlocked (L11 decision 14), which is what removed
  *waiting on his availability* from every item that needed a score. The one thing
  that still needs his hand is the **switch**, and that is one command rather than
  a session he has to sit through.

### 🔴 All three sets RETIRED on 2026-09-22 — this section is history

**Generation 1 is scored, retired and re-sealed.** Arpit ran the full cycle in
one sitting: `just golden-unlock` → phase D scored **11 716 rows** → `just
golden-retire` on all three → `just golden-lock`.

**Their questions and expected values now live at
[`retired/`](retired/)** — `set-1`, `set-2`, `set-3`, each with
`questions.jsonl`, `expected.jsonl` and a README. 🔴 **They are open data any
session may read in any state, and they carry no golden claim**: the model family
that reads them also tunes against them, so a number measured on them says a
behaviour has not regressed and nothing about the engine's quality. The score
itself is [`FINAL-SCORE.md`](../regression/2026-09-22-golden-final-score/FINAL-SCORE.md).

⚠ **`work/golden/questions/` is empty of sets now**, and the key directory is
closed again. **The next generation is authored SEALED** and named
`set-<gen>-<x|u>` (`x` Codex, `u` Claude) — L11 decision 14. ⚠ **These three kept
their original names**, because they retired before any rename, so the
convention begins with generation 2.

**What follows is the generation-1 description, kept as history.**

**Same seed corpus, same ladder, two authors, reported apart — never pooled.**

| | **set 1** | **set 2** | **set 3** |
|---|---|---|---|
| questions **and** answers written by | **Codex** — [prompt 2](prompts/2-codex-questions.md) | **Claude**, from `seed/` only — [prompt 3](prompts/3-claude-questions.md) | **Claude**, from `seed/` only — [prompt 3](prompts/3-claude-questions.md) |
| ids | `s1-001…` | `s2-001…` | `s3-001…` |
| released file | `questions/set-1.jsonl` | `questions/set-2.jsonl` | `questions/set-3.jsonl` |
| predictions / hand-off | `predictions-set-1.jsonl` · `handoff-set-1.jsonl` | `predictions-set-2.jsonl` · `handoff-set-2.jsonl` | `predictions-set-3.jsonl` · `handoff-set-3.jsonl` |
| what a number may claim | `blind` on the first scored run, per [SR-RS](../../records/0133_predictions.md) | 🔴 **`informed`, permanently** | 🔴 **`informed`, permanently** |
| why it exists | the externally-authored arm | authorship-bias comparison against set 1 | **the inputs the seed does not carry** — `RF-118`-shaped identifiers and link-bearing documents |

⚠ **They are numbered, not named after their author** (Arpit, 2026-09-15). The
author is a fact about a set, not its identity — and a number survives a change
of author, where *"the Claude set"* would quietly become a lie.

- **Why more than one.** A benchmark whose questions come from one author
  measures that author's idea of a question as much as it measures the engine.
  **Two authors make that bias visible instead of invisible** — the same engine,
  the same corpus, and the gap between the sets is the measurement.
- 🔴 **Why set 3 (Arpit, 2026-09-20): *"no feature waits on Codex."*** Three
  measurements were stuck not on a design question but on a **corpus** — the seed
  carries no `PROJ-123`-shaped identifier and **0 `ref` edges on all eight
  rungs** — and under [SR-RS](../../records/0133_predictions.md) decision 23 a
  missing input is a **data defect, not a null**, so they were `unmeasurable` and
  filed as such. Set 3 carries those inputs. **The standing rule is
  [SR-WORK-GOLDEN](../../records/0066_WORK-golden.md) decision 14**: an
  agent-authored set is created whenever a measurement would otherwise wait on
  Codex. ⚠ **It is not a way to rescue a disappointing number** — the trigger is
  a missing input, checkable *before* any arm runs.
- 🔴 **Each agent-authored set is authored in ONE session that then leaves, and
  the carve-out is PER SET.** That session reads `seed/` and nothing else, hands
  the questions *and* answers to Arpit **in the chat**, writes no file, and
  **never runs a rung, scores anything, or returns**. From that handoff on the
  set's answers are as closed to Claude as set 1's — authorship buys no access,
  and authoring set 3 gives nobody reach into set 1 or set 2
  ([L11](../../records/0012_LAW-11-sealed-answer-key.md) decision 6).
- 🔴 **Set 2 and set 3 can never be `blind`**, because author and runner are the
  same model family. They are bought for comparison, **not for a clean delta**,
  and every document stating one of their numbers states that label beside it.
- **Each author hands over TWO blocks.** Block 1 is `{"id","question"}` only —
  Arpit commits it as `questions/set-N.jsonl`. Block 2 is the full key — **he
  keeps it, and it never touches disk.** That is what replaced the old
  freeze-and-release step.
- ⚠ **The id namespaces must not collide.** A prediction file names ids and
  nothing else; one ambiguous id silently scores the wrong set.
- ⚠ **Never pool the sets into one figure.** The comparison *between* them is
  the point; a mean across them erases it and means nothing on its own.

## Layout

```
work/golden/
  README.md                 this file — the process
  seed/                     the seed documents (Codex writes; Claude may read)
  seed/archive/             seed documents that are history — each rung declares it archived=true
  seed-dates.tsv            one date per seed document; each rung commits the file at that date
  golden-answers/               🚫 Arpit's. Gitignored, never committed, CLOSED to every agent (L11 d3+d5)
  golden-answer/                🚫 the older singular spelling — deleted 2026-09-15, still guarded
  questions/set-1.jsonl         set 1: ids + text only — Codex-authored questions
  questions/set-2.jsonl         set 2: ids + text only — Claude-authored questions
  questions/set-3.jsonl         set 3: ids + text only — Claude-authored, the failing shapes + links
  questions/README.md           what they omit, and the cost of them existing before the corpus
  ladder/rung-NNNNN.sha256      frozen manifests: which files make each rung, by hash
  ladder/rung-NNNNN.index       the engine version AND COMMIT, and the index root hash, each rung was built with
  prompts/                  the SIX paste-ready prompts, in the order Arpit runs them
```

**The ladder corpus itself lives in `~/my_programs/fux-lab/corpora/golden/`**,
not in this repo — 10 000 documents would bloat fux's git history. Only the
manifests are committed here, so every rung is verifiable byte for byte.

### One directory and one index per rung (Arpit, 2026-09-11)

**Every rung is its own self-contained directory with its own fux index**, so a
rung is tested by asking, never by re-ingesting — and a 100-document run never
waits on 10 000.

```
~/my_programs/fux-lab/corpora/golden/
  rung-seed/    seed/ (every seed document)         .fux/  ← its own index
  rung-00100/   seed/ + ext/ (100)                  .fux/
  rung-00200/   seed/ + ext/ (200)                  .fux/
  rung-00500/   …                                   .fux/
  rung-01000/                                       .fux/
  rung-02000/                                       .fux/
  rung-05000/                                       .fux/
  rung-10000/   seed/ + ext/ (10 000)               .fux/
```

- **Copies, not links.** Each rung directory holds real files, so any one can be
  moved, zipped or handed to a lab environment on its own.
- **Content is still nested.** Rung 200 holds rung 100's files plus 100 more —
  byte-identical, checked by the manifests. That is what makes rungs comparable.
- **Paths match the key.** Seed files sit at `seed/NN-….md` in every rung, exactly
  as the key names them; new files go under `ext/<category>/`. A prediction needs
  no translation.
- **Each rung is a git repo with a committed `.fux/`** (sources list = `seed` and
  `ext`, plus `pii.toml`). Its index is built **once per engine version** and
  recorded in `ladder/rung-NNNNN.index`; a new engine version means a re-ingest of
  that rung, nothing else.
- 🔴 **`engine_commit:` is in the stamp too, since 2026-09-15 (W-186), and the
  version alone was not enough.** `fux.index.v3` was written by a tree whose
  `__version__` still read **2.0.1** — the version published on PyPI, which
  writes **v2**. So *"check the engine version matches"* compared two engines
  that cannot read each other's index and saw a match. Between releases the
  version string is the LAST release's; the commit is what identifies the engine
  that actually built the rung.

---

## The prompts, in the order Arpit runs them

**One prompt per step, and he runs them himself** — the pipeline is deliberately
not a pipeline an agent can drive end to end, because the two places answers exist
are both in his hands.

| # | who | reads | writes | prompt |
|---|---|---|---|---|
| **1** | Codex | nothing from fux | `seed/`, `seed/archive/`, `seed-dates.tsv` — **documents only** | [`1-codex-seed.md`](prompts/1-codex-seed.md) |
| **2** | Codex | `seed/` | **set 1** questions + answers → **two blocks in the chat** | [`2-codex-questions.md`](prompts/2-codex-questions.md) |
| **3** | Claude, **one session per set, that then leaves** | `seed/` **only** | **set N** questions + answers → **two blocks in the chat**, no file; a third block of **seed additions** when that set carries a missing input (set 3 does) | [`3-claude-questions.md`](prompts/3-claude-questions.md) |
| **4** | Claude Code | `seed/` **only** | verifies the eight rungs; builds or repairs the corpus in fux-lab + `ladder/*.sha256` | [`4-claude-corpus.md`](prompts/4-claude-corpus.md) |
| **5** | Claude Code | the ladder + every released `questions/set-N.jsonl` | `predictions-set-N.jsonl`, **`handoff-set-N.jsonl`** and `report.md`, **one pair per set** | [`5-claude-run.md`](prompts/5-claude-run.md) |
| **6** | Codex | the hand-off files + **the keys, pasted by Arpit** | per-query results **without answers**, per set | [`6-codex-score.md`](prompts/6-codex-score.md) |
| **10** | Claude, **an isolated claude.ai chat, one per set** | the seed corpus, **attached — nothing else** | **seed additions** that carry the inputs four ranking features act on (T4, T5, T6) + `set-3-u` → **four blocks in the chat**, no file | [`10-claude-feature-input-seed.md`](prompts/10-claude-feature-input-seed.md) |

🔴 **Every prompt that creates test data is authored against [SR-WORK-TESTDATA](../../records/0068_WORK-test-data.md)** — the fourteen-item checklist — and names the items it carries in its first lines. `tests/test_test_data_prompts.py` fails when one does not, and when a new prompt file is not classified.

**Between 2/3 and 4, Arpit commits block 1 of each handoff** as
`questions/set-N.jsonl`, and keeps block 2 — the key — himself. **Prompt 3 is run
once per agent-authored set**, in its own session; when that set carries seed
additions (block 3) he commits them into `seed/` and **prompt 4 rebuilds the
ladder** before anything is run.

⚠ **[`prompts/7-codex-link-bearing-seed.md`](prompts/7-codex-link-bearing-seed.md)
and [`prompts/8-codex-identifier-questions.md`](prompts/8-codex-identifier-questions.md)
are OPTIONAL and on no critical path** (Arpit, 2026-09-20: *"no feature waits on
Codex"*). What they were blocking is carried by set 3. **Prompt 7 is still worth
running whenever Codex is free** — its links would be `blind` where set 3's are
`informed` permanently — and prompt 8 was **withdrawn** as an unblock by the
2026-09-18 headroom run, which measured the headroom below the floor whatever
questions are written.

**Between 5 and 6, he carries the two `handoff-set-N.jsonl` files to Codex** and
pastes the keys there. 🔴 **That hop is the whole design**: it is the only point
where a question's answer and fux's answer are ever in the same place, and the
party holding both is a person, not an agent.

⚠ **[`prompts/RETIRED-codex-release.md`](prompts/RETIRED-codex-release.md) is kept
and must not be run.** Its three jobs moved on 2026-09-15 — the file says where.

⚠ **[`prompts/6E-codex-score-ephemeral.md`](prompts/6E-codex-score-ephemeral.md)
is prompt 6 by subtraction** (Arpit, 2026-09-17): it writes no file, stores no
key, and does not pool — so **its numbers are lower bounds and are NOT a filed
run** under [SR-RS](../../records/0133_predictions.md) decision 10a, and may be
cited nowhere. It answers *"where does the engine stand"* in a chat that is then
closed. **Prompt 6 is still the one that produces evidence.**

### Order is load-bearing, and one part of it is only honour

**Prompt 4 should run before 2 and 3.** A rung built by a session that could have
read a question is `informed` for good, and `questions/` is on disk from the
moment Arpit commits block 1.

⚠ **Where the order cannot be kept, prompt 4 is on its honour** — the session
building the corpus reads `seed/` and nothing else and says so in its report.
**Nothing mechanical enforces this**, which is why it is written here in full
rather than assumed.

---

## Phase 1 — the seed corpus (Codex)

- **The company and the ten documents are specified in
  [`prompts/1-codex-seed.md`](prompts/1-codex-seed.md)** — *Quillfern Cold
  Logistics*, a fictional Indian cold-chain company, and a roster of ten documents
  that deliberately disagree in format, size, quality and authorship.
- **Why messy on purpose (Arpit, 2026-09-11):** real organisational knowledge is
  legacy YAML, emails, wiki exports, shift logs and half-updated policies written
  by professionals and amateurs and edited by several people. A benchmark of tidy
  Markdown measures a corpus nobody has.
- ⚠ **Claude wrote the brief — the company, the cast and the document roster —
  but no facts.** Every number, date, threshold, incident and decision is Codex's
  invention, so the answer-bearing details were never authored by Claude.
- **Feature coverage is part of prompt 1:** superseding pairs with `supersedes:`
  in frontmatter, archived documents under `seed/archive/`, and a date per seed in
  `seed-dates.tsv` — see *Feature coverage* below.
- ⚠ **Prompt 1 writes documents only since 2026-09-15.** The questions that used
  to be its part B are now prompts 2 and 3, one per set.

---

## Phases 2 and 3 — the two question sets

**Both prompts obey the same contract**; only the author and the id prefix differ.
Each produces **~120–125 questions**, roughly:

| type | share | tests |
|---|---:|---|
| `lookup` — one fact, one document | 30 % | the basics |
| `paraphrase` — no shared keywords with the answer | 20 % | vocabulary gap |
| `multi-doc` — needs two or more documents | 20 % | recall, not just hit |
| `temporal` — current vs superseded / old vs new value | 15 % | archived and superseded ranking |
| `unanswerable` — close to the corpus, answer absent | 10 % | abstention |
| `negation` / exception — "when does X NOT apply" | 5 % | precision |

### The answer file format — one JSON object per line

```json
{"id": "g001", "question": "…", "answer": "…", "answerable": true,
 "relevant": ["seed/03-runbook-….md", "seed/07-adr-….md"], "primary": "seed/03-runbook-….md",
 "evidence": [{"doc": "seed/03-runbook-….md", "section": "## Rollback", "quote": "…"}],
 "type": "multi-doc", "difficulty": "medium", "sealed": false, "key_version": 1}
```

- `relevant` = **every** document that helps answer it; `primary` = the best one.
- `unanswerable` → `answerable: false`, `relevant: []`, `answer: ""`.
- `sealed` is marked by the author, in its own key block — prompts 2 and 3.
- 🔴 **`difficulty` is not hand-written.** It is the object
  [`tools/golden-difficulty/`](../../tools/golden-difficulty/) computes — see
  *Difficulty* below — and an author who types `"difficulty": "medium"` has
  written an unfalsifiable label, not a field.

---

## Difficulty — a count, never a judgement (Arpit, 2026-09-15)

**`difficulty` is the number of independent discriminations a question forces**,
computed from the key and the corpus by
[`tools/golden-difficulty/`](../../tools/golden-difficulty/) and re-derivable by
anyone. It is deliberately **not** a label an author picks.

🔴 **Three things it is never derived from**, each of which would quietly destroy
every stratified claim built on it:

1. **fux's own results.** *Hard = fux got it wrong* makes *"fux is weaker on hard
   questions"* true by construction.
2. **The `type` field.** Difficulty that merely re-encodes `lookup` /
   `multi-doc` / `unanswerable` earns nothing. It is worth having only because it
   varies **within** a type — an easy multi-doc and a brutal multi-doc both exist.
3. **How the question felt to write.** That is the thing being replaced.

### The count

Each condition below adds 1, and every one is computed from bytes already in the
key or already in the rung:

| +1 when | the discrimination it forces |
|---|---|
| `len(relevant) >= 2` — and +1 again at `>= 3` | recall, not a single hit |
| no high-IDF question term appears in the evidence quote | a vocabulary gap |
| an archived or superseded document matches and is **not** in `relevant` | telling current from retired, not just finding |
| the primary document is large, or a low-structure format (`.eml`, `.txt`, `.html`, `.yaml`) | locating a value inside it |
| the question turns on a negation or an exception | precision |
| `answerable: false` | abstention |

**Bands: `d <= 1` easy · `d == 2` medium · `d >= 3` hard**, and an
**unanswerable question is floored at `hard`** whatever its count — abstention is
the discrimination the engine is worst at, and a band that hides one is worse
than no band.

### Two numbers, because difficulty moves with the corpus

- **`difficulty_static`** — the flags and the count, frozen when the key is
  written. Comparable across every rung.
- **`distractors_at_rung`** — documents outside `relevant` that carry the
  question's top-IDF terms, recomputed per rung. **This is the honest one:** a
  lookup that is trivial against 20 documents is genuinely hard against 10 000,
  and showing that curve is what the ladder is for.

```json
"difficulty": {"band": "hard", "d": 4,
  "flags": ["multi_doc", "no_lexical_overlap", "retired_competitor", "negation"],
  "distractors_at_rung": {"rung-00100": 3, "rung-10000": 412}}
```

**Store the components, not just the band.** An unexplained `"medium"` cannot be
checked by anyone; the flag list can, and it lets phase 6 report **which
discrimination failed** rather than only which bucket did.

🔴 **`difficulty` never ships in a released `questions/*.jsonl`** — same reason
as `type` and `answerable`: a runner that can see a question is unanswerable
abstains by arithmetic, and the abstention slice then measures nothing.

⚠ **Neither key exists yet**, so nothing carries a difficulty label today. The
scorer runs for the first time once set 1 and set 2 are written —
[W-190 → W-204](../regression/2026-09-22-golden-final-score/FINAL-SCORE.md).

---

## Feature coverage — what this data can test

**[SR-RS](../../records/0133_predictions.md) decision 23: a feature is measured only
on data that contains the input it acts on.** This table is that declaration.
**File names and counts only — never question text, ids or answers.**

| feature | input fux reads | set up by | documents that exercise it | questions |
|---|---|---|---|---:|
| `superseded_weight` | `supersedes:` in the newer doc's frontmatter | Codex, [prompt 1](prompts/1-codex-seed.md) part A §3 | 4 pairs: `11-decision-telematics-vendor-2026.md` → `05-…-2023.md` · `12-rate-card-2026-h2.md` → `07-rate-card-and-surcharges.md` · `13-dock-scheduling-rules-2026.md` → `09-dock-scheduling-wiki-export.html` · `15-customer-notification-matrix-2026.md` → `14-…-2025.md` | 12 |
| `archived_weight` | a directory declared `archived=true` | Codex places files in `seed/archive/`; each rung declares it (phase 4) | 5 docs in `seed/archive/`: `a01-sop-temperature-excursion-rev2.md` · `a02-kalpa-alert-routing-guide-2021.md` · `a03-dock-scheduling-wiki-2021.html` · `a04-driver-hours-policy-2019.md` · `a05-induction-checklist-2020.txt` | 9 |
| `recency` | commit time per file | Codex writes `seed-dates.tsv`; each rung commits at those dates (phase 4) | all 20 seed documents, dated 2019-08-12 → 2026-07-01 | 7 |
| abstention | unanswerable questions | Codex, prompt 2 | — | 12 |
| `heading` negative control | heading-matched distractors | Claude, phase 4 `sibling` documents | 32 at rung 100, rising to 392 at rung 1 000 — `ext/sibling/` documents reusing the seed documents' **headings and document types** (Temperature Excursion Response SOP, Rate card and surcharges, Customer notification matrix, Dock scheduling rules, …) with a different company, people, facilities and every number changed | — |
| **anchor text · graph walk · graph coherence** | a `ref` edge — an inline markdown link in a body whose target resolves to another ingested document | 🔴 **NOBODY. `ref` edges: 0 on every rung** — requested as [prompt 7](prompts/7-codex-link-bearing-seed.md), not yet written | **0 measurable** |

A feature with no row, or a row still showing *(filled by …)*, **is not measurable
yet** — say so in the pre-registration instead of running.

### 🔴 The `ref`-edge census, per rung — measured 2026-09-16

**Every edge in this corpus is a `supersedes` edge.** There is no link syntax
anywhere in `seed/`, so three features measure nothing
([W-191 → W-204](../regression/2026-09-22-golden-final-score/FINAL-SCORE.md)):

| rung | docs | edges | **`ref`** | `supersedes` |
|---|---:|---:|---:|---:|
| `rung-seed` | 20 | 4 | **0** | 4 |
| `rung-00100` | 100 | 12 | **0** | 12 |
| `rung-00200` | 200 | 22 | **0** | 22 |
| `rung-00500` | 500 | 52 | **0** | 52 |
| `rung-01000` | 1 000 | 102 | **0** | 102 |
| `rung-02000` | 2 000 | 202 | **0** | 202 |
| `rung-05000` | 5 000 | 502 | **0** | 502 |
| `rung-10000` | 10 000 | 1 002 | **0** | 1 002 |

⚠ **This table is regenerated, never hand-maintained** —
[`tools/quality-controls/ref_edge_census.py`](../../tools/quality-controls/ref_edge_census.py),
which **exits 2 when a corpus has no `ref` edges** so a link-dependent run can
gate on it rather than rediscover this. It counts what the **engine wrote**, not
what a document looks like: an inline link whose target does not resolve is
dropped silently, so a corpus can be full of markdown links and carry no edges —
which a hand-count cannot see.

🔴 **Nothing detected this for weeks.** The rungs were frozen, verified, nested
and re-verified while a link-ranking feature was measured against them and filed
**0 of 124 flips at every weight**. [SR-RS](../../records/0133_predictions.md)
decision 23: **missing input is a data defect, not a null.**

---

## Phase 4 — the corpus (Claude Code, blind)

**Rungs: seed → 100 → 200 → 500 → 1 000 → 2 000 → 5 000 → 10 000.** Nested: each
rung is the previous one plus new files, so the seed documents are in every rung.

⚠ **10 000 is the ceiling.** Arpit's 2026-08-22 ruling forbids measuring above it
until he reopens it; *"and so on"* past 10 000 is a separate, later decision.

- 🔴 **Claude reads `seed/` and nothing else** from this directory — **not**
  `questions/`, which now exists before the ladder does and would make the rung
  `informed` permanently.
- **Mix per rung, recorded per file in the manifest (`category`):**

| category | share | what it is |
|---|---:|---|
| `sibling` | ~40 % | same doc types and vocabulary, **different entities and facts** — hard negatives |
| `variant` | ~10 % | older / draft / superseded-style versions of the seed **document types** |
| `adjacent` | ~30 % | same organisation, other teams and topics |
| `filler` | ~20 % | unrelated domains |

- 🔴 **No new document may state a fact about a seed entity** (a named service,
  person, incident, number or decision in `seed/`). That keeps the answers inside
  the key. Vocabulary may overlap; facts may not.
- **Up to rung 500, documents may be authored by the model; beyond that, by a
  deterministic generator** (fixed seed, stable order) — extend
  `fux-lab/shared/generate/` if it fits, since the lab is canonical.
  Each manifest line records `origin: authored | generated`.
- **One directory per rung** (see *One directory and one index per rung*):
  build rung 100 by copying rung 10 and adding files, rung 200 by copying rung 100,
  and so on.
- **Index each rung** once it is complete: `fux setup` (sources `seed` + `ext`),
  `fux ingest --full`, commit inside the rung. Indexing needs no questions, so it
  happens here, blind. Write `ladder/rung-NNNNN.index`: engine version, index root hash.
- 🔴 **Declare and date, so the priors can move** (decision 23d — answer-free mechanics):
  - each rung's `.fux/sources/dirs`: `seed`, `seed/archive archived=true`, `ext`,
    `ext/archive archived=true`;
  - commit every seed file with `GIT_AUTHOR_DATE` / `GIT_COMMITTER_DATE` from
    `seed-dates.tsv`; `ext/` files get deterministic dates spread over the same years;
  - `ext/` may hold superseding pairs and archived documents **among `ext/` files
    only** — **never `supersedes:` a seed**, which would change the key's truth;
  - after ingest, write `ladder/rung-NNNNN.coverage`: counts of records flagged
    `superseded`, `archived`, and carrying `mtime` — **they must match the
    declarations**, or the rung is not frozen.
- 🔴 **Every seed file must be indexed.** The seeds are `.md`, `.txt`, `.yaml`,
  `.eml` and `.html` on purpose; the rung's `.fux/formats.toml` must include every
  extension present, and the ingest skip list must name **no** `seed/` file. A seed
  silently skipped makes a question fail for a reason that has nothing to do with ranking.
- **Freeze:** `ladder/rung-NNNNN.sha256` lists `sha256  path  category  origin` for
  every document in the rung (not the index). A rung is frozen when its manifest
  and index record are committed.

---

### 🔴 Re-frozen on 2026-09-15 — the ladder had drifted off the seed

**Prompt 4 ran as the check it says it is, and the check failed.** All eight
rungs were frozen on 2026-09-12; on 2026-09-15 commit `0aa4bbcf` extended
**7 of the 20 documents in `seed/` by 131 lines**, and **both question sets were
authored afterwards, from the new text**. Every rung still held the old bytes,
and every mechanism in the repo passed: `verify()` compares a rung to its own
manifest, `ladder_check` compares the manifests to each other, and neither ever
asked whether the `seed/` half was the seed this repository has.

🔴 **That rung does not fail. It answers** — with a number shaped exactly like a
good one, against a paragraph it does not contain.

All eight were rebuilt from the current seed with the **unmodified** 2026-09-12
builder and generator and re-frozen. **`ext/` came back byte-identical on all
eight — 18 800 generated documents, zero drift** — so the determinism claim
below is measured now, not asserted. Every coverage count is unchanged; exactly
fourteen manifest lines moved per rung. **Every `index_root_sha256` and
`rung_head_commit` is new**, and every number filed against the old rungs names
a corpus that no longer exists.

**The gate that will catch the next one** — `rungs.seed_drift()`,
`ladder_check.py` check 4, and
[`tests/test_golden_ladder_seed.py`](../../tests/test_golden_ladder_seed.py) in
the fast suite. Two strikes, so a check
([SR-WORK-SESSION](../../records/0060_WORK-session.md) decision 13); W-186 was
the first. Filed:
[`2026-09-15-ladder-seed-refresh`](../regression/2026-09-15-ladder-seed-refresh/report.md).

⚠ **A rung is a COPY of `seed/`, not a view of it.** Changing a seed document in
this repo silently invalidates all eight until they are rebuilt — that is the
shape of the thing, and the gate is what makes it loud.

### Built on 2026-09-12, rebuilt 2026-09-15 — **the ladder is COMPLETE, all eight rungs to 10 000**

The first five landed earlier the same day, under Arpit's cap at rung 1 000; the
cap was lifted and `rung-02000`, `rung-05000` and `rung-10000` were built from
the **same committed generator and the same seed**, so the whole ladder is one
stream.

**10 000 is the ceiling and the ladder stops there** — `CLAUDE.md` §Litmus, and
[SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md) caps the lab at 10 000 documents.
There is no rung above this one and none may be built.

⚠ **Rebuilt 2026-09-21 on set 3's seed** — [the run](../regression/2026-09-21-ladder-set-3-rebuild/report.md).
`seed/` grew from 20 documents to 28, so every rung **keeps its headline size**
and carries eight fewer generated documents; `rung-seed` is the seed corpus and
is therefore 28. `superseded` is one lower above the seed because one
supersession pair fell past the rung boundary.

| rung | documents | of which seed | archived | superseded | carrying `mtime` |
|---|---:|---:|---:|---:|---:|
| `rung-seed` | 28 | 28 | 6 | 4 | 28 / 28 |
| `rung-00100` | 100 | 28 | 13 | 11 | 100 / 100 |
| `rung-00200` | 200 | 28 | 23 | 21 | 200 / 200 |
| `rung-00500` | 500 | 28 | 53 | 51 | 500 / 500 |
| `rung-01000` | 1 000 | 28 | 103 | 101 | 1 000 / 1 000 |
| `rung-02000` | 2 000 | 28 | 203 | 201 | 2 000 / 2 000 |
| `rung-05000` | 5 000 | 28 | 503 | 501 | 5 000 / 5 000 |
| `rung-10000` | 10 000 | 28 | 1 003 | 1 001 | 10 000 / 10 000 |

🔴 **The ladder carries 61 `ref` edges on every rung, and carried 0 until
2026-09-21.** Set 3's documents link to each other and to the older seed —
`ref_edge_census.py` exits 0 for the first time. **That is an input arriving,
never a result**: `[bm25f] anchor` is `0.0` on every rung and moves only on its
own passing pre-registered run.

⚠ **The three new rungs were built AFTER `questions/` was opened**, which the
first five were not. **That does not make them informed** — the generator, its
seed and its blacklist are all committed and unchanged, and no question was read
by anything that produced a document. But the *ordering* argument that covers
rungs seed–1 000 (`92f5bff`, checkable in `git log`) does not extend to them, so
**what protects these three is the generator's determinism, not the clock.**
Anyone re-deriving them gets the same bytes; that is the claim, and it is
checkable. 🔴 **It was checked on 2026-09-15** — re-derived by a
different session at a different engine commit, all eight rungs, **0 of 18 800
generated documents drifted.**

**Nesting is verified across all eight, not asserted**: every rung's manifest
contains the previous rung's documents with **identical hashes**, and all twenty
seed documents are in `rung-10000`. Re-verified after the 2026-09-15 rebuild.

- **Every rung nests**: rung N's manifest contains rung N-1's documents with
  identical hashes, and all twenty seed documents are in every rung. Checked
  against the manifests, not asserted.
- **The `ext/` corpus is reproducible from committed bytes.** The generator and
  the twenty hand-authored hard negatives are filed under
  [`work/regression/2026-09-12-golden-ladder/evidence/generator/`](../regression/2026-09-12-golden-ladder/evidence/generator/);
  the lab itself commits nothing.
- **No `ext/` document names a seed entity.** The generator carries the
  blacklist and refuses to write rather than emit one; the twenty authored
  documents pass the same check.
- **No `ext/` document declares `supersedes:` on a seed.** Every ext
  supersession pair is `ext/archive/…` retired ← `ext/sibling/…` current, and
  both halves enter the ladder at the same rung.

---

## Between the prompts — what Arpit commits, and what he keeps

**This replaced the freeze-and-release step on 2026-09-15.** Each authoring
prompt ends with two fenced blocks and he splits them:

1. **Block 1 → the repository.** `{"id", "question"}` only, committed as
   `questions/set-1.jsonl` / `set-2.jsonl`. No `type`, no `answerable`, no
   `difficulty`, no `sealed`. 🔴 **Ids carry no type signal** — each author
   permutes its rows before numbering, or the `unanswerable` slice can be
   abstained on by arithmetic.
2. **Block 2 → Arpit.** The full key, all fields, **including the 20 % sealed
   holdout the author marked**. It never touches disk; he pastes it into prompt 6
   when a run needs scoring.

⚠ **`ladder/KEY.sha256` is not written any more.** It pinned a key file, and
there is no key file — the pin now lives with whoever holds the key, which is the
point of custody. A changed key is still a new `key_version`, never an edit.

---

## Phase 5 — Run and hand off (Claude Code)

- **Pre-register first**, per run: `work/regression/<date>-golden-rung-NNNNN/PRE-REGISTRATION.md`
  — engine sha, rung, metrics with `k` named, and the headroom disclosure SR-RS
  requires ([SR-RS](../../records/0133_predictions.md) decision 22, which is where
  W-135 landed on 2026-09-11). Commit it before any number.
- **Use the rung's own index — do not re-ingest.** Check the engine version
  matches `ladder/rung-NNNNN.index`; if it does not, re-ingest that rung once, update
  the record, and say so in the report.
- **Rungs are independent**, so they can run in parallel. A lab environment points
  at the rung directory with one pinned engine version.
- For every question, from inside the rung directory, **two calls**:
  `fux ask "<question>" --json --band --why --top 10` and
  `fux answer "<question>" --json`.
- 🔴 **`--why` is not optional and it is not for debugging** —
  [SR-WORK-QUALITY](../../records/0056_WORK-quality.md) decision 13. Its
  `derivation.gates` are the only place `reachable` and `in window` exist, they
  are discarded the moment the query returns, and **a filed run cannot get them
  back**. W-204 phase D scored 11 716 rows and could not compute the funnel at
  all. The hand-off records those five integers and **nothing else from the
  derivation** — the per-term rows are large and the metric reads five numbers.
  ⚠ **An old arm may not have the flag** (`fux-engine 1.0.0` has neither `--band`
  nor `--why`, and argparse exits `2` on an unknown one): pass `--no-why` for
  that arm, and its `gates` are **null**, never zeros.
- **`predictions-set-1.jsonl` and `predictions-set-2.jsonl`**, one line per
  question: `{"id", "ranked": [paths…], "answerable": bool, "band": "…"}`. **One
  file per set**, never one for both — the ids are what phase 6 joins on, and a
  merged file makes a mis-join silent.
- 🔴 **`handoff-set-N.jsonl` is the artifact Arpit carries to Codex** — per
  question: the question, **what fux answered and cited**, the ranked paths, the
  band, **the funnel gates**, the rung and the engine commit. **It contains no
  golden answer**, because no Claude session has one.
- **`report.md`** says what happened: counts, band distribution, how many
  questions fux declined, **how many rows carry funnel gates**, what looked
  wrong. 🔴 **A run whose gates are missing says so in the report**, because the
  alternative is a scoring pass discovering it days later with the rows already
  frozen. 🔴 **It never says whether an answer
  is right** — that word first appears in phase 6, from Codex.

---

## Phase 6 — Score (Codex)

> **Since 2026-09-21 the scorer is `just golden-score <run>`, in Arpit's shell**
> ([L11](../../records/0012_LAW-11-sealed-answer-key.md) decision 13). It finds
> hand-offs in **three layouts** — `evidence/<arm>/rung-*/`, `evidence/rung-*/`
> and **flat**, `evidence/handoff-set-*.jsonl` — and takes a flat hand-off's rung
> from the run's `PRE-REGISTRATION.md` (a `rung:` frontmatter line, or the one
> rung it names), or from a third argument. A set is named as filed: `1` for
> generation 1, `2-u` for `set-2-u` (W-218, 2026-09-23).

- Compare the hand-off with the key **Arpit pastes**. **Return no answer text and no relevant
  document names.**
- **Per-query rows** (non-sealed ids): `id, set, rung, difficulty_band,
  hit@1, hit@5, recall@5, rank_first_relevant, abstained, abstain_correct` →
  `work/regression/<date>-golden-rung-NNNNN/evidence/per-query-<set>.csv`.
  **`set` and `difficulty_band` are columns so the report can stratify**; the
  band comes from the key, never from these rows.
- **Report the sets apart.** Set 1 and set 2 get their own aggregates, and the
  gap between them is a finding in its own right. 🔴 **A figure pooled across both
  sets is never written** — it erases the only thing two sets buy.
- **Sealed ids:** one aggregate row per metric, never per query.
- **Pooling keeps the key complete as the corpus grows:** for every question, judge
  each **top-5 result that is not in `relevant`**. If it genuinely answers the
  question, add it to `relevant` with `added_at_rung`, bump `key_version`, and
  re-score. Report only *how many* were added, and hand the updated key back to
  Arpit in a fenced block — never to a file.
- **Judge the answer text too**, which is new: whether `answer_text` is supported
  by its own citations, and whether it agrees with the key. Counts per set and per
  difficulty band — `supported_and_correct`, `supported_but_wrong`, `unsupported`,
  `declined`.

---

## What a result may and may not claim

- **Set 1's first scored run on a frozen ladder is `blind`.** Once Claude has
  seen per-query scores, any engine or config change made afterwards is
  `informed` for the non-sealed ids. The sealed aggregate stays the clean
  comparison.
- 🔴 **Set 2 is `informed` from its first number and stays that way** — its
  author and its runner are the same model family, and no separation of sessions
  changes that. It is bought for **comparison against set 1**, not for a delta.
- 🔴 **Nothing scored on set 1 or set 2 may be compared with a number from the
  deleted 2026-09-12 key.** Those ids are gone and were never re-used; the
  corpus is the same but the instrument is not.
- **A delta follows SR-RS**: paired, discordant-count floor, headroom per direction.
- **No threshold is moved** after a number exists — **including the difficulty
  bands**, which are movable only until the first number is scored against them.
