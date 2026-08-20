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

- **A `!` prefix subtracts** (`dirs` and `types` only). `!work/regression/*/evidence`
  removes matching paths from the walk; `!*.min.md` removes matching names from
  the type allowlist. **There is no un-exclude**: `!` subtracts and nothing adds
  back, so there is no precedence order to remember or to get wrong.
  Exclusions are **order-independent** — the loader sorts, so two people holding
  the same set in different orders must produce the same committed bytes, which
  is L3 applied to config.
- **An exclusion carries no attributes.** `archived=true` describes a directory
  whose documents are history; it means nothing about a path being removed, and
  accepting it silently would be the kind of no-op configuration this grammar's
  strictness exists to prevent.

The attribute sets are closed and per file: `fetch` + `meta` for `urls`,
`archived` for `dirs`, and **none at all** for `types`. Adding one is a change
to the owning record, which is what makes the unknown-key error safe to be
strict about.

## Glob matching: `*` does not cross a `/`

`fnmatch` is not used, because its `*` matches `/` — so
`work/regression/*/evidence` would also match
`work/regression/a/b/evidence`, which is not what anyone writing that line
means. `glob_match` compiles the pattern itself: `*` is `[^/]*`, `?` is
`[^/]`, and `**` is the explicit "any depth" form. Hand-rolled on purpose,
like every other codec here (L1).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path, PurePosixPath
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
    #: Whether a leading `!` is meaningful in this file. `urls` says no — a URL
    #: you do not want is a line you delete, and there is nothing to subtract
    #: from.
    allow_exclusions: bool = False

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
    #: True when the line began with `!`. `value` is the pattern **without**
    #: the prefix, so a consumer matches on it directly.
    exclude: bool = False

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
    if ".." in PurePosixPath(entry).parts:
        return "escapes the repo root"
    return None


def _type_reason(entry: str) -> str | None:
    """A type pattern matches a file *name* or a path, never a whole tree.

    A bare directory here is almost certainly someone reaching for `dirs`, and
    silently matching nothing is the failure this grammar's strictness exists
    to prevent.
    """
    if entry.startswith("/"):
        return "not a repo-relative pattern"
    if ".." in PurePosixPath(entry).parts:
        return "escapes the repo root"
    if entry.endswith("/"):
        return "a trailing slash means a directory, and types match files (use `dirs` for a tree)"
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
    allow_exclusions=True,
)

#: `.fux/sources/types` — which files in a source tree are documents at all.
#: No attributes: a pattern is a pattern, and every property one might want to
#: hang on it belongs to the *directory* it was found under.
TYPES = ListSpec(
    kind="types",
    attributes=(),
    validate=_type_reason,
    allow_exclusions=True,
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


def glob_match(pattern: str, path: str) -> bool:
    """Does `path` match `pattern`, with `*` **not** crossing a `/`?

    `fnmatch` is deliberately not used: its `*` matches `/`, so
    `work/regression/*/evidence` would also match `work/regression/a/b/evidence`
    — not what the line means. `**` is the explicit any-depth form.

    A pattern with no `/` matches the **basename**, which is what makes `*.md`
    mean "any markdown file anywhere" rather than "a markdown file at the repo
    root".
    """
    if "/" not in pattern:
        path = path.rsplit("/", 1)[-1]
    return _compiled(pattern).match(path) is not None


@lru_cache(maxsize=1024)
def _compiled(pattern: str) -> re.Pattern[str]:
    out: list[str] = []
    i = 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "*":
            if pattern[i : i + 2] == "**":
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
        elif ch == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(ch))
        i += 1
    return re.compile("".join(out) + r"\Z")


def parse(text: str, spec: ListSpec, *, origin: str) -> list[Entry]:
    """Parse a whole list. `origin` is what error messages name (a file path)."""
    seen: dict[tuple[bool, str], Entry] = {}
    for lineno, raw in enumerate(text.split("\n"), start=1):
        line = strip_comment(raw).strip()
        if not line:
            continue
        value, *tokens = line.split()

        exclude = False
        if value.startswith("!"):
            if not spec.allow_exclusions:
                raise FuxError(
                    f"{origin}:{lineno}: `!` means nothing in `{spec.kind}` — there is nothing to "
                    f"subtract from. Delete the line instead of negating it"
                )
            exclude = True
            value = value[1:]
            if not value:
                raise FuxError(f"{origin}:{lineno}: `!` with no pattern after it")
            if value.startswith("!"):
                raise FuxError(
                    f"{origin}:{lineno}: `!!` is not an un-exclude. `!` subtracts and nothing "
                    "adds back, which is why there is no precedence order to get wrong"
                )

        reason = spec.validate(value)
        if reason is not None:
            raise FuxError(f"{origin}:{lineno}: {reason}: {value!r}")

        if exclude and tokens:
            raise FuxError(
                f"{origin}:{lineno}: an exclusion carries no attributes (got {tokens[0]!r}). "
                f"An attribute describes a thing being indexed; this line removes one"
            )

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

        entry = Entry(
            value=value,
            attrs=attrs,
            lineno=lineno,
            declared=frozenset(declared),
            exclude=exclude,
        )
        # Keyed on (exclude, value): `docs` and `!docs` are contradictory rather
        # than duplicate, and collapsing them would silently pick a winner.
        key = (exclude, value)
        prior = seen.get(key)
        if prior is None:
            seen[key] = entry
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
            seen[key] = entry

    # Sorted by (exclude, value): includes first, then exclusions, each block
    # alphabetical. File order is presentation only — L3 applied to config.
    return sorted(seen.values(), key=lambda e: (e.exclude, e.value))


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
