#!/usr/bin/env python3
"""W-168 step 4 — the `expansion_form` tag, from question TEXT and seed/ alone.

**The rule is `step_pools.py`'s "4 expansion" rule, unchanged**
(`work/regression/2026-09-24-golden-gen2-rung-01000/evidence/step_pools.py`),
which is the rule the ruled pool of 10 was counted with. One thing differs, and
it is the reason this file exists: the seed documents are the ones
`work/golden/ladder/rung-01000.sha256` lists, **checked by hash**, and not
whatever `work/golden/seed/` holds today. Generation 3 added 26 seed documents
on 2026-09-27 that rung-01000 does not carry; a form mined from one of them
could not be in the arm's index, and counting it would tag a question for an
input that is not there (SR-RS d23a).

SR-WORK-TESTDATA T2: no key, no score, no engine output. Prints one JSON row per
question (`id`, `tagged`, `forms`) and a count line on stderr — never question
text.

    .venv/bin/python work/regression/2026-09-27-mined-expansion/evidence/tag_expansion.py \
        > work/regression/2026-09-27-mined-expansion/evidence/tags-set-3-u.jsonl
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

from fux.query.tokenize import tokenize

ROOT = pathlib.Path(__file__).resolve().parents[4]
GOLDEN = ROOT / "work" / "golden"
MANIFEST = GOLDEN / "ladder" / "rung-01000.sha256"
QUESTIONS = GOLDEN / "questions" / "set-3-u.jsonl"


def rung_seed() -> dict[str, str]:
    """`seed/…` path → text, for exactly the seed documents rung-01000 was built from."""
    docs: dict[str, str] = {}
    for line in MANIFEST.read_text().splitlines():
        parts = line.split()
        if len(parts) < 2 or not parts[1].startswith("seed/"):
            continue
        sha, rel = parts[0], parts[1]
        path = GOLDEN / rel
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != sha:
            sys.exit(f"{rel}: work/golden/ differs from the rung-01000 manifest; the tag would be counted on the wrong input")
        docs[rel[len("seed/"):]] = data.decode(errors="replace")
    return docs


def forms(docs: dict[str, str]) -> set[str]:
    """step_pools.py's `seed_inputs()` expansion half, verbatim."""
    out: set[str] = set()
    for v in docs.values():
        for longf, short in re.findall(r"\b((?:[A-Z][a-z]+[\s-]+){1,6}[A-Za-z]+)\s+\(([A-Z][A-Za-z]{1,6})\)", v):
            out.add(short.lower())
            out.add(" ".join(tokenize(longf.replace("The ", ""))))
    glossary = docs.get("33-cold-chain-glossary.md", "")
    for line in glossary.splitlines():
        if re.match(r"^\s*(?:[-*]\s+)?\**[A-Za-z]", line) and re.search(r"(—|–|:)\s", line):
            head = re.split(r"\s*(?:—|–|:)\s", re.sub(r"[*\-]", "", line).strip(), maxsplit=1)[0]
            if tokenize(head):
                out.add(" ".join(tokenize(head)))
    return out


def main() -> None:
    fs = forms(rung_seed())
    n = tagged = 0
    for line in QUESTIONS.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        qt = tokenize(row["question"])
        qs, qj = set(qt), " ".join(qt)
        hit = sorted(f for f in fs if ((f in qs) if " " not in f else (f in qj)))
        n += 1
        tagged += bool(hit)
        print(json.dumps({"id": row["id"], "tagged": bool(hit), "forms": hit}, sort_keys=True))
    print(f"forms {len(fs)} · questions {n} · tagged {tagged}", file=sys.stderr)


if __name__ == "__main__":
    main()
