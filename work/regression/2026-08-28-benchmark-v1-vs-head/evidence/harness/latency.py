#!/usr/bin/env python3
"""B5/B6 — wall clock, arms INTERLEAVED.

`A B A B`, never `AAAA BBBB`. Thermal drift on a laptop is a real effect and
sequencing hands the second arm a different machine. Every timing row is
written out; the percentiles are computed from the rows and from nothing else.

**One machine, one session.** A run that measures latency here and quality
elsewhere has published two numbers that cannot be read together.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fux(arm: str) -> str:
    return str(ROOT / "arms" / arm / "venv" / "bin" / "fux")


def work(run: str, arm: str, tier: str) -> Path:
    return ROOT / "runs" / run / "work" / f"{arm}-{tier}"


def timed(argv: list[str], cwd: Path) -> tuple[float, str]:
    t0 = time.perf_counter()
    proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=True)
    return (time.perf_counter() - t0) * 1000, proc.stdout


def queries(tier: str, n: int) -> list[str]:
    path = ROOT / "corpora" / tier / "eval" / "pairs.jsonl"
    return [json.loads(l)["q"] for l in path.read_text().splitlines()[:n]]


def differential_law(run: str, tier: str, qs: list[str]) -> dict:
    """`ask --fast` and `ask --scan` must be byte-identical, WITHIN each arm.

    Asserted before any `--fast` number is reported. An arm that fails this is
    not benchmarked on `--fast` at all — the two paths would be answering
    different questions.
    """
    out = {}
    for arm in ("A", "B"):
        cwd = work(run, arm, tier)
        subprocess.run([fux(arm), "build"], cwd=cwd, capture_output=True, check=True)
        mismatches = []
        for q in qs:
            _, scan = timed([fux(arm), "ask", q, "--json", "--top", "10", "--scan"], cwd)
            _, fast = timed([fux(arm), "ask", q, "--json", "--top", "10", "--fast"], cwd)
            if scan != fast:
                mismatches.append(q)
        out[arm] = {"checked": len(qs), "mismatches": len(mismatches), "examples": mismatches[:3]}
    return out


def b5(run: str, tier: str, qs: list[str], repeats: int) -> list[dict]:
    rows: list[dict] = []
    for arm in ("A", "B"):  # warm-up, discarded
        for q in qs[:20]:
            timed([fux(arm), "ask", q, "--json", "--top", "10"], work(run, arm, tier))
    for rep in range(repeats):
        for i, q in enumerate(qs):
            for arm in ("A", "B"):  # <- the interleave
                ms, _ = timed([fux(arm), "ask", q, "--json", "--top", "10"], work(run, arm, tier))
                rows.append({"metric": "B5", "arm": arm, "tier": tier, "rep": rep,
                             "qid": f"pairs-{i:04d}", "ms": round(ms, 3)})
    return rows


def b6(run: str, tier: str, repeats: int) -> list[dict]:
    """Cold ingest + build. `.fux/` is removed between repeats — a warm ingest
    carries 1 000 documents forward and measures nothing."""
    import shutil
    rows: list[dict] = []
    for rep in range(repeats):
        for arm in ("A", "B"):
            cwd = work(run, arm, tier)
            shutil.rmtree(cwd / ".fux", ignore_errors=True)
            subprocess.run([fux(arm), "setup"], cwd=cwd, capture_output=True, check=True)
            (cwd / ".fux" / "sources" / "dirs").write_text("docs\n")
            ms_i, _ = timed([fux(arm), "ingest"], cwd)
            ms_b, _ = timed([fux(arm), "build"], cwd)
            rows.append({"metric": "B6", "arm": arm, "tier": tier, "rep": rep,
                         "ingest_ms": round(ms_i, 1), "build_ms": round(ms_b, 1)})
    return rows


def pct(values: list[float], q: float) -> float:
    s = sorted(values)
    return round(s[min(len(s) - 1, int(q * len(s)))], 3)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--tier", required=True)
    ap.add_argument("--queries", type=int, default=240)
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--law-queries", type=int, default=240)
    args = ap.parse_args()

    qs = queries(args.tier, args.queries)
    outdir = ROOT / "runs" / args.run / "rows"
    outdir.mkdir(parents=True, exist_ok=True)

    law = differential_law(args.run, args.tier, queries(args.tier, args.law_queries))
    print("differential law:", json.dumps(law, sort_keys=True))

    rows = b5(args.run, args.tier, qs, args.repeats) + b6(args.run, args.tier, 3)
    path = outdir / f"latency-{args.tier}.jsonl"
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))

    summary = {"differential_law": law, "tier": args.tier}
    for arm in ("A", "B"):
        ms = [r["ms"] for r in rows if r["metric"] == "B5" and r["arm"] == arm]
        ing = [r["ingest_ms"] for r in rows if r["metric"] == "B6" and r["arm"] == arm]
        bld = [r["build_ms"] for r in rows if r["metric"] == "B6" and r["arm"] == arm]
        summary[arm] = {"b5_n": len(ms), "b5_p50": pct(ms, 0.50), "b5_p95": pct(ms, 0.95),
                        "b6_ingest_median": round(statistics.median(ing), 1),
                        "b6_ingest_all": ing,
                        "b6_build_median": round(statistics.median(bld), 1)}
    (outdir.parent / f"latency-summary-{args.tier}.json").write_text(
        json.dumps(summary, indent=1, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
