#!/usr/bin/env python3
"""W-154 Part B — does proximity reranking earn its latency?

The arms and the rule are
[`work/regression/2026-09-16-rerank-quality-b2/PRE-REGISTRATION.md`](../../work/regression/2026-09-16-rerank-quality-b2/PRE-REGISTRATION.md),
frozen before this file was edited for it. **This runner applies no bar**: it
emits one row per contest per arm per path and prints the paired counts. The
decision rule and SR-RS decision 19's floor are the pre-registration's.

## 🔴 The citing document is EXCLUDED from the candidate set

The first Part B run was ruled
[**VOID**](../../work/regression/2026-09-15-rerank-quality/VERDICT.md). The
queries are sentences lifted verbatim from a citing document, so that document
is a **perfect proximity match** — the reranker promoted it, and the endpoint
scored that as a miss. Measured across all contests at baseline, **it took rank
1 in 87.5 % of them** while the target took it in 3.3 %.

**It is not a rival the reranker beat; it is where the query came from.** An
endpoint that rewards returning it is asking *can you find the sentence I just
handed you*. `source` is on every contest, so the exclusion is a filter on a
ranked list and not a new truth — and **every emitted row carries the excluded
`source`**, so it is auditable rather than asserted.

## One path, and the other is out of scope by MEASUREMENT

| path | hit | mechanisms |
|---|---|---|
| `ask` | the **target document** is at rank 1 **among non-source candidates** | proximity reranking **only** |

🔴 **`answer` is not run, and was measured out rather than assumed.**
[The reachability check](../../work/regression/2026-09-16-rerank-endpoint-reachability/report.md)
puts **both** candidate criteria at **0 of 120** at the shipped default — the
VOID run's own top-passage overlap, and the same source-exclusion repair one
level down. Zero regression headroom is `INCONCLUSIVE` by construction (SR-RS
22d), so an arm would spend ~2 000 subprocesses on a foregone conclusion.

⚠ **So [W-108](../../records/0133_predictions.md)'s two-mechanism separation is
NOT delivered by this runner and cannot be.** `ask` never fetches, so the refer
plane's rescore is untouched; a verdict built on these rows prices **proximity
reranking on the `ask` path** and nothing else. `answer_hit` is kept below,
unused by default, because the *criterion* is not wrong — the **contest set**
cannot reach it, and a different generator would.

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


def ask_hit(tree: Path, query: str, target: str, source: str) -> bool | None:
    """Is `target` at rank 1 once `source` is removed from the ranked list?

    🔴 **The exclusion is the whole repair** (2026-09-16 pre-registration §3).
    `source` is the document the query's sentence was lifted from, so it is a
    perfect proximity match for its own sentence — not a rival, and not
    something the reranker should be penalised for finding.

    ⚠ **`--top 10` is deliberately more than 1.** The exclusion removes a
    candidate, so a list of one would leave nothing behind it and every
    source-winning contest would read as *no result* rather than as *the target
    was second*.
    """
    payload = run(tree, "ask", query, "--json", "--top", "10")
    if payload is None:
        return None
    kept = [r.get("loc") for r in (payload.get("results") or []) if r.get("loc") != source]
    return kept[:1] == [target]


def answer_hit(tree: Path, query: str, target: str, start: int, end: int) -> bool | None:
    """Does the TOP cited passage overlap the decision the author pointed at?

    ⚠ **Not called by default since 2026-09-16.** It is kept because the
    criterion is not what is wrong — the **contest set** cannot reach it (0 of
    120 at baseline, on this and on its source-excluding variant), and a
    generator whose queries are not lifted verbatim from a corpus document
    would. Deleting it would lose the shape the next instrument has to produce.
    """
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
    # 🔴 **`ask` alone by default** — the pre-registration puts `answer` out of
    # scope on measured grounds, and a default that ran it would quietly file an
    # `INCONCLUSIVE` arm beside a real one.
    parser.add_argument("--paths", nargs="+", default=["ask"])
    parser.add_argument("--limit", type=int, default=0, help="0 = every contest")
    parser.add_argument("--json-out", type=Path)
    # Decision 22e wants per-contest rows as ROWS, not buried in a summary blob:
    # every aggregate anyone computes later comes out of these and nothing else.
    parser.add_argument("--rows-out", type=Path, help="one JSON object per contest")
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
                        hit = ask_hit(tree, c["query"], c["target"], c["source"])
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
        # 🔴 **Headroom is measured in the BASELINE arm, not in both** (the
        # 2026-09-16 pre-registration §6). *Right in both* is post-hoc: it
        # reports what SURVIVED the treatment rather than what was AT RISK going
        # in, and it shrinks exactly when an arm is breaking things — so the
        # endpoint looks like it had less to lose the worse the arm did. The
        # VOID run defined it that way.
        improve = sum(1 for r in usable if not r[f"{path}_off"])
        regress = sum(1 for r in usable if r[f"{path}_off"])
        print(f"{path:>8}  {len(usable):>4}  {off:>5}  {on:>5}  {better:>6}  {worse:>5}  "
              f"{better + worse:>10}  {better - worse:>+5}")
        summary[path] = {"n": len(usable), "off": off, "on": on, "better": better,
                         "worse": worse, "discordant": better + worse,
                         "net": better - worse,
                         "improvement_headroom": improve, "regression_headroom": regress}

    print("\nheadroom (SR-RS 22b) — measured in the BASELINE arm, per path:")
    for path, s in summary.items():
        print(f"  {path:>8}  improvement {s['improvement_headroom']:>4}/{s['n']:<4}  "
              f"regression {s['regression_headroom']:>4}/{s['n']:<4}"
              + ("   ⚠ ZERO IN A DIRECTION -> INCONCLUSIVE (22d)"
                 if not s['improvement_headroom'] or not s['regression_headroom'] else ""))
    print("\n🔴 The bar is the PRE-REGISTRATION's and this runner does not apply it.")
    if "answer" not in args.paths:
        print("   `ask` only: this prices PROXIMITY RERANKING and nothing else.")
        print("   W-108's two-mechanism separation is NOT delivered — `ask` never fetches.")

    if args.json_out:
        args.json_out.write_text(json.dumps({"summary": summary, "rows": out}, indent=2),
                                 encoding="utf-8")
    if args.rows_out:
        args.rows_out.write_text(
            "\n".join(json.dumps(r, sort_keys=True) for r in out) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
