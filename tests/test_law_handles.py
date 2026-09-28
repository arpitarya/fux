"""Every law handle a live file cites exists in SR-LAWS's current table.

**Why this exists.** On 2026-09-28 the laws were renumbered densely (Arpit,
W-234): L13 became L1, L1–L4 became L2–L5, L8 became L9, and a new L8 (Node)
went in after L7. [SR-LAWS](../records/0001_LAWS.md) decision 2 says this
reverses the old *"a handle is never reused"* rule, and decision 2a is the
mapping table a reader of an older document uses.

The renumber repointed every live citation in one change. **This test catches
the ones written afterwards from habit or from an old copy**: a live `L13`, or a
live `L14`, cites a law that does not exist. A citation of a retired law is
written `ex-L5` / `ex-L9` and is not a handle.

⚠ **What it cannot catch, stated rather than discovered:** a live `L3` written
by someone who meant the OLD L3 (*deterministic*, now L4). Every number from L0
to L12 is valid, so a wrong-but-existing handle passes. Nothing mechanical can
tell which law a sentence meant; SR-LAWS decision 2 names that exposure.

**What is not a live file**, and why each is skipped: the same frozen-by-law set
[`tests/test_doc_links.py`](test_doc_links.py) exempts. `archive/`, the
append-only `work/WORKLOG.md`, filed `work/regression/` runs, benchmark reports,
pre-registrations and `CHANGELOG.md` keep the handles of their own date and are
read through decision 2a. `work/golden/` is never enumerated at all (L11). Files
come from `git ls-files`, never a directory walk.

**What is not a handle:** a line locator (`docs/mesh.md:L10-L13`, `#L40`, a
bare `"L40-L52"` span), SVG path data (`L3,5`), and an identifier that merely
contains the letters (`L12_VALUES`, `html5`).

**Two places must name an old handle, and are skipped by construction:** the
rows of SR-LAWS decision 2a's mapping table (each opens `| L<n> |`, a shape no
other row in that record has), and this file's own docstring.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SR_LAWS = ROOT / "records" / "0001_LAWS.md"

#: Frozen-by-law paths, by prefix. Mirrors test_doc_links.py's exemptions and
#: adds the generated trees: `.fux/index/` is derived from the corpus and
#: `.fux/node/` is the built bundle.
_FROZEN_PREFIXES = (
    "archive/",
    "work/golden/",
    "work/regression/",
    "work/benchmark/reports/",
    ".fux/index/",
    ".fux/node/",
)
_FROZEN_FILES = frozenset({"work/WORKLOG.md", "CHANGELOG.md", "tools/archived-signal-eval/queries.jsonl"})
_TEXT_SUFFIXES = frozenset({".md", ".py", ".mjs", ".js", ".sh", ".toml", ".txt", ".html", ".svg", ".yml", ".yaml", ".json", ".mmd"})

_LOCATOR = re.compile(r"[#:]L\d+(?:[-–]L\d+)?")
#: A line span with no prefix — `"lines": "L40-L52"`. A LAW range is never
#: written with a number above the table's last handle, so a span naming one
#: is a locator.
_SPAN = re.compile(r"\bL(\d+)-L(\d+)\b")
_EX = re.compile(r"\bex-L\d+\b")
_HANDLE = re.compile(r"(?<![\w#:/])L(\d+)(?![\w])(?![,.]\d)")


def _current_handles() -> set[str]:
    text = SR_LAWS.read_text(encoding="utf-8")
    table = text.split("| # | law", 1)[1].split("\n\n", 1)[0]
    return {f"L{n}" for n in re.findall(r"^\| \*\*L(\d+)\*\* \|", table, re.M)}


def _live_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT, capture_output=True, check=True,
    ).stdout.decode("utf-8").split("\0")
    live = []
    for rel in out:
        if not rel or rel.startswith(_FROZEN_PREFIXES) or rel in _FROZEN_FILES:
            continue
        if "PRE-REGISTRATION" in rel or Path(rel).suffix not in _TEXT_SUFFIXES:
            continue
        live.append(rel)
    return sorted(live)


def test_the_current_table_is_dense():
    """Decision 2: L0–L12, no gaps, since 2026-09-28."""
    handles = _current_handles()
    assert handles == {f"L{n}" for n in range(13)}, sorted(handles, key=lambda h: int(h[1:]))


def test_every_live_law_handle_exists():
    valid = _current_handles()
    stale = []
    top = max(int(h[1:]) for h in valid)
    for rel in _live_files():
        if rel == "tests/test_law_handles.py":
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(text.split("\n"), 1):
            if rel == "records/0001_LAWS.md" and re.match(r"\| L\d+ \|", line):
                continue  # decision 2a's mapping table names the OLD handles
            scrubbed = _EX.sub("", _LOCATOR.sub("", line))
            scrubbed = _SPAN.sub(
                lambda m: "" if max(int(m.group(1)), int(m.group(2))) > top else m.group(0), scrubbed
            )
            for m in _HANDLE.finditer(scrubbed):
                if f"L{m.group(1)}" not in valid:
                    stale.append(f"{rel}:{lineno}: L{m.group(1)}")
    assert not stale, (
        "live files cite law handles SR-LAWS does not define — the laws were "
        "renumbered on 2026-09-28; map an old handle through SR-LAWS decision 2a, "
        "or write a retired law as ex-L5 / ex-L9:\n" + "\n".join(stale[:50])
    )
