"""W-168 step 9 — a question's intent, and the document type it prefers.

Three pieces, ruled D2 · I1 · M1 on 2026-09-24
([SR-TUNE](../../../records/0135_tuning.md) decision 20):

- **I1, the cue lexicon** — `[intent]` in `constants.toml`. A fixed engine
  value, not a tunable: the pre-registration froze it, and a test holds it
  equal to the frozen tag.
- **D2, the `[doctype]` table** — glob → type, the consumer's own, in
  `.fux/tune.toml`, read at query time. Empty by default.
- **M1, the prior** — `[ranking] intent_weight` scales a document whose type
  matches the question's intent by `1 + intent_weight`. It is applied by
  `rank.Weighting`, the one multiplier both candidate paths share, so `--fast`
  and `--scan` cannot disagree about it.

🔴 **Python and Node must agree byte for byte**, and three places they would
not by default are closed here, identically in `node/src/query/intent.mjs`:

- *Case and whitespace.* Only ASCII letters are lowercased and only ASCII
  whitespace is collapsed. `str.lower` and `toLowerCase`, `\\s` in either
  engine, all disagree on some non-ASCII character.
- *`\\b`.* Python's is Unicode-aware; JavaScript's is ASCII. Compiled with
  `re.ASCII`, Python's is ASCII too.
- *`.`.* Python's skips `\\n` only; JavaScript's skips four line terminators.
  With `re.DOTALL` here and the `s` flag there, both match every character.

A glob is matched by hand over code points rather than compiled to a regex,
for the same reason: `*` matches any run of characters including `/`, `?`
exactly one, and nothing else is special. Where two patterns match, the
longest wins, ties by code-point order — `[priority]`'s rule, so a result
never depends on file order (L4).
"""

from __future__ import annotations

import re
from functools import cache

from ..constants import fixed, table

__all__ = ["TYPES", "glob_match", "intent_of", "prepare", "type_for", "type_of_intent"]

_ASCII_SPACE = re.compile(r"[ \t\n\r\f\v]+")
_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


@cache
def _lexicon() -> tuple[tuple[str, tuple[re.Pattern, ...]], ...]:
    order = fixed("intent", "order")
    return tuple(
        (name, tuple(re.compile(p, re.ASCII | re.DOTALL) for p in fixed("intent", name)))
        for name in order
    )


def _types() -> dict[str, str]:
    return dict(table("intent.type"))


#: The types a `[doctype]` entry may declare: every intent's preferred type.
TYPES: frozenset[str] = frozenset(_types().values())


def prepare(question: str) -> str:
    """ASCII whitespace collapsed to one space and trimmed; ASCII letters lowercased."""
    return _ASCII_SPACE.sub(" ", question).strip(" ").translate(_LOWER)


def intent_of(question: str) -> str | None:
    """The first intent in `[intent] order` with a matching cue, or `None`."""
    q = prepare(question)
    for name, patterns in _lexicon():
        if any(p.search(q) for p in patterns):
            return name
    return None


def type_of_intent(intent: str) -> str:
    """The document type an intent prefers."""
    return _types()[intent]


def glob_match(pattern: str, text: str) -> bool:
    """Whole-string wildcard match: `*` any run (including `/`), `?` one character."""
    p, t = 0, 0
    star, mark = -1, 0
    while t < len(text):
        if p < len(pattern) and (pattern[p] == "?" or (pattern[p] != "*" and pattern[p] == text[t])):
            p += 1
            t += 1
        elif p < len(pattern) and pattern[p] == "*":
            star, mark = p, t
            p += 1
        elif star >= 0:
            p = star + 1
            mark += 1
            t = mark
        else:
            return False
    while p < len(pattern) and pattern[p] == "*":
        p += 1
    return p == len(pattern)


def type_for(loc: str, doctype: tuple[tuple[str, str], ...]) -> str | None:
    """The declared type of a location. `doctype` is sorted longest-first by the loader."""
    for pattern, kind in doctype:
        if glob_match(pattern, loc):
            return kind
    return None
