"""W-298 step 1 — run the sealed intents through fux, record rank of the expected rule.

Writes rows.tsv (one row per intent per verb) and prints the summary.
"""
import csv, json, subprocess, sys, pathlib

REPO = pathlib.Path("/home/claude/spike/repo")
FUX = ["uv", "run", "--project", "/home/claude/arpitarya/fux", "fux"]
PREFIX = "node_modules/@codelaw/rules-js/rules/"
K = 5

intents = list(csv.DictReader(open("/home/claude/spike/intents.tsv"), delimiter="\t"))
rows = []
for verb in ("ask", "find"):
    hits_k = 0
    for it in intents:
        q = it["intent (plain words, as a user would type it)"]
        want = it["expected rule"]
        out = subprocess.run(FUX + [verb, "--json", "--top", "10", q], cwd=REPO,
                             capture_output=True, text=True)
        try:
            d = json.loads(out.stdout)
        except json.JSONDecodeError:
            print("BAD JSON", verb, it["id"], out.stderr[-300:], file=sys.stderr); continue
        res = d["results"] if isinstance(d, dict) else d
        locs = [r["loc"].removeprefix(PREFIX).removesuffix(".md") for r in res]
        rank = locs.index(want) + 1 if want in locs else None
        if rank is not None and rank <= K:
            hits_k += 1
        rows.append({"verb": verb, "id": it["id"], "rank": rank if rank else ">10",
                     "top1": locs[0] if locs else "-", "expected": want, "intent": q,
                     "top5": " | ".join(locs[:5])})
    print(f"{verb}: {hits_k}/{len(intents)} in top {K}")

with open("/home/claude/spike/rows.tsv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
    w.writeheader(); w.writerows(rows)
