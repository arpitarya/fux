"""W-239 harness: time each `fux ingest --full` phase and print the root hash.

    <fux>/.venv/bin/python phase_times.py <rung-dir> [--profile out.prof]

Measurement tooling (L12 exempt: lives outside src/). Wall-clock is fine here —
this reads the engine, it is not the engine.
"""

import cProfile
import hashlib
import json
import sys
import time
from pathlib import Path

from fux.ingest import run as run_mod


class _Phase:
    def __init__(self, sink, name, total):
        self.sink, self.name, self.total = sink, name, total

    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def update(self, n=1, detail=""):
        pass

    def __exit__(self, *exc):
        self.sink.append((self.name, self.total, time.perf_counter() - self.t0))
        return False


class TimingProgress:
    def __init__(self):
        self.phases = []

    def phase(self, name, total, unit=""):
        return _Phase(self.phases, name, total)


def index_digest(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted((root / ".fux" / "index").iterdir()):
        if p.is_file():
            h.update(p.name.encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def main():
    root = Path(sys.argv[1]).resolve()
    prof = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "--profile" else None
    tp = TimingProgress()
    t0 = time.perf_counter()
    if prof:
        pr = cProfile.Profile()
        pr.enable()
    run_mod.run(root, refresh_urls=False, full=True, progress=tp)
    if prof:
        pr.disable()
        pr.dump_stats(prof)
    total = time.perf_counter() - t0
    print(json.dumps({
        "root": root.name,
        "total_s": round(total, 2),
        "phases": [{"name": n, "docs": t, "s": round(s, 2)} for n, t, s in tp.phases],
        "index_sha256": index_digest(root),
    }, indent=1))


if __name__ == "__main__":
    main()
