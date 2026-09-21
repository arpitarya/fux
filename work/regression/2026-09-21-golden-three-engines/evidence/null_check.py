#!/usr/bin/env python3
"""The null control's verdict: v1 against itself must move ZERO rows."""
import json
from pathlib import Path
EV = Path("/Users/arpitarya/my_programs/fux/work/regression/2026-09-21-golden-three-engines/evidence")
total = moved = 0
detail = []
for n in (1, 2, 3):
    a = {r["id"]: r for r in map(json.loads, (EV/"null-a"/f"handoff-set-{n}.jsonl").read_text().splitlines()) }
    b = {r["id"]: r for r in map(json.loads, (EV/"null-b"/f"handoff-set-{n}.jsonl").read_text().splitlines()) }
    for i in sorted(a):
        total += 1
        # Compare only what the ENGINE decided. `ask_ms`/`answer_ms` are wall
        # clock and `arm` is the label; neither is a result, and including them
        # would make the control fail on a busy machine.
        ka = (a[i]["ranked"], a[i]["answer_text"], a[i]["citations"], a[i]["band"], a[i]["answerable"])
        kb = (b[i]["ranked"], b[i]["answer_text"], b[i]["citations"], b[i]["band"], b[i]["answerable"])
        if ka != kb:
            moved += 1
            detail.append((n, i))
print(f"NULL CONTROL: {total} rows compared, {moved} moved")
for n, i in detail[:10]:
    print(f"  set {n} {i}")
print("PASS — the harness is not the variable" if moved == 0 else "🔴 FAIL — nothing else may be measured")
