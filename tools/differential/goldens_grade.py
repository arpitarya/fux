"""Grade a golden set in every retrieval mode, side by side.

Exists so a ranking decision is made on a graded corpus rather than on
impressions, and so the **differential law** — `scan` and `accelerator` must
return the same graded result — is checkable on any corpus with goldens.

🔴 **Renamed and de-defaulted 2026-09-12 (W-138).** It was `playground_grade.py`
and defaulted to `~/my_programs/fux-playground`.
[SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md) made that environment Arpit's
hands alone, so **there is no default corpus any more**: the caller names the
corpus and the goldens file, and the tool knows nothing about where either
lives. The grading logic is unchanged, so a number it produced before the rename
is still reproducible against the corpus it was produced on.

⚠ **The corpus it was actually run on is retired.** The accelerator's filed
41 pass / 0 fail number came from the playground's ten documents and ~50
goldens; that set is history ([SETUP-PLAYGROUND](../../work/setup/fux-playground.md)
§What it used to be) and is not coming back. The live instrument is the golden
ladder in `fux-lab` ([`work/golden/`](../../work/golden/README.md)) — whose
questions carry no `doc` + `max_rank` contract, so **this tool has no live
golden set today** and is kept for the next one that has one.

**The `hybrid` mode is gone (2026-08-25).** It graded the dense lane, and the
lane, the embedding model and the `--hybrid` flag were all deleted after
DENSE-CHUNK measured 0 fixed / 2 broken. Two modes remain, and they are the two
the differential law binds together: `scan` and `accelerator` must agree.

Reports, per mode:

- pass / fail against each golden's `doc` + `max_rank` contract
- `XPASS` — a query marked `known_failure` that now passes
- `REGRESSION` — a query that passed and no longer does, **reported first**,
  because a change that closes two gaps while breaking five is a loss that a
  headline "2 XPASS" would hide.

Usage:
    python tools/differential/goldens_grade.py --corpus <dir> --goldens <file.jsonl>

`--corpus` is the repo holding `.fux/`; `--goldens` is a JSONL file in the
schema `tools/quality/goldens.py` documents. Neither has a default, deliberately.
"""


from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from fux.query import run_query  # noqa: E402
from fux.tune import load as load_tune  # noqa: E402

# `run_query` picks the mode: `force_scan=True` is scan, `False` is the
# accelerator (falling back to scan itself when no fresh build exists — see
# the fallback note in `grade`). Both modes get the SAME `Tune`, resolved
# once per corpus, so the comparison is apples to apples with `fux ask`
# itself: weighting, scoring and reranking all come from `.fux/tune.toml`,
# exactly as the CLI applies them. Calling `scan_ask`/`accel.ask` directly
# with no tuning was the earlier bug — it never matched what a real answer
# looked like.
FORCE_SCAN = {"scan": True, "accelerator": False}


@dataclass
class ModeResult:
    passes: int = 0
    fails: int = 0
    xfail: int = 0
    xpass: list[str] = field(default_factory=list)
    regressions: list[str] = field(default_factory=list)
    failed_ids: set[str] = field(default_factory=set)
    fell_back: list[str] = field(default_factory=list)


def load_goldens(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


# The retired consumer harness's own default, kept so a re-run on an old corpus
# asks the engine for the same amount of evidence per query as the filed number did.
DEFAULT_TOP = 5


def _rank_of(results: list, doc: str) -> int | None:
    for i, r in enumerate(results, 1):
        if r.loc == doc:
            return i
    return None


def grade_one(golden: dict, results: list) -> list[str]:
    """Failure reasons; empty means pass.

    One document, one rank ceiling per golden (`doc` + `max_rank`). This was
    ported verbatim from the retired consumer harness rather than approximated,
    on purpose: a second, looser definition of "pass" living in the engine repo
    is how a lab bench starts reporting better numbers than the consumer does.
    Keep it verbatim — a golden set's own harness, if it has one, is canonical.
    """
    doc_id = golden["doc"]
    want = golden.get("max_rank", 1)
    got = _rank_of(results, doc_id)
    if got is None:
        return [f"{doc_id} absent from top {len(results)} (wanted rank <= {want})"]
    if got > want:
        return [f"{doc_id} at rank {got}, wanted <= {want}"]
    return []


def grade(
    root: Path, goldens: list[dict], mode: str, tune, baseline: ModeResult | None
) -> ModeResult:
    out = ModeResult()
    force_scan = FORCE_SCAN[mode]
    for golden in goldens:
        top = golden.get("top", DEFAULT_TOP)
        results, path = run_query(root, golden["q"], top, force_scan=force_scan, tune=tune)
        if mode == "accelerator" and path != "accelerator":
            # `run_query` falls back to scan silently when no fresh accelerator
            # build exists. Silent here would mislabel a scan result as the
            # accelerator's — exactly the class of bug this file has already
            # had twice. Record it instead of hiding it.
            out.fell_back.append(golden["id"])
        ok = not grade_one(golden, results)
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
    parser = argparse.ArgumentParser(description="grade a golden set in every retrieval mode")
    parser.add_argument("--corpus", type=Path, required=True, help="the repo holding .fux/")
    parser.add_argument("--goldens", type=Path, required=True, help="a goldens JSONL file")
    args = parser.parse_args(argv)

    root = args.corpus.resolve()
    goldens = load_goldens(args.goldens.resolve())
    tune = load_tune(root)
    print(f"{len(goldens)} goldens from {root}\n")

    baseline = None
    results: dict[str, ModeResult] = {}
    for mode in ("scan", "accelerator"):
        results[mode] = grade(root, goldens, mode, tune, baseline)
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
        if r.fell_back:
            print(
                f"\n⚠ {mode} had no fresh accelerator build — ran scan instead for: "
                f"{', '.join(sorted(r.fell_back))} (results below are NOT a real accelerator check)"
            )

    accel_matches = results["accelerator"].failed_ids == results["scan"].failed_ids
    print(f"\naccelerator == scan on every golden: {accel_matches}")
    if not accel_matches:
        print("  DIFFERENTIAL LAW VIOLATED — the accelerator changed a graded result")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
