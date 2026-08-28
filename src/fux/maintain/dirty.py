"""The dirty list — W-66 Phase 1: the artefact a deferred re-index consumes.

Local, gitignored state under `.fux/runtime/` (the existing home for derived
planes, ADR-DOTFUX) recording which documents changed since the last
completed `fux ingest`. `post-commit` appends to it; a completed ingest run
subtracts what it set out to cover.

**It is a union, never a replacement.** Two commits landing before anything
consumes the list must leave both commits' documents pending — this is what
makes a later takeover safe (ADR-MAINTENANCE decision 1d): whichever run
picks the list up gets everything, not just the most recent commit.

**It is emptied by subtraction, never wholesale — there is deliberately no
`clear`.** A run takes a snapshot when it starts and `discard`s exactly that
snapshot when it finishes, so a commit that lands *while the run is in flight*
is still pending afterwards. A wholesale clear would silently drop it, and
under the takeover rule (decision 1d) a commit landing mid-run is ordinary
rather than rare. A run that dies before finishing subtracts nothing, so the
list survives it intact.

**It is advisory, never authoritative.** `fux ingest` walks and re-indexes
the whole corpus regardless of what this file says — a missing, stale or
corrupt list can never change a committed byte. That is the sentence that
keeps L3 true; nothing here is a second write path into the index.
"""

from __future__ import annotations

from pathlib import Path

from ..store import fuxdir

DIRTY_NAME = "dirty"


def _path(root: Path) -> Path:
    return fuxdir.fux_dir(root) / "runtime" / DIRTY_NAME


def read(root: Path) -> list[str]:
    """The currently pending document ids, sorted and deduped. Never raises.

    A missing or unreadable file reads as "nothing known pending" — the list
    is advisory, so "cannot tell" degrades to "empty" rather than raising on
    a reporting path (`fux ask`, `fux doctor`).
    """
    try:
        text = _path(root).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return sorted({line.strip() for line in text.splitlines() if line.strip()})


def is_readable(root: Path) -> bool:
    """Does a dirty list exist and can it be read?

    **Absent is not the same as empty, and under narrow-by-default the
    difference decides whether a URL is ever fetched again.** `read` collapses
    both to `[]` on purpose — it feeds reporting paths where "cannot tell"
    should degrade quietly to "nothing known pending".

    ⚠ **A consumer that ACTS on the list needs the distinction.** `fux update`
    refreshes the dirty list by default (W-82 ruling 3), and an empty list means
    *fetch nothing*. A missing or unreadable list would therefore turn `update`
    into a silent no-op — **exactly the "the tail silently stops being
    refreshed" failure the ruling warns about**, arriving through the file's own
    tolerance rather than through the ruling.

    So: **list present ⇒ trust it. List absent ⇒ sweep everything.** Fail safe,
    not fail silent.
    """
    try:
        _path(root).read_text(encoding="utf-8", errors="replace")
        return True
    except OSError:
        return False


def record(root: Path, doc_ids) -> None:
    """Add `doc_ids` to the list, as a union with whatever is already there.

    A no-op on an empty `doc_ids` — it never creates `.fux/runtime/` just to
    write nothing into it.
    """
    ids = {i.strip() for i in doc_ids if i and i.strip()}
    if not ids:
        return
    merged = sorted(set(read(root)) | ids)
    directory = fuxdir.derived_dir(root, "runtime")
    (directory / DIRTY_NAME).write_text("\n".join(merged) + "\n", encoding="utf-8")


def discard(root: Path, doc_ids) -> None:
    """Subtract `doc_ids` from the list — the snapshot a completed run covered.

    **Not a clear.** Anything recorded since that snapshot was taken stays
    pending, which is the whole of why a commit landing mid-run is not lost.
    Called only by a run that reached `write_index`; a stopped or crashed run
    never gets here.
    """
    covered = {i.strip() for i in doc_ids if i and i.strip()}
    if not covered:
        return
    remaining = [i for i in read(root) if i not in covered]
    path = _path(root)
    if not path.exists():
        return  # nothing was ever written; nothing to subtract from
    path.write_text("".join(f"{i}\n" for i in remaining), encoding="utf-8")
