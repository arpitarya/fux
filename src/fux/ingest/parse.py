"""Decode + NFC-normalize + frontmatter-split — the one place raw file bytes
become text. Every other extractor consumes the result, never raw bytes, so
NFC normalization (the R1/macOS-checkout hazard, handoff §6) happens exactly
once per document.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .. import frontmatter as frontmatter_mod
from ..decode import DecodeFailed, decode


@dataclass(frozen=True)
class ParsedDoc:
    meta: dict
    body: str


def parse_document(content: bytes, rel_path: str, root: Path | None = None) -> ParsedDoc | None:
    """The seam: bytes -> `ParsedDoc`, decoding first when a decoder claims the type.

    `None` means *nothing readable came out* — an image, a scanned PDF, a deck
    of pictures. That is a queue entry (W-86 §8), not an error, which is why it
    is a return value rather than an exception.

    **Frontmatter is not re-parsed on decoded output, and that is deliberate.**
    Frontmatter is a property a human typed at the top of a source file. Decoded
    Markdown is generated, and generated Markdown can legitimately *begin* with
    `---` — an HTML `<hr>` produces exactly that — which the frontmatter parser
    would then eat as a delimiter. Documents that arrive already-prose keep the
    old path unchanged, so nothing about existing corpora moves.
    """
    try:
        decoded = decode(content, rel_path, root)
    except DecodeFailed:
        return None
    if decoded is not None:
        return ParsedDoc(meta={}, body=unicodedata.normalize("NFC", decoded))
    from ..decode import claims

    if claims(rel_path, root):
        return None  # a decoder owns this type and got nothing out of it
    return parse(content)


#: The engine default: metadata key -> the index field its value reaches.
#:
#: 🔴 **Identity keys reach `title`, at weight 2.0, and that is the ruling**
#: (Arpit, 2026-09-20, [SR-INGEST](../../../records/0106_ingest.md) decision
#: 23b). *"An identifier is how a person names the document"* — typing it should
#: rank like typing the title. `ctx` at 1.0 would make it one body word among
#: ten thousand, which for a high-`idf` identifier is the wrong strength.
#:
#: 🔴 **No person key, ever, by default** (decision 23c). `owner`, `author` and
#: `contributors` are names, and SR-PII runs on a value before it enters a
#: posting list. A consumer may bind one explicitly in `.fux/formats.toml
#: [meta]`; **fux never decides it for them.**
#:
#: ⚠ `tags` -> `ctx` is in the default and a tag is not a name — but a consumer
#: whose `tags` hold people has made a different file, and `tags = "none"` is
#: how they say so.
DEFAULT_META_FIELDS: dict[str, str] = {
    "doc_id": "title",
    "id": "title",
    "aliases": "title",
    "tags": "ctx",
}


def meta_fields(decoder=None, root: Path | None = None) -> dict[str, str]:
    """Which metadata keys reach the index, and into which field.

    **Three layers, resolved in one order** ([SR-INGEST](../../../records/0106_ingest.md)
    decision 23a): **binding ▸ claim ▸ engine default**, most specific first.

    | | layer | where |
    |---|---|---|
    | 1 | **binding** | `.fux/formats.toml [meta]` (SR-TYPES decision 13) |
    | 2 | **claim** | the decoder's `META_FIELDS` (SR-DECODE decision 20) |
    | 3 | **default** | `DEFAULT_META_FIELDS` above |

    🔴 **A key absent from the returned dict is not indexed.** That is the closed
    list [W-201](../../../archive/open/W-201-frontmatter-scalars-not-indexed.md)
    asked for — **per decoder rather than global**, because a YAML front-matter
    decoder's identity key is `doc_id` and an `.eml` decoder's is `Message-ID`,
    and one global list would be wrong for both.

    ⚠ **`none` silences, and it is the only way to un-index a key a consumer
    decoder claims.** It is removed from the result rather than mapped, so a
    caller never has to know the word.

    ⚠ **`decoder` is `None` for a prose document, and that is the common case.**
    `parse_document` returns `meta={}` for anything a decoder handled, so
    front-matter reaches the index only on the prose path — where there is no
    module to make a claim and the default does the work. **The claim layer is
    for consumer decoders**, and it is built because the spec ratifies it.
    """
    resolved = dict(DEFAULT_META_FIELDS)
    if decoder is not None:
        resolved.update(getattr(decoder, "meta_fields", {}) or {})
    from ..decode import meta_bindings

    resolved.update(meta_bindings(root))
    return {k: v for k, v in sorted(resolved.items()) if v != "none"}


def parse(content: bytes) -> ParsedDoc:
    # "utf-8-sig" strips a leading BOM if present and is otherwise identical
    # to "utf-8". Plain "utf-8" leaves the BOM as a literal U+FEFF at the
    # start of the text, which lands inside the frontmatter delimiter or the
    # first term and silently corrupts either.
    text = unicodedata.normalize("NFC", content.decode("utf-8-sig"))
    fm = frontmatter_mod.parse(text)
    return ParsedDoc(meta=fm.meta, body=fm.body)
