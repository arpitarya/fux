"""Every record's frontmatter parses, and parses the same way for everyone.

Frontmatter broke twice on 2026-08-18, in two different ways, and neither was
visible from reading the file:

1. **An unquoted value containing `: `.** `fux`'s own parser is permissive by
   design (OKF §9) and read it happily; strict YAML — which is what GitHub,
   editors and every static-site generator use — refused the whole block. A
   record whose metadata is invisible to every tool but this one is broken even
   though nothing errored.
2. **A global rename walked into a title.** `ADR-INGEST (0001)` became
   `ADR-INGEST (ADR-INGEST)` when a citation sweep matched the
   number inside the title. Eight records, silently.

So the rules below are the ones that would have caught each. **No PyYAML** —
the runtime is stdlib-only and this uses `fux.frontmatter`'s own definition of
what must be quoted, which is the same rule its serializer applies.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fux import frontmatter as fm  # noqa: E402

RECORD_DIRS = (ROOT / "docs" / "adr", ROOT / "work" / "adr")
REQUIRED = ("type", "name", "title", "description", "status", "timestamp")
STATUSES = {"proposed", "accepted", "superseded"}

# Frozen. `archive/` is never edited — several records in there predate these
# rules and would fail; repairing them would break the property that makes an
# archived document worth anything.
_DELIM = "---"


def records() -> list[Path]:
    out: list[Path] = []
    for d in RECORD_DIRS:
        out += sorted(d.glob("[0-9][0-9][0-9][0-9]_*.md"))
    return out


def split(path: Path) -> tuple[list[str], str]:
    """Raw frontmatter lines and the body. Fails loudly on a malformed block."""
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    assert lines and lines[0].rstrip() == _DELIM, (
        f"{path.name}: no frontmatter block — a record starts with ---"
    )
    close = next((i for i in range(1, len(lines)) if lines[i].rstrip() == _DELIM), None)
    assert close is not None, f"{path.name}: frontmatter opened but never closed"
    return lines[1:close], "\n".join(lines[close + 1 :])


def meta_of(path: Path) -> dict:
    return fm.parse(path.read_text(encoding="utf-8")).meta


def body_field(body: str, label: str) -> str | None:
    m = re.search(r"^- \*\*%s:\*\*\s*(.+)$" % label, body, re.M)
    return m.group(1).strip() if m else None


# --------------------------------------------------------------------------


@pytest.mark.parametrize("path", records(), ids=lambda p: p.name)
def test_values_that_need_quoting_are_quoted(path: Path) -> None:
    """The break that made a record invisible to every tool but this one.

    `fux.frontmatter._NEEDS_QUOTE_RE` is the project's own definition of a
    value its serializer would have to quote. A value on disk that matches it
    and is *not* quoted is exactly the case strict YAML rejects.
    """
    offenders = []
    for lineno, line in enumerate(split(path)[0], start=2):
        if not line or line.startswith((" ", "-", "#")) or ":" not in line:
            continue
        value = line.split(":", 1)[1].strip()
        if not value or value[0] in "\"'":
            continue
        if fm._NEEDS_QUOTE_RE.search(value) or ": " in value:
            offenders.append(f"{path.name}:{lineno}: {line.strip()[:90]}")
    assert not offenders, (
        "these values must be quoted — strict YAML rejects them, so the record's "
        "metadata is invisible to GitHub, editors and every generator:\n  "
        + "\n  ".join(offenders)
    )


@pytest.mark.parametrize("path", records(), ids=lambda p: p.name)
def test_required_keys_present_and_sane(path: Path) -> None:
    meta = meta_of(path)
    missing = [k for k in REQUIRED if not str(meta.get(k, "")).strip()]
    assert not missing, f"{path.name}: frontmatter is missing {missing}"
    assert meta["type"] == "ADR", f"{path.name}: type must be ADR, got {meta['type']!r}"
    assert meta["status"] in STATUSES, (
        f"{path.name}: status must be one of {sorted(STATUSES)}, got {meta['status']!r}"
    )


@pytest.mark.parametrize("path", records(), ids=lambda p: p.name)
def test_frontmatter_agrees_with_the_body(path: Path) -> None:
    """A record states its name and status twice; the two must not drift."""
    meta = meta_of(path)
    body = split(path)[1]

    declared = body_field(body, "Name") or ""
    m = re.search(r"`(ADR-[A-Z0-9-]+)`", declared)
    assert m, f"{path.name}: body has no '- **Name:** `ADR-…`' line"
    assert m.group(1) == meta["name"], (
        f"{path.name}: frontmatter name is {meta['name']!r}, body says {m.group(1)!r}"
    )

    # The body is prose: it bolds the status and often qualifies it
    # ("**proposed** — awaiting Arpit's ratification"). Compare the first word.
    raw = (body_field(body, "Status") or "").lower()
    status = re.sub(r"[^a-z].*$", "", raw.strip().lstrip("*`_ "))
    assert status == meta["status"], (
        f"{path.name}: frontmatter status is {meta['status']!r}, body says {status!r} "
        f"(from {raw[:50]!r})"
    )


@pytest.mark.parametrize("path", records(), ids=lambda p: p.name)
def test_title_carries_the_name_and_the_number(path: Path) -> None:
    """The break a rename caused: `NAME (0001)` became `NAME (NAME)`.

    A title must open with the record's name and carry its file number — so a
    sweep that substitutes a number for a name is caught the moment it happens.
    """
    meta, number = meta_of(path), path.name[:4]
    title = str(meta["title"])
    assert title.startswith(meta["name"]), (
        f"{path.name}: title should open with {meta['name']!r} — got {title[:60]!r}"
    )
    assert f"({number})" in title, (
        f"{path.name}: title must carry its file number as ({number}) — got {title[:80]!r}. "
        "A name where the number belongs usually means a global rename walked into it."
    )
    assert title.count(meta["name"]) == 1, (
        f"{path.name}: {meta['name']!r} appears twice in the title — {title[:80]!r}"
    )
