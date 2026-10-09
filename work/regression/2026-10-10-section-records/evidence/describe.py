#!/usr/bin/env python3
"""Descriptive only — what each arm MOVED against sw-0.0, never whether it improved.

Reads the five hand-offs (ids, ranked lists, bands, latencies). No key, no score.

    python3 describe.py > describe.json
"""
import json
import statistics
from pathlib import Path

EV = Path(__file__).resolve().parent
ARMS = ("sw-0.0", "sw-0.1", "sw-0.25", "sw-0.5", "sw-1.0")


def load(arm):
    path = EV / arm / "rung-01000" / "handoff-set-5-claude.jsonl"
    return {r["id"]: r for r in map(json.loads, path.read_text().splitlines()) if r}


base = load("sw-0.0")
out = {}
for arm in ARMS:
    rows = load(arm)
    assert set(rows) == set(base)
    bands = {}
    for r in rows.values():
        bands[r["band"]] = bands.get(r["band"], 0) + 1
    out[arm] = {
        "rank1_changed": sum(rows[i]["ranked"][:1] != base[i]["ranked"][:1] for i in rows),
        "order_changed": sum(rows[i]["ranked"] != base[i]["ranked"] for i in rows),
        "membership_changed": sum(set(rows[i]["ranked"]) != set(base[i]["ranked"]) for i in rows),
        "answer_text_changed": sum(rows[i]["answer_text"] != base[i]["answer_text"] for i in rows),
        "bands": dict(sorted(bands.items())),
        "median_ask_ms": statistics.median(r["ask_ms"] for r in rows.values()),
        "max_ask_ms": max(r["ask_ms"] for r in rows.values()),
    }
print(json.dumps(out, indent=1))
