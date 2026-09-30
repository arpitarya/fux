"""W-242 bench — Node find/ask/answer wall time, 3 verbs x 3 corpora.

    bench.py LABEL FUX_MJS FUX_ROOT RUNG01000 RUNG10000 [EXTRA_ARG ...]

Writes one JSON row per cell to evidence/bench-LABEL.jsonl: cold (the first
run), warm (median of the next 7), the load averages, rc and stdout's sha256.
Frozen with PRE-REGISTRATION.md; not edited after the `base` run.
"""
import hashlib, json, os, statistics, subprocess, sys, time
from pathlib import Path

label, entry, fux_root, r1k, r10k, *extra = sys.argv[1:]
corpora = {"fux": (fux_root, "rollback"), "rung-01000": (r1k, "incident"), "rung-10000": (r10k, "incident")}
verbs = {"find": ["find", "Q", "--json", "--top", "5"],
         "ask": ["ask", "Q", "--json", "--top", "20", "--band"],
         "answer": ["answer", "Q", "--json"]}
WARM = 7
out = Path(__file__).parent / f"bench-{label}.jsonl"
rows = []
for cname, (root, q) in corpora.items():
    for vname, args in verbs.items():
        argv = ["node", entry, *[q if a == "Q" else a for a in args], *extra]
        times, outs = [], set()
        for _ in range(1 + WARM):
            t = time.perf_counter()
            r = subprocess.run(argv, cwd=root, capture_output=True)
            times.append(time.perf_counter() - t)
            outs.add((r.returncode, hashlib.sha256(r.stdout).hexdigest()))
        rc, sha = sorted(outs)[0]
        row = {"label": label, "corpus": cname, "verb": vname, "cold_s": round(times[0], 4),
               "warm_median_s": round(statistics.median(times[1:]), 4),
               "load": [round(x, 2) for x in os.getloadavg()], "rc": rc, "stdout_sha256": sha,
               "stable": len(outs) == 1}
        rows.append(row)
        print(f"{cname:11} {vname:6} cold {row['cold_s']:.3f}  warm {row['warm_median_s']:.3f}  "
              f"load {row['load'][0]:.2f}  rc {rc}  {sha[:12]}{'' if row['stable'] else '  UNSTABLE'}")
out.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
