#!/usr/bin/env python3
"""How much can ANY ranking change win here? — SR-RS decision 22, as an instrument.

**What it answers, before a feature is built rather than after it is measured.**
A paired ranking run can only be decided by the questions that **could** move.
[SR-RS](../../records/0133_predictions.md) decision 22 requires every paired run
to disclose that pool per direction; decision 19 sets the net it must then
clear, and **that net RISES with the discordant count**. Put together, they
imply a question nobody was asking early enough:

> **Is there enough room in this corpus for a verdict to be possible at all?**

🔴 **Three filed runs have now returned a null that the corpus determined, not
the feature.** B1 measured `hit@5` at **240/240 in both arms at every tier** —
*"`pb` and `pc` are structurally zero"*. W-168 step 2 found headroom of **3–4 of
33 against a floor of 6**, so *"step 2 cannot be given a verdict on this corpus
whatever questions are written"*. W-191 measured a link feature on a corpus with
**0 `ref` edges**. **In each case the arithmetic was available before the run.**

## What it computes

Per `rung × set`, over the **answerable** questions only:

| column | meaning |
|---|---|
| `pool` | answerable questions whose primary is **not** already in the top `k` — every question a ranking change could win |
| `net_if_all_flip` | the net [SR-RS](../../records/0133_predictions.md) decision 19 requires **if every question in the pool flipped** — the discordant count is then the whole pool |
| `verdict_possible` | whether a perfect feature could clear the bar |
| `min_wins` | the fewest wins that clear **with zero losses** — the discordant count is then the wins themselves, so it is the same number for every pool large enough to hold it |

🔴 **`net_if_all_flip` is NOT the fewest wins that clear, and it was once
labelled as if it were** (`min_fix`, W-219, 2026-09-23). Decision 19's net rises
with the discordant count; a feature that wins `w` and loses nothing has a
discordant count of `w`, not of the pool. So 6 wins with zero losses clear at a
pool of 8, 18 or 23 alike, while `net_if_all_flip` there reads 8, 10 and 11.

⚠ **`min_wins` is a CEILING on optimism, never a prediction.** It assumes a
feature breaks nothing, which no measured ranking change in this repository has
ever managed. Each loss adds one to the discordant count and subtracts one from
the net.

🔴 **It applies no bar and rules on nothing** ([SR-RS](../../records/0133_predictions.md)
decision 10b): a floor lives in a frozen pre-registration, never in an
instrument. It reports what the arithmetic permits.

    python3 tools/quality-controls/ranking_headroom.py \\
        --rows work/regression/2026-09-22-band-operating-point/evidence/per-query.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from verdict import ALPHA  # noqa: E402
from resolution import smallest_detectable, two_sided_p  # noqa: E402

RETIRED = ROOT / "work" / "golden" / "retired"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def expectations() -> dict[str, dict]:
    """`id -> expected row`, from the RETIRED sets — open regression data under
    [L11](../../records/0012_LAW-11-sealed-answer-key.md) decision 14. It opens
    no sealed key on any spelling and needs no unlock."""
    out: dict[str, dict] = {}
    for set_dir in sorted(RETIRED.glob("set-*")):
        path = set_dir / "expected.jsonl"
        if path.is_file():
            for row in read_jsonl(path):
                out[row["id"]] = row
    return out


def fewest_clean_wins(pool: int, alpha: float = ALPHA) -> int | None:
    """The fewest wins that clear decision 19 **with zero losses**, if the pool
    can hold that many. With no losses, `w` wins are a discordant count of `w`
    all going one way, so this is the smallest `w` whose one-sided sweep clears
    — read from `resolution`, never written down here."""
    for w in range(1, pool + 1):
        if two_sided_p(w, w) <= alpha:
            return w
    return None


def headroom(rows: list[dict], key: dict[str, dict], hit_field: str = "hit@5") -> list[dict]:
    """One record per `rung × set`. **Answerable questions only.**

    ⚠ **An unanswerable question is not headroom for a RANKING change.** The
    right outcome there is an abstention, which no field weight produces;
    counting it would inflate the pool with questions the feature cannot win.
    """
    buckets: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        expected = key.get(row["id"])
        if expected is None or not expected.get("answerable"):
            continue
        buckets[(row["rung"], row["set"])].append(row)

    out = []
    for (rung, set_name), group in sorted(buckets.items()):
        pool = sum(1 for r in group if not r.get(hit_field))
        # The most favourable case: every question in the pool flips the right
        # way and nothing regresses, so discordant == pool and net == pool.
        needed = smallest_detectable(pool, ALPHA) if pool else None
        possible = needed is not None and needed <= pool
        out.append({
            "rung": rung, "set": set_name, "n": len(group),
            hit_field: len(group) - pool, "pool": pool,
            "net_if_all_flip": needed,
            "verdict_possible": bool(possible),
            # With zero losses, discordant == wins == net, so the bar is read
            # at the WINS, not at the pool (W-219).
            "min_wins": fewest_clean_wins(pool),
        })
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rows", type=Path, required=True,
                    help="per-query rows carrying `id`, `rung`, `set` and the hit field")
    ap.add_argument("--hit", default="hit@5", help="the hit field to read (default hit@5)")
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args(argv)

    stats = headroom(read_jsonl(args.rows), expectations(), args.hit)
    if not stats:
        sys.exit("refusing: no answerable rows joined. Check --rows and the retired sets.")

    print(f"{'rung':<12}{'set':<8}{'n':>5}{args.hit:>8}{'POOL':>6}{'all-flip':>9}{'min_wins':>9}  verdict possible?")
    for s in stats:
        need = s["net_if_all_flip"] if s["net_if_all_flip"] is not None else "-"
        mf = s["min_wins"] if s["min_wins"] is not None else "-"
        mark = "yes" if s["verdict_possible"] else "🔴 NO — no net clears alpha at this pool"
        print(f"{s['rung']:<12}{s['set']:<8}{s['n']:>5}{s[args.hit]:>8}"
              f"{s['pool']:>6}{need:>9}{mf:>9}  {mark}")

    worst = min(s["pool"] for s in stats)
    print(f"\nsmallest pool anywhere: {worst}")
    if any(not s["verdict_possible"] for s in stats):
        print("🔴 At least one rung x set CANNOT produce a verdict for any feature, "
              "however good — SR-RS decision 23b: a data defect, fixed in the data, never a null.")
    if args.json_out:
        args.json_out.write_text(json.dumps(stats, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
