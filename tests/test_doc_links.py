"""Every relative link in a live document resolves to a file that exists.

**Why this is a test and not a rule.** Broken internal links have now been the
recorded failure twice: five were found and fixed by the 2026-08-24 ADR audit
(W-77), and a repo-wide sweep the same day found **71 more** — every one of them
a link into `work/open/` for an item that had closed and retired into
`archive/open/`, or an ADR path written from the register's stale display label
rather than the filename. CLAUDE.md's standing rule is that a failure class the
WORKLOG records twice becomes a check in the change that records the second
occurrence. This is that check.

**The mechanism that produced them**, so the exemptions below make sense: a work
item's detail file is *deleted from* `work/open/` and *moved to* `archive/open/`
when its row leaves the queue. Every live doc that linked to it silently breaks
at that moment, and nothing was watching. The register's renumbering of
2026-08-22 did the same thing to ADR paths.

**What is exempt, and why each one is exempt by law rather than by convenience:**

- `work/WORKLOG.md` is **append-only** — a past entry describes the tree as it
  was, and repairing its links would make the record false.
- `work/regression/**` are **frozen measurements**. A filed verdict is never
  edited (CLAUDE.md §"A pre-registered threshold may never move").
- `tools/**` holds **frozen pre-registrations**, same rule.
- `archive/**` is frozen and its links are never repaired
  (`tests/test_archive_law.py` states this).
- `CHANGELOG.md` is a **historical record** of released versions.
- `docs/adr/TEMPLATE.md` links **placeholders** (`000N_<short-name>.md`).
- Targets **outside the repo** cannot be checked from inside it — `README.md`
  points at the sibling `fux-playground`, deliberately.

⚠ **The cost, stated rather than discovered:** a genuinely broken link inside an
exempt file is invisible to this test. That is the price of the append-only and
never-edit-a-verdict laws, and it is paid knowingly — those files are read as
history, where a dead link is a fact about the past rather than a defect.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_SKIP_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", "dist", "build", ".fux", "_to_delete",
}

# Frozen-by-law trees: never edited, so never repaired.
_FROZEN_PREFIXES = ("work/regression/", "archive/", "tools/")

# Frozen-by-law single files.
_FROZEN_FILES = {
    "work/WORKLOG.md",       # append-only session log
    "CHANGELOG.md",          # released history
    "docs/adr/TEMPLATE.md",  # links are placeholders, not paths
}

# A link may legitimately point at a sibling repo that is not vendored here.
_EXTERNAL_OK = {"../fux-playground/", "../fux-lab/"}

_LINK = re.compile(r"(?<=\]\()([^)\s]+?)(?=(?:\s+\"[^\"]*\")?\))")


def _live_markdown() -> list[Path]:
    out = []
    for path in sorted(ROOT.rglob("*.md")):
        rel = path.relative_to(ROOT).as_posix()
        if any(part in _SKIP_DIRS for part in Path(rel).parts):
            continue
        if rel in _FROZEN_FILES or rel.startswith(_FROZEN_PREFIXES):
            continue
        out.append(path)
    return out


def test_there_are_live_documents_to_check() -> None:
    """A collector that silently matches nothing is a test that always passes."""
    docs = _live_markdown()
    assert len(docs) > 20, f"only {len(docs)} live documents collected — the filter is too wide"


def test_every_relative_link_in_a_live_document_resolves() -> None:
    broken: list[str] = []
    for path in _live_markdown():
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for target in _LINK.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if any(target.startswith(prefix) for prefix in _EXTERNAL_OK):
                continue
            if (path.parent / target.split("#")[0]).exists():
                continue
            broken.append(f"{rel}  ->  {target}")

    assert not broken, (
        f"{len(broken)} link(s) in live documents point at files that do not exist:\n  "
        + "\n  ".join(broken)
        + "\n\nThe usual cause: the target was a work item under `work/open/` that has "
          "since closed and retired into `archive/open/`, or an ADR path written from "
          "the register's display label instead of the filename. Repoint at the LIVE "
          "successor — a deleted link leaves the claim ungrounded and nobody can see "
          "that anything is missing (CLAUDE.md §Archive is not evidence)."
    )
