"""The corrections file and the human half of an enrichment file — read side.

Core layer (W-282): `fux correct` (the writer) files corrections, and the
ranker (the reader) applies pins and reads provenance from them, so the file
format lives here and neither side imports the other. The verb, its refusals
and everything that WRITES an enrichment file stay in `correct.py`
([SR-ENRICH](../../../records/0137_enrich.md)).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..constants import fixed

#: Committed — **it is the human's own claim, not a record of use** (L9). A
#: correction says *this question should reach this document*; nothing here
#: says anybody ran a query.
CORRECTIONS_FILE = fixed("files", "corrections")

#: The frontmatter key that says how many trailing body lines are human.
CORRECTIONS_KEY = "corrections"

@dataclass(frozen=True)
class Correction:
    """One row of `.fux/eval/corrections.tsv`.

    `source_sha` is the document's content sha **as the corrector saw it**. It
    is what suspends a pin when the document changes, and it is deliberately
    not refreshed silently: a person asserted this question about *that*
    version, and re-asserting it is `--reaffirm`.
    """

    question: str
    doc_id: str
    loc: str
    source_sha: str
    pin: bool = False

    def as_row(self) -> str:
        return "\t".join(
            (self.question, self.doc_id, self.loc, self.source_sha, "1" if self.pin else "0")
        )

    @property
    def key(self) -> tuple[str, str]:
        """Identity: one question per document. A second `fux correct` with the
        same pair updates the row rather than appending a duplicate."""
        return (normalise(self.question), self.doc_id)


def normalise(question: str) -> str:
    """The analyzed form of a question — what a pin matches on.

    **The ANALYZER, not `lower().strip()`.** A pin has to fire for *"How do I
    roll back a release?"* and *"how do i roll back releases"* alike, and the
    only thing in this engine that already knows those are the same question is
    the analyzer the index was built with. Matching on raw text would make a
    pin fire for one capitalisation and not the next, which is the brittleness
    the compare doc's option (a) was nearly rejected for.
    """
    from ..text.tokenize import tokenize

    return " ".join(tokenize(question))


# --------------------------------------------------------------------------
# the eval file
# --------------------------------------------------------------------------


def corrections_path(root: Path) -> Path:
    return root / CORRECTIONS_FILE


def load_corrections(root: Path) -> list[Correction]:
    """Every filed correction, in file order. `[]` when there is no file.

    **Never raises for a malformed row** — it skips it. This file is read on
    the query path when a pin might apply, and a hand-edited tab would
    otherwise take out `fux ask` for everyone in the repository. A row fux
    cannot read is reported by `fux doctor`, which is where a report belongs.
    """
    path = corrections_path(root)
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    out: list[Correction] = []
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        try:
            question, doc_id, loc, source_sha, *rest = line.split("\t")
        except ValueError:
            continue  # fewer than the four required columns
        pin = bool(rest) and rest[0].strip() == "1"
        out.append(Correction(question, doc_id, loc, source_sha, pin))
    return out


def save_corrections(root: Path, corrections: list[Correction]) -> Path:
    """Write the file, **sorted**, with its header.

    Sorted by `(doc_id, normalised question)` rather than kept in insertion
    order: this file is committed and reviewed in a diff, and an append-ordered
    file makes every correction's diff depend on when it was filed. Sorted, a
    new row lands next to its siblings.
    """
    path = corrections_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(corrections, key=lambda c: (c.doc_id, normalise(c.question), c.question))
    body = "".join(row.as_row() + "\n" for row in rows)
    path.write_text(_HEADER + body, encoding="utf-8")
    return path


_HEADER = (
    "# fux corrections — one human-authored question per line, TAB separated.\n"
    "# question\tdoc_id\tloc\tsource_sha\tpin\n"
    "#\n"
    "# COMMITTED, and it is the human's own claim rather than a record of use\n"
    "# (L9): a row says *this question should reach this document*, never that\n"
    "# anybody ran a query. Written by `fux correct`; sorted, so a review diff\n"
    "# does not depend on the order corrections were filed.\n"
    "#\n"
    "# `source_sha` is the document as the CORRECTOR saw it. A `pin` whose\n"
    "# document has changed since is SUSPENDED until `fux correct --reaffirm`;\n"
    "# the vocabulary effect never suspends, because the question is still the\n"
    "# question somebody asks.\n"
)


# --------------------------------------------------------------------------
# pins
# --------------------------------------------------------------------------


def pinned_for(root: Path, query: str, records: dict | None = None) -> str | None:
    """The doc id pinned to this exact question, or `None`.

    **Exact on the ANALYZED form, and exact is the whole point** — a pin is the
    editorial escape hatch for one phrasing that has to work, not a ranking
    rule. Anything that generalised would be the vocabulary effect, which is
    what the body line already does.

    ⚠ **A pin whose document's content sha has moved is SUSPENDED, not
    applied.** The person pinned a question to a version of a document; a
    rewritten document may no longer answer it. `fux doctor` names every
    suspended pin, and `fux correct --reaffirm` is how a human says *still
    true*. **Never re-affirmed automatically** — that would make the pin a
    claim nobody has checked since the day it was made.
    """
    pins = [c for c in load_corrections(root) if c.pin]
    if not pins:
        return None
    wanted = normalise(query)
    if not wanted:
        return None
    if records is None:
        from .reader import read_index

        try:
            records = read_index(root)
        except Exception:  # pragma: no cover - a query must not die on this
            return None
    for correction in pins:
        if normalise(correction.question) != wanted:
            continue
        record = records.get(correction.doc_id)
        if record is None:
            continue  # the document left the corpus; the pin cannot apply
        if record.get("sha", "") != correction.source_sha:
            continue  # suspended — doctor reports it
        return correction.doc_id
    return None


def suspended_pins(root: Path, records: dict | None = None) -> list[tuple[Correction, str]]:
    """`(correction, why)` for every pin that is not currently applying.

    `fux doctor`'s row reads this. Three reasons, each a different remedy, so
    they are named rather than collapsed into *not applying*.
    """
    pins = [c for c in load_corrections(root) if c.pin]
    if not pins:
        return []
    if records is None:
        from .reader import read_index

        try:
            records = read_index(root)
        except Exception:
            return []
    out: list[tuple[Correction, str]] = []
    for correction in pins:
        record = records.get(correction.doc_id)
        if record is None:
            out.append((correction, "its document is no longer in the index"))
        elif record.get("sha", "") != correction.source_sha:
            out.append((correction, "its document changed since the pin was made"))
    return out


# --------------------------------------------------------------------------
# the enrichment file's human half
# --------------------------------------------------------------------------


def human_lines(text: str) -> list[str]:
    """The human-authored body lines of an enrichment file, in file order.

    Read from `corrections: N` in the frontmatter — *the last N body lines* —
    and `[]` when the key is absent or unreadable. **Never guessed from the
    text**: there is nothing in a question that says who wrote it, and a
    heuristic here would attribute a model's line to a person in a provenance
    field.
    """
    from .enrichfile import match_end, parse_frontmatter

    meta = parse_frontmatter(text) or {}
    raw = meta.get(CORRECTIONS_KEY, "")
    try:
        count = int(str(raw).strip())
    except (TypeError, ValueError):
        return []
    if count <= 0:
        return []
    body = [line.strip() for line in text[match_end(text):].splitlines() if line.strip()]
    return body[-count:] if count <= len(body) else body


def model_lines(text: str) -> list[str]:
    """The body lines `human_lines` does not claim — everything else."""
    from .enrichfile import match_end

    body = [line.strip() for line in text[match_end(text):].splitlines() if line.strip()]
    human = human_lines(text)
    return body[: len(body) - len(human)] if human else body
