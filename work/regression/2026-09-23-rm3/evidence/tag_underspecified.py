#!/usr/bin/env python3
"""Tag `rm3_underspecified` on a released question set — from the TEXT alone.

W-168 step 5's coverage tag ([SR-WORK-TESTDATA](../../../../records/0068_WORK-test-data.md)
T2, [SR-RS](../../../../records/0133_predictions.md) d23c). Frozen with the
pre-registration beside it; the rule is stated there and implemented here.

**A question is under-specified iff it carries NO anchor token** — nothing that
names its subject, so the asker describes the thing instead of naming it. An
anchor token is any of:

- a token containing a digit (`2016`, `3pm`, `RF-118`);
- an identifier-shaped token — alphanumerics joined by `-`, `_`, `/` or `.`
  **and carrying a capital or a digit** (`RF-118`, `Compliance-Red`); an
  all-lowercase compound (`three-day`, `dry-ice`) is ordinary English;
- a capitalised token that is not sentence-initial and is not `I` or an `I'`
  contraction (`Nagpur`, `American`, `UPS`);
- a quoted span (`"…"`, `“…”`, `‘…’`, `` `…` ``).

It reads `{"id", "question"}` rows and nothing else: no key, no score, no engine.

    python3 tag_underspecified.py work/golden/questions/set-2-u.jsonl > tags-set-2-u.jsonl
"""

from __future__ import annotations

import json
import re
import sys

TOKEN = re.compile(r"[^\s—–(),;:!?]+")
IDENT = re.compile(r"[A-Za-z0-9]+(?:[-_/.][A-Za-z0-9]+)+")
QUOTED = re.compile(r"\"[^\"]+\"|“[^”]+”|‘[^’]+’|`[^`]+`")
PRONOUN_I = re.compile(r"^I(?:['’](?:m|ve|d|ll))?$")


def anchors(text: str) -> list[str]:
    """Every anchor token in one question, in order of appearance."""
    found = [m.group(0) for m in QUOTED.finditer(text)]
    # Sentence position resets after `.`, `?` or `!`, so split on those first.
    for sentence in re.split(r"(?<=[.?!])\s+", text):
        first = True
        for m in TOKEN.finditer(sentence):
            tok = m.group(0).strip("'\"‘’“”.")
            if not tok:
                continue
            if any(c.isdigit() for c in tok):
                found.append(tok)
            elif IDENT.fullmatch(tok) and any(c.isupper() for c in tok) and not first:
                found.append(tok)
            elif tok[0].isupper() and not first and not PRONOUN_I.match(tok):
                found.append(tok)
            first = False
    return found


def main(argv: list[str]) -> int:
    rows = [json.loads(l) for l in open(argv[0], encoding="utf-8") if l.strip()]
    for row in rows:
        found = anchors(row["question"])
        print(json.dumps({
            "id": row["id"],
            "rm3_underspecified": not found,
            "anchors": found,
        }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
