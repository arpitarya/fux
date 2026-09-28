#!/usr/bin/env python3
"""Plan a golden rung's git history from `work/golden/seed-history.tsv` — W-168 step 8's instrument.

**Why this exists.** The git authority prior (W-168 step 8) reads commit
metadata: distinct authors × commit count per document. The ladder commits
every document **once**, as `fux-lab`, on its `seed-dates.tsv` date — so the
prior would read `1 × 1` everywhere and measure nothing. That is
[SR-WORK-TESTDATA](../../records/0068_WORK-test-data.md) **T11**: a feature
that reads history is measured on a corpus that **has** history. Arpit ruled on
2026-09-25 that the history goes into the seed and the ladder is rebuilt.

**What it does.** Turns three committed inputs into an ordered list of commits:

- `work/golden/seed-dates.tsv` — each document's FINAL date (unchanged role);
- `work/golden/seed-history.tsv` — optional earlier revisions, one row each;
- `work/golden/seed-history/` — the full text of each earlier revision.

A document with no history row gets exactly what the ladder gave it before: one
commit, by the default author, at its `seed-dates.tsv` date. **With an empty or
absent history file the plan is the old ladder's, commit for commit** — that is
the property `tests/test_golden_history.py` holds.

## The file — `seed-history.tsv`

Tab-separated, `#` comments, one row per commit **of one document**:

    # path                  date        author                           revision
    seed/23-cold-room.md    2024-02-01  Priya Nair <priya@quillfern.example>  seed-history/23-cold-room.md@1
    seed/23-cold-room.md    2024-05-10  Tomasz Kral <tomasz@quillfern.example> seed-history/23-cold-room.md@2
    seed/23-cold-room.md    2024-09-03  Priya Nair <priya@quillfern.example>  final

- `revision` is a path under `work/golden/` holding that version's **full
  text**, or `final` — the seed file itself.
- 🔴 **Every document with rows has exactly one `final`, it is the last by
  date, and its date equals the document's `seed-dates.tsv` date.** So the
  document's last commit — which is where fux reads `mtime` — does not move,
  and the recency prior sees the ladder it saw before.
- Dates strictly increase per document; two revisions of one document never
  carry the same text. **A commit that changes nothing is not history** — git
  would refuse it, and an authority count built on it would be counting air.
- 🔴 **`seed-history/` is never copied into a rung.** An earlier revision is a
  past state of a document, not a document; indexing it would put two versions
  of one fact in the corpus.

## Determinism (L4)

Commits are grouped by `(date, author)` and ordered by date, then author, then
path — no clock, no set order, no environment. The default author's commits keep
the ladder's old message (`corpus: <date> (<n> documents)`), so a rung built
with no history is byte-identical to one built before this file existed.

🔴 **This file never reads `work/golden/questions/` or any answer key.** It
reads the three inputs above and nothing else.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

#: The ladder's one author before history existed — `git config user.name
#: fux-lab` in the rung builder. Commits by it keep the old message shape.
DEFAULT_AUTHOR = "fux-lab <lab@fux.example>"

FINAL = "final"

_AUTHOR = re.compile(r"^(?P<name>[^<>]+?)\s*<(?P<email>[^<>\s]+@[^<>\s]+)>$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class HistoryError(ValueError):
    """The history file contradicts itself or the seed. Refused, never repaired."""


@dataclass(frozen=True)
class Revision:
    """One commit of one document."""

    path: str       # rung-relative, e.g. `seed/23-cold-room.md`
    date: str       # YYYY-MM-DD
    author: str     # `Name <email>`
    source: str     # `final`, or a path under work/golden/


@dataclass(frozen=True)
class Commit:
    """One git commit in the rung: every revision sharing a date and an author."""

    date: str
    author: str
    revisions: tuple[Revision, ...]

    @property
    def name(self) -> str:
        return split_author(self.author)[0]

    @property
    def email(self) -> str:
        return split_author(self.author)[1]

    @property
    def message(self) -> str:
        n = len(self.revisions)
        if self.author == DEFAULT_AUTHOR:
            return f"corpus: {self.date} ({n} documents)"
        return f"corpus: {self.date} · {self.name} ({n} documents)"


def split_author(author: str) -> tuple[str, str]:
    m = _AUTHOR.match(author.strip())
    if not m:
        raise HistoryError(f"author is not `Name <email>`: {author!r}")
    return m.group("name"), m.group("email")


def read_history(path: Path) -> list[Revision]:
    """Parse `seed-history.tsv`. Absent means no history, which is legal."""
    if not path.exists():
        return []
    rows: list[Revision] = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        cells = [c.strip() for c in line.split("\t")]
        if len(cells) != 4:
            raise HistoryError(f"line {n}: expected 4 tab-separated cells, got {len(cells)}")
        doc, date, author, source = cells
        if not _DATE.match(date):
            raise HistoryError(f"line {n}: date is not YYYY-MM-DD: {date!r}")
        split_author(author)
        rows.append(Revision(doc, date, author, source))
    return rows


def plan(
    final_dates: dict[str, str],
    history: list[Revision],
    *,
    read_source=None,
    default_author: str = DEFAULT_AUTHOR,
) -> list[Commit]:
    """The rung's commits, in order.

    `final_dates` is every document in the rung → its final date (seed rows from
    `seed-dates.tsv`, ext rows from the generator). `read_source(rev)` returns a
    revision's bytes; it is used only to refuse a revision identical to the one
    before it, and may be omitted when the caller has no bytes to hand.
    """
    by_doc: dict[str, list[Revision]] = {}
    for rev in history:
        if rev.path not in final_dates:
            raise HistoryError(f"history names a document the rung does not hold: {rev.path}")
        by_doc.setdefault(rev.path, []).append(rev)

    revisions: list[Revision] = []
    for doc in sorted(final_dates):
        rows = by_doc.get(doc)
        if not rows:
            revisions.append(Revision(doc, final_dates[doc], default_author, FINAL))
            continue
        _check_document(doc, rows, final_dates[doc], read_source)
        revisions.extend(rows)

    groups: dict[tuple[str, str], list[Revision]] = {}
    for rev in revisions:
        groups.setdefault((rev.date, rev.author), []).append(rev)
    return [
        Commit(date, author, tuple(sorted(groups[(date, author)], key=lambda r: r.path)))
        for date, author in sorted(groups)
    ]


def _check_document(doc: str, rows: list[Revision], final_date: str, read_source) -> None:
    finals = [r for r in rows if r.source == FINAL]
    if len(finals) != 1:
        raise HistoryError(f"{doc}: {len(finals)} `final` rows — exactly one is required")
    dates = [r.date for r in rows]
    if dates != sorted(dates) or len(set(dates)) != len(dates):
        raise HistoryError(f"{doc}: dates must strictly increase in file order: {dates}")
    if rows[-1].source != FINAL:
        raise HistoryError(f"{doc}: the `final` row must be the last by date")
    if finals[0].date != final_date:
        raise HistoryError(
            f"{doc}: `final` is dated {finals[0].date} but seed-dates.tsv says {final_date} — "
            "the last commit is where fux reads mtime, so they must agree"
        )
    for r in rows:
        if r.source != FINAL and not r.source.startswith("seed-history/"):
            raise HistoryError(f"{doc}: a revision must live under seed-history/: {r.source}")
    if read_source is not None:
        previous = None
        for r in rows:
            data = read_source(r)
            if data == previous:
                raise HistoryError(f"{doc}: the revision dated {r.date} changes nothing")
            previous = data


def census(commits: list[Commit]) -> dict[str, int]:
    """What the coverage file records about history — counts only, no content.

    `documents_with_history` is the documents with more than one commit; the
    authority prior has nothing to read on the others.
    """
    commits_per_doc: dict[str, int] = {}
    authors_per_doc: dict[str, set[str]] = {}
    for c in commits:
        for r in c.revisions:
            commits_per_doc[r.path] = commits_per_doc.get(r.path, 0) + 1
            authors_per_doc.setdefault(r.path, set()).add(c.author)
    multi = [d for d, n in commits_per_doc.items() if n > 1]
    return {
        "documents_with_history": len(multi),
        "history_commits": sum(commits_per_doc[d] for d in multi),
        "history_authors": len({a for d in multi for a in authors_per_doc[d]}),
        "max_authors_per_document": max((len(authors_per_doc[d]) for d in multi), default=0),
    }
