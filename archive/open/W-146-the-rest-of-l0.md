---
type: OpenItem
id: W-146
title: "W-146 — the rest of L0: the unhoused CLAUDE.md sections, and the ruling Arpit still owes"
description: "CLOSED 2026-09-15. W-122 moved the ten laws into their records and made CLAUDE.md a generated view; this item carried what it deliberately left — records for the technical-but-unhoused CLAUDE.md sections, and the questions only Arpit could settle. All 26 inventory rows and all three of §2 are done: the docstring reach was ruled narrow with a gate, and row 17 became SR-WORK-GOLDEN with a second generated view. Carries W-122's delivered inventory verbatim."
status: closed
lane: agent
timestamp: 2026-09-12T00:00:00Z
---

# ✅ CLOSED 2026-09-15 — row 17 ruled, and the item is complete

**Arpit ruled row 17 on 2026-09-15: write the record, and keep the `CLAUDE.md`
paragraph as a generated view.** That is
[SR-WORK-GOLDEN](../../records/0066_WORK-golden.md), and it is the last thing
this item was waiting on.

**Why the ruling is not a compromise.** The two options row 17 offered were
*move it* (which deletes Cowork's only cover, since Cowork reads `CLAUDE.md` and
not `records/`) and *leave it* (which leaves two hand-maintained copies that can
disagree while both look correct). The third shape —
[SR-LAW-0](../../records/0002_LAW-0-authority.md) decision 5's generated,
test-bound view — satisfies both, and it is the same argument that produced
decision 5 for the law block in the first place. `scripts/gen-golden.py` renders
it; `tests/test_claude_md_golden.py` is the permission.

**And `work/golden/README.md` lost its copy in the same change** — it was the
*second* statement of the rule, and nothing had noticed because no record owned
either one.

| §1 row | outcome |
|---|---|
| 17 · Golden answer key | ✅ **landed 2026-09-15** — [SR-WORK-GOLDEN](../../records/0066_WORK-golden.md); `CLAUDE.md` §Golden answer key is now a generated, test-bound view and the README links rather than restates |

**All 26 inventory rows are now closed, and §2's three items with them.** Nothing
in this item is open.

---

✅ **§2's agent work is DONE 2026-09-15.** Items 1 and 2 landed;
[SR-LAW-0](../../records/0002_LAW-0-authority.md) decision 4b records what they
found. **Row 17 was the last open thing and it closed the same day** — see the
block above.

| §2 item | outcome |
|---|---|
| 1 · `tests/test_docstring_defaults.py` | ✅ built. 🔴 **It went GREEN on its first run** — `UrlSource`'s docstring, SR-CONFIG decision 5 and `config.py`'s loader all agree (`.fux/fetchers/http.py`, `"hashed"`). The exposure is real in principle and **there was no drift** |
| 2 · key-and-default docstrings → links | ✅ **nothing to do.** No docstring under `src/fux/` is only a key-and-default table; the narrow reading had already been applied on 2026-09-14 when `config.schema.json` and `fux setup`'s comments were removed |
| 3 · row 17 in the same change | ✅ **done 2026-09-15, one change later.** It could not land with items 1 and 2 — row 17 needed Arpit's call — and the contradiction between §2 item 3 and row 17 resolved the way the more specific statement said it would |

🔴 **Two things about the gate itself, kept because they generalise:**

1. **It asserts against the CODE, not the record** — a deliberate narrowing of
   decision 4a's wording. A record declares a key's *existence*; it names a
   value only in prose, which decision 6 says cannot make a key real, so a
   parser reading values out of prose would be guessing. The name is bound to
   the record by `test_sr_config_keys.py` and the value to the loader by this
   gate; a docstring can drift from neither.
2. ⚠ **The first version produced twelve false positives, then eight** — it
   matched every inline `` `key = value` `` example, and every TOML key whose
   name collided with a Python parameter. **A gate that fires wrongly is worse
   than one that does not fire.** It now requires a default claim to say it is
   one, and carries a self-test proving it can still fail. **The cost is that
   the gate is thin**: one claim in the whole tree is checkable today. It is a
   tripwire, not a survey.

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
| 1 | Law zero — the SRs are always up to date | needs no new record: `SR-LAW-0` holds the authority half and [SR-WORK-OWNERSHIP](../../records/0054_WORK-ownership.md) the freshness gate. **The section is a second copy of both** | ✅ **landed 2026-09-14** — W-173 item 2 — [SR-LAW-0](../../records/0002_LAW-0-authority.md) decision 1a (the three obligations) + [SR-WORK-OWNERSHIP](../../records/0054_WORK-ownership.md) 2a (the gate) |
| 2 | Triage first — a human-blocked queue | ~~stays — agent process~~ **overruled by W-173**: it restated queue rules 41 and 42 | ✅ **landed 2026-09-14** — [SR-WORK-OPEN-QUEUE](../../records/0051_WORK-open-queue.md) 32–34, 39–45, **plus the two-strikes rule, which was in `CLAUDE.md` and NOWHERE ELSE** → [SR-WORK-SESSION](../../records/0060_WORK-session.md) 13 |
| 3 | Where the state of play lives | ✅ stays — a pointer table | done |
| 4 | What we are building (scope) | ✅ stays — statements of fact + links | done |
| 5 | **Non-negotiable constraints** | 🔴 **moved** → the ten `SR-LAW-n`; section is now a generated, test-bound block | ✅ **landed** |
| 6 | Litmus (the 10 000-document design point) | 🟠 needs a record | ✅ **landed 2026-09-14** — [SR-WORK-SCALE](../../records/0057_WORK-scale.md) |
| 7 | How work happens here (the lifecycle) | ~~stays — process~~ **overruled 2026-09-14** | ✅ **landed** — [SR-WORK-LIFECYCLE](../../records/0058_WORK-lifecycle.md) |
| 8 | A pre-registered threshold may never move | 🔴 link → [SR-RS](../../records/0133_predictions.md) already holds it | ✅ **landed 2026-09-14** — W-173 item 1 — [SR-RS](../../records/0133_predictions.md) decision 10b |
| 9 | Follow the OKF pattern | 🟠 a record, not a link — the bundle is not the docs table | ✅ **landed 2026-09-14** — [SR-WORK-OKF](../../records/0061_WORK-okf.md) |
| 10 | Documentation style (required) | ~~stays — process~~ **overruled 2026-09-14** | ✅ **landed** — [SR-WORK-DOCS](../../records/0059_WORK-docs.md) |
| 11 | Documentation discipline (required) | ~~stays — process~~ **overruled 2026-09-14** | ✅ **landed** — [SR-WORK-DOCS](../../records/0059_WORK-docs.md) |
| 12 | The three-file session discipline | ~~stays — process~~ **overruled 2026-09-14** | ✅ **landed** — [SR-WORK-SESSION](../../records/0060_WORK-session.md) |
| 13 | OPEN-WORK — the single live queue | 🔴 **needs a record** | ✅ **landed** — [SR-WORK-OPEN-QUEUE](../../records/0051_WORK-open-queue.md); the section is a generated view |
| 14 | Keep the docs in sync (required) | ~~stays — process~~ **overruled 2026-09-14** | ✅ **landed** — [SR-WORK-DOCS](../../records/0059_WORK-docs.md) |
| 15 | Session continuity — the running worklog | ~~stays — process~~ **overruled 2026-09-14** | ✅ **landed** — [SR-WORK-SESSION](../../records/0060_WORK-session.md) |
| 16 | Conformance runs — file every one | 🔴 link → SR-RS holds both halves | ✅ **landed 2026-09-14** — W-173 item 1 — SR-RS decision 10a. 🔴 **And SR-RS had been DEFERRING to `CLAUDE.md`** for the obligation it only explains; inverted in the same change |
| 17 | Golden answer key — Claude never reads it | 🟠 needs a record (it is a technical prohibition with a hook behind it) | ✅ **landed 2026-09-15** — [SR-WORK-GOLDEN](../../records/0066_WORK-golden.md). Arpit ruled the third shape: the record states it, `CLAUDE.md` carries a **generated, test-bound** view, and Cowork keeps its cover |
| 18 | Layout | ~~stays — a statement of fact~~ **overruled by W-173**: 40 lines of tree in the file every session reads first | ✅ **landed 2026-09-14** — [`docs/index.md`](../../docs/index.md) §The tree; a twelve-line tree stays |
| 19 | Error contract | 🟠 no new record — [SR-CLI](../../records/0101_cli-surface.md) is already credited with the boundary error contract | ✅ **landed 2026-09-14** — W-173 item 7 — SR-CLI decisions 4 and 5. 🔴 **The two COPIES CONTRADICTED each other about exit `2`** and the record was right |
| 20 | Build & test | ~~stays — commands~~ **the commands stay; the GOTCHAS did not** | ✅ **landed 2026-09-14** — the `node --test` glob trap and the `pii.toml` requirement are surface quirks → [`work/MACHINE.md`](../MACHINE.md) |
| 21 | Merge wall | ~~stays — a statement of fact~~ **overruled 2026-09-14**: the fact and its consequence are one subject with the release path | ✅ **landed** — [SR-WORK-RELEASE](../../records/0063_WORK-release.md) |
| 22 | Hard-won build knowledge — the two binding items (BM25F weight-then-saturate; no wall-clock on the maintenance path) | 🟠 the two binding items go to the records that own the code; **the dated lessons are a LOG, not a record** — a record carries no history | ✅ **landed 2026-09-14** — W-173 item 5 — [`work/LESSONS.md`](../LESSONS.md); the two binding items point at [SR-RANKING](../../records/0111_ranking.md) and [SR-LAW-3](../../records/0005_LAW-3-deterministic.md) |
| 23 | Blockers stop the session | ~~stays — process~~ **overruled 2026-09-14** | ✅ **landed** — [SR-WORK-BLOCKERS](../../records/0064_WORK-blockers.md) |
| 24 | Answer length · Say what you are doing | ~~stays — process~~ **overruled 2026-09-14** | ✅ **landed** — [SR-WORK-SESSION](../../records/0060_WORK-session.md) decisions 6–9 |
| 25 | Package identity | 🟠 needs a record | ✅ **landed 2026-09-14** — [SR-WORK-RELEASE](../../records/0063_WORK-release.md) |
| 26 | Archive is not evidence | 🟠 needs a record | ✅ **landed 2026-09-14** — [SR-WORK-ARCHIVE](../../records/0062_WORK-archive.md) |

⚠ **The *"stays — process"* verdict was overruled by Arpit on 2026-09-14**, and
nine rows above carry the correction. W-122's rule was that *"there is no record
for how an agent behaves in a session and inventing one would be the same
duplication in a new place"*; asked to shrink `CLAUDE.md`, **Arpit accepted eight
WORK records covering exactly those sections** — so the missing home was the
defect, not the duplication. `0051`–`0064` are that home. **W-173 shipped on 2026-09-14** and executed every row above
([IMPLEMENTATION](../IMPLEMENTATION.md) §2026-09-14 W-173). **What is left in
this item is §2's one ruling and row 17**, which was deliberately not moved.

⚠ **`🟡 open` is not a defect and does not block anything.** Every one of those
sections is *technical and unhoused*, so L0 says it wants a record — and writing
nine new records in the change that moved the laws would have been a far bigger,
far less reviewable diff than the one Arpit ruled on. They are named here so the
next session can take one, and none of them is a second copy of anything: no
record states them today, which is why they stay legible where they are.

## 2 · ✅ RULED 2026-09-14 (Arpit) — option (a), the narrow reading, with a gate

**The ruling:** a docstring may explain *mechanism and rationale*; a docstring's
table of keys and their defaults is a restatement and becomes a link; and the
exposure is closed by a test, not by judgment. Written into
[SR-LAW-0](../../records/0002_LAW-0-authority.md) decision 4 (a new *explains*
row) and decision 4a (the docstring gate).

**Agent work now, in order:**

1. `tests/test_docstring_defaults.py` — extract every `key = value` /
   `default: value` literal from docstrings under `src/fux/`, resolve the owning
   record via the ownership table, assert the literal equals the record's
   declared value. Red first on `UrlSource` if it disagrees with SR-CONFIG;
   fix the docstring, never the record.
2. Turn any docstring that is *only* a key-and-default table into a one-line
   link to its record. Leave every mechanism/rationale docstring alone.
3. Row 17 of §3 lands in the same change. Then this item closes.

The question as it stood before the ruling, kept because the argument still
binds:

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
