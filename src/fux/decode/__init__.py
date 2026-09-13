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
name**. This is [SR-FETCHER]'s pattern at a third boundary: fux refuses to
own network I/O, model calls, and now third-party parsing libraries — the
consumer owns each as a file loaded by path that fux never rewrites.

**The protocol** (see `references` in SR-DECODE):

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
asymmetry SR-ENRICH already owns about `model:`.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import tempfile
from pathlib import Path
from typing import Callable

from ..config import DEFAULT_TYPES_FILE as TYPES_FILE
from ..errors import FuxError
from . import _limits

__all__ = [
    "BUILTIN_MODULES",
    "CONSUMER_DIR",
    "Decoder",
    "claims",
    "declared_bindings",
    "decode",
    "reason",
    "registry",
]

#: Consumer decoders live here, one module per format, overriding a built-in of
#: the same module name. Committed — it is consumer source, like `.fux/fetchers/`.
CONSUMER_DIR = ".fux/decoders"

#: Built-in decoder modules, by module name.
#:
#: ⚠ **The `doc` suffix was dropped on 2026-09-06** (Arpit): `csvdoc` -> `csv`,
#: `jsondoc` -> `json`, and so on for all nineteen. The comment that stood here
#: said the suffix kept `json`, `csv`, `xml` and `yaml` from shadowing the
#: stdlib module imported one line below, while conceding the bare names were
#: "technically safe". **They are, and it was measured before the rename, not
#: assumed** — both load paths, because they differ:
#:
#: * a **built-in** is `importlib.import_module(".json", "fux.decode")`, so it
#:   registers as `fux.decode.json` and Python 3's absolute imports give the
#:   file's own `import json` the stdlib module;
#: * a **consumer copy** is loaded from a path under the name
#:   `fux_decoder_json` (see `_load_consumer`), never as `json`, and is not put
#:   in `sys.modules` at all.
#:
#: `sys.modules["json"]` is the stdlib module in both cases. The four names that
#: now collide with popular PyPI distributions rather than the stdlib — `docx`,
#: `pptx`, `yaml`, `toml` — are safe by the same two mechanisms, and were kept
#: uniform deliberately rather than made four exceptions to a one-line rule.
#:
#: 🔴 **The rename is NOT backward compatible, and no migration was written**
#: (Arpit's call, same day). A repo that ran `fux setup` before it has stale
#: `<name>doc.py` files in `.fux/decoders/`; those still claim the same
#: extensions and **win** over the new copies, so that repo keeps running the
#: old decoders until the stale files are deleted. `tests/test_orphaned_modules.py`
#: catches the shipped half of this — an old module left in `src/fux/decode/`
#: is unreachable from `BUILTIN_MODULES` and fails the run — but **nothing
#: reaches a consumer's `.fux/decoders/`.** SR-DECODE decision 17.
#:
#: Sorted and explicit rather than discovered by scanning the directory: a
#: directory listing is filesystem order, and a plane whose dispatch depends on
#: filesystem order is a plane whose committed index depends on it too (L3).
#: ⚠ **`ipynb` and `odt` were REMOVED on 2026-09-06** (Arpit). Removing `odt`
#: removed **four** extensions, not one — `.odt`, `.ods`, `.odp` and `.fodt`
#: were one module because ODF puts every kind of document in the same
#: `content.xml`. `.ipynb` was one. Six extensions in total leave
#: `DEFAULT_TYPES`, which decision 9 derives from this tuple, so a corpus
#: containing them stops being walked unless `.fux/formats.toml` opts them
#: back in — and nothing can, because no built-in claims them any more.
BUILTIN_MODULES: tuple[str, ...] = (
    "csv",
    "docx",
    "drawio",
    "html",
    "image",
    "ini",
    "json",
    "jsonl",
    "mail",
    "pdf",
    "pptx",
    "rtf",
    "svg",
    "toml",
    "xlsx",
    "xml",
    "yaml",
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
            "callable — see records/0139_decode.md §2 decision 1 for the protocol"
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
    """Extension -> decoder: the committed binding first, module tuples second.

    Precedence, in the order it is applied:

    1. **A built-in's own `EXTENSIONS`.**
    2. **A consumer module of the same name replaces it wholesale** — not
       merged, not fallen back to. Matching on *module name* rather than on
       extension is what makes an override a replacement rather than a race:
       two files both claiming `.html` would otherwise resolve by whichever the
       loader reached first (SR-DECODE decision 5).
    3. **A `[decoders]` binding in `.fux/formats.toml` wins over both** — and it
       is checked, not trusted. A line naming a module that does not exist is a
       hard error, and so is one that takes an extension away from the decoder
       that claims it and gives it to a module that does not. **Giving a
       decoder an extension nothing else claims is allowed** — that is how a
       consumer reads `.geojson` with `json` without copying a file. See
       `_bind`.

    ⚠ **Step 3 is why dispatch is a committed fact rather than a derived one.**
    Steps 1 and 2 answer *"which decoder happens to claim `.csv` on this
    machine"*; step 3 answers *"which decoder this repo has agreed reads
    `.csv`"*, and only the second survives a teammate adding a module.
    """
    decoders: dict[str, Decoder] = {}
    #: Module name -> decoder, which is the key a binding names. Built in the
    #: same pass as `decoders` because an extension collision can drop a
    #: decoder out of the extension map entirely, and a binding must still be
    #: able to name it.
    available: dict[str, Decoder] = {}
    consumer = _consumer_decoders(root)
    for name in BUILTIN_MODULES:
        if name in consumer:
            continue  # replaced wholesale; the built-in is not consulted
        built = _load_builtin(name)
        if built is not None:
            available[name] = built
            for ext in built.extensions:
                decoders[ext] = built
    for name in sorted(consumer):
        decoder = consumer[name]
        available[name] = decoder
        for ext in decoder.extensions:
            decoders[ext] = decoder
    # Snapshot BEFORE any binding is applied: "does another decoder already
    # claim this extension" must be a question about the modules, not about
    # which binding happened to be resolved first. Iteration order of the
    # bindings then cannot change any answer (L3).
    claimed = dict(decoders)
    for ext, (name, where) in _declared_bindings(root).items():
        decoders[ext] = _bind(ext, name, where, available, claimed)
    return decoders


def _bind(
    ext: str,
    name: str,
    where: str,
    available: dict[str, Decoder],
    claimed: dict[str, Decoder],
) -> Decoder:
    """Resolve one `[decoders]` binding, or fail naming both sides.

    `where` is the file, the key, and the line number when one could be found
    (`typesfile` — a parsed TOML value carries no position of its own).

    **The file binds and the module verifies** (Arpit, 2026-09-01). What the
    module verifies is narrower than "the extension is in its `EXTENSIONS`",
    and the distinction is the whole of this function:

    * **Extending — allowed.** `geojson = "json"`, where *no decoder
      claims `.geojson`*. There is no competing answer to be stale against:
      without the line that extension has no decoder at all, so the binding is
      purely additive. **`EXTENSIONS` is a decoder's DEFAULT CLAIM, not a
      declaration of what it is capable of reading** — a `.geojson` is JSON,
      and requiring a consumer to copy `json.py` and edit one tuple to say
      so would make the map a worse answer than the code it replaced.
    * **Redirecting — refused.** `csv = "json"`, where `csv`
      already claims `.csv`. Now there are two answers and the line picks the
      module that does not want the extension. That is a typo or a stale
      binding far more often than it is intent, and it is the shape that
      produces **a plausible index with different postings** rather than a
      visible failure.

    ⚠ **The asymmetry is deliberate and it is where the check gives ground.**
    A binding to an extension nothing claims is accepted without fux being able
    to tell a deliberate extension from a typo'd one — but a typo there binds a
    decoder to an extension no file has, which indexes nothing, while the
    refused direction silently re-reads real documents with the wrong reader.
    **The two mistakes are not the same size**, so they do not get the same
    answer. To redirect an extension anyway, write a consumer decoder that
    declares it: that is a committed file, which is the right weight for it.
    """
    decoder = available.get(name)
    if decoder is None:
        raise FuxError(
            f"{where}: no decoder module named {name!r}. The name is a module "
            f"stem, not a path — a built-in ({', '.join(BUILTIN_MODULES)}) or a file in "
            f"{CONSUMER_DIR}/. Add {CONSUMER_DIR}/{name}.py, or correct the name"
        )
    holder = claimed.get(ext)
    if ext not in decoder.extensions and holder is not None:
        raise FuxError(
            f"{where}: binds {ext} to decoder {name!r}, but {name} "
            f"({decoder.origin}) declares EXTENSIONS = {', '.join(decoder.extensions)} and "
            f"does not claim {ext} — while {holder.name} ({holder.origin}) does. Taking an "
            f"extension from the decoder that claims it and giving it to one that does not "
            f"is a typo or a stale line far more often than it is intent, and the wrong "
            f"reader produces a plausible index rather than a visible failure. Either name "
            f"{holder.name}, or add {ext} to a decoder in {CONSUMER_DIR}/ that means to read "
            f"it. (Giving {name} an extension NOTHING claims needs no change — that is a "
            f"binding fux accepts.)"
        )
    return decoder


#: Keyed on the types file's identity AND its stat, so an edit is picked up
#: within a process while a 10 000-document walk still reads the file once.
#: `registry()` is called per document (via `claims`), so an uncached read here
#: would be one open+parse per file walked. The legacy file's presence is part of
#: the key, so deleting it is seen without a restart.
_BINDINGS: dict[tuple[str, int, int, bool], dict[str, tuple[str, str]]] = {}


def _declared_bindings(root: Path | None) -> dict[str, tuple[str, str]]:
    """Extension (`.csv`) -> (decoder name, where it was declared), from `.fux/formats.toml`.

    Empty when there is no root or no types file — which is the built-in
    default, where nothing is declared and every extension resolves through the
    module tuples. **An absent file never means "bind nothing on purpose"**; it
    means the same thing it means for the allowlist itself (SR-TYPES).

    ⚠ **A leftover `.fux/sources/types` is a hard error here too**, not only in
    `read_types`: `fux ask` decodes fetched documents without ever walking, and
    a binding it silently stopped seeing would re-read them with a different
    decoder than the index was built with.

    **No per-extension shape check any more.** The line grammar had to refuse
    `docs/api/*.json decoder=json` at this point, because dispatch sees a suffix
    and nothing about the glob; a `[decoders]` key IS an extension, so that
    line cannot be written (SR-TYPES decision 12).
    """
    if root is None:
        return {}
    # Deferred: `fux.ingest` imports this package at module level, so importing
    # it back at module level would close the loop. By the time any document is
    # decoded both packages are fully initialised. `gitdir._default_types()`
    # defers the mirror-image import for the mirror-image reason.
    from ..config import LEGACY_TYPES_FILE
    from ..ingest import typesfile

    legacy = (root / LEGACY_TYPES_FILE).is_file()
    path = root / TYPES_FILE
    try:
        stamp = path.stat()
        key = (str(path), stamp.st_mtime_ns, stamp.st_size, legacy)
    except OSError:
        if legacy:
            typesfile.check_legacy(root)
        return {}
    cached = _BINDINGS.get(key)
    if cached is not None:
        return cached

    listed = typesfile.read(root, TYPES_FILE)
    out: dict[str, tuple[str, str]] = {}
    if listed is not None:
        for ext, name in listed.decoders.items():
            out[f".{ext}"] = (name, listed.where_decoder(ext))
    _BINDINGS[key] = out
    return out


def declared_bindings(root: Path | None) -> dict[str, str]:
    """Extension -> the decoder module `.fux/formats.toml` binds it to.

    The public half of `_declared_bindings`, which also carries the location a
    resolution error needs. **`fux doctor` is the caller**: a binding on
    an extension no indexed document has resolves perfectly and indexes nothing
    forever — extending is legal by design (`_bind`), so nothing errors, and a
    typo in the extension is invisible until someone asks why a format is
    missing. That question is `doctor`'s, and it should not have to reach
    through a private name to ask it.
    """
    return {ext: name for ext, (name, _where) in _declared_bindings(root).items()}


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
    `.fux/formats.toml`, which is a committed line a human wrote.
    """
    out: set[str] = set()
    for name in BUILTIN_MODULES:
        decoder = _load_builtin(name)
        if decoder is not None:
            out.update(decoder.extensions)
    return tuple(sorted(out))


def builtin_bindings() -> dict[str, str]:
    """Extension -> the BUILT-IN module that reads it, in extension order.

    This is the map `fux setup` and `fux source add` write into a generated
    types file, so it carries `builtin_extensions()`'s restriction for
    `builtin_extensions()`'s reason: **built-ins only, never `registry(root)`.**
    A generated default derived from consumer code would mean dropping a
    `logdoc.py` into `.fux/decoders/` silently changes what fux writes down as
    the binding for a format the consumer never mentioned.

    Later built-ins win a shared extension, matching `registry()`'s own order —
    but no two built-ins claim one today, and `tests/decode/test_decode.py`
    holds that true.
    """
    out: dict[str, str] = {}
    for name in BUILTIN_MODULES:
        decoder = _load_builtin(name)
        if decoder is not None:
            for ext in decoder.extensions:
                out[ext] = name
    return dict(sorted(out.items()))


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
        # The root is bound, not passed: a decoder is still two names
        # (decision 1) and one that ignores configuration never notices.
        with _limits.bound_root(root):
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
