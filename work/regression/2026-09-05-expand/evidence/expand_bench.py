#!/usr/bin/env python3
"""W-109's gate — `--expand` over the 50 goldens, graded on RANK.

Two arms on one engine and one corpus:
  `base`   — `fux ask --json`, exactly as it ships
  `expand` — the same, plus a BLIND author's expansion for that query

A golden passes when its `doc` appears at rank <= `max_rank`. `known_failure`
rows are graded like every other row: they are the vocabulary-gap population
this feature exists for, and excluding them would remove the subject.
"""
from __future__ import annotations

import csv, json, os, subprocess, sys
from pathlib import Path

def ask(src: Path, cwd: Path, query: str, expand: str, top: int) -> list[str]:
    env = dict(os.environ); env["PYTHONPATH"] = str(src); env.pop("VIRTUAL_ENV", None)
    cmd = [sys.executable, "-m", "fux.cli", "ask", query, "--json", "--top", str(top)]
    if expand:
        cmd += ["--expand", expand]
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env, check=True)
    return [r["loc"] for r in json.loads(p.stdout)["results"]]

def main() -> int:
    corpus, src = Path(sys.argv[1]), Path(sys.argv[2])
    goldens = [json.loads(l) for l in Path(sys.argv[3]).read_text(encoding="utf-8").splitlines() if l.strip()]
    expansions = {json.loads(l)["id"]: json.loads(l)["expand"]
                  for l in Path(sys.argv[4]).read_text(encoding="utf-8").splitlines() if l.strip()}
    out = Path(sys.argv[5])

    rows = []
    for g in goldens:
        top = max(10, int(g.get("max_rank", 1)))
        exp = expansions.get(g["id"], "")
        base = ask(src, corpus, g["q"], "", top)
        with_e = ask(src, corpus, g["q"], exp, top)
        mr = int(g.get("max_rank", 1))
        rank = lambda ls: (ls.index(g["doc"]) + 1) if g["doc"] in ls else None
        b, e = rank(base), rank(with_e)
        rows.append({
            "id": g["id"], "q": g["q"], "doc": g["doc"], "max_rank": mr,
            "known_failure": int(bool(g.get("known_failure"))),
            "expand": exp,
            "base_rank": b or "", "expand_rank": e or "",
            "base_pass": int(b is not None and b <= mr),
            "expand_pass": int(e is not None and e <= mr),
            "base_top5": "|".join(base[:5]), "expand_top5": "|".join(with_e[:5]),
        })

    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    with out.with_suffix(".jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    fixed = [r["id"] for r in rows if not r["base_pass"] and r["expand_pass"]]
    broke = [r["id"] for r in rows if r["base_pass"] and not r["expand_pass"]]
    kf = [r for r in rows if r["known_failure"]]
    print(f"base pass   {sum(r['base_pass'] for r in rows)}/{len(rows)}")
    print(f"expand pass {sum(r['expand_pass'] for r in rows)}/{len(rows)}")
    print(f"FIXED  {len(fixed)}: {fixed}")
    print(f"BROKEN {len(broke)}: {broke}")
    print(f"discordant {len(fixed)+len(broke)}  net {len(fixed)-len(broke)}")
    print(f"of the {len(kf)} known failures: {sum(r['expand_pass'] for r in kf)} now pass "
          f"({sum(r['base_pass'] for r in kf)} passed before)")
    print(f"empty expansions: {sum(1 for r in rows if not r['expand'])}")
    print(f"rows -> {out} and {out.with_suffix('.jsonl')}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
