#!/usr/bin/env python3
"""One paired-comparison verdict, computed the same way by every control.

**Why this is a module and not four copies of an `if`.** Three instruments
landed on 2026-09-12 and each was about to hard-code *"net >= 6"*.
[SR-RS](../../records/0133_predictions.md) decision 19 says that is the
**floor of all floors** — the bar a result must clear *before the discordant
count is even known* — and that the real bar **rises with the flips**: 20 flips
need a net of 10, 50 flips need 16. A tool comparing against 6 alone would pass
a net of 8 on 30 discordant pairs, which decision 19's own table refuses.

So the verdict is the **exact two-sided binomial p-value on the discordant
pairs**, which is what that table is computed from. `resolution.py` already had
the arithmetic; this is the seam that applies it, not a second implementation.

⚠ **Clearing this is DETECTABILITY, never generalisation** — decision 19's last
bullet, and `CLAUDE.md` §Litmus governs the second question separately.
"""

from __future__ import annotations

from resolution import smallest_detectable, two_sided_p

#: Conventional and stated, not derived (SR-RS decision 19).
ALPHA = 0.05

#: The bar that applies with no discordant count in hand. Nets of 1-5 cannot
#: clear ALPHA at any count, verified by exhausting every split up to n = 50.
FLOOR_OF_ALL_FLOORS = 6


def rule(b: int, c: int, *, better: str = "b", worse: str = "c") -> dict:
    """`b` favours one arm, `c` the other. Returns the adjudication.

    `discordant == 0` is **Inconclusive** (decision 22d) and never *"no detected
    change"* — a null measured where nothing could move is the absence of a
    measurement.
    """
    discordant, net = b + c, abs(b - c)
    p = two_sided_p(max(b, c), discordant) if discordant else 1.0
    needed = smallest_detectable(discordant, ALPHA) if discordant else None
    if discordant == 0:
        outcome = "inconclusive"
    elif p <= ALPHA:
        outcome = better if b > c else worse
    else:
        outcome = "no detected change"
    return {"b": b, "c": c, "discordant": discordant, "net": net,
            "p": round(p, 6), "net_needed": needed, "alpha": ALPHA,
            "outcome": outcome}


def line(v: dict) -> str:
    """One line a report can quote verbatim."""
    need = ("no net difference can clear alpha at this count"
            if v["net_needed"] is None else f"net needed {v['net_needed']}")
    return (f"b={v['b']} c={v['c']} discordant={v['discordant']} net={v['net']} "
            f"p={v['p']:.4f} ({need}, alpha={v['alpha']}) -> {v['outcome'].upper()}")
