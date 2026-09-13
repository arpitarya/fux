"""A numbered record path in a live file must resolve — the renumber gate.

**Two strikes, so this is a check rather than a paragraph** (CLAUDE.md
§"Two strikes → a gate"). The register renumbered records on **2026-09-11**
(laws given their own range) and again on **2026-09-13** (`records/` to the
repo root, then the WORK range). Both passes repointed the records and the
queue and **both left the rest of the tree behind**: after the second, 40 dead
paths sat in `src/fux/` docstrings, 11 in `tests/`, 5 in the decoders `fux
setup` writes into a consumer's repo, and 24 in the agent skills. Nothing
failed. A dead `[SR-TUNE](../../records/0038_tuning.md)` in a docstring is
invisible to every other check here, and CI stayed green through both.

**What it fails on, and only this:** a reference `NNNN_<slug>.md` that does not
resolve **while `records/` holds that same `<slug>` under a different number**.
That is unambiguously a renumber miss — the record exists, the citation points
at where it used to be.

**What it deliberately does NOT fail on**, because each would be the check
firing on correct content:

- A slug no live record has. That is a **retired** record being *named* in
  prose, which CLAUDE.md §"Archive is not evidence" explicitly permits.
- Anything frozen or append-only: `archive/`, `work/regression/` (measured
  evidence and verdicts — *"nothing supersedes a measurement except a better
  measurement"*), `work/WORKLOG.md`, `CHANGELOG.md`, and any
  `PRE-REGISTRATION*` (*"a pre-registered threshold may never move"*). These
  SHOULD name the number that was true when they were written; repointing them
  would rewrite history, and in `work/regression/**/evidence/` it would edit
  the measured data itself — a `"gold": "docs/adr/0031_types-list.md"` is a
  **datum**, not a link.
- `work/golden/`, which no Claude session reads.

⚠ **This gate does not make numbered citations correct — it makes them
resolvable.** The standing rule is still *cite records by NAME, never by
number* (CLAUDE.md §The SR standing rules). Every path this test checks is a
citation that should not have carried a number in the first place; the test is
the floor under that rule, not a substitute for it.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "records"

#: Frozen or append-only: these name the number that was true when written.
_FROZEN_PREFIXES = (
    "archive/",
    "work/regression/",
    "work/golden/",
)

#: GENERATED, not authored: these are rebuilt from source and their staleness is
#: a re-ingest/re-build problem, never a citation to repair by hand. `.fux/`'s
#: AUTHORED extension points — `decoders/`, `fetchers/`, `sources/` — are NOT
#: here and are checked like any other source (L10: they are the one place
#: readable source IS the contract).
_GENERATED_PREFIXES = (
    ".fux/index/",
    ".fux/runtime/",
    ".fux/enrich/",
    ".fux/acquired/",
    ".fux/node/",
)

#: This file names real record paths in its own docstring to say what it flags —
#: the check firing on its own explanation. One exact path, never a pattern.
_SELF = "tests/test_record_paths_resolve.py"
_FROZEN_FILES = (
    "work/WORKLOG.md",
    "CHANGELOG.md",
)

_TEXT_SUFFIXES = {
    ".md", ".py", ".mjs", ".js", ".json", ".yml", ".yaml",
    ".toml", ".txt", ".html", ".svg", ".cfg", ".ini",
}

_SKIP_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", "_to_delete", "dist", "build",
}

_REF = re.compile(r"((?:\.\./)*(?:records/)?)(\d{4})_([A-Za-z0-9._-]+\.md)")


def _live_slugs() -> dict[str, str]:
    """`<slug>.md` -> the four-digit number it lives under today."""
    out = {}
    for path in RECORDS.glob("[0-9][0-9][0-9][0-9]_*.md"):
        out[path.name[5:]] = path.name[:4]
    return out


def _is_frozen(rel: str) -> bool:
    if rel == _SELF:
        return True
    if rel in _FROZEN_FILES or rel.startswith(_FROZEN_PREFIXES):
        return True
    if rel.startswith(_GENERATED_PREFIXES):
        return True
    return "PRE-REGISTRATION" in Path(rel).name


def _candidate_files() -> list[Path]:
    out = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in _TEXT_SUFFIXES:
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        rel = path.relative_to(ROOT).as_posix()
        if _is_frozen(rel):
            continue
        out.append(path)
    return out


def _resolves(ref: str, from_dir: Path) -> bool:
    for cand in (
        (from_dir / ref),
        (ROOT / ref),
        (RECORDS / Path(ref).name),
    ):
        if cand.exists():
            return True
    return False


def test_every_numbered_record_path_in_a_live_file_resolves() -> None:
    stale: list[str] = []
    live = _live_slugs()
    for path in _candidate_files():
        rel = path.relative_to(ROOT).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for match in _REF.finditer(text):
            prefix, number, slug = match.groups()
            ref = f"{prefix}{number}_{slug}"
            if _resolves(ref, path.parent):
                continue
            if slug not in live:
                continue  # a retired record, NAMED in prose — permitted
            line = text[: match.start()].count("\n") + 1
            stale.append(f"{rel}:{line}  {ref}  ->  records/{live[slug]}_{slug}")

    assert not stale, (
        "a renumber left these citations pointing at where a record USED to be.\n"
        "Each one names a record that still exists under a different number.\n"
        "Repoint them (the slug is unchanged — only the four digits move), or, "
        "better, replace the link with the record's NAME per CLAUDE.md "
        "§The SR standing rules.\n\n  " + "\n  ".join(sorted(stale))
    )


def test_the_frozen_set_is_exact_paths_and_prefixes_not_a_pattern() -> None:
    """The exemption is the part most likely to widen quietly.

    A `parts` match on `regression`, or a bare `evidence` prefix, would let a
    live document hide under any directory that happened to be named for a
    run. `archive/` is the one archive (CLAUDE.md §Archive is not evidence);
    `work/regression/` is measured evidence; the two files are append-only.
    """
    assert _FROZEN_PREFIXES == ("archive/", "work/regression/", "work/golden/")
    assert _FROZEN_FILES == ("work/WORKLOG.md", "CHANGELOG.md")
    assert _is_frozen("work/WORKLOG.md")
    assert _is_frozen("tools/maintenance-bench/PRE-REGISTRATION.md")
    assert not _is_frozen("work/WORKLOG-notes.md")
    assert not _is_frozen("work/regression-summary.md")
    assert not _is_frozen("src/fux/tune.py")
    # the authored halves of `.fux/` stay checked; only generated planes skip
    assert _is_frozen(".fux/runtime/graph.json")
    assert not _is_frozen(".fux/decoders/csv.py")
    assert not _is_frozen(".fux/fetchers/http.py")
