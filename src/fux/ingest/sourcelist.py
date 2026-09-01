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
    """One attribute: its name, its legal values, what absence means.

    ⚠ **`values` is empty for a TYPED attribute, and `validate` carries the
    rule instead.** Every attribute was a closed enum until `ttl` (ADR-URL-
    FRESHNESS): a duration is an unbounded value, and there is no tuple of
    legal ones to write. The enum is still the default and still the right
    shape for `fetch`, `meta`, `archived` and `keep` -- a typed attribute is
    the exception, and its validator must produce the same *kind* of error the
    enum does, naming what was wrong rather than what was expected.
    """

    name: str
    values: tuple[str, ...]
    default: str
    #: `None` -> the value is legal. A string -> why it is not. Consulted only
    #: when `values` is empty.
    validate: Callable[[str], str | None] | None = None

    def reject(self, raw: str) -> str | None:
        """Why `raw` is not a legal value here, or `None`."""
        if self.values:
            if raw in self.values:
                return None
            return f"is not one of {', '.join(self.values)}"
        if self.validate is not None:
            return self.validate(raw)
        return None


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


#: `ttl=` accepts `0` or `<int><s|m|h|d>`. Seconds would have been unambiguous
#: and unreadable at a glance; named tiers (`daily`, `hourly`) would have been
#: readable and ambiguous -- is `daily` a rolling 24h or midnight? A suffixed
#: integer is both, and it is the same shape `acquired_max_bytes` reads.
_DURATION_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}

_TTL_HELP = (
    "must be 0 (always re-fetch) or <number><unit> where unit is "
    "s, m, h or d - for example 30s, 15m, 1h, 7d"
)


def parse_duration(raw: str) -> int | None:
    """`"1h"` -> 3600. `None` when the text is not a duration.

    ⚠ **Stored verbatim, compared resolved.** `60m` and `1h` are the same
    policy and are NOT the same line, because config order must never change a
    committed byte -- so the file keeps what a human wrote and only the
    resolved seconds are ever compared. `fux add` writes the canonical form.
    """
    text = raw.strip()
    if text == "0":
        return 0
    if len(text) < 2:
        return None
    unit = _DURATION_UNITS.get(text[-1])
    if unit is None or not text[:-1].isdigit():
        return None
    return int(text[:-1]) * unit


def _ttl_reason(raw: str) -> str | None:
    return None if parse_duration(raw) is not None else _TTL_HELP


#: A decoder name is a MODULE STEM -- `csvdoc`, never `csvdoc.py` and never
#: `.fux/decoders/csvdoc.py`. It is the same key ADR-DECODE decision 5 resolves
#: an override on, so a binding and an override cannot disagree about what they
#: are naming.
_DECODER_NAME_RE = re.compile(r"[a-z0-9][a-z0-9_]*")

_DECODER_HELP = (
    "must be a decoder module name - lowercase letters, digits and underscores, "
    "not starting with `_` (a leading underscore marks a shared helper the "
    "registry skips), with no `.py` suffix and no directory part"
)


def _decoder_reason(raw: str) -> str | None:
    """Why `raw` is not a decoder name, or `None`. **Shape only.**

    Whether a module by that name exists is deliberately NOT checked here: the
    parser cannot reach the decoder registry, and reaching for it would make
    reading a config file depend on importing every decoder. Existence and the
    extension agreement are checked where the binding is applied
    (`decode.registry`), which is also the only place that can say what the
    module actually claims. Same split `dirs` already makes -- it accepts any
    repo-relative path and leaves existence to `fux doctor`.
    """
    # `""` is the resolved default and means *no declared binding*: the
    # extension resolves through the decoder's own EXTENSIONS tuple, which is
    # what every line did before this attribute existed. It has to stay legal
    # because `render_line` states every attribute, so a generated line reads
    # `*.md decoder=` and must parse back to the same entry.
    if raw == "":
        return None
    return None if _DECODER_NAME_RE.fullmatch(raw) else _DECODER_HELP


URLS = ListSpec(
    kind="urls",
    attributes=(
        Attribute("fetch", ("http", "cdp"), "http"),
        Attribute("meta", ("plain", "hashed"), "hashed"),
        # ADR-ACQUIRED. Retain the bytes this URL returned.
        #
        # ⚠ **Default TRUE, and it was `false` for one day.** The argument for
        # off-by-default was a stranger's 9,000-URL corpus quietly filling a
        # disk. `[sources.url] acquired_max_bytes` answers that directly -- the
        # store is bounded and evicts -- and once the blast radius is bounded,
        # defaulting off means almost nobody gets the thing the plane exists
        # for: a citation that can still be checked when the source cannot be
        # reached. `keep=false` on the line, or `--no-keep`, opts out.
        Attribute("keep", ("true", "false"), "true"),
        # ADR-URL-FRESHNESS. How long a citation may go unchecked at ask time.
        # THE FIRST TYPED ATTRIBUTE: a duration has no tuple of legal values.
        #
        # The default is NOT 0. A repo-wide always-fetch turns every `fux ask`
        # into a network operation against a warm p95 of 27.2 ms, which is a
        # cost nobody asked for; a day is generous enough to be invisible and
        # short enough to catch a document that moved.
        Attribute("ttl", (), "24h", validate=_ttl_reason),
        # ADR-PII/W-99: the same attribute the `dirs` list carries, and it
        # means the same thing. A `url:` document is enrichable because
        # `.fux/acquired/` holds its bytes locally -- before the acquired
        # plane there was nothing for `fux enrich --plan` to chunk, which is
        # why this attribute could not exist on this list until now.
        Attribute("enrich", ("true", "false"), "false"),
    ),
    validate=_url_reason,
)

DIRS = ListSpec(
    kind="dirs",
    attributes=(
        Attribute("archived", ("true", "false"), "false"),
        # W-76 Phase 8. **Declared, never derived** -- the same rule
        # `archived` follows, for the same reason. Enrichment costs money and
        # changes ranking, so which directories get it is a decision a human
        # writes in a diffable line, not something fux infers from a path.
        #
        # Partial coverage ACROSS the corpus is the intended state; partial
        # coverage INSIDE a declared scope is a defect, and that is exactly
        # the split `fux enrich --check` reports on.
        Attribute("enrich", ("true", "false"), "false"),
    ),
    validate=_dir_reason,
    allow_exclusions=True,
)

#: `.fux/sources/types` — which files in a source tree are documents at all,
#: and which decoder reads each one.
#:
#: ⚠ **This list had NO attributes until 2026-09-01**, on the rule that "a
#: pattern is a pattern, and every property one might want to hang on it
#: belongs to the *directory* it was found under". `decoder` is the exception
#: and the reason is that it is not a property of the directory: it is a
#: property of the **extension**, which is exactly what a line here names.
#: Ruled by Arpit; carried by [ADR-TYPES](../../../docs/adr/0031_types-list.md)
#: decisions 11 and 11a.
TYPES = ListSpec(
    kind="types",
    attributes=(Attribute("decoder", (), "", validate=_decoder_reason),),
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
            fault = attribute.reject(raw_value)
            if fault is not None:
                raise FuxError(f"{origin}:{lineno}: {key}={raw_value!r} {fault}")
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

    ⚠ **One exception, added with `types.decoder` (2026-09-01): an attribute
    whose default is EMPTY is omitted at that default.** Decision 12's rule is
    that a generated line states its policy so a change is a one-word diff —
    and a bare `decoder=` states no policy and cannot be diffed into one. It
    would put four dead characters on every prose line in the types file. No
    other attribute is affected: `fetch`, `meta`, `keep`, `ttl`, `archived` and
    `enrich` all have real defaults, so all are still written at their default.
    """
    defaults = spec.defaults()
    resolved = defaults | {k: v for k, v in attrs.items() if k in defaults}
    stated = [name for name in spec.names if resolved[name] or defaults[name]]
    return " ".join([value, *(f"{name}={resolved[name]}" for name in stated)])


def _render_attrs(attrs: dict[str, str]) -> str:
    return " ".join(f"{k}={v}" for k, v in sorted(attrs.items()))
