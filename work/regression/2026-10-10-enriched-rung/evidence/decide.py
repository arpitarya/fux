#!/usr/bin/env python3
"""W-257 — apply the frozen B-108 and B-109 tables (PRE-REGISTRATION.md). Mechanical.

Written 2026-10-10 **before any arm was scored**. B-110 is `tilt.py`'s, and
this file does not restate it. Reads Arpit's score files only — ids, booleans
and counts (L11 decision 13). It opens no key and runs no scorer.

- **G2** — headroom from the `none` arm: improvement = answerable questions
  that miss rank 1 (counts: n − hit@1 − unanswerable), regression = rank-1
  hits. Below 6 in a direction makes that direction INCONCLUSIVE.
- **G3** — first-pass refusal share, from `check-first-pass.txt`, ≥ 10 %.
- **B-108** — `unfiltered` vs `none` on `hit@1`, with `placebo` vs `none` as
  the control; `filtered` vs `none` reported beside, gating nothing.
- **B-109** — `filtered` vs `unfiltered`.

Every bar is `verdict.rule` at the observed discordant count (SR-RS d19, d19a).

⚠ **The session that captured the arms may not run this to adjudicate them**
(rule 6). It writes `decision.json` and prints each table's outcome.

    python3 work/regression/2026-10-10-enriched-rung/evidence/decide.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "tools" / "quality-controls"))

from verdict import line, rule  # noqa: E402

RUNG, SET = "rung-01000", "set-5-claude"
ARMS = ("none", "declared", "unfiltered", "filtered", "placebo", "cov-25", "cov-50")
FLOOR = 6
G3_SHARE = 0.10
QUESTIONS_WRITTEN = 5620  # the author's count, re-counted from the files in GATES.md


def scores(arm: str) -> dict:
    path = RUN / "scores" / arm / RUNG / f"{SET}.json"
    if not path.is_file():
        sys.exit(f"refusing: {path} is not scored yet — Arpit runs `just golden-score {RUN.relative_to(ROOT)}`")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("partial"):
        sys.exit(f"refusing: {path} is a PARTIAL score")
    payload["by_id"] = {r["id"]: r for r in payload["rows"]}
    return payload


def flips(base: dict, arm: dict, field: str = "hit@1") -> tuple[int, int]:
    """(wins, losses) of `arm` over `base` on a boolean `field`."""
    ids = sorted(base)
    if set(ids) != set(arm):
        sys.exit("refusing: two arms disagree on ids")
    return (sum(1 for i in ids if arm[i][field] and not base[i][field]),
            sum(1 for i in ids if base[i][field] and not arm[i][field]))


def headroom(payload: dict) -> dict:
    t = payload["totals"]
    unanswerable = t["answered_unanswerable"] + t["abstain_correct"]
    return {"improvement": payload["n"] - t["hit@1"] - unanswerable, "regression": t["hit@1"]}


def table(v: dict, room: dict, *, gain: str, loss: str) -> str:
    """The shared shape of both tables: gain/loss clears, else NO DETECTED
    CHANGE with headroom both ways, else INCONCLUSIVE."""
    if room["improvement"] < FLOOR or room["regression"] < FLOOR:
        return "INCONCLUSIVE → Arpit (G2 headroom below 6 in a direction)"
    if v["outcome"] == "treatment":
        return gain
    if v["outcome"] == "baseline":
        return loss
    if v["outcome"] == "no detected change":
        return "NO DETECTED CHANGE"
    return "INCONCLUSIVE → Arpit"


def main() -> int:
    p = {a: scores(a) for a in ARMS}
    by = {a: p[a]["by_id"] for a in ARMS}
    out: dict = {"totals": {a: p[a]["totals"] for a in ARMS}}

    room = headroom(p["none"])
    out["G2"] = room
    refused = sum(1 for l in (HERE / "check-first-pass.txt").read_text(encoding="utf-8").splitlines()
                  if re.match(r"^\s+refused:", l))
    share = refused / QUESTIONS_WRITTEN
    out["G3"] = {"refused": refused, "written": QUESTIONS_WRITTEN, "share": round(share, 4), "passes": share >= G3_SHARE}

    def paired(treat: str, base: str) -> dict:
        w, l = flips(by[base], by[treat])
        v = rule(w, l, better="treatment", worse="baseline")
        beside = {f: flips(by[base], by[treat], f) for f in ("hit@5", "hit@10", "evidence_quoted")}
        pw = sum(1 for i in by[base] if by[treat][i]["primary_rank"] == 1 and by[base][i]["primary_rank"] != 1)
        pl = sum(1 for i in by[base] if by[base][i]["primary_rank"] == 1 and by[treat][i]["primary_rank"] != 1)
        beside["primary@1"] = (pw, pl)
        return {"verdict": v, "line": line(v), "beside_wins_losses": beside}

    main_ = paired("unfiltered", "none")
    plac = paired("placebo", "none")
    filt_none = paired("filtered", "none")
    b108 = table(main_["verdict"], room, gain="PASS", loss="FAIL: hurts")
    if plac["verdict"]["outcome"] == "treatment":
        # The table's first INCONCLUSIVE row, whatever the main pair did.
        b108 = "INCONCLUSIVE → Arpit (placebo clears: the gain may be presence of text)"
    out["B-108"] = {"unfiltered_vs_none": main_, "placebo_vs_none": plac,
                    "filtered_vs_none (beside)": filt_none, "outcome": b108}

    room_u = headroom(p["unfiltered"])  # B-109's baseline arm is unfiltered (d22f)
    b109_pair = paired("filtered", "unfiltered")
    if not out["G3"]["passes"]:
        b109 = "TOO SMALL TO SEE"
    else:
        b109 = table(b109_pair["verdict"], room_u, gain="FILTER HELPS", loss="FILTER HURTS")
    out["B-109"] = {"filtered_vs_unfiltered": b109_pair, "headroom": room_u, "outcome": b109}

    out["B-245_second_condition_met"] = not b108.startswith("INCONCLUSIVE")
    for name in ("B-108", "B-109"):
        print(f"{name}: {out[name]['outcome']}")
    print(f"  unfiltered vs none: {main_['line']}\n  placebo vs none:    {plac['line']}\n"
          f"  filtered vs none:   {filt_none['line']} (beside)\n  filtered vs unfilt: {b109_pair['line']}")
    print(f"G2 {room} · G3 {out['G3']}")
    (HERE / "decision.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
