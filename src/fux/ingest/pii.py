"""PII redaction — what is removed from the COMMITTED INDEX and nowhere else.

A corpus contains things that must not travel: an email address in a support
ticket, a card number pasted into a runbook, an employee id in a spreadsheet.
The index is the one plane in `.fux/` that goes into git and is cloned by
everyone, so it is the one plane where those values become a distribution
problem rather than an access-control problem.

## The rule, stated once

**Redact what gets committed. Leave alone what stays local.**

| plane | PII | why |
|---|---|---|
| `.fux/index/` | **redacted** | committed, cloned, travels to every machine |
| `.fux/acquired/` | raw | gitignored; it must stay the exact bytes the source returned, or the `as-ingested` verdict is a lie (ADR-URL-FRESHNESS decision 6) |
| `runtime/display-cache` | as extracted | gitignored, local, and derived from the redacted text anyway |
| `refer` passages, `fux answer` | raw | read from the source or the retained bytes under the reader's own access, and never committed |

⚠ **So `fux answer` can quote a value the index does not contain.** That is
this design working, not a gap: the reader already has access to the document —
they are quoting from it — and what changed is that the value no longer ships
inside a committed artifact to everyone who clones the repo. A consumer who
needs redaction at answer time as well needs a different decision from this
one, and it is not this file's.

## Why the sha is computed BEFORE redaction

The record's `sha` fingerprints the **raw** document, and it must, because
`refer` verifies a citation by fetching the source and comparing shas. If the
index stored the sha of redacted text, every document with a single PII hit
would compare unequal against its own unchanged source and be reported `stale`
forever — a defect that presents as a working feature. So the ordering in
`run.py` is fixed and load-bearing:

    raw bytes -> content_sha  ->  redact  ->  extract -> terms/title/phrases

A sha is a hash of the whole document and leaks nothing on its own.

## Rules are the consumer's; the engine ships the matcher

`.fux/pii.toml` is a table of named regex rules, applied **in file order**,
each a full pass. Fux ships a starter file a consumer edits and owns. There is
no built-in floor here and deliberately so: unlike a magic byte, *what counts
as PII* is a policy question that differs by jurisdiction, industry and
corpus, and a floor fux imposed would be both wrong somewhere and impossible
to switch off.

## Determinism

Same bytes plus same rules gives the same output, always — no clock, no
randomness, no ordering dependence beyond the declared file order. That is
what keeps L3 true with redaction switched on.

⚠ **Editing `pii.toml` must invalidate extraction reuse**, or documents whose
bytes did not change keep terms built under the OLD rules. `digest()` is what
`run.py` compares to detect that; it is not decoration.

⚠ **A pathological regex can hang an ingest.** Python's `re` has no timeout,
so a pattern with nested quantifiers over a long line is the one failure this
module cannot defend against. Patterns that can match the empty string are
refused (they are the common accident), `fux doctor` compiles every pattern
offline, and beyond that a consumer's regex is a consumer's regex.
"""

from __future__ import annotations

import hashlib
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from ..errors import FuxError

RULES_NAME = "pii.toml"

#: Regex flags a rule may name. A closed set, like every other attribute
#: vocabulary in the source lists: an unknown flag is a typo that would
#: silently change nothing, which is the failure `refusals.py` refuses too.
_FLAGS: dict[str, int] = {
    "ignorecase": re.IGNORECASE,
    "multiline": re.MULTILINE,
    "dotall": re.DOTALL,
    "verbose": re.VERBOSE,
}

#: The keys a rule may declare. Anything else raises.
_KEYS = ("name", "pattern", "replacement", "flags", "group")
_REQUIRED = ("name", "pattern")


@dataclass(frozen=True)
class Rule:
    """One PII signature and what replaces it."""

    name: str
    pattern: str
    replacement: str
    flags: tuple[str, ...] = ()
    #: Which capture group to replace. `0` (the default) replaces the whole
    #: match; a positive integer replaces only that group and leaves the rest
    #: of the match in place -- which is how a rule keeps its own context
    #: ("card ending 4242" -> "card ending [PII:card]") without needing a
    #: variable-width lookbehind Python does not support.
    group: int = 0

    def compiled(self) -> re.Pattern:
        return _compile(self)

    def apply(self, text: str) -> tuple[str, int]:
        """Redacted text, and how many values were replaced."""
        rx = self.compiled()
        if self.group == 0:
            return rx.subn(self.replacement, text)

        count = 0

        def _sub(match: re.Match) -> str:
            nonlocal count
            if match.group(self.group) is None:
                return match.group(0)
            count += 1
            start, end = match.span(self.group)
            offset = match.start()
            whole = match.group(0)
            return whole[: start - offset] + self.replacement + whole[end - offset :]

        return rx.sub(_sub, text), count


def _compile(rule: Rule) -> re.Pattern:
    flags = 0
    for name in rule.flags:
        flags |= _FLAGS[name]
    try:
        return re.compile(rule.pattern, flags)
    except re.error as exc:
        raise FuxError(f"pii rule {rule.name!r}: invalid regex ({exc})") from exc


def rules_path(root: Path) -> Path:
    """`.fux/pii.toml` — fixed, deliberately not configurable.

    Beside `.fuxignore`, `tune.toml`, `output.toml` and `refusals.toml`, none
    of which are relocatable either.
    """
    return root / ".fux" / RULES_NAME


def load(root: Path) -> tuple[Rule, ...]:
    """Parse `.fux/pii.toml`. Absent is `()`; malformed raises.

    Absent is a legitimate configuration — a repo of public documentation has
    no PII to remove. Malformed raises for the same reason `refusals.toml`
    does: a rules file that silently failed to parse looks exactly like a repo
    with no rules, and the consequence is discovered by someone reading a
    committed index months later.
    """
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
            raise FuxError(f"{where}: {key!r} is required and must be a non-empty string")
    name = entry["name"]
    where = f"{origin}: rule {name!r}"
    if name in seen:
        raise FuxError(f"{where}: duplicate rule name — names identify a rule in reports")
    seen.add(name)

    unknown = sorted(k for k in entry if k not in _KEYS)
    if unknown:
        raise FuxError(
            f"{where}: unknown key(s): {', '.join(unknown)} — known: {', '.join(_KEYS)}"
        )

    flags = _flags(entry, where)
    group = _group(entry, where)
    # ⚠ The default is derived from the name rather than being a constant, so
    # a reader of a redacted index can see WHICH rule fired without opening
    # the rules file. A single `[REDACTED]` everywhere destroys that.
    replacement = entry.get("replacement", f"[PII:{name}]")
    if not isinstance(replacement, str):
        raise FuxError(f"{where}: 'replacement' must be a string (got {replacement!r})")

    rule = Rule(
        name=name,
        pattern=entry["pattern"],
        replacement=replacement,
        flags=flags,
        group=group,
    )

    rx = _compile(rule)  # fail at LOAD time, never mid-ingest
    if rx.search("") is not None:
        raise FuxError(
            f"{where}: this pattern matches the empty string, so it would fire between "
            "every character in every document. Anchor it, or require at least one "
            "character"
        )
    if group and group > rx.groups:
        raise FuxError(
            f"{where}: group {group} but the pattern has {rx.groups} capture group(s)"
        )
    return rule


def _flags(entry: dict, where: str) -> tuple[str, ...]:
    if "flags" not in entry:
        return ()
    value = entry["flags"]
    if not isinstance(value, list) or not value:
        raise FuxError(f"{where}: 'flags' must be a non-empty list of strings")
    out = []
    for item in value:
        if item not in _FLAGS:
            raise FuxError(
                f"{where}: unknown flag {item!r} — known: {', '.join(sorted(_FLAGS))}"
            )
        out.append(item)
    return tuple(out)


def _group(entry: dict, where: str) -> int:
    if "group" not in entry:
        return 0
    value = entry["group"]
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise FuxError(f"{where}: 'group' must be an integer >= 0 (got {value!r})")
    return value


# -- applying ---------------------------------------------------------------


def redact(rules: tuple[Rule, ...], text: str) -> tuple[str, dict[str, int]]:
    """Apply every rule in file order. Returns the text and per-rule hit counts.

    ⚠ **Order is observable, and that is why it is the file's order rather
    than anything fux computes.** A rule can match text a previous rule already
    inserted -- a `replacement` of `[PII:email]` is matched by a later rule
    whose pattern is `\\[.*\\]`. Nothing here prevents that; the counts are
    reported so a consumer can see a rule firing far more often than the corpus
    can explain, which is what that mistake looks like.
    """
    if not rules or not text:
        return text, {}
    hits: dict[str, int] = {}
    for rule in rules:
        text, count = rule.apply(text)
        if count:
            hits[rule.name] = hits.get(rule.name, 0) + count
    return text, hits


def digest(rules: tuple[Rule, ...]) -> str:
    """A stable fingerprint of the ruleset, for cache invalidation.

    ⚠ **Load-bearing, not diagnostic.** Extraction is reused when a document's
    content sha is unchanged, and redaction happens BEFORE extraction — so
    editing `pii.toml` changes what should be extracted while changing no
    document's bytes. Without this, a rule added today would never reach a
    document that did not also change, and the index would hold terms built
    under two different policies with nothing to say which.

    Empty ruleset gives the empty string, so a repo with no rules writes no
    state and behaves exactly as it did before this feature existed.
    """
    if not rules:
        return ""
    h = hashlib.sha256()
    for rule in rules:
        h.update(rule.name.encode("utf-8"))
        h.update(b"\0")
        h.update(rule.pattern.encode("utf-8"))
        h.update(b"\0")
        h.update(rule.replacement.encode("utf-8"))
        h.update(b"\0")
        h.update(",".join(rule.flags).encode("utf-8"))
        h.update(b"\0")
        h.update(str(rule.group).encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()
