#!/usr/bin/env python3
"""The paired comparison for W-205 part 2 — flips, net, and the floor it must clear.

🔴 **It prints the rule and does NOT apply it.** The floor lives in the frozen
[PRE-REGISTRATION](../PRE-REGISTRATION.md) and in
[SR-RS](../../../../records/0133_predictions.md) decision 19; a harness that also
encoded it would be a second copy of a threshold that may not move.

**Paired, per rung.** Queries both arms agree on carry no information; only the
ones that **flip** do. That is McNemar's test, an exact binomial on the
discordant pairs — arithmetic, with no corpus in it to have been contaminated by.

**The endpoint is `rank_primary_bare` at `hit@1`**, per the pre-registration, and
the question form is printed beside it and never averaged with it.

🔴 **Headroom first** (decision 22): the before-arm's misses are the headroom for
the improving direction and its hits are the headroom for the degrading one.
Both are printed **before** any net, because a net quoted without them is a
number whose ceiling nobody stated.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

#: SR-RS decision 19, quoted so the reader does not have to look it up. NOT applied.
FLOOR = {2: None, 4: None, 6: 6, 8: 8, 10: 8, 12: 8, 15: 9, 20: 10, 30: 12, 50: 16}


def needed(discordant: int) -> str:
    if discordant <= 5:
        return "IMPOSSIBLE — no split clears alpha at this discordant count"
    for k in sorted(FLOOR):
        if discordant <= k and FLOOR[k]:
            return f"net >= {FLOOR[k]}"
    return "net >= 16"


def load(p: Path) -> dict[str, dict]:
    return {r["id"]: r for r in json.loads(p.read_text(encoding="utf-8"))["rows"]}


def hit1(row: dict, key: str) -> bool:
    return row.get(key) == 1


def compare(before: dict, after: dict, key: str) -> dict:
    ids = sorted(before.keys() & after.keys())
    fixed = [i for i in ids if not hit1(before[i], key) and hit1(after[i], key)]
    broke = [i for i in ids if hit1(before[i], key) and not hit1(after[i], key)]
    return {
        "n": len(ids),
        "before_hits": sum(1 for i in ids if hit1(before[i], key)),
        "after_hits": sum(1 for i in ids if hit1(after[i], key)),
        "fixed": fixed,
        "broke": broke,
        "discordant": len(fixed) + len(broke),
        "net": len(fixed) - len(broke),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--before", type=Path, required=True)
    ap.add_argument("--after", type=Path, required=True)
    ap.add_argument("--rung", required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)

    b, a = load(args.before), load(args.after)
    report = {"rung": args.rung}
    for label, key in (("bare (ENDPOINT)", "rank_primary_bare"),
                       ("question (reported, never averaged)", "rank_primary_question")):
        r = compare(b, a, key)
        report[key] = r
        miss = r["n"] - r["before_hits"]
        print(f"\n--- {args.rung} · {label} ---")
        print(f"  HEADROOM (decision 22): improving {miss} of {r['n']} "
              f"(before-arm misses) · degrading {r['before_hits']} of {r['n']} (before-arm hits)")
        print(f"  before hit@1 {r['before_hits']}/{r['n']}   after hit@1 {r['after_hits']}/{r['n']}")
        print(f"  fixed {len(r['fixed'])}  broke {len(r['broke'])}  "
              f"discordant {r['discordant']}  NET {r['net']:+d}")
        print(f"  the rule (NOT applied here): at {r['discordant']} discordant, {needed(r['discordant'])}")
        if r["fixed"]:
            print(f"  fixed:  {', '.join(b[i]['identifier'] for i in r['fixed'])}")
        if r["broke"]:
            print(f"  broke:  {', '.join(b[i]['identifier'] for i in r['broke'])}")

    # per family, because the sibling families are the population the change acts on
    fams = sorted({b[i].get("family", "") for i in b})
    print(f"\n--- {args.rung} · by family, bare endpoint ---")
    byfam = {}
    for f in fams:
        ids = [i for i in b.keys() & a.keys() if b[i].get("family") == f]
        fx = [i for i in ids if not hit1(b[i], "rank_primary_bare") and hit1(a[i], "rank_primary_bare")]
        bk = [i for i in ids if hit1(b[i], "rank_primary_bare") and not hit1(a[i], "rank_primary_bare")]
        byfam[f] = {"n": len(ids), "fixed": len(fx), "broke": len(bk), "net": len(fx) - len(bk)}
        print(f"  {f:18} n={len(ids):>2}  fixed {len(fx)}  broke {len(bk)}  net {len(fx)-len(bk):+d}")
    report["by_family"] = byfam

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=1, sort_keys=True), encoding="utf-8")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
