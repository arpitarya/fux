"""Scale benchmark for the knowledge substrate (handoff 0004 M8).

    uv run python tools/synth_corpus.py --docs 100000 --out /tmp/synth-100k
    uv run python tools/bench.py --project /tmp/synth-100k

Measures the numbers the phase-4 ADRs are required to record:

- ingest wall time (and whether embedding dominates it),
- `fux.db` and `.fux/state/` sizes against the proposal §8b estimates,
- `ask` latency on the full profile, and lean cold vs warm,
- **FuxVec full-corpus scan time**, which decides whether IVF gets built at
  all: the handoff says build it only if the scan exceeds 150 ms.

Timing is wall clock, which is fine here — a benchmark *reports* time, it never
writes it into an artifact, so the determinism law is untouched.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

IVF_THRESHOLD_MS = 150.0


def run_cli(project: Path, *args: str) -> tuple[str, float]:
    started = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, "-m", "fux", *args],
        cwd=project, capture_output=True, text=True, encoding="utf-8",
    )
    elapsed = (time.perf_counter() - started) * 1000
    if proc.returncode != 0:
        raise SystemExit(f"fux {' '.join(args)} failed:\n{proc.stderr}")
    return proc.stdout, elapsed


def dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def set_profile(project: Path, profile: str) -> None:
    config = project / "fux.toml"
    text = config.read_text(encoding="utf-8").split("[index]")[0]
    config.write_text(
        f'{text}[index]\nformat = "sqlite"\nprofile = "{profile}"\n', encoding="utf-8"
    )


def measure_scan(project: Path) -> float:
    """FuxVec full-corpus Hamming scan, isolated from the rest of the query."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from fux.config import load
    from fux.embed import get_model
    from fux.embed.fuxvec import prefilter, quantize
    from fux.state import load_state

    config = load(project)
    model = get_model()
    if model is None:
        return float("nan")
    state = load_state(project)
    codes = {d: e.code for d, e in state.items() if e.code is not None}
    vec = model.embed("how does failover reconciliation work across shards")
    if vec is None or not codes:
        return float("nan")
    code = quantize(vec)
    best = float("inf")
    for _ in range(5):  # best-of-5: report the floor, not scheduler noise
        started = time.perf_counter()
        prefilter(code, codes, config.index.prefilter_width)
        best = min(best, (time.perf_counter() - started) * 1000)
    return best


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--query", default="failover reconciliation across shards")
    parser.add_argument("--skip-ingest", action="store_true")
    args = parser.parse_args()
    project = args.project

    docs = len(list((project / "docs").glob("*.md")))
    source_bytes = dir_size(project / "docs")

    print(f"corpus: {docs} docs · {source_bytes / 1e6:.1f} MB source\n")

    if not args.skip_ingest:
        set_profile(project, "full")
        shutil.rmtree(project / ".fux", ignore_errors=True)
        (project / "fux.lock").unlink(missing_ok=True)
        out, ingest_ms = run_cli(project, "ingest")
        chunks = next(
            (w for line in out.splitlines() if line.startswith("Index:")
             for w in [line.split()[1]]), "?"
        )
        print(f"ingest        {ingest_ms / 1000:8.1f} s   ({chunks} chunks)")

    db = dir_size(project / ".fux/index/fux.db")
    state_dirs = {
        name: dir_size(project / ".fux/state" / name)
        for name in ("codes", "sigs", "meta", "df")
    }
    state = sum(state_dirs.values())
    lock = dir_size(project / "fux.lock")

    print(f"\nsizes (measured, {docs} docs)")
    print(f"  fux.db      {db / 1e6:8.1f} MB   ({db / max(docs, 1):.0f} B/doc)")
    for name, size in state_dirs.items():
        print(f"  state/{name:<6}{size / 1e6:8.2f} MB   ({size / max(docs, 1):.0f} B/doc)")
    print(f"  state TOTAL {state / 1e6:8.2f} MB   ({state / max(docs, 1):.0f} B/doc)")
    print(f"  fux.lock    {lock / 1e6:8.2f} MB")

    print("\nlatency (ms, best of 3)")
    for profile in ("full", "lean"):
        set_profile(project, profile)
        if profile == "lean":
            from fux.index import leancache

            leancache.clear(project)
            _, cold = run_cli(project, "find", args.query, "--json")
            print(f"  lean  cold  {cold:8.1f}")
        timings = [run_cli(project, "find", args.query, "--json")[1] for _ in range(3)]
        label = "full" if profile == "full" else "lean  warm"
        print(f"  {label:<11}{min(timings):8.1f}")

    scan = measure_scan(project)
    print(f"\nFuxVec scan   {scan:8.2f} ms   (threshold {IVF_THRESHOLD_MS:.0f} ms)")
    print(
        "  → IVF NOT needed: linear scan is well inside budget"
        if scan < IVF_THRESHOLD_MS
        else "  → IVF REQUIRED: build deterministic k-means partitioning"
    )

    set_profile(project, "full")
    print("\n" + json.dumps(
        {
            "docs": docs, "source_bytes": source_bytes, "db_bytes": db,
            "state_bytes": state, "state_breakdown": state_dirs,
            "lock_bytes": lock, "fuxvec_scan_ms": round(scan, 3),
        },
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
