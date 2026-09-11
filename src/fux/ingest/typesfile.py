"""`.fux/formats.toml` — which files are documents, and which decoder reads each.

**Two keys, and the set is closed** (ADR-TYPES decision 12):

```toml
include = [          # globs that are already text -- no decoder in the path
  "*.md",
  "docs/**/*.txt",
]

[decoders]           # extension = the decoder module that reads it
csv = "csv"
geojson = "json"     # extending: nothing else claims .geojson
```

**A bound extension IS a document.** `[decoders] csv` admits `*.csv`; writing
`*.csv` in `include` as well is a loud *stated twice* error, because two lines
that must agree are one edit away from disagreeing. Ruff's `include` /
`extension` pair is the precedent.

## What the shape makes impossible, rather than checks

- **A path-scoped binding.** The key IS an extension, so
  `docs/api/*.json decoder=json` — which would have silently bound every
  `.json` in the corpus — cannot be written. Decision 11's rule is the shape.
- **Two bindings for one extension.** TOML itself refuses a repeated key.

## What it still checks

- **The key set** — `tomllib` accepts any key, so fux refuses one it does not
  know. `!` subtraction is deliberately not a key: exclusions live in
  `.fux/.fuxignore` (ADR-FUXIGNORE decision 5).
- **Every glob** by the same rule the line grammar used
  (`sourcelist._type_reason`), and **every module name** by its shape
  (`sourcelist._decoder_reason`). Whether the module exists, and whether a
  binding redirects a claimed extension, is `decode._bind`'s question — only
  the registry can answer it.

## The reader is lenient, the writer is strict

Any valid TOML with the right keys loads. The editors below change **one
line** of the canonical layout — one glob per line inside `include = [ ... ]`,
one `key = "value"` per line under `[decoders]` — and **refuse** a layout they
did not write rather than reformat it, because a reformat would eat the
comments a human left inside the array (ADR-URL-LIST decision 13, kept).

## Positions in errors are best effort, and say so

`tomllib` reports where a *syntax* error is, but a parsed value carries no
position. So a semantic error always names the **key** (`decoders.geojson`),
and adds `:lineno` only when a scan of the text finds exactly one line for it.
The line grammar guaranteed `file:lineno`; this one does not, and that is a
cost ADR-TYPES decision 12 records.

## The old file is refused, never read

`.fux/sources/types` is a loud error wherever the types list is consulted.
Ignoring it would put the built-in default in its place — *a plausible index
with different postings*, the failure ADR-TYPES decision 11 names. `fux setup`
converts it (`convert_legacy`).
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from ..config import DEFAULT_TYPES_FILE, LEGACY_TYPES_FILE
from ..errors import FuxError
from . import sourcelist

#: The closed key set. Adding one is a change to ADR-TYPES, not a config addition.
KEYS: tuple[str, ...] = ("include", "decoders")

#: An extension key: lowercase, no leading dot, dot-separated parts for a
#: compound suffix (`"tar.gz"`, which TOML requires quoted).
_EXT_RE = re.compile(r"[a-z0-9][a-z0-9_+\-]*(?:\.[a-z0-9][a-z0-9_+\-]*)*")

_BARE_KEY_RE = re.compile(r"[A-Za-z0-9_\-]+")
_STRING = r'"(?:[^"\\]|\\.)*"|\'[^\'\n]*\''
_INCLUDE_OPEN = re.compile(r"^include\s*=\s*\[\s*(?:#.*)?$")
_ARRAY_CLOSE = re.compile(r"^\s*\]\s*(?:#.*)?$")
_ITEM = re.compile(rf"^\s*({_STRING})\s*,?\s*(?:#.*)?$")
_TABLE = re.compile(r"^\s*\[")
_DECODERS_HEADER = re.compile(r"^\s*\[\s*decoders\s*\]\s*(?:#.*)?$")
_KV = re.compile(rf"^\s*({_STRING}|[A-Za-z0-9_\-]+)\s*=\s*({_STRING})\s*(?:#.*)?$")


@dataclass(frozen=True)
class TypesList:
    """A parsed types file. `include` is sorted and deduped; `decoders` is sorted."""

    include: tuple[str, ...]
    #: extension (no dot, lowercase) -> decoder module stem
    decoders: dict[str, str]
    origin: str
    text: str = field(default="", repr=False, compare=False)

    @property
    def allow(self) -> tuple[str, ...]:
        """Every glob that admits a file: the includes, plus `*.<ext>` per binding."""
        return tuple(sorted({*self.include, *(f"*.{ext}" for ext in self.decoders)}))

    def where_include(self, glob: str) -> str:
        return _where_include(self.text, self.origin, glob)

    def where_decoder(self, ext: str) -> str:
        return _where_decoder(self.text, self.origin, ext)


def pattern_extension(glob: str) -> str | None:
    """The extension a bare `*.ext` glob names — `"csv"` — or `None` for any other shape.

    **The one definition** of "this glob is exactly one extension". The *stated
    twice* check uses it, `sources.cmd_add` uses it to decide whether a new
    pattern becomes a binding, and `decode` no longer needs one: its keys are
    extensions already.
    """
    if not glob.startswith("*.") or "/" in glob:
        return None
    ext = glob[2:].lower()
    if not ext or any(ch in ext for ch in "*?[]"):
        return None
    return ext


# -- reading ---------------------------------------------------------------


def legacy_message(root: Path) -> str:
    both = (root / DEFAULT_TYPES_FILE).is_file()
    if both:
        return (
            f"{LEGACY_TYPES_FILE} still exists beside {DEFAULT_TYPES_FILE}. The types list moved "
            f"to {DEFAULT_TYPES_FILE} (ADR-TYPES decision 12) and only that file is the list - "
            f"delete {LEGACY_TYPES_FILE}. fux refuses rather than guess which one you meant"
        )
    return (
        f"{LEGACY_TYPES_FILE} is the old types list; it moved to {DEFAULT_TYPES_FILE} "
        f"(ADR-TYPES decision 12). Run `fux setup` to write {DEFAULT_TYPES_FILE} from it - its "
        f"`!` lines become .fux/.fuxignore lines - then delete {LEGACY_TYPES_FILE}. fux refuses "
        f"rather than ignore it: ignoring it would silently put the built-in default in its place"
    )


def check_legacy(root: Path) -> None:
    """Raise if the old line-grammar types file is still in the repo."""
    if (root / LEGACY_TYPES_FILE).is_file():
        raise FuxError(legacy_message(root))


def read(root: Path, rel_path: str = DEFAULT_TYPES_FILE) -> TypesList | None:
    """The committed types list, or `None` when there is no file (the default applies).

    Refuses a repo still holding `.fux/sources/types` before anything else, so
    no caller can reach a state where the old file is silently outranked.
    """
    check_legacy(root)
    path = root / rel_path
    if not path.is_file():
        return None
    return parse(path.read_text(encoding="utf-8"), origin=rel_path)


def parse(text: str, *, origin: str) -> TypesList:
    """Parse and validate a whole types file. `origin` is what an error names."""
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise FuxError(f"{origin}: not valid TOML - {exc}") from None

    unknown = sorted(set(data) - set(KEYS))
    if unknown:
        hint = ""
        if any(k in ("exclude", "exclusions", "deny") for k in unknown):
            hint = (
                " Exclusions are not part of this file: write them in .fux/.fuxignore, which is "
                "read first and outranks it (ADR-FUXIGNORE decision 5)"
            )
        raise FuxError(
            f"{origin}: unknown key {unknown[0]!r} - the key set is closed and is "
            f"`include` and `decoders` (ADR-TYPES decision 12).{hint}"
        )

    include = data.get("include", [])
    if not isinstance(include, list):
        raise FuxError(f"{origin}: `include` must be an array of glob strings")
    for glob in include:
        if not isinstance(glob, str):
            raise FuxError(f"{origin}: `include` holds {glob!r}, which is not a string")
        _check_glob(glob, text, origin)

    decoders = data.get("decoders", {})
    if not isinstance(decoders, dict):
        raise FuxError(f"{origin}: `decoders` must be a table of `extension = \"module\"`")
    for ext, name in decoders.items():
        _check_binding(ext, name, text, origin)

    for glob in include:
        ext = pattern_extension(glob)
        # Exact case: `*.CSV` beside `csv = "csv"` admits upper-case files the
        # binding does not (`glob_match` is case-sensitive), so it is not a repeat.
        if ext is not None and ext in decoders and glob == f"*.{ext}":
            raise FuxError(
                f"{_where_include(text, origin, glob)}: `{glob}` is in `include` and "
                f"`{ext}` is bound in [decoders]. A bound extension is already a document - "
                f"delete the `include` entry. Two lines that must agree are one edit away "
                f"from disagreeing"
            )

    return TypesList(
        include=tuple(sorted(set(include))),
        decoders=dict(sorted(decoders.items())),
        origin=origin,
        text=text,
    )


def _check_glob(glob: str, text: str, origin: str) -> None:
    where = _where_include(text, origin, glob)
    if not glob or glob != glob.strip() or "\n" in glob:
        raise FuxError(f"{where}: {glob!r} is not a glob - empty, padded or multi-line")
    if glob.startswith("!"):
        raise FuxError(
            f"{where}: `{glob}` - `!` does not subtract here. Exclusions live in "
            f".fux/.fuxignore, which is read first and outranks this file (ADR-FUXIGNORE "
            f"decision 5); write `{glob[1:]}` there"
        )
    reason = sourcelist._type_reason(glob)
    if reason is not None:
        raise FuxError(f"{where}: {reason}: {glob!r}")


def _check_binding(ext: str, name, text: str, origin: str) -> None:
    where = _where_decoder(text, origin, ext)
    if isinstance(name, dict):
        inner = next(iter(name), "")
        raise FuxError(
            f"{origin} (decoders.{ext}): is a table, not a module name. An extension with a "
            f"dot must be quoted - `\"{ext}.{inner}\" = \"<module>\"` - or TOML reads it as a "
            f"nested key"
        )
    if not isinstance(name, str):
        raise FuxError(f"{where}: the decoder must be a module name string, got {name!r}")
    if ext.startswith("."):
        raise FuxError(f"{where}: write the extension without its dot - `{ext[1:]}`, not `{ext}`")
    if ext != ext.lower():
        raise FuxError(
            f"{where}: `{ext}` must be lowercase - dispatch lowercases every suffix, so "
            f"`{ext}` and `{ext.lower()}` would be one extension written two ways"
        )
    if not _EXT_RE.fullmatch(ext):
        raise FuxError(f"{where}: `{ext}` is not an extension - no glob characters, no `/`")
    if name == "":
        raise FuxError(
            f"{where}: an empty decoder binds nothing. A format no decoder reads belongs in "
            f"`include`"
        )
    fault = sourcelist._decoder_reason(name)
    if fault is not None:
        raise FuxError(f"{where}: decoder {name!r} {fault}")


def _line_of(text: str, pattern: re.Pattern[str]) -> int | None:
    hits = [n for n, line in enumerate(text.split("\n"), start=1) if pattern.search(line)]
    return hits[0] if len(hits) == 1 else None


def _where_include(text: str, origin: str, glob: str) -> str:
    esc = re.escape(glob)
    lineno = _line_of(text, re.compile(rf"(?:\"{esc}\"|'{esc}')")) if text else None
    loc = f"{origin}:{lineno}" if lineno else origin
    return f"{loc} (include {glob!r})"


def _where_decoder(text: str, origin: str, ext: str) -> str:
    esc = re.escape(ext)
    lineno = (
        _line_of(text, re.compile(rf"^\s*(?:\"{esc}\"|'{esc}'|{esc})\s*=")) if text else None
    )
    loc = f"{origin}:{lineno}" if lineno else origin
    return f"{loc} (decoders.{ext})"


# -- writing ---------------------------------------------------------------


def quote(value: str) -> str:
    """A TOML basic string. Hand-rolled like every codec in fux (L1): the stdlib
    reads TOML and does not write it."""
    out = ['"']
    for ch in value:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\n":
            out.append("\\n")
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:
            out.append(f"\\u{ord(ch):04x}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def key(ext: str) -> str:
    """An extension as a TOML key — bare when it can be, quoted when it has a dot."""
    return ext if _BARE_KEY_RE.fullmatch(ext) else quote(ext)


def render(
    include,
    decoders: dict[str, str],
    *,
    header: str = "",
    include_note: str = "",
    decoders_note: str = "",
    footer: str = "",
    grouped: bool = True,
) -> str:
    """A whole file in the canonical layout. Sorted (L3); decoders grouped by module
    when `grouped`, so `htm`/`html`/`xhtml` sit together as the map they are."""
    lines: list[str] = []
    if header:
        lines += header.rstrip("\n").split("\n") + [""]
    if include_note:
        lines += include_note.rstrip("\n").split("\n")
    lines.append("include = [")
    lines += [f"  {quote(glob)}," for glob in sorted(set(include))]
    lines.append("]")
    lines.append("")
    if decoders_note:
        lines += decoders_note.rstrip("\n").split("\n")
    lines.append("[decoders]")
    if grouped:
        first = True
        for name in sorted(set(decoders.values())):
            if not first:
                lines.append("")
            first = False
            lines += [
                f"{key(ext)} = {quote(name)}"
                for ext in sorted(e for e, n in decoders.items() if n == name)
            ]
    else:
        lines += [f"{key(ext)} = {quote(name)}" for ext, name in sorted(decoders.items())]
    if footer:
        lines += [""] + footer.rstrip("\n").split("\n")
    return "\n".join(lines) + "\n"


def _refuse(origin: str, what: str) -> FuxError:
    return FuxError(
        f"{origin}: {what}, so fux will not edit it - rewriting it would lose the comments in "
        f"it. Put one entry per line (`include = [` on its own line, one glob per line; one "
        f"`extension = \"module\"` per line under `[decoders]`), or make this edit by hand"
    )


def _unquote(token: str) -> str:
    return tomllib.loads(f"v = {token}")["v"]


def _key_name(token: str) -> str:
    return token if _BARE_KEY_RE.fullmatch(token) else _unquote(token)


def _include_block(lines: list[str], origin: str, present: bool) -> tuple[int, int] | None:
    """`(open, close)` line indices of the canonical `include` array, or `None` when absent."""
    for i, line in enumerate(lines):
        if _TABLE.match(line) and not _INCLUDE_OPEN.match(line):
            break  # past the top level; `include` must come before any table
        if _INCLUDE_OPEN.match(line):
            for j in range(i + 1, len(lines)):
                if _ARRAY_CLOSE.match(lines[j]):
                    for k in range(i + 1, j):
                        body = lines[k].strip()
                        if body and not body.startswith("#") and not _ITEM.match(lines[k]):
                            raise _refuse(origin, "`include` is not one glob per line")
                    return i, j
            raise _refuse(origin, "`include = [` is never closed on a line of its own")
    if present:
        raise _refuse(origin, "`include` is not written as a multi-line array")
    return None


def _decoders_block(lines: list[str], origin: str, present: bool) -> tuple[int, int] | None:
    """`(header, end)` of the `[decoders]` section — `end` exclusive — or `None`."""
    for i, line in enumerate(lines):
        if _DECODERS_HEADER.match(line):
            end = len(lines)
            for j in range(i + 1, len(lines)):
                if _TABLE.match(lines[j]):
                    end = j
                    break
            for k in range(i + 1, end):
                body = lines[k].strip()
                if body and not body.startswith("#") and not _KV.match(lines[k]):
                    raise _refuse(origin, "`[decoders]` is not one `extension = \"module\"` per line")
            return i, end
    if present:
        raise _refuse(origin, "`decoders` is not written as a `[decoders]` table")
    return None


def _items(lines: list[str], start: int, stop: int) -> list[tuple[int, str]]:
    out = []
    for i in range(start, stop):
        m = _ITEM.match(lines[i])
        if m and not lines[i].strip().startswith("#"):
            out.append((i, _unquote(m.group(1))))
    return out


def _pairs(lines: list[str], start: int, stop: int) -> list[tuple[int, str, str]]:
    out = []
    for i in range(start, stop):
        m = _KV.match(lines[i])
        if m and not lines[i].strip().startswith("#"):
            out.append((i, _key_name(m.group(1)), _unquote(m.group(2))))
    return out


def _finish(lines: list[str], origin: str, expect) -> str:
    """Join, then prove the edit did exactly what it meant to by parsing the result."""
    text = "\n".join(lines).rstrip("\n") + "\n"
    parsed = parse(text, origin=origin)
    expect(parsed)
    return text


def add_include(text: str, glob: str, *, origin: str) -> tuple[str, str]:
    """Add one glob to `include`. Returns `(new_text, action)` — `added` or `unchanged`."""
    current = parse(text, origin=origin)
    if glob in current.include:
        return text, "unchanged"
    lines = text.split("\n")
    block = _include_block(lines, origin, present="include" in tomllib.loads(text))
    if block is None:
        at = next((i for i, line in enumerate(lines) if _TABLE.match(line)), len(lines))
        lines[at:at] = ["include = [", f"  {quote(glob)},", "]", ""]
    else:
        open_, close = block
        items = _items(lines, open_ + 1, close)
        later = next((i for i, value in items if value > glob), None)
        at = later if later is not None else (items[-1][0] + 1 if items else close)
        lines.insert(at, f"  {quote(glob)},")

    def expect(parsed: TypesList) -> None:
        assert glob in parsed.include and parsed.decoders == current.decoders

    return _finish(lines, origin, expect), "added"


def set_decoder(text: str, ext: str, name: str, *, origin: str) -> tuple[str, str, str]:
    """Bind one extension. Returns `(new_text, action, previous_module)`.

    A bare `*.<ext>` already in `include` **moves** into `[decoders]` rather
    than tripping the *stated twice* error on fux's own edit.
    """
    current = parse(text, origin=origin)
    previous = current.decoders.get(ext, "")
    if previous == name:
        return text, "unchanged", previous
    lines = text.split("\n")
    data = tomllib.loads(text)

    # Drop a bare `*.<ext>` from include first: it is about to be stated by the binding.
    moved = [g for g in current.include if g == f"*.{ext}"]
    if moved:
        open_, close = _include_block(lines, origin, present=True)
        for i, value in reversed(_items(lines, open_ + 1, close)):
            if value in moved:
                del lines[i]

    block = _decoders_block(lines, origin, present="decoders" in data)
    entry = f"{key(ext)} = {quote(name)}"
    if block is None:
        while lines and not lines[-1].strip():
            lines.pop()
        lines += ["", "[decoders]", entry]
    else:
        header, end = block
        pairs = _pairs(lines, header + 1, end)
        same = [i for i, k, _ in pairs if k == ext]
        if same:
            m = _KV.match(lines[same[0]])
            comment = lines[same[0]][m.end(2):].strip()
            lines[same[0]] = entry + (f"  {comment}" if comment else "")
        else:
            group = [i for i, _, v in pairs if v == name]
            if group:
                siblings = [(i, k) for i, k, v in pairs if v == name]
                later = next((i for i, k in siblings if k > ext), None)
                at = later if later is not None else group[-1] + 1
                lines.insert(at, entry)
            elif pairs:
                lines[pairs[-1][0] + 1 : pairs[-1][0] + 1] = ["", entry]
            else:
                lines.insert(header + 1, entry)

    def expect(parsed: TypesList) -> None:
        assert parsed.decoders.get(ext) == name
        assert set(parsed.include) == set(current.include) - set(moved)

    return _finish(lines, origin, expect), ("updated" if previous else "added"), previous


def remove(text: str, glob: str, *, origin: str) -> tuple[str, str]:
    """Delete the entry that admits `glob`. Returns `(new_text, what_was_removed)`.

    A glob in `include` loses its line; a bare `*.<ext>` bound in `[decoders]`
    loses the binding's line. Anything else is not in the file, and says so.
    """
    current = parse(text, origin=origin)
    lines = text.split("\n")
    data = tomllib.loads(text)
    if glob in current.include:
        open_, close = _include_block(lines, origin, present=True)
        for i, value in _items(lines, open_ + 1, close):
            if value == glob:
                del lines[i]
                break

        def expect(parsed: TypesList) -> None:
            assert glob not in parsed.include

        return _finish(lines, origin, expect), glob
    ext = pattern_extension(glob)
    if ext is not None and ext in current.decoders:
        header, end = _decoders_block(lines, origin, present="decoders" in data)
        for i, k, _ in _pairs(lines, header + 1, end):
            if k == ext:
                del lines[i]
                break

        def expect(parsed: TypesList) -> None:
            assert ext not in parsed.decoders

        return _finish(lines, origin, expect), f"{glob} decoder={current.decoders[ext]}"
    raise FuxError(
        f"{glob} is not in {origin}. The types list has no exclusions: to keep matching files "
        f"out of the index, write the pattern in .fux/.fuxignore"
    )


# -- the old file ----------------------------------------------------------


def convert_legacy(text: str, *, origin: str) -> tuple[list[str], dict[str, str], list[str]]:
    """`.fux/sources/types` -> `(include, decoders, exclusions)`.

    Parsed with the line grammar it was written in, so a legacy file fux could
    not have ingested fails here with the same error rather than converting into
    something else. `!` lines come back as exclusions for `.fux/.fuxignore`.
    """
    entries = sourcelist.parse(text, sourcelist.TYPES, origin=origin)
    include: list[str] = []
    decoders: dict[str, str] = {}
    exclusions: list[str] = []
    for entry in entries:
        if entry.exclude:
            exclusions.append(entry.value)
            continue
        name = entry.attrs.get("decoder", "")
        ext = pattern_extension(entry.value)
        if name:
            if ext is None:
                raise FuxError(
                    f"{origin}:{entry.lineno}: decoder={name} on pattern {entry.value!r} - a "
                    f"binding is per extension, so this line could never have run. Fix it "
                    f"before converting"
                )
            if entry.value != f"*.{ext}":
                # A binding admits `*.<lowercase ext>`. Converting `*.CSV` into
                # `csv` would stop admitting `a.CSV` and start admitting `a.csv` -
                # the silent allowlist change the conversion exists to avoid.
                raise FuxError(
                    f"{origin}:{entry.lineno}: `{entry.value} decoder={name}` - the new file keys "
                    f"a binding on the lowercase extension, which admits `*.{ext}`, not "
                    f"`{entry.value}`. Lowercase the pattern (or write the conversion by hand) "
                    f"and run `fux setup` again"
                )
            decoders[ext] = name
        else:
            include.append(entry.value)
    include = [g for g in include if not (pattern_extension(g) in decoders and g == f"*.{pattern_extension(g)}")]
    return sorted(set(include)), dict(sorted(decoders.items())), sorted(set(exclusions))
