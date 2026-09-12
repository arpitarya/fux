---
type: OpenItem
id: W-146
title: "W-146 — the rest of L0: the unhoused CLAUDE.md sections, and two rulings Arpit owes"
description: "W-122 moved the ten laws into their records and made CLAUDE.md a generated view. What it deliberately did not do: write records for the eleven technical-but-unhoused CLAUDE.md sections its inventory names, and settle two questions only Arpit can — whether ADR-WORK-QUEUE exists, and how far `never restates` reaches into docstrings. Carries W-122's delivered inventory verbatim."
status: open
lane: arpit
timestamp: 2026-09-12T00:00:00Z
---

# W-146 — the rest of L0

**Model: Opus.** Every row here decides where a rule lives, and a wrong answer
reads as authority. The record-writing half is Sonnet-executable once Arpit has
ruled on §2 and a row's target record is named.

## Where this came from

**[W-122](../IMPLEMENTATION.md) landed 2026-09-12** — the ten laws now live in
`ADR-LAW-0` … `ADR-LAW-9`, `CLAUDE.md` §Non-negotiable constraints is generated
and test-bound, and the key-tree gate
([`tests/test_adr_config_keys.py`](../../tests/test_adr_config_keys.py)) holds
ADR-CONFIG and ADR-TUNE equal to the code in both directions.

**This item is what that change deliberately left.** Writing eleven new records
in the commit that moved the constitution would have been a far larger and far
less reviewable diff than the one Arpit ruled on, so the inventory below names
each one instead of half-moving it.

⚠ **Nothing here is a second copy of anything.** Every `🟡 open` row is a section
**no record states today** — that is precisely why it is open. L0's drift hazard
needs two statements, and these have one.

## 1 · The inventory (delivered by W-122, 2026-09-12)

**One row per `CLAUDE.md` section, in file order.** The rule that decided each:
*normative and technical* → a record. *Process, or a statement of fact about the
repo* → stays, because there is no record for "how an agent behaves in a session"
and inventing one would be the same duplication in a new place.

| # | `CLAUDE.md` section | verdict | state |
|---|---|---|---|
| 1 | Law zero — the ADRs are always up to date | needs a record (`ADR-LAW-0` covers authority, not the freshness gate) | 🟡 open |
| 2 | Triage first — a human-blocked queue | ✅ stays — agent process | done |
| 3 | Where the state of play lives | ✅ stays — a pointer table | done |
| 4 | What we are building (scope) | ✅ stays — statements of fact + links | done |
| 5 | **Non-negotiable constraints** | 🔴 **moved** → the ten `ADR-LAW-n`; section is now a generated, test-bound block | ✅ **landed** |
| 6 | Litmus (the 10 000-document design point) | 🟠 needs a record | 🟡 open |
| 7 | How work happens here (the lifecycle) | ✅ stays — process | done |
| 8 | A pre-registered threshold may never move | 🔴 link → [ADR-RS](../../docs/adr/0133_predictions.md) already holds it | 🟡 open |
| 9 | Follow the OKF pattern | 🟠 link to ADR-DOCS-TABLE, or a record | 🟡 open |
| 10 | Documentation style (required) | ✅ stays — process | done |
| 11 | Documentation discipline (required) | ✅ stays — process | done |
| 12 | The three-file session discipline | ✅ stays — process | done |
| 13 | OPEN-WORK — the single live queue | 🔴 **needs a record** | 🔴 **row 20 — Arpit** |
| 14 | Keep the docs in sync (required) | ✅ stays — process | done |
| 15 | Session continuity — the running worklog | ✅ stays — process | done |
| 16 | Conformance runs — file every one | 🔴 link → ADR-RS holds both halves | 🟡 open |
| 17 | Golden answer key — Claude never reads it | 🟠 needs a record (it is a technical prohibition with a hook behind it) | 🟡 open |
| 18 | Layout | ✅ stays — a statement of fact | done |
| 19 | Error contract | 🟠 needs a record | 🟡 open |
| 20 | Build & test | ✅ stays — commands | done |
| 21 | Merge wall | ✅ stays — a statement of fact about GitHub | done |
| 22 | Hard-won build knowledge — the two binding items (BM25F weight-then-saturate; no wall-clock on the maintenance path) | 🟠 **needs a record** — laws-in-waiting in an appendix | 🟡 open |
| 23 | Blockers stop the session | ✅ stays — process | done |
| 24 | Answer length · Say what you are doing | ✅ stays — process | done |
| 25 | Package identity | 🟠 needs a record | 🟡 open |
| 26 | Archive is not evidence | 🟠 needs a record | 🟡 open |

⚠ **`🟡 open` is not a defect and does not block anything.** Every one of those
sections is *technical and unhoused*, so L0 says it wants a record — and writing
nine new records in the change that moved the laws would have been a far bigger,
far less reviewable diff than the one Arpit ruled on. They are named here so the
next session can take one, and none of them is a second copy of anything: no
record states them today, which is why they stay legible where they are.

## 2 · 🔴 The two rulings

1. **The work-queue discipline has no record** (row 13). `OPEN-WORK.md`'s rules
   1–10, the 5-day inbox threshold, the lane tags, the ball markers and *ages are
   recomputed, never copied* are stated in `CLAUDE.md` **and** in that file's own
   footer, and **in no ADR at all** — so under L0 they are stated twice and owned
   nowhere. Surfaced by
   [`tests/test_open_work_is_not_stale.py`](../../tests/test_open_work_is_not_stale.py)
   and [`tests/test_open_work_rows_are_short.py`](../../tests/test_open_work_rows_are_short.py),
   which between them enforce most of those rules and **can name no owning
   record**. ⚠ **Pre-existing, not introduced by either test** — the tests made
   the gap visible. Candidate name: `ADR-WORK-QUEUE`. **Arpit rules whether it is
   written**; until then the two tests are unowned guards, which the ownership
   table permits and L0 does not.
2. **How far does "never restates" reach into code comments?** ADR-LAW-0 decision
   4's table names *a docstring* among the artifacts that must link rather than
   restate. Taken literally that reaches `config.py`'s `UrlSource` docstring, which
   explains every key and its default — and then most docstrings in `src/fux/`,
   because this repo's style is dense explanatory prose next to the code.
   **This session applied the narrow reading** — a comment may explain *mechanism
   and rationale*; the two artifacts whose whole content was *descriptions of
   keys* (`config.schema.json`, `fux setup`'s `fux.toml` comments) were removed —
   and did **not** touch a docstring anywhere. Stripping the codebase's comments
   is not a change an agent should make on its own reading of a law. ⚠ **Cost of
   the narrow reading, stated plainly:** `UrlSource`'s docstring and ADR-CONFIG
   can disagree about a default while both look correct, which is exactly what
   decision 1 forbids. It is unguarded today.
