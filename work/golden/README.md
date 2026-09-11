# `work/golden/` — the sealed golden benchmark

**One test set for `fux-benchmark` and `fux-lab`: ten seed documents written by
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

---

## Layout

```
work/golden/
  README.md                 this file — the process
  seed/                     the 10 seed documents (Codex writes; Claude may read)
  golden-answer/answers.jsonl   🔒 questions + answers (Arpit / Codex / ChatGPT only)
  questions.jsonl           released by Codex AFTER the ladder is frozen — ids + text only
  ladder/rung-NNNNN.sha256      frozen manifests: which files make each rung, by hash
  ladder/rung-NNNNN.index       the engine version and index root hash each rung was built with
  prompts/                  the five paste-ready prompts, one per phase
```

**The ladder corpus itself lives in `~/my_programs/fux-benchmark/corpora/golden/`**,
not in this repo — 10 000 documents would bloat fux's git history. Only the
manifests are committed here, so every rung is verifiable byte for byte.

### One directory and one index per rung (Arpit, 2026-09-11)

**Every rung is its own self-contained directory with its own fux index**, so a
rung is tested by asking, never by re-ingesting — and a 100-document run never
waits on 10 000.

```
~/my_programs/fux-benchmark/corpora/golden/
  rung-00010/   seed/ (10)                          .fux/  ← its own index
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
| **1. Seed** | Codex | nothing from fux | `seed/` (10 docs) + `golden-answer/answers.jsonl` | [`prompts/1-codex-seed.md`](prompts/1-codex-seed.md) |
| **2. Extend** | Claude Code | `seed/` **only** | corpus in fux-benchmark + `ladder/*.sha256` | [`prompts/2-claude-extend.md`](prompts/2-claude-extend.md) |
| **3. Freeze & release** | Codex | the manifests + the key | `questions.jsonl`; marks the sealed subset in the key | [`prompts/3-codex-release.md`](prompts/3-codex-release.md) |
| **4. Run** | Claude Code | the ladder + `questions.jsonl` | `predictions.jsonl` per rung | [`prompts/4-claude-run.md`](prompts/4-claude-run.md) |
| **5. Score** | Codex | predictions + the key | per-query results **without answers** | [`prompts/5-codex-score.md`](prompts/5-codex-score.md) |

**Order is load-bearing.** Questions are released only after **every** rung is
frozen. A rung built after release was built by a session that could have seen
the questions, so it is `informed` for good.

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
- **~100 questions**, roughly:

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

## Phase 2 — Extend the ladder (Claude Code, blind)

**Rungs: 10 → 100 → 200 → 500 → 1 000 → 2 000 → 5 000 → 10 000.** Nested: each
rung is the previous one plus new files, so the seed documents are in every rung.

⚠ **10 000 is the ceiling.** Arpit's 2026-08-22 ruling forbids measuring above it
until he reopens it; *"and so on"* past 10 000 is a separate, later decision.

- **Claude reads `seed/` and nothing else** from this directory.
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
- 🔴 **Every seed file must be indexed.** The seeds are `.md`, `.txt`, `.yaml`,
  `.eml` and `.html` on purpose; the rung's `.fux/formats.toml` must include every
  extension present, and the ingest skip list must name **no** `seed/` file. A seed
  silently skipped makes a question fail for a reason that has nothing to do with ranking.
- **Freeze:** `ladder/rung-NNNNN.sha256` lists `sha256  path  category  origin` for
  every document in the rung (not the index). A rung is frozen when its manifest
  and index record are committed.

---

## Phase 3 — Freeze and release (Codex)

1. Check every manifest against its rung directory (hashes match; each rung's
   documents contain the previous rung's, byte for byte; seed files in every rung).
2. **Sealed holdout:** mark **20 %** of ids `sealed: true`, spread across types.
   Their results are only ever reported **in aggregate** — a clean holdout that
   survives Claude seeing per-query scores for the rest.
3. Write `questions.jsonl` — `{"id", "question"}` **only**. No type, no
   `answerable`, no difficulty, no sealed flag.
4. Record the key's SHA-256 in `ladder/KEY.sha256`. Any later change to the key
   changes the hash, and a changed key is a new `key_version`, never an edit.

---

## Phase 4 — Run (Claude Code)

- **Pre-register first**, per run: `work/regression/<date>-golden-rung-NNNNN/PRE-REGISTRATION.md`
  — engine sha, rung, metrics with `k` named, and the headroom disclosure ADR-RS
  requires ([ADR-RS](../../docs/adr/0043_predictions.md) decision 22, which is where
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
- **A delta follows ADR-RS**: paired, discordant-count floor, headroom per direction.
- **No threshold is moved** after a number exists.
