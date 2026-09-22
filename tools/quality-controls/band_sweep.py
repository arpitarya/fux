#!/usr/bin/env python3
"""W-213 — the confidence band's operating point, swept as a REPLAY.

**What this is.** [W-204 phase D](../../work/regression/2026-09-22-golden-final-score/FINAL-SCORE.md)
measured what fux's abstention **costs** — 818 withholds of 2 992, 747 of them on
questions the key says were answerable — and measured no benefit at all. This
tool prices the other half and decides whether `[confidence] separation_floor`
moves, against the frozen bar in
[`PRE-REGISTRATION.md`](../../work/regression/2026-09-22-band-operating-point/PRE-REGISTRATION.md).

🔴 **READ THIS BEFORE READING A NUMBER FROM IT: the abstention this tool
measures is NOT the engine's any more.** W-213's result *was* the argument that
retired it — Arpit ruled on 2026-09-22 ([W-214](../../work/open/W-214-separation-does-not-carry-correctness.md))
that `weak` is a published signal and not a refusal, so `Confidence.answerable`
is `band != none` from that day on. The sweep keeps the pre-W-214 rule in one
named function, `withheld_under_the_separation_gate`, so **W-213's filed
numbers remain reproducible from the captures that produced them** — and so
that nothing here silently reports a separation abstention fux no longer makes.
**Every number this tool prints describes the old semantics.**

🔴 **The sweep is a replay, not seven runs.** `Confidence.band` is a **pure
function** of `support`, `missing`, `verified`, `doc_coverage`,
`doc_coverage_floor`, `separation` and `separation_floor`, and `as_dict()` emits
every one of them. So `capture` runs the ladder **once**, storing the whole
confidence block per question, and `sweep` re-evaluates the band at each
candidate floor by **constructing the engine's own `Confidence`** with a
different floor.

⚠ **It imports `fux.query.confidence` and `tools/golden-score/score.py` rather
than reimplementing either.** A second copy of the band policy, or of the
evidence proxy, in a measurement tool is the restatement
[SR-LAW-0](../../records/0002_LAW-0-authority.md) decision 1 forbids by its own
test: the tool and the engine could disagree while both looked correct, and the
disagreement would read as a result.

## What it reads, and why that is allowed

**`work/golden/retired/set-N/`** — questions *and* expected values. Those sets
retired on 2026-09-22 under [L11](../../records/0012_LAW-11-sealed-answer-key.md)
decision 14 and are **open regression data any session may read in any state**.
🔴 **It opens no sealed key, on either spelling, and needs no unlock.** The only
path under `work/golden/` it touches is `retired/`.

🔴 **Every number it produces is `informed` permanently** — three ways over: L11
decision 14, sets 2 and 3 being Claude-authored, and the data being open to the
session that tunes against it. Retiring changes what the data is **for**, not
what it has seen.

## The endpoint

SR-WORK-QUALITY decision 6's published cost model at `c = 2`: a correct answer
`+1`, a decline `0`, a wrong answer `−2`. **`correct` is the named proxy
`evidence_quoted`**, never a judgement — and the proxy's bias has a direction,
declared in the pre-registration before any number existed: a substring test
**under-detects** correct answers, so *raise the floor* is the result this
instrument favours and *lower the floor* is the conservative one.

    python3 tools/quality-controls/band_sweep.py capture --arm w213-head --out <evidence dir>
    python3 tools/quality-controls/band_sweep.py sweep --evidence <evidence dir> --primary-rung rung-01000
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from fux.query.confidence import NONE, WEAK, Confidence  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verdict import ALPHA, FLOOR_OF_ALL_FLOORS, rule  # noqa: E402,F401


RETIRED = ROOT / "work" / "golden" / "retired"
RUNS = Path.home() / "my_programs" / "fux-lab" / "arms" / "runs"

#: The ladder, smallest first. Named here rather than globbed so a missing rung
#: is a refusal and not a quietly shorter run — SR-RS decision 24's rule.
RUNGS = ("rung-seed", "rung-00100", "rung-00200", "rung-00500",
         "rung-01000", "rung-02000", "rung-05000", "rung-10000")

SETS = (1, 2, 3)

#: The grid, incumbent included so the replay recomputes it rather than trusting
#: the run's own flag — if the reconstruction disagrees with what the engine
#: emitted, the instrument is wrong and says so.
INCUMBENT = 0.10
GRID = (0.00, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30)

#: SR-WORK-QUALITY decision 6: `t = 0.75` → `c = t/(1-t) = 2`. Frozen before any
#: score in this project existed. **This file does not choose it and may not.**
COST_C = 2.0


def _load_scorer():
    """`score.py`'s `score_one`, by path — `tools/` is not a package.

    ⚠ **Importing is not invoking** (L11 decision 13): what is reserved to
    Arpit's hand is *running the program* against the sealed key. This reads
    retired data and calls one pure function, exactly as `phase_d.py` does.
    """
    path = ROOT / "tools" / "golden-score" / "score.py"
    spec = importlib.util.spec_from_file_location("golden_score", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["golden_score"] = module
    spec.loader.exec_module(module)
    return module


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


# --- capture -----------------------------------------------------------------

def call(tree: Path, *args: str) -> tuple[dict | None, float]:
    cmd = [sys.executable, "-m", "fux.cli", *args]
    t0 = time.perf_counter()
    out = subprocess.run(cmd, cwd=tree, capture_output=True, text=True)
    ms = (time.perf_counter() - t0) * 1000.0
    try:
        return json.loads(out.stdout), ms
    except Exception:
        return None, ms


def capture_one(tree: Path, question: dict) -> dict:
    """One question's whole decision surface, in one pass.

    🔴 **The FULL confidence block, not `band` and `answerable`.** Those two are
    the band's *output*; the sweep needs its *inputs*, and a capture that stored
    only the verdict could not replay anything. This is the field W-204 phase A
    did not keep and the reason this run exists at all.
    """
    asked, ask_ms = call(tree, "ask", question["question"], "--json", "--band", "--why", "--top", "10")
    answered, ans_ms = call(tree, "answer", question["question"], "--json")

    results = (asked or {}).get("results") or []
    payload = (answered or {}).get("answer") or {}
    passages = payload.get("passages") or []
    if passages:
        answer_text = "\n\n".join(p.get("text", "") for p in passages)
    elif payload:
        answer_text = "\n".join(payload.get("phrases") or []) or (payload.get("title") or "")
    else:
        answer_text = ""

    return {
        "id": question["id"],
        "ranked": [r.get("loc") for r in results],
        "answer_text": answer_text,
        # The whole block — `band` and `answerable` included, so the sweep's
        # self-check can prove the replay reproduces what the engine said.
        "confidence": (asked or {}).get("confidence"),
        "gates": ((asked or {}).get("derivation") or {}).get("gates"),
        "ask_ms": round(ask_ms, 1),
        "answer_ms": round(ans_ms, 1),
    }


def capture(arm: str, out: Path, rungs: tuple[str, ...], sets: tuple[int, ...]) -> int:
    for rung in rungs:
        tree = RUNS / arm / rung
        if not (tree / ".fux" / "index").is_dir():
            print(f"no index at {tree} — build it with arm_corpus.py first", file=sys.stderr)
            return 1
        dest = out / rung
        dest.mkdir(parents=True, exist_ok=True)
        for n in sets:
            questions = read_jsonl(RETIRED / f"set-{n}" / "questions.jsonl")
            rows = []
            for i, q in enumerate(questions, 1):
                rows.append(capture_one(tree, q))
                if i % 50 == 0:
                    print(f"  {rung} set-{n}: {i}/{len(questions)}", flush=True)
            path = dest / f"capture-set-{n}.jsonl"
            path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n",
                            encoding="utf-8")
            blank = sum(1 for r in rows if r["confidence"] is None)
            gated = sum(1 for r in rows if r["gates"])
            print(f"{path}  ({len(rows)} rows, {blank} with no confidence block, "
                  f"{gated} with funnel gates)", flush=True)
    return 0


# --- the replay --------------------------------------------------------------

def replay(block: dict, floor: float) -> Confidence:
    """The engine's own band rule, at a different floor. **Reconstructed, never
    reimplemented** — every field below is one `as_dict()` emits."""
    return Confidence(
        coverage=block["coverage"],
        separation=block["separation"],
        support=block["support"],
        verified=block["verified"],
        missing=tuple(block.get("missing") or ()),
        doc_coverage=block["doc_coverage"],
        separation_floor=floor,
        doc_coverage_floor=block["doc_coverage_floor"],
    )


def withheld_under_the_separation_gate(conf: Confidence) -> bool:
    """Did the band withhold this answer, **under the rule W-213 measured**?

    🔴 **That rule is no longer the engine's.** W-213's result was the reason
    Arpit ruled on 2026-09-22 (W-214) that `weak` is a signal and not a
    refusal, so `Confidence.answerable` is `band != none` from that day on and
    reading it here would report every row as answered and every sweep as a
    no-op.

    **This function is therefore a dated statement, not a copy of live policy**
    — it names the pre-W-214 abstention so W-213's filed numbers stay
    reproducible from the captures that produced them. It is the one place in
    this tool that does **not** defer to the engine, and it says why rather
    than looking like an oversight.

    ⚠ **Anything computed through it describes the OLD semantics.** A report
    built on it says so; it is not a measurement of what fux does today, and a
    new operating-point question needs a new instrument, not this one.
    """
    return conf.band in (NONE, WEAK)


def utility(answered: bool, quoted: bool) -> float:
    """SR-WORK-QUALITY decision 6, at the frozen `c = 2`. **Not chosen here.**"""
    if not answered:
        return 0.0
    return 1.0 if quoted else -COST_C


def sweep(evidence: Path, primary_rung: str, rungs: tuple[str, ...],
          sets: tuple[int, ...], selfcheck: bool = True) -> tuple[list[dict], list[dict], list[str]]:
    scorer = _load_scorer()
    per_query: list[dict] = []
    problems: list[str] = []

    for rung in rungs:
        for n in sets:
            path = evidence / rung / f"capture-set-{n}.jsonl"
            if not path.is_file():
                problems.append(f"missing {path}")
                continue
            rows = {r["id"]: r for r in read_jsonl(path)}
            key = {r["id"]: r for r in read_jsonl(RETIRED / f"set-{n}" / "expected.jsonl")}

            # 🔴 A row with no key line, or a key line with no row, is an ERROR
            # and not a skip — phase D's rule, and the reason its join was
            # trustworthy. A partial sweep that looked whole would pick a floor.
            for missing in sorted(set(rows) - set(key)):
                problems.append(f"{rung}/set-{n}: row {missing} has no key line")
            for missing in sorted(set(key) - set(rows)):
                problems.append(f"{rung}/set-{n}: key line {missing} has no row")

            for qid in sorted(rows.keys() & key.keys()):
                row, expected = rows[qid], key[qid]
                block = row.get("confidence")
                if not block:
                    problems.append(f"{rung}/set-{n}/{qid}: no confidence block — the call failed")
                    continue

                # ⚠ `score_one` reads `row["answerable"]` for its abstention
                # counts, and a capture row carries the flag inside the block.
                # Handing it over keeps every field of the scored row coherent
                # **at the incumbent floor**; the sweep reads only
                # `evidence_quoted` and `hit@5`, neither of which depends on it.
                scored = scorer.score_one({**row, "answerable": block["answerable"]}, expected)
                quoted = bool(scored["evidence_quoted"])
                out = {
                    "id": qid, "rung": rung, "set": f"set-{n}",
                    "evidence_quoted": quoted,
                    "hit@5": bool(scored["hit@5"]),
                    "separation": block["separation"],
                    "engine_band": block["band"],
                    "engine_answerable": block["answerable"],
                }
                for floor in GRID:
                    conf = replay(block, floor)
                    answered = not withheld_under_the_separation_gate(conf)
                    out[f"answerable@{floor:.2f}"] = answered
                    out[f"u@{floor:.2f}"] = utility(answered, quoted)
                # 🔴 The self-check compares the **band**, not `answerable`.
                # The band is what the replay reconstructs and it means the same
                # thing before and after W-214; `answerable` does not, so a
                # capture taken after that ruling would fail a comparison on it
                # for a reason that is not an instrument fault.
                if selfcheck and replay(block, INCUMBENT).band != block["band"]:
                    problems.append(
                        f"{rung}/set-{n}/{qid}: REPLAY DISAGREES WITH THE ENGINE at the "
                        f"incumbent floor — replay {replay(block, INCUMBENT).band}, "
                        f"engine {block['band']}. The instrument is wrong, not the engine."
                    )
                per_query.append(out)

    # --- the paired test, per set, at the primary rung only ------------------
    results: list[dict] = []
    buckets: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in per_query:
        buckets[(row["rung"], row["set"])].append(row)

    for (rung, set_name), group in sorted(buckets.items()):
        base = f"u@{INCUMBENT:.2f}"
        answered_base = sum(1 for r in group if r[f"answerable@{INCUMBENT:.2f}"])
        # SR-RS decision 22b, both directions, observed.
        head_improve = sum(1 for r in group
                           if (r[f"answerable@{INCUMBENT:.2f}"] and not r["evidence_quoted"])
                           or (not r[f"answerable@{INCUMBENT:.2f}"] and r["evidence_quoted"]))
        head_regress = sum(1 for r in group
                           if (r[f"answerable@{INCUMBENT:.2f}"] and r["evidence_quoted"])
                           or (not r[f"answerable@{INCUMBENT:.2f}"] and not r["evidence_quoted"]))
        for floor in GRID:
            if floor == INCUMBENT:
                continue
            cand = f"u@{floor:.2f}"
            b = sum(1 for r in group if r[cand] > r[base])
            c = sum(1 for r in group if r[cand] < r[base])
            # 🔴 ADJUDICATED BY `verdict.py`, never by an `if` in this file.
            # Three instruments landed on 2026-09-12 each about to hard-code
            # *"net >= 6"*, and SR-RS decision 19's real bar RISES with the
            # flips: a net of 8 on 30 discordant pairs passes 6 and fails the
            # table. `verdict.rule` is the one seam that applies it.
            # ⚠ **`candidate-better`, not `lower-floor-better`.** The grid runs
            # in BOTH directions around the incumbent, so a label naming one of
            # them would read backwards on half the rows — and a reader taking
            # `lower-floor-better` at face value on a floor of 0.30 would invert
            # the finding. Caught before any number was read.
            v = rule(b, c, better="candidate-better", worse="incumbent-better")
            results.append({
                "rung": rung, "set": set_name, "floor": floor, "n": len(group),
                "adjudicates": rung == primary_rung,
                "utility_incumbent": sum(r[base] for r in group),
                "utility_candidate": sum(r[cand] for r in group),
                "answered_incumbent": answered_base,
                "answered_candidate": sum(1 for r in group if r[f"answerable@{floor:.2f}"]),
                # SR-WORK-QUALITY decision 8: the risk-coverage curve is
                # reported BESIDE the scalar, never instead of it, so the
                # abstention trade stays visible rather than baked into one
                # number. These two columns are that curve, one point per floor.
                "answered_quoted_candidate": sum(
                    1 for r in group if r[f"answerable@{floor:.2f}"] and r["evidence_quoted"]),
                "improved": b, "worsened": c, "discordant": v["discordant"],
                "net": b - c, "p": v["p"], "net_needed": v["net_needed"],
                "outcome": v["outcome"],
                # Clearing means the exact test cleared alpha. **The floor of
                # all floors is implied, not re-applied**: nets of 1-5 clear
                # alpha at no discordant count, so a second `net >= 6` check
                # here would be the hard-coded bar `verdict.py` exists to stop.
                "clears_floor": v["outcome"] not in ("inconclusive", "no detected change"),
                "headroom_improvement": head_improve,
                "headroom_regression": head_regress,
            })
    return per_query, results, problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    cap = sub.add_parser("capture", help="run the ladder once, storing the full confidence block")
    cap.add_argument("--arm", required=True, help="the arm tree under fux-lab/arms/runs/")
    cap.add_argument("--out", type=Path, required=True)
    cap.add_argument("--rungs", default=",".join(RUNGS))
    cap.add_argument("--sets", default="1,2,3")

    swp = sub.add_parser("sweep", help="replay the band at every candidate floor")
    swp.add_argument("--evidence", type=Path, required=True)
    swp.add_argument("--primary-rung", default="rung-01000")
    swp.add_argument("--rungs", default=",".join(RUNGS))
    swp.add_argument("--sets", default="1,2,3")

    args = ap.parse_args(argv)
    rungs = tuple(r.strip() for r in args.rungs.split(",") if r.strip())
    sets = tuple(int(n) for n in args.sets.split(",") if n.strip())

    if args.cmd == "capture":
        return capture(args.arm, args.out, rungs, sets)

    per_query, results, problems = sweep(args.evidence, args.primary_rung, rungs, sets)
    if not per_query:
        sys.exit("refusing: nothing captured. Run `capture` first.")

    out = args.evidence
    with (out / "per-query.jsonl").open("w", encoding="utf-8") as fh:
        for row in per_query:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    (out / "sweep.json").write_text(json.dumps(results, indent=1, sort_keys=True) + "\n",
                                    encoding="utf-8")
    if problems:
        (out / "PROBLEMS.txt").write_text("\n".join(problems) + "\n", encoding="utf-8")

    print(f"{len(per_query)} per-query row(s); {len(results)} (rung x set x floor) comparison(s)")
    print(f"problems: {len(problems)}" + (" — see PROBLEMS.txt" if problems else ""))
    print(f"\nPRIMARY RUNG {args.primary_rung} — the only rows that adjudicate:")
    print(f"{'set':8}{'floor':>7}{'answered':>10}{'utility':>10}"
          f"{'b':>5}{'c':>5}{'net':>6}{'p':>10}  clears")
    for r in results:
        if not r["adjudicates"]:
            continue
        print(f"{r['set']:8}{r['floor']:>7.2f}{r['answered_candidate']:>10}"
              f"{r['utility_candidate']:>10.0f}{r['improved']:>5}{r['worsened']:>5}"
              f"{r['net']:>6}{r['p']:>10.4f}  {'YES' if r['clears_floor'] else '-'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
