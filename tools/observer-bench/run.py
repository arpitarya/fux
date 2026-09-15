"""W-181 — what does the observer hook cost, and whose cost is it?

**The question the keep/remove call needs answered** is p50 `ask` with no
observer against p50 `ask` with one. `.fux/observers/` shipped on 2026-09-15
([SR-OBSERVE](../../records/0157_observe.md)) with the byte-identity half
discharged by a hostile test and this half unfiled, because W-170 said it needed
*a real subscriber's observer* — a wait nothing in fux could ever clear.

## The fork, resolved

| | what it is | what it costs |
|---|---|---|
| **a reference observer in fux** ← **chosen** | `reference_observer.py`: append a line, return | available now, and 🔴 **its realism is an assertion** — it prices the SEAM, never a subscriber's work |
| cage's real observer | `cage setup` drops it; it writes cage's ledger | the honest subscriber number, and **not fux's to write** |

**Both, in that order.** The seam's cost is fux's to know today; cage's number
is the reopen trigger. ⚠ **What must not happen is this number being reported as
a subscriber's**, which is why the verdict names which observer it priced and
why the reference observer's own docstring opens with the same warning.

## How it measures

- **One process per query.** Cold start included, because that is what a
  consumer pays and because the hook runs once per process by design
  (SR-OBSERVE decision 10d: one process runs one verb).
- **Interleaved `off on off on`**, never blocked: thermal drift hands the second
  arm a different machine.
- **The median of each query's repeats**, then p50 and p95 **of those medians**.
  Never a mean — one scheduler hiccup owns it.
- **Per-query rows**, so every aggregate anybody computes later comes out of
  them (SR-RS decision 22e).

Usage::

    python tools/observer-bench/run.py --root . --queries 40 --repeats 5 \\
        --json-out rows.json
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools" / "differential"))

OBSERVER_NAME = "w181_reference.py"
SLOW_NAME = "w181_slow.py"


def queries_for(root: Path, count: int) -> list[str]:
    """A deterministic set drawn from the corpus's own vocabulary.

    Reuses the differential harness's generator rather than inventing one: it is
    corpus-derived by a fixed rule and cannot be curated toward a friendly
    latency profile. **Only the systematic bands are used** — the adversarial
    literals tokenize to nothing and would time an early return.
    """
    from queryset import generate

    everything = generate(root, common=count, median=count, rare=count, pairs=0, triples=0)
    usable = [q for q in everything if q and len(q) > 2 and not q.isspace()]
    return usable[:count]


def timed(root: Path, query: str, env: dict) -> float:
    """Milliseconds for one `fux ask`, as a consumer pays it — process included."""
    start = time.perf_counter()
    subprocess.run(
        [sys.executable, "-m", "fux.cli", "ask", query, "--json"],
        cwd=root, capture_output=True, text=True, env=env,
    )
    return (time.perf_counter() - start) * 1000.0


def install(root: Path, log: Path) -> None:
    """Copy the observer in. ⚠ **The log is NOT truncated here.**

    It is emptied once, before the sweep. Truncating per install would leave one
    record at the end and the *did every `on` run actually fire* check — the one
    thing standing between this number and a delta that prices an absent
    observer — would pass on a single line.
    """
    target = root / ".fux" / "observers" / OBSERVER_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "tools" / "observer-bench" / "reference_observer.py", target)


def install_slow(root: Path) -> None:
    target = root / ".fux" / "observers" / SLOW_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "tools" / "observer-bench" / "slow_observer.py", target)


def remove(root: Path) -> None:
    (root / ".fux" / "observers" / OBSERVER_NAME).unlink(missing_ok=True)
    (root / ".fux" / "observers" / SLOW_NAME).unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--queries", type=int, default=40)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--warmups", type=int, default=2, help="kept and marked, never dropped")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--label", default="")
    parser.add_argument(
        "--cap-arm",
        type=float,
        default=0.0,
        help="also run a third arm with an observer that sleeps this many ms "
        "(SR-OBSERVE decision 10b: the cap ABANDONS, so what is measured is that "
        "`ask` returns at about off + max_ms rather than off + sleep)",
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    log = root / ".fux" / "runtime" / "w181-observer.log"
    log.parent.mkdir(parents=True, exist_ok=True)

    queries = queries_for(root, args.queries)
    if not queries:
        print("no queries could be generated from this corpus", file=sys.stderr)
        return 2
    print(f"corpus: {root}   queries: {len(queries)}   repeats: {args.repeats}")

    base_env = dict(os.environ, FUX_REFERENCE_OBSERVER_LOG=str(log))
    log.write_text("", encoding="utf-8")  # once, before the sweep — see `install`
    rows: list[dict] = []

    remove(root)
    for i in range(args.warmups):
        timed(root, queries[0], base_env)
        rows.append({"query": queries[0], "arm": "warmup", "repeat": i, "ms": None})

    for query in queries:
        for repeat in range(args.repeats):
            # Interleaved within the repeat, so a drifting machine moves both.
            remove(root)
            off = timed(root, query, base_env)
            install(root, log)
            on = timed(root, query, base_env)
            remove(root)
            rows.append({"query": query, "arm": "off", "repeat": repeat, "ms": off})
            rows.append({"query": query, "arm": "on", "repeat": repeat, "ms": on})

    fired = sum(1 for _ in log.open(encoding="utf-8")) if log.is_file() else 0
    remove(root)

    slow_log = root / ".fux" / "runtime" / "w181-slow.log"
    slow_fired = 0
    if args.cap_arm:
        slow_log.write_text("", encoding="utf-8")
        slow_env = dict(
            base_env,
            FUX_SLOW_OBSERVER_MS=str(args.cap_arm),
            FUX_SLOW_OBSERVER_LOG=str(slow_log),
        )
        for query in queries:
            for repeat in range(args.repeats):
                install_slow(root)
                ms = timed(root, query, slow_env)
                remove(root)
                rows.append({"query": query, "arm": "slow", "repeat": repeat, "ms": ms})
        # The thread may still be sleeping when the process exits, which is
        # exactly what "abandoned" means — so a short grace before counting.
        time.sleep(args.cap_arm / 1000.0 + 0.5)
        slow_fired = sum(1 for _ in slow_log.open(encoding="utf-8")) if slow_log.is_file() else 0

    def percentiles(arm: str) -> tuple[float, float]:
        per_query = []
        for query in queries:
            samples = [r["ms"] for r in rows if r["query"] == query and r["arm"] == arm]
            if samples:
                per_query.append(statistics.median(samples))
        per_query.sort()
        if not per_query:
            return 0.0, 0.0
        p50 = statistics.median(per_query)
        p95 = per_query[min(len(per_query) - 1, int(round(0.95 * (len(per_query) - 1))))]
        return p50, p95

    off_p50, off_p95 = percentiles("off")
    on_p50, on_p95 = percentiles("on")

    print(f"\n{args.label or root.name}")
    print(f"  off  p50 {off_p50:8.1f} ms   p95 {off_p95:8.1f} ms")
    print(f"  on   p50 {on_p50:8.1f} ms   p95 {on_p95:8.1f} ms")
    print(f"  delta p50 {on_p50 - off_p50:+8.1f} ms   p95 {on_p95 - off_p95:+8.1f} ms")
    print(f"  observer records written: {fired} (expected {len(queries) * args.repeats})")
    if fired != len(queries) * args.repeats:
        print("  ⚠ THE OBSERVER DID NOT FIRE ON EVERY `on` RUN — the delta prices nothing")

    if args.cap_arm:
        slow_p50, slow_p95 = percentiles("slow")
        print(f"  slow p50 {slow_p50:8.1f} ms   p95 {slow_p95:8.1f} ms "
              f"(observer sleeps {args.cap_arm:.0f} ms)")
        print(f"  delta vs off: p50 {slow_p50 - off_p50:+8.1f} ms "
              f"-- the cap holds if this is about `[observe] max_ms`, not {args.cap_arm:.0f}")
        print(f"  slow observer records written: {slow_fired} "
              f"(of {len(queries) * args.repeats}) -- how many ABANDONED threads finished anyway")

    if args.json_out:
        args.json_out.write_text(
            json.dumps(
                {
                    "root": str(root),
                    "label": args.label,
                    "queries": len(queries),
                    "repeats": args.repeats,
                    "off_p50_ms": round(off_p50, 2),
                    "off_p95_ms": round(off_p95, 2),
                    "on_p50_ms": round(on_p50, 2),
                    "on_p95_ms": round(on_p95, 2),
                    "records_written": fired,
                    "cap_arm_sleep_ms": args.cap_arm or None,
                    "slow_p50_ms": round(percentiles("slow")[0], 2) if args.cap_arm else None,
                    "slow_p95_ms": round(percentiles("slow")[1], 2) if args.cap_arm else None,
                    "slow_records_written": slow_fired if args.cap_arm else None,
                    "rows": rows,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
