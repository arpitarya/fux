#!/usr/bin/env python3
"""W-168 step 9 — the `intent_cue` tag on set-4-claude, from question TEXT alone.

The I1 lexicon exactly as drafted in `compare/intent-doctype-prior` and ruled by
Arpit on 2026-09-24 (*"agree implement all"*), copied from the 2026-09-24 pools
script. It is BOTH the verdict's tag and, after the build, the engine's cue
lexicon: a test will hold the engine's list equal to `CUES` below, so the tag and
the mechanism cannot drift apart.

A question is tagged with the FIRST intent whose pattern matches its lowercased,
stripped text, in the order procedure → rationale → reference. Prints one JSON
line per tagged question, `{"id", "intent"}`, sorted by id — ids only, no text.

    python3 work/regression/2026-09-28-intent-prior/evidence/tag_intent.py > tags-set-4-claude.jsonl
"""

from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[4]
SET = ROOT / "work" / "golden" / "questions" / "set-4-claude.jsonl"

CUES = {
    "procedure": [r"^how (do|should|can) (i|we)\b", r"^how to\b", r"\bsteps? to\b", r"^what (do|should) (i|we) do\b"],
    "rationale": [r"^why\b", r"\bwhat was the (reason|rationale)\b"],
    "reference": [r"^what is\b", r"^what does\b.*\bmean\b", r"^what'?s the\b", r"^define\b"],
}


def intent(question: str) -> str | None:
    q = question.lower().strip()
    for name, patterns in CUES.items():
        if any(re.search(p, q) for p in patterns):
            return name
    return None


def main() -> None:
    rows = []
    for line in SET.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            hit = intent(r["question"])
            if hit:
                rows.append({"id": r["id"], "intent": hit})
    for r in sorted(rows, key=lambda r: r["id"]):
        print(json.dumps(r, sort_keys=True))


if __name__ == "__main__":
    main()
