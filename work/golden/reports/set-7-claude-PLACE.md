# PLACE.md — put set-7-claude (generation 6) in place · W-277

**Model: Claude Code, Sonnet.** Run from the fux repository root, after Arpit
has unzipped set-7-claude-release.zip there. Read CLAUDE.md first.

🔴 **L11.** The key is NOT in this folder and you never look for it. Do not
open, list, count, hash or search work/golden/golden-answers/ or its singular
spelling, and never search work/ recursively without excluding work/golden/.

## 1 · Check before reading anything — stop on any failure

1. List incoming/set-7-claude/ recursively, names only. Every file is in
   MANIFEST.tsv and every MANIFEST.tsv row has its file. If any file name
   contains "key" or "answer" in any case, STOP: do not open it, tell Arpit a
   key may be outside its address (L11 decision 10), and file it.
2. Field names only, printing no value:

   python3 -c "import json,sys; print(sorted({tuple(sorted(json.loads(l))) for l in open(sys.argv[1]) if l.strip()}))" incoming/set-7-claude/work/golden/questions/set-7-claude.jsonl

   It must print exactly [('id', 'question')]. Anything else: STOP, as above.
3. Additions only (SR-WORK-TESTDATA A20): no `move` destination exists yet, and
   no path in seed-dates.add.tsv is already in work/golden/seed-dates.tsv.

## 2 · Place

Follow MANIFEST.tsv: `move` puts the file at its destination; `append` adds its
lines to the end of the destination. Write nothing else.

## 3 · Check the released half (W-277 DoD 4), from the placed files only

- 8 new long documents, each ≥ 3 000 words and ≥ 8 `## ` headings;
- 48 short competitors, each under 400 words;
- 165 question ids s7c-001 … contiguous and unique, `{"id", "question"}` only;
- one seed-dates.tsv row per new seed file, dated 2024-01-01 … 2026-09-01, no
  duplicate path.

Report each as PASS or FAIL with its numbers.

## 4 · Clean up, in the same change

- Delete incoming/set-7-claude/, and incoming/ if it is then empty.
- Delete work/golden/prompts/15-claude-gen6-section-seed.md (SR-WORK-TESTDATA
  decision 5).
- Update work/open/W-277-section-test-data-gen6.md (DoD 3–5),
  work/OPEN-WORK.md, work/golden/README.md (generation 6, set-7-claude) and
  work/WORKLOG.md.

## 5 · Show Arpit, then commit on his yes

Summarise the change as file names and counts only. Run the unit suite and the
doc tests. Commit with explicit pathspecs on his "yes". Do not push.
