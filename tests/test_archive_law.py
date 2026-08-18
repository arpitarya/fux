"""There is exactly one archive directory, and it is at the repo root.

Arpit ruled this on 2026-08-10 and restated it on 2026-08-18 after a
reorganisation quietly reintroduced a second one. A rule that has to be
restated is a rule that needs a check.

The cost of two archives is not tidiness. It is that "where did this go?"
stops having one answer, and the archive-is-not-evidence rule has to be
remembered in two places instead of enforced in one.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "archive"

# Directories that are not part of the repo's own structure.
_SKIP = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
    ".mypy_cache", "_to_delete",
}

# `work/WORKLOG.md` is append-only history: its old entries describe a tree that
# really did have a second archive, and rewriting them would make the record
# false. `archive/` itself is frozen and its links are never repaired.
_STALE_LINK_EXEMPT = {"work/WORKLOG.md"}


def test_the_root_archive_exists_and_is_mapped() -> None:
    assert ARCHIVE.is_dir(), "the archive lives at the repo root and must exist"
    readme = ARCHIVE / "README.md"
    assert readme.is_file(), "archive/README.md is the map; without it the archive is a dead end"


def test_there_is_no_second_archive() -> None:
    """Any directory named `archive` outside the root is the defect."""
    strays = []
    for path in ROOT.rglob("archive"):
        if not path.is_dir():
            continue
        if path == ARCHIVE:
            continue
        rel = path.relative_to(ROOT)
        if any(part in _SKIP for part in rel.parts):
            continue
        if ARCHIVE in path.parents:  # nested inside the one archive is fine
            continue
        strays.append(rel.as_posix())

    assert not strays, (
        "these are second archives, and there is only ever one:\n  "
        + "\n  ".join(sorted(strays))
        + "\n\nMove their contents into archive/ — mirroring the live tree "
        "(work/adr/ retires into archive/adr/, and the handoff directory "
        "retired wholesale into archive/handoff/) — and add a row to "
        "archive/README.md naming each "
        "one's live successor."
    )


def test_nothing_live_points_into_a_retired_second_archive() -> None:
    """`work/archive/…` and `work/handoff/…` were real paths until 2026-08-18.

    Both retired into the one archive on the same day. Catch stale links.
    """
    offenders = []
    for path in sorted(ROOT.rglob("*.md")):
        rel = path.relative_to(ROOT)
        if any(part in _SKIP for part in rel.parts):
            continue
        if rel.parts and rel.parts[0] == "archive":  # frozen; links are not repaired
            continue
        if rel.as_posix() in _STALE_LINK_EXEMPT:
            continue
        # Frozen measurement records are never edited; their paths are read
        # through the move map in docs/adr/README.md instead.
        if len(rel.parts) > 2 and rel.parts[:1] == ("work",) and rel.parts[1] == "regression":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for stale in ("work/archive/", "docs/archive/", "work/handoff/"):
            if stale in text:
                offenders.append(f"{rel.as_posix()}: still refers to {stale}")
    assert not offenders, (
        "\n".join(sorted(offenders))
        + "\n\nThere is one archive, at the repo root. Repoint these at archive/."
    )
