#!/usr/bin/env python3
"""How often does hybrid lose a document --lexical-only would have returned?

Phase 9 M2. The orbit finding was n=1 on ONE question kind. This measures the
whole population: every kind, every eval set, plus the reverse direction (what
hybrid GAINS) so the trade is visible rather than one-sided.

Also answers the interaction question: does the supersession offset ever CREATE
a demotion that penalty=0 did not have?

Usage: lexlost.py <env-dir> <fux-bin> [--penalty N] [--out FILE]
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

TOP = 5


def set_penalty(toml_path: Path, value: int | None) -> None:
    text = toml_path.read_text(encoding="utf-8")
    text = re.sub(r"\n?supersession_penalty\s*=\s*\d+", "", text)
    if value is not None:
        if "[engine.hybrid]" in text:
            text = text.replace("[engine.hybrid]", f"[engine.hybrid]\nsupersession_penalty = {value}", 1)
        else:
            text = text.rstrip("\n") + f"\n\n[engine.hybrid]\nsupersession_penalty = {value}\n"
    toml_path.write_text(text, encoding="utf-8")


def rank_of(fux: str, ws: Path, q: str, doc: str, flags: list[str]) -> int | None:
    p = subprocess.run([fux, "find", q, "--json", "--top", str(TOP)] + flags,
                       cwd=ws, capture_output=True, text=True, timeout=600)
    if p.returncode != 0:
        return None
    try:
        paths = [r.get("path", "") for r in json.loads(p.stdout).get("results", [])]
    except json.JSONDecodeError:
        return None
    return next((i + 1 for i, x in enumerate(paths) if x.endswith(doc)), None)


def measure(fux: str, ws: Path, pairs: list[dict]) -> dict:
    scorable = [p for p in pairs if p.get("kind") != "unanswerable" and p.get("doc")]
    lost, gained, kept, missed = [], [], 0, 0
    by_kind = defaultdict(lambda: {"n": 0, "lost": 0, "gained": 0})
    for p in scorable:
        lex = rank_of(fux, ws, p["q"], p["doc"], ["--lexical-only"])
        hyb = rank_of(fux, ws, p["q"], p["doc"], [])
        k = p["kind"]
        by_kind[k]["n"] += 1
        row = {"q": p["q"], "kind": k, "doc": p["doc"], "lexical_rank": lex, "hybrid_rank": hyb}
        if lex is not None and hyb is None:
            lost.append(row); by_kind[k]["lost"] += 1
        elif lex is None and hyb is not None:
            gained.append(row); by_kind[k]["gained"] += 1
        elif lex is not None and hyb is not None:
            kept += 1
        else:
            missed += 1
    return {
        "n_scorable": len(scorable),
        "lexical_top5_lost": len(lost), "lost_detail": lost,
        "hybrid_gained": len(gained), "gained_detail": gained,
        "both_found": kept, "neither_found": missed,
        "by_kind": {k: dict(v) for k, v in sorted(by_kind.items())},
    }


def main() -> int:
    env = Path(sys.argv[1]).resolve()
    fux = sys.argv[2]
    penalty = None
    if "--penalty" in sys.argv:
        penalty = int(sys.argv[sys.argv.index("--penalty") + 1])
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else None

    ws = env / "corpus"
    pairs = json.loads((ws / "_manifest.json").read_text())["eval_pairs"]
    toml_path = ws / "fux.toml"
    original = toml_path.read_text(encoding="utf-8")
    try:
        if penalty is not None:
            set_penalty(toml_path, penalty)
        res = measure(fux, ws, pairs)
    finally:
        toml_path.write_text(original, encoding="utf-8")

    res["env"] = env.name
    res["penalty"] = penalty if penalty is not None else "default"
    print(f"[{env.name}] penalty={res['penalty']}  n={res['n_scorable']}  "
          f"LOST={res['lexical_top5_lost']}  gained={res['hybrid_gained']}  "
          f"both={res['both_found']}  neither={res['neither_found']}")
    for r in res["lost_detail"]:
        print(f"    LOST  [{r['kind']}] lex={r['lexical_rank']} → hybrid out   {r['q'][:52]}")
    if out:
        out.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
