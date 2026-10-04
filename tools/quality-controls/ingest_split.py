#!/usr/bin/env python3
"""Time a delta ingest against a full one, phase by phase. W-256 section 8.

Pre-registered in `work/regression/2026-10-04-ingest-split/PRE-REGISTRATION.md`
BEFORE this script produced a number. Measurement tooling (L12 exempt: lives
under `tools/`); wall-clock is fine here, it reads the engine and is not the
engine.

**Why this is not `phase_times.py` from W-239.** That instrument sums the
engine's own progress phases, and the `walk` phase wraps one `p.update` AFTER
`walk_sources` has already returned, so it reads 0.0 s by construction -- and
parsing, hashing and the reuse resolution run between phases and appear in none
of them (W-239's own table: 12.84 s total against 8.3 s of named phases). The
split B-002 needs lives exactly in that unattributed time. So this script keeps
the same hook (`progress.phase`) and ALSO names every GAP between phase events,
which is where the walk and the parse sit.

**A run is a fresh process.** `fux ingest` is a fresh process, and W-239's own
fix was a per-process cache; timing repeated runs in one interpreter would time
warm caches a user never has. So `run` spawns `one` per measurement.

    ingest_split.py run <copy-of-rung> --repeats 3 --out <evidence dir>
    ingest_split.py one <copy-of-rung> --full|--delta         (internal)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def index_digest(root: Path) -> str:
    """sha-256 over every file of `.fux/index/`, names included -- W-239's digest."""
    h = hashlib.sha256()
    for p in sorted((root / ".fux" / "index").iterdir()):
        if p.is_file():
            h.update(p.name.encode())
            h.update(p.read_bytes())
    return h.hexdigest()


class _Phase:
    def __init__(self, sink, name, total, t0):
        self.sink, self.name, self.total, self.t0 = sink, name, total, t0

    def __enter__(self):
        self.enter = time.perf_counter() - self.t0
        return self

    def update(self, n=1, detail=""):
        pass

    def __exit__(self, *exc):
        self.sink.append({"name": self.name, "docs": self.total, "enter": self.enter,
                          "exit": time.perf_counter() - self.t0})
        return False


class Timing:
    def __init__(self):
        self.t0 = time.perf_counter()
        self.phases: list[dict] = []

    def phase(self, name, total, unit=""):
        return _Phase(self.phases, name, total, self.t0)


def segments(phases: list[dict], total: float) -> list[dict]:
    """Every second of the run, attributed: a `before:<phase>` GAP ahead of each
    phase event, the phase itself, and the `tail` after the last one."""
    out: list[dict] = []
    cursor = 0.0
    for ph in sorted(phases, key=lambda p: p["enter"]):
        out.append({"name": f"before:{ph['name']}", "s": ph["enter"] - cursor})
        out.append({"name": ph["name"], "s": ph["exit"] - ph["enter"]})
        cursor = ph["exit"]
    out.append({"name": "tail", "s": total - cursor})
    return out


def one(root: Path, full: bool) -> dict:
    from fux.ingest import run as run_mod

    timing = Timing()
    report = run_mod.run(root, refresh_urls=False, full=full, progress=timing)
    total = time.perf_counter() - timing.t0
    segs = segments(timing.phases, total)
    by = {s["name"]: s["s"] for s in segs}
    extract = by.get("extract", 0.0)
    # walk := everything up to the walk event (config + walk_sources);
    # parse := the gap straight after it (existing-index load, decode/parse,
    # content sha, reuse resolution) up to the next phase event.
    names = [s["name"] for s in segs]
    walk = by.get("before:walk", 0.0) + by.get("walk", 0.0)
    after_walk = names[names.index("walk") + 1] if "walk" in names else None
    parse = by.get(after_walk, 0.0) if after_walk else 0.0
    return {
        "mode": "full" if full else "delta",
        "total_s": round(total, 3),
        "segments": [{"name": s["name"], "s": round(s["s"], 3)} for s in segs],
        "extract_s": round(extract, 3),
        "non_extract_s": round(total - extract, 3),
        "walk_s": round(walk, 3),
        "parse_s": round(parse, 3),
        "docs": report.doc_count,
        "changed": report.changed_count,
        "reused": report.reused_count,
        "index_sha256": index_digest(root),
        "loadavg": os.getloadavg(),
    }


def spawn(root: Path, mode: str) -> dict:
    cmd = [sys.executable, str(Path(__file__).resolve()), "one", str(root), f"--{mode}"]
    before = os.getloadavg()
    done = subprocess.run(cmd, capture_output=True, text=True, check=False,
                          env={**os.environ, "PYTHONPATH": str(ROOT / "src")})
    if done.returncode != 0:
        sys.exit(f"{mode} run failed ({done.returncode}):\n{done.stderr}")
    row = json.loads(done.stdout.strip().splitlines()[-1])
    row["loadavg_before"] = before
    return row


def run(root: Path, repeats: int, out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    warm = spawn(root, "full")  # primes runtime digests; NOT counted
    print(f"warm-up full (discarded): {warm['total_s']} s  {warm['index_sha256'][:12]}")
    for i in range(1, repeats + 1):
        # interleaved, delta first on odd repeats and full first on even ones,
        # so drift on a shared machine (SR-WORK-SESSION d12) hits both alike
        for mode in (("delta", "full") if i % 2 else ("full", "delta")):
            row = spawn(root, mode)
            row.update({"id": f"{mode}-{i}", "arm": mode, "repeat": i})
            rows.append(row)
            print(f"{mode:5} #{i}: total {row['total_s']:7.2f}  extract {row['extract_s']:6.2f}  "
                  f"non-extract {row['non_extract_s']:6.2f}  reused {row['reused']}/{row['docs']}  "
                  f"load {row['loadavg_before'][0]:.1f}")
    with (out / "per-run.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")

    deltas = [r for r in rows if r["arm"] == "delta"]
    fulls = [r for r in rows if r["arm"] == "full"]
    shas = {r["index_sha256"] for r in rows} | {warm["index_sha256"]}
    problems = []
    if len(shas) != 1:
        problems.append(f"index sha not identical across runs: {sorted(s[:12] for s in shas)}")
    for r in deltas:
        if r["changed"] != 0 or r["reused"] != r["docs"]:
            problems.append(f"{r['id']}: not an unchanged delta (changed {r['changed']}, "
                            f"reused {r['reused']} of {r['docs']})")
    med = statistics.median
    summary = {
        "repeats": repeats, "docs": deltas[0]["docs"], "identical_root_sha": len(shas) == 1,
        "index_sha256": sorted(shas)[0] if len(shas) == 1 else None,
        "delta_non_extract_s": [r["non_extract_s"] for r in deltas],
        "delta_non_extract_median_s": round(med(r["non_extract_s"] for r in deltas), 3),
        "delta_walk_parse_s": [round(r["walk_s"] + r["parse_s"], 3) for r in deltas],
        "delta_walk_parse_share": [round((r["walk_s"] + r["parse_s"]) / r["non_extract_s"], 3)
                                   for r in deltas],
        "full_total_median_s": round(med(r["total_s"] for r in fulls), 3),
        "delta_total_median_s": round(med(r["total_s"] for r in deltas), 3),
        "full_over_delta": round(med(r["total_s"] for r in fulls) / med(r["total_s"] for r in deltas), 2),
        "problems": problems,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n",
                                      encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("root", type=Path)
    r.add_argument("--repeats", type=int, default=3)
    r.add_argument("--out", type=Path, required=True)
    o = sub.add_parser("one")
    o.add_argument("root", type=Path)
    g = o.add_mutually_exclusive_group(required=True)
    g.add_argument("--full", action="store_true")
    g.add_argument("--delta", action="store_true")
    args = ap.parse_args(argv)
    root = args.root.resolve()
    if args.cmd == "one":
        print(json.dumps(one(root, args.full)))
        return 0
    if "fux-lab" in root.parts and "scratch" not in root.parts and "tmp" not in str(root):
        sys.exit("refusing: this writes .fux/ in place -- point it at a THROWAWAY COPY, never the lab")
    return run(root, args.repeats, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
