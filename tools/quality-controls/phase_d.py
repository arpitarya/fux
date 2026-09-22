#!/usr/bin/env python3
"""W-204 phase D — score every filed hand-off against the key, and aggregate.

**What this is.** The scoring pass W-204 phase D describes: join each hand-off
to its key on `id`, score every question, and roll the rows up per **rung × set
× arm** so `FINAL-SCORE.md` can be written from data rather than from prose.

🔴 **It imports [`tools/golden-score/score.py`](../golden-score/score.py) rather
than reimplementing it**, and that is the whole reason this file is short.
`score_one` is the per-question arithmetic — `hit@k`, `primary_rank`, the
abstention counts, the evidence proxy — and a second copy of it would be two
scorers that can disagree while both look correct, which is the restatement
[SR-LAW-0](../../records/0002_LAW-0-authority.md) decision 1 forbids by its own
test.

⚠ **Importing is not invoking.** [L11](../../records/0012_LAW-11-sealed-answer-key.md)
decision 13 reserves *running `score.py`* — the program, through
`just golden-score` — to Arpit's own hand, in either state. What permits **this**
file to read a key is **decision 14**: while the tree is UNLOCKED a session may
read the key *for scoring and review and nothing else*. Two different
permissions; this one uses the second and leaves the first alone. **It refuses to
run while the tree is locked**, which is what keeps that distinction honest
rather than asserted.

🔴 **Every number this produces is `informed` PERMANENTLY** — L11 decision 14,
accepted in Arpit's ruling of 2026-09-21. There is no arm of this benchmark whose
runner's model family had not seen the key, and locking again does not bring one
back.

## What it does NOT do

- **No answer-text verdict.** `score.py` emits `answer_text_verdict: null`
  always, and this file does not fill it. W-204 phase D step 3 wants
  `correct · partial · wrong · declined` *"with the evidence quote as the
  criterion"*, and that is a judgement, not a substring test. `evidence_quoted`
  is reported **under its own name** as the mechanical proxy it is.
- **No pooling.** Phase D step 6 sends newly-judged top-5 hits back into the key
  with `key_version` advanced. That writes a **key byte**, which no agent does in
  any state (L11). It stays Arpit's.
- **No difficulty bands.** Step 2's `tools/golden-difficulty/` run and the
  `d <= 1 / 2 / >= 3` bands freeze the moment a number is filed by band
  ([SR-RS](../../records/0133_predictions.md) decision 10b). Not started here, so
  not frozen here.
- **It never prints an answer.** The aggregate carries ids, ranks, booleans and
  counts. `score.py`'s allow-list is the contract and this file stays inside it.

## The funnel, added 2026-09-22 (W-212)

[SR-WORK-QUALITY](../../records/0056_WORK-quality.md) decision 1's
`reachable → in window → placed → answered` is computed **per `arm × rung × set`
bucket, from the hand-off's own `gates`** — `ask --json --why`'s
`derivation.gates`, captured by `golden_run.py` and never derived here.

🔴 **A bucket whose rows carry no gates reports `computed: false` and a reason,
never four zeros.** That distinction is the entire item: W-204 phase D scored
11 716 rows in which the cut line had been computed and discarded 11 716 times,
and a funnel of zeros would have been filed as a retrieval collapse instead of as
a missing instrument.

⚠ **The cost model is applied under the name `utility_c2_retrieval_proxy` and
carries its own `basis` string.** Decision 6's `c = 2` prices an *answer*; this
pass has no answer-text verdict, so `hit@5` stands in for *correct*. It is a
proxy, it says so in its own key, and it is not decision 6's utility.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KEY_DIR = ROOT / "work" / "golden" / "golden-answers"
STATE_FILE = ROOT / ".claude" / ".golden-lock" / "STATE"

KS = (1, 5, 10, 20, 50)

#: SR-WORK-QUALITY decision 1's four gates plus the cut line, in funnel order.
#: ⚠ **The same tuple `golden_run.GATE_FIELDS` writes**, because a scorer and a
#: writer that spell the contract twice can disagree while both look correct.
GATE_FIELDS = ("reachable", "in_window", "placed", "answered", "cut_score")

#: The confidence target SR-WORK-QUALITY decision 6 publishes — `t = 0.75`, from
#: which `c = t/(1-t) = 2`. 🔴 **Frozen before any score existed and never moved
#: since**: a correct answer `+1`, a decline `0`, a wrong answer `−2`. It is
#: named here so a reader can see which weight produced the utility column
#: without going to look.
COST_C = 2.0


def _load_scorer():
    """`score.py`'s functions, by path — `tools/` is not a package."""
    path = ROOT / "tools" / "golden-score" / "score.py"
    spec = importlib.util.spec_from_file_location("golden_score", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["golden_score"] = module
    spec.loader.exec_module(module)
    return module


def _require_unlocked() -> None:
    """🔴 Decision 14 is the permission, so its state is the precondition.

    A scoring pass that ran on a locked tree would be reaching into the key
    under no permission at all — decision 13's carve-out belongs to a program
    Arpit starts, not to this one.
    """
    try:
        state = STATE_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        state = "locked"
    if state != "unlocked":
        sys.exit(
            "refusing: the tree is LOCKED. L11 decision 14 is what permits a session\n"
            "  to read the key, and it permits it only while unlocked. Ask Arpit for\n"
            "  `just golden-unlock`; do not run it yourself."
        )


#: `(label, run directory, layout)`. `flat` means `evidence/rung-*/`, `armed`
#: means `evidence/<arm>/rung-*/`.
def discover(runs: list[Path]) -> list[tuple[str, str, str, Path]]:
    """`(arm, rung, set_name, handoff_path)` for every hand-off under `runs`."""
    found: list[tuple[str, str, str, Path]] = []
    for run in runs:
        evidence = run / "evidence"
        if not evidence.is_dir():
            continue
        for handoff in sorted(evidence.rglob("handoff-set-*.jsonl")):
            rel = handoff.relative_to(evidence).parts
            set_name = handoff.stem.replace("handoff-", "")
            # Three layouts are in use and the middle one is ambiguous by depth
            # alone, so the RUNG PREFIX decides rather than the nesting:
            #
            #   <arm>/rung-NNNNN/handoff-set-N.jsonl   the three-engine arms
            #   rung-NNNNN/handoff-set-N.jsonl         a flat single-arm ladder
            #   <arm>/handoff-set-N.jsonl              the null controls, one rung
            #
            # ⚠ Reading the second and third as the same shape is exactly what
            # the first draft did: it labelled `null-a` and `null-b` with the RUN
            # directory's name and reported them as one 748-row arm.
            if len(rel) >= 3:
                arm, rung = rel[0], rel[1]
            elif len(rel) == 2 and rel[0].startswith("rung-"):
                arm, rung = _arm_of(run), rel[0]
            elif len(rel) == 2:
                arm, rung = rel[0], "single"
            else:
                arm, rung = _arm_of(run), "single"
            found.append((arm, rung, set_name, handoff))
    return found


def _arm_of(run: Path) -> str:
    """A flat run's arm is the run's own engine. Named, never guessed."""
    return {
        "2026-09-20-golden-ladder-outputs": "HEAD-pre-set3",
        "2026-09-21-golden-ladder-outputs-set-3": "HEAD",
    }.get(run.name, run.name)


def _row_gates(row: dict) -> dict | None:
    """One hand-off row's five funnel integers, or `None` when it has none."""
    gates = row.get("gates")
    if not isinstance(gates, dict):
        return None
    kept = {field: gates.get(field) for field in GATE_FIELDS}
    return kept if any(v is not None for v in kept.values()) else None


def funnel(group: list[dict]) -> dict:
    """SR-WORK-QUALITY decision 1's funnel over one `arm × rung × set` bucket.

    🔴 **It returns `null` rather than zeros when the rows never carried gates.**
    That is the whole of W-212: W-204 phase D scored 11 716 rows and reported the
    funnel as *not computed*, because `reachable` and `in window` live in
    `ask --why`'s `derivation.gates` and prompt 5 never asked for them. A funnel
    of four zeros would have been indistinguishable from an engine that retrieved
    nothing, and it would have been **filed**.

    ⚠ **Partial coverage is reported, not averaged away.** `rows_with_gates`
    against `n` is how a reader sees that a bucket's funnel rests on some of its
    questions, and a bucket that mixes armed and unarmed runs cannot hide it.
    """
    measured = [r["gates"] for r in group if isinstance(r.get("gates"), dict)]
    if not measured:
        return {
            "computed": False,
            "reason": "no row in this bucket carries `derivation.gates` — the run "
                      "did not pass `ask --why` (W-212). Absent is NOT zero.",
            "rows_with_gates": 0,
            "n": len(group),
        }

    out: dict = {"computed": True, "rows_with_gates": len(measured), "n": len(group)}
    for field in ("reachable", "in_window", "placed", "answered"):
        values = [g.get(field) for g in measured if isinstance(g.get(field), int)]
        out[field] = sum(values) if values else None
        out[f"{field}_rows"] = len(values)
    cuts = [g.get("cut_score") for g in measured if isinstance(g.get("cut_score"), (int, float))]
    # The cut line is a score, so it is summarised as a median rather than a sum:
    # adding the last-in-window scores of 124 questions produces a number with no
    # referent at all.
    out["cut_score_median"] = sorted(cuts)[len(cuts) // 2] if cuts else None
    return out


def utility_c2_retrieval_proxy(group: list[dict]) -> dict:
    """SR-WORK-QUALITY decision 6's cost model, at the RETRIEVAL gate only.

    🔴 **`proxy` is in the name because the substitution is real.** Decision 6
    prices an *answer*: correct `+1`, declined `0`, wrong `−2` at the published
    `t = 0.75` → `c = 2`. There is no answer-text verdict in this pass
    (`score.py` emits `answer_text_verdict: null` always and no agent fills it),
    so *correct* here means **the key's primary document was inside the top 5** —
    `in window`, gate 2 — and nothing about whether the prose fux wrote was true.

    ⚠ **This number may not be read as decision 6's utility**, and it may not be
    fused into a headline (decision 9's rule for the judged series applies with
    more force to a stand-in for it). It exists so the frozen weight is applied
    to something rather than quoted at nothing, and `basis` travels with it.
    """
    correct = declined = wrong = 0
    for row in group:
        if row.get("said_unanswerable"):
            declined += 1
        elif row.get("hit@5"):
            correct += 1
        else:
            wrong += 1
    return {
        "c": COST_C,
        "basis": "hit@5 stands in for `correct`; there is no answer-text verdict "
                 "in this pass. NOT SR-WORK-QUALITY decision 6's utility.",
        "correct": correct,
        "declined": declined,
        "wrong": wrong,
        "utility": correct - COST_C * wrong,
    }


def score_run(runs: list[Path]) -> tuple[list[dict], list[str]]:
    scorer = _load_scorer()
    keys: dict[str, dict] = {}
    rows: list[dict] = []
    errors: list[str] = []

    for arm, rung, set_name, handoff in discover(runs):
        key_path = KEY_DIR / f"{set_name}.jsonl"
        if not key_path.is_file():
            errors.append(f"{handoff}: no key at {key_path.name}")
            continue
        if set_name not in keys:
            keys[set_name] = scorer.read_jsonl(key_path, redact=True)
        key = keys[set_name]
        handoff_rows = scorer.read_jsonl(handoff)

        # 🔴 Phase D step 1: a row with no key line, or a key line with no row,
        # is an ERROR and not a skip. Silently dropping either is how a partial
        # score comes to look like a whole one.
        missing_key = sorted(set(handoff_rows) - set(key))
        missing_row = sorted(set(key) - set(handoff_rows))
        if missing_key:
            errors.append(f"{arm}/{rung}/{set_name}: {len(missing_key)} row(s) with no key line")
        if missing_row:
            errors.append(f"{arm}/{rung}/{set_name}: {len(missing_row)} key line(s) with no row")

        for qid, row in handoff_rows.items():
            if qid not in key:
                continue
            scored = scorer.score_one(row, key[qid])
            scored.update(arm=arm, rung=rung, set=set_name)
            # 🔴 The funnel's input, carried through UNSCORED. `score.py`'s
            # output allow-list (L11 decision 13) is about what an answer is,
            # and five query-level integers are not one — but they are also not
            # the scorer's to compute, so they are copied from the hand-off and
            # never derived here.
            scored["gates"] = _row_gates(row)
            rows.append(scored)
    return rows, errors


def aggregate(rows: list[dict]) -> list[dict]:
    """Roll per-query rows up per `arm × rung × set`. Counts only."""
    buckets: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in rows:
        buckets[(row["arm"], row["rung"], row["set"])].append(row)

    out = []
    for (arm, rung, set_name), group in sorted(buckets.items()):
        n = len(group)
        agg = {
            "arm": arm, "rung": rung, "set": set_name, "n": n,
            "primary_found": sum(1 for r in group if r["primary_rank"]),
            "abstain_correct": sum(1 for r in group if r["abstain_correct"]),
            "abstain_wrong": sum(1 for r in group if r["abstain_wrong"]),
            "answered_unanswerable": sum(1 for r in group if r["answered_unanswerable"]),
            "evidence_quoted": sum(1 for r in group if r["evidence_quoted"]),
        }
        for k in KS:
            agg[f"hit@{k}"] = sum(1 for r in group if r[f"hit@{k}"])
        agg["funnel"] = funnel(group)
        agg["utility_c2_retrieval_proxy"] = utility_c2_retrieval_proxy(group)
        out.append(agg)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("runs", nargs="+", type=Path, help="filed run directories")
    ap.add_argument("--out", type=Path, required=True, help="directory for the rows and aggregate")
    args = ap.parse_args(argv)

    _require_unlocked()
    rows, errors = score_run(args.runs)
    if not rows:
        sys.exit("refusing: no hand-off rows scored. Check the run directories.")

    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "per-query.jsonl").open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    agg = aggregate(rows)
    (args.out / "aggregate.json").write_text(
        json.dumps(agg, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    if errors:
        (args.out / "JOIN-ERRORS.txt").write_text("\n".join(errors) + "\n", encoding="utf-8")

    print(f"scored {len(rows)} row(s) into {args.out}")
    print(f"  {len(agg)} arm x rung x set bucket(s)")
    print(f"  join errors: {len(errors)}" + (" — see JOIN-ERRORS.txt" if errors else ""))

    # 🔴 Said out loud, every run. W-204 phase D's funnel failure was discovered
    # by a human reading the rows days later; this line is the same discovery,
    # at the moment it is still cheap.
    computed = sum(1 for a in agg if a["funnel"]["computed"])
    if computed == len(agg):
        print(f"  funnel: computed for all {computed} bucket(s)")
    else:
        print(f"  🔴 funnel: computed for {computed}/{len(agg)} bucket(s) — the rest "
              "carry no `--why` gates and NO DOCUMENT MAY STATE A FUNNEL FOR THEM")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
