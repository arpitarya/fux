---
name: docket
description: Walk Arpit through work/OPEN-WORK.md one item at a time — the decider's inbox first, then the open items — explaining each in plain words, recommending a ruling or next move, and writing his rulings back once he confirms. Use on /docket, "go through open work", "what's waiting on me", "walk me through the queue/inbox", "explain the open items".
---

# Docket — the queue, one case at a time

**Takes** `work/OPEN-WORK.md`. **Gives** one card per item, a recommendation, and Arpit's ruling written back.

**Docket holds no rules.** Every rule it follows lives in the record named in OPEN-WORK's frontmatter (`governed_by_path`) and the records it points to — here, SR-WORK-OPEN-QUEUE, with SR-WORK-DOCS, SR-WORK-SESSION and SR-WORK-BLOCKERS. Where this skill and a record disagree, the record wins (SR-LAW-0): say so, and fix the skill.

## 1 · Prepare — silently, before the first card

- **Read:** `CLAUDE.md`, `work/OPEN-WORK.md`, its governing record, `work/BLOCKED.json`, `work/NOW.md`, `work/INTERVIEW.md` §1–2, the top three `work/WORKLOG.md` entries.
- **Per row:** read its `work/open/W-nn-*.md` — At a glance, DoD, what is left, the record it names.
- **Reconcile before you report** (queue rules 46, 50): check each row against `work/IMPLEMENTATION.md`, `git log -- <its paths>` and the worklog. A marker that disagrees with ground truth is **drift** — an inbox row the worklog says is already ruled, a 🟢 row the worklog says waits on the decider.
- **Recompute every inbox `age`** as today − `filed` (rule 40); never copy it.

## 2 · Open — one short block

- Line 1: `Docket: N rulings owed · M open items · D drift`.
- An open blocker in `BLOCKED.json` is named first.
- The inbox rows rule 41 says to name, each with its age; 🔺 first (rule 33).
- Drift: one line each.

## 3 · Order

1. **Drift** — each is a case of its own, fixed only with his OK.
2. **The inbox** — table order, 🔺 first.
3. **Open items** — `build` → `testing` → `record update` → `research`, in the order the queue lists them.

Default is everything; he can say "inbox only" at any point.

## 4 · One card per item — ten lines or fewer (SR-WORK-SESSION decision 8)

```
**[k/N] 🔴 W-nn — <short title>**
- **What:** <one line, plain words>
- **Stuck on / left:** <the one thing>
- **Blocks:** <the ↳ blocks sub-row, or "nothing else">
- **Options:** A <…, its cost> · B <…, its cost> · (C)
- **Recommend: A** — <why, one line; name the law or record it rests on>
- **ELI5:** <one sentence a child would follow>
```

A 🟡 card carries its blocker in the header, as its row does: `**[k/N] 🟡 W-nn waits on W-mm — <short title>**` (another project's: `waits on fux W-mm`).

**Then ask** — AskUserQuestion, plain text if it is absent:

- **Inbox row:** the recommended ruling first, labelled `(Recommended)` · the other ruling(s) · `Skip`. "Stop" comes through Other.
- **Open item:** `Do it now` · `Leave as is` · `Re-ball or close` · `Skip`. `Do it now` is offered for 🟢 only, and never for a `research` row in Claude Code (rules 32, 37a).

**A recommendation is earned:**

- **Ground it** — read the code or run the command before claiming state (SR-WORK-SESSION decision 11).
- **Weigh by the queue's priority** — damage that grows with time beats damage that is merely present (rule 36).
- **Check it against the laws** — name the one it touches (L2 for a dependency, L8 for a budget).
- **Close call?** Say so, and give the strongest case for the other option in one line.

## 5 · Write the ruling back — only after he confirms

- **Show the edits first** — a short list, file → change — and get a yes. Silence, "ok" or "next" is not a ruling.
- **His words, verbatim:** `**Arpit, YYYY-MM-DD:** *"…"*`.
- **One change, in SR-WORK-DOCS decision 10's order:**
  1. `work/OPEN-WORK.md` — remove the inbox row **and** its `↳ blocks:` sub-row; re-ball every row that waited on it (rule 28); an emptied inbox keeps its table and gets the `*Empty since YYYY-MM-DD` line naming the next gate (rule 45a).
  2. The item file — the ruling, the At a glance state, `updated` / `updated_by` (rules 58–62).
  3. The owning record, when the ruling changes a decision (rule 52; SR-LAW-0).
  4. `work/BLOCKED.json`, when the ruling answers it (SR-WORK-BLOCKERS).
  5. `work/INTERVIEW.md` — state of play, in flight.
  6. The registry row of every doc touched (SR-WORK-REGISTRY §3).
- **Ruled is not done.** A ruling that needs his hands (a GitHub setting, a registry account) keeps its row, reworded, until he says it is done.
- **Check:** `python3 scripts/check-open-work-inbox.py && python3 scripts/check-work-system.py` — fix what they print before the next card.
- **No commit unless he asks.** If he does: re-derive `git status`, commit with explicit pathspecs, let the `commit-msg` guard run (SR-WORK-OWNERSHIP).

## 6 · Close

- One line: `Ruled X · skipped Y · drift fixed Z · next: <the single next step>`.
- Append the worklog entry (SR-WORK-SESSION decision 1 — a docket with no rulings still counts) and set `work/NOW.md`.

## Never

- Rule for him, add a 🔺, or start work on a 🔴, 🟣 or 🟡 item.
- Write before he confirms, or mark done what he has only ruled.
- Copy a record's rule into a file — point to it.
- Cite an `archive/` document as evidence (SR-WORK-ARCHIVE).

## Outside a repo with these records

A repo with `work/OPEN-WORK.md` but no governing record: run steps 1–4 as written, write back only to OPEN-WORK and the item file, and skip the checks that do not exist.
