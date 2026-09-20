"""Fetcher routing — a URL resolves to a fetcher the way a file resolves to a decoder.

**Three layers, and there is no fourth** ([SR-FETCHER](../../../records/0117_fetcher.md)
decision 16a): the URL line's `fetch=` **pin** wins over the committed
`[sources.url.routes]` **binding**, which wins over a fetcher module's `ROUTES`
**claim**. 🔴 **There is no default layer** — `[sources.url] fetcher` was deleted
on 2026-09-20, and a URL that resolves to nothing is an error naming the hosts
tried and the stems on disk, never a quiet fall back to plain HTTP.

🔴 **A claim is read with `ast`, never imported.** `fux doctor` is offline by
contract and `fux ingest --check` promises it opens no socket; importing a
consumer's fetcher to decide which fetcher to use would run their module-level
code on exactly those paths. The precedent is `doctor._fetcher_capabilities`,
which already reads a fetcher as text.

🔴 **Two patterns matching one host is a hard error naming both.** Between two
regexes there is no specificity order that is not arbitrary, and the failure a
guessed order produces is *a plausible index built by the wrong fetcher*, which
nothing downstream detects. ⚠ **This is stricter than the decoder plane on
purpose**: `decode.registry()` resolves a collision last-consumer-wins, and the
cost of being wrong there is one file read by the wrong reader.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from ..errors import FuxError

#: `host` · `*.host` · `host:port` — the three literal shapes. Lowercase
#: letters, digits, dots and hyphens, which is what a normalised host holds.
_LITERAL = re.compile(r"^(?:\*\.)?[a-z0-9]([a-z0-9.-]*[a-z0-9])?(?::\d{1,5})?$")

#: The prefix that makes a pattern a regex (SR-FETCHER decision 16c).
REGEX_PREFIX = "re:"

#: Specificity among the LITERAL shapes only, most specific first. A regex never
#: competes on specificity — it collides (see `resolve`).
_HOST_PORT, _HOST, _WILDCARD = 0, 1, 2


def normalise_host(url: str) -> str:
    """The host a pattern is matched against: lowercased, no userinfo, port kept.

    ⚠ **Port is kept when the URL states one**, because `host:port` is a
    pattern shape. A URL with no port matches a `host:port` pattern never —
    `https://a.example.com/x` is not `a.example.com:8443`, and inventing the
    scheme's default port here would make `:443` patterns match plain `https://`
    URLs that never said so.
    """
    rest = url.split("://", 1)[-1]
    authority = rest.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    if "@" in authority:
        authority = authority.rsplit("@", 1)[-1]
    return authority.lower()


def _compile(pattern: str, where: str) -> re.Pattern[str] | None:
    """A `re:` pattern, compiled and ANCHORED. `None` for a literal shape."""
    if not pattern.startswith(REGEX_PREFIX):
        return None
    body = pattern[len(REGEX_PREFIX):]
    if not body:
        raise FuxError(f"{where}: {pattern!r} is `re:` with no pattern after it")
    try:
        # Anchored at load, not at match: a caller who forgets `fullmatch` is a
        # silent widening, and `^…$` in the source is what a reader of the
        # committed file expects the pattern to mean.
        return re.compile(f"(?:{body})\\Z")
    except re.error as exc:
        raise FuxError(f"{where}: {pattern!r} is not a valid regular expression ({exc})") from exc


#: A validated table: `{pattern: (fetcher stem, compiled regex or None)}`.
Table = dict[str, "tuple[str, re.Pattern[str] | None]"]


def validate(patterns: dict[str, str], *, where: str) -> Table:
    """Every pattern checked and compiled, or a named error at the pattern.

    ⚠ **Returns the STEM alongside the compiled form.** An earlier shape
    returned only the compiled regexes and made the caller look the stem up
    again — which is how a resolver comes to return a pattern where a stem was
    meant, caught by a probe before it shipped.
    """
    out: Table = {}
    for pattern, stem in sorted(patterns.items()):
        if not isinstance(stem, str) or not stem.strip():
            raise FuxError(
                f"{where}: route {pattern!r} must name a fetcher module stem "
                f"(got {stem!r}) — `cdp`, never `cdp.py` and never .fux/fetchers/cdp.py"
            )
        # 🔴 **The SAME validator the line grammar uses**, so `fetch=cdp.py` on a
        # URL line and `"x" = "cdp.py"` in the routes table fail identically.
        # Two validators for one name shape is how they drift.
        from .sourcelist import _fetcher_reason

        fault = _fetcher_reason(stem)
        if fault is not None:
            raise FuxError(f"{where}: route {pattern!r} names {stem!r}, which {fault}")
        compiled = _compile(pattern, where)
        if compiled is None and not _LITERAL.match(pattern):
            raise FuxError(
                f"{where}: {pattern!r} is not a route pattern. Legal shapes are "
                f"`example.com`, `*.example.com` (not the apex), `example.com:8443`, "
                f"and `re:<regex>`"
            )
        out[pattern] = (stem, compiled)
    return out


def _specificity(pattern: str) -> int:
    if pattern.startswith("*."):
        return _WILDCARD
    return _HOST_PORT if ":" in pattern else _HOST


def _matches(pattern: str, compiled: re.Pattern[str] | None, host: str) -> bool:
    if compiled is not None:
        return compiled.match(host) is not None
    if pattern.startswith("*."):
        # ⚠ **A wildcard does NOT match the apex**, and this is the first thing
        # a consumer gets wrong. `*.example.com` matches `a.example.com` and not
        # `example.com`; the apex needs its own row.
        return host.endswith(pattern[1:]) and host != pattern[2:]
    return host == pattern


def resolve(host: str, table: Table, *, where: str) -> str | None:
    """The fetcher **stem** for `host`, or `None` when nothing matches.

    Among the **literal** shapes the order is `host:port` ▸ `host` ▸ `*.host`.
    🔴 **A regex never competes**: if a regex matches and anything else matches,
    or two regexes match, it is a collision and this raises naming both.
    """
    hits = [(p, _specificity(p)) for p, (_, c) in table.items() if _matches(p, c, host)]
    if not hits:
        return None
    regexes = [p for p, _ in hits if p.startswith(REGEX_PREFIX)]
    if regexes and len(hits) > 1:
        raise FuxError(
            f"{where}: {host!r} matches {len(hits)} routes — "
            f"{', '.join(repr(p) for p, _ in sorted(hits))}. There is no specificity order "
            f"between a regex and another pattern, so this is refused rather than sorted: "
            f"guessing one builds a plausible index with the wrong fetcher, and nothing "
            f"downstream detects it. Delete or narrow one"
        )
    best = min(hits, key=lambda h: h[1])[1]
    tied = sorted(p for p, s in hits if s == best)
    if len(tied) > 1:
        raise FuxError(
            f"{where}: {host!r} matches {len(tied)} equally specific routes — "
            f"{', '.join(repr(p) for p in tied)}. Refused rather than sorted"
        )
    return table[tied[0]][0]


def claims(fetchers_dir: Path) -> dict[str, tuple[str, str]]:
    """Every `ROUTES` claim on disk: `{pattern: (stem, file)}`.

    🔴 **Read with `ast`. Nothing here imports a fetcher, ever.** The module is
    parsed as text and only a literal `ROUTES = {...}` at module level is read.

    ⚠ **A malformed `ROUTES` is a hard error naming the file, not a skip.** A
    claim fux silently could not read is a routing rule its author believes is
    in force — the same defect an ignored config key is.
    """
    found: dict[str, tuple[str, str]] = {}
    if not fetchers_dir.is_dir():
        return found
    for path in sorted(fetchers_dir.glob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            raise FuxError(f"{path}: could not be read to check its ROUTES claim ({exc})") from exc
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            if not any(isinstance(tgt, ast.Name) and tgt.id == "ROUTES" for tgt in node.targets):
                continue
            if not isinstance(node.value, ast.Dict):
                raise FuxError(
                    f"{path}:{node.lineno}: ROUTES must be a dict literal of "
                    f"str -> str. It is read with `ast` and never imported, so a "
                    f"computed value cannot be evaluated"
                )
            for key, value in zip(node.value.keys, node.value.values):
                if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                    raise FuxError(f"{path}:{node.lineno}: every ROUTES key must be a string literal")
                if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                    raise FuxError(f"{path}:{node.lineno}: every ROUTES value must be a string literal")
                pattern, stem = key.value, value.value
                prior = found.get(pattern)
                if prior is not None and prior[0] != stem:
                    raise FuxError(
                        f"{fetchers_dir}: two fetchers claim the route {pattern!r} — "
                        f"{prior[1]} says {prior[0]!r} and {path.name} says {stem!r}. "
                        f"A claim collision is refused, not sorted"
                    )
                found[pattern] = (stem, path.name)
    return found
