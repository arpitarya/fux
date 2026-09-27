#!/usr/bin/env python3
"""The pre-registration's S1–S5, read from the hand-off alone.

Descriptive only: it opens `handoff-set-4-claude.jsonl` and nothing else, and it
never says whether an answer is right — no key reaches the session that runs it.

    python3 work/regression/2026-09-27-golden-set-4-rung-01000/evidence/describe.py
"""

from __future__ import annotations

import collections
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = [json.loads(line) for line in (HERE / "handoff-set-4-claude.jsonl").open()]

bands = collections.Counter(r["band"] for r in rows)
print(f"questions                        {len(rows)}")
print(f"rows carrying funnel gates  (S4) {sum(r['gates'] is not None for r in rows)}")
print(f"empty ranked lists          (S3) {sum(not r['ranked'] for r in rows)}")
print(f"ranked lists shorter than 10     {sum(0 < len(r['ranked']) < 10 for r in rows)}")
print(f"answers declined            (S1) {sum(not r['answer_text'] for r in rows)}")
print(f"answers with no citation         {sum(not r['citations'] for r in rows)}")
print(f"answerable: true                 {sum(r['answerable'] is True for r in rows)}")
for b in ("grounded", "partial", "weak", "none"):
    print(f"band {b:<9}              (S2) {bands.get(b, 0)}")
top = [r["ranked"][0] for r in rows if r["ranked"]]
print(f"rank-1 document under seed/      {sum(p.startswith('seed/') for p in top)}")
print(f"rank-1 document archived         {sum('/archive/' in p for p in top)}")
print(f"source                           {dict(collections.Counter(r['source'] for r in rows))}")
print(f"freshness                        {dict(collections.Counter(r['freshness'] for r in rows))}")
for verb in ("ask_ms", "answer_ms"):
    slow = sorted(rows, key=lambda r: -r[verb])[:3]
    print(f"slowest {verb:<10}          (S5) " + " · ".join(f"{r['id']} {r[verb]:.0f}" for r in slow))
