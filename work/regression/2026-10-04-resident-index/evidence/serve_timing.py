"""W-249: serve's `/ask` and `/graph` command, per-call vs inside the holder.
usage: serve_timing.py <root> <seed> <query> [...]  — informational, one run."""
import json, os, sys, time
from pathlib import Path
root = Path(sys.argv[1]).resolve(); os.chdir(root)
from fux.serve import _run_cli
from fux.store.resident import Holder
seed, queries = sys.argv[2], sys.argv[3:]
argvs = [["ask", q, "--json", "--why", "--band"] for q in queries] + [["graph", "--json", "--seed", seed]]
holder = Holder(root)
def timed(held):
    out = {}
    for argv in argvs:
        ts = []
        for _ in range(3):
            t = time.perf_counter()
            if held:
                with holder.call():
                    _run_cli(argv)
            else:
                _run_cli(argv)
            ts.append((time.perf_counter() - t) * 1000)
        out[argv[0]] = out.get(argv[0], []) + ts
    return {k: round(sorted(v)[len(v) // 2], 1) for k, v in out.items()}
sys.stderr = open(os.devnull, "w")
for argv in argvs:
    _run_cli(argv)
print(json.dumps({"root": root.name, "per_call_median_ms": timed(False), "held_median_ms": timed(True)}))
