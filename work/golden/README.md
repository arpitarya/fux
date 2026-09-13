---
type: Index
description: "Index of the sealed golden benchmark: seed corpus, prompts, and the one rule."
---

# `work/golden/` — the sealed golden benchmark

**The test data for `fux-lab` — and only for `fux-lab`, per [SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md): seed documents written by
Codex, ~100 questions with answers Claude never sees, and a corpus ladder Claude
grows from 10 to 10 000 documents without ever seeing a question.**

Ruled by Arpit, 2026-09-11. Tracked as [W-136](../open/W-136-golden-benchmark.md).

---

## 🔴 The one rule

**Claude never opens `golden-answer/`.** Not Cowork, not Claude Code, not a
subagent — not to check the format, not to count lines, not by `grep -r`.

- **Who may read it:** Arpit, Codex, ChatGPT.
- **Why:** a question whose answer the engine's builder has seen can be
  optimised against without anyone meaning to. A leak does not fail loudly; it
  produces a number that looks exactly like a clean one.
- **What guards it** — layered, and **none of it is a cryptographic guarantee**
  (Claude Code and Codex run as the same Mac user, so no file permission can
  tell them apart):

| guard | stops |
|---|---|
| `.gitignore` | the key reaching git history or a remote; `rg` and Claude's Grep skipping it by default |
| `!work/golden` in `.fux/sources/dirs` | the key's vocabulary landing in fux's own **committed** index |
| `permissions.deny` in `.claude/settings.json` | Claude Code's Read / Edit / Grep / Glob on the folder |
| `.claude/hooks/guard-golden-answer.sh` | any Claude Code tool call — Bash included — that names `golden-answer` |
| CLAUDE.md §Golden answer key | everything above can't reach: Cowork, and a recursive `grep` |

⚠ **Back the key up yourself.** It is gitignored, so git will not keep it.

### ⚠ The key in use today is Claude-authored and provisional (2026-09-12)

**Arpit's Codex quota ran out with phase 1 half done**, so he ruled that Claude
write the feature-coverage documents and the key rather than leave phase 2
blocked. **Nothing leaked** — no Claude session read a key it was not meant to.
The defect is upstream: the same model family authored the questions and will
grow the corpus and run the engine, so the *"Claude wrote the brief but no facts"*
property below is **false for the key and for documents 11–15 and `seed/archive/`**.
The base ten documents are still Codex's.

**Consequence, binding:** every run scored against this key is `informed`, and
**no delta measured against it may be stated**. Codex regenerates the key under
[W-145](../open/W-145-codex-regenerates-the-key.md); the stopgap is destroyed
when it does.

### Where the key lives — Arpit decides, every time (2026-09-11)

- **No agent puts the key in this directory by default.** Every agent that would
  create, read or change the key — Codex in phases 1, 3 and 5 — **first asks Arpit**:
  *(1) the file `golden-answer/answers.jsonl`, or (2) the chat?* — and waits.
- **(1) file:** the agent reads or writes `golden-answer/answers.jsonl`.
- **(2) chat:** the agent writes **no** key file; Arpit pastes the key in, and the
  agent hands any new or updated key back in the chat for him to store.
- Claude never uses the key either way, so Claude's prompts carry no such question.

---

## Layout

```
work/golden/
  README.md                 this file — the process
  seed/                     the seed documents (Codex writes; Claude may read)
  seed/archive/             seed documents that are history — each rung declares it archived=true
  seed-dates.tsv            one date per seed document; each rung commits the file at that date
  golden-answer/answers.jsonl   🔒 questions + answers — ONLY if Arpit chose "file" (see Where the key lives)
  questions/questions.jsonl     ids + text only — the phase-4 input; see questions/README.md
  questions/README.md           what it omits, and the cost of it existing before the freeze
  ladder/rung-NNNNN.sha256      frozen manifests: which files make each rung, by hash
  ladder/rung-NNNNN.index       the engine version and index root hash each rung was built with
  prompts/                  the five paste-ready prompts, one per phase
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

---

## Who does what

| phase | who | reads | writes | prompt |
|---|---|---|---|---|
| **1. Seed** (incl. feature coverage) | Codex | nothing from fux | `seed/`, `seed/archive/`, `seed-dates.tsv` + the key, **where Arpit says** | [`prompts/1-codex-seed.md`](prompts/1-codex-seed.md) |
| **2. Extend** | Claude Code | `seed/` **only** | corpus in fux-lab + `ladder/*.sha256` | [`prompts/2-claude-extend.md`](prompts/2-claude-extend.md) |
| **3. Freeze & release** | Codex | the manifests + the key | `questions.jsonl`; marks the sealed subset in the key | [`prompts/3-codex-release.md`](prompts/3-codex-release.md) |
| **4. Run** | Claude Code | the ladder + `questions.jsonl` | `predictions.jsonl` per rung | [`prompts/4-claude-run.md`](prompts/4-claude-run.md) |
| **5. Score** | Codex | predictions + the key | per-query results **without answers** | [`prompts/5-codex-score.md`](prompts/5-codex-score.md) |

**Order is load-bearing.** Questions are released only after **every** rung is
frozen. A rung built after release was built by a session that could have seen
the questions, so it is `informed` for good.

⚠ **That order is broken on purpose since 2026-09-12** (Arpit): `questions/` exists
before the ladder does, so a chat agent can read it instead of asking him. **Phase 2
is therefore on its honour** — the session extending the corpus reads `seed/` and
nothing else, and says so in its report. Nothing mechanical enforces this.

---

## Phase 1 — Seed (Codex)

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
- **Feature coverage is part of prompt 1 (Arpit, 2026-09-12; it was prompt 1b
  until then):** superseding pairs with `supersedes:` in frontmatter, archived
  documents under `seed/archive/`, a date per seed in `seed-dates.tsv`, and
  intent-split questions that depend on them — see *Feature coverage* below.
  `1b-codex-feature-coverage.md` was merged into prompt 1 and deleted.

- **~120–125 questions**, roughly:

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
- `sealed` is set in phase 3, not phase 1.

---

## Feature coverage — what this data can test

**[SR-RS](../../records/0133_predictions.md) decision 23: a feature is measured only
on data that contains the input it acts on.** This table is that declaration.
**File names and counts only — never question text, ids or answers.**

| feature | input fux reads | set up by | documents that exercise it | questions |
|---|---|---|---|---:|
| `superseded_weight` | `supersedes:` in the newer doc's frontmatter | Codex, [prompt 1](prompts/1-codex-seed.md) part A §3 | 4 pairs: `11-decision-telematics-vendor-2026.md` → `05-…-2023.md` · `12-rate-card-2026-h2.md` → `07-rate-card-and-surcharges.md` · `13-dock-scheduling-rules-2026.md` → `09-dock-scheduling-wiki-export.html` · `15-customer-notification-matrix-2026.md` → `14-…-2025.md` | 12 |
| `archived_weight` | a directory declared `archived=true` | Codex places files in `seed/archive/`; each rung declares it (phase 2) | 5 docs in `seed/archive/`: `a01-sop-temperature-excursion-rev2.md` · `a02-kalpa-alert-routing-guide-2021.md` · `a03-dock-scheduling-wiki-2021.html` · `a04-driver-hours-policy-2019.md` · `a05-induction-checklist-2020.txt` | 9 |
| `recency_half_life_days` | commit time per file | Codex writes `seed-dates.tsv`; each rung commits at those dates (phase 2) | all 20 seed documents, dated 2019-08-12 → 2026-07-01 | 7 |
| abstention | unanswerable questions | Codex, prompt 1 | — | ~10 % of the key |
| `heading` negative control | heading-matched distractors | Claude, phase 2 `sibling` documents | 32 at rung 100, rising to 392 at rung 1 000 — `ext/sibling/` documents reusing the seed documents' **headings and document types** (Temperature Excursion Response SOP, Rate card and surcharges, Customer notification matrix, Dock scheduling rules, …) with a different company, people, facilities and every number changed | — |

A feature with no row, or a row still showing *(filled by …)*, **is not measurable
yet** — say so in the pre-registration instead of running.

---

## Phase 2 — Extend the ladder (Claude Code, blind)

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

### Built on 2026-09-12 — **the ladder is COMPLETE, all eight rungs to 10 000**

The first five landed earlier the same day, under Arpit's cap at rung 1 000; the
cap was lifted and `rung-02000`, `rung-05000` and `rung-10000` were built from
the **same committed generator and the same seed**, so the whole ladder is one
stream.

**10 000 is the ceiling and the ladder stops there** — `CLAUDE.md` §Litmus, and
[SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md) caps the lab at 10 000 documents.
There is no rung above this one and none may be built.

| rung | documents | archived | superseded | carrying `mtime` |
|---|---:|---:|---:|---:|
| `rung-seed` | 20 | 5 | 4 | 20 / 20 |
| `rung-00100` | 100 | 13 | 12 | 100 / 100 |
| `rung-00200` | 200 | 23 | 22 | 200 / 200 |
| `rung-00500` | 500 | 53 | 52 | 500 / 500 |
| `rung-01000` | 1 000 | 103 | 102 | 1 000 / 1 000 |
| **`rung-02000`** | **2 000** | **203** | **202** | **2 000 / 2 000** |
| **`rung-05000`** | **5 000** | **503** | **502** | **5 000 / 5 000** |
| **`rung-10000`** | **10 000** | **1 003** | **1 002** | **10 000 / 10 000** |

⚠ **The three new rungs were built AFTER `questions/` was opened**, which the
first five were not. **That does not make them informed** — the generator, its
seed and its blacklist are all committed and unchanged, and no question was read
by anything that produced a document. But the *ordering* argument that covers
rungs seed–1 000 (`92f5bff`, checkable in `git log`) does not extend to them, so
**what protects these three is the generator's determinism, not the clock.**
Anyone re-deriving them gets the same bytes; that is the claim, and it is
checkable.

**Nesting is verified across all eight, not asserted**: every rung's manifest
contains the previous rung's documents with **identical hashes**, and all twenty
seed documents are in `rung-10000`.

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

## Phase 3 — Freeze and release (Codex)

1. Check every manifest against its rung directory (hashes match; each rung's
   documents contain the previous rung's, byte for byte; seed files in every rung).
2. **Sealed holdout:** mark **20 %** of ids `sealed: true`, spread across types.
   Their results are only ever reported **in aggregate** — a clean holdout that
   survives Claude seeing per-query scores for the rest.
3. Write `questions/questions.jsonl` — `{"id", "question"}` **only**. No type, no
   `answerable`, no difficulty, no sealed flag. **Ids must carry no type signal** —
   permute the rows before numbering them, or the `unanswerable` slice can be
   abstained on by arithmetic. ⚠ **Since 2026-09-12 this file is written in phase 1,
   not phase 3** (Arpit), so a chat agent can run a rung without being handed the
   questions; [`questions/README.md`](questions/README.md) carries what that costs.
4. Record the key's SHA-256 in `ladder/KEY.sha256`. Any later change to the key
   changes the hash, and a changed key is a new `key_version`, never an edit.

---

## Phase 4 — Run (Claude Code)

- **Pre-register first**, per run: `work/regression/<date>-golden-rung-NNNNN/PRE-REGISTRATION.md`
  — engine sha, rung, metrics with `k` named, and the headroom disclosure SR-RS
  requires ([SR-RS](../../records/0133_predictions.md) decision 22, which is where
  W-135 landed on 2026-09-11). Commit it before any number.
- **Use the rung's own index — do not re-ingest.** Check the engine version
  matches `ladder/rung-NNNNN.index`; if it does not, re-ingest that rung once, update
  the record, and say so in the report.
- **Rungs are independent**, so they can run in parallel. A lab environment points
  at the rung directory with one pinned engine version.
- For every question, from inside the rung directory:
  `fux ask "<question>" --json --band --top 10`.
- **`predictions.jsonl`**, one line per question:
  `{"id", "ranked": [paths…], "answerable": bool, "band": "…"}`.

---

## Phase 5 — Score (Codex)

- Compare predictions with the key. **Return no answer text and no relevant
  document names.**
- **Per-query rows** (non-sealed ids): `id, rung, hit@1, hit@5, recall@5,
  rank_first_relevant, abstained, abstain_correct` →
  `work/regression/<date>-golden-rung-NNNNN/evidence/per-query.csv`.
- **Sealed ids:** one aggregate row per metric, never per query.
- **Pooling keeps the key complete as the corpus grows:** for every question, judge
  each **top-5 result that is not in `relevant`**. If it genuinely answers the
  question, add it to `relevant` with `added_at_rung`, bump `key_version`, and
  re-score. Report only *how many* were added.

---

## What a result may and may not claim

- **The first scored run on a frozen ladder is `blind`.** Once Claude has seen
  per-query scores, any engine or config change made afterwards is `informed`
  for the non-sealed ids. The sealed aggregate stays the clean comparison.
- **A delta follows SR-RS**: paired, discordant-count floor, headroom per direction.
- **No threshold is moved** after a number exists.
