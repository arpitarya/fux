"""W-249: RSS of a held index (no tracemalloc), and warm `fux_search` latency.

usage: memory_rss.py <root> <seed-path> <query> [<query> ...]

Steady RSS after three per-call rounds of fux_search + fux_related, then after
three rounds through one Holder; then each query timed 5x per arm, median and
max. Informational: one machine, one run.
"""
import gc, json, os, subprocess, sys, time
from pathlib import Path
root = Path(sys.argv[1]).resolve(); os.chdir(root)
seed, queries = sys.argv[2], sys.argv[3:]
from fux import mcp
from fux.output_config import load
from fux.store.resident import Holder
cfg = load(root, enabled=True)
top, mh = int(cfg.resolve_mcp("top")), int(cfg.resolve_mcp("max_headings"))


def rss():
    return int(subprocess.run(["ps", "-o", "rss=", "-p", str(os.getpid())], capture_output=True, text=True).stdout) / 1024


def call(holder, name, args):
    msg = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}}
    return mcp._handle(root, msg, top=top, max_headings=mh, holder=holder)


def rounds(holder):
    for _ in range(3):
        for q in queries:
            call(holder, "fux_search", {"query": q})
        call(holder, "fux_related", {"path": seed})
    gc.collect()


def timed(holder):
    out = []
    for q in queries:
        for _ in range(5):
            t = time.perf_counter()
            call(holder, "fux_search", {"query": q})
            out.append((time.perf_counter() - t) * 1000)
    out.sort()
    return {"median_ms": round(out[len(out) // 2], 1), "max_ms": round(out[-1], 1), "n": len(out)}


rounds(None)
per_call = rss()
holder = Holder(root)
rounds(holder)
held = rss()
state = holder.state
print(json.dumps({
    "root": root.name, "docs": len(state.records), "shards": len(state.lines),
    "shard_bytes": sum(len(l) for _, ls in state.lines.values() for l in ls),
    "rss_per_call_mb": round(per_call, 1), "rss_held_mb": round(held, 1), "rss_delta_mb": round(held - per_call, 1),
    "fux_search_per_call": timed(None), "fux_search_held": timed(holder), "loads": holder.loads,
}))
