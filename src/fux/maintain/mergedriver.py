"""The line-wise merge driver for `.fux/index/*.jsonl`.

Git invokes this as a custom merge driver (see `hooks.py` for the wiring):

```
fux-merge-index %O %A %B
```

`%O` is the common ancestor, `%A` is *ours* — and **also the file git reads the
result from** — and `%B` is *theirs*. Exit 0 means resolved; non-zero means
conflict, and git leaves the file for a human.

## Why a shard can be merged at all

A shard is a header line plus **one JSON line per document, sorted by `id`**.
Two branches that each added documents produce two line sets whose union is the
correct answer, and a textual three-way merge cannot see that: it sees
neighbouring lines and reports a conflict on adjacency alone. That is the whole
reason this driver exists — **machine planes should never conflict on the mere
fact that two people worked at once.**

## Last-writer-wins on `(ver, sha)`, and what it refuses to do

For a document present on both sides:

- **Different `ver`** — the higher one wins. `ver` increments exactly when a
  document's own `sha` changes, so a higher `ver` is strictly later work.
- **Same `ver`, same bytes** — no conflict; they agree.
- **Same `ver`, different bytes** — **refused.** Two branches derived a
  different record for the same document at the same revision, which means one
  of them ingested content the other did not have. Picking either silently
  publishes a record nobody produced.

> **The hazard this is written against.** A merge driver is the piece a user
> cannot debug when it goes wrong, so its failure mode must be *refuse and
> leave both sides*, never *silently pick one*. When this driver cannot
> resolve, it writes ordinary conflict markers and exits non-zero — the same
> thing a human already knows how to fix.

## Deletions

A document present in the ancestor and absent from one side was **deleted**
there, and the deletion wins over an unmodified other side. A deletion racing a
*modification* is refused, for the same reason as above.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

__all__ = ["merge_shards", "main", "MergeConflict"]


class MergeConflict(Exception):
    """Unresolvable. Carries the ids so the message can name them."""

    def __init__(self, ids: list[str]) -> None:
        super().__init__(", ".join(ids))
        self.ids = ids


def _split(text: str) -> tuple[str, dict[str, str]]:
    """`(header_line, {id: line})`. Order is rebuilt by sorting, never kept."""
    lines = [l for l in text.split("\n") if l.strip()]
    if not lines:
        return "", {}
    header, *records = lines
    out: dict[str, str] = {}
    for line in records:
        try:
            out[json.loads(line)["id"]] = line
        except (json.JSONDecodeError, KeyError) as exc:
            raise MergeConflict([f"<unparseable line: {exc}>"]) from exc
    return header, out


def _ver(line: str) -> int:
    return int(json.loads(line).get("ver", 0))


def merge_shards(ancestor: str, ours: str, theirs: str) -> str:
    """Three-way merge of one shard. Raises `MergeConflict` when it cannot.

    Deterministic: the output is sorted by id, so two machines merging the same
    three inputs produce the same bytes. Without that the merge driver would be
    a hole in L3 the size of every collaborative repository.
    """
    base_header, base = _split(ancestor)
    our_header, mine = _split(ours)
    their_header, yours = _split(theirs)

    header = our_header or their_header or base_header
    if our_header and their_header and our_header != their_header:
        raise MergeConflict(["<header>"])  # a format change is never auto-merged

    merged: dict[str, str] = {}
    conflicts: list[str] = []

    for doc_id in sorted(set(base) | set(mine) | set(yours)):
        in_base, in_ours, in_theirs = base.get(doc_id), mine.get(doc_id), yours.get(doc_id)

        if in_ours == in_theirs:                      # agree, or both deleted
            if in_ours is not None:
                merged[doc_id] = in_ours
            continue

        if in_base is None:
            # Not in the ancestor: one side ADDED it. A one-sided add is the
            # common case — two people documenting different things — and it
            # is not a conflict. Ordering this branch after the None check
            # below is the bug this comment exists to prevent: it made every
            # disjoint add look like a delete-vs-modify race.
            if in_ours is None:
                merged[doc_id] = in_theirs
            elif in_theirs is None:
                merged[doc_id] = in_ours
            else:
                conflicts.append(doc_id)              # both added, differently
            continue

        if in_ours is None or in_theirs is None:
            # In the ancestor and gone from one side: that side DELETED it.
            # A deletion beats an untouched other side; a deletion racing a
            # modification is a real disagreement.
            surviving = in_ours if in_theirs is None else in_theirs
            if surviving == in_base:
                continue                              # the other side deleted it
            conflicts.append(doc_id)                  # deleted here, changed there
            continue

        # Ancestor check first, `ver` second. If one side is byte-identical to
        # the ancestor, the other side's bytes win outright — this is exactly
        # as certain as the delete-vs-unmodified case above, and it does not
        # depend on `ver` having been bumped correctly. Relying on `ver`
        # alone means a document whose `ver` was not incremented (a hand
        # repair, an external edit, an ingest edge case) reads as "same
        # ver, different bytes" and gets refused as an unresolvable
        # conflict — even though one side provably did not touch it.
        if in_ours == in_base:
            merged[doc_id] = in_theirs
            continue
        if in_theirs == in_base:
            merged[doc_id] = in_ours
            continue

        our_ver, their_ver = _ver(in_ours), _ver(in_theirs)
        if our_ver > their_ver:
            merged[doc_id] = in_ours
        elif their_ver > our_ver:
            merged[doc_id] = in_theirs
        else:
            conflicts.append(doc_id)                  # same ver, different bytes

    if conflicts:
        raise MergeConflict(conflicts)
    return "\n".join([header, *(merged[k] for k in sorted(merged))]) + "\n"


def _conflict_text(ours: str, theirs: str, ids: list[str]) -> str:
    """Ordinary conflict markers — the thing a human already knows how to fix."""
    named = ", ".join(ids[:5]) + (f" (+{len(ids) - 5} more)" if len(ids) > 5 else "")
    return (
        f"<<<<<<< ours\n{ours.rstrip()}\n"
        f"======= fux could not merge: {named}\n"
        f"{theirs.rstrip()}\n>>>>>>> theirs\n"
    )


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 3:
        print("usage: fux-merge-index <ancestor> <ours> <theirs>", file=sys.stderr)
        return 2

    ancestor, ours, theirs = (Path(a) for a in argv[:3])
    # Reading with the default `newline=None` is deliberate: universal-newline
    # translation normalizes CRLF/CR/LF alike to `\n`, so a file checked out
    # with CRLF (Windows) parses identically to one checked out with LF. The
    # write side needs the opposite instinct — `newline="\n"` below disables
    # the platform-default translation there, so this driver never commits
    # CRLF on Windows while committing LF everywhere else, which would break
    # L3's byte-identical guarantee across machines.
    base_text = ancestor.read_text(encoding="utf-8") if ancestor.exists() else ""
    our_text = ours.read_text(encoding="utf-8")
    their_text = theirs.read_text(encoding="utf-8")

    try:
        ours.write_text(
            merge_shards(base_text, our_text, their_text), encoding="utf-8", newline="\n"
        )
    except MergeConflict as exc:
        # Refuse loudly and leave both sides. Never pick one.
        ours.write_text(
            _conflict_text(our_text, their_text, exc.ids), encoding="utf-8", newline="\n"
        )
        print(
            f"fux: cannot merge {ours.name} — {len(exc.ids)} document(s) changed on both sides "
            f"at the same revision: {', '.join(exc.ids[:5])}\n"
            f"     Resolve by re-running `fux ingest`, which derives the index from the merged "
            f"content rather than from either side's copy.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
