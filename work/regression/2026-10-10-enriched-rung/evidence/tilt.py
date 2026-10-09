#!/usr/bin/env python3
"""W-257 — B-110, the tilt. Implements PRE-REGISTRATION.md §B-110 and nothing else.

Written 2026-10-10 **before any arm was scored**; its sha256 goes in the report.
It reads harness hand-offs (what fux ranked, no key) and Arpit's score files
(ids, booleans and counts, what L11 decision 13 lets a session read). It opens
no key and runs no scorer. 🔴 **It prints counts only, never a document name
next to a hit.**

Two jobs, one definition of the subsets:

- `subsets(enrich_dir)` — every document with a file in `unfiltered`, ordered
  by `sha256(loc as UTF-8)` ascending; `S_c` is the first `ceil(c/100 · n)`.
  `build_arms.py` imports it, so the arms and this table cannot disagree.
- `main()` — for `c` in 25, 50: `Q_out(c)` is the questions whose rank-1
  document in the `none` arm is not in `S_c`. On `Q_out(c)`, `cov-c` is paired
  with `cov-100` (= `unfiltered`) on `hit@1`. A loss hits under full coverage
  and misses under partial. `verdict.rule` at the observed discordant count.

⚠ **The session that captured the arms may not run this to adjudicate them**
(rule 6). It writes `tilt.json` and prints the table's outcome per `c`.

    python3 work/regression/2026-10-10-enriched-rung/evidence/tilt.py
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "tools" / "quality-controls"))

RUNG, SET = "rung-01000", "set-5-claude"
UNFILTERED = Path.home() / "my_programs" / "fux-lab" / "arms" / "runs" / "w257" / "unfiltered" / ".fux" / "enrich"
COVERAGES = (25, 50)
FLOOR = 6  # |Q_out(c)| < 6 is INCONCLUSIVE (the B-110 table)


def source_of(path: Path) -> str:
    """The `source:` value in an enrichment file's frontmatter: the loc."""
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        if line == "---":
            break
        if line.startswith("source:"):
            return line.split(":", 1)[1].strip()
    raise SystemExit(f"refusing: {path} names no source")


def subsets(enrich_dir: Path = UNFILTERED) -> dict[int, set[str]]:
    locs = sorted((source_of(p) for p in enrich_dir.glob("*.md")),
                  key=lambda loc: hashlib.sha256(loc.encode("utf-8")).hexdigest())
    return {c: set(locs[: math.ceil(c / 100 * len(locs))]) for c in COVERAGES}


def rank1(arm: str) -> dict[str, str]:
    path = RUN / "evidence" / arm / RUNG / f"handoff-{SET}.jsonl"
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    return {r["id"]: (r["ranked"][0] if r["ranked"] else "") for r in rows}


def scored(arm: str) -> dict[str, dict]:
    path = RUN / "scores" / arm / RUNG / f"{SET}.json"
    if not path.is_file():
        sys.exit(f"refusing: {path} is not scored yet — Arpit runs `just golden-score {RUN.relative_to(ROOT)}`")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("partial"):
        sys.exit(f"refusing: {path} is a PARTIAL score")
    return {r["id"]: r for r in payload["rows"]}


def main() -> int:
    from verdict import line, rule

    s = subsets()
    n_docs = len(list(UNFILTERED.glob("*.md")))
    none_top = rank1("none")
    full = scored("unfiltered")
    out: dict = {"n_documents": n_docs, "coverages": {}}
    for c in COVERAGES:
        part = scored(f"cov-{c}")
        q_out = sorted(i for i, loc in none_top.items() if loc not in s[c])
        if set(part) != set(full):
            sys.exit(f"refusing: cov-{c} and unfiltered disagree on ids")
        wins = sum(1 for i in q_out if part[i]["hit@1"] and not full[i]["hit@1"])
        losses = sum(1 for i in q_out if full[i]["hit@1"] and not part[i]["hit@1"])
        # Headroom on Q_out from the comparison's baseline, cov-100 (SR-RS d22f).
        # An unanswerable question can never hit, so it is not improvement room.
        improvement = sum(1 for i in q_out if not full[i]["hit@1"]
                          and not (full[i]["answered_unanswerable"] or full[i]["abstain_correct"]))
        regression = sum(1 for i in q_out if full[i]["hit@1"])
        v = rule(losses, wins, better="tilt", worse="reverse tilt")
        if len(q_out) < FLOOR or improvement == 0 or regression == 0:
            outcome = "INCONCLUSIVE → Arpit"
        elif v["outcome"] == "tilt":
            outcome = "TILT"
        elif v["outcome"] == "no detected change":
            outcome = "NO DETECTED TILT"
        else:
            outcome = "INCONCLUSIVE → Arpit"  # anything the table does not name
        # Reported beside, gating nothing: the share of the 90 rank-1 documents in S_c.
        part_top = rank1(f"cov-{c}")
        out["coverages"][c] = {
            "S_c": len(s[c]), "share_of_corpus": round(len(s[c]) / n_docs, 4),
            "Q_out": len(q_out), "losses": losses, "wins": wins,
            "headroom": {"improvement": improvement, "regression": regression},
            "verdict": v, "line": line(v), "outcome": outcome,
            "rank1_in_S_c": {"none": sum(1 for loc in none_top.values() if loc in s[c]),
                             f"cov-{c}": sum(1 for loc in part_top.values() if loc in s[c])},
        }
        print(f"B-110 c={c}: |S_c|={len(s[c])} |Q_out|={len(q_out)} {line(v)} => {outcome}")
    d6 = all(out["coverages"][c]["outcome"] == "NO DETECTED TILT" for c in COVERAGES)
    out["d6_condition_met"] = d6
    print(f"main d6 condition (NO DETECTED TILT at 25 and 50): {'MET' if d6 else 'NOT MET'}")
    (HERE / "tilt.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
