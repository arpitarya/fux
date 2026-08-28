"""Render the frozen bins from `per-query.json`. No fux call, no re-measure.

Split out from `harness.py` deliberately: re-running the harness against a
DIFFERENT index silently produces a different table under the same filename,
which is exactly what happened once while filing this run.
"""
import json, sys
from pathlib import Path

T, NBINS = 0.75, 10
rows = json.loads(Path(sys.argv[1] if len(sys.argv) > 1 else "per-query.json").read_text())

bins = [[] for _ in range(NBINS)]
for r in rows:
    s = min(max(r["separation"], 0.0), 1.0)
    bins[NBINS - 1 if s >= 1.0 else int(s * NBINS)].append(r)

print(f"n = {len(rows)} goldens, {sum(r['correct'] for r in rows)} correct\n")
print(f"{'bin':<14}{'n':>4}{'correct':>9}{'P(correct)':>12}   note")
rates = []
for i, b in enumerate(bins):
    lo, hi = i / NBINS, (i + 1) / NBINS
    n, c = len(b), sum(r["correct"] for r in b)
    rate = (c / n) if n else None
    rates.append((lo, n, c, rate))
    note = "" if n else "empty bin"
    if n and n < 5:
        note = f"n={n}: interval far wider than +/-0.4"
    print(f"[{lo:.1f},{hi:.1f})   {n:>4}{c:>9}{(f'{rate:.2f}' if rate is not None else '--'):>12}   {note}")

ones = [r for r in rows if r["separation"] >= 1.0]
print(f"\nseparation == 1.0 (structural: exactly one document scored): "
      f"n={len(ones)}, correct={sum(r['correct'] for r in ones)}")

floor = None
for i, (lo, n, c, rate) in enumerate(rates):
    if rate is not None and rate >= T and all(rt is None or rt >= T for _, _, _, rt in rates[i:]):
        floor = lo
        break
print(f"\nlowest bin reaching P(correct) >= {T} AND staying >= it for every higher bin: "
      f"{'none' if floor is None else f'{floor:.1f}'}")
occupied = [rt for _, n, _, rt in rates if n]
print(f"any bin reaches {T}: {any(rt >= T for rt in occupied)}   "
      f"every OCCUPIED bin exceeds {T}: {all(rt >= T for rt in occupied)}")
print(f"monotone non-decreasing across occupied bins: "
      f"{all(a <= b for a, b in zip(occupied, occupied[1:]))}")
