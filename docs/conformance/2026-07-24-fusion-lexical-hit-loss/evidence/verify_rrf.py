#!/usr/bin/env python3
"""Independently reconcile reported RRF scores against the specified formula.

RRF(d) = sum over lists of 1/(k + rank). Three lists fuse in the hybrid path:
bm25f, dense, dense_global. If the reported score matches the recomputed one for
every result, the fusion code is doing exactly what it is specified to do — and
"non-monotone fusion" cannot be the explanation for any demotion.
"""
import json
import subprocess
import sys
from pathlib import Path

WS = Path.home() / 'my_programs/fux-lab/orbit/corpus'
FUX = str(Path.home() / 'my_programs/fux-lab/orbit/.venv/bin/fux')
K = 60

QUERIES = [
    "How is inventory accuracy verified without shutting the warehouse?",
    "How do we make sure a picker is not routed to an empty location?",
    "What is the same-day dispatch order cutoff time?",
    "Why are frequently ordered products stored near the shipping dock?",
]

total = mismatch = 0
worst = 0.0
for q in QUERIES:
    out = subprocess.run([FUX, 'ask', q, '--json', '--top', '40'],
                         cwd=WS, capture_output=True, text=True, timeout=600).stdout
    for r in json.loads(out)['results']:
        h = r.get('hybrid') or {}
        if 'rrf' not in h:
            continue
        # A superseded doc contributes 1/(k + rank + penalty) in EVERY list it
        # appears in (ADR 0015). Omitting this term is what made the first pass
        # of this script report a false mismatch.
        offset = h.get('supersession_penalty', 0) or 0
        recomputed = 0.0
        for key in ('bm25f_rank', 'dense_rank', 'dense_global_rank'):
            rank = h.get(key)
            if rank:
                recomputed += 1.0 / (K + rank + offset)
        total += 1
        delta = abs(round(recomputed, 5) - h['rrf'])
        worst = max(worst, delta)
        if delta > 1e-5:
            mismatch += 1
            print(f'  MISMATCH {r["path"]}: reported {h["rrf"]} vs recomputed '
                  f'{round(recomputed,5)}  ({h})')

print(f'checked {total} fused results across {len(QUERIES)} queries')
print(f'mismatches: {mismatch}   worst delta: {worst:.8f}')
print('VERDICT:', 'RECONCILES — fusion matches its specification'
      if mismatch == 0 else 'DOES NOT RECONCILE — pre-work is wrong, stop')
sys.exit(1 if mismatch else 0)
