#!/usr/bin/env python3
"""Do the generated documents name anything generation 3's seeds introduced?

The generator's `SEED_ENTITIES` blacklist predates seeds 16–62, so the rule
"no new document states a fact about a seed entity" is checked here after the
build instead: every capitalised word and every code (`ABC-12`, `F1-A`) that
occurs in seeds 37–62 and in NO earlier seed, intersected with the words of
`rung-10000/ext/` (a superset of every smaller rung's ext). The intersection is
printed for a person to read; a common English word is not an entity.

    python3 new_seed_name_leaks.py <fux repo> <rung-10000 dir>

Reads `work/golden/seed/` only — never `questions/`, never a key.
"""
import re
import sys
from pathlib import Path

repo, rung = Path(sys.argv[1]), Path(sys.argv[2])
TOKEN = re.compile(r"\b(?:[A-Z][A-Za-z]{2,}|[A-Z0-9]{1,6}-[A-Z0-9-]{1,8})\b")


def tokens(paths):
    out = set()
    for p in paths:
        out |= set(TOKEN.findall(p.read_text(encoding="utf-8", errors="replace")))
    return out


def number(p):
    m = re.match(r"a?(\d+)-", p.name)
    return int(m.group(1)) if m else -1


seed = [p for p in (repo / "work/golden/seed").rglob("*") if p.is_file()]
new = tokens(p for p in seed if 37 <= number(p) <= 62 and p.parent.name == "seed")
old = tokens(p for p in seed if not (37 <= number(p) <= 62 and p.parent.name == "seed"))
ext = tokens(p for p in (rung / "ext").rglob("*") if p.is_file())
hits = sorted((new - old) & ext)
print(f"new-only tokens: {len(new - old)} · also in ext: {len(hits)}")
for t in hits:
    print(" ", t)
