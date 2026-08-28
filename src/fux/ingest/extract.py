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

#: Markdown, and the default for every type without its own grammar.
#: The `text` group name is shared by all four patterns so the caller
#: never branches on which one matched.
_HEADING_RE = re.compile(r"^(#{1,6})\s+(?P<text>.+?)\s*$", re.MULTILINE)

# -- W-86 P0: the three allowed types whose headings reached nothing ---------
#
# `DEFAULT_TYPES` has admitted `.rst`, `.adoc` and `.org` since the allowlist
# shipped, and `_HEADING_RE` knows only `#`. **Every heading in those three
# formats landed in the body field**, and their `phrases` list — what `fux ask`
# renders as `§` lines — was empty. Three of six allowed types, silently, for
# as long as the filter has existed.
#
# Each grammar below is the format's own, not an approximation:

#: reStructuredText: a title line followed by a full-width run of one punctuation
#: character. The underline must be at least as long as the text — that is the
#: spec's rule and it is what stops a row of dashes in a table being read as one.
_RST_RE = re.compile(
    r"""^(?P<text>\S[^\n]*)\n(?P<ch>[=\-`:'"~^_*+#<>])(?P=ch){2,}[ \t]*$""",
    re.MULTILINE,
)

#: AsciiDoc: `= Title`, `== Section`. Same shape as Markdown with `=`, and the
#: level is the run length, so `==` is a section rather than a document title.
_ADOC_RE = re.compile(r"^(={1,6})\s+(?P<text>\S[^\n]*?)\s*$", re.MULTILINE)

#: Org-mode: `* Heading`, `** Subheading`. ⚠ The trailing space is required —
#: without it a line of `*emphasis*` or a `**bold**` fragment at the start of a
#: line reads as a heading, which is the false-positive this format invites.
_ORG_RE = re.compile(r"^(\*{1,6})[ \t]+(?P<text>\S[^\n]*?)\s*$", re.MULTILINE)

#: extension -> its heading pattern. Markdown's is applied to everything else,
#: including `.txt`, because a `#` line in a text file is a heading by intent
#: far more often than it is prose.
_GRAMMARS: dict[str, re.Pattern] = {
    ".rst": _RST_RE,
    ".adoc": _ADOC_RE,
    ".asciidoc": _ADOC_RE,
    ".org": _ORG_RE,
}


def _grammar(rel_path: str) -> re.Pattern:
    dot = rel_path.rfind(".")
    slash = max(rel_path.rfind("/"), rel_path.rfind("\\"))
    ext = rel_path[dot:].lower() if dot > slash + 1 else ""
    return _GRAMMARS.get(ext, _HEADING_RE)


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
    # W-86 P0: the heading grammar follows the file type. A decoded document
    # always arrives as Markdown (ADR-DECODE decision 2), so only an
    # already-prose `.rst`/`.adoc`/`.org` takes a different pattern.
    grammar = _grammar(rel_path)
    headings = [m.group("text").strip() for m in grammar.finditer(doc.body)]
    title = _title(doc.meta, headings, rel_path)
    phrases = headings[:MAX_PHRASES]

    # `title` now has its own field, so it is no longer folded into the
    # heading tokens. Under two fields it had to be (there was nowhere else to
    # put it); doing so now would double-count every title word.
    heading_tokens = tokenize(" ".join(headings))
    # Strip heading lines out of body text too — without this a heading's
    # words would count twice: once as heading tf, once as body tf, diluting
    # "heading match outranks body match".
    body_tokens = tokenize(grammar.sub("", doc.body))
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



