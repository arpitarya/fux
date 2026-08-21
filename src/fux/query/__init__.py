"""The query plane — `ask` / `find` / `answer`.

## The three verbs, and what they mean at M2

| verb | what it is | what changes at M4 |
|---|---|---|
| `ask` | the agent-facing default: ranked documents with citations | gains passages re-scored on fetched bytes |
| `find` | ranked documents, terse — one line per hit | unchanged |
| `answer` | the single best answer, assembled from the index | becomes extractive over fetched content |

**`answer` is honest about its ceiling.** The archived engine's `answer` was
extractive TextRank over cached document content; this build commits
statistics, not content, and the refer plane that fetches it is M4. So M2's
`answer` assembles what the index actually holds — the winning document's
title, its heading-derived phrases, and its citation — and says so. The verb
exists now so M4 is an upgrade to it rather than a new command, which is the
expensive thing to retrofit.

## Which path answers

`ask` uses the B2 scan by default, and the derived accelerator only when
`--fast` is passed and a build is present and fresh (Arpit, 2026-08-21 —
scan needs no build step, so it is the conservative default). **That choice
can never change a result** — the differential law (`tools/differential/`,
`tests/derive/test_differential.py`) asserts the two are byte-identical — so
it is purely a speed decision. `--scan` forces the reference path explicitly
(redundant with the default; kept for bug reproduction), and `--fast` and
`--scan` are mutually exclusive.
"""

from __future__ import annotations

import json as json_mod
from pathlib import Path

from ..config import find_root
from ..errors import FuxError
from .rank import AskResult
from .scan import ask as scan_ask

__all__ = ["AskResult", "cmd_answer", "cmd_ask", "cmd_find", "run_query"]


def run_query(
    root: Path, query: str, top: int, *, force_scan: bool = True, use_hybrid: bool = False
) -> tuple[list[AskResult], str]:
    """Scan by default; use the accelerator only when `force_scan` is False
    and a fresh build exists. Return `(results, path)`."""
    if use_hybrid:
        from .hybrid import hybrid_ask

        return hybrid_ask(root, query, top=top), "hybrid"
    if not force_scan:
        from ..derive import accel, format as derive_fmt

        if (derive_fmt.runtime_dir(root) / derive_fmt.STATS_NAME).exists() and accel.is_fresh(root):
            return accel.ask(root, query, top=top), "accelerator"
    return scan_ask(root, query, top=top), "scan"


def _root() -> Path:
    root = find_root()
    if root is None:
        raise FuxError("no fux.toml or .git found — run from inside a configured repo")
    return root


def _force_scan(args) -> bool:
    """Scan by default; `--fast` is the only thing that opts into the
    accelerator. `--scan` is accepted too — it is already the default, kept
    for explicit bug reproduction — and argparse's mutually exclusive group
    guarantees the two are never both set."""
    return not getattr(args, "fast", False)


def cmd_ask(args) -> int:
    root = _root()
    results, path = run_query(
        root,
        args.query,
        args.top,
        force_scan=_force_scan(args),
        use_hybrid=getattr(args, "hybrid", False),
    )

    if args.json:
        # `--explain` is not text-only: a caller that wants to log which path
        # answered a slow query needs it in the machine-readable form too. The
        # key is additive and appears only when asked for, so no existing
        # consumer's parse changes (W-48).
        payload: dict = {"results": [_as_dict(root, r) for r in results]}
        if getattr(args, "explain", False):
            payload["path"] = path
        print(json_mod.dumps(payload, indent=2))
        return 0

    if not results:
        print("No confident matches.")
        return 0

    for r in results:
        print(f"{r.score:.4f}  {_resolve_title(root, r.id, r.title)}  ({r.loc})")
    if getattr(args, "explain", False):
        print(f"\n[{path}]")
    return 0


def cmd_find(args) -> int:
    """Ranked documents, one per line — the terse listing verb."""
    root = _root()
    results, _ = run_query(root, args.query, args.top, force_scan=_force_scan(args))

    if args.json:
        print(json_mod.dumps({"results": [_as_dict(root, r) for r in results]}, indent=2))
        return 0

    if not results:
        print("No confident matches.")
        return 0

    for r in results:
        print(r.loc)
    return 0


def cmd_answer(args) -> int:
    """The single best answer — a fetched, re-scored passage when the source
    is reachable (PRIORITY.md P6); the index's own structure otherwise.

    No model is involved and none ever will be on this path (the `$0` law).
    Refer is the **default**: the winning document's citation is fetched
    through the consumer's fetcher, re-scored on the fetched bytes, and cited
    with a fresh `sha` — `"source": "refer"`. `--no-refer` (or refer
    producing nothing usable — unreachable source, no fetcher, a citation
    deleted from the working tree) falls back to the M2 index-only path —
    `"source": "index"` — never silence.
    """
    root = _root()
    results, _ = run_query(root, args.query, 1, force_scan=_force_scan(args))

    if not results:
        if args.json:
            # `"source"` is the key ADR-ANSWER tells callers to switch on when
            # the refer plane lands, so it must be present on the no-match
            # branch too — an absent key is a trap, not a signal (W-48).
            print(
                json_mod.dumps(
                    {"answer": None, "citation": None, "source": "index"}, indent=2
                )
            )
        else:
            print("No confident matches.")
        return 0

    best = results[0]
    no_refer_flag = getattr(args, "no_refer", False)

    if not no_refer_flag:
        referred = _answer_via_refer(root, args.query, best)
        if referred is not None:
            _print_refer_answer(referred, args.json)
            return 0

    return _print_index_answer(root, best, args.json, requested=no_refer_flag)


def _answer_via_refer(root: Path, query: str, best: AskResult):
    """`None` on any failure to produce a usable citation — never raises."""
    from .refer_answer import answer_via_refer

    record = _record_for(root, best.id)
    if record is None:
        return None
    return answer_via_refer(root, query, best.id, best.loc, record["sha"])


def _print_refer_answer(bundle, as_json: bool) -> None:
    citations = bundle.assembled.citations
    cited = bundle.documents[0] if bundle.documents else None
    freshness = cited.verdict.label if cited is not None else "unverified"

    if as_json:
        print(
            json_mod.dumps(
                {
                    "answer": {
                        "passages": [
                            {"heading": c.heading, "text": c.text, "score": c.score}
                            for c in citations
                        ]
                    },
                    "citation": {
                        "id": citations[0].doc_id,
                        "loc": citations[0].locator,
                        "sha": citations[0].sha,
                        "freshness": freshness,
                    },
                    "source": "refer",
                },
                indent=2,
            )
        )
        return

    for c in citations:
        if c.heading:
            print(f"# {c.heading}\n")
        print(c.text)
        print()
    print(f"  -- {citations[0].locator} (sha {citations[0].sha[:12]}, {freshness})")


def _print_index_answer(root: Path, best: AskResult, as_json: bool, *, requested: bool) -> int:
    """The M2 path: the winning record's own extracted structure — no fetch.

    `requested` distinguishes why: the caller passed `--no-refer`, versus
    refer being tried and producing nothing usable (unreachable source, no
    fetcher configured, a citation deleted from the working tree).
    """
    phrases = _phrases_for(root, best.id)
    title = _resolve_title(root, best.id, best.title)

    if as_json:
        print(
            json_mod.dumps(
                {
                    "answer": {"title": title, "phrases": phrases},
                    "citation": {"id": best.id, "loc": best.loc, "score": best.score},
                    "source": "index",
                },
                indent=2,
            )
        )
        return 0

    print(title)
    for phrase in phrases:
        print(f"  - {phrase}")
    print(f"\n  -- {best.loc}")
    reason = "--no-refer was passed" if requested else "the source could not be reached or verified"
    print(f"\n(from the index's own structure — {reason})")
    return 0


def _phrases_for(root: Path, doc_id: str) -> list[str]:
    """The winning record's heading-derived phrases, read from its shard alone."""
    record = _record_for(root, doc_id)
    return list(record.get("phrases", [])) if record is not None else []


def _record_for(root: Path, doc_id: str) -> dict | None:
    """`doc_id`'s own committed record, read from its shard alone — one shard,
    not the corpus, the same shape as `_phrases_for`."""
    from .. import store as store_mod

    path = store_mod.shard_path(root, store_mod.shard_for(doc_id))
    if not path.exists():
        return None
    _, records = store_mod.read_shard(path)
    for record in records:
        if record["id"] == doc_id:
            return record
    return None


def _resolve_title(root: Path, doc_id: str, fallback_title: str) -> str:
    """P5: the best title to show for `doc_id`.

    `rank()` already computed `fallback_title` with no cache access — it must
    stay a pure function of the record for the differential law
    (`store.display_title`'s docstring). This is a *second*, display-only
    lookup, after the accelerator and scan paths have already produced
    byte-identical results, so applying it uniformly here can never make the
    two paths disagree. Re-reads one shard rather than trusting
    `fallback_title`'s shape to reveal whether the record is hashed.
    """
    from .. import store as store_mod

    record = _record_for(root, doc_id)
    if record is None:
        return fallback_title
    return store_mod.display_title(record, cache=store_mod.DisplayCache(root))


def _as_dict(root: Path, result: AskResult) -> dict:
    """`AskResult` as JSON, with `title` upgraded through the P5 display cache."""
    payload = dict(result.__dict__)
    payload["title"] = _resolve_title(root, result.id, result.title)
    return payload
