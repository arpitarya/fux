#!/usr/bin/env python3
"""W-110's gate — `recall@k` across four enrichment arms, on one engine.

| arm | `.fux/enrich/` holds |
|---|---|
| `none` | nothing |
| `placebo` | content-free matched-length text (ADR-RS decision 15's control) |
| `real` | the blind author's questions, **all 98** |
| `filtered` | the same, minus the 2 `fux enrich --check` refused (doc2query--) |

`recall@k` over the goldens declared `relevance: complete`, per ADR-QUALITY
decision 2's headline. One row per query per arm.
"""
from __future__ import annotations

import csv, json, os, subprocess, sys
from pathlib import Path

KS = (1, 3, 5, 10)


def ask(src: Path, cwd: Path, query: str, top: int) -> list[str]:
    env = dict(os.environ); env["PYTHONPATH"] = str(src); env.pop("VIRTUAL_ENV", None)
    p = subprocess.run(
        [sys.executable, "-m", "fux.cli", "ask", query, "--json", "--top", str(top)],
        cwd=cwd, capture_output=True, text=True, env=env, check=True,
    )
    return [r["loc"] for r in json.loads(p.stdout)["results"]]


def main() -> int:
    scratch, src = Path(sys.argv[1]), Path(sys.argv[2])
    goldens = [json.loads(l) for l in Path(sys.argv[3]).read_text(encoding="utf-8").splitlines() if l.strip()]
    complete = [g for g in goldens if g.get("relevance") == "complete"]
    out = Path(sys.argv[4])
    arms = {a: scratch / f"pg-{a}" for a in ("none", "placebo", "real", "filtered")}

    rows = []
    for g in complete:
        relevant = set(g["relevant"])
        for arm, cwd in arms.items():
            ranked = ask(src, cwd, g["q"], max(KS))
            row = {"id": g["id"], "q": g["q"], "arm": arm, "n_relevant": len(relevant),
                   "top5": "|".join(ranked[:5])}
            for k in KS:
                row[f"recall@{k}"] = round(len(relevant & set(ranked[:k])) / len(relevant), 4)
            row["hit@1"] = int(bool(relevant & set(ranked[:1])))
            rows.append(row)

    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    with out.with_suffix(".jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"{len(complete)} of {len(goldens)} goldens declared complete\n")
    hdr = "arm".ljust(9) + "".join(f"recall@{k}".rjust(11) for k in KS) + "hit@1".rjust(9)
    print(hdr)
    for arm in arms:
        rs = [r for r in rows if r["arm"] == arm]
        line = arm.ljust(9) + "".join(f"{sum(r[f'recall@{k}'] for r in rs)/len(rs):11.4f}" for k in KS)
        print(line + f"{sum(r['hit@1'] for r in rs)/len(rs):9.4f}")

    print()
    base = {r["id"]: r for r in rows if r["arm"] == "none"}
    for arm in ("placebo", "real", "filtered"):
        cur = {r["id"]: r for r in rows if r["arm"] == arm}
        up = [i for i in base if cur[i]["recall@5"] > base[i]["recall@5"]]
        dn = [i for i in base if cur[i]["recall@5"] < base[i]["recall@5"]]
        print(f"none -> {arm:9} recall@5  up {len(up):2} {up}")
        print(f"{'':21}down {len(dn):2} {dn}   net {len(up)-len(dn):+d}  discordant {len(up)+len(dn)}")
    print(f"\nrows -> {out} and {out.with_suffix('.jsonl')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
