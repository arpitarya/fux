"""Per-document field extraction — title, heading-derived phrases and the
tokenizer's per-field `terms`/`flen`. Extracted-mode law: every field is
*taken from* the document; nothing invented.

**No vectors, no codes, and no model** (2026-08-25, Arpit). Extraction is pure
tokenisation now: the embedding lane it used to feed was deleted with the
bundle, so this module has no dependency outside the analyzer.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from ..query.tokenize import tokenize
from .parse import ParsedDoc

MAX_PHRASES = 12  # headings only, not headings + first-sentence — the simpler
# of the handoff's two open options (§10), picked and recorded here / ADR-RECORD.

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Extracted:
    title: str
    phrases: list[str]
    #: raw term -> per-field tf, in `store.TF_FIELDS` order:
    #: (body, heading, title, path, ctx)
    terms: dict[str, tuple[int, ...]]
    #: per-field TOKEN COUNTS, same order. Replaces the committed `wlen`
    #: (W-76 Phase 1): `wlen` is a weighted sum of these, and committing it
    #: made a committed field a function of a tunable — ADR-TUNE decision 6.
    #: These are facts; the weighting happens at query time.
    flen: tuple[int, ...]


def extract_fields(rel_path: str, doc: ParsedDoc, enrichment: str = "") -> Extracted:
    headings = [m.group(2).strip() for m in _HEADING_RE.finditer(doc.body)]
    title = _title(doc.meta, headings, rel_path)
    phrases = headings[:MAX_PHRASES]

    # `title` now has its own field, so it is no longer folded into the
    # heading tokens. Under two fields it had to be (there was nowhere else to
    # put it); doing so now would double-count every title word.
    heading_tokens = tokenize(" ".join(headings))
    # Strip heading lines out of body text too — without this a heading's
    # words would count twice: once as heading tf, once as body tf, diluting
    # "heading match outranks body match".
    body_tokens = tokenize(_HEADING_RE.sub("", doc.body))
    title_tokens = tokenize(title)
    # Path segments and the split filename — "where is X" queries. The
    # analyzer's identifier splitting does the work here: `docs/adr-storage.md`
    # yields `docs`, `adr`, `storage`, `md`.
    path_tokens = tokenize(rel_path.replace("/", " ").replace(".", " "))
    # `ctx` — Phase 8's enrichment field. **Pinned TEXT, tokenized like any
    # other field**: by the time it reaches here a model has already run, in an
    # agent, in a separate command, and what fux consumes is a committed file.
    # Ingest stays a deterministic function of (sources union pinned
    # enrichment), which is L3 with a wider input rather than a weaker one.
    #
    # Empty when a document has no enrichment -- which is the steady state for
    # most corpora and costs nothing: a per-field count of 0 is a trailing zero
    # and is not written at all.
    ctx_tokens = tokenize(enrichment) if enrichment else []

    per_field = (body_tokens, heading_tokens, title_tokens, path_tokens, ctx_tokens)
    terms = _term_freqs(per_field)
    flen = tuple(len(tokens) for tokens in per_field)

    # `code` went in W-76 Phase 1, `vectors` on 2026-08-25 with the model.
    # Both were the dense lane's input, and the lane never earned its cost:
    # DENSE-CHUNK measured 0 fixed / 2 broken at every setting that fires.
    return Extracted(title=title, phrases=phrases, terms=terms, flen=flen)


def _title(meta: dict, headings: list[str], rel_path: str) -> str:
    front = meta.get("title")
    if isinstance(front, str) and front.strip():
        return front.strip()
    if headings:
        return headings[0]
    return rel_path.rsplit("/", 1)[-1]


def _term_freqs(per_field: tuple[list[str], ...]) -> dict[str, tuple[int, ...]]:
    """One tf tuple per term, in `store.TF_FIELDS` order.

    Trailing zeros are NOT trimmed here — `store.hash_terms` does that at the
    wire boundary, so exactly one place decides the encoding.
    """
    counters = [Counter(tokens) for tokens in per_field]
    vocabulary: set[str] = set()
    for counter in counters:
        vocabulary |= counter.keys()
    return {term: tuple(counter[term] for counter in counters) for term in vocabulary}



