"""The decoder plane — the one place bytes that are not already prose become
Markdown, so every other part of ingest sees exactly one kind of document.

**Why Markdown is the intermediate and not plain text.** `ingest/extract.py`
re-derives headings with `^(#{1,6})\\s+` and puts them in their own weighted
field. A decoder that returned flat text would drop every heading into the body
and silently disable *"heading match outranks body match"* on every
non-Markdown document. The heading syntax is the interface, so the intermediate
has to carry it.

**Two kinds of decoder, one protocol.** Built-ins live in this package and are
stdlib-only (**L1**). Consumer decoders live in `.fux/decoders/<name>.py`, may
import whatever the consumer installed, and **override a built-in of the same
name**. This is [ADR-FETCHER]'s pattern at a third boundary: fux refuses to
own network I/O, model calls, and now third-party parsing libraries — the
consumer owns each as a file loaded by path that fux never rewrites.

**The protocol** (see `references` in ADR-DECODE):

    EXTENSIONS = (".html", ".htm")          # required; lowercase, with the dot
    def decode(raw: bytes, rel_path: str) -> str | None: ...

    # opt-in variant, for a library that insists on a real file:
    WANTS_PATH = True
    def decode(path: Path, rel_path: str) -> str | None: ...

Returning `None` means *this needs a model to read it* — an image, a scanned
PDF — and is not an error. It is the signal the enrichment queue is built on.
A decoder never raises for malformed input: one corrupt file in a
10 000-document corpus must not stop the other 9 999.

**Determinism (L3) is the decoder's obligation, not this module's.** Same bytes
must produce the same string, byte for byte: sort every iteration, never rely
on `set` order, never read a clock. This module can only guarantee that
*dispatch* is deterministic, which it does by resolving one extension to one
decoder with a documented precedence.

**Offline (L4).** No built-in decoder opens a socket — not for a schema, not
for a font, not for an XML external entity. The import fence test asserts it
for this package. ⚠ It cannot reach `.fux/decoders/`, and that limit is stated
rather than papered over: a consumer decoder's offline behaviour is a
documented obligation checked by review of a committed diff, the same
asymmetry ADR-ENRICH already owns about `model:`.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import tempfile
from pathlib import Path
from typing import Callable

from ..errors import FuxError

__all__ = [
    "BUILTIN_MODULES",
    "CONSUMER_DIR",
    "Decoder",
    "claims",
    "decode",
    "reason",
    "registry",
]

#: Consumer decoders live here, one module per format, overriding a built-in of
#: the same module name. Committed — it is consumer source, like `.fux/fetchers/`.
CONSUMER_DIR = ".fux/decoders"

#: Built-in decoder modules, by module name. **Sorted and explicit rather than
#: discovered by scanning the directory**: a directory listing is filesystem
#: order, and a plane whose dispatch depends on filesystem order is a plane
#: whose committed index depends on it too (L3).
#:
#: The `doc` suffix keeps `json`, `csv`, `xml` and `yaml` from shadowing the
#: stdlib module a reader is about to see imported one line below. Python 3's
#: absolute imports make the bare names technically safe; the suffix costs
#: three characters and removes the question.
BUILTIN_MODULES: tuple[str, ...] = (
    "csvdoc",
    "docxdoc",
    "drawiodoc",
    "htmldoc",
    "imagedoc",
    "inidoc",
    "ipynbdoc",
    "jsondoc",
    "jsonldoc",
    "maildoc",
    "odtdoc",
    "pdfdoc",
    "pptxdoc",
    "rtfdoc",
    "svgdoc",
    "tomldoc",
    "xlsxdoc",
    "xmldoc",
    "yamldoc",
)


class Decoder:
    """One format's decoder, built-in or consumer, behind one call shape.

    `wants_path` is the opt-in from the protocol above. Fux always holds the
    bytes already — the walker read them — so a path-wanting decoder is served
    from a temporary file that fux writes and removes. That cost is real and is
    why bytes is the default rather than the only option: it buys compatibility
    with libraries that will not accept a buffer, and nothing else.
    """

    __slots__ = ("name", "extensions", "_fn", "wants_path", "origin")

    def __init__(
        self,
        name: str,
        extensions: tuple[str, ...],
        fn: Callable,
        *,
        wants_path: bool,
        origin: str,
    ) -> None:
        self.name = name
        self.extensions = extensions
        self._fn = fn
        self.wants_path = wants_path
        self.origin = origin

    def __call__(self, raw: bytes, rel_path: str) -> str | None:
        if not self.wants_path:
            return self._fn(raw, rel_path)
        # A suffix is kept because a library that wants a path usually wants to
        # sniff the extension off it. The stem is not derived from `rel_path`:
        # a temp name that varied with the document would be one more way for
        # an environment detail to reach a decoder's output.
        suffix = _suffix(rel_path)
        handle, tmp = tempfile.mkstemp(suffix=suffix, prefix="fux-decode-")
        try:
            with os.fdopen(handle, "wb") as out:
                out.write(raw)
            return self._fn(Path(tmp), rel_path)
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass  # a decoder that moved or deleted it is not our failure


def _suffix(rel_path: str) -> str:
    """The lowercase extension of `rel_path`, or `""`.

    Lowercased because `README.MD` and `readme.md` are the same format, and a
    registry keyed on raw case would make an index depend on how a filesystem
    happened to record a name — which on a case-insensitive checkout is not
    even stable across machines.
    """
    dot = rel_path.rfind(".")
    slash = max(rel_path.rfind("/"), rel_path.rfind("\\"))
    if dot <= slash + 1:
        return ""
    return rel_path[dot:].lower()


def _load_builtin(name: str) -> Decoder | None:
    module = importlib.import_module(f".{name}", __package__)
    return _from_module(module, name, origin=f"built-in:{name}")


def _load_consumer(path: Path, name: str) -> Decoder:
    spec = importlib.util.spec_from_file_location(f"fux_decoder_{name}", path)
    if spec is None or spec.loader is None:
        raise FuxError(f"decoder could not be loaded: {path}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except ModuleNotFoundError as exc:
        # The loud failure Arpit ruled on 2026-08-26. A decoder whose library is
        # absent must NOT quietly hand the file to the enrichment queue: two
        # machines with the same sources would then commit different indexes,
        # which is L3, not a convenience. Naming the module is most of the fix.
        raise FuxError(
            f"decoder {name} needs a dependency this machine does not have: {exc.name}. "
            f"Install it (for example `uv pip install {exc.name}`), or remove "
            f"{CONSUMER_DIR}/{path.name} if this repo should not decode that format. "
            "Ingesting without it would produce a different index than your "
            "teammates' from the same sources"
        ) from exc
    except Exception as exc:
        raise FuxError(f"decoder failed to import: {path} ({exc})") from exc
    decoder = _from_module(module, name, origin=str(path))
    if decoder is None:
        raise FuxError(
            f"decoder {path} defines no EXTENSIONS tuple and decode(raw, rel_path) "
            "callable — see docs/adr/0042_decode.md §2 decision 1 for the protocol"
        )
    return decoder


def _from_module(module, name: str, *, origin: str) -> Decoder | None:
    fn = getattr(module, "decode", None)
    extensions = getattr(module, "EXTENSIONS", None)
    if not callable(fn) or not extensions:
        return None
    return Decoder(
        name=name,
        extensions=tuple(sorted(str(e).lower() for e in extensions)),
        fn=fn,
        wants_path=bool(getattr(module, "WANTS_PATH", False)),
        origin=origin,
    )


def registry(root: Path | None = None) -> dict[str, Decoder]:
    """Extension -> decoder, with consumer modules overriding built-ins by name.

    Precedence is deliberate and narrow: a consumer module named `htmldoc.py`
    replaces the built-in `htmldoc`, whatever extensions it declares. Matching
    on *module name* rather than on extension is what makes an override a
    replacement rather than a race — two files both claiming `.html` would
    otherwise resolve by whichever the loader reached first.
    """
    decoders: dict[str, Decoder] = {}
    consumer = _consumer_decoders(root)
    for name in BUILTIN_MODULES:
        if name in consumer:
            continue  # replaced wholesale; the built-in is not consulted
        built = _load_builtin(name)
        if built is not None:
            for ext in built.extensions:
                decoders[ext] = built
    for name in sorted(consumer):
        decoder = consumer[name]
        for ext in decoder.extensions:
            decoders[ext] = decoder
    return decoders


def _consumer_decoders(root: Path | None) -> dict[str, Decoder]:
    if root is None:
        return {}
    directory = root / CONSUMER_DIR
    if not directory.is_dir():
        return {}
    out: dict[str, Decoder] = {}
    # Sorted, so two machines load the same files in the same order even though
    # their filesystems enumerate differently.
    for path in sorted(directory.glob("*.py")):
        if path.name.startswith("_"):
            continue  # a shared helper the consumer imports, not a decoder
        out[path.stem] = _load_consumer(path, path.stem)
    return out


def builtin_extensions() -> tuple[str, ...]:
    """Every extension a **built-in** decoder claims, sorted.

    ⚠ **Built-ins only, deliberately — never `registry(root)`.** This feeds
    `DEFAULT_TYPES`, and a default allowlist derived from consumer code would
    mean that dropping a `logdoc.py` into `.fux/decoders/` silently starts
    walking every `.log` file in the repo. **Adding a decoder must not, by
    itself, change what is indexed**: a consumer says what is a document in
    `.fux/sources/types`, which is a committed line a human wrote.
    """
    out: set[str] = set()
    for name in BUILTIN_MODULES:
        decoder = _load_builtin(name)
        if decoder is not None:
            out.update(decoder.extensions)
    return tuple(sorted(out))


def claims(rel_path: str, root: Path | None = None) -> bool:
    """Whether any decoder handles this path's extension.

    The walker asks this before skipping a file as binary: a `.docx` is binary
    and is still a document, so "binary" stopped being a sufficient reason to
    skip the moment decoders existed.
    """
    return _suffix(rel_path) in registry(root)


def reason(rel_path: str, root: Path | None = None) -> str:
    """Why this document is unreadable, in words a human can triage.

    Two distinct facts, and conflating them would make the queue useless: a
    format **nothing claims** is a missing decoder (someone could write one); a
    format a decoder **owns but got nothing out of** is a scan or an image
    (only a model will help). The queue's whole value is that difference.
    """
    suffix = _suffix(rel_path) or "(no extension)"
    decoder = registry(root).get(_suffix(rel_path))
    if decoder is None:
        return f"no decoder for {suffix}"
    return f"{decoder.name}: nothing readable in {suffix}"


def decode(raw: bytes, rel_path: str, root: Path | None = None) -> str | None:
    """Bytes -> Markdown, or `None` when a model is needed to read it.

    Returns `None` for an unclaimed extension too — callers treat "no decoder"
    and "a decoder that could not extract text" the same way, because the
    document is equally unreadable either way and the queue records the reason.
    """
    decoder = registry(root).get(_suffix(rel_path))
    if decoder is None:
        return None
    try:
        out = decoder(raw, rel_path)
    except FuxError:
        raise
    except Exception as exc:
        # A malformed document is data, not a bug. Ingest of 10 000 files must
        # not end because one of them is truncated; the queue keeps the reason.
        raise DecodeFailed(f"{decoder.name}: {type(exc).__name__}: {exc}") from exc
    if out is None:
        return None
    return out if out.strip() else None


class DecodeFailed(Exception):
    """One document could not be decoded. Caught by the walker, never fatal.

    Deliberately not a `FuxError`: `FuxError` is rendered to the user at the
    CLI boundary as a failure of the command, and one unreadable file is not
    that. It is a skipped document with a recorded reason.
    """
