"""`fux correct` — a human's own question, written onto the document's record.

## What this is, in one paragraph

For a question the corpus answers, fux served the wrong document. The durable
fix is **the words people actually ask with, on the document that answers**:
`fux correct "<question>" <doc>` appends that question to the document's
existing enrichment file, where it is indexed as `ctx` exactly like the
model-written questions beside it. Same file, same field, **different author**.
Accepted by Arpit on 2026-09-13 —
[the compare doc](../../work/compare/fux-correct.compare.md).

**It is the deterministic cousin of doc2query** (Nogueira, Yang, Lin and Cho,
*Document expansion by query prediction*, 2019), which is what `fux enrich`
already does. A correction is **the eleventh line, in a human's handwriting** —
and it is the highest-value line the file can hold, because it is the question
that actually failed.

## Four things this module refuses to do, and why each one matters

- **It never learns from what anyone clicked.** L8 forbids a committed use
  record and L3 forbids a model in the maintenance path. A correction is a
  **signed human edit in a diff**, which is the opposite thing: somebody
  decided it, in public, and a reviewer can disagree.
- **It refuses a negative correction.** *"Don't serve X for this"* is not a
  correction, it is a **supersession or an archive decision**, and it is
  corpus-wide rather than per-query — `supersedes` or `archived=`. A per-query
  demotion is the rule that rots silently: it keeps working long after the
  reason for it is gone, and nothing ever says so.
- **It writes no date of its own.** `generated:` for a file this command
  creates is derived from **the document's own committed `mtime`**, never from
  the wall clock — L3's rule as
  [CLAUDE.md](../../CLAUDE.md) §Hard-won states it. Two runs of this command a
  week apart on an unchanged document produce byte-identical bytes.
- **It changes no ranking weight.** A correction bites because `ctx` is already
  indexed and already weighted. **Raising `ctx`'s weight so corrections bite
  harder is a ranking change** and goes through
  [W-156](../../work/open/W-156-prevalence-outside-golden.md)'s rule, not
  through this module.

## The marker: frontmatter counts, the body carries

A human line has to be **indexed** (or it corrects nothing) and **identifiable**
(or regeneration eats it). Those pull in opposite directions, because
[SR-ENRICH](../../records/0137_enrich.md) decision 8 strips the frontmatter
before indexing. So:

- **the question is a plain body line** — it reaches `ctx` like any other;
- **`corrections: N` in the frontmatter** says *the last N body lines are
  human*. The marker is in the half that is never indexed, so it adds no
  vocabulary; the text is in the half that is.

⚠ **`.fux/eval/corrections.tsv` is the durable record, not the marker.** A
regenerating agent rewrites the enrichment file wholesale, frontmatter
included, so the marker cannot survive on its own — and `fux enrich --check`
compares the eval file against the enrichment files and **names every
correction whose line has gone missing**. That is the half fux can actually
enforce; the marker is what makes a diff readable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .errors import FuxError

__all__ = [
    "Correction",
    "CORRECTIONS_FILE",
    "cmd_correct",
    "human_lines",
    "load_corrections",
    "normalise",
    "pinned_for",
    "save_corrections",
]

#: Committed — **it is the human's own claim, not a record of use** (L8). A
#: correction says *this question should reach this document*; nothing here
#: says anybody ran a query.
CORRECTIONS_FILE = ".fux/eval/corrections.tsv"

#: The frontmatter key that says how many trailing body lines are human.
CORRECTIONS_KEY = "corrections"

#: What this command stamps into a file it creates itself. `model:` is a
#: **claim about what produced the text** (SR-ENRICH), and the honest claim
#: for a line a person typed is that no model did.
HUMAN_MODEL = "none (human correction)"
HUMAN_SKILL = "fux-correct@1"

#: 🔴 **A negative correction is refused, and this is the whole test.** Phrases
#: a person reaches for when they mean *stop serving this*, which is a
#: corpus-wide decision and not a question. Deliberately shallow: a cleverer
#: classifier would refuse sentences somebody wrote on purpose, and the remedy
#: for a false refusal — rephrase as the question you would type — is the thing
#: the verb wants anyway.
_NEGATIVE = re.compile(
    # A negation, then a SERVING verb within two words — which is how English
    # says it: *stop ranking*, *don't serve*, *never show*.
    #
    # ⚠ **Two deliberate narrowings, and both were widenings first.**
    # `\brank\b` missed *stop RANKING* (the stem takes a suffix), so the verbs
    # match a stem with any ending. And a 40-character gap with `use` in the
    # verb list fired on *"how do I stop the supervisor and use the rollback
    # script"* — an ordinary question. Two words and no `use`: the negation has
    # to be ABOUT the serving verb, not merely in the same sentence as one.
    r"\b(?:don'?t|do not|does not|never|stop|avoid|exclude)\s+(?:\w+\s+){0,2}"
    r"(?:serv|show|return|rank|surfac|display)\w*"
    r"|\binstead of\b|\bnot this\b|\bwrong (?:doc|document|answer|result)\b",
    re.I,
)


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
    from .query.tokenize import tokenize

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
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        question, doc_id, loc, source_sha = parts[:4]
        pin = len(parts) > 4 and parts[4].strip() == "1"
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
    "# (L8): a row says *this question should reach this document*, never that\n"
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
        from .store import read_index

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
        from .store import read_index

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
    from .enrich import match_end, parse_frontmatter

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
    from .enrich import match_end

    body = [line.strip() for line in text[match_end(text):].splitlines() if line.strip()]
    human = human_lines(text)
    return body[: len(body) - len(human)] if human else body


def _append_human_line(text: str, question: str) -> str:
    """The file with `question` appended as a human body line, marker bumped."""
    from .enrich import match_end

    end = match_end(text)
    front, body = text[:end], text[end:]
    existing = len(human_lines(text))
    if not body.endswith("\n") and body:
        body += "\n"
    body += question.strip() + "\n"
    front = _set_frontmatter_key(front, CORRECTIONS_KEY, str(existing + 1))
    return front + body


def _set_frontmatter_key(front: str, key: str, value: str) -> str:
    """Replace or append one `key: value` line inside a frontmatter block.

    Written by hand rather than through a YAML writer for the reason
    `enrich.parse_frontmatter` is a hand parser: the key set is closed and flat,
    and adopting a dependency to write one line is the L1 trade this design
    refuses. **The block's other lines are left byte-identical**, because this
    file is prose a human reviews in a diff.
    """
    lines = front.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.split(":", 1)[0].strip() == key:
            lines[i] = f"{key}: {value}\n"
            return "".join(lines)
    # Before the closing `---`, which is the last line of the block.
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == "---":
            lines.insert(i, f"{key}: {value}\n")
            return "".join(lines)
    return "".join(lines)


def _new_file(loc: str, sha: str, chunks: int, generated: str, question: str) -> str:
    """A fresh enrichment file holding one human question and nothing invented.

    Every frontmatter value is **derived**: `source` and `source_sha` from the
    record, `chunks` from the chunker, `generated` from the document's own
    committed `mtime`. Nothing here reads a clock.
    """
    return (
        "---\n"
        f"source: {loc}\n"
        f"source_sha: {sha}\n"
        f"chunks: {chunks}\n"
        f"model: {HUMAN_MODEL}\n"
        f"generated: {generated}\n"
        f"skill: {HUMAN_SKILL}\n"
        f"{CORRECTIONS_KEY}: 1\n"
        "---\n"
        f"{question.strip()}\n"
    )


# --------------------------------------------------------------------------
# the verb
# --------------------------------------------------------------------------


def _root() -> Path:
    from .config import find_root

    root = find_root()
    if root is None:
        raise FuxError("no fux.toml or .git found — run from inside a configured repo")
    return root


def _resolve(root: Path, given: str) -> tuple[str, dict]:
    """`(doc id, record)` for a `loc` or an id. Refuses anything else by name."""
    from .store import read_index

    records = read_index(root)
    doc_id = given if given.startswith(("file:", "url:")) else f"file:{given}"
    record = records.get(doc_id)
    if record is None:
        raise FuxError(
            f"{given!r} is not in the index. `fux find` locates a document and prints "
            f"the `loc` to paste here; `fux add` puts one in. "
            f"(Looked for {doc_id!r}.)"
        )
    return doc_id, record


def _generated_from(record: dict) -> str:
    """`YYYY-MM-DD` from the document's committed `mtime`, or `unknown`.

    🔴 **Never `date.today()`.** A command on the maintenance path that stamps
    the wall clock makes its own output non-reproducible, and CLAUDE.md's rule
    is explicit: timestamps derive from `SOURCE_DATE_EPOCH` or the source's
    mtime. The record's `mtime` IS the source's mtime, already committed and
    already derived from git — so two runs of `fux correct` a week apart on an
    unchanged document write identical bytes.

    `unknown` for a document outside git history, which is honest and is what
    `mtime: null` already means everywhere else in this engine.
    """
    from datetime import datetime, timezone

    mtime = record.get("mtime")
    if not isinstance(mtime, int):
        return "unknown"
    return datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d")


def _refuse_negative(question: str) -> None:
    if _NEGATIVE.search(question):
        raise FuxError(
            "that reads as a negative correction — *stop serving this* rather than a "
            "question somebody would type. `fux correct` adds the words people ASK "
            "with to the document that answers; it cannot demote a document for one "
            "query.\n"
            "  If a document is retired, say so where it is corpus-wide: "
            "`supersedes:` on the successor (or `superseded_by:` in the retired "
            "document's enrichment frontmatter), or `archived=true` on its "
            "`.fux/sources/dirs` line.\n"
            "  If it is simply the wrong answer, correct the RIGHT document instead: "
            "`fux correct \"<the question>\" <the document that answers it>`."
        )


def _refuse_pii(root: Path, question: str) -> None:
    """Refuse a question a `pii.toml` rule fires on, naming the rule.

    **Refuse rather than redact**, exactly as `fux enrich --check` does: a
    redacted question indexes `[PII:email]` as vocabulary and retrieves
    nothing, so redaction is not the remedy here. The remedy is to write the
    question without the value, and only a person can do that.
    """
    from .ingest import pii as pii_mod

    try:
        rules = pii_mod.load(root)
    except FuxError:
        raise
    if not rules:
        return
    _redacted, hits = pii_mod.redact(rules, question)
    if hits:
        named = ", ".join(sorted(hits))
        raise FuxError(
            f"the question matches `.fux/pii.toml` rule(s): {named}. A correction is "
            "COMMITTED and INDEXED, so the value would travel twice — in the file "
            "every clone gets, and as a term in `.fux/index/`. Redacting it is not "
            "the fix: `[PII:...]` as vocabulary retrieves nothing. Write the question "
            "without the value."
        )


def cmd_correct(args) -> int:
    """`fux correct "<question>" <doc>` — and `--reaffirm`, and `--list`."""
    import json as json_mod

    from .enrich import enrich_path, validate

    root = _root()
    as_json = bool(getattr(args, "json", False))

    if getattr(args, "list", False):
        rows = load_corrections(root)
        if as_json:
            print(
                json_mod.dumps(
                    {
                        "corrections": [
                            {
                                "question": c.question,
                                "doc": c.loc,
                                "id": c.doc_id,
                                "source_sha": c.source_sha,
                                "pin": c.pin,
                            }
                            for c in rows
                        ],
                        "suspended": [
                            {"question": c.question, "doc": c.loc, "why": why}
                            for c, why in suspended_pins(root)
                        ],
                    },
                    indent=2,
                )
            )
            return 0
        if not rows:
            print("No corrections filed.")
            return 0
        for c in rows:
            print(f"{'pin ' if c.pin else '    '}{c.loc}  {c.question}")
        for c, why in suspended_pins(root):
            print(f"warn: the pin for {c.loc!r} is SUSPENDED — {why}")
        return 0

    if not getattr(args, "question", None) or not getattr(args, "doc", None):
        raise FuxError(
            'fux correct needs a question and a document: '
            'fux correct "how do I roll back a release?" docs/runbook-rollback.md'
        )

    question = " ".join(args.question.split())
    if not question:
        raise FuxError("the question is empty")
    _refuse_negative(question)
    _refuse_pii(root, question)

    doc_id, record = _resolve(root, args.doc)
    sha = record.get("sha", "")
    if not sha:
        raise FuxError(f"{doc_id} carries no content sha, so nothing can be pinned to it")

    path = enrich_path(root, sha)
    reason = validate(path, expected_sha=sha) if path.is_file() else "absent"
    if path.is_file() and reason is not None:
        raise FuxError(
            f"{path} exists and is not a usable enrichment file: {reason}. "
            "Fix it (or delete it and let `fux enrich` rewrite it) before correcting — "
            "appending to a file fux will not index corrects nothing."
        )

    # 🔴 **Every refusal happens BEFORE any write, and the ordering is a fix
    # rather than a style.** The first cut decided the eval row after writing
    # the enrichment file, so a refused `fux correct` printed
    # `wrote .fux/enrich/<sha>.md` and then `error:` — a command that exited 1
    # having already changed the repository. Caught by running the suspended-pin
    # path, not by a test.
    pin = bool(getattr(args, "pin", False))
    rows = load_corrections(root)
    entry = Correction(question, doc_id, record.get("loc", ""), sha, pin)
    existing = {c.key: c for c in rows}
    if entry.key in existing:
        previous = existing[entry.key]
        # `pin` is raised by `--pin` and lowered only by `--no-pin`, so a plain
        # re-run cannot quietly drop somebody's pin.
        keep_pin = pin or (previous.pin and not getattr(args, "no_pin", False))
        # 🔴 **A SUSPENDED pin is not released by re-running the command.** The
        # document changed after a person pinned a question to it, so the pin
        # is a claim nobody has checked since; re-filing it as a side effect of
        # typing the same command again would make *suspended* mean nothing.
        # `--reaffirm` is a human saying *still true*, and it is the only thing
        # that moves the stored sha for a pin.
        if keep_pin and previous.source_sha != sha and not getattr(args, "reaffirm", False):
            raise FuxError(
                f"that pin is SUSPENDED: {previous.loc} has changed since it was made "
                f"(pinned against {previous.source_sha[:12]}, now {sha[:12]}).\n"
                "  Read the document, then `fux correct --reaffirm "
                f'"{entry.question}" {entry.loc}` if it still answers the question.\n'
                "  `fux correct --no-pin \u2026` keeps the correction and drops the pin. "
                "The correction's vocabulary effect is unaffected either way — the "
                "question is still the question somebody asks."
            )
        stored_sha = sha if (getattr(args, "reaffirm", False) or not keep_pin) else previous.source_sha
        entry = Correction(entry.question, entry.doc_id, entry.loc, stored_sha, keep_pin)
        rows = [c for c in rows if c.key != entry.key]
    rows.append(entry)

    # Nothing above this line has written a byte.
    if path.is_file():
        text = path.read_text(encoding="utf-8")
        if question in human_lines(text) or question in model_lines(text):
            print(f"already there: {path.relative_to(root).as_posix()} carries that question")
        else:
            path.write_text(_append_human_line(text, question), encoding="utf-8")
            print(f"appended to {path.relative_to(root).as_posix()} (human line)")
    else:
        from .enrich import _chunk_count

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            _new_file(
                record.get("loc", ""),
                sha,
                _chunk_count(root, record),
                _generated_from(record),
                question,
            ),
            encoding="utf-8",
        )
        print(f"wrote {path.relative_to(root).as_posix()} (human line)")

    save_corrections(root, rows)
    print(f"filed in {CORRECTIONS_FILE}" + (" · PINNED" if entry.pin else ""))
    print("next: `fux ingest` to index it, then ask the question again")
    return 0
