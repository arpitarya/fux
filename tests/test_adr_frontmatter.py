"""Every record's frontmatter parses, parses the same way for everyone, and is
the *only* place the record states its metadata.

Three failure classes are checked here, and each one has been paid for:

1. **An unquoted value containing `: `.** `fux`'s own parser is permissive by
   design (OKF §9) and read it happily; strict YAML — which is what GitHub,
   editors and every static-site generator use — refused the whole block. A
   record whose metadata is invisible to every tool but this one is broken even
   though nothing errored.
2. **A global rename walked into a title.** `ADR-INGEST (0001)` became
   `ADR-INGEST (ADR-INGEST)` when a citation sweep matched the number inside
   the title. Eight records, silently.
3. **Metadata stated twice.** Every record used to carry a `- **Name:** …`
   bullet block restating six frontmatter keys in prose, and the two drifted —
   which is why an earlier version of this file compared them to each other
   instead of forbidding the second copy. **The frontmatter is now the only
   statement**, and `test_the_body_does_not_restate_the_frontmatter` keeps the
   duplicate from coming back.

A fourth check has no history behind it and is here to stop one starting:
`test_no_amendment_sections` forbids the `Amended …` block. A record states
what is true now; a correction appended under a false sentence leaves the false
sentence in place, and an agent reading top-down acts on the first answer it
finds.

**No PyYAML** — the runtime is stdlib-only and this uses `fux.frontmatter`'s own
definition of what must be quoted, which is the same rule its serializer
applies.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fux import frontmatter as fm  # noqa: E402

RECORD_DIR = ROOT / "docs" / "adr"

# The ten keys, in order. `supersedes` and `ratifies` are optional and appear
# only where they are true, so they are not listed.
REQUIRED = (
    "type",
    "name",
    "title",
    "description",
    "status",
    "date",
    "feature",
    "owns",
    "laws",
    "timestamp",
)
LIST_KEYS = ("owns", "laws")
STATUSES = {"proposed", "accepted", "superseded"}

_DELIM = "---"
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# The bullet block that used to restate the frontmatter. Any of these labels
# appearing as a top-level bullet means the duplicate has come back.
_RESTATED = (
    "Name",
    "Status",
    "Date",
    "Feature",
    "Owns",
    "Owns (on acceptance)",
    "Owns (on build)",
    "Laws",
    "Supersedes",
    "Supersedes (on acceptance)",
    "Ratifies",
)
_RESTATED_RE = re.compile(
    r"^- \*\*(?:%s):\*\*" % "|".join(re.escape(label) for label in _RESTATED), re.M
)

# `## Amended …`, `> ## Amended …`, `> **Amended …`, `# Amended …` in a fence.
_AMENDED_RE = re.compile(r"^\s*>?\s*(?:#{1,6}\s*|\*\*)Amended\b", re.M | re.I)


def records() -> list[Path]:
    return sorted(RECORD_DIR.glob("[0-9][0-9][0-9][0-9]_*.md"))


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
        if value.startswith("[") and value.endswith("]"):
            continue  # an inline list round-trips; the quoting rule is per-scalar
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
    missing = [k for k in REQUIRED if k not in meta]
    assert not missing, f"{path.name}: frontmatter is missing {missing}"

    empty = [
        k
        for k in REQUIRED
        if k not in LIST_KEYS and not str(meta.get(k, "")).strip()
    ]
    assert not empty, f"{path.name}: these keys are present but empty: {empty}"

    assert meta["type"] == "ADR", f"{path.name}: type must be ADR, got {meta['type']!r}"
    assert meta["status"] in STATUSES, (
        f"{path.name}: status must be one of {sorted(STATUSES)}, got {meta['status']!r}"
    )
    assert _DATE_RE.match(str(meta["date"])), (
        f"{path.name}: date must be YYYY-MM-DD, got {meta['date']!r}"
    )
    for key in LIST_KEYS:
        assert isinstance(meta[key], list), (
            f"{path.name}: {key} must be an inline list — `{key}: []` when there "
            f"are none. Got {meta[key]!r}"
        )


@pytest.mark.parametrize("path", records(), ids=lambda p: p.name)
def test_keys_are_in_the_declared_order(path: Path) -> None:
    """A fixed order is what makes forty-two records diffable against each other."""
    meta = meta_of(path)
    seen = [k for k in meta if k in REQUIRED]
    assert seen == list(REQUIRED), (
        f"{path.name}: frontmatter keys are out of order.\n"
        f"  expected: {list(REQUIRED)}\n"
        f"  found:    {seen}"
    )


@pytest.mark.parametrize("path", records(), ids=lambda p: p.name)
def test_the_body_does_not_restate_the_frontmatter(path: Path) -> None:
    """The frontmatter is the metadata; the body opens at §1.

    Every record used to carry both, written by hand at different times, and
    they drifted. Two copies of a fact is one fact and one liability.
    """
    body = split(path)[1]
    hits = [m.group(0) for m in _RESTATED_RE.finditer(body)]
    assert not hits, (
        f"{path.name}: the body restates frontmatter — {', '.join(sorted(set(hits)))}.\n"
        "Put the value in the frontmatter block and delete the bullet; see TEMPLATE.md."
    )


@pytest.mark.parametrize("path", records(), ids=lambda p: p.name)
def test_no_amendment_sections(path: Path) -> None:
    """A record states what is true now. Corrections are rewrites, not layers.

    An `Amended …` block leaves the sentence it corrects in place. An agent
    reads top-down and acts on the first answer it finds, so the layer is not
    a correction — it is a second, contradictory answer sitting below the first.
    """
    body = split(path)[1]
    hits = [m.group(0).strip() for m in _AMENDED_RE.finditer(body)]
    assert not hits, (
        f"{path.name}: {len(hits)} amendment block(s) — {hits[:3]}\n"
        "Rewrite the sentence the amendment corrects, in place, and delete the "
        "block. Git holds the history; the record holds what is true."
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


@pytest.mark.parametrize("path", records(), ids=lambda p: p.name)
def test_the_h1_agrees_with_the_name(path: Path) -> None:
    """The one place the name legitimately appears twice: the document heading."""
    body = split(path)[1]
    m = re.search(r"^# (\S+)", body, re.M)
    assert m, f"{path.name}: body has no `# ADR-…` heading"
    assert m.group(1).rstrip(":") == meta_of(path)["name"], (
        f"{path.name}: heading says {m.group(1)!r}, frontmatter name is "
        f"{meta_of(path)['name']!r}"
    )
