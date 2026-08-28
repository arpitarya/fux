"""Power for the contested design, computed BEFORE any corpus exists.

Uses only the exact test the harness uses. Nothing here reads a run.
"""
import random
from math import comb

def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2.0 * sum(comb(n, i) for i in range(k + 1)) / (2 ** n))

def power(n, pb, pc, trials=20000, alpha=0.05, seed=11):
    rng = random.Random(seed)
    hit = 0
    for _ in range(trials):
        b = c = 0
        for _ in range(n):
            u = rng.random()
            if u < pb: b += 1
            elif u < pb + pc: c += 1
        if b > c and mcnemar_exact(b, c) < alpha:
            hit += 1
    return hit / trials

print("Power, exact two-sided McNemar, alpha=0.05, 20k sims")
print(f"{'N':>5} | {'.06/.02':>8} {'.10/.03':>8} {'.15/.05':>8} {'.25/.05':>8} {'.40/.05':>8}")
print("-" * 56)
for n in (50, 100, 120, 150, 200):
    cells = " ".join(f"{power(n, pb, pc):8.2f}" for pb, pc in
                     [(.06,.02), (.10,.03), (.15,.05), (.25,.05), (.40,.05)])
    print(f"{n:>5} | {cells}")

print()
print("Resolution floor (the bar the SET SIZE cannot change):")
for net in range(1, 8):
    print(f"  net {net}: best achievable two-sided p = {mcnemar_exact(net, 0):.4f}"
          + ("   <- clears 0.05" if mcnemar_exact(net, 0) < 0.05 else ""))
