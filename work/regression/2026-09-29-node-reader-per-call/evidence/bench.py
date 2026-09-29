"""Median wall time of Node find/ask/answer, before vs after, on two corpora.

    bench.py BEFORE_FUX_MJS AFTER_FUX_MJS FUX_ROOT RUNG_ROOT
"""
import statistics, subprocess, sys, time

before, after, fux_root, rung_root = sys.argv[1:5]
variants = {"before": before, "after": after}
roots = {"fux": (fux_root, "rollback"), "rung-10000": (rung_root, "incident")}
verbs = {"find": ["find", "Q", "--json", "--top", "5", "--no-tune"],
         "ask": ["ask", "Q", "--json", "--top", "20", "--no-tune", "--band"],
         "answer": ["answer", "Q", "--json", "--no-tune"]}
N = 7
print("| corpus | verb | before median s | after median s | outputs equal |")
print("|---|---|---|---|---|")
for rn, (root, q) in roots.items():
    for vn, args in verbs.items():
        argv = [q if a == "Q" else a for a in args]
        med, outs = {}, {}
        for var, entry in variants.items():
            ts = []
            for _ in range(N):
                t = time.perf_counter()
                r = subprocess.run(["node", entry, *argv], cwd=root, capture_output=True)
                ts.append(time.perf_counter() - t)
            med[var] = statistics.median(ts)
            outs[var] = (r.returncode, r.stdout)
        print(f"| {rn} | {vn} | {med['before']:.3f} | {med['after']:.3f} | "
              f"{outs['before'] == outs['after']} (rc {outs['after'][0]}) |")
