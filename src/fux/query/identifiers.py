"""Identifier families — `.fux/identifiers.toml`, matched on both sides (W-233).

**What this adds to the analyzer, and what it leaves alone.** Analyzer v3 keeps
`RF-118` whole when it is *written* `RF-118`. It does nothing for `RF 118`,
`rf118`, `RF–118` or `ADR-4` against `ADR-0004`, and the measured result of that
is the exact document ranking **second**, below a neighbour that merely shares
the parts ([fixture run](../../../work/regression/2026-09-28-identifier-fixture/report.md)).
A *family* — a template such as `RF-{n}` — is matched against the TEXT, and each
match adds ONE term, its **canonical form** (`rf-118`), beside v3's own terms.
v3's output is never changed or removed, so an empty file is byte-identical to
no feature at all, and that is also the rollback.

**The file has two owners** (Arpit, 2026-09-28, F1–F5):

    [user]       keep = [...templates]   drop = [...templates]   regex = [...]
    [detected]   families = [...templates]      # written by `fux identifiers --write`

The effective rule list is `(detected − user.drop) ∪ user.keep`, then
`user.regex`. **`[user]` always wins and the engine never writes it.** A file
with only `[user]` is valid; so is a file with both sections empty.

**Templates are the default and the only form detection writes.** Regex is
allowed in `[user]` only, for experts, behind a STATIC guard (`check_regex`):
no timeout exists anywhere in this module, because a timeout is wall-clock and
L4 forbids wall-clock output.

🔴 **The Node reader transcribes this module** (`node/src/query/identifiers.mjs`),
and a divergence is a silent no-match — the query writes a canonical term the
index never did. `tests/query/identifiers-fixture.json` is read by both readers'
tests from one file.
"""

from __future__ import annotations

import hashlib
import re
import tomllib
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from ..constants import fixed
from ..errors import FuxError

#: The characters a template's `-` or `_` accepts in the text: both ASCII
#: separators, the Unicode dashes, and one space. `constants.toml
#: [identifiers] flexible_separators` — the Node twin reads the same key.
_FLEX = fixed("identifiers", "flexible_separators")
_FLEX_CLASS = "[" + "".join(re.escape(c) for c in _FLEX) + "]"
#: A match may not touch a letter, a digit or a flexible separator on either
#: side, nor a `.` that continues into an alphanumeric (`v2.3.1.4` is not
#: `v2.3.1`). `/`, `:`, `?`, `#` and sentence punctuation are boundaries —
#: that is what reaches `…/wiki/RF-118?rev=2`.
_EDGE = "[A-Za-z0-9" + "".join(re.escape(c) for c in _FLEX if c != " ") + "]"
_LEAD = rf"(?<!{_EDGE})(?<![A-Za-z0-9]\.)"
_TRAIL = rf"(?!{_EDGE})(?!\.[A-Za-z0-9])"
_RUN_OF_FLEX = re.compile(_FLEX_CLASS + "+")

FILE = fixed("files", "identifiers")
_DIGEST_BYTES = fixed("identifiers", "digest_bytes")

_PLACEHOLDER = re.compile(r"\{([A-Za-z]+)\}")


@dataclass(frozen=True)
class Rule:
    """One compiled family. `plan` rebuilds the canonical form from a match."""

    source: str  # as written in the file
    kind: str  # "template" | "regex"
    pattern: str  # flavour-neutral regex source, no outer boundaries
    plan: tuple  # template: (("lit", s) | ("sep", c) | ("n",) | ("X",)); regex: ()


def _kind(ch: str) -> str:
    return "d" if ch.isdigit() else "a"


def parse_template(src: str) -> Rule:
    """`RF-{n}` → a Rule. Raises `FuxError` naming the problem.

    The grammar (compare doc S2): letters and digits are literals, matched
    case-insensitively; `-` and `_` are FLEXIBLE separators; `.` `/` `:` match
    themselves; `{n}` is a digit run with leading zeros dropped from the
    canonical form; `{X}` is a letter run. **A template must start with a
    literal letter** — without it `{X}-{n}` matches `step 4`.
    """
    where = f"identifier template {src!r}"
    if not isinstance(src, str) or not src:
        raise FuxError(f"{where}: must be a non-empty string")
    if not src[0].isascii() or not src[0].isalpha():
        raise FuxError(f"{where}: must start with a literal letter (e.g. RF-{{n}}), "
                       "so that prose like 'step 4' cannot match it")
    # Tokenise into elements: ("lit", ch) | ("sep", ch) | ("punct", ch) | ("n",) | ("X",)
    elems: list[tuple] = []
    i = 0
    while i < len(src):
        m = _PLACEHOLDER.match(src, i)
        if m:
            name = m.group(1)
            if name not in ("n", "X"):
                raise FuxError(f"{where}: unknown placeholder {{{name}}} - only {{n}} and {{X}}")
            elems.append((name,))
            i = m.end()
            continue
        ch = src[i]
        if ch.isascii() and ch.isalnum():
            elems.append(("lit", ch))
        elif ch in "-_":
            elems.append(("sep", ch))
        elif ch in "./:":
            elems.append(("punct", ch))
        else:
            raise FuxError(f"{where}: {ch!r} is not allowed - letters, digits, - _ . / : "
                           "and {n} {X} only; use a [user] regex for anything else")
        i += 1
    if not any(e[0] in ("n", "X") for e in elems):
        raise FuxError(f"{where}: has no {{n}} or {{X}} - a fixed string is not a family")

    def side(e: tuple, first: bool) -> str | None:
        # The character class an element presents at its left (first) or right edge.
        if e[0] == "lit":
            return _kind(e[1])
        if e[0] == "n":
            return "d"
        if e[0] == "X":
            return "a"
        return None

    parts: list[str] = []
    plan: list[tuple] = []
    for idx, e in enumerate(elems):
        prev = elems[idx - 1] if idx else None
        if e[0] in ("n", "X") and prev is not None and prev[0] in ("lit", "n", "X"):
            if side(prev, False) == side(e, True):
                raise FuxError(f"{where}: {{{e[0]}}} directly after a same-kind element is "
                               "ambiguous — put a separator between them")
        if e[0] == "lit":
            parts.append(re.escape(e[1]))
            plan.append(("lit", e[1].lower()))
        elif e[0] == "punct":
            parts.append(re.escape(e[1]))
            plan.append(("lit", e[1]))
        elif e[0] == "n":
            parts.append("([0-9]+)")
            plan.append(("n",))
        elif e[0] == "X":
            parts.append("([A-Za-z]+)")
            plan.append(("X",))
        else:  # a flexible separator
            nxt = elems[idx + 1] if idx + 1 < len(elems) else None
            if prev is None or nxt is None or prev[0] in ("sep", "punct") or nxt[0] in ("sep", "punct"):
                raise FuxError(f"{where}: a separator must sit between two letters, digits or placeholders")
            # Empty is allowed only where the boundary is visible without it:
            # letter<->digit (`rf118`). `RFQA` for `RF-QA` is not recoverable.
            optional = side(prev, False) != side(nxt, True)
            parts.append(_FLEX_CLASS + ("?" if optional else ""))
            plan.append(("sep", e[1]))
    return Rule(source=src, kind="template", pattern="".join(parts), plan=tuple(plan))


# ---- the regex guard (F3) ---------------------------------------------------

#: Escapes a [user] regex may use, and what each becomes. `\\d` and `\\w` are
#: REWRITTEN to ASCII classes so both readers agree; the rest pass through.
_CLASS_ESC = {"d": "0-9", "w": "A-Za-z0-9_"}
_PLAIN_ESC = set("tnr") | set("\\.-/()[]{}*+?|^$#:, ")


def check_regex(src: str) -> str:
    """Validate a [user] regex and return its flavour-neutral source.

    **Static and deterministic** (compare doc S7) — there is no timeout, because
    a timeout is wall-clock (L4). One walk over the source:

    - **refused:** any `(?` except `(?:` (lookaround, named groups, inline
      flags, atomic groups, comments, conditionals); a quantifier after `)`
      (nested or overlapping quantifiers backtrack catastrophically — quantify
      single characters or classes only); a possessive quantifier; `^` or `$`
      outside a class; an unescaped `.`; `\\s`, `\\S`, `\\D`, `\\W`, `\\p`,
      `\\B`, a digit escape (a backreference) or any escape not listed; set
      operations or a nested `[` inside a class;
    - **rewritten:** `\\d` → `[0-9]`, `\\w` → `[A-Za-z0-9_]`; a capturing group
      becomes `(?:…)`, since the canonical form uses the whole match.

    ⚠ **Adjacent overlapping quantifiers (`\\d+\\d+`) are accepted.** They are
    polynomial, not exponential, and every match is bounded by one document.
    """
    where = f"identifier regex {src!r}"
    if not isinstance(src, str) or not src:
        raise FuxError(f"{where}: must be a non-empty string")
    out: list[str] = []
    depth = 0
    in_class = False
    prev_quant = False
    i = 0
    n = len(src)
    while i < n:
        ch = src[i]
        if ch == "\\":
            if i + 1 >= n:
                raise FuxError(f"{where}: ends in a lone backslash")
            e = src[i + 1]
            if e in _CLASS_ESC:
                out.append(_CLASS_ESC[e] if in_class else f"[{_CLASS_ESC[e]}]")
                i += 2
            elif e == "b" and not in_class:
                out.append("\\b")
                i += 2
            elif e in "xu":
                width = 2 if e == "x" else 4
                hexpart = src[i + 2:i + 2 + width]
                if len(hexpart) != width or any(c not in "0123456789abcdefABCDEF" for c in hexpart):
                    raise FuxError(f"{where}: refused - \\{e} needs exactly {width} hex digits")
                out.append(src[i:i + 2 + width])
                i += 2 + width
            elif e in _PLAIN_ESC:
                out.append(src[i:i + 2])
                i += 2
            else:
                raise FuxError(f"{where}: refused - the escape \\{e} is not portable between "
                               "Python and JS (allowed: \\d \\w \\b \\t \\n \\r \\xhh \\uhhhh and escaped punctuation)")
            prev_quant = False
            continue
        if in_class:
            if ch == "]":
                in_class = False
            elif ch == "[" or src.startswith(("&&", "--", "~~", "||"), i):
                raise FuxError(f"{where}: refused - a nested '[' or a set operation inside a class")
            out.append(ch)
            i += 1
            continue
        if ch == "[":
            in_class = True
            out.append(ch)
            if src.startswith("[^", i):
                out.append("^")
                i += 1
            i += 1
            prev_quant = False
            continue
        if ch in "^$":
            raise FuxError(f"{where}: refused - an anchor (^ or $); multiline semantics differ "
                           "between the readers, and the engine adds its own boundaries")
        if ch == ".":
            raise FuxError(f"{where}: refused - an unescaped '.' matches different sets in "
                           "Python and JS; write \\. or a class")
        if ch == "(":
            if src.startswith("(?", i):
                if not src.startswith("(?:", i):
                    raise FuxError(f"{where}: refused - '(?' other than '(?:' (lookaround, named "
                                   "groups, inline flags, atomic groups) is flavour-dependent")
                i += 3
            else:
                i += 1
            out.append("(?:")
            depth += 1
            prev_quant = False
            continue
        if ch == ")":
            depth -= 1
            if depth < 0:
                raise FuxError(f"{where}: unbalanced ')'")
            out.append(ch)
            i += 1
            if i < n and src[i] in "*+?{":
                raise FuxError(f"{where}: refused - a quantifier on a group can backtrack "
                               "catastrophically; quantify single characters or classes only")
            prev_quant = False
            continue
        if ch in "*+?" or ch == "{":
            if ch == "{":
                close = src.find("}", i)
                body = src[i + 1:close] if close > 0 else ""
                if close < 0 or not re.fullmatch(r"[0-9]+(,[0-9]*)?", body):
                    raise FuxError(f"{where}: refused - '{{' must be a quantifier {{m}}, {{m,}} or {{m,n}}; "
                                   "escape a literal brace")
                out.append(src[i:close + 1])
                i = close + 1
            else:
                if prev_quant and ch != "?":
                    raise FuxError(f"{where}: refused - a stacked or possessive quantifier")
                out.append(ch)
                i += 1
            if i < n and src[i] == "+":
                raise FuxError(f"{where}: refused - a possessive quantifier (Python only)")
            prev_quant = True
            continue
        out.append(ch)
        i += 1
        prev_quant = False
    if depth or in_class:
        raise FuxError(f"{where}: unbalanced group or class")
    body = "".join(out)
    try:
        compiled = re.compile(body, re.ASCII | re.IGNORECASE)
    except re.error as exc:
        raise FuxError(f"{where}: invalid regex ({exc})") from exc
    # Python's finditer and a JS exec loop step past an EMPTY match differently,
    # so a pattern that can match nothing is refused rather than reconciled.
    if compiled.fullmatch(""):
        raise FuxError(f"{where}: refused - it can match the empty string")
    return body


def parse_regex(src: str) -> Rule:
    return Rule(source=src, kind="regex", pattern=check_regex(src), plan=())


# ---- the effective rule set -------------------------------------------------


@dataclass(frozen=True)
class IdentifierRules:
    """The effective, ordered rule list and its combined matcher.

    **Order is deterministic and is part of the digest:** templates sorted by
    source, then regexes in file order. Alternation is leftmost-first in both
    Python `re` and V8, so the same order gives the same match on both readers.
    """

    rules: tuple[Rule, ...]

    @property
    def empty(self) -> bool:
        return not self.rules

    @property
    def digest(self) -> str:
        """Of the EFFECTIVE rules, not the file bytes — a comment edit moves nothing.
        Empty for no rules, so a repo without families writes no state."""
        if not self.rules:
            return ""
        blob = "\n".join(f"{r.kind}\t{r.source}" for r in self.rules)
        return hashlib.blake2b(blob.encode("utf-8"), digest_size=_DIGEST_BYTES).hexdigest()

    def combined_source(self) -> str:
        return _LEAD + "(?:" + "|".join(f"({r.pattern})" for r in self.rules) + ")" + _TRAIL

    def matches(self, text: str) -> list[tuple[int, int, str]]:
        """`(start, end, canonical)` for every match, in text order."""
        if not self.rules:
            return []
        rx, groups, gated = _compiled(self)
        if gated is None:
            return [_found(m, groups) for m in rx.finditer(text)]
        # 🔴 **The gated scan (W-239), and why it returns exactly what the
        # `finditer` above would.** Every template starts with a literal letter
        # (`parse_template` refuses anything else), so a match can only start on
        # one of those letters where the leading boundary holds — `gate` finds
        # exactly those positions, cheaply. At such a position every family
        # whose first letter differs fails on its first character, so trying
        # only the families that share it, IN THEIR ORIGINAL ORDER, picks the
        # same alternative leftmost-first alternation would. Scanning resumes
        # at a match's end, as `finditer` does. The combined pattern tried 103
        # alternatives behind two lookbehinds at every character; this was
        # 2 ms/KB of every ingested document.
        #
        # The Node reader keeps the combined pattern: it matches questions, not
        # documents, and the two give the same answer.
        gate, by_letter = gated
        out = []
        pos = 0
        while True:
            g = gate.search(text, pos)
            if g is None:
                return out
            start = g.start()
            sub_rx, sub_groups = by_letter[text[start].lower()]
            m = sub_rx.match(text, start)
            if m is None:
                pos = start + 1
                continue
            out.append(_found(m, sub_groups))
            pos = m.end()


def _found(m: re.Match, groups: list[tuple]) -> tuple[int, int, str]:
    for rule, g0, ng in groups:
        if m.group(g0) is not None:
            return (m.start(), m.end(), canonical(rule, m.group(g0), [m.group(g0 + 1 + k) for k in range(ng)]))
    raise AssertionError("a combined match with no alternative group")  # unreachable


_CACHE: dict[tuple, tuple] = {}
_FLAGS = re.ASCII | re.IGNORECASE


def _alternation(rules: list[Rule]) -> tuple[re.Pattern, list[tuple]]:
    """`LEAD(?:(r1)|(r2)|…)TRAIL` and, per rule, `(rule, its group, its group count)`."""
    groups = []
    g = 1
    for r in rules:
        n = re.compile(r.pattern).groups
        groups.append((r, g, n))
        g += 1 + n
    return re.compile(IdentifierRules(rules=tuple(rules)).combined_source(), _FLAGS), groups


def _compiled(rules: IdentifierRules):
    key = tuple((r.kind, r.source) for r in rules.rules)
    hit = _CACHE.get(key)
    if hit is None:
        rx, groups = _alternation(list(rules.rules))
        gated = None
        # A [user] regex may start with anything, so it has no first letter to
        # gate on; a file holding one keeps the combined scan.
        if all(r.kind == "template" for r in rules.rules):
            by_letter: dict[str, list[Rule]] = {}
            for r in rules.rules:  # file order, which is the alternation order
                by_letter.setdefault(r.source[0].lower(), []).append(r)
            letters = "".join(sorted(by_letter))
            # The consumed letter is the candidate; the two lookbehinds are
            # `_LEAD`'s, shifted one character left to sit before it.
            gate = re.compile(
                f"[{letters}](?<!{_EDGE}.)(?<![A-Za-z0-9]\\..)", _FLAGS
            )
            gated = (gate, {ch: _alternation(rs) for ch, rs in by_letter.items()})
        hit = (rx, groups, gated)
        _CACHE[key] = hit
    return hit


def canonical(rule: Rule, whole: str, captured: list[str]) -> str:
    """The one term a match adds. Template: the plan instantiated. Regex: the
    match lowercased with every run of flexible separators read as `-`."""
    if rule.kind == "regex":
        return _RUN_OF_FLEX.sub("-", whole.lower())
    out = []
    k = 0
    for step in rule.plan:
        if step[0] in ("lit", "sep"):
            out.append(step[1])
        elif step[0] == "n":
            out.append(captured[k].lstrip("0") or "0")
            k += 1
        else:
            out.append(captured[k].lower())
            k += 1
    return "".join(out)


def build(detected: list[str], keep: list[str], drop: list[str], regex: list[str]) -> IdentifierRules:
    """`(detected − drop) ∪ keep`, sorted, then the regexes in file order."""
    dropped = set(drop)
    templates = sorted((set(detected) - dropped) | (set(keep) - dropped))
    rules = [parse_template(t) for t in templates]
    for t in drop:  # a drop entry must itself be a valid template, or it is a typo
        parse_template(t)
    rules.extend(parse_regex(r) for r in regex)
    return IdentifierRules(rules=tuple(rules))


def path(root: Path) -> Path:
    return root / FILE


def template_text() -> str:
    """The packaged `identifiers.toml` — what `fux setup` and `doctor --fix` write."""
    return (resources.files("fux") / "templates" / fixed("templates", "identifiers")).read_text(
        encoding="utf-8"
    )


def _strings(table: dict, key: str, where: str) -> list[str]:
    value = table.get(key, [])
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise FuxError(f"{where} {key}: must be a list of strings")
    return value


def parse(data: dict, *, origin: str) -> IdentifierRules:
    unknown = set(data) - {"user", "detected"}
    if unknown:
        raise FuxError(f"{origin}: unknown table(s) {sorted(unknown)} - only [user] and [detected]")
    user = data.get("user", {})
    detected = data.get("detected", {})
    if not isinstance(user, dict) or not isinstance(detected, dict):
        raise FuxError(f"{origin}: [user] and [detected] must be tables")
    bad = (set(user) - {"keep", "drop", "regex"}) | {f"detected.{k}" for k in set(detected) - {"families"}}
    if bad:
        raise FuxError(f"{origin}: unknown key(s) {sorted(bad)}")
    return build(
        _strings(detected, "families", f"{origin}: [detected]"),
        _strings(user, "keep", f"{origin}: [user]"),
        _strings(user, "drop", f"{origin}: [user]"),
        _strings(user, "regex", f"{origin}: [user]"),
    )


def load(root: Path) -> IdentifierRules:
    """Parse `.fux/identifiers.toml`. **Absent raises** (L12: the file's
    existence is the contract; `fux setup` writes it). Empty sections are fine."""
    p = path(root)
    if not p.is_file():
        raise FuxError(f"{p} is missing - run `fux setup` to write it (both sections may stay empty)")
    try:
        data = tomllib.loads(p.read_bytes().decode("utf-8-sig"))
    except tomllib.TOMLDecodeError as exc:
        raise FuxError(f"{p}: invalid TOML ({exc})") from exc
    return parse(data, origin=str(p))


EMPTY = IdentifierRules(rules=())

#: `for_root`'s cache, keyed by the file's path, mtime and size — the
#: `decode._BINDINGS` pattern. Per process, and re-read the moment the file
#: changes, so a long-lived `serve` or MCP process never analyzes with stale
#: families. Keyed by path, so two repos in one process never share an entry.
_BY_ROOT: dict[tuple, IdentifierRules] = {}


def for_root(root: Path) -> IdentifierRules:
    """`load(root)`, cached on the file's stat. Raises exactly as `load` does."""
    p = path(root)
    try:
        st = p.stat()
    except OSError:
        return load(root)  # raises the missing-file error
    key = (str(p.resolve()), st.st_mtime_ns, st.st_size)
    hit = _BY_ROOT.get(key)
    if hit is None:
        hit = _BY_ROOT[key] = load(root)
    return hit
