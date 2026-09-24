#!/usr/bin/env python3
"""W-168 step pools on the scored generation-2 capture (2026-09-24).

Tags come from question TEXT alone (SR-WORK-TESTDATA T2) and from seed/ — never
from the key. Correctness comes from `score.py`'s own output under scores/,
which carries ids, ranks and flags only. Prints counts, never a question.

A pool is tagged ∩ answerable ∩ missing the endpoint; "reorderable" means the
target is already in the returned ten (the capture asked `--top 10`, so
`hit@10` is the deepest rank known — `hit@50` equals it by construction).

    .venv/bin/python work/regression/2026-09-24-golden-gen2-rung-01000/evidence/step_pools.py
"""

from __future__ import annotations

import json
import pathlib
import re

from fux.query.tokenize import tokenize

ROOT = pathlib.Path(__file__).resolve().parents[4]
SEED = ROOT / "work" / "golden" / "seed"
RUN = pathlib.Path(__file__).resolve().parents[1]

#: step 9's I1 lexicon as DRAFTED in compare/intent-doctype-prior — not ruled.
CUES = {
    "procedure": [r"^how (do|should|can) (i|we)\b", r"^how to\b", r"\bsteps? to\b", r"^what (do|should) (i|we) do\b"],
    "rationale": [r"^why\b", r"\bwhat was the (reason|rationale)\b"],
    "reference": [r"^what is\b", r"^what does\b.*\bmean\b", r"^what'?s the\b", r"^define\b"],
}


def seed_inputs():
    docs = {p.relative_to(SEED).as_posix(): p.read_text(errors="replace") for p in SEED.rglob("*") if p.is_file()}
    toks = {k: set(tokenize(v)) for k, v in docs.items()}
    anchor: set[str] = set()
    for k, v in docs.items():
        for text, tgt in re.findall(r"\[([^\]]+)\]\(([^)\s#]+)", v):
            t = (pathlib.PurePosixPath(k).parent / tgt).as_posix()
            if t in toks:
                anchor |= set(tokenize(text)) - toks[t]
    forms: set[str] = set()
    for v in docs.values():
        for longf, short in re.findall(r"\b((?:[A-Z][a-z]+[\s-]+){1,6}[A-Za-z]+)\s+\(([A-Z][A-Za-z]{1,6})\)", v):
            forms.add(short.lower())
            forms.add(" ".join(tokenize(longf.replace("The ", ""))))
    glossary = docs.get("33-cold-chain-glossary.md", "")
    for line in glossary.splitlines():
        if re.match(r"^\s*(?:[-*]\s+)?\**[A-Za-z]", line) and re.search(r"(—|–|:)\s", line):
            head = re.split(r"\s*(?:—|–|:)\s", re.sub(r"[*\-]", "", line).strip(), maxsplit=1)[0]
            if tokenize(head):
                forms.add(" ".join(tokenize(head)))
    return anchor, forms


def main() -> None:
    anchor, forms = seed_inputs()
    print(f"anchor-distinctive words {len(anchor)} · expansion forms {len(forms)}")
    for s in ("2-u", "3-u"):
        questions = {}
        for line in (ROOT / "work" / "golden" / "questions" / f"set-{s}.jsonl").read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                questions[row["id"]] = row["question"]
        rows = {r["id"]: r for r in json.loads((RUN / "scores" / "single" / "rung-01000" / f"set-{s}.json").read_text())["rows"]}
        tags: dict[str, set] = {"1 anchor": set(), "2 identifier": set(), "4 expansion": set(), "9 intent": set()}
        for qid, q in questions.items():
            qt = tokenize(q)
            qs, qj = set(qt), " ".join(qt)
            if qs & anchor:
                tags["1 anchor"].add(qid)
            if re.search(r"\b[A-Z]{2,5}-\d{1,4}\b", q):
                tags["2 identifier"].add(qid)
            if any((f in qs) if " " not in f else (f in qj) for f in forms):
                tags["4 expansion"].add(qid)
            if any(re.search(p, q.lower().strip()) for ps in CUES.values() for p in ps):
                tags["9 intent"].add(qid)
        print(f"set-{s}")
        print("  step           tagged answerable miss@1 reorderable@1 miss@5 reorderable@5 not-in-top10")
        for step, ids in tags.items():
            ans = [i for i in ids if not rows[i]["answered_unanswerable"]]
            m1 = [i for i in ans if not rows[i]["hit@1"]]
            m5 = [i for i in ans if not rows[i]["hit@5"]]
            print(f"  {step:14} {len(ids):6} {len(ans):10} {len(m1):6} {sum(rows[i]['hit@10'] for i in m1):13}"
                  f" {len(m5):6} {sum(rows[i]['hit@10'] for i in m5):13} {sum(not rows[i]['hit@10'] for i in ans):12}")


if __name__ == "__main__":
    main()
