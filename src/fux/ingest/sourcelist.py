"""One parser for both committed source lists — `.fux/sources/urls` and
`.fux/sources/dirs`.

The grammar is fixed by ADR-URL-LIST decisions 2-13 and reused verbatim by
ADR-DIR-LIST decision 2. **There is one reader for both files on purpose**:
two parsers for one grammar is how `#`-handling, sorting and the unknown-key
error end up disagreeing, and the disagreement surfaces as a document
silently missing rather than as an error.

The grammar, in one place:

- **One entry per line**, blank lines ignored. This is what makes the file
  merge line by line at 5 000 entries.
- **`#` begins a comment only at the start of a line or after whitespace.**
  Not anywhere. A URL fragment (`https://x/page#section`) is part of the
  entry, and stripping from the first `#` anywhere collapsed two URLs into
  one and dropped a document with no error.
- **`<entry> key=value [key=value ...]`**, whitespace-separated. Values carry
  no whitespace and no quoting (ADR-URL-LIST decision 8).
- **An unknown key, an unknown value, or a repeated key is a loud error
  naming `file:lineno`.** A reader that does not know a key refuses rather
  than guesses: a typo'd `mata=plain` that is silently ignored ships a
  private document to a public index.
- **The reader is lenient, the writer is strict** (decision 13). A missing
  attribute takes its default when read, so a hand-made or merged list still
  loads; `render` always emits every attribute, so a generated file holds no
  implicit state.
- **The loader dedupes and sorts.** File order is presentation only, which is
  L3 applied to config: two people holding the same set in different orders
  must produce the same committed bytes. A duplicate entry is a merge
  artefact and not an error — but a duplicate whose *resolved* attributes
  disagree is, naming both line numbers, because exact entries cannot
  legitimately disagree and letting a merge artefact pick a privacy policy is
  the worst available outcome (decision 10).

The attribute sets are closed and per file: `fetch` + `meta` for `urls`,
`archived` for `dirs`. Adding one is a change to the owning record, which is
what makes the unknown-key error safe to be strict about.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..errors import FuxError


@dataclass(frozen=True)
class Attribute:
    """One closed attribute: its name, its legal values, what absence means."""

    name: str
    values: tuple[str, ...]
    default: str


@dataclass(frozen=True)
class ListSpec:
    """A source list's file-specific half of the grammar.

    `validate` receives the entry text and returns the *reason* it is
    unacceptable, or `None`. It is the only place the two files differ beyond
    their attribute sets — `urls` rejects a non-`http(s)` scheme, `dirs`
    accepts any repo-relative path (existence is `fux doctor`'s question, not
    the parser's).
    """

    kind: str
    attributes: tuple[Attribute, ...]
    validate: Callable[[str], str | None] = lambda _entry: None

    def defaults(self) -> dict[str, str]:
        return {a.name: a.default for a in self.attributes}

    def attribute(self, name: str) -> Attribute | None:
        for a in self.attributes:
            if a.name == name:
                return a
        return None

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(a.name for a in self.attributes)


@dataclass(frozen=True)
class Entry:
    """One parsed line.

    `attrs` is **resolved** — every attribute in the spec is present, absent
    ones filled with their default — so a caller never re-implements decision
    13's leniency. `declared` is the subset the line actually stated, which is
    what `fux doctor` needs to report a line that fux did not write.
    """

    value: str
    attrs: dict[str, str]
    lineno: int
    declared: frozenset[str]

    def is_complete(self) -> bool:
        """True when the line stated every attribute — i.e. fux wrote it."""
        return len(self.declared) == len(self.attrs)


def _url_reason(entry: str) -> str | None:
    if not entry.startswith(("http://", "https://")):
        return "not an http(s) URL"
    return None


def _dir_reason(entry: str) -> str | None:
    if entry.startswith("/"):
        return "not a repo-relative path"
    if ".." in Path(entry).parts:
        return "escapes the repo root"
    return None


URLS = ListSpec(
    kind="urls",
    attributes=(
        Attribute("fetch", ("http", "cdp"), "http"),
        Attribute("meta", ("plain", "hashed"), "hashed"),
    ),
    validate=_url_reason,
)

DIRS = ListSpec(
    kind="dirs",
    attributes=(Attribute("archived", ("true", "false"), "false"),),
    validate=_dir_reason,
)


def strip_comment(raw: str) -> str:
    """Drop a trailing comment. `#` counts only at line start or after whitespace.

    This is forced, not chosen: under a whitespace-delimited grammar,
    `https://x/a#frag meta=plain` cannot parse at all if `#` means a comment
    everywhere. It is also the fix for the silent fragment truncation.
    """
    if raw.lstrip().startswith("#"):
        return ""
    for i, ch in enumerate(raw):
        if ch == "#" and i > 0 and raw[i - 1] in " \t":
            return raw[:i]
    return raw


def parse(text: str, spec: ListSpec, *, origin: str) -> list[Entry]:
    """Parse a whole list. `origin` is what error messages name (a file path)."""
    seen: dict[str, Entry] = {}
    for lineno, raw in enumerate(text.split("\n"), start=1):
        line = strip_comment(raw).strip()
        if not line:
            continue
        value, *tokens = line.split()

        reason = spec.validate(value)
        if reason is not None:
            raise FuxError(f"{origin}:{lineno}: {reason}: {value!r}")

        attrs = spec.defaults()
        declared: set[str] = set()
        for token in tokens:
            if "=" not in token:
                raise FuxError(
                    f"{origin}:{lineno}: {token!r} is not `key=value` — attributes are "
                    f"`key=value` only, no bare flags (the set here is {', '.join(spec.names)})"
                )
            key, _, raw_value = token.partition("=")
            attribute = spec.attribute(key)
            if attribute is None:
                raise FuxError(
                    f"{origin}:{lineno}: unknown attribute {key!r} — the set for `{spec.kind}` "
                    f"is closed and is {', '.join(spec.names)}. Adding one is a change to the "
                    "record, not a config addition"
                )
            if key in declared:
                raise FuxError(f"{origin}:{lineno}: attribute {key!r} is given twice")
            if raw_value not in attribute.values:
                raise FuxError(
                    f"{origin}:{lineno}: {key}={raw_value!r} is not one of "
                    f"{', '.join(attribute.values)}"
                )
            attrs[key] = raw_value
            declared.add(key)

        entry = Entry(value=value, attrs=attrs, lineno=lineno, declared=frozenset(declared))
        prior = seen.get(value)
        if prior is None:
            seen[value] = entry
            continue
        if prior.attrs != entry.attrs:
            raise FuxError(
                f"{origin}:{prior.lineno} and {origin}:{lineno}: {value!r} appears twice with "
                f"conflicting attributes ({_render_attrs(prior.attrs)} vs "
                f"{_render_attrs(entry.attrs)}) — a duplicate is a merge artefact, and a merge "
                "artefact may not decide a policy. Delete one line"
            )
        # A duplicate that agrees is a merge artefact and not an error; keep the
        # more explicit of the two so `is_complete` does not degrade.
        if len(entry.declared) > len(prior.declared):
            seen[value] = entry

    return sorted(seen.values(), key=lambda e: e.value)


def read(root: Path, rel_path: str, spec: ListSpec, *, missing_hint: str) -> list[Entry]:
    """Read and parse one list file, or fail loudly naming the path."""
    path = root / rel_path
    if not path.is_file():
        raise FuxError(f"{rel_path} not found (looked in {path}) — {missing_hint}")
    return parse(path.read_text(encoding="utf-8"), spec, origin=str(path))


def render_line(value: str, attrs: dict[str, str], spec: ListSpec) -> str:
    """One generated line, **every attribute stated** (ADR-URL-LIST decision 12).

    A generated file holds no implicit state: the line says what it means, so
    changing a policy is a one-word diff rather than the appearance or
    disappearance of a key.
    """
    resolved = spec.defaults() | {k: v for k, v in attrs.items() if k in spec.defaults()}
    return " ".join([value, *(f"{name}={resolved[name]}" for name in spec.names)])


def _render_attrs(attrs: dict[str, str]) -> str:
    return " ".join(f"{k}={v}" for k, v in sorted(attrs.items()))
