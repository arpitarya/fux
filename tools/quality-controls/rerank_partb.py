#!/usr/bin/env python3
"""W-154 Part B — does proximity reranking earn its latency?

The arms and the rule are
[`work/regression/2026-09-15-rerank-quality/PRE-REGISTRATION.md`](../../work/regression/2026-09-15-rerank-quality/PRE-REGISTRATION.md),
frozen before this file existed. **This runner applies no bar**: it emits one row
per contest per arm per path and prints the paired counts. The decision rule and
SR-RS decision 19's floor are the pre-registration's.

## Two paths, never pooled

| path | hit | mechanisms |
|---|---|---|
| `ask` | the **target document** is at rank 1 | proximity reranking **only** |
| `answer` | the cited locator's line range **overlaps** the true decision | reranking **and** the refer plane's rescore |

🔴 **A flip on `answer` and not on `ask` IS the refer-plane rescore** (W-108).
Pooling them would price two features as one.

## One lever moves

`[ranking] rerank_weight`, `0.0` (shipped) against `1.0`. The tune file is
rewritten between arms and restored at the end; nothing else is touched.

⚠ **Run this on a SCRATCH COPY of the tree.** It writes `.fux/tune.toml`.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools" / "quality-controls"))

LOCATOR = re.compile(r":L(\d+)-L(\d+)$")


def set_weight(tree: Path, value: float) -> str | None:
    """Write `[ranking] rerank_weight`; return the file as it was."""
    path = tree / ".fux" / "tune.toml"
    original = path.read_text(encoding="utf-8") if path.is_file() else None
    text = original or ""
    if re.search(r"^rerank_weight\s*=", text, re.M):
        text = re.sub(r"^rerank_weight\s*=.*$", f"rerank_weight = {value}", text, flags=re.M)
    elif "[ranking]" in text:
        text = text.replace("[ranking]", f"[ranking]\nrerank_weight = {value}", 1)
    else:
        text += f"\n[ranking]\nrerank_weight = {value}\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return original


def run(tree: Path, *args: str) -> dict | None:
    out = subprocess.run([sys.executable, "-m", "fux.cli", *args],
                         cwd=tree, capture_output=True, text=True)
    try:
        return json.loads(out.stdout)
    except Exception:
        return None


def ask_hit(tree: Path, query: str, target: str) -> bool | None:
    payload = run(tree, "ask", query, "--json", "--top", "10")
    if payload is None:
        return None
    results = payload.get("results") or []
    return bool(results) and results[0].get("loc") == target


def answer_hit(tree: Path, query: str, target: str, start: int, end: int) -> bool | None:
    """Does the TOP cited passage overlap the decision the author pointed at?"""
    payload = run(tree, "answer", query, "--json")
    if payload is None:
        return None
    passages = ((payload.get("answer") or {}).get("passages")) or []
    if not passages:
        return False
    loc = passages[0].get("loc") or ""
    match = LOCATOR.search(loc)
    if not match or not loc.startswith(target):
        return False
    lo, hi = int(match.group(1)), int(match.group(2))
    return lo <= end and hi >= start


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tree", type=Path, required=True, help="a SCRATCH copy of the corpus")
    parser.add_argument("--contests", type=Path, required=True, help="contests.jsonl from cited_decision")
    parser.add_argument("--paths", nargs="+", default=["ask", "answer"])
    parser.add_argument("--limit", type=int, default=0, help="0 = every contest")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)

    tree = args.tree.resolve()
    rows = [json.loads(l) for l in args.contests.read_text().splitlines() if l.strip()]
    if args.limit:
        rows = rows[:args.limit]
    print(f"tree: {tree}\ncontests: {len(rows)}   paths: {args.paths}")

    original = None
    out: list[dict] = []
    try:
        for i, c in enumerate(rows, 1):
            row = {"probe": i, "query": c["query"], "target": c["target"],
                   "number": c["number"], "source": c["source"],
                   "line_start": c["line_start"], "line_end": c["line_end"]}
            for path in args.paths:
                for arm, weight in (("off", 0.0), ("on", 1.0)):
                    original = set_weight(tree, weight) if original is None else (
                        set_weight(tree, weight) or original)
                    if path == "ask":
                        hit = ask_hit(tree, c["query"], c["target"])
                    else:
                        hit = answer_hit(tree, c["query"], c["target"],
                                         c["line_start"], c["line_end"])
                    row[f"{path}_{arm}"] = hit
            out.append(row)
            if i % 25 == 0:
                print(f"  {i}/{len(rows)}", flush=True)
    finally:
        if original is not None:
            (tree / ".fux" / "tune.toml").write_text(original, encoding="utf-8")

    print()
    print(f"{'path':>8}  {'n':>4}  {'off':>5}  {'on':>5}  {'better':>6}  {'worse':>5}  "
          f"{'discordant':>10}  {'net':>5}")
    summary = {}
    for path in args.paths:
        usable = [r for r in out if r.get(f"{path}_off") is not None
                  and r.get(f"{path}_on") is not None]
        off = sum(1 for r in usable if r[f"{path}_off"])
        on = sum(1 for r in usable if r[f"{path}_on"])
        better = sum(1 for r in usable if r[f"{path}_on"] and not r[f"{path}_off"])
        worse = sum(1 for r in usable if r[f"{path}_off"] and not r[f"{path}_on"])
        # Headroom, declared before the numbers by the pre-registration.
        improve = sum(1 for r in usable if not r[f"{path}_off"] and not r[f"{path}_on"])
        regress = sum(1 for r in usable if r[f"{path}_off"] and r[f"{path}_on"])
        print(f"{path:>8}  {len(usable):>4}  {off:>5}  {on:>5}  {better:>6}  {worse:>5}  "
              f"{better + worse:>10}  {better - worse:>+5}")
        summary[path] = {"n": len(usable), "off": off, "on": on, "better": better,
                         "worse": worse, "discordant": better + worse,
                         "net": better - worse,
                         "improvement_headroom": improve, "regression_headroom": regress}

    print("\nheadroom (SR-RS 22b), per path:")
    for path, s in summary.items():
        print(f"  {path:>8}  improvement {s['improvement_headroom']:>4}/{s['n']:<4}  "
              f"regression {s['regression_headroom']:>4}/{s['n']:<4}"
              + ("   ⚠ ZERO IN A DIRECTION -> INCONCLUSIVE (22d)"
                 if not s['improvement_headroom'] or not s['regression_headroom'] else ""))
    print("\n🔴 The bar is the PRE-REGISTRATION's and this runner does not apply it.")
    print("   A flip on `answer` and not on `ask` IS the refer-plane rescore (W-108).")

    if args.json_out:
        args.json_out.write_text(json.dumps({"summary": summary, "rows": out}, indent=2),
                                 encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
