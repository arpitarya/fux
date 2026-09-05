"""The query plane — `ask` / `find` / `answer`.

## The three verbs, and what they mean at M2

| verb | what it is | what changes at M4 |
|---|---|---|
| `ask` | the agent-facing default: ranked documents with citations | gains passages re-scored on fetched bytes |
| `find` | ranked documents, terse — one line per hit | unchanged |
| `answer` | the single best answer, assembled from the index | becomes extractive over fetched content |

## `ask` is heading-level; `answer` is line-level (W-84, 2026-08-26)

**`ask` names the sections that match, `answer` names the lines.** The split is
L2 and L4 showing through the surface, not an omission:

- A **line range** can only be computed by chunking **fetched** bytes, which is
  what `answer` does and `ask`, offline by default, does not. A range computed
  at ingest would describe the document as it was then and point somewhere
  wrong after one edit, while looking exactly as right.
- A **heading** is already committed — `phrases` on every plain record, put
  there by `ingest/extract.py`. Naming the matching ones costs no positional
  index, no fetch and no byte. Its staleness exposure is `title`'s exactly.

The selection lives in [`headings.py`](headings.py) and is **display-only**:
it runs on the already-unified result list after `run_query` returns, like
`_resolve_title` (P5), so it can never reach a score or an ordering.

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

__all__ = ["AskResult", "cmd_answer", "cmd_ask", "cmd_find", "cmd_verify", "run_query"]


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
    confidence_out: dict | None = None,
    trace_out: dict | None = None,
    expand: str = "",
) -> tuple[list[AskResult], str]:
    """Scan by default; use the accelerator only when `force_scan` is False
    and a fresh build exists. Return `(results, path)`.

    `use_tune=False` is `--no-tune`: `.fux/tune.toml` is not read at all, so
    the answer is the engine's own (ADR-TUNE decision 11). Callers that have
    already loaded a `Tune` pass it as `tune=` rather than paying for a second
    parse.

    `trace_out`, when a caller supplies a dict, receives `{"window": [...],
    "pre_rerank": [...]}` — ADR-PROVENANCE. The **window** is what `depth`
    retrieved before truncation, and it is the only place the *negative space*
    exists: once `_maybe_rerank` has truncated to `top`, the documents that
    were considered and cut are gone and no later stage can recover them.
    Costs one list reference on a path that already holds both lists.

    `confidence_out`, when a caller supplies a dict, receives
    `{"confidence": Confidence}` — ADR-CONFIDENCE. **It stays an
    out-parameter rather than becoming a third element of the return tuple**
    because that tuple is unpacked by `cmd_ask`, `cmd_find`, `cmd_answer`,
    `mcp._search` and the test suite; an additive keyword changes none of them,
    and a caller that does not ask pays only for a `None` check.

    `expand` is W-109's agent-written expansion — free text, analyzed by the
    **same** analyzer the index was built with and scored at
    `[ranking] expand_weight`. Empty means no expansion, and then every value
    below is byte-identical to what this function returned before the parameter
    existed (`query/expand.py::Expansion.none`).

    ⚠ **The confidence block is built on the ORIGINAL query, always.**
    `_fill_confidence` receives `query`, never the expansion, so `coverage`,
    `missing` and `doc_coverage` describe what the *user* asked — a document
    lifted by expansion terms cannot raise its own band. It also cannot be
    returned at all: `rank()` drops a candidate that matches no original term.

    **The block is built from the FINAL result list, after reranking.**
    `rank()` supplies `df` and `n`; the scores come from `results` as the caller
    will see them. Computing separation from `rank()`'s pre-rerank scores would
    describe an ordering nobody was shown — the reranker exists precisely to
    change which document is first.
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
    stats: dict | None = {} if confidence_out is not None else None

    from .expand import build as build_expansion
    from .scan import query_term_hashes

    query_hashes = query_term_hashes(query)
    expansion = build_expansion(
        query_hashes, query_term_hashes(expand) if expand else [], tune.expand_weight
    )

    if not force_scan:
        from ..derive import accel, format as derive_fmt

        if (derive_fmt.runtime_dir(root) / derive_fmt.STATS_NAME).exists() and accel.is_fresh(root):
            results = accel.ask(
                root, query, top=depth, weighting=weighting, archived_dirs=dirs,
                scoring=scoring, stats_out=stats, expansion=expansion,
            )
            final = _maybe_rerank(root, query, results, rerank_weight, top)
            _fill_trace(trace_out, results, rerank_weight)
            _fill_confidence(confidence_out, stats, query, final, tune)
            return final, "accelerator"
    results = scan_ask(
        root, query, top=depth, weighting=weighting, archived_dirs=dirs,
        scoring=scoring, stats_out=stats, expansion=expansion,
    )
    final = _maybe_rerank(root, query, results, rerank_weight, top)
    _fill_trace(trace_out, results, rerank_weight)
    _fill_confidence(confidence_out, stats, query, final, tune)
    return final, "scan"


def _fill_confidence(
    out: dict | None, stats: dict | None, query: str, results, tune: "Tune"
) -> None:
    """Assemble the confidence block, if anyone asked for one.

    **`tune` supplies the two band floors** (ADR-CONFIDENCE decision 13). They
    are resolved once, here, from the same `Tune` that scored the query — so a
    query cannot be judged by one floor and reported with another, and
    `--no-tune` reaches the band exactly as it reaches the ranking.

    **Never raises.** A confidence signal that can fail a query is worse than no
    signal — the same contract `_declare_change_since_last_ask` takes, and for
    the same reason: this is something fux says *about* an answer, and it must
    not be able to take the answer down with it. A caller that gets no block
    sees an absent key, which is the honest report of "not computed".
    """
    if out is None:
        return
    try:
        from .confidence import signals as build_signals
        from .scan import query_term_hashes
        from .tokenize import tokenize_pairs

        stats = stats or {}
        # ADR-PROVENANCE reads the same `df`/`n` rather than recomputing them:
        # a derivation that invented its own frequencies could disagree with the
        # confidence block printed beside it, and two numbers that disagree
        # about the same corpus are worse than one.
        out["stats"] = stats
        out["confidence"] = build_signals(
            tokenize_pairs(query),
            query_term_hashes(query),
            stats.get("df", {}),
            int(stats.get("n", 0)),
            [r.score for r in results],
            # ADR-CONFIDENCE: `rank()` put this in the same dict as `df`/`n`,
            # from the record it actually ranked first — so the accelerator and
            # the scan cannot disagree about it.
            top_doc_hashes=stats.get("top_doc_hashes"),
            separation_floor=tune.separation_floor,
            doc_coverage_floor=tune.doc_coverage_floor,
        )
    except Exception:  # pragma: no cover - a signal must not break an answer
        pass


def _fill_trace(out: dict | None, window, rerank_weight: float) -> None:
    """Hand the caller the pre-truncation candidate list. **Never raises.**

    Same contract as `_fill_confidence`, for the same reason: a diagnostic that
    can fail a query is worse than no diagnostic. A caller that gets nothing
    sees absent keys, which is the honest report of *"not computed"*.

    `pre_rerank` is recorded **only when the reranker actually ran**. Recording
    it unconditionally would let `--why` print a `rank_before_rerank` for every
    document on a tree where reranking is off — a field that looks like a
    measurement and is really a copy of the rank beside it.
    """
    if out is None:
        return
    try:
        out["window"] = list(window)
        if rerank_weight > 0:
            out["pre_rerank"] = list(window)
    except Exception:  # pragma: no cover - a diagnostic must not break an answer
        pass


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


# -- the output contract -------------------------------------------------------

#: The declared shape of what `--json` prints, beside this module
#: (`query/output.schema.json`). **The only PUBLIC shape fux has**: everything
#: else declared in this repo is internal, and this one is parsed by other
#: people's agents.
OUTPUT_SCHEMA = "output.schema.json"


def _emit(payload: dict, shape: str, *, band_requested: bool = False) -> None:
    """Validate against the output contract, then print.

    **Fux cannot emit JSON that violates its own contract**, and that is worth
    a few microseconds on a payload of a handful of keys. ADR-ANSWER already
    tells callers to switch on `source` and ADR-ASK tells them to branch on the
    `archived` boolean — two promises stated in prose and checked by nothing
    until now. A key quietly renamed here breaks a consumer silently, at their
    end, with no error at ours.

    ⚠ **A contract violation is a BUG IN FUX, so it raises rather than
    degrading.** That is the opposite of how the reading paths behave, and
    deliberately: `coerce` exists because a file on disk may have been written
    by an older version or a killed process, and neither applies to a dict this
    process built three lines ago.
    """
    from ..schema import load as load_schema

    # `band_requested` is a caller-defined condition (ADR-CONFIDENCE decision
    # 11, ADR-OUTPUT decision 3): `confidence` is required **when the caller
    # asked for it** and absent otherwise.
    #
    # ⚠ **The condition must come from the REQUEST, not from the payload.**
    # `schema.validate` only consults it for a key that is already missing, so
    # a test reading `"confidence" in payload` is a tautology that can never
    # fire — and the guard worth having is exactly the one it would lose: with
    # `--band` passed, an `answer` branch that forgot the key now FAILS instead
    # of quietly emitting one shape where its siblings emit another.
    load_schema("fux.query", OUTPUT_SCHEMA).shape(shape).validate(
        payload,
        label=f"--json {shape}",
        conditions={"band_requested": lambda _payload: band_requested},
    )
    print(json_mod.dumps(payload, indent=2))


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


def _show_band(args) -> bool:
    """ADR-CONFIDENCE decision 11: the CLI emits the block only under `--band`.

    By the time this runs, `cli._apply_output_defaults` has already folded
    `.fux/output.toml` into `args.band`, so this is a plain read — the
    precedence chain lives in exactly one place and this is not it.

    ⚠ **The block is still COMPUTED when this is False.** Gating the
    computation would gate `stats_out` with it, and the differential law
    (`--fast` vs `--scan` agree on confidence) would stop being exercised on
    the default path — which is the path almost every run takes.
    """
    return bool(getattr(args, "band", False))


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

#: W-84 — what precedes a matched heading in `ask`'s text output. The section
#: sign, because that is what a section reference has looked like in print for
#: four centuries and no reader has to be taught it.
SECTION_MARKER = "§"


def _headings_for(record: dict | None, query: str) -> list[str]:
    """W-84's matched headings — imported lazily so `find`'s hot path and every
    caller that never renders one pays nothing for the analyzer import."""
    from .headings import headings_for

    return headings_for(record, query)


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


def _declare_confidence(block, show: bool = False) -> None:
    """ADR-CONFIDENCE decision 4, as amended: the band on stderr, never stdout.

    Same contract as `_declare_archived` and `_declare_pending`, for the same
    three reasons — `find` pipes bare paths, `--json` is a contract, and this
    declares rather than gating.

    ⚠ **`show` is `--band`, and under it `grounded` prints too.** The original
    silence-at-`grounded` existed so a healthy query would not print a line on
    every invocation; once a human has explicitly asked for the band, a flag
    that goes quiet exactly when the answer is good reads as broken.
    """
    if block is None or not show:
        return
    line = block.line() or f"confidence: {block.band}."
    print(line, file=sys.stderr)


def _queries_of(args) -> list[str]:
    """The primary question, then every extra `-q`, de-duplicated in order.

    **The positional query is always first and always present**, so the
    "primary" arm is a syntactic fact rather than a convention — which is what
    lets the confidence block name one query rather than a set.
    """
    extra = list(getattr(args, "also", None) or [])
    return list(dict.fromkeys([args.query, *extra]))


def _expand_of(args) -> str:
    return str(getattr(args, "expand", "") or "")


def _run_fused(root, args, top, *, tune, confidence_out, trace_out=None):
    """`run_query` for one question, or several fused by RRF. W-109.

    Returns `(results, path, fused)`.

    ## The confidence block describes the PRIMARY query, and says so

    🔴 **`separation` may not be computed on RRF scores.** `separation_floor`
    is calibrated against BM25F, and reciprocal ranks live on a different
    scale entirely: a perfect fused top-2 differs by `1/61 - 1/62 ≈ 0.0003`,
    so every fused query would fall below any BM25F-calibrated floor and be
    demoted for the unit change rather than for its quality. **That is a moved
    threshold in disguise**, and the alternative — recalibrating the floor for
    fusion — is a ranking default nobody has measured.

    So a fused answer reports the block for the **first** query's own ranking,
    and `--json` carries `"fused": true` beside it so a consumer knows the band
    describes one arm rather than the list it is printed under. **Stated, not
    collapsed**: the block is neither silently omitted nor silently rescaled.
    """
    queries = _queries_of(args)
    expand = _expand_of(args)
    results, path = run_query(
        root, queries[0], top, force_scan=_force_scan(args), tune=tune,
        confidence_out=confidence_out, trace_out=trace_out, expand=expand,
    )
    if len(queries) == 1:
        return results, path, False

    from .fuse import fuse_results

    # ⚠ Every arm carries the SAME expansion. An expansion is the caller's
    # description of the document's vocabulary, not of one phrasing of the
    # question, and giving each arm a different one would make the fusion a
    # comparison of expansions rather than of queries.
    arms = [results]
    for q in queries[1:]:
        more, _ = run_query(
            root, q, top, force_scan=_force_scan(args), tune=tune, expand=expand,
        )
        arms.append(more)
    return fuse_results(arms, top), path, True


def cmd_ask(args) -> int:
    root = _root()
    tune = _tune_for(root, args)
    signals: dict = {}
    want_why = bool(getattr(args, "why", False))
    trace: dict | None = {} if want_why else None
    results, path, fused = _run_fused(
        root, args, args.top, tune=tune, confidence_out=signals, trace_out=trace,
    )
    block = signals.get("confidence")
    why = _derivation_for(root, args, results, path, signals, trace, tune) if want_why else None
    _declare_pending(root)
    _declare_no_accelerator(root)

    # ADR-OUTPUT decision 21. `getattr` rather than `args.sections` because
    # `_as_dict` is shared with `find`, which declares no such key, and a
    # caller constructing args by hand (the MCP surface, the tests) should get
    # the built-in rather than an AttributeError.
    show_sections = bool(getattr(args, "sections", True))

    if args.json:
        # `--explain` is not text-only: a caller that wants to log which path
        # answered a slow query needs it in the machine-readable form too. The
        # key is additive and appears only when asked for, so no existing
        # consumer's parse changes (W-48).
        payload: dict = {
            "results": [_as_dict(root, r, args.query, sections=show_sections) for r in results]
        }
        # ADR-CONFIDENCE decision 11: present only under `--band`. **Absent
        # means NOT ASKED FOR — it is never a claim about the answer**, which
        # is why the schema makes it conditional rather than optional-in-prose.
        if block is not None and _show_band(args):
            payload["confidence"] = block.as_dict()
        # W-109 — additive, and it is not optional when it applies: without
        # it a consumer reads an RRF score as a BM25F score, and the two are
        # not comparable. Absent means "one question", never "unknown".
        if fused:
            payload["fused"] = True
        if getattr(args, "explain", False):
            payload["path"] = path
        if why is not None:
            payload["derivation"] = why.as_dict()
        print(json_mod.dumps(payload, indent=2))
        _declare_archived(results, tune.archived_weight)
        return 0

    if not results:
        print("No confident matches.")
        _declare_confidence(block, _show_band(args))
        return 0

    # W-84 — the matched headings under each hit. **Indented, never on the
    # citation line**: the `(loc)` a reader copies must stay a bare locator,
    # and a heading is not part of one. `find` is the verb for piping and is
    # deliberately unchanged.
    for r in results:
        record = _record_for(root, r.id)
        mark = f"{ARCHIVED_MARKER} " if r.archived else ""
        print(f"{r.score:.4f}  {mark}{_title_from(root, record, r.title)}  ({r.loc})")
        if show_sections:
            for heading in _headings_for(record, args.query):
                print(f"        {SECTION_MARKER} {heading}")
    if getattr(args, "explain", False):
        print(f"\n[{path}]")
    if why is not None:
        _declare_derivation(why)
    _declare_archived(results, tune.archived_weight)
    _declare_confidence(block, _show_band(args))
    return 0


def _derivation_for(root: Path, args, results, path, signals, trace, tune):
    """Assemble the `--why` block. **Never raises** — see `_fill_confidence`.

    ⚠ **The untuned comparison is a SECOND QUERY, and that is deliberate.**
    Threading a parallel untuned score through the ranker would double the hot
    path's work for every caller to serve a diagnostic almost nobody asks for.
    Lucene's `explain` makes the same trade — an explanation is a second,
    narrower query, never a tax on the first — and here it is paid only when
    `--why` is passed. It is also the only honest way to answer *"is this
    document first because of the corpus, or because somebody edited
    `tune.toml`?"*, which is the question a tuned ranker makes unanswerable
    from the output alone.
    """
    try:
        from . import provenance

        untuned = None
        if provenance.tune_digest(root) != "none":
            try:
                # ⚠ The untuned arm carries the SAME expansion. `--why`'s
                # question is *"is this document first because of the corpus or
                # because somebody edited tune.toml"*, and dropping the
                # expansion here would answer a third question neither of them
                # asked.
                untuned, _ = run_query(
                    root, args.query, args.top,
                    force_scan=_force_scan(args), use_tune=False,
                    expand=_expand_of(args),
                )
            except Exception:
                untuned = None
        stats = signals.get("stats") if isinstance(signals, dict) else None
        return provenance.derive(
            root,
            args.query,
            results,
            path=path,
            stats=stats,
            records=lambda doc_id: _record_for(root, doc_id),
            window=(trace or {}).get("window"),
            pre_rerank=(trace or {}).get("pre_rerank"),
            untuned=untuned,
            multiplier=getattr(tune, "archived_weight", 1.0),
            expand=_expand_of(args),
        )
    except Exception:  # pragma: no cover - a diagnostic must not break an answer
        return None


def _declare_derivation(why) -> None:
    """The `--why` block, on **stderr**.

    Same rule as the progress plane (W-64), the archived-results signal and the
    confidence line: `ask`'s stdout is what a human copies and a script parses,
    and it stays byte-identical with this flag on or off. The machine-readable
    form is `--json`, which is where a machine reader should look.
    """
    g = why.gates
    print(
        f"[why] reachable {g.reachable} -> window {g.in_window} -> "
        f"placed {g.placed} -> answered {g.answered}"
        + (f" (cut at {g.cut_score:.4f})" if g.cut_score is not None else ""),
        file=sys.stderr,
    )
    for doc in why.documents:
        bits = [f"#{doc.rank + 1} {doc.loc} {doc.score:.4f}"]
        if doc.matched:
            bits.append("matched " + ",".join(t.term for t in doc.matched))
        if doc.missing:
            bits.append("absent " + ",".join(doc.missing))
        if doc.rank_before_rerank is not None and doc.rank_before_rerank != doc.rank:
            bits.append(f"rerank {doc.rank_before_rerank + 1}->{doc.rank + 1}")
        if doc.rank_untuned is not None and doc.rank_untuned != doc.rank:
            bits.append(f"untuned #{doc.rank_untuned + 1}")
        print("       " + "  ".join(bits), file=sys.stderr)


def cmd_find(args) -> int:
    """Ranked documents, one per line — the terse listing verb."""
    root = _root()
    tune = _tune_for(root, args)
    signals: dict = {}
    results, _path, fused = _run_fused(
        root, args, args.top, tune=tune, confidence_out=signals,
    )
    block = signals.get("confidence")
    _declare_no_accelerator(root)

    if args.json:
        payload: dict = {"results": [_as_dict(root, r, args.query) for r in results]}
        if fused:
            payload["fused"] = True
        # ADR-CONFIDENCE decision 11: present only under `--band`. **Absent
        # means NOT ASKED FOR — it is never a claim about the answer**, which
        # is why the schema makes it conditional rather than optional-in-prose.
        if block is not None and _show_band(args):
            payload["confidence"] = block.as_dict()
        print(json_mod.dumps(payload, indent=2))
        _declare_archived(results, tune.archived_weight)
        return 0

    if not results:
        print("No confident matches.")
        _declare_confidence(block, _show_band(args))
        return 0

    # **Bare paths, deliberately unmarked.** `find` exists to be piped, so a
    # `[archived]` prefix on stdout would be read as part of the filename — the
    # concrete reason ADR-DIR-LIST decision 12 put the note on stderr. The flag
    # is carried in `--json`, which is where a machine reader should look.
    for r in results:
        print(r.loc)
    _declare_archived(results, tune.archived_weight)
    _declare_confidence(block, _show_band(args))
    return 0


#: How many ranked documents `answer` hands to the refer plane. **W-108.**
#:
#: `answer` used to refer exactly one, which capped it at `recall@1` — `0.5969`
#: against `0.9535` at k=5 on the 43 graded playground queries, where 19 of the
#: 43 have more than one relevant document
#: ([the first-recall run](../../../work/regression/2026-08-28-first-recall/report.md)).
#: That was never a ranking failure: `refer()` loops candidates and `_rescore`
#: computes passage `df` across all of them, so a fair cross-document passage
#: contest existed and was being handed a field of one.
#:
#: **Three, and not a tunable.** The uplift is bounded by the `recall@1 ->
#: recall@3` gap, the byte budget is unchanged (`per_doc_fraction` bounds each
#: document once there is more than one), and every extra candidate is a real
#: fetch against someone's source system. A `[refer]` key here would be a new
#: default nobody has measured, on a verb whose defaults are already an open
#: question on Arpit's desk.
ANSWER_TOP = 3


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
    signals: dict = {}
    # ⚠ **`answer` takes ONE question and no `-q`** — [ADR-ANSWER](../../..)
    # decision 4: the verb means one answer. `--expand` applies here exactly as
    # it does to `ask`, because expanding a question is not asking a second one.
    results, _ = run_query(
        root, args.query, ANSWER_TOP, force_scan=_force_scan(args), tune=tune,
        confidence_out=signals, expand=_expand_of(args),
    )
    block = signals.get("confidence")
    _declare_no_accelerator(root)

    if not results:
        if args.json:
            # `"source"` is the key ADR-ANSWER tells callers to switch on when
            # the refer plane lands, so it must be present on the no-match
            # branch too — an absent key is a trap, not a signal (W-48).
            # `confidence` is required on this branch for the same reason, and
            # it is the branch that most needs it: `band: none` is fux saying
            # *do not answer this*, which is a stronger claim than an empty
            # `results` array a caller may read as "try harder".
            _emit(
                _gated(
                    {
                        "answer": None,
                        "citation": None,
                        "source": "index",
                        "confidence": _block_dict(block),
                    },
                    _show_band(args),
                ),
                "answer_payload",
                band_requested=_show_band(args),
            )
        else:
            print("No confident matches.")
            _declare_confidence(block, _show_band(args))
        return 0

    best = results[0]
    no_refer_flag = getattr(args, "no_refer", False)

    if not no_refer_flag:
        referred = _answer_via_refer(root, args.query, results, tune)
        if referred is not None:
            _declare_change_since_last_ask(root, args.query, referred)
            # ⚠ **The UPGRADED block, not the one `run_query` produced.**
            # `_print_refer_answer` raises `verified` to the refer plane's real
            # verdict before printing; handing the receipt the pre-upgrade
            # block made it say `unverified` beside its own `verdicts` saying
            # `current` — two statements about one answer disagreeing, which is
            # the exact failure this plane exists to prevent. Caught by running
            # it, not by a test, which is why the regression test below exists.
            block = _upgraded(block, referred)
            extra = _provenance_for(root, args, referred, block)
            _print_refer_answer(referred, args.json, block, extra=extra, show_band=_show_band(args))
            return 0

    extra = _provenance_for(root, args, None, block, best=best)
    return _print_index_answer(
        root, best, args.json, requested=no_refer_flag, block=block, extra=extra,
        show_band=_show_band(args),
    )


def _provenance_for(root: Path, args, bundle, block, *, best=None) -> dict:
    """`--audit` and `--receipt`, and the journal. **Never raises.**

    Returns the keys to merge into `--json`; `{}` when neither flag was passed,
    so an existing consumer's parse is untouched (W-48 — an ADDITIVE key is
    safe, an absent one must never be readable as a claim).

    ⚠ **The journal is written only on `--journal`, and that is the consent.**
    L8 as reverted permits a plaintext local log; it does not oblige fux to
    start one behind a consumer's back. A `$0`, offline tool whose pitch is
    *nothing leaves your machine* may not quietly begin recording questions
    because a law was relaxed. Always-on journalling is a real want and it needs
    a `.fux/tune.toml` key, which is an ADR-TUNE change deliberately not made
    here — it is a fork, and this session may not pick a default on one.
    """
    want_audit = bool(getattr(args, "audit", False))
    want_receipt = bool(getattr(args, "receipt", False))
    want_journal = bool(getattr(args, "journal", False))
    if not (want_audit or want_receipt or want_journal):
        return {}
    out: dict = {}
    try:
        from . import provenance

        record = bundle.as_record() if bundle is not None else None
        if want_audit and record is not None:
            out["audit"] = record

        if want_receipt or want_journal:
            if record is not None:
                subject = [
                    {"id": c["id"], "loc": c["locator"], "sha": c["sha"]}
                    for c in record["citations"]
                ]
                verdicts = record["documents"]
            elif best is not None:
                # ⚠ The index branch fetched nothing, so there is no `sha` of
                # cited bytes to name. An empty string here would look like a
                # digest; the key is omitted instead, and `verify` reports
                # `unverifiable` rather than pretending to a subject.
                subject = [{"id": best.id, "loc": best.loc}]
                verdicts = []
            else:
                subject, verdicts = [], []
            payload = provenance.receipt(
                root,
                args.query,
                expand=_expand_of(args),
                path="refer" if record is not None else "index",
                subject=subject,
                confidence=_block_dict(block),
                verdicts=verdicts,
            )
            if want_receipt:
                out["receipt"] = payload
            if want_journal:
                provenance.remember(root, payload)
    except Exception:  # pragma: no cover - provenance must not break an answer
        return out
    return out


def cmd_verify(args) -> int:
    """`fux verify <receipt>` — does this answer still reproduce?

    **Four states, never a boolean**, and the exit code carries the same
    distinction: `0` reproduced, `1` drifted or unverifiable. A caller that
    branches on the exit code learns *something happened*; a caller that reads
    `verdict` learns what. Collapsing them would make *"we could not check"*
    indistinguishable from *"we checked and it was fine"* — the failure this
    repo has now refused four times (`max_age_seconds`, `cached` reported as
    `current`, a line range for `ask`, and this).

    ⚠ **`--rerun` is opt-in and its absence is REPORTED, not hidden.** Without
    it this verifies the *inputs* — index digest, tune digest, engine version —
    and returns `unverifiable` with a note saying the answer was not re-run.
    Silently returning `reproduced` on matching inputs would be a claim about
    an answer nobody recomputed.
    """
    from . import provenance

    root = _root()
    path = Path(args.receipt)
    try:
        payload = json_mod.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise FuxError(f"cannot read {path}: {exc}") from exc
    except ValueError as exc:
        raise FuxError(f"{path} is not JSON: {exc}") from exc

    # A receipt may have been captured whole (`--receipt` writes it under the
    # `receipt` key of the answer payload) or extracted. Accept both, because
    # `fux answer --receipt --json > r.json` is the obvious thing to type.
    if isinstance(payload, dict) and "receipt" in payload:
        payload = payload["receipt"]

    replay_expand = ""
    try:
        replay_expand = str(payload["predicate"]["inputs"].get("expand", "") or "")
    except Exception:  # pragma: no cover - a malformed receipt is verify's problem, not this line's
        replay_expand = ""

    rerun = None
    if getattr(args, "rerun", False):
        def rerun(query: str):
            # ⚠ **`ANSWER_TOP`, not 1** — a rerun that retrieves a different
            # number of candidates than `cmd_answer` did is not a rerun. This
            # read `1` while `answer` read `1` too; when W-108 moved one it had
            # to move both, or `verify --rerun` would report `drifted` on every
            # multi-document answer and be right about nothing.
            # ⚠ **The expansion is replayed too, from the receipt's own
            # inputs.** Re-running the bare question against an answer that was
            # produced with `--expand` compares two different queries and
            # reports `drifted` for a reason that has nothing to do with the
            # corpus.
            results, _ = run_query(
                root, query, ANSWER_TOP, force_scan=_force_scan(args), expand=replay_expand,
            )
            if not results:
                return []
            bundle = _answer_via_refer(root, query, results, _tune(root))
            if bundle is None:
                return []
            return [
                {"id": c.doc_id, "sha": c.sha} for c in bundle.assembled.citations
            ]

    result = provenance.verify(root, payload, rerun=rerun)
    if args.json:
        print(json_mod.dumps(result.as_dict(), indent=2))
    else:
        print(result.verdict + (f" — {result.note}" if result.note else ""))
    return 0 if result.verdict == provenance.REPRODUCED else 1


def _block_dict(block) -> dict:
    """A confidence block as JSON, or the honest empty one when it could not be
    computed.

    **Never absent, and never invented.** `answer_payload` declares
    `confidence` required on every branch, so an absent key would fail fux's own
    output contract; a *fabricated* healthy block would be worse still. The
    fallback is the block that claims nothing: no coverage, no separation, no
    support, `answerable: false`.

    ⚠ **Its two floors are the ENGINE defaults, not the repo's**, because this
    branch runs only when the block could not be computed at all and there is
    no tune in hand. `band` is `none` regardless — the floors gate nothing here
    — but a consumer diffing floors across answers will see this one differ.
    """
    if block is None:
        from .confidence import Confidence

        return Confidence(0.0, 0.0, 0, "unverified", ()).as_dict()
    return block.as_dict()


def _answer_via_refer(root: Path, query: str, results: list[AskResult], tune: "Tune"):
    """`None` when NO candidate produced a usable citation — never raises.

    Takes the ranked list since W-108 and reads each candidate's indexed `sha`
    from its own shard. **A candidate whose record cannot be read is skipped,
    not fatal**: it is one document short of a contest, which is the same
    degradation `refer()` applies to one that cannot be fetched. Only an empty
    set — every record unreadable — returns `None` here, and `refer()` returning
    no citations returns `None` there; both land on the index fallback.
    """
    from .refer_answer import answer_via_refer

    citations: list[tuple[str, str, str]] = []
    for result in results:
        record = _record_for(root, result.id)
        if record is None:
            continue
        citations.append((result.id, result.loc, record["sha"]))
    if not citations:
        return None
    return answer_via_refer(root, query, citations, tune=tune)


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

        # ⚠ **The documents that were CITED, not every document fetched**
        # (W-108). With one candidate the two sets were identical. With three,
        # a document can be fetched, lose the passage contest and appear in no
        # citation — and reporting *"this changed since you last asked"* about
        # bytes that are in neither answer describes a comparison the caller
        # never saw. The report is about the answer that was given.
        answered = {c.doc_id for c in bundle.assembled.citations}
        cited = {
            d.loc: (d.verdict.fetched_sha or d.verdict.indexed_sha)
            for d in bundle.documents
            if d.doc_id in answered
        }
        if not cited:
            return
        change = lastcited.compare(root, query, cited)
        line = change.line()
        if line:
            print(line, file=sys.stderr)
        lastcited.remember(root, query, cited)
    except Exception:  # pragma: no cover - a report must not break an answer
        pass


def _freshness_of(bundle) -> str:
    """The refer plane's verdict for the answer's own document.

    ⚠ **The document that produced the WINNING passage, not the first
    candidate** (W-108). With one candidate those were the same object and
    `documents[0]` was correct; with three they are routinely different, and
    reporting candidate one's verdict beside candidate two's passage is the
    collapse this plane's four states exist to prevent — a `current` label on
    bytes nobody checked.

    `unverified` when the plane looked at nothing — *"we did not look"*, never
    folded into `current`.
    """
    return _freshness_by_doc(bundle).get(_winning_doc_id(bundle), "unverified")


def _winning_doc_id(bundle) -> str:
    """The document behind the top-scoring citation, or the first candidate."""
    citations = bundle.assembled.citations
    if citations:
        return citations[0].doc_id
    return bundle.documents[0].doc_id if bundle.documents else ""


def _freshness_by_doc(bundle) -> dict[str, str]:
    """`doc_id -> verdict label`, for every document the plane looked at."""
    return {d.doc_id: d.verdict.label for d in bundle.documents}


def _upgraded(block, bundle):
    """Raise a confidence block to the refer plane's real verdict.

    **One function, two callers** — the printer and the receipt — because the
    alternative is what actually shipped for one run: the printed block
    upgraded, the receipt's not. Idempotent, so calling it twice is harmless.
    """
    if block is None:
        return None
    return block.with_verified(_freshness_of(bundle))


def _gated(payload: dict, show: bool) -> dict:
    """Drop `confidence` from an `answer` payload when `--band` was not passed.

    ⚠ **Applied to the BUILT payload rather than at each construction site**,
    so the three `answer` branches — refer, index, and no-match — cannot
    disagree about when the block is present. They disagreed once already
    (a receipt read `verified: unverified` beside verdicts saying `current`),
    and that class of defect is what one choke point prevents.
    """
    if not show:
        payload.pop("confidence", None)
    return payload


def _print_refer_answer(bundle, as_json: bool, block=None, extra=None, show_band: bool = False) -> None:
    """The fetched, re-scored answer — and the one path where `verified` is real.

    **This is where the fourth signal stops being a placeholder.** `ask` and
    `find` never fetch, so they can only ever report `unverified`. Here the
    refer plane has actually compared the fetched bytes against the sha the
    index ranked on, so the block is upgraded to that verdict before it is
    emitted — and a `stale` verdict demotes the band to `partial` on its own,
    with no threshold involved (ADR-CONFIDENCE decision 3).
    """
    citations = bundle.assembled.citations
    freshness = _freshness_of(bundle)
    by_doc = _freshness_by_doc(bundle)
    block = _upgraded(block, bundle)

    if as_json:
        # ⚠ **This branch used to print unvalidated.** `output.schema.json`
        # claims *"`fux answer --json` is validated against this before it is
        # printed"*, and only the no-match branch went through `_emit` — a
        # promise in a declaration that nothing enforced, which is the same
        # defect class W-84 found in the MCP tool descriptions. Routed through
        # `_emit` here so the claim is true of every branch.
        payload = {
            "answer": {
                # ⚠ **`id`/`loc`/`sha` per passage are ADDITIVE and W-108
                # requires them.** Passages may now come from different
                # documents, and a list of texts under a single top-level
                # `citation` would attribute the second document's prose to the
                # first — in the one product whose promise is that a citation is
                # checkable. No key was removed or repurposed, which is W-48's
                # actual rule; `citation` still names the winning passage's
                # document and means exactly what it meant.
                "passages": [
                    {
                        "id": c.doc_id,
                        "loc": c.locator,
                        "sha": c.sha,
                        "heading": c.heading,
                        "text": c.text,
                        "score": c.score,
                    }
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
            "confidence": _block_dict(block),
        }
        payload.update(extra or {})
        _emit(_gated(payload, show_band), "answer_payload", band_requested=show_band)
        return

    # ⚠ **One locator PER PASSAGE, not one for the answer** (W-108). This
    # printed every passage above `citations[0]`'s locator, which was already
    # wrong before the top-3 change — a second passage of the same document has
    # its own line range, and the single trailing line named the first one's.
    # With passages from three documents it would name the wrong *file*.
    for c in citations:
        if c.heading:
            print(f"# {c.heading}\n")
        print(c.text)
        print()
        print(f"  -- {c.locator} (sha {c.sha[:12]}, {by_doc.get(c.doc_id, freshness)})")
        print()
    _declare_provenance(extra)
    _declare_confidence(block, show_band)


def _print_index_answer(
    root: Path, best: AskResult, as_json: bool, *, requested: bool, block=None, extra=None,
    show_band: bool = False,
) -> int:
    """The M2 path: the winning record's own extracted structure — no fetch.

    `requested` distinguishes why: the caller passed `--no-refer`, versus
    refer being tried and producing nothing usable (unreachable source, no
    fetcher configured, a citation deleted from the working tree).
    """
    phrases = _phrases_for(root, best.id)
    title = _resolve_title(root, best.id, best.title)

    if as_json:
        payload = {
            "answer": {"title": title, "phrases": phrases},
            "citation": {"id": best.id, "loc": best.loc, "score": best.score},
            "source": "index",
            # Deliberately NOT upgraded: nothing was fetched on this
            # path, so `verified` stays `unverified`. Reporting
            # `current` because the index is internally consistent
            # would be the exact collapse the refer plane's four-state
            # verdict exists to prevent.
            "confidence": _block_dict(block),
        }
        payload.update(extra or {})
        _emit(_gated(payload, show_band), "answer_payload", band_requested=show_band)
        return 0

    print(title)
    for phrase in phrases:
        print(f"  - {phrase}")
    print(f"\n  -- {best.loc}")
    reason = "--no-refer was passed" if requested else "the source could not be reached or verified"
    print(f"\n(from the index's own structure — {reason})")
    _declare_provenance(extra)
    _declare_confidence(block, show_band)
    return 0


def _declare_provenance(extra) -> None:
    """The receipt digest and the audit summary, on **stderr**.

    Text mode gets the *digest*, not the receipt: a receipt is 2-10 KB of JSON
    and a terminal is not where anyone reads one. `--json` carries the object.
    Same stdout-stays-identical rule as every other signal on this surface.
    """
    if not extra:
        return
    audit = extra.get("audit")
    if audit:
        budget = audit.get("budget", {})
        print(
            f"[audit] {len(audit.get('documents', []))} document(s) examined, "
            f"{budget.get('used', 0)}/{budget.get('bytes', 0)} bytes used, "
            f"{budget.get('dropped', 0)} passage(s) dropped",
            file=sys.stderr,
        )
    payload = extra.get("receipt")
    if payload:
        from . import provenance

        print(f"[receipt] {provenance.receipt_sha(payload)}", file=sys.stderr)


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
    return _title_from(root, _record_for(root, doc_id), fallback_title)


def _title_from(root: Path, record: dict | None, fallback_title: str) -> str:
    """`_resolve_title`'s second half, split out so a caller that already holds
    the record does not read the same shard twice.

    W-84: `ask` needs the record for its `phrases` as well as its title, and
    two lookups per result for one record is a cost with no reader. The
    behaviour is `_resolve_title`'s exactly — that name is what ADR-ASK cites
    and what P5 decided, and it still does what it says.
    """
    from .. import store as store_mod

    if record is None:
        return fallback_title
    return store_mod.display_title(record, cache=store_mod.DisplayCache(root))


def _as_dict(root: Path, result: AskResult, query: str, *, sections: bool = True) -> dict:
    """`AskResult` as JSON, with `title` upgraded through the P5 display cache
    and W-84's matched `headings` alongside it.

    **`headings` is always present, even when empty — WHEN IT IS ASKED FOR.**
    An absent key is a trap, not a signal (W-48): a caller cannot tell "this
    document has no matching heading" from "this version of fux does not do
    headings", so `[]` is the answer to the first and the key never simply
    disappears because nothing matched. Both paths produce it from the same
    committed record, so the differential law is untouched: it is a function
    of a list the two generators already agree on.

    ⚠ **`sections=False` is the ONE case the key is absent, and it is not the
    W-48 trap** (ADR-OUTPUT decision 21). It is `confidence`-under-`--band`'s
    shape exactly: **absent means NOT ASKED FOR — never a claim about the
    document.** The distinction W-48 is about is *"empty vs. unsupported"*,
    and both of those still resolve to `[]`; this third state is *"the
    consumer said don't compute it"*, which only the consumer can set and
    only on `ask`. `find` has no `sections` key, so its payload is unchanged.
    """
    record = _record_for(root, result.id)
    payload = dict(result.__dict__)
    payload["title"] = _title_from(root, record, result.title)
    if sections:
        payload["headings"] = _headings_for(record, query)
    return payload
