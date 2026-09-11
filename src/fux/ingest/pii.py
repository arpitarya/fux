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

⚠ **The file itself is required** (ADR-PII decision 17): `fux setup` writes the
starter, `load()` raises without it, and the CLI refuses every verb but
`setup`, `tune`, `output` and `doctor`. A file with no rules is legal and
redacts nothing -- that is a committed choice. A missing file is an accident.

## Checksums are the engine's, and the set is closed

A regex sees shape. A payment card and an Aadhaar number also carry a check
digit, and a regex cannot compute one, so a shape-only rule for either is full
of order ids and timestamps. `validate = "luhn"` or `validate = "verhoeff"`
makes a rule replace **only the matches whose digits pass**. The set is closed
and engine-owned rather than a consumer hook: a hook is consumer code running
inside ingest, and determinism would stop being this engine's guarantee and
become each consumer's (ADR-PII decision 16).

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
import json
import re
import tomllib
from collections.abc import Callable
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

# -- checksum validators ------------------------------------------------------
#
# ⚠ **A checksum is a 1-in-10 filter, not an identity.** A random run of digits
# passes Luhn, and passes Verhoeff, one time in ten. `validate` cuts a
# shape-only rule's false positives by about an order of magnitude and never to
# zero -- which is why the starter still ships both checksum rules commented
# out (ADR-PII decision 12).

_ASCII_DIGITS = "0123456789"


def _digits(text: str) -> list[int]:
    """Every ASCII digit in `text`, in order; everything else is ignored.

    Separators (`4111 1111`, `2345-6789`) drop out, which is the point. A
    non-ASCII digit (`²`, `٣`) is not a digit here: neither scheme is defined
    over one, and `str.isdigit` would quietly let it in.
    """
    return [ord(ch) - 48 for ch in text if ch in _ASCII_DIGITS]


def luhn(text: str) -> bool:
    """The Luhn mod-10 check (ISO/IEC 7812-1 Annex B) — payment cards, IMEI.

    Catches every single-digit error and most adjacent transpositions, but not
    `09` <-> `90`. Fewer than two digits is never valid: a check digit needs a
    payload to check.
    """
    digits = _digits(text)
    if len(digits) < 2:
        return False
    total = 0
    for position, digit in enumerate(reversed(digits)):
        if position % 2:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


#: Verhoeff's multiplication table for the dihedral group D5.
_VERHOEFF_D = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 2, 3, 4, 0, 6, 7, 8, 9, 5),
    (2, 3, 4, 0, 1, 7, 8, 9, 5, 6),
    (3, 4, 0, 1, 2, 8, 9, 5, 6, 7),
    (4, 0, 1, 2, 3, 9, 5, 6, 7, 8),
    (5, 9, 8, 7, 6, 0, 4, 3, 2, 1),
    (6, 5, 9, 8, 7, 1, 0, 4, 3, 2),
    (7, 6, 5, 9, 8, 2, 1, 0, 4, 3),
    (8, 7, 6, 5, 9, 3, 2, 1, 0, 4),
    (9, 8, 7, 6, 5, 4, 3, 2, 1, 0),
)

#: Verhoeff's position permutation; row `i` is applied at position `i mod 8`.
_VERHOEFF_P = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 5, 7, 6, 2, 8, 3, 0, 9, 4),
    (5, 8, 0, 3, 7, 9, 6, 1, 4, 2),
    (8, 9, 1, 6, 0, 4, 3, 5, 2, 7),
    (9, 4, 5, 3, 1, 2, 7, 6, 8, 0),
    (4, 2, 8, 6, 5, 7, 3, 9, 0, 1),
    (2, 7, 9, 3, 8, 0, 6, 4, 1, 5),
    (7, 0, 4, 6, 9, 1, 3, 2, 5, 8),
)


def verhoeff(text: str) -> bool:
    """The Verhoeff (1969) dihedral check — the last digit of an Aadhaar number.

    Catches every single-digit error and every adjacent transposition,
    including the `09` <-> `90` that Luhn misses. Fewer than two digits is
    never valid, for the same reason as `luhn`.
    """
    digits = _digits(text)
    if len(digits) < 2:
        return False
    check = 0
    for position, digit in enumerate(reversed(digits)):
        check = _VERHOEFF_D[check][_VERHOEFF_P[position % 8][digit]]
    return check == 0


#: Checksum validators a rule may name. A CLOSED set, like `_FLAGS`: an
#: unknown name raises at load. ⚠ **Not a plugin point, on purpose** — a
#: consumer-supplied function would be consumer code inside ingest (ADR-PII
#: decision 16). A new scheme is added here, with its test vectors, or not at all.
_VALIDATORS: dict[str, Callable[[str], bool]] = {
    "luhn": luhn,
    "verhoeff": verhoeff,
}

#: The keys a rule may declare. Anything else raises.
_KEYS = ("name", "pattern", "replacement", "flags", "group", "validate")
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
    #: A checksum the replaced value must pass, named from `_VALIDATORS`, or
    #: `""` for none. It narrows WHICH matches are replaced and never changes
    #: WHAT replaces them.
    validate: str = ""

    def compiled(self) -> re.Pattern:
        return _compile(self)

    def accepts(self, match: re.Match) -> bool:
        """Would this match be replaced?

        The target is what `group` names -- the whole match for `0` -- and a
        checksum runs over the target's ASCII digits only. So a rule that keeps
        its context (`card ending ([0-9 ]{19})`, `group = 1`) validates the
        captured value and never the label around it, and a whole-match rule
        whose pattern swallows a stray digit of context will fail its checksum.
        """
        target = match.group(self.group)
        if target is None:
            return False
        if not self.validate:
            return True
        return _VALIDATORS[self.validate](target)

    def apply(self, text: str) -> tuple[str, int]:
        """Redacted text, and how many values were replaced."""
        rx = self.compiled()
        if self.group == 0 and not self.validate:
            return rx.subn(self.replacement, text)

        count = 0

        def _sub(match: re.Match) -> str:
            nonlocal count
            if not self.accepts(match):
                return match.group(0)
            count += 1
            if self.group == 0:
                # `expand`, not the bare string: the template semantics `subn`
                # gives the no-checksum path above, so adding `validate` to a
                # rule changes which values go and never what replaces them.
                return match.expand(self.replacement)
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


def require(root: Path) -> Path:
    """`.fux/pii.toml`, or `FuxError` naming the fix. ADR-PII decision 17.

    The one place the refusal is worded: `load()` calls it, and the CLI gate
    calls it on the path where the file is missing, so a person meets the same
    sentence whichever layer stopped them.
    """
    path = rules_path(root)
    if not path.is_file():
        raise FuxError(
            f"{path.relative_to(root).as_posix()} is missing, and fux will not run without it (ADR-PII decision 17). "
            "Run `fux setup` to write the starter, then review its rules; to redact "
            "nothing, keep the file with no [[rule]] entries."
        )
    return path


def load(root: Path) -> tuple[Rule, ...]:
    """Parse `.fux/pii.toml`. Absent raises; malformed raises; no rules is `()`.

    ⚠ **Absent raised nothing until 2026-09-11** -- it read as "no rules", and
    a deleted file was indistinguishable from a public-docs repo that had
    decided to redact nothing. Decision 17 keeps the second and refuses the
    first: a file with every rule commented out still loads to `()`.

    Malformed raises for the same reason `refusals.toml` does: a rules file
    that silently failed to parse looks exactly like a repo with no rules, and
    the consequence is discovered by someone reading a committed index months
    later.
    """
    path = require(root)
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
    validate = _validate(entry, where)
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
        validate=validate,
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


def _validate(entry: dict, where: str) -> str:
    if "validate" not in entry:
        return ""
    value = entry["validate"]
    if not isinstance(value, str) or value not in _VALIDATORS:
        raise FuxError(
            f"{where}: unknown validator {value!r} — known: {', '.join(sorted(_VALIDATORS))}"
        )
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

    **The digest covers `validate` too**: a checksum changes which values reach
    the index exactly as a pattern edit does.

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
        # ⚠ `validate` rides in the group slot as `"<group>:<name>"`, and only
        # when set. The slot is otherwise digits alone, so no checksum-free
        # ruleset can spell one that has a checksum -- and every ruleset written
        # before checksums existed keeps its digest, so upgrading fux forces no
        # full re-extract that no edit of the consumer's caused.
        slot = f"{rule.group}:{rule.validate}" if rule.validate else str(rule.group)
        h.update(slot.encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()


# -- the counter ---------------------------------------------------------------
#
# W-101 item 4. `redact()` has always returned per-rule hit counts and `run()`
# has always summed them; **nothing ever read the sum**, so *"did my rule do
# anything, and to how much"* had no answer between runs. The counts are the
# only observable a consumer has about a policy that is otherwise invisible by
# construction — the redacted text is what got committed, and the original is
# what stayed on disk.
#
# ⚠ **Gitignored, advisory, and never an input to anything.** It lives beside
# `pii-digest` under `runtime/`, is rebuilt by the next ingest, and no code path
# reads it back into a decision. A counter that could change what is indexed
# would be a second policy input nobody declared.
#
# ⚠ **What `doctor` still cannot see is unchanged.** A well-formed rule that is
# too broad shows up here as a large number, which is a *hint* and not the
# finding — `tools/pii-probe/` is the instrument, and a big count on a big
# corpus is exactly what a correct rule looks like too.

COUNTS_NAME = "pii-counts.json"


@dataclass(frozen=True)
class Counts:
    """What the last ingest redacted, per rule.

    Two dictionaries rather than one total, because **they have different
    coverage and merging them would state a completeness neither has.**

    * `body` is corpus-wide and complete: `run()`'s redact phase walks every
      parsed document on every ingest, changed or not.
    * `enrichment` is **this run's re-extracted documents only** — enrichment
      is redacted inside the extract loop, which incremental ingest skips for
      a document whose sha and enrichment both held. `partial` says so.
    """

    body: dict[str, int]
    enrichment: dict[str, int]
    #: True when the run that wrote this reused any extraction, so
    #: `enrichment` covers part of the corpus. Never affects `body`.
    partial: bool = False
    #: How many documents the redact phase walked — the denominator a count
    #: means nothing without.
    documents: int = 0

    @property
    def total(self) -> int:
        return sum(self.body.values()) + sum(self.enrichment.values())

    def as_json(self) -> dict:
        return {
            "body": dict(sorted(self.body.items())),
            "enrichment": dict(sorted(self.enrichment.items())),
            "partial": self.partial,
            "documents": self.documents,
        }


def counts_path(root: Path) -> Path:
    from ..store import fuxdir

    return fuxdir.fux_dir(root) / "runtime" / COUNTS_NAME


def record_counts(
    root: Path,
    *,
    body: dict[str, int],
    enrichment: dict[str, int],
    partial: bool,
    documents: int,
) -> None:
    """Write the counts this run produced. **Never raises.**

    Replaced, never accumulated: `body` is a corpus-wide census taken on every
    ingest, so adding today's to yesterday's would report a corpus several
    times its own size. That is the opposite of `urlstate.rate_limited`, which
    accumulates because each entry is one event that happened once.
    """
    from ..store import fuxdir

    try:
        fuxdir.derived_dir(root, "runtime")
        payload = Counts(body=body, enrichment=enrichment, partial=partial, documents=documents)
        counts_path(root).write_text(
            json.dumps(payload.as_json(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except (OSError, TypeError, ValueError):
        # A counter that could fail an ingest is worse than a missing counter.
        pass


def read_counts(root: Path) -> Counts | None:
    """The last run's counts, or `None` when nothing has been recorded.

    `None` and *"zero redactions"* are different answers and are kept apart:
    the first means no ingest has run since the counter existed, the second
    means rules ran and matched nothing. Collapsing them would let a repo whose
    rules have never executed read as a repo whose rules found nothing.
    """
    try:
        raw = json.loads(counts_path(root).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(raw, dict):
        return None

    def _counts(value) -> dict[str, int]:
        if not isinstance(value, dict):
            return {}
        return {
            k: v for k, v in value.items() if isinstance(k, str) and isinstance(v, int) and v > 0
        }

    documents = raw.get("documents")
    return Counts(
        body=_counts(raw.get("body")),
        enrichment=_counts(raw.get("enrichment")),
        partial=bool(raw.get("partial")),
        documents=documents if isinstance(documents, int) and documents >= 0 else 0,
    )
