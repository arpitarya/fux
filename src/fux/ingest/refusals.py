"""Refusal detection — the response the server sent INSTEAD of the document.

A refusal is a sign-in wall, a session-expired interstitial, a paywall, a 403
shell, a geo-block. It arrives looking like a success and decodes perfectly
well as HTML, which is exactly what makes it dangerous: nothing downstream can
tell it from a real document, and an indexed login page is a confident wrong
answer that survives until a human reads it.

## Two layers, and only one of them is yours

**The magic-byte floor is fux's and is always on.** A declared content type
that disagrees with the response's first bytes is a fact about *formats* —
OOXML opens `PK\\x03\\x04`, PDF opens `%PDF-` — and formats are the engine's
business. `refusals.toml` cannot switch it off.

**Everything else is the consumer's**, declared in `.fux/refusals.toml`, and
fux ships no knowledge of any vendor. The rules table ADDS refusals; it can
never subtract one.

## Every condition is pure over the bytes, and that is not an oversight

There is no `status`, no `final_url_host`, no "were you redirected" here.
[ADR-FETCHER](../../docs/adr/0019_fetcher.md) decision 13 says fux never reads
a status code, a header or an error string — a fetcher knows it speaks HTTP,
and fux deliberately does not — and its veto condition names *this file's
caller* by path. `content_type` is admissible because a MIME type is FORMAT
vocabulary; a `302` is TRANSPORT vocabulary and belongs to whatever protocol
the fetcher happens to speak.

⚠ **The cost of that is near zero, which is why the rule held rather than
being amended.** An identity provider that bounces you still has to return a
page, and that page is HTML where a document was requested — caught by the
shipped `document-request-returned-a-web-page` rule without knowing the
provider exists. Provider-specific detection survives as `body_contains` over
form-field names (`name="loginfmt"`, `name="SAMLRequest"`), which are an API
between the page and its own backend and so outlive the redesigns that rewrite
every visible string. **Reopen only on a real captured refusal that these
conditions cannot express.**

## Missing is not malformed

A **missing** file is a legitimate configuration: this repo has no
organisation-specific refusals and the magic-byte floor is its protection.
Silence.

A **malformed** file raises. A rules file that silently failed to parse would
look exactly like a repo with no rules, and the consequence — a login page in
the index — is discovered weeks later by a human reading an answer. This is
the same strictness `config.py` applies to `fux.toml` and for the same reason.

An **undeclared condition key** raises too. A typo'd condition that quietly
does nothing is a rule that reads as protection and is not, which is the
failure `http.py`'s `configure()` already refuses for tunables.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from ..errors import FuxError

RULES_NAME = "refusals.toml"

#: Content type -> the bytes a real document of that type must begin with.
#:
#: Keyed by MIME rather than by extension so this module never imports
#: `urlsrc._TYPE_EXT` — the dependency runs the other way, and a cycle between
#: the fetch path and its own guard is how a guard ends up unimportable.
#:
#: ⚠ **Only formats with a fixed, unambiguous signature appear here.** A type
#: absent from this table is simply not checked; guessing a signature would
#: turn the always-on floor into a source of false refusals, and a floor that
#: cries wolf gets switched off.
MAGIC: dict[str, bytes] = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": b"PK\x03\x04",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": b"PK\x03\x04",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": b"PK\x03\x04",
    "application/vnd.oasis.opendocument.text": b"PK\x03\x04",
    "application/pdf": b"%PDF-",
}

#: How much of a TEXTY body `body_contains` may search.
#:
#: ⚠ **This was 64 KiB and that was too small, measured rather than argued.**
#: A live Office web viewer arrived as 160,068 bytes of HTML that decoded to
#: two words, and its `WacFrame_Excel` marker sat at roughly byte 101,000 --
#: past the cap, so the rule written to catch that exact page could not see
#: it and the shell was indexed as a document.
#:
#: The original 64 KiB was reasoning about the wrong risk. The cost it feared
#: was scanning a 40 MB workbook for a login string, but a workbook is binary
#: and `_searchable_text` already declines to decode it. What actually reaches
#: this path is HTML, which is being decoded anyway; a megabyte of it is
#: microseconds. The cap stays only so a pathological response cannot make
#: matching unbounded.
BODY_SCAN_BYTES = 1024 * 1024

#: Below this, a response is searched for text markers whatever its declared
#: type — an error shell served as `application/octet-stream` is still an
#: error shell, and at this size the scan is free.
ALWAYS_SCAN_UNDER = 8 * 1024

_TEXTY_PREFIXES = ("text/", "application/xhtml", "application/xml", "application/json")

#: The conditions a rule may declare. Anything else raises rather than being
#: ignored — see the module docstring.
_CONDITIONS = (
    "content_type",
    "requested_suffix",
    "requested_suffix_not",
    "body_contains",
    "body_starts_with",
    "max_bytes",
)

_REQUIRED = ("name", "reason")


@dataclass(frozen=True)
class Rule:
    """One refusal signature. Conditions present are ANDed; lists are ORed."""

    name: str
    reason: str
    content_type: tuple[str, ...] = ()
    requested_suffix: tuple[str, ...] = ()
    requested_suffix_not: tuple[str, ...] = ()
    body_contains: tuple[str, ...] = ()
    body_starts_with: bytes | None = None
    max_bytes: int | None = None

    def matches(self, *, suffix: str, mime: str, raw: bytes, text: str | None) -> bool:
        if self.content_type and not any(mime.startswith(c) for c in self.content_type):
            return False
        if self.requested_suffix and suffix not in self.requested_suffix:
            return False
        if self.requested_suffix_not and suffix in self.requested_suffix_not:
            return False
        if self.body_starts_with is not None and not raw.startswith(self.body_starts_with):
            return False
        if self.max_bytes is not None and len(raw) >= self.max_bytes:
            return False
        if self.body_contains:
            # ⚠ `text is None` means the body was not searchable (large and
            # binary), which is NOT a match. A rule that fires because we could
            # not look is a rule that refuses real documents.
            if text is None or not any(needle in text for needle in self.body_contains):
                return False
        return True


def rules_path(root: Path) -> Path:
    """`.fux/refusals.toml` — a fixed location, deliberately not configurable.

    It sits beside `.fuxignore`, `tune.toml` and `output.toml`, none of which
    are relocatable either. A knob here would buy nothing and cost a key in
    `fux.toml` that every reader has to learn.
    """
    return root / ".fux" / RULES_NAME


def load(root: Path) -> tuple[Rule, ...]:
    """Parse `.fux/refusals.toml`. Absent is `()`; malformed raises."""
    path = rules_path(root)
    if not path.is_file():
        return ()
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise FuxError(f"{path}: invalid TOML ({exc})") from exc
    except OSError as exc:
        raise FuxError(f"{path}: cannot be read ({exc})") from exc
    return parse(data, origin=str(path))


def parse(data: dict, *, origin: str) -> tuple[Rule, ...]:
    """Declared table -> rules, in file order. Every fault names the rule."""
    if not isinstance(data, dict):
        raise FuxError(f"{origin}: expected a table of [[rule]] entries")
    raw_rules = data.get("rule", [])
    if not isinstance(raw_rules, list):
        raise FuxError(f"{origin}: [[rule]] must be an array of tables")
    unknown_top = sorted(k for k in data if k != "rule")
    if unknown_top:
        raise FuxError(
            f"{origin}: unknown top-level key(s): {', '.join(unknown_top)} — "
            "this file holds [[rule]] entries and nothing else"
        )

    out: list[Rule] = []
    seen: set[str] = set()
    for index, entry in enumerate(raw_rules, start=1):
        out.append(_rule(entry, origin=origin, index=index, seen=seen))
    return tuple(out)


def _rule(entry, *, origin: str, index: int, seen: set[str]) -> Rule:
    where = f"{origin}: rule #{index}"
    if not isinstance(entry, dict):
        raise FuxError(f"{where}: must be a table")

    for key in _REQUIRED:
        value = entry.get(key)
        if not isinstance(value, str) or not value.strip():
            raise FuxError(
                f"{where}: {key!r} is required and must be a non-empty string. "
                + (
                    "`fux doctor` reports it, so a refused URL can say which rule caught it"
                    if key == "name"
                    else "it is recorded verbatim as the skip reason a human reads"
                )
            )
    name = entry["name"]
    where = f"{origin}: rule {name!r}"
    if name in seen:
        raise FuxError(f"{where}: duplicate rule name — names identify a rule in reports")
    seen.add(name)

    unknown = sorted(k for k in entry if k not in _CONDITIONS and k not in _REQUIRED)
    if unknown:
        raise FuxError(
            f"{where}: unknown condition(s): {', '.join(unknown)} — known: "
            f"{', '.join(_CONDITIONS)}. A typo'd condition would silently do "
            "nothing, leaving a rule that reads as protection and is not"
        )

    declared = [k for k in _CONDITIONS if k in entry]
    if not declared:
        raise FuxError(
            f"{where}: declares no conditions, so it would refuse every document. "
            f"Add at least one of: {', '.join(_CONDITIONS)}"
        )

    return Rule(
        name=name,
        reason=entry["reason"],
        content_type=_strs(entry, "content_type", where, lower=True),
        # ⚠ `allow_empty` on the suffix lists only. `""` is a REAL suffix — it
        # is how a rule says "a URL that names no extension", and the shipped
        # starter depends on it so that a bare wiki URL returning HTML is not
        # refused corpus-wide. An empty `content_type` prefix or an empty
        # `body_contains` needle would match every response instead, which is
        # a rule that silently refuses everything.
        requested_suffix=_strs(entry, "requested_suffix", where, lower=True, allow_empty=True),
        requested_suffix_not=_strs(
            entry, "requested_suffix_not", where, lower=True, allow_empty=True
        ),
        body_contains=_strs(entry, "body_contains", where),
        body_starts_with=_hex(entry, "body_starts_with", where),
        max_bytes=_positive_int(entry, "max_bytes", where),
    )


def _strs(
    entry: dict, key: str, where: str, *, lower: bool = False, allow_empty: bool = False
) -> tuple[str, ...]:
    if key not in entry:
        return ()
    value = entry[key]
    if not isinstance(value, list) or not value:
        raise FuxError(f"{where}: {key!r} must be a non-empty list of strings")
    out: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise FuxError(f"{where}: every entry in {key!r} must be a string")
        if not item and not allow_empty:
            raise FuxError(
                f"{where}: {key!r} contains an empty string, which would match every "
                "response — remove it, or state the value you meant"
            )
        out.append(item.lower() if lower else item)
    return tuple(out)


def _hex(entry: dict, key: str, where: str) -> bytes | None:
    if key not in entry:
        return None
    value = entry[key]
    if not isinstance(value, str) or not value.strip():
        raise FuxError(f"{where}: {key!r} must be space-separated hex, e.g. \"50 4b 03 04\"")
    try:
        return bytes.fromhex(value.replace(" ", ""))
    except ValueError as exc:
        raise FuxError(
            f"{where}: {key!r} is not valid hex ({exc}) — write it as \"50 4b 03 04\""
        ) from exc


def _positive_int(entry: dict, key: str, where: str) -> int | None:
    if key not in entry:
        return None
    value = entry[key]
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise FuxError(f"{where}: {key!r} must be a positive integer (got {value!r})")
    return value


# -- matching ---------------------------------------------------------------


def suffix_of(url: str) -> str:
    """The extension the URL asks for, lowercased; `""` when it names none.

    Deliberately the *requested* suffix and not anything the response said —
    it is what the consumer's line asked for, which is the half of the
    comparison a refusal cannot forge.
    """
    try:
        path = urlsplit(url).path
    except ValueError:
        return ""
    return PurePosixPath(path).suffix.lower()


def _mime(content_type: str) -> str:
    return (content_type or "").split(";", 1)[0].strip().lower()


def _searchable_text(mime: str, raw: bytes) -> str | None:
    """The first `BODY_SCAN_BYTES` as text, or `None` when not worth searching.

    `errors="replace"` rather than a strict decode: a refusal page with one
    mis-encoded byte is still a refusal page, and a decode that raised here
    would turn a guard into a crash on exactly the malformed input it exists
    to catch.
    """
    if not raw:
        return ""
    if mime.startswith(_TEXTY_PREFIXES) or len(raw) <= ALWAYS_SCAN_UNDER:
        return raw[:BODY_SCAN_BYTES].decode("utf-8", errors="replace")
    return None


def magic_mismatch(content_type: str, raw: bytes) -> str | None:
    """The always-on floor: does the body begin the way its type requires?

    Returns a reason, or `None` when there is nothing to say — an unknown
    type, or bytes that start correctly. **Not configurable**, because this is
    a fact about the format rather than about anyone's identity provider.
    """
    expected = MAGIC.get(_mime(content_type))
    if expected is None or raw.startswith(expected):
        return None
    return (
        f"declared {_mime(content_type)} but the body does not start like one — "
        "the response is not the document it claims to be"
    )


def refused(rules: tuple[Rule, ...], url: str, content_type: str, raw: bytes) -> str | None:
    """The reason this response is a refusal, or `None`.

    The floor is checked first and cannot be overridden; then the consumer's
    rules in file order, first match winning. The returned string is recorded
    verbatim as the skip reason, so it is written as an instruction rather
    than a diagnosis.
    """
    floor = magic_mismatch(content_type, raw)
    if floor is not None:
        return floor
    if not rules:
        return None
    mime = _mime(content_type)
    suffix = suffix_of(url)
    text = _searchable_text(mime, raw)
    for rule in rules:
        if rule.matches(suffix=suffix, mime=mime, raw=raw, text=text):
            return f"{rule.reason} [{rule.name}]"
    return None
