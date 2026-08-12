"""R3 — warm `ask` latency on the RFC corpus, worst-case terms reported apart.

**The pre-registered threshold: warm `ask` <= 150 ms, including worst-case
common terms.** That clause is the whole point. An average over easy queries
is not R3, and reporting one as R3 would be the exact law-3 violation this
repo's own pruning gate exists to remember — M1 recorded a zero delta over a
population the treatment never touched, and the lesson was *always report the
fraction of the population a treatment actually reaches*.

So this bench reports three populations separately and never blends them:

1. **worst** — the highest-`df` terms in the corpus. This is B4's trap: the
   posting lists that make a naive scan quadratic. R3 is judged here.
2. **typical** — mid-band `df`, the queries a user actually types.
3. **multi** — realistic multi-term questions, where the rarest term seeds and
   the common ones are candidates for skipping.

Latency is reported as median and p95 over repeated runs after a warm-up, with
scan and both accelerator modes side by side, so the speedup is attributable
rather than asserted.

Usage:
    python tools/differential/bench_r3.py --root ~/my_programs/fux-lab/2026-08-12-m2-r3
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from fux.derive import accel  # noqa: E402
from fux.derive import format as fmt  # noqa: E402
from fux.query import scan  # noqa: E402

#: The pre-registered bar. Do not edit this constant to make a run pass.
R3_BUDGET_MS = 150.0


@dataclass
class Timing:
    label: str
    queries: int
    median_ms: float
    p95_ms: float
    max_ms: float
    slowest_query: str

    def verdict(self) -> str:
        return "PASS" if self.p95_ms <= R3_BUDGET_MS else "FAIL"


def corpus_terms(root: Path) -> list[tuple[str, int]]:
    """Every indexed term with its df, read from the offset table alone."""
    out: list[tuple[str, int]] = []
    for path in sorted((fmt.runtime_dir(root) / fmt.POSTINGS_DIR).glob("*.idx")):
        buf = path.read_bytes()
        counts: dict[bytes, int] = {}
        for i in range(len(buf) // fmt.ENTRY_SIZE):
            raw = fmt.unpack_entry(buf, i)
            counts[raw[0]] = counts.get(raw[0], 0) + raw[8]
        out.extend((term.hex(), df) for term, df in counts.items())
    out.sort(key=lambda kv: (-kv[1], kv[0]))
    return out


def source_vocabulary(root: Path) -> list[tuple[str, int]]:
    """Plaintext terms with df, from the sources — hashes are not queryable."""
    from fux.config import load
    from fux.ingest.gitdir import walk_sources
    from fux.query.tokenize import tokenize

    config = load(root)
    walked, _ = walk_sources(root, config.source_dirs)
    df: dict[str, int] = {}
    for f in walked:
        for term in set(tokenize(f.content.decode("utf-8", errors="replace"))):
            df[term] = df.get(term, 0) + 1
    return sorted(df.items(), key=lambda kv: (-kv[1], kv[0]))


def time_queries(fn, queries: list[str], label: str, repeats: int = 3) -> Timing:
    per_query: list[tuple[float, str]] = []
    for query in queries:
        fn(query)  # warm-up: caches, imports, page-ins
        samples = []
        for _ in range(repeats):
            t0 = time.perf_counter()
            fn(query)
            samples.append((time.perf_counter() - t0) * 1000)
        per_query.append((statistics.median(samples), query))

    times = sorted(t for t, _ in per_query)
    slowest = max(per_query)
    return Timing(
        label=label,
        queries=len(queries),
        median_ms=statistics.median(times),
        p95_ms=times[min(len(times) - 1, int(len(times) * 0.95))],
        max_ms=slowest[0],
        slowest_query=slowest[1],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="R3: warm ask latency on the RFC corpus")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--n", type=int, default=25, help="queries per population")
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)

    root = args.root.resolve()
    vocab = source_vocabulary(root)
    print(f"corpus vocabulary: {len(vocab)} distinct terms")
    print(f"highest df: {vocab[0][1]}  median df: {vocab[len(vocab) // 2][1]}\n")

    worst = [t for t, _ in vocab[: args.n]]
    mid = len(vocab) // 2
    typical = [t for t, _ in vocab[mid : mid + args.n]]
    tail = [t for t, _ in vocab[-args.n * 4 :]]
    multi = [f"{tail[i * 3 % len(tail)]} {worst[i % len(worst)]}" for i in range(args.n)]

    populations = {
        "worst (highest df)": worst,
        "typical (median df)": typical,
        "multi-term": multi,
    }

    runners = {
        "scan": lambda q: scan.ask(root, q, top=args.top),
        "accel (skip off)": lambda q: accel.ask(root, q, top=args.top, skipping=False),
        "accel (skip on)": lambda q: accel.ask(root, q, top=args.top, skipping=True),
    }

    print(f"{'population':<22} {'path':<18} {'median':>9} {'p95':>9} {'max':>9}   R3")
    print("-" * 82)
    collected: list[dict] = []
    for pop_label, queries in populations.items():
        for run_label, fn in runners.items():
            t = time_queries(fn, queries, run_label)
            judged = t.verdict() if run_label == "accel (skip on)" else ""
            print(
                f"{pop_label:<22} {run_label:<18} {t.median_ms:>8.1f}ms {t.p95_ms:>8.1f}ms "
                f"{t.max_ms:>8.1f}ms   {judged}"
            )
            collected.append(
                {
                    "population": pop_label,
                    "path": run_label,
                    "queries": t.queries,
                    "median_ms": round(t.median_ms, 3),
                    "p95_ms": round(t.p95_ms, 3),
                    "max_ms": round(t.max_ms, 3),
                    "slowest_query": t.slowest_query,
                }
            )
        print()

    worst_on = next(
        c for c in collected if c["population"].startswith("worst") and c["path"] == "accel (skip on)"
    )
    verdict = "PASS" if worst_on["p95_ms"] <= R3_BUDGET_MS else "FAIL"
    print(f"R3 (bar: p95 <= {R3_BUDGET_MS:.0f} ms on the WORST-CASE population): {verdict}")
    print(f"  worst-case p95 = {worst_on['p95_ms']:.1f} ms;  slowest single query "
          f"{worst_on['slowest_query']!r} at {worst_on['max_ms']:.1f} ms")

    if args.json_out:
        args.json_out.write_text(
            json.dumps(
                {"budget_ms": R3_BUDGET_MS, "verdict": verdict, "measurements": collected},
                indent=2,
            ),
            encoding="utf-8",
        )
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
