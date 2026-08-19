"""`fux url` — the committed URL list, written by the tool rather than by hand.

ADR-URL-LIST decisions 12 and 13. A fux-written line carries **every**
attribute, explicitly, even where the value equals the default: a generated
file holds no implicit state, so changing a policy is a one-word diff rather
than the appearance or disappearance of a key. That is the property a record
already has for `meta` ("*a record read years later still says what rule it was
written under*"), now given to the source list that produced it.

**This command does not fetch. Nothing here touches the network.**
`--cdp` / `--plain` decide what is *recorded*, never what happens at ingest
time — which is why the same list can never produce different committed bytes
on different invocations. `fux ingest --refresh-urls` remains the only
networked path in the engine (law L4, [ADR-CLI](../../docs/adr/0002_cli-surface.md)).

**It edits one line, never the file.** A regenerating writer would be simpler
and would silently eat the grouping comments a human left behind — and under
[ADR-URL-LIST](../../docs/adr/0018_url-list.md) decision 3 those comments are
the reason the file is maintainable at all. So an add inserts one line at its
sorted position, an update rewrites that one line and keeps its trailing
comment, and a removal deletes it. Every other byte in the file is untouched,
and the diff is one line either way. The loader sorts regardless
(decision 4), so the insertion position is a courtesy to the reader, not a
correctness property.
"""

from __future__ import annotations

from pathlib import Path

from .config import CONFIG_NAME, DEFAULT_URLS_FILE, find_root, load
from .errors import FuxError
from .ingest import sourcelist

SPEC = sourcelist.URLS


def _urls_file(root: Path) -> str:
    """Where the list lives — `[sources.url] urls_file`, or the default.

    A repo with no `[sources.url]` block still has a URL list path: the command
    that puts the first URL in it should not also demand you configure the
    source first.
    """
    config = load(root)
    return config.url.urls_file if config.url is not None else DEFAULT_URLS_FILE


def _write(path: Path, lines: list[str]) -> None:
    """Write the lines back, always ending in exactly one newline.

    A committed text file without a trailing newline makes the next diff touch
    a line nobody edited, which is the opposite of what a one-line writer is
    for.
    """
    text = "\n".join(lines).rstrip("\n")
    path.write_text(text + "\n" if text else "", encoding="utf-8")


def _split(raw: str) -> tuple[str, str]:
    """One raw line -> (its entry text, its trailing comment including the `#`)."""
    body = sourcelist.strip_comment(raw)
    return body, raw[len(body) :]


def _entry_value(raw: str) -> str | None:
    """The entry a raw line declares, or None for a blank or comment line."""
    body, _ = _split(raw)
    stripped = body.strip()
    return stripped.split()[0] if stripped else None


def add(path: Path, url: str, overrides: dict[str, str]) -> tuple[str, str, str]:
    """Add or update one line. Returns `(action, new_line, previous_line)`."""
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    lines = text.split("\n")

    existing = sourcelist.parse(text, SPEC, origin=str(path))
    prior = next((e for e in existing if e.value == url), None)
    attrs = SPEC.defaults() | (prior.attrs if prior is not None else {}) | overrides
    body = sourcelist.render_line(url, attrs, SPEC)

    for i, raw in enumerate(lines):
        if _entry_value(raw) != url:
            continue
        _, comment = _split(raw)
        previous = raw
        lines[i] = body + (f"  {comment.strip()}" if comment.strip() else "")
        _write(path, lines)
        return ("unchanged" if lines[i] == previous else "updated"), lines[i], previous

    # New entry: insert at its sorted position among the lines that are entries.
    at = len(lines)
    for i, raw in enumerate(lines):
        value = _entry_value(raw)
        if value is not None and value > url:
            at = i
            break
    else:
        # No later entry: land after the last one rather than after the file's
        # trailing blank lines, so a generated list stays a single block.
        last = max((i for i, raw in enumerate(lines) if _entry_value(raw) is not None), default=None)
        at = last + 1 if last is not None else _after_preamble(lines)

    lines.insert(at, body)
    _write(path, lines)
    return "added", body, ""


def _after_preamble(lines: list[str]) -> int:
    """The first index past the file's leading comment block, blanks trimmed."""
    i = 0
    while i < len(lines) and (not lines[i].strip() or lines[i].lstrip().startswith("#")):
        i += 1
    return i


def remove(path: Path, url: str) -> str:
    """Delete the line declaring `url`. Returns it, or raises if it is not there."""
    if not path.is_file():
        raise FuxError(f"{path} does not exist — nothing to remove")
    lines = path.read_text(encoding="utf-8").split("\n")
    for i, raw in enumerate(lines):
        if _entry_value(raw) == url:
            removed = lines.pop(i)
            _write(path, lines)
            return removed
    raise FuxError(f"{url} is not in {path}")


def _overrides(args) -> dict[str, str]:
    """Flags -> the attributes to record. Two flags for one attribute is an error.

    `--cdp --http` has no defensible meaning, and picking one silently is how a
    scripted call records the opposite of what it meant.
    """
    pairs = (("fetch", ("cdp", "http")), ("meta", ("plain", "hashed")))
    overrides: dict[str, str] = {}
    for attribute, flags in pairs:
        given = [flag for flag in flags if getattr(args, flag, False)]
        if len(given) > 1:
            raise FuxError(f"--{given[0]} and --{given[1]} both set `{attribute}` — pick one")
        if given:
            overrides[attribute] = given[0]
    return overrides


def cmd_url(args) -> int:
    root = find_root()
    if root is None:
        raise FuxError(f"no {CONFIG_NAME} or .git found — run from inside a configured repo")
    path = root / _urls_file(root)

    if not getattr(args, "url", None):
        return _list(path)

    url = args.url
    reason = SPEC.validate(url)
    if reason is not None:
        raise FuxError(f"{reason}: {url!r}")

    if getattr(args, "remove", False):
        print(f"removed  {remove(path, url).strip()}")
        return 0

    overrides = _overrides(args)

    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
    action, line, previous = add(path, url, overrides)
    print(f"{action:9s} {line.strip()}")
    if action == "updated":
        print(f"      was {previous.strip()}")
    print(f"  in {path.relative_to(root).as_posix()} — commit it; `fux ingest --refresh-urls` fetches")
    return 0


def _list(path: Path) -> int:
    """Print the list as the loader sees it: sorted, deduped, fully resolved."""
    if not path.is_file():
        print(f"{path} does not exist — `fux setup` writes one, `fux url <URL>` fills it")
        return 0
    entries = sourcelist.parse(path.read_text(encoding="utf-8"), SPEC, origin=str(path))
    if not entries:
        print("no URLs listed")
        return 0
    for entry in entries:
        mark = " " if entry.is_complete() else "*"
        print(f"{mark} {sourcelist.render_line(entry.value, entry.attrs, SPEC)}")
    incomplete = [e for e in entries if not e.is_complete()]
    if incomplete:
        print(
            f"\n* {len(incomplete)} line(s) do not state every attribute, so fux did not write "
            "them. They load fine (the reader is lenient); `fux url <URL>` rewrites one in full."
        )
    return 0
