"""The decoder plane — the one place bytes that are not already prose become
Markdown, so every other part of ingest sees exactly one kind of document.

**Why Markdown is the intermediate and not plain text.** `ingest/extract.py`
re-derives headings with `^(#{1,6})\\s+` and puts them in their own weighted
field. A decoder that returned flat text would drop every heading into the body
and silently disable *"heading match outranks body match"* on every
non-Markdown document. The heading syntax is the interface, so the intermediate
has to carry it.

**Two kinds of decoder, one protocol.** Packaged decoders ship in the
`fux-decoder-*` plugin packages and are stdlib-only (**L2**); **one runs only
when its package is declared in the committed `.fux/plugins.toml`**, verified
against its pinned version and digest ([SR-PLUGINS](../../../records/0165_plugins.md)
P3, P4, W-289). Consumer decoders live in `.fux/decoders/<name>.py`, may
import whatever the consumer installed, and **override a packaged decoder of
the same module name** (P8). This is [SR-FETCHER]'s pattern at a third
boundary: fux refuses to own network I/O, model calls, and now third-party
parsing libraries — the consumer owns each as a file loaded by path that fux
never rewrites.

🔴 **No declaration, prose only.** A repository without `.fux/plugins.toml`
decodes nothing — Markdown and plain text are read without a decoder — and
`fux ingest` and `fux doctor` say so in one line, with `fux setup` as the lever.
An installed package nobody declared is never imported here.

**The protocol** (see `references` in SR-DECODE):

    EXTENSIONS = (".html", ".htm")          # required; lowercase, with the dot
    def decode(raw: bytes, rel_path: str) -> str | None: ...

    # opt-in variant, for a library that insists on a real file:
    WANTS_PATH = True
    def decode(path: Path, rel_path: str) -> str | None: ...

    # optional: the decoder extensions it calls (`fux.decode.ext.<name>`),
    # each one's VERSION then rides in its reuse key — SR-DECODE decision 24
    USES = ("table", "limits")

Returning `None` means *this needs a model to read it* — an image, a scanned
PDF — and is not an error. It is the signal the enrichment queue is built on.
A decoder never raises for malformed input: one corrupt file in a
10 000-document corpus must not stop the other 9 999.

**Determinism (L4) is the decoder's obligation, not this module's.** Same bytes
must produce the same string, byte for byte: sort every iteration, never rely
on `set` order, never read a clock. This module can only guarantee that
*dispatch* is deterministic, which it does by resolving one extension to one
decoder with a documented precedence.

**Offline (L5).** No built-in decoder opens a socket — not for a schema, not
for a font, not for an XML external entity. The import fence test asserts it
for this package. ⚠ It cannot reach `.fux/decoders/`, and that limit is stated
rather than papered over: a consumer decoder's offline behaviour is a
documented obligation checked by review of a committed diff, the same
asymmetry SR-ENRICH already owns about `model:`.
"""

from __future__ import annotations

import functools
import importlib
import importlib.util
import os
import sys
import tempfile
from pathlib import Path
from typing import Callable

from ..config import DEFAULT_TYPES_FILE as TYPES_FILE
from ..errors import FuxError
from .ext import limits as _limits
from ..constants import fixed

#: 🔴 **The pre-4.2 helper names stay importable — as ALIASES, never copies**
#: (W-288, SR-DECODE decision 24). The shared helpers moved to `decode/ext/` as
#: decoder extensions; every `.fux/decoders/` copy `fux setup` seeded before
#: then, and every decoder written from the `fux-decoder` skill, imports
#: `fux.decode._xml` and its siblings. Without these an engine upgrade would stop
#: each such repo's ingest at its first decoder import. Each old name is bound to
#: the extension MODULE OBJECT itself — one `ContextVar`, one cache — and no
#: `_<name>.py` file exists to drift. ⚠ A decoder importing an old name declares
#: no `USES` for it, so the extension's `VERSION` does not reach its reuse key;
#: that is the stale copy `fux doctor`'s `seeded copies current` row already
#: names, and re-seeding closes it.
for _helper in fixed("decoders", "legacy_helpers"):
    _extension = importlib.import_module(f"{__name__}.ext.{_helper}")
    sys.modules.setdefault(f"{__name__}._{_helper}", _extension)
    globals()[f"_{_helper}"] = _extension
del _helper, _extension

__all__ = [
    "BUILTIN_MODULES",
    "CONSUMER_DIR",
    "PROSE_DECODER",
    "Decoder",
    "claims",
    "declared_bindings",
    "decode",
    "decode_with",
    "decoder_named",
    "reason",
    "registry",
]

#: Consumer decoders live here, one module per format, overriding a built-in of
#: the same module name. Committed — it is consumer source, like `.fux/fetchers/`.
CONSUMER_DIR = fixed("decoders", "consumer_dir")

#: The one reserved decoder name, and the one name a consumer file may not take.
#:
#: 🔴 **It names a BRANCH, not a module** — bytes that are already prose reach no
#: decoder at all (`urlsrc._decode_fetched`'s `_PROSE` path, which predates this
#: by a month). A URL line says `decoder=prose` for a `text/markdown` or
#: `text/plain` page, so `.fux/decoders/prose.py` would be a file that looks like
#: it is being used and never is. `_consumer_decoders` refuses the name — the
#: pipe ruling, §3 edge case 1.
#:
#: ⚠ **Spelled in two modules and that is deliberate, not a restatement.**
#: `ingest.sourcelist.PROSE_DECODER` is the GRAMMAR's reserved word (what a line
#: may say) and `ingestlog.PROSE` is the LEDGER's name for *no decoder ran*.
#: They cannot disagree while both look correct — a mismatch fails the parse or
#: the registry build immediately — so by L0's own test these are
#: implementations, not restatements. `tests/decode/test_decoder_named.py` holds
#: the three equal anyway.
PROSE_DECODER = "prose"

#: Every first-party decoder module, by module name — `constants.toml [decoders]
#: builtin`. **Since W-289 phase 2 none ships in fux-core**: each lives in the
#: plugin package whose `[plugins.packages.*] modules` names it, and runs only
#: when that package is declared. The name stays `BUILTIN_MODULES` because every
#: error message that lists "the built-ins" lists exactly these.
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
#: filesystem order is a plane whose committed index depends on it too (L4).
#: ⚠ **`ipynb` and `odt` were REMOVED on 2026-09-06** (Arpit). Removing `odt`
#: removed **four** extensions, not one — `.odt`, `.ods`, `.odp` and `.fodt`
#: were one module because ODF puts every kind of document in the same
#: `content.xml`. `.ipynb` was one. Six extensions in total leave
#: `DEFAULT_TYPES`, which decision 9 derives from this tuple, so a corpus
#: containing them stops being walked unless `.fux/formats.toml` opts them
#: back in — and nothing can, because no built-in claims them any more.
BUILTIN_MODULES: tuple[str, ...] = tuple(fixed("decoders", "builtin"))


class Decoder:
    """One format's decoder, built-in or consumer, behind one call shape.

    `wants_path` is the opt-in from the protocol above. Fux always holds the
    bytes already — the walker read them — so a path-wanting decoder is served
    from a temporary file that fux writes and removes. That cost is real and is
    why bytes is the default rather than the only option: it buys compatibility
    with libraries that will not accept a buffer, and nothing else.
    """

    __slots__ = (
        "name", "extensions", "primary", "_fn", "wants_path", "origin", "meta_fields", "uses",
    )

    def __init__(
        self,
        name: str,
        extensions: tuple[str, ...],
        fn: Callable,
        *,
        wants_path: bool,
        origin: str,
        meta_fields: dict[str, str] | None = None,
        primary: str = "",
        uses: tuple[str, ...] = (),
    ) -> None:
        self.name = name
        self.extensions = extensions
        #: 🔴 **`EXTENSIONS[0]` as the module WROTE it, not `extensions[0]`.**
        #: `extensions` is sorted — two machines must load one module the same
        #: way — and sorting answers a different question from *"what is this
        #: format called"*: it makes `xlsx` primary in `.xlsm` and `html`
        #: primary in `.htm`. Nothing cared while a decoder was only ever
        #: reached BY an extension; the pipe ruling reaches one by **name**
        #: (`decoder=xlsx`) and then has to invent the path it decodes under,
        #: and the name of the retained blob beside it. The author's first
        #: extension is the format's own name; the sorted one is an accident
        #: of the alphabet. Empty only for a module with no `EXTENSIONS`, which
        #: `_from_module` already declines to build a decoder from.
        self.primary = primary or (extensions[0] if extensions else "")
        self._fn = fn
        self.wants_path = wants_path
        self.origin = origin
        #: This decoder's `META_FIELDS` claim (SR-DECODE decision 20a). Empty
        #: means it declares none, which is NOT the same as "nothing is
        #: indexed" — the engine default still applies.
        self.meta_fields = dict(meta_fields or {})
        #: The decoder extensions this decoder declares it calls, in its own
        #: order (SR-DECODE decision 24). Read by the reuse key, never passed to
        #: `decode()` — the protocol does not grow a parameter (decision 5).
        self.uses = tuple(uses)

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


#: `Decoder.origin` for a decoder loaded from a declared plugin package:
#: `pkg:<dist>@<version>/<module>` — and the head of its digest (SR-PLUGINS P12).
PACKAGE_PREFIX = fixed("decoders", "package_prefix")


def _load_packaged(decl, name: str) -> Decoder | None:
    """A decoder module from a DECLARED package, verified first (P4, P7)."""
    from .. import plugins

    module = plugins.load_decoder(decl, name)
    decoder = _from_module(module, name, origin=f"{PACKAGE_PREFIX}{decl.name}@{decl.version}/{name}")
    if decoder is None:
        return None
    if not decl.package.first_party:
        # A third-party package reads what its declaration says it reads, and
        # nothing more: the committed row is the claim (SR-PLUGINS P2).
        claimed = tuple(e for e in decoder.extensions if e in decl.package.suffixes)
        decoder.extensions = claimed
    return decoder


def _moved(missing: str | None) -> str | None:
    """Where a module a pre-W-289 decoder imports went, or `None`.

    `fux.decode.<format>` moved into its `fux-decoder-*` package and
    `fux.decode.ext.table` into `fux-extension-table` (W-289 phase 2). A copy
    `fux setup` seeded before then imports the old names, and the right fix is
    almost always to delete the copy so the declared package runs.
    """
    if not missing:
        return None
    from .. import plugins

    if missing in (f"{__name__}.ext.table", f"{__name__}._table"):
        return f"{plugins.import_name('extension', 'table')}.table, in fux-extension-table"
    head, _, tail = missing.rpartition(".")
    if head == __name__ and tail in BUILTIN_MODULES:
        package = plugins.package_for_module(tail)
        if package is not None:
            return f"{package.module}.{tail}, in {package.name}"
    return None


def _load_consumer(path: Path, name: str) -> Decoder:
    # Not `fux_decoder_<name>`: since W-289 that is a plugin package's import
    # name (SR-PLUGINS P7), and a consumer file must never be mistaken for one.
    spec = importlib.util.spec_from_file_location(f"fux_consumer_decoder_{name}", path)
    if spec is None or spec.loader is None:
        raise FuxError(f"decoder could not be loaded: {path}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except ImportError as exc:
        moved = _moved(getattr(exc, "name", None))
        if moved is None and not isinstance(exc, ModuleNotFoundError):
            raise FuxError(f"decoder failed to import: {path} ({exc})") from exc
        if moved is not None:
            raise FuxError(
                f"{CONSUMER_DIR}/{path.name} imports {exc.name}, which moved to {moved} "
                "(W-289). If this file is a copy an older `fux setup` seeded and you never "
                "edited it, delete it - the declared package runs instead, and `fux doctor` "
                "lists the copies it can prove unedited. If you edited it, change the import "
                "and declare the package in .fux/plugins.toml (SR-PLUGINS P8)"
            ) from exc
        # The loud failure Arpit ruled on 2026-08-26. A decoder whose library is
        # absent must NOT quietly hand the file to the enrichment queue: two
        # machines with the same sources would then commit different indexes,
        # which is L4, not a convenience. Naming the module is most of the fix.
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
        primary=str(tuple(extensions)[0]).lower(),
        fn=fn,
        wants_path=bool(getattr(module, "WANTS_PATH", False)),
        origin=origin,
        # 🔴 **Read on the same import path as `EXTENSIONS`, and that is a
        # deliberate difference from a fetcher's `ROUTES`** (SR-DECODE decision
        # 20b). A decoder is already imported in order to decode, so reading one
        # more module attribute costs nothing and adds no new trust. A FETCHER is
        # read with `ast` and never imported, because importing consumer code on
        # the offline path breaks L5. **The two rules differ because the risk
        # differs**, and copying one to the other copies the wrong half.
        meta_fields=_meta_fields_of(module, name, origin),
        # `USES` is read the same way and for the same reason as `META_FIELDS`.
        uses=_uses_of(module, origin),
    )


def _uses_of(module, origin: str) -> tuple[str, ...]:
    """A decoder's `USES` — the decoder extensions it calls (SR-DECODE decision 24).

    Absent means *none declared*, the shape of every decoder written before
    W-288. A name that is not a decoder extension is a hard error naming the
    file, as an unknown `META_FIELDS` target is: a reuse key built from a name
    with no `VERSION` behind it would look current for ever.
    """
    from .ext import NAMES

    declared = getattr(module, "USES", None)
    if declared is None:
        return ()
    if isinstance(declared, str) or not isinstance(declared, (tuple, list)):
        raise FuxError(
            f"decoder {origin} declares USES that is not a tuple of decoder-extension "
            f"names (SR-DECODE decision 24)"
        )
    out: list[str] = []
    for item in declared:
        if item not in NAMES:
            raise FuxError(
                f"decoder {origin}: USES names {item!r}, which is not a decoder extension. "
                f"Use any of {', '.join(NAMES)} — the modules under fux.decode.ext"
            )
        if item in out:
            raise FuxError(f"decoder {origin}: USES names {item!r} twice")
        out.append(item)
    return tuple(out)


def _meta_fields_of(module, name: str, origin: str) -> dict[str, str]:
    """A decoder's `META_FIELDS` claim — metadata key -> index field.

    Absent is the common case and means *this decoder declares none*, which is
    not the same as *nothing is indexed*: the engine default in
    `ingest/parse.meta_fields()` still applies. SR-DECODE decision 20a.
    """
    claimed = getattr(module, "META_FIELDS", None)
    if claimed is None:
        return {}
    if not isinstance(claimed, dict):
        raise FuxError(
            f"decoder {origin} declares META_FIELDS that is not a dict of "
            f"`metadata key -> index field` (SR-DECODE decision 20a)"
        )
    from ..acquire.typesfile import META_TARGETS

    out: dict[str, str] = {}
    for key, target in claimed.items():
        if not isinstance(key, str) or not isinstance(target, str):
            raise FuxError(
                f"decoder {origin}: META_FIELDS holds {key!r} = {target!r}; both must be strings"
            )
        if target not in META_TARGETS:
            fields = ", ".join(t for t in META_TARGETS if t != "none")
            raise FuxError(
                f"decoder {origin}: META_FIELDS maps {key!r} to {target!r}, which is not an "
                f"index field. Use one of {fields}, or \"none\". A claim naming no field "
                f"would index nothing and say nothing"
            )
        out[key] = target
    return dict(sorted(out.items()))


#: `registry()`'s cache (W-239). Keyed on everything the map is a function of —
#: the repo, the stat of every `.py` in `.fux/decoders/` (helpers included, since
#: a decoder may import one), the stat of `.fux/formats.toml` and the legacy
#: file's presence — so an edit is seen in the same process while a walk over
#: 10 000 documents imports each consumer decoder ONCE. Until 2026-09-29 every
#: call re-ran `exec_module` on every consumer file, and `registry()` is called
#: two or three times per document (`decode`, `claims`, `extract._decoder_for`):
#: 58 000 imports, 35% of a 1 000-document ingest.
#:
#: ⚠ **A consumer decoder now keeps its module state between documents.** One
#: that mutates a module global while decoding could make a document's output
#: depend on the documents decoded before it. A decoder is a function of
#: `(raw, rel_path)` (SR-DECODE decision 1); the per-call re-import used to hide
#: a decoder that is not, and no longer does.
_REGISTRY: dict[tuple, dict[str, "Decoder"]] = {}


def _registry_key(root: Path | None) -> tuple:
    if root is None:
        return (None,)
    from ..config import LEGACY_TYPES_FILE

    files: list[tuple] = []
    try:
        with os.scandir(root / CONSUMER_DIR) as entries:
            for entry in entries:
                if entry.name.endswith(".py") and entry.is_file():
                    st = entry.stat()
                    files.append((entry.name, st.st_mtime_ns, st.st_size, st.st_ino))
    except OSError:
        pass  # no directory: no consumer decoders, as in `_consumer_decoders`
    try:
        st = (root / TYPES_FILE).stat()
        types = (st.st_mtime_ns, st.st_size, st.st_ino)
    except OSError:
        types = None
    legacy = (root / LEGACY_TYPES_FILE).is_file()
    from .. import plugins

    # W-289: the declaration decides which packaged modules load, so an edited
    # `.fux/plugins.toml` is a different registry.
    return (os.path.abspath(root), tuple(sorted(files)), types, legacy, plugins.stamp(root))


def registry(root: Path | None = None) -> dict[str, Decoder]:
    """Extension -> decoder: the committed binding first, module tuples second.

    **Cached per process on `_registry_key`** (W-239). A failure is never
    cached, so a broken decoder or binding raises on every call as it always
    did, and each caller gets its own copy of the map.

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
    key = _registry_key(root)
    hit = _REGISTRY.get(key)
    if hit is None:
        hit = _REGISTRY[key] = _build_registry(root)
    return dict(hit)


def _build_registry(root: Path | None) -> dict[str, Decoder]:
    decoders: dict[str, Decoder] = {}
    #: Module name -> decoder, which is the key a binding names. Built in the
    #: same pass as `decoders` because an extension collision can drop a
    #: decoder out of the extension map entirely, and a binding must still be
    #: able to name it.
    available: dict[str, Decoder] = {}
    if root is not None:
        from .. import plugins

        # P4 for the whole declaration, once per registry: a declared package
        # whose dependency is undeclared would otherwise import an installed
        # but undeclared sibling (`fux_decoder_mail.mail` -> `fux_decoder_html`).
        plugins.require(root)
    consumer = _consumer_decoders(root)
    # A consumer file replaces a packaged module of its name wholesale (P8),
    # so a declared package whose every module is overridden is never imported.
    packaged = _packaged_decoders(root, set(consumer))
    for name in sorted(packaged):
        built = packaged[name]
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
    # bindings then cannot change any answer (L4).
    claimed = dict(decoders)
    for ext, (name, where) in _declared_bindings(root).items():
        if name not in available and _undeclared_module(name):
            # 🔴 **A binding to a first-party module whose package is not
            # declared reads nothing, and is not an error** (SR-PLUGINS P3): a
            # `.fux/formats.toml` seeded with every first-party binding stays
            # valid in a repository that declares only some packages. The files
            # are counted on `fux ingest`'s stderr and in `fux doctor`, never
            # read as prose (P5).
            continue
        decoders[ext] = _bind(ext, name, where, available, claimed)
    return decoders


def _undeclared_module(name: str) -> bool:
    """Is `name` a first-party decoder module — one a package carries?"""
    return name in BUILTIN_MODULES


def _packaged_decoders(root: Path | None, overridden: set[str]) -> dict[str, Decoder]:
    """Module name -> decoder, for every module a DECLARED package carries.

    🔴 **The declaration is the whole gate (P3).** No root, no file, or a
    package nobody declared: nothing is imported. A module in `overridden` — a
    consumer file of that name exists — is skipped (P8). Sorted by package and
    module, so two machines load the same modules in the same order (L4).
    """
    if root is None:
        return {}
    from .. import plugins

    out: dict[str, Decoder] = {}
    for _name, decl in sorted(plugins.declared(root).items()):
        if decl.package.kind != "decoder":
            continue
        for module in sorted(decl.package.modules):
            if module in overridden:
                continue
            built = _load_packaged(decl, module)
            if built is not None:
                out[module] = built
    return out


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
            f"stem, not a path — one a declared package carries ({', '.join(BUILTIN_MODULES)}) "
            f"or a file in {CONSUMER_DIR}/. Add {CONSUMER_DIR}/{name}.py, or correct the name"
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
    from ..acquire import typesfile

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
    for ext, name in listed.decoders.items():
        out[f".{ext}"] = (name, listed.where_decoder(ext))
    _BINDINGS[key] = out
    return out


def meta_bindings(root: Path | None) -> dict[str, str]:
    """`.fux/formats.toml [meta]` — metadata key -> index field, or `"none"`.

    🔴 **It outranks the decoder's claim**, exactly as `[decoders]` outranks a
    built-in's `EXTENSIONS` ([SR-TYPES](../../records/0128_types-list.md)
    decision 13). **One table for the repo while the claim is per decoder** —
    so binding `doc_id = "ctx"` moves it for every decoder that emits `doc_id`.
    That is the intended trade: the claim is where per-format knowledge lives,
    the binding is where a repo states one policy.
    """
    if root is None:
        return {}
    from ..acquire import typesfile

    # Dispatch, not policy: an absent file binds nothing here. That the file
    # must exist is `read_types`'s (ingest) and `_limits`'s (every capped
    # decoder) to say, once, with the remedy.
    path = root / TYPES_FILE
    if not path.is_file():
        return {}
    st = path.stat()
    # Cached on the file's stat, like `_BINDINGS` (W-239): this runs once per
    # document, and re-parsing the types file each time was 13% of an ingest.
    key = (str(path), st.st_mtime_ns, st.st_size, st.st_ino)
    hit = _META.get(key)
    if hit is None:
        hit = _META[key] = dict(typesfile.read(root, TYPES_FILE).meta)
    return dict(hit)


_META: dict[tuple[str, int, int, int], dict[str, str]] = {}


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
        if path.stem == PROSE_DECODER:
            # 🔴 **Refused, not shadowed.** `decoder=prose` on a URL line names
            # the already-text branch and never reaches a module, so this file
            # would be loaded, registered, and then never called for the one
            # name it answers to. Failing at registry build is the only place
            # the consumer finds out.
            raise FuxError(
                f"{CONSUMER_DIR}/{path.name} takes the reserved name {PROSE_DECODER!r}. "
                f"`decoder={PROSE_DECODER}` names the already-text path and no module, so "
                f"this file would never be called. Rename it (`{PROSE_DECODER}text.py`, "
                "`plain.py`) and bind the extensions you want it to read in "
                f"{TYPES_FILE} [decoders]"
            )
        out[path.stem] = _load_consumer(path, path.stem)
    return out


def decoder_named(name: str, root: Path | None = None) -> Decoder | None:
    """The decoder module called `name`, or `None` — the pipe ruling's lookup.

    **A URL line names a decoder by STEM** (`decoder=xlsx`), which is the same
    vocabulary `.fux/formats.toml [decoders]` uses and the same key SR-DECODE
    decision 5 resolves an override on.

    Precedence is `registry()`'s first two steps and **deliberately not its
    third**: a consumer module of that name replaces the built-in wholesale, and
    the `[decoders]` binding table is **not consulted at all**. That table maps
    an **extension** to a module — it decides what a *file* gets and what
    `fux add` *proposes* — and letting it re-route a line would undo the whole
    point of declaring one: the line is the most specific thing there is
    ("Precedence, for the record", `work/proposals/fetcher-routing.md` §2).

    ⚠ **`prose` returns `None`, and the caller must check for it first.** It
    names a branch rather than a module (`PROSE_DECODER`), so *"no module"* and
    *"no decoder runs"* are the same answer here and opposite outcomes upstream.
    """
    if name == PROSE_DECODER:
        return None
    consumer = _consumer_decoders(root)
    if name in consumer:
        return consumer[name]
    if root is None:
        return None
    from .. import plugins

    resolved = plugins.resolve(root, "decoder", name)
    if resolved.how == "package":
        return _load_packaged(resolved.declared, name)
    return None


def _first_party_extensions(name: str) -> tuple[str, ...]:
    """`constants.toml [decoders.<name>] extensions` — read, never imported.

    🔴 **Nothing is imported to answer this** (SR-PLUGINS P3): the default
    allowlist and the generated bindings are about what fux CAN read, and a
    package nobody declared must not be executed to say so.
    `tests/decode/test_decoder_versions.py` holds each module's `EXTENSIONS` equal
    to its row.
    """
    return tuple(sorted(str(e).lower() for e in fixed(f"decoders.{name}", "extensions")))


@functools.cache
def builtin_extensions() -> tuple[str, ...]:
    """Every extension a **built-in** decoder claims, sorted.

    *Built-in* means first-party since W-289 phase 2: a module a
    `fux-decoder-*` package carries, declared here or not.

    ⚠ **Built-ins only, deliberately — never `registry(root)`.** This feeds
    `DEFAULT_TYPES`, and a default allowlist derived from consumer code would
    mean that dropping a `logdoc.py` into `.fux/decoders/` silently starts
    walking every `.log` file in the repo. **Adding a decoder must not, by
    itself, change what is indexed**: a consumer says what is a document in
    `.fux/formats.toml`, which is a committed line a human wrote.
    """
    out: set[str] = set()
    for name in BUILTIN_MODULES:
        out.update(_first_party_extensions(name))
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
        for ext in _first_party_extensions(name):
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
        return f"{fixed('decoders', 'reason_no_decoder')}{suffix}"
    return f"{decoder.name}{fixed('decoders', 'reason_nothing_readable')}{suffix}"


def decode(raw: bytes, rel_path: str, root: Path | None = None) -> str | None:
    """Bytes -> Markdown, or `None` when a model is needed to read it.

    Returns `None` for an unclaimed extension too — callers treat "no decoder"
    and "a decoder that could not extract text" the same way, because the
    document is equally unreadable either way and the queue records the reason.
    """
    decoder = registry(root).get(_suffix(rel_path))
    if decoder is None:
        return None
    return decode_with(decoder, raw, rel_path, root)


def decode_with(
    decoder: Decoder, raw: bytes, rel_path: str, root: Path | None = None
) -> str | None:
    """Run one decoder that has **already been chosen**. Bytes -> Markdown, or `None`.

    🔴 **Factored out of `decode()` for the pipe ruling and for nothing else.**
    `decode()` chooses by extension, which is the right question about a file;
    a URL line declares its decoder by name (`decoder_named`) and then needs the
    identical call, the identical `bound_root`, and the identical
    `DecodeFailed` — so the two paths share the body rather than each having
    one. Two copies of this would diverge in exactly the way that makes one
    plane's failure a crash and the other's a skip.
    """
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
