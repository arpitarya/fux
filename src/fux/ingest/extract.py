"""Per-document field extraction — title, heading-derived phrases and the
tokenizer's per-field `terms`/`flen`. Extracted-mode law: every field is
*taken from* the document; nothing invented.

**No vectors, no codes, and no model** (2026-08-25, Arpit). Extraction is pure
tokenisation now: the embedding lane it used to feed was deleted with the
bundle, so this module has no dependency outside the analyzer.
"""

from __future__ import annotations



#: **The reuse key's handle on THIS module** (W-166). Ingest reuses a document's
#: extracted record when its source bytes are unchanged; the rules in this file
#: are the other input, and they were not in the key. SR-INGEST's Consequences
#: said so from the start — *"a new extraction rule does not reach an unchanged
#: document until that document changes or `--full` runs"* — and filed it as the
#: carry-forward's defining property rather than as a thing to fix.
#:
#: **Bump it by hand in the same change as any edit that can change what this
#: module returns**, and the next `fux ingest` re-extracts every document.
#: Leaving it alone is the claim that the edit cannot move a byte of output — a
#: comment, a docstring, a renamed local.
#:
#: ⚠ **This one is corpus-wide, unlike the decoder digests**, and that asymmetry
#: is deliberate rather than an oversight. A decoder is bound to an extension, so
#: the documents it read are identifiable; these rules run on every document
#: fux extracts, so there is no smaller set to invalidate. A bump costs one full
#: re-extraction — which is why it is a constant somebody bumps rather than a
#: sha of this file, whose every whitespace edit would charge that price.
#:
#: `tests/ingest/test_extract_rules_version.py` fails on a working tree that
#: changed this module and did not bump this constant.
#:
#: **2 (2026-09-21, W-205 part 1):** front-matter identity values now reach the
#: field the resolver chooses, so **every document with front-matter produces
#: different fields than it did at version 1** — and the corpus-wide bump is
#: exactly right here, because front-matter is not bound to an extension.
RULES_VERSION = 2

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from ..decode._markdown import headings as _md_headings
from ..decode._markdown import strip_headings as _md_strip_headings
from ..query.tokenize import tokenize
from .parse import ParsedDoc, meta_fields

#: The cap on `phrases` is `.fux/tune.toml [index] max_phrases` (default
#: `tune.DEFAULT_MAX_PHRASES`, 32), passed in by `ingest/run.py`. It was a
#: hard-coded 12 until 2026-09-11. Headings only, not headings + first
#: sentence — the simpler of the original handoff's two options (SR-EXTRACTED).
#: ⚠ **The cap truncates DISPLAY, never ranking**: `heading` tf below is built
#: from every heading, so a heading past the cap still ranks.

#: Markdown is NOT here. Its grammar moved to `decode/_markdown.py` on
#: 2026-09-06, because a regex cannot see a code fence and this one did not:
#: a `# Install dependencies` line inside a ```bash block was counted as a
#: heading, given heading-field weight, published in `phrases` where `fux ask`
#: renders it as a `§` line, and **removed from the body**. Every SR in this
#: repository contains such a block. `refer/_chunk.py` reads the same module,
#: so the two planes can no longer disagree about what a heading is.
#:
#: The `text` group name is still shared by all three patterns below, so the
#: caller never branches on which one matched.

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

#: extension -> its heading pattern. A `None` result means Markdown, which is
#: applied to everything else — including `.txt`, because a `#` line in a text
#: file is a heading by intent far more often than it is prose, and including
#: every decoded document, which is Markdown by construction (SR-DECODE
#: decision 2).
#:
#: ⚠ **These three keep regexes and get no fence handling.** Their heading
#: syntax is not Markdown's and neither is their code-block convention (`::`
#: plus indentation, `----`, `#+BEGIN_SRC`). Bringing them under one scanner is
#: a separate change with its own risk, and no decoder emits them.
_GRAMMARS: dict[str, re.Pattern] = {
    ".rst": _RST_RE,
    ".adoc": _ADOC_RE,
    ".asciidoc": _ADOC_RE,
    ".org": _ORG_RE,
}


def _grammar(rel_path: str) -> re.Pattern | None:
    dot = rel_path.rfind(".")
    slash = max(rel_path.rfind("/"), rel_path.rfind("\\"))
    ext = rel_path[dot:].lower() if dot > slash + 1 else ""
    return _GRAMMARS.get(ext)


def _headings_and_body(rel_path: str, body: str) -> tuple[list[str], str]:
    """The document's headings, and the body with those lines removed.

    Two returns from one call because they must agree: whatever counted as a
    heading has to be the thing taken out of the body, or a heading's words are
    counted twice — once as `heading` tf and once as `body` tf — and *heading
    match outranks body match* stops meaning anything.
    """
    grammar = _grammar(rel_path)
    if grammar is None:
        found = _md_headings(body)
        return [h.text for h in found], _md_strip_headings(body)
    return (
        [m.group("text").strip() for m in grammar.finditer(body)],
        grammar.sub("", body),
    )


@dataclass(frozen=True)
class Extracted:
    title: str
    phrases: list[str]
    #: raw term -> per-field tf, in `store.TF_FIELDS` order:
    #: (body, heading, title, path, ctx)
    terms: dict[str, tuple[int, ...]]
    #: per-field TOKEN COUNTS, same order. Replaces the committed `wlen`
    #: (W-76 Phase 1): `wlen` is a weighted sum of these, and committing it
    #: made a committed field a function of a tunable — SR-TUNE decision 6.
    #: These are facts; the weighting happens at query time.
    flen: tuple[int, ...]


def extract_fields(
    rel_path: str,
    doc: ParsedDoc,
    enrichment: str = "",
    max_phrases: int | None = None,
    root: Path | None = None,
) -> Extracted:
    # `None` is the default rather than the constant so this module does not
    # import `fux.tune` (and through it the query package) at import time.
    if max_phrases is None:
        from ..tune import DEFAULT_MAX_PHRASES

        max_phrases = DEFAULT_MAX_PHRASES
    # W-86 P0: the heading grammar follows the file type. A decoded document
    # always arrives as Markdown (SR-DECODE decision 2), so only an
    # already-prose `.rst`/`.adoc`/`.org` takes a different pattern.
    headings, stripped_body = _headings_and_body(rel_path, doc.body)
    title = _title(doc.meta, headings, rel_path)
    phrases = headings[:max_phrases]

    # `title` now has its own field, so it is no longer folded into the
    # heading tokens. Under two fields it had to be (there was nowhere else to
    # put it); doing so now would double-count every title word.
    heading_tokens = tokenize(" ".join(headings))
    # Strip heading lines out of body text too — without this a heading's
    # words would count twice: once as heading tf, once as body tf, diluting
    # "heading match outranks body match". `_headings_and_body` did the strip
    # with the same grammar that found them, so the two cannot disagree.
    body_tokens = tokenize(stripped_body)
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

    # 🔴 **Front-matter identity values, appended to the field the resolver
    # chose** (SR-INGEST decision 23). Until 2026-09-21 `meta` was dropped
    # entirely except for `title`, so a `doc_id:` a human could read was not one
    # they could search — 7 of the golden seed's 14 declared identity keys are
    # front-matter-only, and every one of them was absent from the index.
    #
    # 🔴 **They go in THROUGH the analyzer, not beside it** (decision 23d): the
    # value is appended to the field's token stream and analyzed exactly as body
    # text is. **Which is why this does not make an identifier WHOLE** — only
    # reachable. `QCL-IT-ADR-08` enters and then loses its `IT` to the stopword
    # list and its hyphens to `_WORD_RE`, precisely as it would in the body.
    by_field = {
        "body": body_tokens, "heading": heading_tokens, "title": title_tokens,
        "path": path_tokens, "ctx": ctx_tokens,
    }
    # The decoder that owns this path, so its `META_FIELDS` claim is consulted.
    # `None` for a prose document, which is every document that HAS front-matter
    # today — `parse_document` returns `meta={}` for anything a decoder handled.
    decoder = _decoder_for(rel_path, root) if doc.meta else None
    for key, field_name in meta_fields(decoder, root).items():
        for value in _meta_values(doc.meta.get(key)):
            by_field[field_name].extend(tokenize(value))

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


def _decoder_for(rel_path: str, root: Path | None):
    """The decoder registered for this path's extension, or `None`."""
    from ..decode import registry

    suffix = "." + rel_path.rsplit(".", 1)[-1].lower() if "." in rel_path else ""
    return registry(root).get(suffix)


def _meta_values(value) -> list[str]:
    """The strings a metadata value contributes, or none.

    **A scalar is one value; a list is its string members** — `aliases:` is the
    key this exists for, and a YAML list is how a human writes more than one
    name for a document.

    ⚠ **A bool is NOT a string and is skipped, though `isinstance(True, int)`.**
    `draft: true` contributes nothing; indexing the word `true` would put every
    draft in the corpus on one posting list. Numbers ARE indexed: a `doc_id: 4471`
    is an identifier a person types.
    """
    if isinstance(value, bool) or value is None:
        return []
    if isinstance(value, (int, float)):
        return [str(value)]
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple)):
        out: list[str] = []
        for item in value:
            out.extend(_meta_values(item))
        return out
    return []


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



