#!/usr/bin/env python3
"""W-175 — does a `fux correct` line help phrasings OTHER than its own?

**The one claim [`fux correct`](../../records/0137_enrich.md) shipped
unmeasured**, and the single argument on which document expansion beat an
editorial pin: *(a) yes, but brittle — one phrasing fixed, the next still
wrong. (b) best fit — generalises across phrasings.*

The bar, the arms and the sizes are
[`work/regression/2026-09-15-correction-generalisation/PRE-REGISTRATION.md`](../../work/regression/2026-09-15-correction-generalisation/PRE-REGISTRATION.md),
frozen before this file existed. **This runner applies no bar**: it emits one row
per paraphrase per arm and prints the paired counts.

## What it does, per correction

1. measure every paraphrase **before** — is the target in the top 3?
2. `fux correct "<the correction's own question>" <target>`
3. re-ingest, so the appended question reaches `ctx`
4. measure every paraphrase **again**

🔴 **The correction's OWN question is filed; the PARAPHRASES are only ever
measured.** Filing a paraphrase would be measuring whether a question helps
itself, which is the thing document expansion was *not* chosen for.

## What this runner cannot supply, by construction

- 🔴 **The corrections.** They must come from real failures on a corpus the
  measurer did not grade — inventing them is fitting the instrument to the
  answer.
- 🔴 **The paraphrases.** Written **blind by Codex**, from the question alone
  ([the prompt](../../work/regression/2026-09-15-correction-generalisation/prompt-codex-paraphrases.md)).
  **A paraphrase written by anyone who has seen the correction is the
  correction's own wording in disguise**, and a leaked one produces a filed
  number shaped exactly like a clean one.

So it takes them as a **file**, and refuses to run without one.

⚠ **Run on a SCRATCH COPY.** It writes `.fux/enrich/` and re-ingests.

    python3 tools/quality-controls/correction_generalisation.py \
        --tree /tmp/scratch --arm iii --paraphrases paraphrases-iii.jsonl \
        --rows-out evidence/rows-iii.jsonl
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOP = 3


def run(tree: Path, *args: str) -> dict | None:
    out = subprocess.run(
        [sys.executable, "-m", "fux.cli", *args], cwd=tree, capture_output=True, text=True
    )
    try:
        return json.loads(out.stdout)
    except Exception:
        return None


def hit(tree: Path, question: str, target: str) -> bool | None:
    """Is `target` in the top 3 for `question`? `None` if the call produced no JSON."""
    payload = run(tree, "ask", question, "--json", "--top", str(TOP))
    if payload is None:
        return None
    return target in [r.get("loc") for r in (payload.get("results") or [])]


def file_correction(tree: Path, question: str, target: str) -> bool:
    out = subprocess.run(
        [sys.executable, "-m", "fux.cli", "correct", question, target],
        cwd=tree, capture_output=True, text=True,
    )
    if out.returncode != 0:
        print(f"  ! correct failed for {target}: {out.stderr.strip()[:160]}", file=sys.stderr)
    return out.returncode == 0


def reingest(tree: Path) -> bool:
    # ⚠ `--no-fetch`: this is a local corpus and the run must not depend on a
    # network, on a path L4 fences (W-177 made the bare verb networked).
    out = subprocess.run(
        [sys.executable, "-m", "fux.cli", "ingest", "--no-fetch"],
        cwd=tree, capture_output=True, text=True,
    )
    return out.returncode == 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tree", type=Path, required=True, help="a SCRATCH copy — this writes to it")
    ap.add_argument("--arm", required=True, choices=["i", "ii", "iii"])
    ap.add_argument(
        "--paraphrases", type=Path, required=True,
        help="Codex's block 1: {arm, correction_id, question, paraphrases[], should_win}",
    )
    ap.add_argument("--rows-out", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args(argv)

    rows_in = [
        json.loads(l)
        for l in args.paraphrases.read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    if not rows_in:
        print("no paraphrases — this runner may not author them (see the module docstring)",
              file=sys.stderr)
        return 1

    tree = args.tree.resolve()
    print(f"arm {args.arm}: {len(rows_in)} corrections, "
          f"{sum(len(r['paraphrases']) for r in rows_in)} paraphrases\ntree: {tree}\n")

    rows: list[dict] = []
    for i, c in enumerate(rows_in, 1):
        target = c.get("should_win") or c.get("target")
        if not target:
            print(f"  ! {c['correction_id']}: no target document named", file=sys.stderr)
            continue

        before = {p: hit(tree, p, target) for p in c["paraphrases"]}
        # 🔴 The correction's OWN question, never a paraphrase.
        filed = file_correction(tree, c["question"], target)
        if filed:
            reingest(tree)
        after = {p: hit(tree, p, target) for p in c["paraphrases"]}

        for p in c["paraphrases"]:
            rows.append({
                "arm": args.arm, "correction_id": c["correction_id"],
                "target": target, "question": c["question"], "paraphrase": p,
                "before": before[p], "after": after[p], "filed": filed,
            })
        if i % 3 == 0:
            print(f"  {i}/{len(rows_in)} corrections", flush=True)

    usable = [r for r in rows if r["before"] is not None and r["after"] is not None]
    better = sum(1 for r in usable if r["after"] and not r["before"])
    worse = sum(1 for r in usable if r["before"] and not r["after"])
    # Regression headroom is measured in the BASELINE arm (SR-RS 22f).
    regress = sum(1 for r in usable if r["before"])
    improve = len(usable) - regress

    print(f"\n{'arm':>4}  {'n':>4}  {'before':>6}  {'after':>5}  {'better':>6}  {'worse':>5}  "
          f"{'discordant':>10}  {'net':>5}")
    print(f"{args.arm:>4}  {len(usable):>4}  {regress:>6}  "
          f"{sum(1 for r in usable if r['after']):>5}  {better:>6}  {worse:>5}  "
          f"{better + worse:>10}  {better - worse:>+5}")
    print(f"\nheadroom (SR-RS 22b/22f), measured in the BASELINE arm:")
    print(f"  improvement {improve:>4}/{len(usable):<4}  regression {regress:>4}/{len(usable):<4}"
          + ("   ⚠ ZERO IN A DIRECTION -> INCONCLUSIVE (22d)" if not improve or not regress else ""))
    print("\n🔴 The bar is the PRE-REGISTRATION's and this runner does not apply it.")
    print("   The tilt check — no golden answerable question loses its top-1 — is a")
    print("   CONJUNCTION with it, is scored where the key is, and is Codex's.")

    if args.rows_out:
        args.rows_out.parent.mkdir(parents=True, exist_ok=True)
        args.rows_out.write_text(
            "\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n", encoding="utf-8"
        )
    if args.json_out:
        args.json_out.write_text(json.dumps({
            "arm": args.arm, "n": len(usable), "better": better, "worse": worse,
            "discordant": better + worse, "net": better - worse,
            "improvement_headroom": improve, "regression_headroom": regress,
        }, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
