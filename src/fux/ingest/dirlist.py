"""The committed directory list, read — `.fux/sources/dirs`.

**Owned by [SR-DIR-LIST](../../../records/0120_dir-list.md)** since 2026-10-05
(W-261, Arpit's ruling that every `kind: component` record owns a file). A pure
move out of `ingest/gitdir.py`, which keeps the walk the list drives
(SR-INGEST's). The grammar machinery is `sourcelist.py`'s (SR-URL-LIST); what is
here is where the `dirs` list becomes values: the included entries, the `!`
subtractions, and the two declarations a line may carry — `archived=true` and
`enrich=true`, each **declared, never derived from a path** (decision 4).

Its Node twin is `node/src/ingest/dirlist.mjs`, which carries `read_dirs` and
`archived_dirs` — the only half the query plane reads.
"""

from __future__ import annotations

from pathlib import Path

from . import sourcelist

__all__ = ["archived_dirs", "enrich_dirs", "read_dirs", "source_dirs", "source_excludes"]


def read_dirs(root: Path, rel_path: str) -> list[sourcelist.Entry]:
    """Parse the committed directory list through the one shared grammar.

    Deduped and sorted by entry, so file order is presentation only — a human
    may group by team or by system and it cannot change a committed byte.
    """
    return sourcelist.read(
        root,
        rel_path,
        sourcelist.DIRS,
        missing_hint=(
            "create it with one directory or file per line (a line may carry "
            "`archived=true`), or run `fux setup` to write a starter"
        ),
    )


def source_dirs(root: Path, rel_path: str) -> list[str]:
    """Just the **included** entry values. Exclusions are `source_excludes`."""
    return [entry.value for entry in read_dirs(root, rel_path) if not entry.exclude]


def source_excludes(root: Path, rel_path: str) -> list[str]:
    """The `!` patterns — repo-relative globs, applied to the whole walk."""
    return [entry.value for entry in read_dirs(root, rel_path) if entry.exclude]


def archived_dirs(root: Path, rel_path: str) -> list[str]:
    """Included entries declared `archived=true` (SR-ARCHIVED-CONTENT decision 6's
    input). Reads the same committed declaration SR-ARCHIVED-CONTENT decision 1 leaves off the
    record — the ranking keys off the source list, never a path convention
    (SR-DIR-LIST decision 4)."""
    return [
        entry.value
        for entry in read_dirs(root, rel_path)
        if not entry.exclude and entry.attrs.get("archived") == "true"
    ]


def enrich_dirs(root: Path, rel_path: str) -> list[str]:
    """Included entries declared `enrich=true` (W-76 Phase 8).

    The same shape as `archived_dirs` and read from the same committed file,
    because the two answer the same kind of question: *which directories did a
    human decide something about?* Neither is ever inferred from a path.
    """
    return [
        entry.value
        for entry in read_dirs(root, rel_path)
        if not entry.exclude and entry.attrs.get("enrich") == "true"
    ]
