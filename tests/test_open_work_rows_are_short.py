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

   ⚠ **Not checkable:** whether 🧨 is true, and whether Arpit, rather than an
   agent, added a 🔺. Both are stated in rule 6 and rest on judgment.
7. **Every inbox row has a `↳ blocks:` sub-row, and it is complete** (Arpit,
   2026-09-11). It names every open item that waits on the decision, directly
   or through another item, as the rows' own *blocked on / after* text says --
   and nothing that is not an open item. `nothing else` is legal only when
   nothing waits.

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


def _section(title: str, stop: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    inside = False
    for lineno, line in enumerate(QUEUE.read_text(encoding="utf-8").splitlines(), 1):
        if line.rstrip() == title:
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
_WAITS_ON_ID = re.compile(r"\b(?:blocked on|after|waiting on|waits on)\s+(W-\d+)", re.IGNORECASE)


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
        for blocker in _WAITS_ON_ID.findall(text):
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
        for blocker in _WAITS_ON_ID.findall(text):
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
    assert blocks_subrows(), "no decision rows parsed out of *Blocked on Arpit*"
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
