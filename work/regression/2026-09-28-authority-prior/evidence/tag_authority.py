#!/usr/bin/env python3
"""W-168 step 8 — the `authority_reach` tag, key-free, and its pool.

Under the ruled factor S2, `f = 1 − 1/(authors × commits)` is above zero exactly
when a document has MORE THAN ONE COMMIT (more than one author implies it). So
the documents the prior can lift are the rows of `multi-commit.tsv`, counted
from the arm tree's `git log --name-only`: paths and counts only, no author.

A question is tagged iff a lifted document sits at ranks 2–10 of its baseline
hand-off: only then can a multiplier move rank 1. The pool is tag ∩ miss@1 ∩
hit@10, read from that hand-off's score rows (which carry no answer).

    .venv/bin/python work/regression/2026-09-28-authority-prior/evidence/tag_authority.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN9 = HERE.parents[1] / "2026-09-28-intent-prior"
HANDOFF = RUN9 / "evidence/ip-0.1/rung-01000/handoff-set-4-claude.jsonl"
SCORES = RUN9 / "scores/ip-0.1/rung-01000/set-4-claude.json"

lifted = {line.split("\t")[0] for line in (HERE / "multi-commit.tsv").read_text().splitlines() if line}
rows = [json.loads(l) for l in HANDOFF.read_text(encoding="utf-8").splitlines() if l.strip()]
scored = {r["id"]: r for r in json.loads(SCORES.read_text())["rows"]}

tags = []
for row in rows:
    ranked = [x for x in row.get("ranked") or [] if x][:10]
    if any(x in lifted for x in ranked[1:]):
        tags.append(row["id"])
pool = [q for q in tags if not scored[q]["hit@1"] and scored[q]["hit@10"]]
held = [q for q in tags if scored[q]["hit@1"]]
(HERE / "tags-set-4-claude.jsonl").write_text("".join(json.dumps({"id": q, "tag": "authority_reach"}) + "\n" for q in tags))
print(f"lifted documents={len(lifted)} tagged={len(tags)} pool(miss@1 ∩ hit@10)={len(pool)} tagged_rank1_hits={len(held)}")
print("pool:", " ".join(pool))
