"""`pkg:` locations — a pinned package's file, read where it is installed (W-301).

[SR-PKG-INDEX](../../../records/0166_pkg-index.md) decision 11. A record in a
pinned index segment was ingested from the **docs** package the segment's
manifest names in `content` (`npm`, `pypi`, `version`) — which may be another
package than the index package itself (codelaw: the index in
`@codelaw/rules-js-fux-index`, the docs in `@codelaw/rules-js`). So a hit from a
segment is addressed in the docs package:

    pkg:<docs package>@<content.version>#<the record's loc>

— the npm name when `content` has one, else the PyPI name, so the address is the
same string in both runtimes. The record's own `id` is unchanged (`file:…`): a
`pkg:` location is composed by the read plane and **never stored in a record**
([SR-RECORD](../../../records/0109_index-record.md)).

Reading one (`read`):

1. parse it; find the pin whose verified manifest names that package at that
   version (`plugins.locate_index` — the segment is verified before its
   manifest is read);
2. resolve the docs package **by module resolution from the repository**, never
   by a path: its version from `importlib.metadata`, its root from
   `importlib.util.find_spec` of the distribution's normalised name — located,
   never imported;
3. 🔴 **an installed docs version other than `content.version` is a refusal**
   naming both and the install line: the index was built from other bytes, so
   it would cite a file it never indexed;
4. join the fragment, collapse `..` and contain it inside that package's root
   (`source.contain`, the one containment function);
5. read the file in place and hash it with `content_sha` — the ledger sha the
   segment's record carries, so a fresh read compares directly against the
   indexed one. **Nothing is copied** (L3).

The words are `constants.toml [pkg_location_refusals]`, shared with the Node
twin `node/src/refer/pkgsrc.mjs`, which resolves through
`createRequire(<repo>/package.json)` and reads `content.npm` where this reads
`content.pypi`.
"""

from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path

from .. import plugins
from ..constants import fixed
from ..errors import FuxError

__all__ = [
    "Content",
    "Segment",
    "Read",
    "docs_root",
    "find_segment",
    "hit_fields",
    "is_pkg",
    "location",
    "parse",
    "read",
    "refuse",
    "segment",
    "segments",
]


def _refusal(code: str, **values) -> str:
    return fixed("pkg_location_refusals", code).format(**values)


@dataclass(frozen=True)
class Content:
    """The manifest's `content` — the docs package a segment indexes (d3)."""

    version: str
    npm: str | None = None
    pypi: str | None = None

    @property
    def name(self) -> str:
        """The name a `pkg:` location spells: npm's when present, else PyPI's."""
        return self.npm or self.pypi or ""


@dataclass(frozen=True)
class Segment:
    """A verified pin and the docs package its manifest names."""

    pin: plugins.IndexPin
    content: Content


@dataclass(frozen=True)
class Read:
    """One file read in place inside an installed docs package."""

    location: str
    loc: str
    path: Path
    content: bytes
    sha: str


def _content(pin: plugins.IndexPin, directory: Path) -> Content:
    manifest = fixed("plugins.index", "manifest")
    bad = FuxError(_refusal("content", index=pin.name, index_version=pin.version, manifest=manifest))
    try:
        data = json.loads((directory / manifest).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise bad from None
    raw = data.get("content") if isinstance(data, dict) else None
    if not isinstance(raw, dict):
        raise bad
    version, npm, pypi = raw.get("version"), raw.get("npm"), raw.get("pypi")
    names_ok = all(v is None or (isinstance(v, str) and v) for v in (npm, pypi)) and (npm or pypi)
    if not (isinstance(version, str) and version) or not names_ok:
        raise bad
    return Content(version=version, npm=npm, pypi=pypi)


def segment(pin: plugins.IndexPin) -> Segment:
    """The pin, verified, with its manifest's `content` — the only way one is read."""
    return Segment(pin=pin, content=_content(pin, plugins.locate_index(pin)))


def segments(root: Path) -> list[Segment]:
    """Every pin of `root`, verified, in pin-name order."""
    pins = plugins.indexes(root)
    return [segment(pins[name]) for name in sorted(pins)]


def is_pkg(text: str) -> bool:
    return isinstance(text, str) and text.startswith(fixed("pkg_location", "scheme"))


def location(seg: Segment, loc: str) -> str:
    """`pkg:<docs package>@<version>#<loc>` for a segment record's `loc`."""
    scheme, frag, at = (fixed("pkg_location", k) for k in ("scheme", "fragment", "version_sep"))
    return f"{scheme}{seg.content.name}{at}{seg.content.version}{frag}{loc}"


def hit_fields(record_id: str, loc: str, seg: Segment | None = None) -> dict:
    """The `location` and `package` every rendered hit carries (SR-MCP).

    A repository hit: its own id and no package. A hit whose record came from a
    pinned segment: its `pkg:` location, and the index package's pin name —
    provenance, not an address.
    """
    if seg is None:
        return {"location": record_id, "package": None}
    return {"location": location(seg, loc), "package": seg.pin.name}


def parse(text: str) -> tuple[str, str, str]:
    """`pkg:<name>@<version>#<path>` -> `(name, version, path)`, or refused."""
    scheme, frag, at = (fixed("pkg_location", k) for k in ("scheme", "fragment", "version_sep"))
    if not is_pkg(text):
        raise FuxError(_refusal("malformed", location=text))
    spec, sep, path = text[len(scheme):].partition(frag)
    name, at_sep, version = spec.rpartition(at)
    if not sep or not path or not at_sep or not name or not version:
        raise FuxError(_refusal("malformed", location=text))
    return name, version, path


def find_segment(root: Path, name: str, version: str, text: str) -> Segment:
    """The pinned segment whose docs package is `name` at `version`."""
    for seg in segments(root):
        if seg.content.version == version and name in (seg.content.npm, seg.content.pypi):
            return seg
    raise FuxError(_refusal("not_pinned", location=text, name=name, version=version))


def docs_root(seg: Segment) -> Path:
    """Steps 2-3: the installed docs package's root, version-checked."""
    content, pin = seg.content, seg.pin
    manifest = fixed("plugins.index", "manifest")
    if not content.pypi:
        raise FuxError(
            _refusal("no_registry", name=content.name, version=content.version, key="pypi", index=pin.name, manifest=manifest)
        )
    name = content.pypi
    install = plugins.install_line([(name, content.version)])
    common = {"name": name, "version": content.version, "index": pin.name, "index_version": pin.version, "install": install}
    have = plugins.installed_version(name)
    if have is None:
        raise FuxError(_refusal("missing", **common))
    if have != content.version:
        raise FuxError(_refusal("drifted", have=have, **common))
    import_name = plugins.IndexPin(name=pin.name, version=have, digest="", pypi=name).import_name
    try:
        spec = importlib.util.find_spec(import_name)
    except (ImportError, ValueError):
        spec = None
    locations = list(spec.submodule_search_locations or []) if spec is not None else []
    if len(locations) != 1 or not Path(locations[0]).is_dir():
        raise FuxError(_refusal("no_root", have=have, **common))
    return Path(locations[0])


def read(root: Path, text: str) -> Read:
    """Steps 1-5: the file a `pkg:` location names, read in place."""
    from ..store import content_sha
    from .source import contain

    name, version, fragment = parse(text)
    seg = find_segment(root, name, version, text)
    base = docs_root(seg)
    target = contain(base, fragment)
    if target is None:
        raise FuxError(_refusal("outside", location=text, name=name, version=version))
    if not target.is_file():
        raise FuxError(_refusal("not_file", location=text, name=name, version=version))
    raw = target.read_bytes()
    return Read(location=text, loc=fragment, path=target, content=raw, sha=content_sha(raw))


def refuse(given: str, verb: str) -> None:
    """The by-name refusal for a verb that reads only the repository's own
    documents (`fux correct`, `fux explain`/`graph`/`path`, `fux inspect`,
    `fux_related`): a `pkg:` id is never read as a `file:` one."""
    if is_pkg(given):
        raise FuxError(_refusal("refused", given=given, verb=verb))
