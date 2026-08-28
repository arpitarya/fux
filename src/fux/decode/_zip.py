"""Shared zip handling for every zip-shaped format — OOXML, OpenDocument, and
anything a consumer decoder builds on them.

**This module exists because three families need identical caps and identical
ordering, and three hand-written copies of that would diverge.** That is the
`_MdParser` defect the decoder plane was created to remove; repeating it one
directory down would be a poor joke.

Two hazards, both real and both silent:

* **Decompression bombs.** `zipfile` will happily inflate a 40 KB archive into
  gigabytes. A committed document that exhausts memory at ingest is a denial of
  service that needs no network to reach you.
* **Member order.** `namelist()` returns *archive* order, which is whatever the
  writing tool chose. A decoder that walked it directly would produce different
  Markdown for two archives with identical content — same sources, different
  index, which is L3.
"""

from __future__ import annotations

import zipfile
from io import BytesIO

#: A single document's uncompressed payload. Generous for a real deck or
#: spreadsheet (the largest in this repo's fixtures is under 1 MB) and far
#: below what a bomb needs to hurt.
MAX_UNCOMPRESSED = 64 * 1024 * 1024

#: Members, not bytes. A deck with a thousand slides is unusual; a hundred
#: thousand entries is an attack or a mistake, and either way not a document.
MAX_MEMBERS = 4096

#: Per-member, so one pathological entry cannot consume the whole budget while
#: staying under the archive total.
MAX_MEMBER_BYTES = 32 * 1024 * 1024


class ZipTooBig(ValueError):
    """The archive exceeds a cap. Raised so the caller records a skip.

    A `ValueError` rather than a `FuxError`: this is one unreadable document,
    and `decode()` turns it into `DecodeFailed`, which never ends a run.
    """


class SafeZip:
    """A `ZipFile` with the caps applied and the member list sorted.

    Sorting is the whole reason `names()` exists rather than callers reaching
    for `namelist()`: it is the difference between a deterministic decoder and
    one that depends on how PowerPoint felt that day.
    """

    def __init__(self, raw: bytes) -> None:
        try:
            self._zip = zipfile.ZipFile(BytesIO(raw))
        except (zipfile.BadZipFile, OSError) as exc:
            raise ZipTooBig(f"not a readable zip: {exc}") from exc
        infos = self._zip.infolist()
        if len(infos) > MAX_MEMBERS:
            raise ZipTooBig(f"{len(infos)} members exceeds {MAX_MEMBERS}")
        total = 0
        for info in infos:
            if info.file_size > MAX_MEMBER_BYTES:
                raise ZipTooBig(f"{info.filename} inflates to {info.file_size} bytes")
            total += info.file_size
        if total > MAX_UNCOMPRESSED:
            raise ZipTooBig(f"inflates to {total} bytes, over {MAX_UNCOMPRESSED}")

    def names(self) -> list[str]:
        """Every member, **sorted**. Never archive order."""
        return sorted(self._zip.namelist())

    def read(self, name: str) -> bytes:
        return self._zip.read(name)

    def read_text(self, name: str) -> str:
        # OOXML and ODF parts are XML and therefore UTF-8 by declaration;
        # `replace` keeps one mangled character from costing the document.
        return self.read(name).decode("utf-8", errors="replace")

    def has(self, name: str) -> bool:
        return name in self._zip.namelist()

    def matching(self, prefix: str, suffix: str = "") -> list[str]:
        """Members under `prefix` ending in `suffix`, sorted.

        ⚠ Sorted **lexically**, which is why callers that need slide or sheet
        order sort numerically themselves: `slide10.xml` sorts before
        `slide2.xml`, and a deck read in that order reads as gibberish.
        """
        return [n for n in self.names() if n.startswith(prefix) and n.endswith(suffix)]

    def close(self) -> None:
        self._zip.close()

    def __enter__(self) -> SafeZip:
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def numeric_key(name: str) -> tuple:
    """Sort key that reads embedded digits as numbers.

    `slide2.xml` before `slide10.xml`. Without it a ten-slide deck decodes with
    slide 10 in second position — deterministic, and wrong, which is the worse
    of the two failure modes because nothing looks broken.
    """
    parts: list = []
    digits = ""
    for char in name:
        if char.isdigit():
            digits += char
        else:
            if digits:
                parts.append((1, int(digits)))
                digits = ""
            parts.append((0, char))
    if digits:
        parts.append((1, int(digits)))
    return tuple(parts)
