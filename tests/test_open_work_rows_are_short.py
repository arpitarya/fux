"""OPEN-WORK is an index. A row is one or two lines, and the detail goes in the item's file.

**Arpit, 2026-09-11:** *"open work document should just be one liner or two
liner. That's it. Nothing else. All the details should go into work document.
Always."*

**Why this is a test and not just a rule.** `work/open/README.md` already said
*"one line per item, no detail"*. The queue still grew to 370 lines, with rows
running forty lines long, tables inside bullets and rulings copied in. Arpit had
to ask twice on the same day, once for the inbox and once for the open items.
CLAUDE.md's two-strikes rule makes the second time the trigger for a gate.

## What is checked

1. **An item is at most two source lines**, and a bullet never runs past
   `MAX_CHARS`. Two 2 000-character lines are not a one-liner.
2. **An item has no body**: no nested bullet, no table, no indented paragraph.
3. **Every item links its detail file**, `open/W-nn-slug.md`, the file exists,
   and the `W-nn` in the row matches the file.
4. **An inbox row is also short.** A table row is always one source line, so
   only the length is checked.
5. **Every row opens with exactly one ball, then optional 🧨, then optional
   🔺, in that order** (OPEN-WORK rule 6, Arpit 2026-09-11). Balls: 🔴 blocked on
   Arpit, directly or through another item · 🟣 gated on a named date, directly or
   through another item (Arpit, 2026-09-13) · 🟡 waiting on another item · 🟢 no
   blockers. An inbox decision row is always 🔴 -- a date gate is not a decision
   owed, so a 🟣 item is never in the inbox.
6. **The balls agree with the chain.** An item is 🔴 exactly when it is an inbox
   decision or waits -- through any chain of *blocked on / after* rows -- on one.
   An item is 🟣 when its own row names the date it waits for, or it waits through
   such a chain on one that does; **red wins, then purple**. A 🟡 row names what
   it waits on and reaches neither a decision nor a date. A 🟢 row waits on
   nothing. A 🔺 row does not wait on a row without 🔺.
6a. **A 🟡 row names the ITEM, or says there is none** (rule 23a, Arpit
   2026-09-15). `waiting on W-nn` with the bare id when the blocker is in the
   queue; the words `not a queue item` when it is not. A noun phrase alone --
   *"waiting on a subscriber"* -- satisfied rule 6 while hiding which of two
   opposite states the row was in.
6b. **A 🟡 row shows its blocker right after its id** (rule 23d, Arpit
   2026-10-25): `🟡 **W-nn** waits on **W-mm**`, or `**<project> W-mm**` for
   another project's item, and a local blocker is an open row. The check is
   `scripts/check-open-work-inbox.py`'s, imported -- the PostToolUse hook and
   this suite run one implementation.

   ⚠ **Not checkable:** whether 🧨 is true, and whether Arpit, rather than an
   agent, added a 🔺. Both are stated in rule 6 and rest on judgment.
7. **Every inbox row has a `↳ blocks:` sub-row, and it is complete** (Arpit,
   2026-09-11). It names every open item that waits on the decision, directly
   or through another item, as the rows' own *blocked on / after* text says --
   and nothing that is not an open item. `nothing else` is legal only when
   nothing waits.

8. **Every item file opens with its meeting view** (SR-WORK-OPEN-QUEUE rule 59,
   Arpit 2026-10-18). The first thing under the `# W-nn` title is
   `## At a glance`, and the first thing under that is a Markdown table (header,
   separator, at least one row), a closed `mermaid` or `text` fence, or an image.
   Whether the view is plain English and current (rules 60-61) is judgement.
9. **Every item file says who filed it and who last updated it** (SR-WORK-OPEN-QUEUE
   rules 62-64, Arpit 2026-10-18). Its frontmatter carries `filed_by`, `updated` and
   `updated_by`, each `_by` shaped `"<person> (<surface>, <model>)"` (the model may be
   absent), `updated` is not before `filed`, and every *Open items* row says
   `Filed by <person> (<surface>).` exactly as its file's `filed_by` has it.

## What is NOT checked

Whether the line is a *good* summary. A row can be short and still wrong about
the world. Rule 4 of OPEN-WORK stays a human obligation.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
QUEUE = WORK / "OPEN-WORK.md"

#: About two rendered lines. Long enough for id, lane, one sentence and a link.
MAX_CHARS = 280

_DETAIL = re.compile(r"\]\((open/(W-\d+)-[^)\s]+\.md)\)")
_SUBJECT = re.compile(r"^- [^A-Za-z0-9*]*\*\*(W-\d+)\b")


#: Rule 37b: a group heading ends in its count, `### build (10)`.
_COUNT = re.compile(r" \(\d+\)$")


def _section(title: str, stop: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    inside = False
    for lineno, line in enumerate(QUEUE.read_text(encoding="utf-8").splitlines(), 1):
        if _COUNT.sub("", line.rstrip()) == title:  # `### research (7)` is `### research` (rule 37b)
            inside = True
            continue
        if inside and line.startswith(stop):
            break
        if inside:
            out.append((lineno, line))
    return out


def open_items() -> list[tuple[int, list[str]]]:
    """(first line number, source lines) for every item under `## Open items`."""
    items: list[tuple[int, list[str]]] = []
    for lineno, line in _section("## Open items", "# The rules"):
        if not line.strip() or line.startswith("### ") or line.strip() == "---":
            continue
        if line.startswith("- "):
            items.append((lineno, [line]))
        elif items:
            items[-1][1].append(line)
        else:
            items.append((lineno, [line]))
    return items


def _inbox_table() -> list[tuple[int, str]]:
    """Every data row of the *Blocked on Arpit* table, decision rows and sub-rows alike."""
    return [
        (n, l) for n, l in _section("## Blocked on Arpit", "---")
        if l.startswith("|") and not set(l.strip()) <= set("|- :") and "| filed |" not in l
    ]


def _first_cell(line: str) -> str:
    return line.split("|")[1].strip()


def inbox_rows() -> list[tuple[int, str]]:
    """The decision rows -- everything but the `↳ blocks:` sub-rows."""
    return [(n, l) for n, l in _inbox_table() if not _first_cell(l).startswith("↳")]


def test_the_open_items_parse_at_all() -> None:
    assert open_items(), (
        "no items parsed under `## Open items` in work/OPEN-WORK.md. Either the queue is "
        "empty, and this test should say so, or the heading moved and every check below "
        "passes on nothing."
    )


def test_every_open_item_is_one_or_two_lines() -> None:
    bad = []
    for lineno, lines in open_items():
        text = " ".join(l.strip() for l in lines)
        if not lines[0].startswith("- "):
            bad.append(f"L{lineno}: text outside a bullet: {lines[0][:80]!r}")
        elif len(lines) > 2:
            bad.append(f"L{lineno}: {len(lines)} lines: {lines[0][:80]!r}")
        elif len(text) > MAX_CHARS:
            bad.append(f"L{lineno}: {len(text)} chars (max {MAX_CHARS}): {lines[0][:80]!r}")
        elif any(l.lstrip().startswith(("- ", "|", "* ")) for l in lines[1:]):
            bad.append(f"L{lineno}: nested bullet or table: {lines[0][:80]!r}")
    assert not bad, (
        "OPEN-WORK rule 10: one or two lines per item. Move the detail into the item's "
        "file under work/open/ and leave id, lane, what is open and the link.\n  "
        + "\n  ".join(bad)
    )


def test_every_open_item_links_its_own_detail_file() -> None:
    bad = []
    for lineno, lines in open_items():
        text = " ".join(lines)
        subject = _SUBJECT.match(lines[0])
        link = _DETAIL.search(text)
        if not subject:
            bad.append(f"L{lineno}: no **W-nn** subject. Give the item an id and a file first.")
        elif not link:
            bad.append(f"L{lineno}: {subject.group(1)} links no open/W-nn-*.md file.")
        elif link.group(2) != subject.group(1):
            bad.append(f"L{lineno}: row is {subject.group(1)} but links {link.group(1)}.")
        elif not (WORK / link.group(1)).is_file():
            bad.append(f"L{lineno}: {link.group(1)} does not exist.")
    assert not bad, "OPEN-WORK rule 10:\n  " + "\n  ".join(bad)


def test_every_inbox_row_is_short() -> None:
    bad = [
        f"L{n}: {len(l)} chars: {l[:80]!r}"
        for n, l in _inbox_table()
        if len(_first_cell(l)) > MAX_CHARS
    ]
    assert not bad, (
        "OPEN-WORK rule 10: a *Blocked on Arpit* row is one or two lines. The detail goes "
        "in the item's file.\n  " + "\n  ".join(bad)
    )


#: OPEN-WORK rule 6 (Arpit, 2026-09-11; 🟣 added 2026-09-13). A ball always; 🧨 and 🔺 optional.
BALLS = ("🔴", "🟣", "🟡", "🟢")

#: A 🟣 row that owns its gate names the date, ISO, in its own text.
_DATE = re.compile(r"\b20\d\d-\d\d-\d\d\b")
_LEAD = re.compile(r"^- (\S+)( 🧨)?( 🔺)? \*\*(W-\d+)\*\*")
_INBOX_LEAD = re.compile(r"^\|\s*(\S+)( 🧨)?( 🔺)? \*\*(W-\d+)\b")
_WAITS = re.compile(r"\b(blocked on|after|waiting on|waits on)\b", re.IGNORECASE)
#: `\**` so the rule-23d form, `waits on **W-299**`, is the same edge as the bare one.
#: `**fux W-298**` -- another project's item -- is never an edge: a word sits between.
_WAITS_ON_ID = re.compile(r"\b(?:blocked on|after|waiting on|waits on)\s+\**(W-\d+)", re.IGNORECASE)
#: Rule 23d: every local id in the blocker tag right after the row's own id, not just the first.
_TAG_IDS = re.compile(r"^- \S+(?: 🧨)?(?: 🔺)? \*\*W-\d+\*\* waits on ((?:\*\*[^*]+\*\*(?:, | and )?)+)")


def blockers_of(text: str) -> set[str]:
    """Every queue id a row waits on: rule 27's verb list, plus each local id in its rule-23d tag."""
    ids = set(_WAITS_ON_ID.findall(text))
    tag = _TAG_IDS.match(text)
    if tag:
        ids |= set(re.findall(r"\*\*(W-\d+)\*\*", tag.group(1)))
    return ids

#: Rule 23a (Arpit, 2026-09-15). A 🟡 row waiting on something that is NOT a
#: queue item says so **in these words**, so the two states are distinguishable
#: by reading rather than by guessing at a noun phrase. It is a fixed phrase for
#: the same reason rule 27's verb list is fixed: a blocker named any other way
#: names one no check can see.
_NOT_A_QUEUE_ITEM = re.compile(r"not a queue item", re.IGNORECASE)


def marked_items() -> dict[str, tuple[int, str, bool, str]]:
    """W-nn -> (line, ball, has 🔺, row text) for every open item with a parseable lead."""
    out: dict[str, tuple[int, str, bool, str]] = {}
    for lineno, lines in open_items():
        m = _LEAD.match(lines[0])
        if m:
            out[m.group(4)] = (lineno, m.group(1), bool(m.group(3)), " ".join(lines))
    return out


def inbox_ids() -> dict[str, str]:
    """W-nn -> the ball on its *Blocked on Arpit* row."""
    out: dict[str, str] = {}
    for _, line in inbox_rows():
        m = _INBOX_LEAD.match(line)
        if m:
            out[m.group(4)] = m.group(1)
    return out


def test_every_row_opens_with_exactly_one_ball() -> None:
    bad = []
    for lineno, lines in open_items():
        m = _LEAD.match(lines[0])
        if not m or m.group(1) not in BALLS:
            bad.append(f"L{lineno}: {lines[0][:80]!r}")
    for lineno, line in inbox_rows():
        m = _INBOX_LEAD.match(line)
        if not m or m.group(1) != "🔴":
            bad.append(f"L{lineno} (inbox, must be 🔴): {line[:80]!r}")
    assert not bad, (
        "OPEN-WORK rule 6: every row opens with one ball (🔴 blocked on Arpit · 🟣 gated on a "
        "named date · 🟡 waiting on another item · 🟢 no blockers), then optionally 🧨 (broken or "
        "getting worse), then optionally 🔺 (do first), then **W-nn**.\n  " + "\n  ".join(bad)
    )


def red_set() -> set[str]:
    """Every item blocked on Arpit: the inbox decisions and everything that waits on one."""
    out = set(inbox_ids())
    for decision in list(out):
        out |= waiting_on(decision)
    return out


def test_red_is_exactly_what_waits_on_a_decision() -> None:
    items, red = marked_items(), red_set()
    bad = [
        f"L{line}: {wid} is {ball} but waits, directly or through another item, on an Arpit decision -- it is 🔴."
        for wid, (line, ball, _, _) in items.items() if wid in red and ball != "🔴"
    ] + [
        f"L{line}: {wid} is 🔴 but is neither a *Blocked on Arpit* decision nor waits on one."
        for wid, (line, ball, _, _) in items.items() if ball == "🔴" and wid not in red
    ]
    assert not bad, "OPEN-WORK rule 6:\n  " + "\n  ".join(bad)


def date_gated() -> set[str]:
    """Every 🟣 item whose OWN row names the date it is waiting for."""
    return {
        wid for wid, (_, ball, _, text) in marked_items().items()
        if ball == "🟣" and _DATE.search(text)
    }


def purple_set() -> set[str]:
    """Every item gated on a date: the rows that name one, and everything behind them."""
    out = set(date_gated())
    for owner in list(out):
        out |= waiting_on(owner)
    return out


def test_every_purple_row_reaches_a_named_date() -> None:
    """🟣 says *the calendar is the only thing left*. Say which day, or which item knows."""
    reachable = purple_set()
    bad = [
        f"L{line}: {wid} is 🟣 but neither names a date (YYYY-MM-DD) nor waits on an item that does."
        for wid, (line, ball, _, _) in marked_items().items()
        if ball == "🟣" and wid not in reachable
    ]
    assert not bad, "OPEN-WORK rule 6:\n  " + "\n  ".join(bad)


def test_purple_is_exactly_what_is_date_gated_unless_red_wins() -> None:
    items, red, purple = marked_items(), red_set(), purple_set()
    bad = [
        f"L{line}: {wid} is {ball} but waits, directly or through another item, on a named date -- it is 🟣."
        for wid, (line, ball, _, _) in items.items()
        if wid in purple and wid not in red and ball != "🟣"
    ]
    assert not bad, "OPEN-WORK rule 6 (red wins, then purple):\n  " + "\n  ".join(bad)


def test_a_date_gated_item_is_not_in_the_inbox() -> None:
    """*Blocked on Arpit* is what he DECIDES. `wait until <date>` is a decision he made."""
    bad = sorted(purple_set() & set(inbox_ids()))
    assert not bad, (
        "OPEN-WORK rule 6: a date-gated item leaves the *Blocked on Arpit* table and lives as a "
        f"🟣 row under *Open items*: {bad}"
    )


def test_yellow_names_what_it_waits_on_and_green_waits_on_nothing() -> None:
    bad = []
    for wid, (line, ball, _, text) in marked_items().items():
        if ball == "🟡" and not _WAITS.search(text):
            bad.append(f"L{line}: {wid} is 🟡 but never says what it is waiting on.")
        if ball == "🟢" and (_WAITS_ON_ID.search(text) or re.search(r"\bblocked on\b", text, re.IGNORECASE)):
            bad.append(f"L{line}: {wid} is 🟢 but says it waits on something.")
    assert not bad, "OPEN-WORK rule 6:\n  " + "\n  ".join(bad)


def test_every_yellow_row_names_an_id_or_says_there_is_none() -> None:
    """Rule 23a. Saying *what* you wait on is not the same as saying *which item*.

    🔴 **The two states this separates are opposites, and the old rule let them
    look identical.** A row waiting on `W-145` clears itself the day W-145
    lands; a row waiting on *"a subscriber"* clears itself never, because
    nothing in the queue is tracking a subscriber. Both used to read as
    *"waiting on a thing"*, so a session triaging the queue could not tell which
    rows were live and which were parked.

    ⚠ **What this does NOT check is whether the claim is true** -- a row may say
    `not a queue item` about something that is one. That is rule 46's re-derive,
    a human obligation, and approximating it here (grepping the row's nouns
    against the item titles) is the `test_open_work_is_not_stale` gap in a new
    costume: it would pass on the wrong file and fail on prose it does not
    understand.
    """
    bad = []
    for wid, (line, ball, _, text) in marked_items().items():
        if ball != "🟡":
            continue
        if _WAITS_ON_ID.search(text) or _NOT_A_QUEUE_ITEM.search(text):
            continue
        bad.append(
            f"L{line}: {wid} is 🟡 but names no blocking item. Rule 23a: write "
            f"`waiting on W-nn` with the bare id, or say `not a queue item` "
            f"when nothing in the queue is what it waits for."
        )
    assert not bad, "OPEN-WORK rule 23a:\n  " + "\n  ".join(bad)


def test_a_do_first_item_is_not_waiting_on_a_normal_one() -> None:
    """🔺 on a waiting row is dead weight if what it waits on is in normal order.

    The fix is Arpit's -- 🔺 the blocker or drop the 🔺 -- so this fails loudly
    rather than letting an agent add a 🔺 it is not allowed to add.
    """
    items = marked_items()
    bad = []
    for wid, (line, _, top, text) in items.items():
        if not top:
            continue
        for blocker in blockers_of(text):
            if blocker in items and not items[blocker][2]:
                bad.append(f"L{line}: {wid} has 🔺 but waits on {blocker}, which has no 🔺.")
    assert not bad, (
        "OPEN-WORK rule 6: flag this to Arpit -- only he adds or removes 🔺.\n  " + "\n  ".join(bad)
    )


#: OPEN-WORK rule 10 (Arpit, 2026-09-11): what each decision holds up, named under it.
_SUB = re.compile(r"^↳ \*\*blocks:\*\*\s*(.+)$")


def blocks_subrows() -> dict[str, tuple[int, str | None]]:
    """Decision W-nn -> (line of its decision row, text of the sub-row below it or None)."""
    table = _inbox_table()
    out: dict[str, tuple[int, str | None]] = {}
    for i, (lineno, line) in enumerate(table):
        m = _INBOX_LEAD.match(line)
        if not m:
            continue
        nxt = _first_cell(table[i + 1][1]) if i + 1 < len(table) else ""
        sub = _SUB.match(nxt)
        # group(4) is the id: groups 2 and 3 are the optional 🧨 and 🔺. Keying this on
        # group(3) -- None on almost every row -- collapsed the whole table into one
        # entry, so the two checks below ran against the last row alone. Fixed 2026-09-13.
        out[m.group(4)] = (lineno, sub.group(1) if sub else None)
    return out


def waiting_on(decision: str) -> set[str]:
    """Every open item that waits on `decision`, directly or through a chain of rows."""
    edges: dict[str, set[str]] = {}
    for wid, (_, _, _, text) in marked_items().items():
        for blocker in blockers_of(text):
            edges.setdefault(blocker, set()).add(wid)
    seen: set[str] = set()
    todo = [decision]
    while todo:
        for w in edges.get(todo.pop(), ()):
            if w not in seen and w != decision:
                seen.add(w)
                todo.append(w)
    return seen


def test_every_inbox_row_is_followed_by_its_blocks_subrow() -> None:
    bad = [
        f"L{line}: {wid} has no `| ↳ **blocks:** ... | | |` row directly beneath it."
        for wid, (line, sub) in blocks_subrows().items() if sub is None
    ]
    if not blocks_subrows():
        from test_open_work_is_not_stale import _inbox_declared_empty

        assert _inbox_declared_empty(), (
            "no decision rows parsed out of *Blocked on Arpit*, and the file does not "
            "declare the inbox empty (`*Empty since YYYY-MM-DD` under the table)."
        )
    assert not bad, (
        "OPEN-WORK rule 10: under every *Blocked on Arpit* row, name the work that decision "
        "holds up -- or `nothing else in the queue`.\n  " + "\n  ".join(bad)
    )


def test_a_blocks_subrow_names_exactly_the_waiting_items() -> None:
    open_ids = set(marked_items())
    bad = []
    for wid, (line, sub) in blocks_subrows().items():
        if sub is None:
            continue
        named = set(re.findall(r"\bW-\d+\b", sub)) - {wid}
        owed = waiting_on(wid)
        if owed - named:
            bad.append(f"L{line}: {wid}'s sub-row is missing {sorted(owed - named)}, which wait on it.")
        if named - open_ids:
            bad.append(f"L{line}: {wid}'s sub-row names {sorted(named - open_ids)}, not open items.")
        if not named and not owed and "nothing else" not in sub:
            bad.append(f"L{line}: {wid}'s sub-row names nothing; write `nothing else in the queue`.")
    assert not bad, "OPEN-WORK rule 10:\n  " + "\n  ".join(bad)


# --- B-047: three more rules of SR-WORK-OPEN-QUEUE, promoted from judgement ----
# W-246. The remaining conduct rules (1, 5, 11, 12, 29, 30, 32, 33, 35, 36, 48, 50,
# 53) are judgement, permanently: no parser can tell whether a row's priority was
# honest or whether a session reconciled before it reported.

OPEN_DIR = WORK / "open"
GROUPS = ("### fux build", "### testing", "### adr update", "### research")
#: Rule 47's own words: what is or is not committed, staged, pushed or unpushed.
#: The *verb* ("commit its three blocks") and the CI noun ("a docs-only push") are
#: instructions and events, not a statement of repository state, and are legal.
_GIT_STATE = re.compile(
    r"\b(?:un)?(?:committed|staged|pushed)\b|\bunpushed\b|\bgit status\b", re.IGNORECASE
)


def test_rule_37_the_open_items_are_grouped_by_what_closing_them_takes() -> None:
    """SR-WORK-OPEN-QUEUE rule 37: the four group headers are present under `## Open items`."""
    headers = {_COUNT.sub("", l.strip()) for _, l in _section("## Open items", "# The rules") if l.startswith("### ")}
    missing = [g for g in GROUPS if g not in headers]
    assert not missing, f"rule 37: group header(s) missing from OPEN-WORK: {missing}"


def test_rule_37a_research_runs_in_cowork_never_claude_code() -> None:
    """SR-WORK-OPEN-QUEUE rule 37a (Arpit, 2026-10-05): every row under `### research`
    is lane `cowork`, and its detail file's Model line names Cowork."""
    rows = [l for _, l in _section("### research", "---") if l.startswith("- ")]
    bad = []
    for row in rows:
        if "· `cowork` —" not in row:
            bad.append(f"lane is not `cowork`: {row[:80]!r}")
        m = re.search(r"\(open/(W-\d+-[^)]+\.md)\)", row)
        if not m:
            continue
        text = (OPEN_DIR / m.group(1)).read_text(encoding="utf-8")
        model = re.search(r"\*\*Model:\*\*[^\n]*", text)
        if not model or "Cowork" not in model.group(0):
            bad.append(f"{m.group(1)}: its **Model:** line does not name Cowork")
    assert not bad, "rule 37a: research is Cowork-only:\n  " + "\n  ".join(bad)


def test_rule_38_every_item_file_names_the_record_it_updates() -> None:
    """SR-WORK-OPEN-QUEUE rule 38: each `work/open/W-*.md` names an `SR-` record, or says
    *no SR affected* out loud."""
    bad = [
        p.name
        for p in sorted(OPEN_DIR.glob("W-*.md"))
        if not re.search(r"\bSR-[A-Z0-9]|no SR affected", p.read_text(encoding="utf-8"))
    ]
    assert not bad, f"rule 38: these items name no SR- record and do not say 'no SR affected': {bad}"


def test_rule_47_the_queue_says_nothing_about_git_state() -> None:
    """SR-WORK-OPEN-QUEUE rule 47 (Arpit's standing rule): nothing in the queue says what is or
    is not committed, staged, pushed or unpushed. If git state blocks work, name what the work needs."""
    bad = [
        f"L{n}: {l.strip()[:90]}"
        for n, l in enumerate(QUEUE.read_text(encoding="utf-8").splitlines(), 1)
        if _GIT_STATE.search(l)
    ]
    assert not bad, "rule 47: git housekeeping in the queue:\n  " + "\n  ".join(bad)


#: SR-WORK-OPEN-QUEUE rule 59: the heading the meeting view sits under.
GLANCE = "## At a glance"
_TABLE_ROW = re.compile(r"^\|.*\|\s*$")
_TABLE_SEP = re.compile(r"^\|(\s*:?-{3,}:?\s*\|)+\s*$")
_FENCE_OPEN = re.compile(r"^```(mermaid|text)\s*$")
_IMAGE = re.compile(r"^!\[[^\]]*\]\([^)\s]+\)\s*$")


def meeting_view_defect(text: str) -> str | None:
    """Return why a `work/open/W-*.md` breaks rule 59, or None when it does not."""
    lines = text.splitlines()
    i = 0
    if lines and lines[0].strip() == "---":
        try:
            i = next(n for n in range(1, len(lines)) if lines[n].strip() == "---") + 1
        except StopIteration:
            return "the frontmatter never closes"
    while i < len(lines) and not lines[i].startswith("# "):
        i += 1
    if i == len(lines):
        return "no `# W-nn` title"

    def next_nonblank(k: int) -> int:
        while k < len(lines) and not lines[k].strip():
            k += 1
        return k

    h = next_nonblank(i + 1)
    if h == len(lines) or lines[h].strip() != GLANCE:
        got = lines[h].strip()[:60] if h < len(lines) else "end of file"
        return f"the first thing under the title is {got!r}, not {GLANCE!r}"
    b = next_nonblank(h + 1)
    if b == len(lines):
        return f"{GLANCE!r} is empty"
    first = lines[b].rstrip()
    if _TABLE_ROW.match(first):
        if b + 2 >= len(lines) or not _TABLE_SEP.match(lines[b + 1].rstrip()):
            return "the table under it has no `|---|` separator under its header"
        if not _TABLE_ROW.match(lines[b + 2].rstrip()):
            return "the table under it has a header and no rows"
        return None
    if _FENCE_OPEN.match(first):
        if not any(l.strip() == "```" for l in lines[b + 1 :]):
            return "the diagram's fence never closes"
        return None
    if _IMAGE.match(first):
        return None
    return f"the first thing under {GLANCE!r} is {first[:60]!r}: not a table, a mermaid/text diagram or an image"


def test_rule_59_every_item_file_opens_with_a_meeting_view() -> None:
    """SR-WORK-OPEN-QUEUE rule 59 (Arpit, 2026-10-18): *"I want the first item to be a graph or
    a tabular kind of structure, which is easier to present in a meeting ... And we are going to
    enforce it."* Every `work/open/W-*.md` opens, right under its title, with `## At a glance`
    and a table or diagram under that."""
    bad = [
        f"{p.name}: {why}"
        for p in sorted(OPEN_DIR.glob("W-*.md"))
        if (why := meeting_view_defect(p.read_text(encoding="utf-8")))
    ]
    assert not bad, "rule 59: item files without a meeting view first:\n  " + "\n  ".join(bad)


def test_rule_59_the_checker_rejects_what_it_should() -> None:
    """The checker itself, on fixed inputs — so a regex that matches nothing cannot pass vacuously."""
    head = "---\nname: W-1\n---\n\n# W-1 — x\n\n"
    good_table = head + GLANCE + "\n\n| step | what we do | what it gives us | state |\n|---|---|---|---|\n| 1 | a | b | ⏳ |\n"
    good_fence = head + GLANCE + "\n\n```mermaid\nflowchart LR\n  a --> b\n```\n"
    good_image = head + GLANCE + "\n\n![plan](../plan.svg)\n"
    assert meeting_view_defect(good_table) is None
    assert meeting_view_defect(good_fence) is None
    assert meeting_view_defect(good_image) is None
    assert meeting_view_defect(head + "**Arpit:** *\"x\"*\n\n" + GLANCE + "\n\n| a |\n|---|\n| 1 |\n")
    assert meeting_view_defect(head + GLANCE + "\n\nSome prose first.\n\n| a |\n|---|\n| 1 |\n")
    assert meeting_view_defect(head + GLANCE + "\n\n| a | b |\n| 1 | 2 |\n")
    assert meeting_view_defect(head + GLANCE + "\n\n| a | b |\n|---|---|\n")
    assert meeting_view_defect(head + GLANCE + "\n\n```python\nx = 1\n```\n")
    assert meeting_view_defect(head + GLANCE + "\n\n```text\nnever closed\n")
    assert meeting_view_defect(head + GLANCE + "\n")


#: SR-WORK-OPEN-QUEUE rule 62: `"<person> (<surface>, <model>)"`, the model optional.
_BY = re.compile(r'^"(?P<who>[^"()]+?) \((?P<surface>[^",()]+?)(?:, (?P<model>[^"()]+))?\)"$')
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def frontmatter(text: str) -> dict[str, str]:
    """The item file's frontmatter as raw `key: value` strings (no YAML needed for these keys)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def authorship_defects(fm: dict[str, str]) -> list[str]:
    """Why a frontmatter breaks rules 62-63, or an empty list."""
    bad = []
    for key in ("filed_by", "updated_by"):
        if key not in fm:
            bad.append(f"no `{key}`")
        elif not _BY.match(fm[key]):
            bad.append(f'`{key}: {fm[key]}` is not "<person> (<surface>, <model>)"')
    for key in ("filed", "updated"):
        if key not in fm:
            bad.append(f"no `{key}`")
        elif not _ISO.match(fm[key]):
            bad.append(f"`{key}: {fm[key]}` is not YYYY-MM-DD")
    if not bad and fm["updated"] < fm["filed"]:
        bad.append(f"`updated: {fm['updated']}` is before `filed: {fm['filed']}`")
    return bad


def test_rule_62_every_item_file_names_who_filed_and_who_updated_it() -> None:
    """SR-WORK-OPEN-QUEUE rules 62-63 (Arpit, 2026-10-18): *"In work items, in front matter, always
    have the name who filed the work item, who updated the work item."*"""
    bad = [
        f"{p.name}: {why}"
        for p in sorted(OPEN_DIR.glob("W-*.md"))
        for why in authorship_defects(frontmatter(p.read_text(encoding="utf-8")))
    ]
    assert not bad, "rules 62-63: item files missing who filed / updated them:\n  " + "\n  ".join(bad)


def test_rule_64_every_open_item_row_says_who_filed_it() -> None:
    """SR-WORK-OPEN-QUEUE rule 64 (Arpit, 2026-10-18): *"And in open items as well, do call out who
    filed the work item."* The row's `Filed by <person> (<surface>).` equals its file's `filed_by`."""
    bad = []
    for n, lines in open_items():
        row = " ".join(l.strip() for l in lines)
        m = _DETAIL.search(row)
        if not m:
            continue
        path = WORK / m.group(1)
        if not path.exists():
            continue
        by = _BY.match(frontmatter(path.read_text(encoding="utf-8")).get("filed_by", ""))
        if not by:
            continue  # rule 62's test names it
        want = f"Filed by {by['who']} ({by['surface']})."
        if want not in row:
            bad.append(f"L{n} {m.group(2)}: the row does not say {want!r}")
    assert not bad, "rule 64: open-items rows that do not say who filed them:\n  " + "\n  ".join(bad)


def test_rules_62_64_the_checker_rejects_what_it_should() -> None:
    """The authorship checker on fixed inputs, so a pattern that matches nothing cannot pass vacuously."""
    ok = {"filed": "2026-10-04", "updated": "2026-10-18",
          "filed_by": '"Arpit (Cowork, Fable 5.1)"', "updated_by": '"Arpit (Claude Code)"'}
    assert authorship_defects(ok) == []
    assert authorship_defects({**ok, "updated": "2026-10-01"})
    assert authorship_defects({k: v for k, v in ok.items() if k != "updated_by"})
    assert authorship_defects({**ok, "filed_by": '"Arpit"'})
    assert authorship_defects({**ok, "filed_by": "Arpit (Cowork, Opus 5.5)"})
    assert authorship_defects({**ok, "updated": "18 Oct"})


def _inbox_script():
    """`scripts/check-open-work-inbox.py`, imported: the hook and the suite share one check."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "check_open_work_inbox", ROOT / "scripts" / "check-open-work-inbox.py"
    )
    assert spec and spec.loader, "scripts/check-open-work-inbox.py is not importable"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_rule_23d_every_yellow_row_names_its_blocker_after_its_id() -> None:
    """SR-WORK-OPEN-QUEUE rule 23d (Arpit, 2026-10-25): *"The yellow balls in open work should
    always have the other work item mentioned based on which it is on hold. Always, always,
    always."* The blocker sits right after the id, as visible as the id: `waits on **W-mm**`."""
    bad = _inbox_script().check_yellow(QUEUE)
    assert not bad, "rule 23d:\n  " + "\n  ".join(bad)


def test_rule_23d_the_checker_rejects_what_it_should(tmp_path: Path) -> None:
    """The 🟡 checker on fixed inputs, so a pattern that matches nothing cannot pass vacuously."""
    check = _inbox_script().check_yellow

    def queue(*rows: str) -> Path:
        p = tmp_path / "OPEN-WORK.md"
        p.write_text("# q\n\n## Open items\n\n### fux build\n\n" + "\n".join(rows) + "\n\n---\n", encoding="utf-8")
        return p

    green = "- 🟢 **W-2** · `agent` — x. [detail](open/W-2-x.md)"
    assert check(queue(green, "- 🟡 **W-3** waits on **W-2** · `agent` — y")) == []
    assert check(queue("- 🟡 🧨 **W-3** waits on **fux W-299** · `agent` — y")) == []
    assert check(queue(green, "- 🟡 **W-3** waits on **W-2**, **codelaw W-34** · `agent` — y")) == []
    assert check(queue(green, "- 🟡 **W-3** · `agent` — waits on W-2"))  # in the prose, not after the id
    assert check(queue("- 🟡 **W-3** waits on **W-9** · `agent` — y"))  # W-9 is not an open row
    assert check(queue("- 🟡 **W-3** waits on **W-3** · `agent` — y"))  # itself
    assert check(queue("- 🟡 **W-3** waits on **a subscriber** · `agent` — y"))  # a noun, not a reference
    assert check(queue("- 🟡 **W-3** waits on **fux 5.1.0** · `agent` — y")) == []  # another project's version
    assert check(queue("- 🟡 **W-3** waits on **298** · `agent` — y"))  # neither an id nor `<project> <ref>`


def test_rule_37b_every_group_heading_carries_its_count() -> None:
    """SR-WORK-OPEN-QUEUE rule 37b (Arpit, 2026-10-26): `### build (10)` — the count of open
    items under each group heading, checked by the same script the PostToolUse hook runs."""
    bad = _inbox_script().check_counts(QUEUE)
    assert not bad, "rule 37b:\n  " + "\n  ".join(bad)


def test_rule_37b_the_checker_rejects_what_it_should(tmp_path: Path) -> None:
    check = _inbox_script().check_counts
    row = "- 🟢 **W-1** · `agent` — x. [detail](open/W-1-x.md)"
    def q(*lines: str) -> Path:
        p = tmp_path / "OPEN-WORK.md"
        p.write_text("## Open items\n\n" + "\n".join(lines) + "\n\n---\n", encoding="utf-8")
        return p
    assert check(q("### fux build (1)", "", row, "", "### testing (0)")) == []
    assert check(q("### fux build", "", row))          # no count
    assert check(q("### fux build (2)", "", row))      # wrong count
    assert check(q("### testing"))                     # an empty group still says (0)
