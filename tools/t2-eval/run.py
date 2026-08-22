"""R9 — does the T1 accelerator clear R3's bar at the 10 000-document design point?

**The bar, the populations and the verdict rule live in
[`PRE-REGISTRATION.md`](PRE-REGISTRATION.md), not here.** This file is the
instrument; that file is the contract. Nothing in this module may restate the
bar in looser words — the constant below is copied from it and is not to be
edited to make a run pass.

## What is timed, and why in-process

`fux ask --fast` warm, against a built accelerator: the T1 path, which is the
thing T2 would replace. R3 timed the same way — one warm-up run per query, then
the median of three — and reusing a bar means reusing the method that produced
it, or the number is not comparable to the bar it is judged against.

In-process rather than by `subprocess`, deliberately: a CLI invocation adds
~50-100 ms of interpreter start to every sample, which at a 150 ms bar would be
most of the budget and would be measuring Python's startup rather than the
accelerator. R3 measured in-process for the same reason.

## The populations

`worst` is the 20 highest-`df` terms in the committed index. **The verdict is
read from that population alone** — R3's bar names worst-case terms explicitly,
and an average over easy queries is not R3. `typical` and `multi` are reported
beside it and gate nothing.

## Index size is characterisation, not R7

The report records committed bytes because the paper's §5 needs a measured
number to replace a projection. **No budget is applied to it.** R7's threshold
was retired with the design point and its re-derivation is Arpit's
(pre-registration §3); a budget picked after reading this number would be
contaminated by it.

Usage:
    python tools/t2-eval/run.py --repo <path-to-lab-env>/repo --out <dir>
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

#: The pre-registered bar, from PRE-REGISTRATION.md §2 — which took it verbatim
#: from R3. **Do not edit this to make a run pass.**
R9_BAR_MS = 150.0
R9_JUDGED_DOCS = 10_000

#: R3's method: one warm-up, then the median of three.
WARMUPS = 1
REPEATS = 3
POPULATION_SIZE = 20


def _engine_sha() -> str:
    out = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True
    )
    dirty = subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True
    )
    return out.stdout.strip() + ("+dirty" if dirty.stdout.strip() else "")


def _df_populations(repo: Path) -> dict[str, list[str]]:
    """Query populations derived from the committed index's own `df`.

    Terms are stored hashed, so the populations are built from **hashes**, not
    words: `ask` tokenizes a query into hashes anyway, so a query can be posed
    directly as the hash that a document actually contains. This is what makes
    "the 20 highest-df terms" an exact statement rather than a guess about
    which English word happens to be common in a generated corpus.
    """
    from fux import store as store_mod

    df: Counter[str] = Counter()
    for path in store_mod.iter_shard_paths(repo):
        _, records = store_mod.read_shard(path)
        for record in records:
            df.update(record.get("terms", {}).keys())

    if not df:
        raise SystemExit(f"no committed index at {repo} — run the environment's setup first")

    ranked = df.most_common()
    worst = [h for h, _ in ranked[:POPULATION_SIZE]]
    mid = len(ranked) // 2
    typical = [h for h, _ in ranked[mid : mid + POPULATION_SIZE]]
    # Three-term queries drawn from the worst population: the most expensive
    # shape, since every term opens a posting list.
    multi = [
        " ".join(worst[i % len(worst)] for i in (j, j + 1, j + 2))
        for j in range(POPULATION_SIZE)
    ]
    return {"worst": worst, "typical": typical, "multi": multi, "_df_top": ranked[:5]}


def _time_query(fn, query: str) -> float:
    for _ in range(WARMUPS):
        fn(query)
    samples = []
    for _ in range(REPEATS):
        start = time.perf_counter()
        fn(query)
        samples.append((time.perf_counter() - start) * 1000.0)
    return statistics.median(samples)


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    # Nearest-rank p95, the same definition R3 used.
    idx = max(0, min(len(ordered) - 1, int(round(0.95 * len(ordered))) - 1))
    return ordered[idx]


def measure(repo: Path, docs: int, *, scan_too: bool) -> dict:
    from fux.derive import accel
    from fux.query import scan as scan_mod

    populations = _df_populations(repo)
    row: dict = {"corpus_docs": docs, "populations": {}}

    for name in ("worst", "typical", "multi"):
        queries = populations[name]
        accel_ms = [_time_query(lambda q: accel.ask(repo, q, top=5), q) for q in queries]
        entry = {
            "queries": len(queries),
            "accel_median_ms": round(statistics.median(accel_ms), 2),
            "accel_p95_ms": round(_p95(accel_ms), 2),
            "accel_max_ms": round(max(accel_ms), 2),
        }
        if scan_too:
            # Unjudged. R3 found the scan 28x over budget at RFC scale; whether
            # that still holds is interesting and gates nothing.
            scan_ms = [_time_query(lambda q: scan_mod.ask(repo, q, top=5), q) for q in queries]
            entry["scan_median_ms"] = round(statistics.median(scan_ms), 2)
            entry["scan_p95_ms"] = round(_p95(scan_ms), 2)
        row["populations"][name] = entry
        print(
            f"  {docs:>6} docs · {name:<8}: accel p95 {entry['accel_p95_ms']:>8.2f} ms"
            + (f"  · scan p95 {entry['scan_p95_ms']:>10.2f} ms" if scan_too else "")
        )

    row["judged_p95_ms"] = row["populations"]["worst"]["accel_p95_ms"]
    row["passes"] = row["judged_p95_ms"] <= R9_BAR_MS
    return row


def _index_size(repo: Path) -> dict:
    """Committed index bytes, working tree and git-packed.

    **Characterisation for the paper's §5, not R7** — see the module docstring
    and PRE-REGISTRATION.md §3. Packed size is measured the way the 2026-08-21
    preliminary analysis measured it: an isolated scratch repo plus an
    aggressive gc, because `du` reports working-tree bytes and the committed
    cost is what git actually stores.
    """
    import shutil
    import tempfile

    index = repo / ".fux" / "index"
    raw = sum(p.stat().st_size for p in index.glob("*.jsonl"))

    packed = None
    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp) / "scratch"
        shutil.copytree(index, scratch / ".fux" / "index")
        env = {"GIT_AUTHOR_NAME": "bench", "GIT_AUTHOR_EMAIL": "b@f",
               "GIT_COMMITTER_NAME": "bench", "GIT_COMMITTER_EMAIL": "b@f",
               "PATH": "/usr/bin:/bin:/usr/local/bin"}
        run = lambda *a: subprocess.run(a, cwd=scratch, capture_output=True, env=env)
        run("git", "init", "-q")
        run("git", "add", "-A")
        run("git", "commit", "-qm", "index")
        run("git", "gc", "--aggressive", "--prune=now", "-q")
        objects = scratch / ".git" / "objects"
        if objects.is_dir():
            packed = sum(p.stat().st_size for p in objects.rglob("*") if p.is_file())

    return {
        "raw_bytes": raw,
        "packed_bytes": packed,
        "raw_bytes_per_doc": None,
        "packed_bytes_per_doc": None,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True, help="a lab environment's repo/")
    parser.add_argument("--docs", type=int, required=True, help="corpus size, for the report")
    parser.add_argument("--out", type=Path, help="directory to write report.json into")
    parser.add_argument("--no-scan", action="store_true", help="skip the unjudged scan arm")
    args = parser.parse_args(argv)

    repo = args.repo.resolve()
    print(f"R9 — T1 at {args.docs} documents, against R3's {R9_BAR_MS:.0f} ms bar")

    row = measure(repo, args.docs, scan_too=not args.no_scan)
    size = _index_size(repo)
    if args.docs:
        size["raw_bytes_per_doc"] = round(size["raw_bytes"] / args.docs, 1)
        if size["packed_bytes"]:
            size["packed_bytes_per_doc"] = round(size["packed_bytes"] / args.docs, 1)

    report = {
        "engine_sha": _engine_sha(),
        "python": sys.version.split()[0],
        "platform": subprocess.run(["uname", "-srm"], capture_output=True, text=True).stdout.strip(),
        "pre_registration": "tools/t2-eval/PRE-REGISTRATION.md",
        "r9_bar_ms": R9_BAR_MS,
        "r9_judged_docs": R9_JUDGED_DOCS,
        "latency": row,
        # Labelled at the key, so it cannot be read as a gated number.
        "index_size_POST_HOC_not_R7": size,
    }
    if args.docs == R9_JUDGED_DOCS:
        report["r9_verdict"] = "PASS" if row["passes"] else "FAIL"
    else:
        # Refusing to rule off a size the pre-registration did not judge is
        # correct behaviour, not a gap.
        report["r9_verdict"] = f"NOT RULED — {args.docs} is not the judged size"
    print(f"  verdict: {report['r9_verdict']}")
    print(
        f"  index: {size['raw_bytes'] / 1e6:.1f} MB raw"
        + (f", {size['packed_bytes'] / 1e6:.1f} MB packed" if size["packed_bytes"] else "")
        + "  (post-hoc characterisation, NOT R7)"
    )

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / f"report-{args.docs}.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
        print(f"wrote {args.out / f'report-{args.docs}.json'}")
    else:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
