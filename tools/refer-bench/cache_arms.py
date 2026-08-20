"""ARC vs LRU hit-rate, against the cache compare doc's own reopen-trigger.

[`work/compare/cache-policy.compare.md`](../../work/compare/cache-policy.compare.md)
chose ARC over LRU and wrote its own condition for reversing that:

> *measured hit-rate shows no advantage over LRU on real Fux workloads (then
> take the simpler code).*

Nothing had measured it. This does — and states plainly what it can and cannot
settle.

## What is measured, and what "advantage" means here

Both policies get **the same byte budget** and **the same request sequence**,
and the number reported is hit rate: `hits / (hits + misses)`. A cache miss in
this plane is a **network fetch**, not a page fault, so a point of hit rate is
worth far more than it would be in a page cache — but the comparison itself is
just two counters over one trace.

**Advantage is pre-declared as ≥ 2 percentage points on the scan workload.**
Below that, ARC's extra machinery — four lists, two ghost lists, an adaptation
parameter — is not buying anything a reader of the code would guess it buys,
and the compare doc's trigger fires. This number is fixed here, before the run.

## The workloads, and why the second one is the whole argument

| workload | shape | what it tests |
|---|---|---|
| `hot` | a small working set, requested repeatedly, uniform | does either policy do the obvious thing? |
| `scan` | the same hot set, **interrupted by one pass over every document** | ARC's entire claim |

The `scan` workload is the one ARC was chosen for. The compare doc's argument
was that *"the maintenance operations this engine runs — a hook re-indexing
after a large merge — are exactly the bulk scans that flush an LRU's hot set."*
A bulk pass evicts the hot set from an LRU and leaves it in place for an ARC,
so if ARC has an advantage anywhere it is here, and if it does not have one
here it does not have one.

## The honest limit

**These are synthetic traces, not real Fux workloads.** The compare doc's
trigger says *real*; nobody has a production access log for this engine because
nothing is in production. So this run can **fire** the trigger (no advantage
even on the workload ARC was picked for is strong evidence) but it cannot
**clear** it: an advantage here means ARC behaves as advertised on the shape
its argument named, not that the shape occurs.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from fux.refer.arc import ARC  # noqa: E402

#: Pre-declared before the run: below this, the compare doc's trigger fires.
ADVANTAGE_PTS = 2.0


class LRU:
    """Plain LRU over the same interface, bounded by the same byte budget.

    Deliberately the simplest thing that could work — that is the point of the
    comparison. Recency is `OrderedDict` order, never a timestamp, matching the
    v0.26 lean profile's monotonic-counter rule that ARC inherited.
    """

    def __init__(self, max_bytes: int) -> None:
        self.max_bytes = max_bytes
        self.store: OrderedDict[tuple[str, str], bytes] = OrderedDict()
        self.live = 0
        self.hits = 0
        self.misses = 0

    def get(self, key):
        if key in self.store:
            self.store.move_to_end(key)
            self.hits += 1
            return self.store[key]
        self.misses += 1
        return None

    def put(self, key, value: bytes) -> None:
        if key in self.store:
            self.live -= len(self.store.pop(key))
        if len(value) > self.max_bytes:
            return
        while self.live + len(value) > self.max_bytes and self.store:
            self.live -= len(self.store.popitem(last=False)[1])
        self.store[key] = value
        self.live += len(value)


def _trace(kind: str, docs: int, hot: int, rounds: int) -> list[tuple[int, bool]]:
    """A deterministic request sequence of `(doc, is_hot_request)`.

    No randomness: the same trace every run, on every machine.

    **The flag is load-bearing.** A first version returned bare document ids and
    scored hit rate over the whole trace — and the bulk pass is 76 % of the
    requests and a guaranteed miss for both policies, so it drowned the very
    difference the workload exists to expose (ARC +0.91 pts, which reads as "no
    advantage" and is really "the metric could not see one"). Both numbers are
    reported below; the **hot-request** one is what a user experiences, because
    nobody is waiting on the re-index pass.
    """
    sequence: list[tuple[int, bool]] = []
    for r in range(rounds):
        # The hot set, walked repeatedly — the steady state of an agent asking
        # follow-up questions about the same few runbooks.
        for _ in range(4):
            sequence.extend((d, True) for d in range(hot))
        if kind == "scan" and r % 2 == 1:
            # The bulk pass: every document once. This is the hook re-indexing
            # after a large merge, and it is what an LRU cannot survive.
            sequence.extend((d, False) for d in range(docs))
    return sequence


def run_policy(policy, trace, payload: dict[int, bytes]) -> tuple[float, float]:
    """`(overall_hit_rate, hot_request_hit_rate)`, both as percentages."""
    hot_hits = hot_total = 0
    for doc, is_hot in trace:
        key = (f"http://example/doc-{doc}", f"sha-{doc}")
        hit = policy.get(key) is not None
        if not hit:
            policy.put(key, payload[doc])
        if is_hot:
            hot_total += 1
            hot_hits += hit
    total = policy.hits + policy.misses
    return (
        100.0 * policy.hits / total if total else 0.0,
        100.0 * hot_hits / hot_total if hot_total else 0.0,
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--docs", type=int, default=500)
    parser.add_argument("--hot", type=int, default=20)
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--doc-bytes", type=int, default=8 * 1024)
    args = parser.parse_args(argv)

    payload = {i: bytes(args.doc_bytes) for i in range(args.docs)}
    # A budget that holds the hot set comfortably and the corpus nowhere near —
    # the only regime in which a replacement policy matters at all.
    budget = args.doc_bytes * (args.hot * 2)

    rows = []
    for kind in ("hot", "scan"):
        trace = _trace(kind, args.docs, args.hot, args.rounds)
        arc_all, arc_hot = run_policy(ARC(budget), trace, payload)
        lru_all, lru_hot = run_policy(LRU(budget), trace, payload)
        row = {
            "workload": kind,
            "requests": len(trace),
            "hot_requests": sum(1 for _, is_hot in trace if is_hot),
            "arc_hit_rate_pct": round(arc_all, 2),
            "lru_hit_rate_pct": round(lru_all, 2),
            "advantage_pts": round(arc_all - lru_all, 2),
            "arc_hot_hit_rate_pct": round(arc_hot, 2),
            "lru_hot_hit_rate_pct": round(lru_hot, 2),
            "hot_advantage_pts": round(arc_hot - lru_hot, 2),
        }
        rows.append(row)
        print(
            f"  {kind:<5}: overall ARC {arc_all:6.2f}% / LRU {lru_all:6.2f}% "
            f"({arc_all - lru_all:+.2f} pts)   |   hot-request ARC {arc_hot:6.2f}% / "
            f"LRU {lru_hot:6.2f}% ({arc_hot - lru_hot:+.2f} pts)"
        )

    scan = next(r for r in rows if r["workload"] == "scan")
    # Read against the hot-request metric, and the reason is stated rather than
    # assumed: the trigger is about what the cache does for a *caller*, and no
    # caller is waiting on the bulk re-index pass.
    fires = scan["hot_advantage_pts"] < ADVANTAGE_PTS
    report = {
        "budget_bytes": budget,
        "docs": args.docs,
        "hot_set": args.hot,
        "advantage_threshold_pts": ADVANTAGE_PTS,
        "advantage_read_from": "hot_advantage_pts on the scan workload",
        "workloads": rows,
        "compare_doc_trigger": (
            "FIRES — no advantage on the workload ARC was chosen for; "
            "cache-policy.compare.md says take the simpler code"
            if fires
            else "does not fire — ARC behaves as advertised on the scan workload it was "
            "chosen for. Note the limit: this is a synthetic trace, so it cannot CLEAR "
            "a trigger whose wording says 'real Fux workloads'"
        ),
    }
    print(f"  trigger: {report['compare_doc_trigger']}")
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "cache-arms.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    else:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
