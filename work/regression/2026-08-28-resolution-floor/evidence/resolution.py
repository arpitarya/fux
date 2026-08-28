#!/usr/bin/env python3
"""What delta on a 50-query set is distinguishable from chance?

**Replaces a placeholder.** `CLAUDE.md` §Conformance runs says, and says it is a
placeholder: *"provisionally — and this is a placeholder for a measurement, not
a measurement — nothing under ±2 queries (4 pp) on a 50-query set counts."*
**Every "no detected change" ruling this project has filed rests on that
number.**

## Why this is arithmetic and not a run

Two arms graded on the **same** queries is a **paired** comparison, so the
queries both arms agree on carry no information about which is better — only the
ones that **flip** do. That is McNemar's test, and for a binary outcome it
reduces to an exact binomial on the discordant pairs.

**So the answer does not depend on the corpus, the engine, or who authored
anything.** It depends on how many queries flipped. No model, no network, pure
stdlib — L1, L3 and L4 are not in play.

## What it computes

For each plausible number of discordant pairs `n_d`, the smallest **net**
difference `|b - c|` whose two-sided exact binomial p-value clears `alpha`.

⚠ **This is a floor on DETECTABILITY, never a licence.** Clearing it means a
delta is unlikely to be chance. It does **not** make the delta generalise: 50
queries over 10 documents is three orders of magnitude below the design point,
and `CLAUDE.md` §Litmus governs that separately.

    python3 tools/quality-controls/resolution.py [alpha]
"""

from __future__ import annotations

import sys
from math import comb


def two_sided_p(b: int, n_d: int) -> float:
    """Exact two-sided binomial p for `b` of `n_d` flips going one way, p=0.5."""
    if n_d == 0:
        return 1.0
    total = 2 ** n_d
    observed = comb(n_d, b) / total
    # Sum every outcome at least as extreme as the observed one — the exact
    # test, not a normal approximation, because n_d is small by construction.
    return min(1.0, sum(comb(n_d, k) / total for k in range(n_d + 1)
                        if comb(n_d, k) / total <= observed + 1e-15))


def smallest_detectable(n_d: int, alpha: float) -> int | None:
    """Smallest net |b - c| that clears `alpha`, or `None` if none does."""
    for net in range(1, n_d + 1):
        if (n_d + net) % 2:
            continue  # b - c and b + c share a parity
        b = (n_d + net) // 2
        if two_sided_p(b, n_d) <= alpha:
            return net
    return None


def main(argv: list[str]) -> int:
    alpha = float(argv[0]) if argv else 0.05
    print(f"Paired (McNemar) exact binomial, two-sided, alpha = {alpha}\n")
    print(f"{'discordant':>11}{'net needed':>12}{'as queries':>12}   note")
    for n_d in (2, 4, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50):
        net = smallest_detectable(n_d, alpha)
        if net is None:
            print(f"{n_d:>11}{'--':>12}{'--':>12}   no net difference can clear alpha")
        else:
            note = "" if n_d > 6 else "so few flips that only a near-total split counts"
            print(f"{n_d:>11}{net:>12}{net:>12}   {note}")
    print(
        "\n`discordant` = queries where the two arms DISAGREE. Queries both arms"
        "\nget right, or both get wrong, carry no information in a paired test."
        "\n\n⚠ The floor is a function of the FLIPS, not of the set size. A '±2 on 50'"
        "\nrule of thumb is only right when about 5 queries flipped; at 20 flips it"
        "\nis far too loose, and at 4 flips it is too strict."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
