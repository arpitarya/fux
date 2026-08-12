"""Grade the fux-playground goldens in both retrieval modes, side by side.

Exists so the M2 hybrid decision is made on the graded corpus rather than on
impressions, **without editing the sibling repo** — `fux-playground/tools/check.py`
grades one mode (whatever `fux ask` does by default) and has no flag for a
second, by design: it is a consumer, not a lab bench.

Reports, per mode:

- pass / fail against each golden's `expect_top` contract
- `XPASS` — a query marked `known_failure` that now passes, which is the number
  M2's DoD asks for
- `REGRESSION` — a query that passed and no longer does. **This is the number
  that decides the hybrid default**, and it is reported first, because a lane
  that closes two gaps while breaking five is a loss that a headline
  "2 XPASS" would hide.

Usage:
    python tools/differential/playground_grade.py [--playground ~/my_programs/fux-playground]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from fux.derive import accel  # noqa: E402
from fux.query.hybrid import hybrid_ask  # noqa: E402
from fux.query.scan import ask as scan_ask  # noqa: E402

MODES = {
    "scan": lambda root, q, top: scan_ask(root, q, top=top),
    "accelerator": lambda root, q, top: accel.ask(root, q, top=top),
    "hybrid": lambda root, q, top: hybrid_ask(root, q, top=top),
}


@dataclass
class ModeResult:
    passes: int = 0
    fails: int = 0
    xfail: int = 0
    xpass: list[str] = field(default_factory=list)
    regressions: list[str] = field(default_factory=list)
    failed_ids: set[str] = field(default_factory=set)


def load_goldens(playground: Path) -> list[dict]:
    path = playground / "goldens" / "queries.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


DEFAULT_TOP = 10


def _rank_of(results: list, doc_id: str) -> int | None:
    for i, r in enumerate(results, 1):
        if r.id == doc_id:
            return i
    return None


def grade_one(golden: dict, results: list) -> list[str]:
    """Failure reasons; empty means pass.

    **A verbatim port of `fux-playground/tools/check.py:grade`.** Copied rather
    than approximated on purpose: a second, looser definition of "pass" living
    in the engine repo is how a lab bench starts reporting better numbers than
    the consumer's own harness. If the playground's contract changes, this must
    be re-synced, and the sanity check in `main` is what catches the drift.
    """
    failures: list[str] = []

    if golden.get("expect_empty"):
        if results:
            got = ", ".join(f"{r.id}@{i}" for i, r in enumerate(results, 1))
            failures.append(f"expected no results, got {len(results)}: {got}")
        return failures

    satisfied_ranks: list[int] = []
    for want in golden.get("expect", []):
        doc_id, max_rank = want["id"], want["max_rank"]
        got = _rank_of(results, doc_id)
        if got is None:
            failures.append(f"{doc_id} absent from top {len(results)} (wanted rank <= {max_rank})")
        elif got > max_rank:
            failures.append(f"{doc_id} at rank {got}, wanted <= {max_rank}")
        else:
            satisfied_ranks.append(got)

    if satisfied_ranks:
        floor = max(satisfied_ranks)
        for doc_id in golden.get("forbid_above", []):
            got = _rank_of(results, doc_id)
            if got is not None and got < floor:
                failures.append(f"{doc_id} at rank {got} outranks the expected answer at {floor}")

    return failures


def grade(root: Path, goldens: list[dict], mode: str, baseline: ModeResult | None) -> ModeResult:
    out = ModeResult()
    runner = MODES[mode]
    for golden in goldens:
        top = golden.get("top", DEFAULT_TOP)
        ok = not grade_one(golden, runner(root, golden["query"], top))
        known = bool(golden.get("known_failure"))
        if ok:
            out.passes += 1
            if known:
                out.xpass.append(golden["id"])
        else:
            out.failed_ids.add(golden["id"])
            if known:
                out.xfail += 1
            else:
                out.fails += 1
        if baseline is not None and not ok and golden["id"] not in baseline.failed_ids:
            out.regressions.append(golden["id"])
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="grade the playground goldens in every retrieval mode")
    parser.add_argument("--playground", type=Path, default=Path.home() / "my_programs" / "fux-playground")
    args = parser.parse_args(argv)

    root = args.playground.resolve()
    goldens = load_goldens(root)
    print(f"{len(goldens)} goldens from {root}\n")

    baseline = None
    results: dict[str, ModeResult] = {}
    for mode in ("scan", "accelerator", "hybrid"):
        results[mode] = grade(root, goldens, mode, baseline)
        if mode == "scan":
            baseline = results[mode]

    print(f"{'mode':<14} {'pass':>5} {'fail':>5} {'xfail':>6} {'XPASS':>6} {'REGRESSIONS':>12}")
    print("-" * 54)
    for mode, r in results.items():
        print(f"{mode:<14} {r.passes:>5} {r.fails:>5} {r.xfail:>6} {len(r.xpass):>6} {len(r.regressions):>12}")

    for mode, r in results.items():
        if r.xpass:
            print(f"\n{mode} XPASS (a named gap closed): {', '.join(sorted(r.xpass))}")
        if r.regressions:
            print(f"{mode} REGRESSIONS (passed under scan, fails here): {', '.join(sorted(r.regressions))}")

    accel_matches = results["accelerator"].failed_ids == results["scan"].failed_ids
    print(f"\naccelerator == scan on every golden: {accel_matches}")
    if not accel_matches:
        print("  DIFFERENTIAL LAW VIOLATED — the accelerator changed a graded result")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
