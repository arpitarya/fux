"""`.pptx` -> Markdown.

Slides are `ppt/slides/slideN.xml`, and **slide order is numeric, not lexical** —
`_zip.numeric_key` exists because `slide10.xml` sorts before `slide2.xml` and a
deck read that way is deterministic and wrong, which is worse than noisy,
because nothing looks broken.

Two things a deck has that a document does not:

* **A slide title**, which is the one line most worth having in the heading
  field. It is marked in the shape's placeholder type, not by style name.
* **Speaker notes**, in a separate part. They are kept — a deck's notes often
  carry the actual argument the slide only gestures at.
"""

from __future__ import annotations

# Imports are ABSOLUTE, not relative, and that is what makes this file work in
# both places it runs: as a package module, and as a consumer copy in
# `.fux/decoders/` loaded by path. A path-loaded file has no parent package, so
# `from . import _xml` raises `attempted relative import with no known parent
# package` — the copy would be dead on arrival. Absolute imports mean the file
# fux ships and the file you edit are byte-identical (ADR-DECODE decision 11).
from fux.decode import _ooxml, _xml
from fux.decode._zip import SafeZip, ZipTooBig, numeric_key

EXTENSIONS = (".pptx", ".pptm")

_SLIDES = "ppt/slides/slide"
_NOTES = "ppt/notesSlides/notesSlide"


def decode(raw: bytes, rel_path: str) -> str | None:
    try:
        with SafeZip(raw) as archive:
            slides = sorted(
                (n for n in archive.matching(_SLIDES, ".xml")),
                key=numeric_key,
            )
            if not slides:
                return None
            blocks: list[str] = []
            for index, name in enumerate(slides, start=1):
                try:
                    root = _xml.parse(archive.read(name))
                except _xml.UnsafeXml:
                    continue  # one unreadable slide, not an unreadable deck
                blocks.extend(_slide(root, index))
                notes_name = f"{_NOTES}{_slide_number(name)}.xml"
                if archive.has(notes_name):
                    try:
                        notes_root = _xml.parse(archive.read(notes_name))
                    except _xml.UnsafeXml:
                        continue
                    notes = _lines(notes_root)
                    if notes:
                        blocks.append("*Notes:* " + " ".join(notes))
    except ZipTooBig:
        return None

    body = "\n\n".join(b for b in blocks if b.strip())
    # A deck of nothing but images decodes to nothing — which is `None`, the
    # signal that a model must read it, not an empty document.
    return body if body.strip() else None


def _slide_number(name: str) -> str:
    return "".join(c for c in name.rsplit("/", 1)[-1] if c.isdigit())


def _slide(root, index: int) -> list[str]:
    title = _title(root)
    lines = _lines(root)
    if title and lines and lines[0] == title:
        lines = lines[1:]
    out: list[str] = []
    # The slide keeps a heading even when untitled: without one, every bullet in
    # a hundred-slide deck lands in a single undifferentiated body field, and
    # the headings `fux ask` renders as `§` lines would be empty for decks.
    out.append(f"## {title}" if title else f"## Slide {index}")
    out.extend(f"- {line}" for line in lines)
    return out


def _title(root) -> str:
    """The text of the shape whose placeholder type is a title.

    `ph type="title"` (or `ctrTitle`) is how PowerPoint marks it; a shape's
    position on the slide is not reliable and reading the layout part to find
    out would mean a second file per slide.
    """
    for shape in root.iter():
        if _xml.local(shape.tag) != "sp":
            continue
        kind = None
        for node in shape.iter():
            if _xml.local(node.tag) == "ph":
                for key, value in node.attrib.items():
                    if _xml.local(key) == "type":
                        kind = value
        if kind in ("title", "ctrTitle"):
            texts = [
                _ooxml.paragraph_text(p) for p in shape.iter() if _xml.local(p.tag) == "p"
            ]
            joined = " ".join(t for t in texts if t).strip()
            if joined:
                return joined
    return ""


def _lines(root) -> list[str]:
    out: list[str] = []
    for node in root.iter():
        if _xml.local(node.tag) != "p":
            continue
        text = _ooxml.paragraph_text(node)
        if text:
            out.append(text)
    return out
