"""The differential harness — accelerator results MUST equal scan results.

**Byte-for-byte, over the whole query set.** Not spot-checked, not "the top 5
agree", not tolerance-based. The comparison is the exact string `fux ask
--json` would print, because that string is what every downstream consumer and
every future measurement reads.

Why the bar is this high: an accelerator that is 99 % equivalent produces a
fast system whose every downstream number is quietly wrong, and nothing ever
errors. The tiering story (T0 scan -> T1 accelerator -> T2 segments) only
holds if each tier is provably the same engine, and M4's ARC cache will carry
this same discipline.

Usage:

    python tools/differential/run.py [--root .] [--full] [--skipping both]

Exit code 0 only if every query matched. A single mismatch prints both
payloads and fails the run.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fux.derive import accel  # noqa: E402
from fux.query import scan  # noqa: E402
from fux.query.rank import Weighting  # noqa: E402
from queryset import generate_with_vocabulary  # noqa: E402


def payload(results) -> str:
    """Exactly what `fux ask --json` prints — the surface under test."""
    return json.dumps({"results": [r.__dict__ for r in results]}, indent=2)


#: `top` values every query is checked at.
#:
#: Sweeping this is not thoroughness for its own sake — it was forced by a
#: mutation test. At `top=5` on a repo-scale corpus the rarest query term
#: already determines the answer, so replacing the block bound with a constant
#: **zero** still produced byte-identical output: the skip was accidentally
#: correct and the bound was never load-bearing. At `top=20` and `top=50` the
#: same mutation is caught immediately. A harness that only checked the default
#: would have certified an unsound bound as proven.
TOPS = (1, 5, 20, 50)


@dataclass
class Mismatch:
    query: str
    scan_payload: str
    accel_payload: str
    mode: str
    top: int


@dataclass
class Report:
    queries: int
    checks: int
    mismatches: list[Mismatch]
    scan_seconds: float
    accel_seconds: float

    @property
    def ok(self) -> bool:
        return not self.mismatches


#: Score weights every query is checked at (W-73, 2026-08-23).
#:
#: Before W-73 this harness only ever ran at `1.0`, which is why "thousands of
#: comparisons" never touched the defect: the weight was applied after the
#: candidate set had already been truncated on an unweighted bound. The values
#: below straddle 1.0 in both directions, because both directions diverge for
#: different reasons.
#:
#: **500.0 is not decoration.** The measured divergence on the adversarial
#: fixture in `tests/derive/test_weighted_bound.py` appears at 500 and NOT at
#: 4.0 or 25.0 — the block bound is tight but the slack between a weak
#: posting and its block's `mx` is real, and a small weight does not eat it.
#: A sweep that stops at "a plausible configuration" measures floating point.
#:
#: 🔴 **The LEVER these values ride changed on 2026-09-13 and this harness was
#: not told.** They used to be `archived_weight`, passed as a keyword to both
#: `ask`s; W-152 removed that prior — along with `superseded_weight` and
#: `recency_half_life_days` — after VERDICT-W143 measured that no single global
#: value cleared the bar. `ask()` has not accepted the keyword since, so every
#: invocation of this harness raised `TypeError` before its first comparison,
#: and **nothing noticed for two days** because the one arm anybody ran is
#: `tests/derive/test_differential.py`, which builds its own corpora and calls
#: `compare()` with its own arguments.
#:
#: **`[priority]` is the weight that survived** (SR-TUNE decision 8), so the
#: sweep rides it now: a per-location multiplier on one prefix of the corpus.
#: That is a strictly better shape for W-73's property than the prior was —
#: the bound has to hold when SOME documents are scaled and others are not, and
#: a prefix splits the corpus where a global prior scaled everything it touched.
WEIGHTS = (1.0, 0.5, 2.0, 500.0)


def compare(
    root: Path,
    queries: list[str],
    *,
    tops: tuple[int, ...] = TOPS,
    modes: tuple[str, ...] = ("off", "on"),
    weights: tuple[float, ...] = WEIGHTS,
    archived_dirs: frozenset[str] = frozenset(),
    priority_prefix: str | None = None,
) -> Report:
    """Run every query down both paths, at every `top`, in every mode, and diff.

    Both skipping modes are compared against the *same* scan oracle: skipping
    must be loss-free, so turning it on may not move a single byte either.

    `priority_prefix` is the document-location prefix each weight in `weights`
    is applied to via `[priority]`. `None` runs the sweep at no weighting at
    all, which is the pre-W-73 shape and proves less — callers that have a
    corpus should name a prefix that covers part of it.
    """
    mismatches: list[Mismatch] = []
    scan_seconds = 0.0
    accel_seconds = 0.0
    checks = 0

    for query in queries:
        for top in tops:
            for weight in weights:
                weighting = (
                    Weighting(
                        archived_dirs=archived_dirs,
                        priority=((priority_prefix, weight),),
                    )
                    if priority_prefix is not None
                    else None
                )
                kw = {"archived_dirs": archived_dirs, "weighting": weighting}
                t0 = time.perf_counter()
                expected = payload(scan.ask(root, query, top=top, **kw))
                scan_seconds += time.perf_counter() - t0

                for mode in modes:
                    t0 = time.perf_counter()
                    got = payload(accel.ask(root, query, top=top, skipping=(mode == "on"), **kw))
                    accel_seconds += time.perf_counter() - t0
                    checks += 1
                    if got != expected:
                        mismatches.append(
                            Mismatch(f"{query}  [w={weight}]", expected, got, mode, top)
                        )

    return Report(len(queries), checks, mismatches, scan_seconds, accel_seconds)


def _default_priority_prefix(root: Path) -> str | None:
    """The first configured source DIRECTORY, or `None` if there are only files.

    Deterministic because `source_dirs` returns a sorted, deduped list — L3
    applies to the harness too, or a mismatch is not reproducible.
    """
    from fux.config import load
    from fux.ingest.gitdir import source_dirs

    for entry in source_dirs(root, load(root).dirs_file):
        if (root / entry).is_dir():
            return entry
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="differential: accelerator vs scan, byte-for-byte")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--tops",
        type=int,
        nargs="+",
        default=list(TOPS),
        help=f"top values to check at (default {list(TOPS)}); see TOPS for why this is a sweep",
    )
    parser.add_argument("--full", action="store_true", help="the wide sweep (lab); default is the fast set")
    parser.add_argument("--goldens", type=Path, help="a JSON file of golden queries to fold in")
    parser.add_argument(
        "--priority-prefix",
        help="the `[priority]` location prefix the weight sweep rides "
        "(default: the first configured source DIRECTORY, so part of the corpus "
        "is scaled and part is not — which is what W-73's bound has to survive)",
    )
    parser.add_argument(
        "--skipping",
        choices=("off", "on", "both"),
        default="both",
        help="which accelerator modes to check (default: both)",
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    goldens = _load_goldens(args.goldens) if args.goldens else None
    sizes = dict(common=600, median=600, rare=600, pairs=1200, triples=600) if args.full else {}
    queries, vocab = generate_with_vocabulary(root, goldens=goldens, **sizes)
    prefix = args.priority_prefix or _default_priority_prefix(root)

    modes = ("off", "on") if args.skipping == "both" else (args.skipping,)
    report = compare(
        root, queries, tops=tuple(args.tops), modes=modes, priority_prefix=prefix
    )

    print(f"queries: {report.queries}   tops: {args.tops}   modes: {', '.join(modes)}")
    print(f"weights: {list(WEIGHTS)} on `[priority]` prefix {prefix!r}")
    if vocab.skipped_undecodable:
        # ⚠ Named, never a silent shrink: these files contributed no term, so
        # the query set is smaller than the corpus would suggest (W-184).
        print(
            f"undecodable: {vocab.skipped_undecodable} file(s) walked but not UTF-8, "
            f"contributing no terms — {', '.join(vocab.undecodable[:5])}"
            + (" ..." if vocab.skipped_undecodable > 5 else "")
        )
    print(f"comparisons: {report.checks}")
    print(f"scan:  {report.scan_seconds * 1000:9.1f} ms total")
    print(f"accel: {report.accel_seconds * 1000:9.1f} ms total")

    if report.ok:
        print(f"\nDIFFERENTIAL GREEN — {report.checks} comparisons, byte-identical in every mode")
        return 0

    print(f"\nDIFFERENTIAL FAILED — {len(report.mismatches)} mismatch(es)")
    for mismatch in report.mismatches[:5]:
        print(f"\n--- query {mismatch.query!r}  (skipping={mismatch.mode}, top={mismatch.top})")
        print("scan:\n" + mismatch.scan_payload)
        print("accel:\n" + mismatch.accel_payload)
    if len(report.mismatches) > 5:
        print(f"\n... and {len(report.mismatches) - 5} more")
    return 1


def _load_goldens(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data["queries"] if isinstance(data, dict) else data
    return [e["query"] if isinstance(e, dict) else str(e) for e in entries]


if __name__ == "__main__":
    sys.exit(main())
