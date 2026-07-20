"""Glob matching with proper `**` semantics — fnmatch treats `**` as `*` and
won't match files directly under a `**/` segment. This translates gitignore-style
globs to regex so `a/**/b.py` matches both `a/b.py` and `a/x/y/b.py`.
"""
from __future__ import annotations

import re
from functools import lru_cache


@lru_cache(maxsize=512)
def _regex(pattern: str) -> re.Pattern:
    i, n, out = 0, len(pattern), []
    while i < n:
        if pattern[i:i + 3] == "**/":
            out.append("(?:.*/)?")          # zero or more directory segments
            i += 3
        elif pattern[i:i + 2] == "**":
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")             # a single path segment
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def match(path: str, pattern: str) -> bool:
    return _regex(pattern).match(path) is not None


def match_any(path: str, patterns: list[str]) -> bool:
    return any(match(path, p) for p in patterns)
