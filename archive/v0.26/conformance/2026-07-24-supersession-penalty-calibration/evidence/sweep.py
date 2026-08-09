#!/usr/bin/env python3
"""Supersession-penalty calibration sweep (fux phase 7, M3).

Per penalty value, per environment: inversion recovery vs hit@1/hit@5
regression. The penalty is read at query time, so no re-ingest is needed
between values — that is what makes a wide sweep affordable.

Usage: sweep.py <env-dir> <fux-bin> <penalty>[,<penalty>...] [--out FILE]
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


def set_penalty(toml_path: Path, value: int) -> None:
    """Rewrite [engine.hybrid] supersession_penalty in place."""
    text = toml_path.read_text(encoding="utf-8")
    if "supersession_penalty" in text:
        text = re.sub(r"supersession_penalty\s*=\s*\d+", f"supersession_penalty = {value}", text)
    elif "[engine.hybrid]" in text:
        text = text.replace("[engine.hybrid]", f"[engine.hybrid]\nsupersession_penalty = {value}", 1)
    else:
        text = text.rstrip("\n") + f"\n\n[engine.hybrid]\nsupersession_penalty = {value}\n"
    toml_path.write_text(text, encoding="utf-8")


def find(fux: str, ws: Path, q: str, top: int = 10, lexical: bool = False) -> list[str]:
    cmd = [fux, "find", q, "--json", "--top", str(top)]
    if lexical:
        cmd.append("--lexical-only")
    p = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, timeout=600)
    if p.returncode != 0:
        return []
    try:
        return [r.get("path", "") for r in json.loads(p.stdout).get("results", [])]
    except json.JSONDecodeError:
        return []


def measure(fux: str, ws: Path, pairs: list[dict]) -> dict:
    """One full pass over the eval set at the currently-configured penalty."""
    answerable = [p for p in pairs if p.get("kind") != "unanswerable" and p.get("doc")]
    by_kind: dict[str, list[int | None]] = defaultdict(list)
    ranks: dict[str, int | None] = {}

    for p in answerable:
        paths = find(fux, ws, p["q"], top=10)
        rank = next((i + 1 for i, pp in enumerate(paths) if pp.endswith(p["doc"])), None)
        by_kind[p["kind"]].append(rank)
        ranks[p["q"]] = rank

    def agg(rs: list[int | None]) -> dict:
        n = max(len(rs), 1)
        return {
            "n": len(rs),
            "hit@1": round(sum(1 for r in rs if r == 1) / n, 3),
            "hit@5": round(sum(1 for r in rs if r and r <= 5) / n, 3),
            "MRR": round(sum(1 / r for r in rs if r) / n, 3),
        }

    allr = [r for rs in by_kind.values() for r in rs]

    # staleness inversions — the harness's own definition, verbatim
    stale = [p for p in pairs if p.get("stale_doc") and p.get("doc")]
    inversions, current_top5, detail = [], 0, []
    for p in stale:
        paths = find(fux, ws, p["q"], top=10)
        cur = next((i for i, pp in enumerate(paths) if pp.endswith(p["doc"])), None)
        stl = next((i for i, pp in enumerate(paths) if pp.endswith(p["stale_doc"])), None)
        if cur is not None and cur < 5:
            current_top5 += 1
        inverted = stl is not None and (cur is None or stl < cur)
        if inverted:
            inversions.append(p["q"])
        detail.append({
            "q": p["q"], "current_rank": (cur + 1) if cur is not None else None,
            "stale_rank": (stl + 1) if stl is not None else None, "inverted": inverted,
        })

    return {
        "all": agg(allr),
        "by_kind": {k: agg(v) for k, v in sorted(by_kind.items())},
        "staleness": {
            "pairs": len(stale), "inversions": len(inversions),
            "current_in_top5": current_top5, "inverted_questions": inversions,
            "detail": detail,
        },
        "ranks": ranks,
    }


def main() -> int:
    env = Path(sys.argv[1]).resolve()
    fux = sys.argv[2]
    values = [int(v) for v in sys.argv[3].split(",")]
    out_path = None
    if "--out" in sys.argv:
        out_path = Path(sys.argv[sys.argv.index("--out") + 1])

    corpus = env / "corpus"
    pairs = json.loads((corpus / "_manifest.json").read_text())["eval_pairs"]
    toml_path = corpus / "fux.toml"
    original = toml_path.read_text(encoding="utf-8")

    results = {}
    try:
        for v in values:
            set_penalty(toml_path, v)
            print(f"  penalty={v} …", flush=True)
            results[str(v)] = measure(fux, corpus, pairs)
            s, a = results[str(v)]["staleness"], results[str(v)]["all"]
            print(f"    inversions {s['inversions']}/{s['pairs']} · "
                  f"hit@1 {a['hit@1']} · hit@5 {a['hit@5']} · MRR {a['MRR']}", flush=True)
    finally:
        toml_path.write_text(original, encoding="utf-8")  # always restore

    payload = {"env": env.name, "values": values, "results": results}
    if out_path:
        out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
