#!/usr/bin/env python3
"""What each authority-prior arm DID on `set-4-claude` — descriptive only, from the hand-offs.

🔴 **No correctness column, and there cannot be one.** It reads the captured
hand-offs (what fux ranked, its band, its funnel gates, its timings) and the
frozen tags. It opens no key and no score. *Moved* here means **the ranking
changed**, never that it got better or worse. That word is Arpit's scorer's,
and the decision belongs to a session that did not capture these arms.

It also checks the bar's precondition: the `au-0.0` arm must rank all 125
questions identically to the `ip-0.1` hand-off the tag was computed from
(sha256 `6207c88e…`), and it lists any id that moved.

    python3 work/regression/2026-09-28-authority-prior/evidence/describe.py
"""

from __future__ import annotations

import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARMS = ("au-0.0", "au-0.1", "au-0.2", "au-0.3", "au-0.5")
BASELINE = ARMS[0]
REFERENCE = HERE.parents[1] / "2026-09-28-intent-prior" / "evidence" / "ip-0.1" / "rung-01000" / "handoff-set-4-claude.jsonl"
REFERENCE_SHA = "6207c88e32a9946693b3f685525db80efc0371ae845029bc9a3453202a445de6"
HANDOFF = "handoff-set-4-claude.jsonl"


def _load(path: Path) -> dict[str, dict]:
    return {r["id"]: r for r in map(json.loads, path.read_text(encoding="utf-8").splitlines()) if r}


def rows(arm: str) -> dict[str, dict]:
    return _load(HERE / arm / "rung-01000" / HANDOFF)


def precondition(base: dict[str, dict]) -> dict:
    sha = hashlib.sha256(REFERENCE.read_bytes()).hexdigest()
    ref = _load(REFERENCE)
    assert set(ref) == set(base), "the reference and au-0.0 name different ids"
    moved = sorted(i for i in base if base[i]["ranked"] != ref[i]["ranked"])
    band_moved = sorted(i for i in base if base[i]["band"] != ref[i]["band"])
    return {
        "reference": REFERENCE.relative_to(HERE.parents[2]).as_posix(),
        "reference_sha256": sha,
        "reference_sha256_is_the_frozen_one": sha == REFERENCE_SHA,
        "n": len(base),
        "ranked_identical": len(base) - len(moved),
        "moved_ids": moved,
        "band_identical": len(base) - len(band_moved),
        "band_moved_ids": band_moved,
    }


def main() -> int:
    tagged = {r["id"] for r in map(json.loads, (HERE / "tags-set-4-claude.jsonl").read_text(encoding="utf-8").splitlines()) if r}
    base = rows(BASELINE)
    tags = {i: i in tagged for i in base}
    out: dict = {"precondition": precondition(base), "arms": {}}
    for arm in ARMS:
        r = rows(arm)
        assert set(r) == set(base) == set(tags), f"{arm}: ids differ"
        top1 = [i for i in r if (r[i]["ranked"] or [None])[0] != (base[i]["ranked"] or [None])[0]]
        order = [i for i in r if r[i]["ranked"] != base[i]["ranked"]]
        members = [i for i in r if set(r[i]["ranked"]) != set(base[i]["ranked"])]
        out["arms"][arm] = {
            "n": len(r),
            "engine_commits": sorted({x["engine_commit"] for x in r.values()}),
            "bands": dict(sorted(Counter(x["band"] for x in r.values()).items())),
            "gates_captured": sum(1 for x in r.values() if x.get("gates")),
            "top1_changed_vs_baseline": {"all": len(top1), "tagged": sum(tags[i] for i in top1)},
            "top1_changed_ids": sorted(top1),
            "order_changed_vs_baseline": len(order),
            "membership_changed_vs_baseline": len(members),
            "ask_ms_median": round(statistics.median(x["ask_ms"] for x in r.values()), 1),
        }
    (HERE / "describe.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    p = out["precondition"]
    print(f"precondition: reference sha256 {p['reference_sha256'][:8]}… frozen={p['reference_sha256_is_the_frozen_one']}; "
          f"ranked identical {p['ranked_identical']}/{p['n']}, moved {p['moved_ids']}; "
          f"band identical {p['band_identical']}/{p['n']}, moved {p['band_moved_ids']}")
    print(f"{'arm':<9}{'top1Δ':>7}{'tagged':>8}{'orderΔ':>8}{'setΔ':>6}{'gates':>7}{'ask ms':>8}  bands")
    for arm, a in out["arms"].items():
        print(f"{arm:<9}{a['top1_changed_vs_baseline']['all']:>7}{a['top1_changed_vs_baseline']['tagged']:>8}"
              f"{a['order_changed_vs_baseline']:>8}{a['membership_changed_vs_baseline']:>6}"
              f"{a['gates_captured']:>7}{a['ask_ms_median']:>8}  {a['bands']}  {a['engine_commits']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
