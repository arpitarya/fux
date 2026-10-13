---
type: Handoff
name: W-277
description: "Arpit's ask (2026-10-11, Cowork): new test data for the section re-test, built from W-270's finding (49 of 60 section questions already at rank 1) — generation 6, eight long documents, one short competitor per tagged section (≥ 48) and set-7-claude (~165 questions, ≥ 100 tagged step10_section), authored by an isolated claude.ai chat from prompt 15 and delivered as downloadable files plus a Claude Code placement prompt — the delivery he ruled the standing rule for every future set."
item: W-277
filed: 2026-10-11
ball: arpit
---

# W-277 — section records: generation-6 test data (`set-7-claude`)

**Status: CLOSED 2026-10-12.** Arpit ran prompt 15 (as re-amended) in a fresh chat, saved the key by his own hand and unzipped the release; Claude Code ran its `PLACE.md`, every check passed, and 75 files were placed by the manifest. Generation 6 is seeds 113–182 and `questions/set-7-claude.jsonl` (165). Prompt 15 and `incoming/` were deleted in the same change. The ladder rebuild and the re-run are W-278's.

**Arpit, 2026-10-11 (Cowork),** after W-270's STOP: *"Give me a work item to
create the new test data based on the findings. And I'll run it in an
independent chat. The chat should give me downloadable files. And that should be
done for all the future test data creations rather than in chat blocks."* Then:
*"the test data creation chat … should create all those files then at the end
give a prompt that can be used in Claude code … I'll download those files, put
it in the repository then I'll run that Claude prompt so that all the files are
placed in proper place."*

**Model:** the author is **Claude Opus, highest reasoning, in a brand-new
claude.ai chat** outside the `fux` project, with file creation and nothing else
(A1). **The session that filed this read W-270's scores, so it may not author.**
Placement and the DoD 4 check: **Claude Code, Sonnet**, by `PLACE.md`.

## What W-270 found, and what this generation changes

| finding (W-270, `set-6-claude`) | change (SR-WORK-TESTDATA R10, amended 2026-10-11) |
|---|---|
| 49 of 60 tagged questions already at rank 1 at baseline; slice **11** against a floor of **15** — an 18 % miss rate | **≥ 100 tagged**, sized as 15 ÷ the last miss rate with margin; ~165 questions in all |
| 6 long documents — 60 questions on 6 documents behave like few independent points | **8 long documents**, ≥ 12 questions each over ≥ 6 sections |
| competitors "able to win" on paper, but the question's words were also **scattered** through 3 000-word bodies, which add up | the question's distinctive words appear in the long document **only inside the answering section, twice each**; the competitor carries them **once each, in its body only — never in its title or a heading** (re-amended the same day, below); **one competitor per tagged section** (≥ 48; Arpit, 2026-10-11, below) |
| 3 of 6 long documents came out under 3 000 words (2 596–2 949) | word, section and placement rules **checked by counting in code** before delivery — a count, never a ranking (T3) |

## Amended 2026-10-11 — a competitor for every tagged section

**Arpit, 2026-10-11 (Cowork),** after the analysis of why set 6 showed no gain:
*"Any future set test needs a shorter competitor for each tagged section."*
Prompt 15 asked for ≥ 3 competitors per long document, one able to serve several
questions — so most tagged sections had no rival and their questions could not
lose at baseline. **Now every tagged section has its own competitor** (≥ 48),
written into [SR-WORK-TESTDATA](../../records/0068_WORK-test-data.md) R10 and
prompt 15 §2–§3 before Arpit runs it. The two mechanism changes he asked for in
the same message are [W-278](W-278-section-term-v3.md).

## Re-amended 2026-10-11 (later) — the competitor wins by length alone

**Arpit, 2026-10-11 (Cowork), on the research into why section records
failed: *"update the work items to go with the suggestive approach."*** The
first amendment over-corrected. It asked for the question's words in the
competitor's **title or a heading, its first three lines and ≥ 2 more times**
(a field-weighted tf of about 8) against the section's **≤ 2, body only**. Under
BM25F that competitor out-matches the section in *any* unit — per distinctive
term about 1.9·idf against 1.0·idf for the section scored as a document — so
the baseline would miss nearly every tagged question (the slice floor met) and
**no section mechanism could win one back: a FAIL by construction.**

The shape step 10 exists for is *a long document loses because it is long*, so
the data isolates that one cause (R10, re-amended; prompt 15 §2–§3):

| | the long document | its competitor |
|---|---|---|
| the question's distinctive words | **twice each**, only inside the answering section, body only — nowhere else in the document | **once each**, **body only — never in its title, a heading or its first line** |
| length | ≥ 3 000 words; the answering section **≤ 200 words** | **200–400 words** |

By the formula (`b` 0.15, `k1` 1.2, document average ≈ 134 tokens, idf = 1): at
baseline the competitor scores ≈ 0.91 per term against the long document's
≈ 0.70 — it wins by length; the answering section scored as a document scores
≈ 1.37 against that 0.91 — a term that credits the section wins it back. Both
margins hold by construction and are **checked by counting** (T3), never by
ranking. The competitor stays plausible and wrong on the value; its title
paraphrases the subject without the distinctive words.

**The guardrail stays in `other`:** a few `other` questions whose answer is a
short document that *does* carry the words in its title (the first amendment's
shape) — the term must not steal those, and L13's C2 reads them.

## The delivery — the standing rule from this item on

**Ruled by Arpit for every future set**, and written into the records in the
filing change: [L11](../../records/0013_LAW-11-sealed-answer-key.md) decision 6
(a law, amended on his ruling, named there) and
[SR-WORK-TESTDATA](../../records/0068_WORK-test-data.md) A1, A3, A24.

| download | holds | goes |
|---|---|---|
| `set-7-claude-release.zip` → `incoming/set-7-claude/` | documents, `seed-dates.add.tsv`, the released questions, `MANIFEST.tsv`, `REPORT.md`, **`PLACE.md`** | unzipped at the repo root by Arpit; placed by Claude Code running `PLACE.md` |
| `set-7-claude-KEY.jsonl` | **the key** | 🔴 Arpit's hand only → `work/golden/golden-answers/set-7-claude.jsonl`; download deleted |

`PLACE.md` checks **file names against the manifest** and the released
questions' **field names only** (a program that prints no value) before it reads
anything, and stops and declares on anything that looks like a key.

## Definition of done

| DoD | state | where |
|---|---|---|
| 1 · the authoring prompt, written from SR-WORK-TESTDATA, with the placement prompt inside it | ✅ 2026-10-11 | prompt 15 — deleted 2026-10-12 (DoD 5); `git log --diff-filter=D -- work/golden/prompts/` |
| 2 · 🔴 **Arpit** runs it in a fresh chat; saves the key into `golden-answers/` by hand; unzips the release at the repo root | ✅ 2026-10-12 | Arpit; the key's address was never looked at (L11) |
| 3 · `PLACE.md` run in Claude Code (Sonnet): checks pass, files placed by the manifest | ✅ 2026-10-12 | 75 manifest rows, each with its file and no file without a row; no name holds `key` or `answer`; fields `[('id', 'question')]`; no `move` destination pre-existed; 70 date rows, none already present. Run by Opus 5.5, not Sonnet |
| 4 · the released half checked against prompt 15's counts: 8 long (≥ 3 000 words, ≥ 8 sections), ≥ 48 short (200–400 words, the words once each and never in a title or heading), one per tagged section and none shared across sections, ≈ 165 ids `s7c-…` with `id` + `question` only, a date row per new file | ✅ 2026-10-12 | 8 long (113–120): 3 060–3 166 words, 13–21 `## ` headings · 48 short (121–168): 254–324 words · 165 ids `s7c-001…165`, contiguous, unique, `{id, question}` only · 70 date rows, 2025-03-24…2026-08-24, no duplicate path. **Not counted here:** word placement and one-competitor-per-section — those need the key. The author's `REPORT.md` says 104 of 104 placements pass; the scorer's pool counts check the rest |
| 5 · prompt 15 and `incoming/` deleted in the change that commits the data (SR-WORK-TESTDATA decision 5) | ✅ 2026-10-12 | the closing change |

## Out of scope — and why this data alone cannot give a PASS

- **The latency guardrail failed** in W-270 (+328 ms against 100), located in
  `scan.py:_attach_sections` (≈ 18 900 `json.loads` per query). A re-run on this
  data still fails it unless that attachment is rebuilt and measured first.
- **The mechanism did lift wrong long documents** — measured from the arms'
  own `ranked` lists on 2026-10-11 (set-5: 19 of 24 rank-1 changes brought in a
  long document; set-6: 17 of 21). The cause and the third form are
  [W-278](W-278-section-term-v3.md). Data cannot fix a mechanism.
- **The ladder rebuild (generation 6, a new baseline), the new bar and the
  re-run** are [W-278](W-278-section-term-v3.md) DoD 3–5, ruled 2026-10-11
  (W-270 closed on that ruling). This item only makes the data.

## Custody

- 🔴 **The key is Arpit's** ([L11](../../records/0013_LAW-11-sealed-answer-key.md)).
  No session writes, reads or receives it; the placement session never looks
  for it. Tag counts DoD 4 cannot see are checked by the scorer's pool counts in
  the measuring run.
- `informed`, permanently (A5).

## Records

Amended in the filing change: SR-LAW-11 (law block and decision 6 — Arpit's
ruling), SR-WORK-TESTDATA (A1, A3, A24, R10), SR-WORK-GOLDEN (the per-set
handoff), `work/golden/README.md`, `CLAUDE.md` (regenerated). The data change
itself touches no SR; `work/golden/README.md` names the generation.
