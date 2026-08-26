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
import sys
from pathlib import Path

from ..config import find_root
from ..errors import FuxError
from . import rerank
from typing import TYPE_CHECKING

from .rank import AskResult, Weighting
from .scan import ask as scan_ask

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..tune import Tune

__all__ = ["AskResult", "cmd_answer", "cmd_ask", "cmd_find", "run_query"]


def _tune(root: Path, *, enabled: bool = True) -> "Tune":
    """`.fux/tune.toml`, read once per query.

    **A malformed tune file is a loud error, not a silent default.** That is
    the opposite of `_archived_ranking`'s old tolerance for a missing
    `fux.toml`, and deliberately so: an absent file means *"every default"*
    and is the normal case, while a file that exists and cannot be parsed
    means someone edited it and got it wrong. Degrading there would answer a
    question with the engine's ranking while the reader believed it was
    theirs (ADR-TUNE decision 10).
    """
    from ..tune import load as load_tune

    return load_tune(root, enabled=enabled)


def _archived_ranking(root: Path, tune: "Tune") -> tuple["Weighting", frozenset[str]]:
    """The document-level multipliers and the directories they apply to.

    The weights come from `.fux/tune.toml` (ADR-TUNE decision 7 moved them out
    of `fux.toml`); the archived *declaration* still comes from the committed
    dirs list, never from a path convention (ADR-DIR-LIST decision 4).

    Degrades to no archived directories when the dirs list can't be read, so
    `ask`/`find` never fail because ranking metadata is missing — the same
    tolerance `_root()` already extends to a corpus with no `fux.toml` at all.
    **The tune file is not covered by that tolerance**; see `_tune`.
    """
    from ..config import load as load_config
    from ..ingest.gitdir import archived_dirs

    try:
        dirs = frozenset(archived_dirs(root, load_config(root).dirs_file))
    except FuxError:
        dirs = frozenset()
    return (
        Weighting(
            archived_weight=tune.archived_weight,
            archived_dirs=dirs,
            superseded_weight=tune.superseded_weight,
            recency_half_life_days=tune.recency_half_life_days,
            priority=tune.priority,
        ),
        dirs,
    )


def run_query(
    root: Path,
    query: str,
    top: int,
    *,
    force_scan: bool = True,
    tune: "Tune | None" = None,
    use_tune: bool = True,
) -> tuple[list[AskResult], str]:
    """Scan by default; use the accelerator only when `force_scan` is False
    and a fresh build exists. Return `(results, path)`.

    `use_tune=False` is `--no-tune`: `.fux/tune.toml` is not read at all, so
    the answer is the engine's own (ADR-TUNE decision 11). Callers that have
    already loaded a `Tune` pass it as `tune=` rather than paying for a second
    parse.
    """
    if tune is None:
        tune = _tune(root, enabled=use_tune)
    scoring = tune.scoring
    weighting, dirs = _archived_ranking(root, tune)
    # The dense lane is GONE (2026-08-25, Arpit) -- `--hybrid`, `[dense]`, the
    # committed vectors and the embedding model with it. DENSE-CHUNK measured
    # 0 fixed / 2 broken at every setting that fires, and a lane that is off by
    # measurement is a lane nobody may switch on. There is one ranking path now.
    #
    # W-76 Phase 6: when the reranker is on, retrieve DEEPER than the caller
    # asked and hand back `top` from the reordered list. This is what the gate
    # means by "top-20 -> top-5" -- a reranker that can only shuffle the five
    # documents already shown cannot promote the sixth, and the sixth is where
    # most of the recoverable failures are.
    rerank_weight = tune.rerank_weight
    depth = max(top, rerank.DEPTH) if rerank_weight > 0 else top

    if not force_scan:
        from ..derive import accel, format as derive_fmt

        if (derive_fmt.runtime_dir(root) / derive_fmt.STATS_NAME).exists() and accel.is_fresh(root):
            results = accel.ask(
                root, query, top=depth, weighting=weighting, archived_dirs=dirs, scoring=scoring
            )
            return _maybe_rerank(root, query, results, rerank_weight, top), "accelerator"
    results = scan_ask(
        root, query, top=depth, weighting=weighting, archived_dirs=dirs, scoring=scoring
    )
    return _maybe_rerank(root, query, results, rerank_weight, top), "scan"


def _maybe_rerank(root: Path, query: str, results, weight: float, top: int):
    """Proximity rerank, then truncate to what the caller asked for.

    **It used to run after dense fusion, and the ordering mattered**: fusion
    could admit a document the lexical lane missed, and reranking a list that
    document was not yet in would have skipped it. Fusion was deleted on
    2026-08-25, so this is now simply the last stage.
    """
    if weight <= 0:
        return results[:top]
    return rerank.rerank(root, query, results, weight=weight)[:top]


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


def _tune_for(root: Path, args) -> "Tune":
    """The tune for one command invocation, honouring `--no-tune`.

    Loaded ONCE and handed to both `run_query` and the archived declaration.
    Two loads could disagree if the file changed between them, and a ranking
    explained by a different weight than the one that produced it is worse
    than no explanation at all.
    """
    return _tune(root, enabled=not getattr(args, "no_tune", False))


def _declare_pending(root: Path) -> None:
    """W-66 Phase 3: state a lagging index on stderr, never on stdout.

    `--json` is a contract and the ADR surface captures compare stdout bytes
    (the W-64 progress plane solved the identical problem the identical way),
    so this never touches the answer itself — it declares, it never gates.
    ASCII only: a Windows console's default codepage cannot encode a fancy
    dash or arrow and the process crashes on print() rather than degrading.
    """
    from ..maintain import dirty

    pending = dirty.read(root)
    if pending:
        print(f"fux: {len(pending)} changed path(s) pending re-index", file=sys.stderr)


def _declare_no_accelerator(root: Path) -> None:
    """W-76 Phase 0: tell a fresh clone that `fux build` exists.

    **The gap this closes.** Everything fux needs to answer is committed, so a
    clone answers immediately — on the reference scan, which is correct and
    slow (measured: 4.2 s against the accelerator's warm p95 of 27.2 ms on
    8 870 documents). Nothing ever told the person that. `fux build` has always
    existed; it was undiscoverable at exactly the moment it was worth running.

    **The condition is narrow on purpose:** committed shards present, no fresh
    accelerator. That is a clone, a merge, or a checkout — precisely the cases
    `fux build` exists for. It deliberately does NOT fire when the index itself
    is absent, because then the answer is `fux ingest` and saying `fux build`
    would send someone down the wrong path.

    Same contract as `_declare_pending` and `_declare_archived`, for the same
    three reasons: `fux find` pipes bare paths so a note on stdout is read by
    `xargs` as a filename; `--json` is a contract; and this **declares, it
    never gates**. ASCII only -- a Windows console's default codepage cannot
    encode a fancy dash and the process crashes on `print()` rather than
    degrading.

    **The second line is load-bearing.** Without "results are identical either
    way" a reader assumes building might change their answers, which is the
    exact opposite of the differential law the accelerator is built on.
    """
    from .. import store as store_mod
    from ..derive import accel, format as derive_fmt

    try:
        if not any(True for _ in store_mod.iter_shard_paths(root)):
            return  # no index at all -- `fux ingest` is the answer, not `fux build`
    except (OSError, FuxError):
        return
    if (derive_fmt.runtime_dir(root) / derive_fmt.STATS_NAME).exists() and accel.is_fresh(root):
        return
    print(
        "fux: no fresh accelerator - this query used the reference scan.\n"
        "     Run 'fux build' for faster queries; results are identical either way.",
        file=sys.stderr,
    )


#: ADR-ARCHIVED-CONTENT decision 3 — the per-result marker in text output.
ARCHIVED_MARKER = "[archived]"


def _declare_archived(results, weight: float) -> None:
    """ADR-ARCHIVED-CONTENT decision 7: a response-level note when any archived
    document is returned. **stderr, never stdout.**

    Three reasons it cannot go on stdout, each sufficient alone:

    - `fux find` prints bare paths so it can pipe. A note on stdout is read by
      `xargs` as a filename.
    - `--json` is a contract, and the ADR surface captures compare stdout bytes.
    - It declares; it never gates. Same contract as `_declare_pending` above,
      and the same one ADR-CLI's staleness declaration took.

    ASCII only: a Windows console's default codepage cannot encode a fancy dash
    and the process crashes on `print()` rather than degrading (v0.35.0).

    The note carries **the rule, not a hedge** — it says what an archived
    document *is* and does not tell the reader what to conclude from it.
    Intent-neutral by ADR-DIR-LIST decision 12: Fux ships facts, not policy.
    """
    n = sum(1 for r in results if r.archived)
    if not n:
        return
    demoted = f" (demoted, weight {weight:.2f})" if weight != 1.0 else ""
    print(
        f"note: {n} of {len(results)} results are from archived sources{demoted}"
        f" - retired from the live corpus. An archived document records what was"
        f" true when it was retired, not what is true now.",
        file=sys.stderr,
    )


def cmd_ask(args) -> int:
    root = _root()
    tune = _tune_for(root, args)
    results, path = run_query(
        root,
        args.query,
        args.top,
        force_scan=_force_scan(args),
        tune=tune,
    )
    _declare_pending(root)
    _declare_no_accelerator(root)

    if args.json:
        # `--explain` is not text-only: a caller that wants to log which path
        # answered a slow query needs it in the machine-readable form too. The
        # key is additive and appears only when asked for, so no existing
        # consumer's parse changes (W-48).
        payload: dict = {"results": [_as_dict(root, r) for r in results]}
        if getattr(args, "explain", False):
            payload["path"] = path
        print(json_mod.dumps(payload, indent=2))
        _declare_archived(results, tune.archived_weight)
        return 0

    if not results:
        print("No confident matches.")
        return 0

    for r in results:
        mark = f"{ARCHIVED_MARKER} " if r.archived else ""
        print(f"{r.score:.4f}  {mark}{_resolve_title(root, r.id, r.title)}  ({r.loc})")
    if getattr(args, "explain", False):
        print(f"\n[{path}]")
    _declare_archived(results, tune.archived_weight)
    return 0


def cmd_find(args) -> int:
    """Ranked documents, one per line — the terse listing verb."""
    root = _root()
    tune = _tune_for(root, args)
    results, _ = run_query(root, args.query, args.top, force_scan=_force_scan(args), tune=tune)
    _declare_no_accelerator(root)

    if args.json:
        print(json_mod.dumps({"results": [_as_dict(root, r) for r in results]}, indent=2))
        _declare_archived(results, tune.archived_weight)
        return 0

    if not results:
        print("No confident matches.")
        return 0

    # **Bare paths, deliberately unmarked.** `find` exists to be piped, so a
    # `[archived]` prefix on stdout would be read as part of the filename — the
    # concrete reason ADR-DIR-LIST decision 12 put the note on stderr. The flag
    # is carried in `--json`, which is where a machine reader should look.
    for r in results:
        print(r.loc)
    _declare_archived(results, tune.archived_weight)
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
    tune = _tune_for(root, args)
    results, _ = run_query(root, args.query, 1, force_scan=_force_scan(args), tune=tune)
    _declare_no_accelerator(root)

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
        referred = _answer_via_refer(root, args.query, best, tune)
        if referred is not None:
            _declare_change_since_last_ask(root, args.query, referred)
            _print_refer_answer(referred, args.json)
            return 0

    return _print_index_answer(root, best, args.json, requested=no_refer_flag)


def _answer_via_refer(root: Path, query: str, best: AskResult, tune: "Tune"):
    """`None` on any failure to produce a usable citation — never raises."""
    from .refer_answer import answer_via_refer

    record = _record_for(root, best.id)
    if record is None:
        return None
    return answer_via_refer(root, query, best.id, best.loc, record["sha"], tune=tune)


def _declare_change_since_last_ask(root: Path, query: str, bundle) -> None:
    """W-82 3.4 — *"nothing has changed since you last asked."*

    **A report, not a memo.** No answer is stored and nothing is replayed: the
    answer above was recomputed on freshly fetched bytes, per the 2026-08-26
    ruling that a URL's actual document is fetched before any final answer. All
    this remembers is which `(loc, sha)` pairs the previous answer to the same
    question cited.

    **stderr, in both text and JSON mode**, so `answer`'s stdout stays
    byte-identical with this on or off — the rule W-64 set for the progress
    plane, and the reason the archived-results signal sits there too. Promoting
    it to a JSON field would be additive but would move a documented surface,
    so it is a fork rather than a default (W-82 3.4).

    Best-effort throughout: a diagnostic that can fail an answer is worse than
    no diagnostic.
    """
    try:
        from ..maintain import lastcited

        cited = {d.loc: (d.verdict.fetched_sha or d.verdict.indexed_sha) for d in bundle.documents}
        if not cited:
            return
        change = lastcited.compare(root, query, cited)
        line = change.line()
        if line:
            print(line, file=sys.stderr)
        lastcited.remember(root, query, cited)
    except Exception:  # pragma: no cover - a report must not break an answer
        pass


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
