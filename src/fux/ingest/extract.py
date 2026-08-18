"""Per-document field extraction — title, heading-derived phrases, the
tokenizer's `terms`/`wlen`, and FuxVec's `code`. Extracted-mode law: every
field is *taken from* the document; nothing invented.
"""

from __future__ import annotations

import base64
import re
from collections import Counter
from dataclasses import dataclass

from ..embed import get_model, quantize
from ..query.tokenize import tokenize
from .parse import ParsedDoc

HEADING_WEIGHT = 3
BODY_WEIGHT = 1
MAX_PHRASES = 12  # headings only, not headings + first-sentence — the simpler
# of the handoff's two open options (§10), picked and recorded here / ADR-RECORD.

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Extracted:
    title: str
    phrases: list[str]
    terms: dict[str, tuple[int, int]]  # raw term -> (tf_heading, tf_body)
    wlen: int
    code: str | None  # base64url, no padding; None when nothing embeddable


def extract_fields(rel_path: str, doc: ParsedDoc) -> Extracted:
    headings = [m.group(2).strip() for m in _HEADING_RE.finditer(doc.body)]
    title = _title(doc.meta, headings, rel_path)
    phrases = headings[:MAX_PHRASES]

    # `title` often *is* headings[0] (the fallback case) — don't double-count
    # it into tf_heading when that happens.
    heading_sources = headings if title in headings else [*headings, title]
    heading_tokens = tokenize(" ".join(heading_sources))
    # Strip heading lines out of body text too — there's no chunker yet (M4),
    # but without this a heading's words would count twice: once as heading
    # tf, once as body tf, diluting "heading match outranks body match".
    body_tokens = tokenize(_HEADING_RE.sub("", doc.body))
    terms = _term_freqs(heading_tokens, body_tokens)
    wlen = HEADING_WEIGHT * len(heading_tokens) + BODY_WEIGHT * len(body_tokens)

    return Extracted(title=title, phrases=phrases, terms=terms, wlen=wlen, code=_fuxvec_code(title, doc.body))


def _title(meta: dict, headings: list[str], rel_path: str) -> str:
    front = meta.get("title")
    if isinstance(front, str) and front.strip():
        return front.strip()
    if headings:
        return headings[0]
    return rel_path.rsplit("/", 1)[-1]


def _term_freqs(heading_tokens: list[str], body_tokens: list[str]) -> dict[str, tuple[int, int]]:
    h, b = Counter(heading_tokens), Counter(body_tokens)
    return {term: (h[term], b[term]) for term in h.keys() | b.keys()}


def _fuxvec_code(title: str, body: str) -> str | None:
    model = get_model()
    if model is None:  # bundle not present (e.g. sdist without the wheel's data file)
        return None
    vec = model.embed(f"{title}\n{body}")
    if vec is None:
        return None
    return base64.urlsafe_b64encode(quantize(vec)).rstrip(b"=").decode("ascii")
