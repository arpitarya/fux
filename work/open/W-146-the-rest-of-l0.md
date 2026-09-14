---
type: OpenItem
id: W-146
title: "W-146 — the rest of L0: the unhoused CLAUDE.md sections, and the ruling Arpit still owes"
description: "W-122 moved the ten laws into their records and made CLAUDE.md a generated view. What it deliberately did not do: write records for the eleven technical-but-unhoused CLAUDE.md sections its inventory names, and settle the questions only Arpit can. One is answered — SR-WORK-OPEN-QUEUE is written and the queue's rules have a home; what is left is how far `never restates` reaches into docstrings. Carries W-122's delivered inventory verbatim."
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
`SR-LAW-0` … `SR-WORK-ENVIRONMENTS`, `CLAUDE.md` §Non-negotiable constraints is generated
and test-bound, and the key-tree gate
([`tests/test_sr_config_keys.py`](../../tests/test_sr_config_keys.py)) holds
SR-CONFIG and SR-TUNE equal to the code in both directions.

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
| 1 | Law zero — the SRs are always up to date | needs no new record: `SR-LAW-0` holds the authority half and [SR-WORK-OWNERSHIP](../../records/0054_WORK-ownership.md) the freshness gate. **The section is a second copy of both** | 🟡 open — the fold is [W-173](W-173-finish-the-claude-md-extraction.md) item 2 |
| 2 | Triage first — a human-blocked queue | ✅ stays — agent process | done |
| 3 | Where the state of play lives | ✅ stays — a pointer table | done |
| 4 | What we are building (scope) | ✅ stays — statements of fact + links | done |
| 5 | **Non-negotiable constraints** | 🔴 **moved** → the ten `SR-LAW-n`; section is now a generated, test-bound block | ✅ **landed** |
| 6 | Litmus (the 10 000-document design point) | 🟠 needs a record | ✅ **landed 2026-09-14** — [SR-WORK-SCALE](../../records/0057_WORK-scale.md) |
| 7 | How work happens here (the lifecycle) | ~~stays — process~~ **overruled 2026-09-14** | ✅ **landed** — [SR-WORK-LIFECYCLE](../../records/0058_WORK-lifecycle.md) |
| 8 | A pre-registered threshold may never move | 🔴 link → [SR-RS](../../records/0133_predictions.md) already holds it | 🟡 open — [W-173](W-173-finish-the-claude-md-extraction.md) item 1 |
| 9 | Follow the OKF pattern | 🟠 a record, not a link — the bundle is not the docs table | ✅ **landed 2026-09-14** — [SR-WORK-OKF](../../records/0061_WORK-okf.md) |
| 10 | Documentation style (required) | ~~stays — process~~ **overruled 2026-09-14** | ✅ **landed** — [SR-WORK-DOCS](../../records/0059_WORK-docs.md) |
| 11 | Documentation discipline (required) | ~~stays — process~~ **overruled 2026-09-14** | ✅ **landed** — [SR-WORK-DOCS](../../records/0059_WORK-docs.md) |
| 12 | The three-file session discipline | ~~stays — process~~ **overruled 2026-09-14** | ✅ **landed** — [SR-WORK-SESSION](../../records/0060_WORK-session.md) |
| 13 | OPEN-WORK — the single live queue | 🔴 **needs a record** | ✅ **landed** — [SR-WORK-OPEN-QUEUE](../../records/0051_WORK-open-queue.md); the section is a generated view |
| 14 | Keep the docs in sync (required) | ~~stays — process~~ **overruled 2026-09-14** | ✅ **landed** — [SR-WORK-DOCS](../../records/0059_WORK-docs.md) |
| 15 | Session continuity — the running worklog | ~~stays — process~~ **overruled 2026-09-14** | ✅ **landed** — [SR-WORK-SESSION](../../records/0060_WORK-session.md) |
| 16 | Conformance runs — file every one | 🔴 link → SR-RS holds both halves | 🟡 open — [W-173](W-173-finish-the-claude-md-extraction.md) item 1 |
| 17 | Golden answer key — Claude never reads it | 🟠 needs a record (it is a technical prohibition with a hook behind it) | 🟡 open — **deliberately left in place 2026-09-14**: the paragraph is Cowork's only cover, so moving it needs Arpit's call |
| 18 | Layout | ✅ stays — a statement of fact | done |
| 19 | Error contract | 🟠 no new record — [SR-CLI](../../records/0101_cli-surface.md) is already credited with the boundary error contract | 🟡 open — [W-173](W-173-finish-the-claude-md-extraction.md) item 7 |
| 20 | Build & test | ✅ stays — commands | done |
| 21 | Merge wall | ~~stays — a statement of fact~~ **overruled 2026-09-14**: the fact and its consequence are one subject with the release path | ✅ **landed** — [SR-WORK-RELEASE](../../records/0063_WORK-release.md) |
| 22 | Hard-won build knowledge — the two binding items (BM25F weight-then-saturate; no wall-clock on the maintenance path) | 🟠 the two binding items go to the records that own the code; **the dated lessons are a LOG, not a record** — a record carries no history | 🟡 open — [W-173](W-173-finish-the-claude-md-extraction.md) item 5 |
| 23 | Blockers stop the session | ~~stays — process~~ **overruled 2026-09-14** | ✅ **landed** — [SR-WORK-BLOCKERS](../../records/0064_WORK-blockers.md) |
| 24 | Answer length · Say what you are doing | ~~stays — process~~ **overruled 2026-09-14** | ✅ **landed** — [SR-WORK-SESSION](../../records/0060_WORK-session.md) decisions 6–9 |
| 25 | Package identity | 🟠 needs a record | ✅ **landed 2026-09-14** — [SR-WORK-RELEASE](../../records/0063_WORK-release.md) |
| 26 | Archive is not evidence | 🟠 needs a record | ✅ **landed 2026-09-14** — [SR-WORK-ARCHIVE](../../records/0062_WORK-archive.md) |

⚠ **The *"stays — process"* verdict was overruled by Arpit on 2026-09-14**, and
nine rows above carry the correction. W-122's rule was that *"there is no record
for how an agent behaves in a session and inventing one would be the same
duplication in a new place"*; asked to shrink `CLAUDE.md`, **Arpit accepted eight
WORK records covering exactly those sections** — so the missing home was the
defect, not the duplication. `0051`–`0064` are that home. What is left here is
§2's ruling and the rows still marked open, which [W-173](W-173-finish-the-claude-md-extraction.md)
executes.

⚠ **`🟡 open` is not a defect and does not block anything.** Every one of those
sections is *technical and unhoused*, so L0 says it wants a record — and writing
nine new records in the change that moved the laws would have been a far bigger,
far less reviewable diff than the one Arpit ruled on. They are named here so the
next session can take one, and none of them is a second copy of anything: no
record states them today, which is why they stay legible where they are.

## 2 · 🔴 The ruling still owed

1. **How far does "never restates" reach into code comments?** SR-LAW-0 decision
   4's table names *a docstring* among the artifacts that must link rather than
   restate. Taken literally that reaches `config.py`'s `UrlSource` docstring, which
   explains every key and its default — and then most docstrings in `src/fux/`,
   because this repo's style is dense explanatory prose next to the code.
   **This session applied the narrow reading** — a comment may explain *mechanism
   and rationale*; the two artifacts whose whole content was *descriptions of
   keys* (`config.schema.json`, `fux setup`'s `fux.toml` comments) were removed —
   and did **not** touch a docstring anywhere. Stripping the codebase's comments
   is not a change an agent should make on its own reading of a law. ⚠ **Cost of
   the narrow reading, stated plainly:** `UrlSource`'s docstring and SR-CONFIG
   can disagree about a default while both look correct, which is exactly what
   decision 1 forbids. It is unguarded today.
