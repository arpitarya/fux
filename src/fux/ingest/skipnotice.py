"""The skip record — W-93: it lives in `.fux/.fuxignore`, and it is committed.

`fux ingest` reports every path it did not index, with its reason, always
([ADR-INGEST](../../../docs/adr/0007_ingest.md) decision 4) — a silently
dropped file is indistinguishable from a file that was never there. On a real
corpus that is a **wall of identical lines on every single run**, and a wall
nobody reads is the same failure the rule exists to prevent, arrived at from
the other side.

**So the rule stays and only the repetition goes.** Every skip is still
reported the first time it is seen. What this module holds is *where the
already-reported set lives*, so a later run can print what is **new** and count
the rest.

## The set is `.fux/.fuxignore`, and that is a deliberate reversal

It was `.fux/runtime/skipped` — derived, gitignored, invisible to review.
**Arpit ruled on 2026-08-27 that the list belongs in `.fuxignore`**, written by
every ingest, and this module is the writer. Three things change and each is a
trade, not a free win:

- **The list is committed and reviewable.** It diffs, it survives a clone, and
  *"why is this file not in my index"* is answered by opening one file that is
  already the answer to that question by name.
- ⚠ **The list now DECIDES, not just describes.** A path in a block is ignored
  because it is in the block. So a derived verdict is **frozen**: widen
  `.fux/sources/types` and the `.py` files already listed stay out until their
  lines go. An `empty` file that gains content stays out too. **That cost was
  stated and accepted** — the escape hatch is deleting the line, or a `!` line,
  which always wins because the blocks are written first.
- **`.fux/runtime/skipped` is deleted on every run**, so a repo that has one
  from an older version loses it rather than keeping a second, stale answer.

## Two blocks, because the class must not be parsed back out of the reason

`fuxignore.BLOCK_NOT_INDEXED` holds the skips a committed list caused;
`fuxignore.BLOCK_SKIPPED` holds the ones fux could not read. A line's class is
**which block it is in** — structural. Reading it out of the note text would
put the classification one string edit away from being silently wrong, which is
exactly what ADR-INGEST decision 15 refuses.

**The reason is part of the key, deliberately.** A file that changes *why* it
is skipped — `empty` becoming `not an indexed file type` — is news, and prints
again. A fetch failure whose exception text changes prints again for the same
reason; that is correct, not noise.

**A path a hand-written pattern already covers gets no line.** Write
`*.py[cod]` yourself and 257 generated lines collapse to zero — the writer asks
`decide(..., hand_only=True)` before listing anything.

**URL skips are only replaced by a run that actually fetched.** An offline
`fux ingest` learns nothing about any URL, so it must not forget the URL skips
a networked run recorded — otherwise the next `fux update` re-prints them as
though they were new. This is `_observe_url_health`'s rule
([ADR-URL-INGEST](../../../docs/adr/0008_url-ingest.md)) applied to the
writer: an offline run does not get to speak about the networked plane.

⚠ **A URL is never written into a block, and the consequence is stated rather
than hidden.** `.fuxignore` matches repo-relative paths; an `https://` line
there would ignore nothing while reading as though it did. So a URL skip has
nowhere to be recorded and **prints on every networked run** — W-88's
report-once promise now covers files only.

**That is accepted rather than worked around**, for two reasons. A repo has a
handful of dead URLs, not hundreds, so it is a line and not a wall — the thing
W-88 was actually about. And repeat URL failure already has a home built for
it: `.fux/runtime/url-state.json` and the dead-URL report
([ADR-URL-INGEST](../../../docs/adr/0008_url-ingest.md)), which counts streaks
rather than restating one run's outcome. Keeping a second runtime file alive
just for URLs would put the answer in two places, which is what this change
removed.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..store import fuxdir
from . import fuxignore
from .gitdir import POLICY, Skipped, would_index

#: The pre-W-93 home. Kept only so every run can delete it.
LEGACY_NOTICE = "skipped"

#: A recorded key belongs to the URL plane iff it is an absolute URL. A URL
#: skip's `rel_path` *is* the URL (`urlsrc.fetch_all`), and a repo-relative
#: path can never carry a scheme, so this partition is exact rather than a
#: guess — and it needs no second file to record which plane a line came from.
_SCHEME = re.compile(r"^[a-z][a-z0-9+.\-]*://", re.IGNORECASE)


def path(root: Path) -> Path:
    """Where the record lives. Public so `doctor` and tests can name it."""
    return root / fuxignore.IGNORE_FILE


def legacy_path(root: Path) -> Path:
    """The pre-W-93 runtime file, which every run now removes."""
    return fuxdir.fux_dir(root) / "runtime" / LEGACY_NOTICE


def read(root: Path) -> dict[str, str]:
    """The `{rel_path: reason}` already reported. Never raises.

    A missing or unreadable file reads as *nothing reported yet*, which
    degrades to printing the full list once — the safe direction to fail in.
    Failing the other way would suppress a skip that was never shown.
    """
    try:
        ignores = fuxignore.read(root)
    except Exception:
        return {}
    return {g.path: g.note for g in ignores.generated.values()}


def unseen(root: Path, skipped) -> list[Skipped]:
    """The subset of `skipped` not already recorded, in the caller's order.

    Order is preserved rather than re-sorted: `walk_sources` and `fetch_all`
    both return sorted lists, so the printed lines stay in the order the
    unsuppressed run would have used.
    """
    ignores = fuxignore.read(root)
    seen = {g.path: g.note for g in ignores.generated.values()}
    out = []
    for skip in skipped:
        if seen.get(skip.rel_path) == skip.reason:
            continue
        # **A pattern you wrote is not news either.** Such a path gets no
        # generated line (one line beats many), so without this it would have
        # nothing recording it and would print on every run forever — W-88's
        # wall, rebuilt by the fix for W-93.
        if ignores.decide(skip.rel_path, hand_only=True).ignored:
            continue
        out.append(skip)
    return out


def write(root: Path, skipped) -> None:
    """Record `skipped` in `.fuxignore`, and delete the legacy runtime file."""
    legacy_path(root).unlink(missing_ok=True)
    ignores = fuxignore.read(root)
    blocks: dict[str, list[tuple[str, str]]] = {name: [] for name in fuxignore.BLOCKS}
    for skip in skipped:
        if not fuxignore.writable(skip.rel_path) or _SCHEME.match(skip.rel_path):
            continue
        if ignores.decide(skip.rel_path, hand_only=True).ignored:
            continue  # a pattern you wrote already covers it; one line beats many
        name = fuxignore.BLOCK_NOT_INDEXED if skip.kind == POLICY else fuxignore.BLOCK_SKIPPED
        blocks[name].append((skip.rel_path, skip.reason))
    fuxignore.write_blocks(
        root,
        not_indexed=blocks[fuxignore.BLOCK_NOT_INDEXED],
        skipped=blocks[fuxignore.BLOCK_SKIPPED],
    )


def stale_warnings(root: Path, *, types, excludes) -> list[str]:
    """Lines warning that a fux-written line no longer describes its file.

    **This is the guard on the cost of writing the list into `.fuxignore`.** A
    generated line decides, so it freezes the verdict that produced it: widen
    `.fux/sources/types` and the `.py` lines keep those files out; write content
    into a file listed as `empty` and it stays out, still labelled `empty`. The
    line is then a false statement that is also load-bearing — the exact shape
    ADR-FUXIGNORE exists to abolish.

    **The freeze is not undone here** (that was Arpit's call on 2026-08-27);
    it is made *loud*. Advisory, stderr, never an error, and it names the one
    edit that fixes it.

    ⚠ **It costs a byte read only for a path that passes both committed lists**
    — see `gitdir.would_index`. On this repo that is one file out of 599.
    """
    ignores = fuxignore.read(root)
    warnings = []
    for g in sorted(ignores.generated.values(), key=lambda g: g.path):
        if ignores.decide(g.path, hand_only=True).ignored:
            continue  # your own rule covers it; the generated line is not what holds it out
        if not would_index(root, g.path, excludes=excludes, types=types):
            continue
        warnings.append(
            f"warning: {fuxignore.IGNORE_FILE} lists `{g.path}` as `{g.note}`, "
            "and that is no longer true - it would be indexed today.\n"
            f"  fux wrote that line and will not remove it, because the line is what "
            "keeps the file out. Delete it to index the document."
        )
    return warnings


def label(skip: Skipped) -> str:
    """The word that opens a printed line, and it is the summary's own word.

    `not indexed` for a deliberate skip, `skip` for one fux could not read.
    **The two have to agree with the summary counts** - a line that says `skip`
    under a total that says `not indexed` is the W-83 shape: two true-looking
    statements about one event, and a reader who trusts the wrong one.

    ASCII only, like everything else printed here.
    """
    return "not indexed" if skip.deliberate else "skip"


def render(root: Path, skipped) -> list[str]:
    """The lines `fux ingest` should print, and record what it printed.

    One code path for every case, including the first run: with nothing on file
    every skip is unseen, so the full list prints exactly as it did before.

    ASCII only — these reach a Windows console (`_report_takeover`'s rule).
    """
    new = unseen(root, skipped)
    write(root, skipped)
    lines = [f"  {label(s)} {s.rel_path}: {s.reason}" for s in new]
    # **Two populations, one line, and "already recorded" is true of both.**
    # A path fux wrote into a block, and a path a hand-written pattern covers
    # (which gets no line of its own). The older wording said "unchanged since
    # the last run", which is false for the second on a FIRST run.
    repeated = len(skipped) - len(new)
    if repeated:
        more = "more " if new else ""
        lines.append(
            f"  ({repeated} {more}already recorded in {fuxignore.IGNORE_FILE}; "
            "'fux ingest --list-skipped' lists them all)"
        )
    return lines
