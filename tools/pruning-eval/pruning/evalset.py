"""Eval-set construction for the long-document corpora, and its honest biases.

There are no human relevance judgments for RFCs or for this repo's own docs, so
queries are derived from the documents themselves, with the source document as
gold. That is a real limitation and it is *shaped*, not uniform — so the set is
built in two kinds and reported separately:

* **`abstract`** — a sentence lifted from the document's abstract or opening
  prose. Body text: **no rule guarantees these terms survive**, so this slice
  is neutral across the five arms. It is the slice the gate is registered on.

* **`heading`** — a section heading. Rule A keeps every heading term *by
  construction*, so arms containing Rule A are flattered here. Reported as a
  diagnostic, never as the gate. Naming the bias is the point: the previous
  run's failure was an unstated assumption, not a wrong number.

Deterministic throughout: documents in sorted order, seeded sampling, no
wall-clock. Queries are lowercased and tokenized by the archived tokenizer at
scoring time, so nothing here depends on the scorer's internals.
"""

from __future__ import annotations

import random
import re

__all__ = ["rfc_queries", "markdown_queries", "EvalQuery"]

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"[a-z0-9_]+")

# RFC section headings: "1. Introduction", "2.1.3 Message Format", "Appendix A."
_RFC_HEADING = re.compile(r"^\s{0,3}((?:\d+\.)+\d*|Appendix\s+[A-Z]\.?)\s+(\S.*?)\s*$")
_MD_HEADING = re.compile(r"^#{1,6}\s+(\S.*?)\s*$")

# Structural boilerplate that identifies no document in particular.
_STOP_QUERIES = {
    "introduction", "conclusion", "abstract", "overview", "terminology",
    "security considerations", "iana considerations", "references",
    "normative references", "informative references", "acknowledgements",
    "acknowledgments", "table of contents", "status of this memo",
    "copyright notice", "author's address", "authors' addresses",
    "conventions used in this document", "requirements language",
    "background", "motivation", "summary", "context", "scope", "notes",
    "definitions", "examples", "appendix", "glossary", "changelog",
}

_MIN_TOKENS, _MAX_TOKENS = 4, 16


class EvalQuery:
    __slots__ = ("text", "gold", "kind")

    def __init__(self, text: str, gold: str, kind: str):
        self.text = text
        self.gold = gold
        self.kind = kind


def _ok(text: str) -> bool:
    lowered = text.strip().lower().rstrip(".")
    if lowered in _STOP_QUERIES:
        return False
    tokens = _WORD.findall(lowered)
    if not (_MIN_TOKENS <= len(tokens) <= _MAX_TOKENS):
        return False
    # A query of pure digits/section numbers identifies nothing.
    return sum(1 for t in tokens if not t.isdigit()) >= _MIN_TOKENS


def _rfc_abstract(lines: list[str]) -> list[str]:
    """Sentences from the Abstract section, or the first prose block."""
    start = None
    for i, line in enumerate(lines):
        if line.strip().lower() in ("abstract", "abstract."):
            start = i + 1
            break
    if start is None:
        return []
    body: list[str] = []
    for line in lines[start:start + 60]:
        stripped = line.strip()
        if not stripped:
            if body:
                break
            continue
        if _RFC_HEADING.match(line) or stripped.lower().startswith(
            ("status of this memo", "table of contents", "copyright")
        ):
            break
        body.append(stripped)
    return [s.strip() for s in _SENT_SPLIT.split(" ".join(body)) if s.strip()]


def _rfc_headings(lines: list[str]) -> list[str]:
    out = []
    for line in lines:
        m = _RFC_HEADING.match(line)
        if m:
            out.append(m.group(2))
    return out


def rfc_queries(doc_id: str, text: str, rng: random.Random,
                per_doc: int = 1) -> list[EvalQuery]:
    """Up to ``per_doc`` of each kind for one RFC."""
    lines = text.splitlines()
    out: list[EvalQuery] = []
    for kind, candidates in (
        ("abstract", [s for s in _rfc_abstract(lines) if _ok(s)]),
        ("heading", [h for h in _rfc_headings(lines) if _ok(h)]),
    ):
        if not candidates:
            continue
        picks = rng.sample(candidates, k=min(per_doc, len(candidates)))
        for text_ in picks:
            out.append(EvalQuery(" ".join(_WORD.findall(text_.lower())), doc_id, kind))
    return out


def markdown_queries(doc_id: str, text: str, rng: random.Random,
                     per_doc: int = 1) -> list[EvalQuery]:
    """The same two kinds for a Markdown document.

    ``abstract`` is the first prose paragraph after any frontmatter and title —
    the document's own opening statement, which is the closest analogue to an
    RFC abstract.
    """
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":  # skip YAML frontmatter
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                lines = lines[i + 1:]
                break
    prose: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", ">", "-", "*", "|", "`", "!")):
            if prose:
                break
            continue
        prose.append(stripped)
        if len(" ".join(prose)) > 400:
            break
    out: list[EvalQuery] = []
    for kind, candidates in (
        ("abstract", [s for s in _SENT_SPLIT.split(" ".join(prose)) if _ok(s)]),
        ("heading", [m.group(1) for line in lines
                     if (m := _MD_HEADING.match(line)) and _ok(m.group(1))]),
    ):
        if not candidates:
            continue
        for text_ in rng.sample(candidates, k=min(per_doc, len(candidates))):
            out.append(EvalQuery(" ".join(_WORD.findall(text_.lower())), doc_id, kind))
    return out
