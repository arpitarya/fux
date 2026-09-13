#!/usr/bin/env python3
"""W-143 — sweep the ranking priors against an INTENT-SPLIT probe set.

**The question, fixed by Arpit's 2026-09-11 ruling and not re-opened here:**
*does **any single global value** of a prior clear a `0 broken` bar?* It is not
*"which value is best"*. A run that answers **no** is a success — it closes the
knob and moves the work query-side — and a run designed only to find a good
value cannot report that.

## Why the probe set is split by intent, and why that is the whole design

`P-SUPERSEDE` did not fail because `0.5` was the wrong number. At `0.5` it fixed
two queries and broke two, and **every broken query had the superseded document
as its correct answer**. Supersession belongs to the **query's intent**, not to
the document: *"what do we do now?"* and *"what did we do before?"* want opposite
orderings out of one corpus, and a per-document multiplier cannot express both.

So the probe set is balanced by construction — 8 current-seeking and 8
history-seeking over the four declared supersession pairs, 5 and 5 over the
archived documents. **A set holding only current-seeking probes would clear any
bar and prove nothing**, which is the failure this file exists to make
impossible.

## The truth is mechanical — there is no answer key here

For a `supersedes:` pair, *current* means the superseder and *history* means the
retired document. For an archived document, *current* means the live one and
*history* the one under `seed/archive/`. Both come straight out of a
**declaration** — frontmatter, or an `archived=true` source line — so nothing
was judged and nothing can be fitted.

⚠ **The probe wording was written by a session that had read the documents**, so
this run is `informed` and says so. That asymmetry is worth stating precisely:
**favourable wording can manufacture a pass, and cannot manufacture a failure.**
A `0 broken` result here would need independent probes before anyone believed
it; a *"no value clears the bar"* result is robust to the bias, because the bias
pushes the other way.

## The criterion, per probe

`correct` must outrank `competitor`. Pairwise, not `hit@1`: the pair is what the
prior acts on, and an absolute metric would fold in every other reason a third
document might win.

`broken` = right at the shipped default, wrong at the candidate.
`fixed`   = wrong at the shipped default, right at the candidate.

Usage:
    python3 tools/quality-controls/priors_sweep.py --rung rung-00100 --knob rerank_weight --json rows.jsonl

🔴 **THREE OF THE FOUR SUBJECTS NO LONGER EXIST.** `superseded_weight` (W-151),
`archived_weight` and `recency_half_life_days` (W-152) were removed on
2026-09-13 — writing any of them into a `tune.toml` is a refusal now, not a
sweep. This script is kept **narrowed, not retired**, because `rerank_weight`
is still open: it is the one prior left, and W-154 restates its question as
*cost*, which this harness does not measure. **A verdict on `rerank_weight`
needs a latency fence (`fux-benchmark`) that this script has no part of** — do
not mistake a green run here for an answer to W-154.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAB = Path.home() / "my_programs" / "fux-lab" / "corpora" / "golden"
SCRATCH = Path.home() / "my_programs" / "fux-lab" / "corpora" / "golden-sweep"
FUX = ROOT / ".venv" / "bin" / "fux"
PROBES = Path(__file__).resolve().parent / "priors-probes.jsonl"

#: Shipped defaults — the baseline arm, and the value `broken` is measured against.
DEFAULTS = {"rerank_weight": 0.0}

#: The grids. A multiplier below 1.0 demotes; `0.0` is the sharp column — it
#: pushes the matched document below every other result, so a knob that moves
#: nothing at `0.0` reaches nothing at all.
GRIDS = {
    "rerank_weight": [0.0, 0.25, 0.5, 1.0, 2.0],
}


def probes() -> list[dict]:
    return [json.loads(l) for l in PROBES.read_text().splitlines() if l.strip()]


def write_tune(root: Path, knob: str, value: float) -> None:
    settings = dict(DEFAULTS)
    settings[knob] = value
    body = "[ranking]\n" + "".join(f"{k} = {v}\n" for k, v in sorted(settings.items()))
    (root / ".fux" / "tune.toml").write_text(body, encoding="utf-8")


def ranked(root: Path, query: str, top: int = 20) -> list[str]:
    p = subprocess.run([str(FUX), "ask", query, "--json", "--top", str(top)],
                       cwd=str(root), text=True, capture_output=True, check=False)
    if p.returncode != 0 or not p.stdout.strip():
        return []
    try:
        return [r.get("loc") for r in json.loads(p.stdout).get("results", [])]
    except json.JSONDecodeError:
        return []


def rank_of(order: list[str], loc: str) -> int | None:
    return order.index(loc) + 1 if loc in order else None


def arm(root: Path, knob: str, value: float, rows: list[dict]) -> list[dict]:
    write_tune(root, knob, value)
    out = []
    for pr in rows:
        order = ranked(root, pr["query"])
        rc, rw = rank_of(order, pr["correct"]), rank_of(order, pr["competitor"])
        # Absent from the window is worse than any present rank, and both
        # absent is a tie that no prior caused — scored `False`, never dropped,
        # because a dropped row is a row that cannot be re-tested later.
        if rc is None:
            right = False
        elif rw is None:
            right = True
        else:
            right = rc < rw
        out.append({**pr, "knob": knob, "value": value, "rank_correct": rc,
                    "rank_competitor": rw, "right": right})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rung", required=True)
    ap.add_argument("--knob", required=True, choices=sorted(GRIDS))
    ap.add_argument("--json")
    a = ap.parse_args()

    src = LAB / a.rung
    if not src.is_dir():
        raise SystemExit(f"no such rung: {src}")
    # 🔴 Never mutate a frozen rung. `tune.toml` does not change the index, but
    # a frozen artifact that a sweep writes into is no longer frozen, and the
    # pre-registration says so in writing.
    SCRATCH.mkdir(parents=True, exist_ok=True)
    root = SCRATCH / a.rung
    if root.exists():
        shutil.rmtree(root)
    shutil.copytree(src, root)

    rows = probes()
    grid = GRIDS[a.knob]
    base_value = DEFAULTS[a.knob]
    assert grid[0] == base_value, "the first grid point must be the shipped default"

    all_rows: list[dict] = []
    baseline = arm(root, a.knob, base_value, rows)
    all_rows += baseline
    base_right = {r["id"]: r["right"] for r in baseline}

    n = len(rows)
    print(f"rung {a.rung}   knob {a.knob}   probes {n} "
          f"({sum(1 for r in rows if r['intent']=='current')} current / "
          f"{sum(1 for r in rows if r['intent']=='history')} history)")
    print(f"baseline at the shipped default {base_value}: "
          f"{sum(base_right.values())} / {n} right")
    print()
    print(f"{'value':>8}  {'right':>7}  {'fixed':>5}  {'broken':>6}  "
          f"{'cur':>7}  {'hist':>7}   verdict")

    headroom_up = n - sum(base_right.values())
    headroom_down = sum(base_right.values())
    results = []
    for value in grid:
        rows_v = baseline if value == base_value else arm(root, a.knob, value, rows)
        if value != base_value:
            all_rows += rows_v
        right = {r["id"]: r["right"] for r in rows_v}
        fixed = [i for i in right if right[i] and not base_right[i]]
        broken = [i for i in right if base_right[i] and not right[i]]
        cur = [r for r in rows_v if r["intent"] == "current"]
        hist = [r for r in rows_v if r["intent"] == "history"]
        verdict = ("baseline" if value == base_value
                   else "CLEARS 0 broken" if not broken and fixed
                   else "0 broken, 0 fixed — no effect" if not broken
                   else f"BREAKS {len(broken)}: {' '.join(broken)}")
        print(f"{value:>8}  {sum(right.values()):>3} /{n:>3}  {len(fixed):>5}  "
              f"{len(broken):>6}  {sum(1 for r in cur if r['right']):>3} /{len(cur):>3}  "
              f"{sum(1 for r in hist if r['right']):>3} /{len(hist):>3}   {verdict}")
        results.append({"value": value, "fixed": fixed, "broken": broken})

    print()
    print(f"HEADROOM, observed, from the rows (SR-RS decision 22b):")
    print(f"  improvement — probes not right at the default: {headroom_up} / {n}")
    print(f"  regression  — probes right at the default:     {headroom_down} / {n}")
    if headroom_up == 0:
        print("  🔴 zero improvement headroom → Inconclusive in that direction, "
              "never 'no detected change' (22d).")

    clears = [r for r in results if r["value"] != base_value and not r["broken"] and r["fixed"]]
    print()
    if clears:
        print("🟢 value(s) clearing the 0-broken bar WITH a fix: "
              + ", ".join(str(r["value"]) for r in clears))
    else:
        moved = any(r["fixed"] or r["broken"] for r in results if r["value"] != base_value)
        if not moved:
            print("🔴 NO value moved a single probe in either direction — the knob "
                  "does not reach this corpus. Inconclusive, not a null.")
        else:
            print("🔴 NO single global value clears the 0-broken bar. Every value "
                  "that fixes a probe breaks another, which is the pre-registered "
                  "answer NO — and it is a result, not a failed run.")

    if a.json:
        Path(a.json).write_text("".join(json.dumps(r) + "\n" for r in all_rows),
                                encoding="utf-8")
        print(f"\nper-probe rows ({len(all_rows)}) -> {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
