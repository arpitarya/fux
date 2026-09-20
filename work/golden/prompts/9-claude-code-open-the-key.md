---
type: Prompt
title: "Prompt 9 — Claude Code: retire L11's prohibition; the golden key is readable by Claude for scoring"
item: W-136
timestamp: 2026-09-18T00:00:00Z
---

# Prompt 9 — open the key

**Model: Opus.** This retires a Law and regenerates two byte-gated blocks.

**Arpit, 2026-09-18:** *"Codex already did the job. Codex gave us the answer.
That's it. Now run all the test cases and give me one prompt at the end through
which I'll disable all the golden answers restrictions and then you can test out
all the answers."*

⚠ **Consequence, recorded so nobody rediscovers it:** from the moment this lands,
**every number ever filed against the golden benchmark is `informed`**, set 1
included, and W-196's "set 1 keeps its status" ruling is superseded by this one.

**Paste everything below the line into Claude Code, from the root of the `fux` repo.**

---

Arpit rules, 2026-09-18, that the golden answer key is no longer closed to
Claude. Land that ruling as one change. Read `CLAUDE.md`, `records/0012_LAW-11-sealed-answer-key.md`,
`records/0066_WORK-golden.md` and `work/golden/README.md` first.

**1. The hook will block you.** `.claude/hooks/guard-golden-answer.sh` fails
closed on the substring `golden-answer`, in prose as well as paths. Before any
other edit, remove its registration from `.claude/settings.json` (the
`PreToolUse` entry) and delete the `permissions.deny` rules that name
`golden-answer`. Keep the file itself until step 6 so its history is visible.

**2. Amend the Law, with his name and date.** In `records/0012_LAW-11-sealed-answer-key.md`:
- Decision 4 ("the one route is a paste, and it is Codex's") is **superseded**:
  the key at `work/golden/golden-answers/` (plural — canonical since W-198) is
  **readable by any session for scoring and review**. Quote the ruling above.
- Decision 5 (read and write forbidden) is narrowed to **write**: no agent
  edits, moves or deletes a key; `key_version` still advances only by a pooling
  step that returns the whole key to Arpit.
- Decisions 6–8 (authoring carve-out, informed-permanently, declare-a-leak) are
  **retired**, with one sentence each saying why they no longer bind.
- The block in §2 "The law (normative)" is rewritten to state the new law in
  one paragraph: **the key is never committed, and every golden number is
  `informed`.** That is all that remains of L11.
- Consequences gains: *"Every golden number filed before or after this date is
  `informed`. The benchmark measures where the engine stands; it no longer
  produces a number the builder's model family could not have seen."*
- The Veto condition is rewritten: reopen only if a key is found **committed**
  on any ref.

**3. Amend the process record.** `records/0066_WORK-golden.md` decision 2: drop
"no key file exists" and "the paste route"; state that the key lives at
`work/golden/golden-answers/` on Arpit's machine, gitignored, readable, never
committed. Retire the `blind`/`informed` split for golden runs — all are
`informed` — and say so in SR-RS's terms with a link to
`records/0133_predictions.md` decision 11.

**4. Regenerate the two blocks.** `python scripts/gen-laws.py --write` and
`python scripts/gen-golden.py --write`; `tests/test_claude_md_laws.py` and
`tests/test_claude_md_golden.py` must pass byte-equal.

**5. Guards that STAY, guards that go.**
- **Stays:** `.gitignore` lines for `golden-answer/`, `**/golden-answer/`,
  `**/golden-answers*` — the key is never committed. Stays: `!work/golden` in
  `.fux/sources/dirs` — the benchmark never enters fux's own index. Stays:
  `tests/test_golden_key_never_committed.py`, updated so it no longer asserts
  a Claude session may not read.
- **Goes:** every `permissions.deny` rule naming `golden-answer`; the hook's
  registration; `feedback`-style prose in `CLAUDE.md` saying Claude may not
  look. `work/golden/README.md` §Custody and §Between the prompts are rewritten;
  prompts 1–8 and 6E lose their "no key file / never read" clauses and gain one
  line: *"the key is readable; every number is informed."*

**6. Delete the hook file** `.claude/hooks/guard-golden-answer.sh` in the same
change, with the commit message saying it was retired by this ruling.

**7. Queue.** W-196 (archived): add a one-line note that its ruling is
superseded by this one. W-197 / W-198: unchanged in substance — the plural
canonical name and gitignore glob still land; strip their "no agent may look"
language. W-136: prompt 6 is no longer Codex-only; note that Claude may score.
W-87, W-176 g4–9, W-190, W-191, W-195 remain waiting on a scored run.

**8. Then score.** Read `work/golden/golden-answers/`, join to
`work/regression/2026-09-16-golden-rung-00100/evidence/handoff-set-1.jsonl` and
`handoff-set-2.jsonl` on `id`, and produce what prompt 6 asked for: pooling
judged into `relevant` with `key_version` bumped, `evidence/per-query-<SET>.csv`
for non-sealed ids, `evidence/sealed-aggregate-<SET>.csv`, the answer-text
verdicts, both sets separate, never pooled. `difficulty_band` is still absent
from key_version 1 (W-195) — report that the breakdown is not producible and do
not derive one from `type` or from fux's results. File it under that run
directory with `classification: informed`, an `## Authorship` section, and a
README row. Nothing here changes the engine.

**9. Run both suites whole** before believing any of it is done. Append the
worklog entry. Do not run the other seven rungs in this change — that is
prompt 5 in `fux-lab`, and it is next.
