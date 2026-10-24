"""`.fux/sources.yaml` — the one include manifest, read and edited.

**Owned by [SR-SOURCES](../../../records/0116_url-list.md)** (W-294, Arpit
2026-10-24). It replaced two line-grammar lists, `.fux/sources/dirs` and
`.fux/sources/urls`, and is read through the fux YAML subset
(`yamlsubset.py`). Exclusion is NOT spelled here — `.fux/.fuxignore` is its one
home, so `!` means one thing in `.fux/`.

```yaml
paths:
  include:
    - docs
  archived:          # indexed as history
    - archive

urls:
  - url: https://wiki.corp/display/ENG/runbook
    fetch: cdp
    decoder: html
```

The schema, in one place:

- **Two top-level keys, `paths` and `urls`, and nothing else.** Either may be
  absent; a file of only comments lists nothing.
- **`paths:` holds flag lists** — `include`, `archived`, `enrich`. A path in
  ANY list is indexed, and each list it is in sets that flag (`include` sets
  none), so a plain path is a bare list item with no `{}`. The flags are
  **declared, never derived from a path** (SR-ARCHIVED-CONTENT).
- **`urls:` is a list of entries**, keys `url` plus the seven attributes of
  `sourcelist.URLS`; `url`, `fetch` and `decoder` are required.
- **The kind is the section**, never inferred from a `scheme://`: a URL under
  `paths:` is refused, naming where it goes.
- 🔴 **Typing is the schema's.** Every path and URL is text; `keep`, `enrich`
  and `archived` accept only `true`/`false`; `ttl` is a duration; `update` is
  `auto`/`never`. `no`, `on`, `null`, `~`, `1.10`, `010` stay text where text
  is expected.
- **Duplicates are an error**, not a silent dedupe — the file is hand-edited,
  and a dedupe hides a merge mistake. **The loader still SORTS**, so file order
  is for humans and cannot change a committed byte (L4).

The values come back as `sourcelist.Entry` rows — the same shape every caller
already spoke — so a path's flags are `attrs["archived"]` / `attrs["enrich"]`
exactly as a `dirs` line's were, and a URL entry's attributes are resolved
through the built-in defaults exactly as a `urls` line's were.

## The writer edits text

`fux add` inserts one line into the right `paths` list, or one entry block under
`urls`; `fux remove` deletes that line or block. **Every other byte — every
comment, the hand order — is kept, and the file is never re-rendered.** The
result is re-parsed before it is returned, so the writer cannot hand back a file
the reader refuses.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..constants import fixed, table
from ..errors import FuxError
from . import sourcelist, yamlsubset

__all__ = [
    "FILE",
    "Sources",
    "archived_paths",
    "check_legacy",
    "convert_legacy",
    "enrich_paths",
    "parse",
    "read",
    "read_urls",
    "remove",
    "set_path",
    "set_url",
    "source_paths",
]

FILE = fixed("files", "sources")
LEGACY_DIRS = fixed("files", "dirs_legacy")
LEGACY_URLS = fixed("files", "urls_legacy")

PATHS_KEY = fixed("sources_file", "paths")
URLS_KEY = fixed("sources_file", "urls")
INCLUDE = fixed("sources_file", "include")
PATH_LISTS: tuple[str, ...] = tuple(fixed("sources_file", "path_lists"))
URL_KEY = fixed("sources_file", "url_key")

_TEXTS = table("sources_messages")

#: The flag a list sets on its paths. `include` sets none.
_FLAGS: tuple[str, ...] = tuple(name for name in PATH_LISTS if name != INCLUDE)


def _fail(name: str, origin: str, line: int, **fill: object) -> FuxError:
    return FuxError(f"{origin}:{line}: " + _TEXTS[name].format(**fill))


@dataclass(frozen=True)
class Sources:
    """The parsed file: path entries and URL entries, each sorted by value."""

    paths: tuple[sourcelist.Entry, ...] = ()
    urls: tuple[sourcelist.Entry, ...] = ()


# -- reading -----------------------------------------------------------------


def _known(names) -> str:
    return ", ".join(f"`{n}`" for n in names)


def _text(node, what: str, origin: str, line: int) -> yamlsubset.Scalar:
    if not isinstance(node, yamlsubset.Scalar):
        raise _fail("not_text", origin, getattr(node, "line", line), what=what)
    return node


def _seq(pair: yamlsubset.Pair, origin: str) -> yamlsubset.Seq:
    if isinstance(pair.value, yamlsubset.Null):
        raise _fail("empty", origin, pair.line, key=pair.key)
    if not isinstance(pair.value, yamlsubset.Seq):
        raise _fail("not_list", origin, pair.line, key=pair.key)
    return pair.value


def _path_entries(pair: yamlsubset.Pair, origin: str) -> list[sourcelist.Entry]:
    if isinstance(pair.value, yamlsubset.Null):
        raise _fail("empty", origin, pair.line, key=pair.key)
    if not isinstance(pair.value, yamlsubset.Map):
        raise _fail("not_map", origin, pair.line, key=pair.key)
    lists: dict[str, set[str]] = {}
    first: dict[str, int] = {}
    for name, sub in pair.value.pairs.items():
        if name not in PATH_LISTS:
            raise _fail("unknown", origin, sub.line, key=name, where=f" under `{PATHS_KEY}`",
                        known=_known(PATH_LISTS))
        seen: dict[str, int] = {}
        for item in _seq(sub, origin).items:
            scalar = _text(item, "path", origin, sub.line)
            value = scalar.text
            if value in seen:
                raise _fail("path_twice", origin, scalar.line, value=value, list=name, first=seen[value])
            seen[value] = scalar.line
            _check_path(value, origin, scalar.line)
            lists.setdefault(value, set()).add(name)
            first[value] = min(first.get(value, scalar.line), scalar.line)
    names = frozenset(sourcelist.PATHS.names)
    return [
        sourcelist.Entry(
            value=value,
            attrs={flag: "true" if flag in held else "false" for flag in _FLAGS},
            lineno=first[value],
            declared=names,
        )
        for value, held in lists.items()
    ]


def _check_path(value: str, origin: str, line: int) -> None:
    if value.startswith("!"):
        raise _fail("bang", origin, line, value=value, rest=value[1:].lstrip("/"))
    if sourcelist.has_scheme(value):
        raise _fail("url_in_paths", origin, line, value=value)
    reason = sourcelist.PATHS.validate(value)
    if reason is not None:
        raise _fail("reason", origin, line, reason=reason, value=value)


def _url_entries(pair: yamlsubset.Pair, origin: str) -> list[sourcelist.Entry]:
    spec = sourcelist.URLS
    known = (URL_KEY, *spec.names)
    seen: dict[str, int] = {}
    out: list[sourcelist.Entry] = []
    for item in _seq(pair, origin).items:
        if not isinstance(item, yamlsubset.Map):
            raise _fail("not_map", origin, item.line, key=f"{URLS_KEY}` entry `")
        for name, sub in item.pairs.items():
            if name not in known:
                raise _fail("unknown", origin, sub.line, key=name, where=f" in a `{URLS_KEY}` entry",
                            known=_known(known))
        if URL_KEY not in item.pairs:
            raise _fail("no_url", origin, item.line)
        url_pair = item.pairs[URL_KEY]
        url = _text(url_pair.value, "URL", origin, url_pair.line)
        reason = spec.validate(url.text)
        if reason is not None:
            raise _fail("reason", origin, url.line, reason=reason, value=url.text)
        if url.text in seen:
            raise _fail("url_twice", origin, url.line, value=url.text, first=seen[url.text])
        seen[url.text] = url.line
        attrs = spec.defaults()
        declared: set[str] = set()
        for name in spec.names:
            if name not in item.pairs:
                continue
            sub = item.pairs[name]
            scalar = _text(sub.value, f"`{name}`", origin, sub.line)
            fault = spec.attribute(name).reject(scalar.text)
            if fault is not None:
                raise _fail("attribute", origin, scalar.line, key=name, value=scalar.text, fault=fault)
            attrs[name] = scalar.text
            declared.add(name)
        for attribute in spec.attributes:
            if attribute.required and attribute.name not in declared:
                raise _fail("required", origin, url.line, value=url.text, key=attribute.name,
                            hint=attribute.required_hint)
        out.append(sourcelist.Entry(value=url.text, attrs=attrs, lineno=url.line,
                                    declared=frozenset(declared)))
    return out


def parse(text: str, *, origin: str) -> Sources:
    """Parse a whole `.fux/sources.yaml`. `origin` is what an error names."""
    root = yamlsubset.parse(text, origin=origin)
    if root is None:
        return Sources()
    if not isinstance(root, yamlsubset.Map):
        raise _fail("top", origin, root.line)
    for name, pair in root.pairs.items():
        if name not in (PATHS_KEY, URLS_KEY):
            raise _fail("unknown", origin, pair.line, key=name, where="",
                        known=_known((PATHS_KEY, URLS_KEY)))
    paths = _path_entries(root.pairs[PATHS_KEY], origin) if PATHS_KEY in root.pairs else []
    urls = _url_entries(root.pairs[URLS_KEY], origin) if URLS_KEY in root.pairs else []
    # Sorted: file order is presentation only (L4 applied to config).
    return Sources(
        paths=tuple(sorted(paths, key=lambda e: e.value)),
        urls=tuple(sorted(urls, key=lambda e: e.value)),
    )


def check_legacy(root: Path) -> None:
    """Refuse while a pre-W-294 list still sits in the tree.

    The `formats.toml` precedent (SR-TYPES decision 12): **no reader for the old
    paths beyond `fux setup`'s conversion**, and no silent choice between two
    files that both claim to say what is indexed. On a repo whose `dirs` list
    holds an L11 guard (`!work/golden`), a reader that ignored the old file
    would index what it excluded.
    """
    for legacy in (LEGACY_DIRS, LEGACY_URLS):
        if (root / legacy).is_file():
            raise FuxError(_TEXTS["legacy"].format(legacy=legacy))


def read(root: Path, rel_path: str, *, missing_hint: "str | None" = None) -> Sources:
    """Read and parse the manifest, or fail loudly naming the path."""
    check_legacy(root)
    path = root / rel_path
    if not path.is_file():
        raise FuxError(
            _TEXTS["missing"].format(file=rel_path, path=path, hint=missing_hint or _TEXTS["missing_hint"])
        )
    return parse(path.read_text(encoding="utf-8"), origin=str(path))


def read_or_empty(root: Path, rel_path: str) -> Sources:
    """The manifest, or nothing listed when the file is absent — the verbs' read,
    where `fux add` exists to write the first entry."""
    check_legacy(root)
    path = root / rel_path
    if not path.is_file():
        return Sources()
    return parse(path.read_text(encoding="utf-8"), origin=str(path))


def source_paths(root: Path, rel_path: str) -> list[str]:
    """Every listed path, sorted — the roots the walk visits."""
    return [entry.value for entry in read(root, rel_path).paths]


def archived_paths(root: Path, rel_path: str) -> list[str]:
    """Paths under `archived:` (SR-ARCHIVED-CONTENT decision 6's input)."""
    return [e.value for e in read(root, rel_path).paths if e.attrs.get("archived") == "true"]


def enrich_paths(root: Path, rel_path: str) -> list[str]:
    """Paths under `enrich:` (W-76 Phase 8) — declared, never derived."""
    return [e.value for e in read(root, rel_path).paths if e.attrs.get("enrich") == "true"]


def read_urls(root: Path, rel_path: str, *, missing_hint: "str | None" = None) -> list[sourcelist.Entry]:
    """The `urls:` entries, sorted by URL, attributes resolved to the built-ins."""
    return list(read(root, rel_path, missing_hint=missing_hint).urls)


# -- writing: one line in, one line or block out -------------------------------

#: A plain value may not start with one of these; the writer quotes instead.
_UNSAFE_START = set("{}[]&*!|>@`,%#'\"?:-")


def render_scalar(value: str) -> str:
    """`value` as the writer spells it: plain when the reader reads it back
    as the same text, single-quoted otherwise. Never a guess either way."""
    plain = (
        value
        and value == value.strip()
        and value[0] not in _UNSAFE_START
        and ": " not in value
        and " #" not in value
        and not value.endswith(":")
        and "\t" not in value
        and "\n" not in value
    )
    if plain:
        return value
    return "'" + value.replace("'", "''") + "'"


def _lead(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _root_map(text: str, origin: str) -> "yamlsubset.Map | None":
    root = yamlsubset.parse(text, origin=origin)
    return root if isinstance(root, yamlsubset.Map) else None


def _content_end(lines: list[str]) -> int:
    """The index just past the last non-blank line."""
    end = len(lines)
    while end and not lines[end - 1].strip():
        end -= 1
    return end


def _join(lines: list[str]) -> str:
    text = "\n".join(lines).rstrip("\n")
    return text + "\n" if text else ""


def _paths_lists(text: str, origin: str) -> dict[str, set[str]]:
    """`{path: {list names}}` as the file stands."""
    root = _root_map(text, origin)
    out: dict[str, set[str]] = {}
    if root is None or PATHS_KEY not in root.pairs:
        return out
    for name, sub in root.pairs[PATHS_KEY].value.pairs.items():
        for item in sub.value.items:
            out.setdefault(item.text, set()).add(name)
    return out


def _insert_path(text: str, list_name: str, value: str, origin: str) -> str:
    lines = text.split("\n")
    root = _root_map(text, origin)
    rendered = render_scalar(value)
    paths = root.pairs.get(PATHS_KEY) if root is not None else None
    if paths is None:
        block = [f"{PATHS_KEY}:", f"  {list_name}:", f"    - {rendered}"]
        urls = root.pairs.get(URLS_KEY) if root is not None else None
        if urls is not None:
            at = urls.line - 1
            lines[at:at] = [*block, ""]
        else:
            end = _content_end(lines)
            lines[end:end] = ([""] if end else []) + block
        return _join(lines)
    lists = paths.value.pairs
    if list_name in lists:
        seq = lists[list_name].value
        indent = _lead(lines[seq.items[0].line - 1])
        at = seq.last  # after the last item
        for item in seq.items:
            if item.text > value:
                at = item.line - 1
                break
        lines[at:at] = [f"{' ' * indent}- {rendered}"]
        return _join(lines)
    first = next(iter(lists.values()))
    key_indent = _lead(lines[first.line - 1])
    item_indent = _lead(lines[first.value.items[0].line - 1])
    order = PATH_LISTS.index(list_name)
    at = paths.value.last
    for name, sub in lists.items():
        if name in PATH_LISTS and PATH_LISTS.index(name) > order:
            at = sub.line - 1
            break
    lines[at:at] = [f"{' ' * key_indent}{list_name}:", f"{' ' * item_indent}- {rendered}"]
    return _join(lines)


def _delete_path(text: str, list_name: str, value: str, origin: str) -> tuple[str, str]:
    lines = text.split("\n")
    root = _root_map(text, origin)
    paths = root.pairs[PATHS_KEY]
    sub = paths.value.pairs[list_name]
    item = next(i for i in sub.value.items if i.text == value)
    removed = lines[item.line - 1].strip()
    if len(sub.value.items) > 1:
        del lines[item.line - 1]
    elif len(paths.value.pairs) > 1:
        del lines[sub.line - 1 : sub.value.last]
    else:
        del lines[paths.line - 1 : paths.value.last]
        _drop_blank_run(lines, paths.line - 1)
    return _join(lines), removed


def _drop_blank_run(lines: list[str], at: int) -> None:
    """Collapse a double blank line a deleted block left at `at`."""
    while 0 < at < len(lines) and not lines[at].strip() and not lines[at - 1].strip():
        del lines[at]


def set_path(text: str, value: str, flags: dict[str, str], *, origin: str) -> tuple[str, str]:
    """Put `value` in the lists its flags name. Returns `(new_text, action)`.

    `flags` is `{"archived": "true"|"false", "enrich": ...}`; none true means
    `include`. A path already in exactly those lists is `unchanged`.
    """
    parse(text, origin=origin)
    wanted = {flag for flag in _FLAGS if flags.get(flag) == "true"} or {INCLUDE}
    held = _paths_lists(text, origin).get(value, set())
    if held == wanted:
        return text, "unchanged"
    for name in sorted(held - wanted):
        text, _ = _delete_path(text, name, value, origin)
    for name in [n for n in PATH_LISTS if n in wanted - held]:
        text = _insert_path(text, name, value, origin)
    parse(text, origin=origin)
    return text, "updated" if held else "added"


def _url_item(root: "yamlsubset.Map | None", url: str):
    if root is None or URLS_KEY not in root.pairs:
        return None, None
    seq = root.pairs[URLS_KEY].value
    for item in seq.items:
        if item.pairs[URL_KEY].value.text == url:
            return seq, item
    return seq, None


def set_url(text: str, url: str, attrs: dict[str, str], *, origin: str) -> tuple[str, str]:
    """Add or update one `urls:` entry. Returns `(new_text, action)`.

    A new entry states every attribute (SR-SOURCES decision 12 — a generated
    entry holds no implicit state). An existing one has each changed value
    replaced **on its own line**, keeping its comment, and each missing one
    appended to its block; nothing else in the file moves.
    """
    parse(text, origin=origin)
    spec = sourcelist.URLS
    lines = text.split("\n")
    root = _root_map(text, origin)
    seq, item = _url_item(root, url)
    if item is not None:
        changed = False
        first = lines[item.line - 1]
        dash = _lead(first)
        key_indent = dash + 1 + _lead(first[dash + 1 :])
        tail: list[str] = []
        for name in spec.names:
            value = attrs[name]
            pair = item.pairs.get(name)
            if pair is None:
                tail.append(f"{' ' * key_indent}{name}: {render_scalar(value)}")
                changed = True
                continue
            if pair.value.text != value:
                raw = lines[pair.value.line - 1]
                lines[pair.value.line - 1] = raw[: pair.value.col] + render_scalar(value) + raw[pair.value.end :]
                changed = True
        if not changed:
            return text, "unchanged"
        lines[item.last : item.last] = tail
        new = _join(lines)
        parse(new, origin=origin)
        return new, "updated"
    indent = _lead(lines[seq.items[0].line - 1]) if seq is not None else 2
    block = [f"{' ' * indent}- {URL_KEY}: {render_scalar(url)}"] + [
        f"{' ' * (indent + 2)}{name}: {render_scalar(attrs[name])}" for name in spec.names
    ]
    if seq is None:
        end = _content_end(lines)
        lines[end:end] = ([""] if end else []) + [f"{URLS_KEY}:", *block]
    else:
        at = seq.last
        for other in seq.items:
            if other.pairs[URL_KEY].value.text > url:
                at = other.line - 1
                break
        lines[at:at] = block
    new = _join(lines)
    parse(new, origin=origin)
    return new, "added"


def remove(text: str, value: str, *, kind: str, origin: str) -> tuple[str, str]:
    """Delete `value`'s line (a path, from every list) or block (a URL).

    Returns `(new_text, what_was_removed)`; raises when it is not listed.
    """
    parse(text, origin=origin)
    if kind == sourcelist.URLS.kind:
        root = _root_map(text, origin)
        seq, item = _url_item(root, value)
        if item is None:
            raise FuxError(f"{value} is not in {origin}")
        lines = text.split("\n")
        if len(seq.items) > 1:
            del lines[item.line - 1 : item.last]
        else:
            urls = root.pairs[URLS_KEY]
            del lines[urls.line - 1 : seq.last]
            _drop_blank_run(lines, urls.line - 1)
        new = _join(lines)
        parse(new, origin=origin)
        return new, f"{URL_KEY}: {value}"
    held = _paths_lists(text, origin).get(value)
    if not held:
        raise FuxError(f"{value} is not in {origin}")
    for name in sorted(held):
        text, _ = _delete_path(text, name, value, origin)
    parse(text, origin=origin)
    return text, value


def describe_path(value: str, flags: dict[str, str]) -> str:
    """How a verb prints a path entry: the value and the lists that hold it."""
    held = [flag for flag in _FLAGS if flags.get(flag) == "true"] or [INCLUDE]
    return f"{value}  ({PATHS_KEY}: {', '.join(held)})"


# -- the one-time conversion `fux setup` runs ---------------------------------


@dataclass(frozen=True)
class Converted:
    """What `convert_legacy` produced: the manifest, and the `.fuxignore` lines."""

    text: str
    #: Anchored `.fuxignore` lines, each with the comment its `!` line carried,
    #: preceded by any comment lines that sat directly above it.
    ignore_lines: tuple[str, ...]
    #: The patterns moved, without comments — what `fux setup` announces.
    moved: tuple[str, ...]


def _comment(raw: str) -> str:
    """The trailing `# ...` of a legacy line, including the `#`, or `""`."""
    body = sourcelist.strip_comment(raw)
    return raw[len(body) :].strip()


def _legacy_blocks(text: str, *, drop_headers: tuple[str, ...]):
    """`(header, [(comments_above, raw_line)], trailing_comments)` for a legacy list."""
    lines = text.split("\n")
    header: list[str] = []
    i = 0
    while i < len(lines) and lines[i].lstrip().startswith("#"):
        header.append(lines[i])
        i += 1
    if "\n".join(header) + "\n" in drop_headers or "\n".join(header) in drop_headers:
        header = []
    rows: list[tuple[list[str], str]] = []
    pending: list[str] = []
    for raw in lines[i:]:
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            pending.append(stripped)
            continue
        rows.append((pending, raw))
        pending = []
    return header, rows, pending


def convert_legacy(
    dirs_text: "str | None",
    urls_text: "str | None",
    *,
    dirs_origin: str,
    urls_origin: str,
    header: str,
    drop_headers: tuple[str, ...] = (),
    ignore_pattern=None,
) -> Converted:
    """`.fux/sources/dirs` + `.fux/sources/urls` → one `.fux/sources.yaml` text.

    Plain path lines go to `include`, `archived=true` to `archived`,
    `enrich=true` to `enrich`; every URL line becomes an entry stating what the
    line stated. **Comments travel with the line they sat on or directly above.**
    A list's own header is dropped only when it is one `fux setup` wrote
    (`drop_headers`) — a header a human wrote is carried, verbatim.

    Each `!` line becomes an **anchored** `.fuxignore` line (`ignore_pattern`,
    `fuxignore.exclusion_pattern`), which the caller writes **before** it deletes
    the old list — on this repository three of them are an L11 guard.

    🔴 **The result is proved equal to the input before it is returned**: the
    same paths with the same flags, the same URLs with the same resolved and
    declared attributes. A conversion that changed what is indexed would be
    the silent failure this whole file exists to make loud.
    """
    dirs = sourcelist.parse(dirs_text or "", sourcelist.DIRS, origin=dirs_origin)
    urls = sourcelist.parse(urls_text or "", sourcelist.URLS, origin=urls_origin)
    by_path = {e.value: e for e in dirs if not e.exclude}
    by_url = {e.value: e for e in urls}

    lists: dict[str, list[str]] = {name: [] for name in PATH_LISTS}
    ignore: list[str] = []
    moved: list[str] = []
    carried: list[str] = []
    placed: set[tuple[str, str]] = set()

    dh, drows, dtail = _legacy_blocks(dirs_text or "", drop_headers=drop_headers)
    if dh:
        carried += [f"# carried from {dirs_origin}:", *dh]
    for above, raw in drows:
        token = sourcelist.strip_comment(raw).split()[0]
        note = _comment(raw)
        if token.startswith("!"):
            pattern = ignore_pattern(token[1:]) if ignore_pattern else "/" + token[1:]
            if pattern in moved:
                continue
            ignore += above
            ignore.append(f"{pattern}   {note}" if note else pattern)
            moved.append(pattern)
            continue
        entry = by_path[token]
        names = [flag for flag in _FLAGS if entry.attrs.get(flag) == "true"] or [INCLUDE]
        for n, name in enumerate(names):
            if (name, token) in placed:
                continue
            placed.add((name, token))
            item = f"    - {render_scalar(token)}" + (f"   {note}" if note and n == 0 else "")
            lists[name] += [f"    {c}" for c in (above if n == 0 else [])] + [item]

    url_rows: list[str] = []
    uh, urows, utail = _legacy_blocks(urls_text or "", drop_headers=drop_headers)
    if uh:
        carried += [f"# carried from {urls_origin}:", *uh]
    done: set[str] = set()
    for above, raw in urows:
        token = sourcelist.strip_comment(raw).split()[0]
        if token in done:
            continue
        done.add(token)
        entry = by_url[token]
        note = _comment(raw)
        url_rows += [f"  {c}" for c in above]
        url_rows.append(f"  - {URL_KEY}: {render_scalar(token)}" + (f"   {note}" if note else ""))
        url_rows += [
            f"    {name}: {render_scalar(entry.attrs[name])}"
            for name in sourcelist.URLS.names
            if name in entry.declared
        ]

    out: list[str] = [header.rstrip("\n")]
    if carried:
        out += ["", *carried]
    if any(lists.values()):
        out += ["", f"{PATHS_KEY}:"]
        for name in PATH_LISTS:
            if lists[name]:
                out += [f"  {name}:", *lists[name]]
    if url_rows:
        out += ["", f"{URLS_KEY}:", *url_rows]
    if dtail or utail:
        out += ["", *dtail, *utail]
    text = _join(out)

    got = parse(text, origin=FILE)
    want_paths = sorted((e.value, e.attrs["archived"], e.attrs["enrich"]) for e in by_path.values())
    have_paths = sorted((e.value, e.attrs["archived"], e.attrs["enrich"]) for e in got.paths)
    want_urls = sorted((e.value, tuple(sorted(e.attrs.items())), tuple(sorted(e.declared))) for e in by_url.values())
    have_urls = sorted((e.value, tuple(sorted(e.attrs.items())), tuple(sorted(e.declared))) for e in got.urls)
    if want_paths != have_paths or want_urls != have_urls:
        raise FuxError(
            f"converting {dirs_origin} and {urls_origin} into {FILE} would change what is "
            "indexed, so nothing was written. Convert them by hand; this is a fux bug worth reporting"
        )
    return Converted(text=text, ignore_lines=tuple(ignore), moved=tuple(moved))
