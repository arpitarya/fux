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
#
# ⚠ SR-ONE-ARCHIVE's exemption was REMOVED 2026-09-13. The record was retired
# and its file deleted, so the exemption named a path that no longer existed —
# a dead entry in a law's exemption set, which is the one place a dead entry is
# dangerous: it reads as a live carve-out. **No live record names `docs/archive/`
# or `work/archive/` today** (re-derived, not assumed), so the set is one path.
# It was kept exempt while it existed because it was **the record of this very
# rule** and could not state what it retired without naming those two paths —
# they were its §Alternatives and its history, not links to
# follow. Flagging it is the check firing on correct content, which is how a
# check gets switched off rather than fixed (the same lesson
# `tests/test_windows_console_safe.py` paid for when it flagged the code
# defending against a character).
#
# ⚠ **The cost, stated rather than discovered:** a genuinely stale link inside
# that one file is now invisible to this test. The exemption is per-file
# because that is the mechanism available, and the mitigation is that the file
# is short, is about nothing else, and names those paths only in prose.
_STALE_LINK_EXEMPT = {"work/WORKLOG.md"}


def test_the_corpus_exemption_is_one_exact_path_not_a_pattern() -> None:
    """A law's exemption is the thing most likely to be widened quietly.

    It must stay an exact path: a `parts` match on `golden`, or a prefix, would
    let a genuine second archive hide under any directory that happened to be
    named for the benchmark.
    """
    assert "/" in _CORPUS_ARCHIVE and not _CORPUS_ARCHIVE.endswith("/")
    assert _CORPUS_ARCHIVE == "work/golden/seed/archive"


def test_the_root_archive_exists_and_is_mapped() -> None:
    assert ARCHIVE.is_dir(), "the archive lives at the repo root and must exist"
    readme = ARCHIVE / "README.md"
    assert readme.is_file(), "archive/README.md is the map; without it the archive is a dead end"


#: The one place a directory named `archive` is CONTENT rather than a second
#: archive: the sealed benchmark's corpus.
#:
#: ⚠ **This exemption was forced by a rule, not chosen for convenience.**
#: [SR-RS](../records/0133_predictions.md) decision 23a says the test data
#: must contain the input each feature acts on — *"one that reads
#: `archived=true` needs a directory declared archived"*. Codex's prompt 1b
#: created `work/golden/seed/archive/` on 2026-09-12 to satisfy exactly that,
#: and this check fired on it.
#:
#: **The law is about documentation that retired**; these are five fictional
#: retired documents about a fictional cold-chain company, and they exist so a
#: ranking prior has something to act on. Moving them into `archive/` would
#: move the corpus away from its manifests and break the ladder.
#:
#: ⚠ **The cost:** a real second archive created under `work/golden/` would
#: now be invisible here. The prefix is as narrow as it can be — one path, not
#: a `golden` part anywhere — and `work/golden/` holds no project documentation
#: to retire.
_CORPUS_ARCHIVE = "work/golden/seed/archive"


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
        if rel.as_posix() == _CORPUS_ARCHIVE:  # test data, not a retired doc
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
        # through the move map in records/README.md instead.
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
