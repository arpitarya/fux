"""`.fux/config/plugins.toml` - the packages a repository declares (W-289, SR-PLUGINS).

Only the engine is mandatory. Every decoder, fetcher and extension package is
**declared per repository** in a committed `.fux/config/plugins.toml`, **pinned** by
version and digest, and **refused loudly** when missing or drifted — so two
machines on one repository can never build different indexes because of what
each happened to have installed ([SR-LAW-2](../../records/0004_LAW-2-zero-cost.md),
[SR-PLUGINS](../../records/0165_plugins.md)).

The decisions this module implements, by SR-PLUGINS number:

- **P2** the file: one `[[package]]` row per package — `name`, `version`,
  `digest`, and `suffixes` for a third-party decoder. Read once per process.
- **P3** declared, not detected: a package runs only if declared; an installed
  package nobody declared is never consulted (`for_suffix`, `for_fetch`).
- **P4** missing or drifted is a hard error naming the package, the expected
  version and digest, and the install line (`check`, `verify`, `require`).
- **P5 / P6** the suffix scan: which suffixes in the configured sources have no
  declared package, and which packages a scan proposes (`scan`, `undeclared`,
  `propose`).
- **P7** discovery by fixed import name only — `fux_<kind>_<subject>` — and
  **no entry-point scan** (`load`).
- **P8** precedence: a consumer override file beats a declared package, which
  beats nothing (`resolve`).

🔴 **Nothing here imports a package to inspect it.** Versions come from
`importlib.metadata`, digests from the files `importlib.util.find_spec` locates
— neither executes the package — so `fux doctor` and `fux setup` stay offline
(L5) even when a declared fetcher carries network code. `load` is the one
function that executes a package, and only after `verify` passed.

The first-party table is `constants.toml [plugins.packages]` (L12): fixed
identity, never a knob.
"""

from __future__ import annotations

import base64
import hashlib
import importlib.metadata
import importlib.util
import json
import re
import tomllib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .constants import fixed, table
from .errors import FuxError

__all__ = [
    "Declared",
    "IndexPin",
    "Package",
    "Resolution",
    "check",
    "closure",
    "declared",
    "exists",
    "fetcher_names",
    "first_party",
    "for_decoder_module",
    "for_fetch",
    "for_suffix",
    "check_index",
    "index_install_line",
    "indexes",
    "locate_index",
    "parse_indexes",
    "pin_index",
    "segment_digest",
    "segment_docs",
    "segment_root",
    "verify_index",
    "install_line",
    "installed_digest",
    "installed_version",
    "is_suffix_declared",
    "load",
    "load_decoder",
    "notes",
    "package_for_module",
    "package_for_suffix",
    "package_named",
    "parse",
    "path",
    "pin",
    "problems",
    "propose",
    "read",
    "render",
    "require",
    "reset",
    "resolve",
    "scan",
    "stamp",
    "undeclared",
    "unread",
    "verify",
]


@dataclass(frozen=True)
class Package:
    """What a distribution IS - from the first-party table, or its name."""

    name: str
    kind: str
    subject: str
    module: str
    suffixes: tuple[str, ...]
    #: Decoder module names it carries — what a URL line's `decoder=` names.
    modules: tuple[str, ...]
    depends: tuple[str, ...]
    first_party: bool

    @property
    def fetch(self) -> str | None:
        """The `fetch=` name a fetcher package answers to; `None` otherwise."""
        return self.subject if self.kind == "fetcher" else None


@dataclass(frozen=True)
class Declared:
    """One `[[package]]` row of `.fux/config/plugins.toml`."""

    package: Package
    version: str
    #: `sha256:<hex>`, or empty when the row is not pinned yet (P4 refuses it).
    digest: str

    @property
    def name(self) -> str:
        return self.package.name


@dataclass(frozen=True)
class Resolution:
    """P8: where one decoder or fetcher name resolves, and how."""

    #: `"override"` (a consumer file), `"package"` (a declared package) or `None`.
    how: str | None
    name: str
    path: Path | None = None
    declared: Declared | None = None


@dataclass(frozen=True)
class IndexPin:
    """One `kind = "index"` row of `.fux/config/plugins.toml` (SR-PKG-INDEX d2).

    A package that ships a fux index segment — data, never code. It is located
    by its registry names, never by a path (d5), and nothing in it is executed.
    """

    name: str
    version: str
    #: `sha256:<hex>` over the segment files, or empty when not pinned yet.
    digest: str
    npm: str | None = None
    pypi: str | None = None

    @property
    def import_name(self) -> str | None:
        """The PyPI distribution's normalised name — the segment's import package."""
        return re.sub(r"[-_.]+", "_", self.pypi).lower() if self.pypi else None


# -- the first-party table -----------------------------------------------------


def _strings(value, where: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise FuxError(f"{where} must be a list of strings")
    return tuple(value)


def split_name(name: str) -> tuple[str, str]:
    """`fux-<kind>-<subject>` -> `(kind, subject)`; anything else is refused.

    The naming rule is the whole of discovery (P7): the distribution's name
    decides its import name, so a name that does not follow it has nothing fux
    could import.
    """
    prefix = fixed("plugins", "dist_prefix")
    kinds = fixed("plugins", "kinds")
    if isinstance(name, str) and name.startswith(prefix):
        kind, sep, subject = name[len(prefix):].partition("-")
        if sep and kind in kinds and subject and subject.replace("-", "").isalnum() and subject == subject.lower():
            return kind, subject
    raise FuxError(
        f"{name!r} is not a plugin package name: it must read "
        f"`{prefix}<kind>-<subject>` with kind one of {', '.join(kinds)} (SR-PLUGINS P7)"
    )


def import_name(kind: str, subject: str) -> str:
    """P7: the one import name a package is loaded by."""
    return f"{fixed('plugins', 'import_prefix')}{kind}_{subject.replace('-', '_')}"


_FIRST_PARTY: "dict[str, Package] | None" = None


def first_party() -> dict[str, Package]:
    """Every first-party package, by distribution name, from `constants.toml`."""
    global _FIRST_PARTY
    if _FIRST_PARTY is None:
        out: dict[str, Package] = {}
        for name, row in sorted(table("plugins.packages").items()):
            kind, subject = split_name(name)
            where = f"constants.toml [plugins.packages.{name}]"
            if row.get("kind") != kind:
                raise FuxError(f"{where}: kind {row.get('kind')!r} disagrees with the name")
            out[name] = Package(
                name=name,
                kind=kind,
                subject=subject,
                module=import_name(kind, subject),
                suffixes=_strings(row["suffixes"], f"{where} suffixes"),
                modules=_strings(row["modules"], f"{where} modules"),
                depends=_strings(row["depends"], f"{where} depends"),
                first_party=True,
            )
        _FIRST_PARTY = out
    return _FIRST_PARTY


def package_named(name: str, suffixes: "tuple[str, ...]" = ()) -> Package:
    """The first-party package `name`, or a third-party one derived from it.

    🔴 **A first-party name cannot be redefined by a declaration** — its kind,
    suffixes and dependencies are this release's, and a repository that could
    restate them could make one package claim another's formats.
    """
    known = first_party()
    if name in known:
        return known[name]
    kind, subject = split_name(name)
    return Package(
        name=name,
        kind=kind,
        subject=subject,
        module=import_name(kind, subject),
        suffixes=tuple(sorted(s.lower() for s in suffixes)),
        modules=(subject.replace("-", "_"),) if kind == "decoder" else (),
        depends=(),
        first_party=False,
    )


# -- P2: the file --------------------------------------------------------------


def path(root: Path) -> Path:
    """`.fux/config/plugins.toml` under `root`."""
    return root / fixed("plugins", "file")


def parse(text: str, origin: str) -> dict[str, Declared]:
    """P2: the declaration's package rows, validated. Malformed is a `FuxError`
    naming the file.

    The order of rows is presentation: the result is keyed and sorted by name,
    so two files declaring the same set are the same declaration (L4). The
    `kind = "index"` rows are validated too, and returned by `parse_indexes`.
    """
    return _parse(text, origin)[0]


def parse_indexes(text: str, origin: str) -> dict[str, IndexPin]:
    """SR-PKG-INDEX d2: the declaration's `kind = "index"` rows, by name."""
    return _parse(text, origin)[1]


def _parse_index_row(row: dict, origin: str, row_key: str) -> IndexPin:
    """One `kind = "index"` row, or a `FuxError` naming what is wrong with it."""
    allowed = set(fixed("plugins.index", "keys"))
    name = row.get("name")
    label = name if isinstance(name, str) and name else f"a `[[{row_key}]]` index row"
    if "suffixes" in row:
        raise FuxError(
            f"{origin}: {label} is an index package, which reads no format - delete its "
            "`suffixes` key (SR-PKG-INDEX d2)"
        )
    unknown = sorted(set(row) - allowed)
    if unknown:
        raise FuxError(f"{origin}: {label} carries unknown key(s) {', '.join(unknown)} (SR-PKG-INDEX d2)")
    if not isinstance(name, str) or not re.fullmatch(fixed("plugins.index", "name_pattern"), name):
        raise FuxError(
            f"{origin}: an index row's `name` must match {fixed('plugins.index', 'name_pattern')} "
            f"(got {_json_value(name)}) - it names a directory under .fux/runtime/ (SR-PKG-INDEX d2)"
        )
    version, digest = row.get("version"), row.get("digest", "")
    if not isinstance(version, str) or not version:
        raise FuxError(f"{origin}: {name} has no `version` - every package is pinned")
    prefix = fixed("plugins", "digest_prefix")
    if not isinstance(digest, str) or (digest and not digest.startswith(prefix)):
        raise FuxError(f"{origin}: {name}'s `digest` must read `{prefix}<hex>`")
    names = {}
    for key in ("npm", "pypi"):
        value = row.get(key)
        if value is not None and (not isinstance(value, str) or not value):
            raise FuxError(f"{origin}: {name}'s `{key}` must be a package name")
        names[key] = value
    if not names["npm"] and not names["pypi"]:
        raise FuxError(
            f"{origin}: {name} names neither an `npm` nor a `pypi` package, so nothing can "
            "locate it (SR-PKG-INDEX d2)"
        )
    return IndexPin(name=name, version=version, digest=digest, npm=names["npm"], pypi=names["pypi"])


def _parse(text: str, origin: str) -> "tuple[dict[str, Declared], dict[str, IndexPin]]":
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise FuxError(f"{origin}: not valid TOML ({exc})") from exc
    row_key = fixed("plugins", "table")
    allowed = set(fixed("plugins", "keys"))
    extra = sorted(set(data) - {row_key})
    if extra:
        raise FuxError(
            f"{origin}: unknown top-level key(s) {', '.join(extra)}; the file holds "
            f"`[[{row_key}]]` rows and nothing else (SR-PLUGINS P2)"
        )
    rows = data.get(row_key, [])
    if not isinstance(rows, list):
        raise FuxError(f"{origin}: `{row_key}` must be an array of tables, written `[[{row_key}]]`")
    prefix = fixed("plugins", "digest_prefix")
    declarable = set(fixed("plugins", "declarable")) | {"extension"}
    out: dict[str, Declared] = {}
    index_kind = fixed("plugins.index", "kind")
    found_indexes: dict[str, IndexPin] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise FuxError(f"{origin}: every `[[{row_key}]]` entry must be a table")
        if "kind" in row:
            if row["kind"] != index_kind:
                raise FuxError(
                    f"{origin}: a `[[{row_key}]]` row's `kind` may only be {index_kind!r} - a "
                    "decoder, fetcher or extension package's kind is its name (SR-PKG-INDEX d2)"
                )
            pin = _parse_index_row(row, origin, row_key)
            if pin.name in out or pin.name in found_indexes:
                raise FuxError(f"{origin}: {pin.name} is declared twice")
            found_indexes[pin.name] = pin
            continue
        unknown = sorted(set(row) - allowed)
        if unknown:
            raise FuxError(f"{origin}: a `[[{row_key}]]` row carries unknown key(s) {', '.join(unknown)}")
        name, version, digest = row.get("name"), row.get("version"), row.get("digest", "")
        if not isinstance(name, str) or not name:
            raise FuxError(f"{origin}: a `[[{row_key}]]` row has no `name`")
        if not isinstance(version, str) or not version:
            raise FuxError(f"{origin}: {name} has no `version` - every package is pinned")
        if not isinstance(digest, str) or (digest and not digest.startswith(prefix)):
            raise FuxError(f"{origin}: {name}'s `digest` must read `{prefix}<hex>`")
        if name in out or name in found_indexes:
            raise FuxError(f"{origin}: {name} is declared twice")
        suffixes = row.get("suffixes")
        if name in first_party():
            if suffixes is not None:
                raise FuxError(
                    f"{origin}: {name} is first-party, and its suffixes are fux's to state; "
                    "delete the `suffixes` key"
                )
            package = first_party()[name]
        else:
            package = package_named(name, _strings(suffixes or [], f"{origin}: {name} suffixes"))
            if package.kind == "decoder" and not package.suffixes:
                raise FuxError(
                    f"{origin}: {name} is a third-party decoder and must state the "
                    "`suffixes` it claims"
                )
            if package.kind != "decoder" and suffixes:
                raise FuxError(f"{origin}: only a decoder package claims suffixes; {name} is a {package.kind}")
        if package.kind not in declarable:  # pragma: no cover - the kinds table is closed
            raise FuxError(f"{origin}: {name}: a {package.kind} package cannot be declared")
        out[name] = Declared(package=package, version=version, digest=digest)
    claimed: dict[str, str] = {}
    for name, decl in sorted(out.items()):
        for suffix in decl.package.suffixes:
            if suffix in claimed:
                raise FuxError(
                    f"{origin}: {suffix} is claimed by both {claimed[suffix]} and {name}; "
                    "exactly one declared package may read a format"
                )
            claimed[suffix] = name
    return dict(sorted(out.items())), dict(sorted(found_indexes.items()))


#: P2: read once per process, per repository root — and per version of the
#: file. The key carries the file's stat, so a long-lived process (`fux mcp`,
#: the daemon) sees an edited declaration the way `decode.registry()` sees an
#: edited `.fux/config/formats.toml`, while a 10 000-document walk still parses it once.
_CACHE: dict[tuple, "tuple[dict[str, Declared], dict[str, IndexPin]] | None"] = {}


def reset() -> None:
    """Forget what was read - `fux setup` calls it after writing the file."""
    _CACHE.clear()


def stamp(root: Path) -> tuple:
    """The declaration's identity for a cache key: its path and stat, or absent."""
    target = path(Path(root).resolve())
    try:
        st = target.stat()
    except OSError:
        return (str(target), None)
    return (str(target), st.st_mtime_ns, st.st_size, st.st_ino)


def _read_all(root: Path) -> "tuple[dict[str, Declared], dict[str, IndexPin]] | None":
    key = stamp(root)
    if key not in _CACHE:
        if key[1] is None:
            _CACHE[key] = None
        else:
            target = path(Path(root).resolve())
            _CACHE[key] = _parse(target.read_text(encoding="utf-8"), fixed("plugins", "file"))
    return _CACHE[key]


def read(root: Path) -> "dict[str, Declared] | None":
    """The declaration's package rows, or `None` when `.fux/config/plugins.toml`
    does not exist."""
    found = _read_all(root)
    return None if found is None else found[0]


def indexes(root: Path) -> dict[str, IndexPin]:
    """Every `kind = "index"` row (SR-PKG-INDEX d2); empty when there is no file."""
    found = _read_all(root)
    return {} if found is None else found[1]


def exists(root: Path) -> bool:
    """Is there a `.fux/config/plugins.toml` at all? Absent means prose only (P3)."""
    return path(Path(root)).is_file()


def declared(root: Path) -> dict[str, Declared]:
    """Every declared package; empty when there is no file."""
    return read(root) or {}


# -- P3: declared, never detected ----------------------------------------------


def for_suffix(root: Path, suffix: str) -> Declared | None:
    """The declared package that reads `suffix`, or `None`."""
    suffix = suffix.lower()
    for decl in declared(root).values():
        if suffix in decl.package.suffixes:
            return decl
    return None


def is_suffix_declared(root: Path, suffix: str) -> bool:
    """P3: is some declared package the reader of `suffix`?"""
    return for_suffix(root, suffix) is not None


def for_fetch(root: Path, name: str) -> Declared | None:
    """The declared fetcher package a `fetch=<name>` line resolves to, or `None`."""
    for decl in declared(root).values():
        if decl.package.fetch == name:
            return decl
    return None


def for_decoder_module(root: Path, module: str) -> Declared | None:
    """The declared decoder package carrying decoder module `module`, or `None`."""
    for decl in declared(root).values():
        if decl.package.kind == "decoder" and module in decl.package.modules:
            return decl
    return None


# -- P4: pinned, and refused when missing or drifted ---------------------------


def installed_version(name: str) -> str | None:
    """The installed distribution's version, read from its metadata."""
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _record_hash(data: bytes) -> str:
    """RECORD's own hash spelling: urlsafe base64 of the sha256, unpadded."""
    digest = hashlib.sha256(data.replace(b"\r\n", b"\n")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def installed_digest(module: str) -> str | None:
    """`sha256:<hex>` over the import package's files, or `None` if absent.

    🔴 **Located, never imported.** `find_spec` on a top-level name does not
    execute it.

    The lines are RECORD's — `<path>,sha256=<urlsafe b64>` — over the files the
    import name resolves to, sorted, with CRLF read as LF. **Not the RECORD
    file itself**: that also lists `INSTALLER` and `direct_url.json`, which
    differ by installer and by machine, so a pip install, a uv install, an
    editable checkout and a wheel of the same release all agree here.
    """
    try:
        spec = importlib.util.find_spec(module)
    except (ImportError, ValueError):
        return None
    if spec is None:
        return None
    files: list[tuple[str, Path]] = []
    locations = list(spec.submodule_search_locations or [])
    if locations:
        for base in sorted(Path(p) for p in locations):
            for item in sorted(base.rglob("*")):
                if not item.is_file() or "__pycache__" in item.parts or item.suffix == ".pyc":
                    continue
                files.append((f"{module}/{item.relative_to(base).as_posix()}", item))
    elif spec.origin and Path(spec.origin).is_file():
        origin = Path(spec.origin)
        files.append((origin.name, origin))
    else:
        return None
    lines = [f"{rel},sha256={_record_hash(item.read_bytes())}" for rel, item in sorted(files)]
    body = "\n".join(lines).encode("utf-8")
    return fixed("plugins", "digest_prefix") + hashlib.sha256(body).hexdigest()


def segment_digest(directory: Path) -> str | None:
    """`sha256:<hex>` over an index segment's files, or `None` if it has none.

    The ONE digest of a shipped index (SR-PKG-INDEX): `fux pack` writes it into
    the manifest and the `kind = "index"` pin verifies it. It covers the files
    `[plugins.index] segment` names, relative to `directory`, in the same RECORD
    line form as `installed_digest` — so a wheel and an npm tarball holding the
    same segment bytes agree, whatever else either distribution carries.
    """
    files = sorted(
        {item for pattern in fixed("plugins.index", "segment") for item in directory.glob(pattern) if item.is_file()}
    )
    if not files:
        return None
    lines = [f"{item.relative_to(directory).as_posix()},sha256={_record_hash(item.read_bytes())}" for item in files]
    body = "\n".join(lines).encode("utf-8")
    return fixed("plugins", "digest_prefix") + hashlib.sha256(body).hexdigest()


def _shard_glob() -> str:
    """The one `[plugins.index] segment` glob that names the document shards."""
    suffix = fixed("index", "shard_suffix")
    return next(g for g in fixed("plugins.index", "segment") if g.endswith(suffix))


def segment_docs(directory: Path) -> int:
    """How many document records a segment's shards hold — read off the shards,
    never the manifest's `docs` (SR-PKG-INDEX d3: the manifest is not covered)."""
    header = fixed("index", "shard_header_lines")
    total = 0
    for item in sorted(directory.glob(_shard_glob())):
        if item.is_file():
            lines = [line for line in item.read_bytes().split(b"\n") if line.strip()]
            total += max(0, len(lines) - header)
    return total


# -- SR-PKG-INDEX: the `kind = "index"` pin --------------------------------------


def index_install_line(pin: IndexPin, runtime: str | None = None) -> str:
    """The one install line for an index pin in `runtime` (Python unless
    `"node"`). fux never runs it."""
    if runtime == "node":
        return f"{fixed('plugins.index', 'npm_install')} {pin.npm}@{pin.version}"
    return install_line([(pin.pypi, pin.version)])


def segment_root(pin: IndexPin) -> Path | None:
    """SR-PKG-INDEX d5: the installed segment's directory, or `None`.

    🔴 **Located, never imported**: `find_spec` on a top-level name does not
    execute it, and a namespace package (no `__init__.py`) resolves too. It must
    resolve to exactly one directory, and that directory must hold the manifest.
    """
    if not pin.import_name:
        return None
    try:
        spec = importlib.util.find_spec(pin.import_name)
    except (ImportError, ValueError):
        return None
    locations = list(spec.submodule_search_locations or []) if spec is not None else []
    if len(locations) != 1:
        return None
    directory = Path(locations[0])
    return directory if (directory / fixed("plugins.index", "manifest")).is_file() else None


def _json_value(value) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def _foreign(directory: Path) -> "dict | None":
    """d6: the first shard header key that is not the reader's, or `None`."""
    want = {key: fixed("index", source) for key, source in fixed("plugins.index", "header_keys").items()}
    index_glob = _shard_glob()
    for shard in sorted(directory.glob(index_glob)):
        if not shard.is_file():
            continue
        with shard.open("rb") as handle:
            first = handle.readline()
        try:
            header = json.loads(first)
        except ValueError:
            header = {}
        if not isinstance(header, dict):
            header = {}
        for key, value in want.items():
            if header.get(key) != value:
                return {
                    "shard": shard.relative_to(directory).as_posix(),
                    "key": key,
                    "got_value": _json_value(header.get(key)),
                    "want_value": _json_value(value),
                }
    return None


def _manifest_digest(directory: Path) -> str:
    """What the manifest claims as the digest, as a word for the refusal."""
    try:
        data = json.loads((directory / fixed("plugins.index", "manifest")).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "no digest"
    value = data.get("digest") if isinstance(data, dict) else None
    return value if isinstance(value, str) and value else "no digest"


def _refusal(code: str, **values) -> str:
    return fixed("pkg_index_refusals", code).format(**values)


def check_index(pin: IndexPin) -> str | None:
    """SR-PKG-INDEX d7: why this index pin cannot be read, or `None` when it can.

    The checks run in the record's order, and the words are
    `constants.toml [pkg_index_refusals]`, shared with the Node twin.
    """
    return _check_index(pin)[1]


def _check_index(pin: IndexPin) -> "tuple[str | None, str | None]":
    """`(code, refusal)` — the code is what the differential test compares."""
    name, version = pin.name, pin.version
    expected = f"pinned {name} {version}" + (f" {pin.digest}" if pin.digest else "")
    if not pin.pypi:
        return "no_registry", _refusal("no_registry", name=name, key="pypi", expected=expected)
    install = index_install_line(pin)
    have = installed_version(pin.pypi)
    if have is None:
        return "missing", _refusal("missing", name=name, expected=expected, install=install)
    if have != version:
        return "other_version", _refusal("other_version", name=name, have=have, expected=expected, install=install)
    if not pin.digest:
        return "no_digest", _refusal("no_digest", name=name, version=version)
    manifest = fixed("plugins.index", "manifest")
    directory = segment_root(pin)
    if directory is None:
        return "no_segment", _refusal("no_segment", name=name, have=have, manifest=manifest, install=install)
    got = segment_digest(directory) or "nothing"
    if got != pin.digest:
        return "drifted", _refusal("drifted", name=name, have=have, got=got, expected=expected, install=install)
    claimed = _manifest_digest(directory)
    if claimed != got:
        return "manifest", _refusal(
            "manifest", name=name, have=have, manifest=manifest, claimed=claimed, got=got, install=install
        )
    foreign = _foreign(directory)
    if foreign is not None:
        return "foreign", _refusal("foreign", name=name, have=have, **foreign)
    return None, None


def verify_index(pin: IndexPin) -> None:
    """d7 as a refusal."""
    problem = check_index(pin)
    if problem is not None:
        raise FuxError(f"{fixed('plugins', 'file')}: {problem} (SR-PLUGINS P4)")


def locate_index(pin: IndexPin) -> Path:
    """Verify, then the segment's directory — the only way a segment is read."""
    verify_index(pin)
    directory = segment_root(pin)
    assert directory is not None  # verify_index located it
    return directory


def pin_index(pypi: str, npm: str | None = None, name: str | None = None) -> IndexPin:
    """An index row for the installed PyPI distribution `pypi` (`fux setup
    --index`, `--pin`): its version and its segment's digest, from what is
    installed. Refused when it is not installed or holds no segment."""
    version = installed_version(pypi)
    if version is None:
        raise FuxError(f"{pypi} is not installed, so there is no index segment to pin")
    pin = IndexPin(name=name or pypi.lower(), version=version, digest="", npm=npm, pypi=pypi)
    directory = segment_root(pin)
    if directory is None:
        raise FuxError(
            f"{pypi} {version} is installed but holds no index segment "
            f"(no {fixed('plugins.index', 'manifest')}) (SR-PKG-INDEX d5)"
        )
    return IndexPin(
        name=pin.name, version=version, digest=segment_digest(directory) or "", npm=npm, pypi=pypi
    )


def _fux_version() -> str:
    from . import __version__

    return __version__


def install_line(names_versions: "list[tuple[str, str]]") -> str:
    """The one install line for `(name, version)` pairs. fux never runs it."""
    pins = " ".join(f"{name}=={version}" for name, version in sorted(names_versions))
    return f"{fixed('plugins', 'install')} {pins}"


def check(decl: Declared) -> str | None:
    """P4: why this declared package cannot run, or `None` when it can."""
    name, want = decl.name, decl.version
    expected = f"declared {name}=={want}" + (f" {decl.digest}" if decl.digest else "")
    line = install_line([(name, want)])
    if decl.package.first_party and want != _fux_version():
        return (
            f"{name} is pinned at {want}, but a first-party package must equal fux's "
            f"version {_fux_version()} - run `{install_line([(name, _fux_version())])}`, "
            "then `fux setup --pin`"
        )
    have = installed_version(name)
    if have is None:
        return f"{name} is declared and not installed ({expected}) - run `{line}`"
    if have != want:
        return f"{name} {have} is installed, {expected} - run `{line}`"
    if not decl.digest:
        return f"{name} {want} is declared without a digest - run `fux setup --pin` to pin it"
    got = installed_digest(decl.package.module)
    if got is None:
        return (
            f"{name} {have} is installed but its import name {decl.package.module} does not "
            f"resolve ({expected}) - reinstall it: `{line}`"
        )
    if got != decl.digest:
        return (
            f"{name} {have} has drifted: installed {got}, {expected}. Reinstall it "
            f"(`{line}`), or re-pin a deliberate change with `fux setup --pin`"
        )
    return None


def verify(decl: Declared) -> None:
    """P4 as a refusal."""
    problem = check(decl)
    if problem is not None:
        raise FuxError(f"{fixed('plugins', 'file')}: {problem} (SR-PLUGINS P4)")


def closure(names: "list[str] | set[str] | tuple[str, ...]") -> list[str]:
    """`names` plus every package they depend on, transitively, sorted."""
    seen: set[str] = set()
    todo = list(names)
    while todo:
        name = todo.pop()
        if name in seen:
            continue
        seen.add(name)
        todo.extend(package_named(name).depends if name in first_party() else ())
    return sorted(seen)


def problems(root: Path) -> list[str]:
    """Every reason the declaration cannot run as written, in name order.

    P4 per package, a declared package whose dependency is undeclared, and P10:
    a declared fetcher with no declared HTML decoder (every fetcher emits HTML).
    """
    found = declared(root)
    out: list[str] = []
    for name, decl in found.items():
        problem = check(decl)
        if problem is not None:
            out.append(problem)
        for dep in decl.package.depends:
            if dep not in found:
                out.append(f"{name} needs {dep}, which is not declared - run `fux setup` to add it")
    for pin in indexes(root).values():  # SR-PKG-INDEX d7: index rows, the same gate
        problem = check_index(pin)
        if problem is not None:
            out.append(problem)
    needs = fixed("plugins", "fetcher_needs")
    fetchers = sorted(n for n, d in found.items() if d.package.kind == "fetcher")
    if fetchers and needs not in found:
        out.append(
            f"{', '.join(fetchers)} declared without {needs}: every fetcher returns HTML, "
            f"which nothing declared can read - declare {needs} (SR-PLUGINS P10)"
        )
    return out


def require(root: Path) -> dict[str, Declared]:
    """Refuse unless every declared package can run (P4); the declaration."""
    found = problems(root)
    if found:
        raise FuxError(
            f"{fixed('plugins', 'file')}: "
            + "; ".join(found)
            + " (SR-PLUGINS P4)"
        )
    return declared(root)


# -- P7: discovery by fixed name; P8: precedence --------------------------------


def load(decl: Declared):
    """P7: verify, then execute the declared package by its fixed import name.

    **A fresh module object per call**, never registered in `sys.modules`: a
    fetcher's `configure()` writes its module globals, and a module shared
    across calls would carry one run's settings into the next — the
    per-call file load this replaces never did.
    """
    verify(decl)
    spec = importlib.util.find_spec(decl.package.module)
    if spec is None or spec.loader is None:  # pragma: no cover - verify() located it
        raise FuxError(f"{decl.name}: {decl.package.module} could not be located")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise FuxError(f"{decl.name} failed to import: {exc}") from exc
    return module


def load_decoder(decl: Declared, module: str):
    """P7 for a decoder: verify, then import `<import name>.<module>`.

    **A normal import, registered in `sys.modules`** — unlike `load`, which
    hands a fetcher a fresh module per call for its `configure()` state. A
    decoder module is a function of `(raw, rel_path)` (SR-DECODE decision 1)
    and its siblings import each other by name: `fux_decoder_config.toml`
    imports `fux_decoder_json.json`, and `fux_decoder_mail.mail` imports
    `fux_decoder_html.html`. 🔴 **Only a declared package is ever imported
    here**, and `problems()` refuses a declared package whose dependency is
    not declared too, so the import graph never leaves the declaration.
    """
    import importlib

    if module not in decl.package.modules:
        raise FuxError(f"{decl.name} carries no decoder module {module!r} ({', '.join(decl.package.modules)})")
    verify(decl)
    target = f"{decl.package.module}.{module}"
    try:
        return importlib.import_module(target)
    except ModuleNotFoundError as exc:
        raise FuxError(
            f"{decl.name}: {target} could not be imported - {exc.name} is missing. "
            f"Reinstall it: `{install_line([(decl.name, decl.version)])}` (SR-PLUGINS P4)"
        ) from exc
    except Exception as exc:
        raise FuxError(f"{decl.name}: {target} failed to import: {exc}") from exc


def package_for_module(module: str) -> "Package | None":
    """The first-party decoder package that carries decoder module `module`."""
    for package in first_party().values():
        if package.kind == "decoder" and module in package.modules:
            return package
    return None


def package_for_suffix(suffix: str) -> "Package | None":
    """The first-party decoder package that reads `suffix`, declared or not."""
    name = _claims().get(suffix.lower())
    return first_party()[name] if name else None


def resolve(root: Path, kind: str, name: str) -> Resolution:
    """P8: `.fux/<kind>s/<name>.py` (the consumer's) > a declared package > none."""
    if kind == "fetcher":
        directory = root / fixed("files", "fetchers_dir")
        decl = for_fetch(root, name)
    elif kind == "decoder":
        directory = root / fixed("decoders", "consumer_dir")
        decl = for_decoder_module(root, name)
    else:
        raise FuxError(f"no {kind!r} plugin kind resolves by name; one of fetcher, decoder")
    override = directory / f"{name}.py"
    if override.is_file():
        return Resolution("override", name, path=override)
    if decl is not None:
        return Resolution("package", name, declared=decl)
    return Resolution(None, name)


def fetcher_names(root: Path) -> list[str]:
    """Every `fetch=` name this repository can run: the consumer's files in
    `.fux/fetchers/` and the declared fetcher packages (P8), sorted."""
    directory = root / fixed("files", "fetchers_dir")
    try:
        names = {p.stem for p in directory.glob("*.py")}
    except OSError:  # pragma: no cover - an unreadable directory
        names = set()
    names |= {d.package.fetch for d in declared(root).values() if d.package.fetch}
    return sorted(names)


# -- P5 / P6: what the sources need ---------------------------------------------


def _claims() -> dict[str, str]:
    """suffix -> the first-party package that reads it."""
    return {s: name for name, pkg in first_party().items() for s in pkg.suffixes}


def scan(root: Path) -> Counter:
    """Files per lowercase suffix in the configured directories.

    The same roots and hand-written `.fuxignore` lines ingest honours — and
    **an ignored directory is pruned, never entered** (W-244: a walk that lists
    `work/golden/` reads the sealed key's file names, L11). The
    blocks fux itself writes into `.fuxignore` are NOT honoured: a file fux
    wrote there because nothing could read it is exactly what this scan is for.
    Names only; no file is opened.
    """
    from .acquire import fuxignore
    from .acquire.sourcesfile import source_paths
    from .acquire.gitdir import _candidate_paths, ignored_dir
    from .config import load as load_config

    import unicodedata

    config = load_config(root)
    ignores = fuxignore.read(root)

    def prune(directory: Path) -> bool:
        rel = unicodedata.normalize("NFC", directory.relative_to(root).as_posix())
        return ignored_dir(ignores, rel) is not None

    counts: Counter = Counter()
    seen: set[str] = set()
    for entry in source_paths(root, config.sources_file):
        base = root / entry
        if not base.exists():
            continue
        for item in _candidate_paths(base, prune):
            rel = unicodedata.normalize("NFC", item.relative_to(root).as_posix())
            if rel in seen:
                continue
            seen.add(rel)
            if ignores.decide(rel, is_dir=False, hand_only=True).ignored:
                continue
            name = rel.rsplit("/", 1)[-1]
            dot = name.rfind(".")
            if dot > 0:
                counts[name[dot:].lower()] += 1
    return counts


def undeclared(counts: Counter, found: dict[str, Declared]) -> dict[str, tuple[int, str]]:
    """P5: suffix -> (files, the package that reads it) for every suffix a
    first-party package reads and no declared package does."""
    claims = _claims()
    covered = {s for d in found.values() for s in d.package.suffixes}
    return {
        suffix: (count, claims[suffix])
        for suffix, count in sorted(counts.items())
        if suffix in claims and suffix not in covered
    }


def unread(root: Path) -> dict[str, tuple[int, str]]:
    """P5: suffix -> (files, package) for every format in the sources that a
    first-party package reads and nothing in this repository does.

    `undeclared()` minus what a consumer decoder in `.fux/decoders/` claims —
    an override reads its format whether or not the package is declared (P8).
    """
    from . import decode

    claimed = decode.registry(root)
    return {
        suffix: row
        for suffix, row in undeclared(scan(root), declared(root)).items()
        if suffix not in claimed
    }


def notes(root: Path) -> list[str]:
    """What `fux ingest` prints on stderr about the declaration (P5).

    🔴 **Never silent** (W-289's hazard: *a corpus that loses its PDFs looks
    exactly like one that never had any*). One line when the file is missing —
    only Markdown and plain text are read, and `fux setup` is the lever — then
    one line per suffix the sources hold that nothing declared reads, with the
    count and the package. Names only; no file is opened.
    """
    rel = fixed("plugins", "file")
    out: list[str] = []
    if not exists(root):
        out.append(
            f"fux: no {rel} - only Markdown and plain text are read. Run `fux setup` to "
            "declare the decoder packages your sources need (SR-PLUGINS)"
        )
    for suffix, (count, package) in unread(root).items():
        out.append(
            f"fux: {count} {suffix} file(s) not read - no declared package reads {suffix}; "
            f"declare {package} in {rel} (`fux setup` adds it) (SR-PLUGINS P5)"
        )
    return out


def _url_needs(root: Path) -> tuple[set[str], set[str]]:
    """`(fetch names, decoder modules)` the URL list names; empty without one."""
    from .acquire import sourcesfile
    from .config import load as load_config

    config = load_config(root)
    if config.url is None:
        return set(), set()
    target = root / config.url.sources_file
    if not target.is_file():
        return set(), set()
    entries = sourcesfile.parse(target.read_text(encoding="utf-8"), origin=config.url.sources_file).urls
    fetches = {e.attrs["fetch"] for e in entries if not e.exclude and "fetch" in e.attrs}
    decoders = {e.attrs["decoder"] for e in entries if not e.exclude and "decoder" in e.attrs}
    return fetches, decoders


def propose(root: Path) -> list[str]:
    """P6: the first-party packages this repository's sources need, sorted.

    Every suffix in the configured directories a package reads; every
    `fetch=` and `decoder=` the URL list names; the HTML decoder whenever a
    fetcher is proposed (P10); and the closure of all of it. A `fetch=` that
    names a consumer file in `.fux/fetchers/` needs no package.
    """
    claims = _claims()
    wanted = {claims[s] for s in scan(root) if s in claims}
    fetches, decoders = _url_needs(root)
    by_fetch = {p.fetch: n for n, p in first_party().items() if p.fetch}
    by_module = {m: n for n, p in first_party().items() for m in p.modules}
    overrides = root / fixed("files", "fetchers_dir")
    for name in fetches:
        if name in by_fetch and not (overrides / f"{name}.py").is_file():
            wanted.add(by_fetch[name])
    wanted |= {by_module[m] for m in decoders if m in by_module}
    if any(first_party()[n].kind == "fetcher" for n in wanted):
        wanted.add(fixed("plugins", "fetcher_needs"))
    return closure(wanted)


# -- writing the file -------------------------------------------------------------


def pin(name: str, suffixes: "tuple[str, ...]" = ()) -> Declared:
    """A row for `name` from what is installed, or unpinned when it is not.

    A first-party package is pinned at fux's own version (P11, lockstep); a
    third-party one at whatever is installed.
    """
    package = package_named(name, suffixes)
    if package.first_party:
        version = _fux_version()
    else:
        version = installed_version(name) or ""
        if not version:
            raise FuxError(f"{name} is not installed, so there is no version to pin")
    digest = ""
    if installed_version(name) == version:
        digest = installed_digest(package.module) or ""
    return Declared(package=package, version=version, digest=digest)


def render(rows: "list[Declared]", index_rows: "list[IndexPin] | tuple" = ()) -> str:
    """The file `fux setup` writes, rows sorted by name."""
    row_key = fixed("plugins", "table")
    lines = [
        "# .fux/config/plugins.toml -- the packages this repository's index needs (SR-PLUGINS).",
        "#",
        "# Committed. Only fux itself is mandatory; every decoder and fetcher package",
        "# runs only when declared here, at exactly this version and digest. An",
        "# installed package nobody declared is never loaded. A declared package that",
        "# is missing or differs stops fux with the install line -- two machines on",
        "# one repository never build different indexes.",
        "#",
        "# `fux setup` proposes rows from your sources; `fux setup --pin` re-pins every",
        "# row from what is installed, after an upgrade.",
    ]
    for decl in sorted(rows, key=lambda d: d.name):
        lines += ["", f"[[{row_key}]]", f'name = "{decl.name}"', f'version = "{decl.version}"']
        lines.append(f'digest = "{decl.digest}"')
        if not decl.package.first_party and decl.package.suffixes:
            quoted = ", ".join(f'"{s}"' for s in decl.package.suffixes)
            lines.append(f"suffixes = [{quoted}]")
    for pin in sorted(index_rows, key=lambda p: p.name):
        lines += ["", f"[[{row_key}]]", f'name = "{pin.name}"', f'kind = "{fixed("plugins.index", "kind")}"']
        lines += [f'version = "{pin.version}"', f'digest = "{pin.digest}"']
        for key in ("npm", "pypi"):
            if getattr(pin, key):
                lines.append(f'{key} = "{getattr(pin, key)}"')
    return "\n".join(lines) + "\n"
