"""`fux doctor`'s reader rows — the ranking priors, the band's floor, the
accelerator, the journal and the freshness share — and a reader-only doctor.

Reader layer (W-282). `doctor.py` (the engine) runs these among every other
row; on a `fux-reader` install without the engine, `cmd_doctor` here runs the
core rows and these, in the order `health.ROWS` states
([SR-DOCTOR](../../../records/0152_doctor.md)).
"""

from __future__ import annotations

import json
from pathlib import Path

from .. import config as config_mod
from ..errors import FuxError
from .. import output_config
from ..constants import fixed
from ..health import (  # noqa: F401
    Check,
    _is_git_tracked,
    _records,
)
from .confidence import FLOOR_OFF_NOTE


#: The ranking priors that ship at a value which makes them do nothing, with
#: the record field each one reads.
#:
#: `(key, no-op value, record field, what the field means)`. `None` for the
#: field means the prior is not driven by a per-record declaration.
#:
#: ⚠ **There were FOUR until 2026-09-13 and there is ONE.** Arpit ruled all
#: three DOCUMENT priors closed that day on VERDICT-W143's evidence —
#: `superseded_weight` (W-151), then `archived_weight` and
#: `recency_half_life_days` (W-152). A prior no single global value can set
#: correctly is not a prior waiting for a number, and disclosing it as one was
#: misleading. **The facts they read all survive and all reach a caller.**
#:
#: `rerank_weight` is the survivor and was never the same question: it ships
#: **off** rather than neutral, acts on refer-plane passage proximity rather
#: than a document flag, and its open question is cost, not which value (W-154).
_NO_OP_PRIORS = (
    ("rerank_weight", 0.0, None, ""),
)


def _no_op_priors(root: Path) -> Check:
    """Every ranking prior that is BUILT, WIRED and SWITCHED OFF at its default.

    **W-126 part B, on Arpit's ask of 2026-09-11.** Four mechanisms — the
    archived demotion, the supersession demotion, the proximity reranker and the
    recency decay — were each implemented, each read their input, and each
    shipped at a value that made them return the score unchanged, with nothing
    telling the repo that declared `archived=true` it was getting nothing.

    🔴 **THREE OF THE FOUR WERE REMOVED ON 2026-09-13** rather than tuned
    (W-151, W-152; SR-TUNE decision 15), which is the disclosure working: once
    a dead knob is visible, *"what value should it be?"* turns out to be the
    wrong question, and **no single global value clears the bar for any of them**
    (`work/regression/2026-09-12-priors-and-tables/VERDICT-W143.md`).

    **What is left is `rerank_weight`**, which ships **off** rather than neutral
    and whose open question is cost, not which value. This row keeps disclosing
    it, and keeps refusing to recommend one.

    ⚠ **This is a DISCLOSURE and not a ranking change**, and the distinction is
    the whole reason it could be built today. Whether any of these defaults
    should move is blocked on a measurement nobody can run yet (the hand-graded
    corpus is uncommitted), and Arpit ruled *remeasure first* on
    `superseded_weight` and `rerank_weight` the same day.

    🔴 **So it REFUSES to recommend a value, deliberately.** Recommending one is
    the remeasure's job. `P-SUPERSEDE` is the standing proof of why: at `0.5`
    the supersession prior fixed two queries and **broke two**, and every
    broken query had the superseded document as its correct answer. A `doctor`
    row that said *"try 0.5"* would have been handing out the exact change a
    frozen pre-registration already failed — and in the end that knob, and the
    two beside it, were deleted rather than given a number.

    **What it does say is the part nobody could see:** for each dead prior, how
    many documents in THIS corpus declare the thing it would have acted on. A
    repo with 0 archived documents has a knob that is off and irrelevant; a
    repo with 40 has one that is off and costing it something. Those are
    different findings and a flat list of four defaults cannot tell them apart.

    A **warning**, never an error: shipping at a default is not a broken
    install, and every one of these values is a legitimate choice somebody may
    have made on purpose.
    """
    from ..tune import load as load_tune

    try:
        tune = load_tune(root, enabled=True)
    except FuxError:
        # Not assessed rather than assessed against a value from nowhere: L12
        # leaves no default to read, and the `tune.toml loads` row already
        # names what is wrong with the file.
        return Check(
            "ranking priors",
            True,
            "not assessed - .fux/config/tune.toml does not load (see `tune.toml loads`)",
            level="warn",
        )

    records = _records(root)
    dead: list[str] = []
    for key, no_op, field, meaning in _NO_OP_PRIORS:
        if getattr(tune, key) != no_op:
            continue
        part = f"{key}={no_op:g}"
        if field is not None and records:
            declared = sum(1 for record in records.values() if record.get(field))
            part += f" ({declared} document(s) {meaning})"
            # 🔴 **SWITCHED OFF and UNREACHABLE are different problems with
            # different remedies, and printing the count alone left a reader to
            # notice the zero.** Changing the value fixes the first and does
            # nothing whatever about the second. Measured 2026-09-11: three of
            # the four priors returned BYTE-IDENTICAL results at every value
            # including 0.0 on a corpus that declares none of what they read,
            # and the premise that they were testable there had stood in the
            # queue for two weeks because the documents discuss supersession in
            # PROSE while declaring none of it.
            #
            # ⚠ **It states a fact and still recommends nothing.** *"0 documents,
            # so this knob is inert here"* is derived from data already in hand;
            # *"0 documents, so set it to X"* would be the R10 failure this row
            # exists to refuse.
            if declared == 0:
                part += " - so changing this value would change NOTHING in this repository"
        dead.append(part)

    intent_part, intent_dead = _intent_weight_part(tune, records)
    if intent_dead:
        dead.append(intent_part)

    if not dead:
        return Check(
            "ranking priors",
            True,
            "every ranking prior is set to a value that does something"
            + (f"; {intent_part}" if intent_part else ""),
        )
    return Check(
        "ranking priors",
        False,
        "BUILT, WIRED AND SWITCHED OFF at these values: "
        + "; ".join(dead)
        + ". Each is implemented and reads its input, and at the value shown it "
        "returns the score unchanged. fux states this and does NOT recommend a "
        "value: the one change ever measured (superseded_weight at 0.5, a knob "
        "since REMOVED) fixed two queries and broke two, and every broken one had "
        "the superseded document as its correct answer"
        + ("" if intent_dead or not intent_part else f". Also: {intent_part}"),
        level="warn",
    )


def _intent_weight_part(tune, records: dict) -> tuple[str, bool]:
    """`intent_weight` with its count of documents of each preferred type.

    [SR-DOCTOR](records/0152_doctor.md) decision 5a owed this: the intent prior
    (SR-RANKING decision 13) is the one prior driven by a per-record
    declaration, namely the type `[doctype]` assigns a document's location. The
    count is taken with `intent.type_for`, the resolver ranking itself uses, so
    the row cannot count a document the ranker would not.

    Returns `(text, dead)`. **Dead is only a declared `[doctype]` that is off
    or reaches no document** - an empty `[doctype]` is the shipped state, the
    prior is simply not opted into, and a warning on every default repository
    would teach readers to ignore the row. It is still stated, with the zero
    clause 5a asks for. **Recommends no value**, like the rest of the row.
    """
    from ..query import intent

    weight = tune.intent_weight
    counts = dict.fromkeys(sorted(intent.TYPES), 0)
    if tune.doctype:
        for record in records.values():
            kind = intent.type_for(record.get("loc", ""), tune.doctype)
            if kind in counts:
                counts[kind] += 1
    total = sum(counts.values())
    listed = ", ".join(f"{kind}={n}" for kind, n in counts.items())
    part = f"intent_weight={weight:g} ({total} document(s) of a preferred type: {listed})"
    if total == 0:
        part += " - so changing this value would change NOTHING in this repository"
        if not tune.doctype:
            part += " ([doctype] in tune.toml is empty, so the prior is not in use)"
    dead = bool(tune.doctype) and (weight <= 0 or total == 0)
    return part, dead


def _priority_keys(root: Path) -> Check:
    """Every `[priority]` key in `tune.toml` reaches a listed source.

    [SR-TUNE](records/0135_tuning.md) decision 10a: an orphaned priority is
    silently inert, and nothing said so. The tune-load warning half of that
    decision is dropped (the loader has no source lists, and a seam for one is
    not worth a second reader); this row is the durable half.

    **The match rule is `Weighting.priority_for`'s, called, not re-spelled** -
    a key matches a location exactly or at a `/` boundary. A key is live when
    it matches a source entry, or sits under one (`docs/runbooks` under the
    listed `docs`), since both ways can reach a document. A warning: a source
    can be legitimately absent for a moment, which is why decision 10a does not
    fail a read over it.
    """
    import math

    from ..acquire import sourcelist
    from ..query.rank import Weighting
    from ..tune import load as load_tune

    name = "priority keys"
    try:
        tune = load_tune(root, enabled=True)
    except FuxError:
        return Check(name, True, "not assessed - .fux/config/tune.toml does not load (see `tune.toml loads`)")
    if not tune.priority:
        return Check(name, True, "no [priority] keys declared")
    try:
        config = config_mod.load(root)
    except FuxError:
        return Check(name, True, "not assessed - fux.toml does not load; see its row")

    from ..acquire import sourcesfile

    entries: list[str] = []
    try:
        parsed = sourcesfile.parse(
            (root / config.sources_file).read_text(encoding="utf-8"), origin=config.sources_file
        )
        entries = [e.value for e in (*parsed.paths, *parsed.urls)]
    except (OSError, FuxError):
        pass

    def reaches(key: str, entry: str) -> bool:
        probe = math.inf
        return (
            Weighting(priority=((key, probe),)).priority_for(entry) == probe
            or Weighting(priority=((entry, probe),)).priority_for(key) == probe
        )

    orphans = [key for key, _ in tune.priority if not any(reaches(key, e) for e in entries)]
    if not orphans:
        return Check(name, True, f"{len(tune.priority)} [priority] key(s), each reaching a listed source")
    return Check(
        name,
        False,
        f"{len(orphans)} [priority] key(s) match no listed source and so scale nothing: "
        + ", ".join(f"`{k}`" for k in orphans[:5])
        + (f" and {len(orphans) - 5} more" if len(orphans) > 5 else "")
        + ". A key matches a location exactly or at a `/` boundary (SR-TUNE decision 8a); "
        "fix the spelling or `fux add` the source",
        level="warn",
    )


def freshness_counts(root: Path) -> dict[str, int]:
    """Verified-citation verdicts, by label, from the local receipt journal.

    **This is the veto check for two accepted records** —
    [SR-ACQUIRED](../../records/0145_acquired-plane.md) and
    [SR-URL-FRESHNESS](../../records/0147_url-freshness.md) both say
    *"reopen this decision if `as-ingested` exceeds a quarter of verified
    citations"* and both name `fux doctor --json` as how to check it. Until
    this existed neither veto could be run at all.

    ⚠ **The journal is the ONLY durable source, and it is opt-in.** A freshness
    verdict is produced at answer time by the refer plane and nothing else
    persists one; `.fux/runtime/provenance.jsonl` holds it only for answers run
    with `--journal`. So a repo that has never journalled has **no** answer
    here, which is reported as *unknown* rather than as a zero share — the two
    are different claims and collapsing them would let a repo that has never
    looked read as a repo that looked and found nothing.

    ⚠ **Local and gitignored (L9).** Everything read here lives under
    `.fux/runtime/`, reaches no committed byte, and goes nowhere.
    """
    try:
        from ..query import provenance
    except Exception:  # pragma: no cover - the package is always importable
        return {}
    counts: dict[str, int] = {}
    for entry in provenance.read_journal(root):
        predicate = entry.get("predicate") if isinstance(entry, dict) else None
        if not isinstance(predicate, dict):
            continue
        for verdict in predicate.get("verdicts") or []:
            if not isinstance(verdict, dict):
                continue
            label = verdict.get("freshness")
            if isinstance(label, str) and label:
                counts[label] = counts.get(label, 0) + 1
    return counts


#: The share above which `as-ingested` stops meaning *"a rare unreachable
#: source"* and starts meaning *"the fetch path is broken and the plane is
#: masking it"*. **Not a threshold this check invented** — it is the reopen
#: condition written into SR-ACQUIRED and SR-URL-FRESHNESS, quoted here so
#: the number has one home.
AS_INGESTED_VETO_SHARE = fixed("doctor", "as_ingested_veto_share")


def _freshness_share(root: Path) -> Check:
    """The `as-ingested` share — SR-ACQUIRED and SR-URL-FRESHNESS's veto.

    See `freshness_counts` for where the numbers come from and why the journal
    is the only source. The machine-readable form is `fux doctor --json`'s
    `freshness` block, which is what both records tell a reader to compare.

    A **warning** at the veto share, never an error: crossing it means a
    *decision* should be reopened, which is a person's work and not a broken
    install.
    """
    counts = freshness_counts(root)
    total = sum(counts.values())
    if not total:
        return Check(
            "freshness verdicts",
            True,
            "no receipts journalled - run an answer with `--journal` to record verdicts. "
            "Until then the as-ingested share (SR-ACQUIRED and SR-URL-FRESHNESS's veto "
            "condition) cannot be computed",
            level="warn",
        )
    as_ingested = counts.get("as-ingested", 0)
    share = as_ingested / total
    listed = ", ".join(f"{label} {counts[label]}" for label in sorted(counts))
    detail = f"{total} verified citation(s) journalled: {listed}"
    if share > AS_INGESTED_VETO_SHARE:
        return Check(
            "freshness verdicts",
            False,
            f"{detail} - as-ingested is {share:.0%}, past the {AS_INGESTED_VETO_SHARE:.0%} "
            "reopen condition in SR-ACQUIRED and SR-URL-FRESHNESS. That reads as a broken "
            "fetch path being masked by the retained bytes, not a rare unreachable source",
            level="warn",
        )
    return Check("freshness verdicts", True, f"{detail} - as-ingested {share:.0%}", level="warn")


def _journal_size(root: Path) -> Check:
    """The `fux answer --journal` log against `[cli.answer] journal_max_bytes`.

    [SR-PROVENANCE](records/0142_provenance.md) decision 15: the journal is a
    plaintext use record (gitignored, L9) and `journal_max` bounds it by COUNT,
    which says nothing about bytes when one receipt carries long passages. An
    absent journal is the normal state (it is opt-in), not a warning.
    """
    from ..query import provenance

    name = "journal size"
    path = provenance.journal_path(root)
    try:
        size = path.stat().st_size
    except OSError:
        return Check(name, True, "no journal (opt-in: `fux answer --journal`)")
    try:
        limit = output_config.load(root, enabled=True).resolve(
            "answer", "journal_max_bytes", None, as_json=False
        )
    except FuxError as exc:
        return Check(name, True, f"{size} bytes; limit not read - {exc}", level="warn")
    if size <= limit:
        return Check(name, True, f"{size} bytes, within journal_max_bytes={limit}")
    return Check(
        name,
        False,
        f"{path.name} is {size} bytes, above [cli.answer] journal_max_bytes={limit}. It holds the plaintext "
        "of what was asked and answered (gitignored, L9); delete it, or raise the key if you mean to keep more",
        level="warn",
    )


def _confidence_floors(root: Path) -> Check:
    """A confidence floor tuned to zero — the knob that turns a band OFF silently.

    🔴 **SR-CONFIDENCE decision 13's own words, about itself:** *"A consumer can
    set `separation_floor = 0.0` and no answer is ever `weak` again. That is
    tuning away the SIGNAL rather than the ranking, it is silent, and **nothing
    mechanical catches it.**"* This is the mechanical catch (W-164 gate 4).

    **It reports; it never refuses.** Decision 13 reversed a prohibition on
    exactly the reasoning that fux states costs rather than clamping knobs, and a
    row that refused the value would be decision 7 coming back in a new costume.
    Zero is a legal value; what it is not is a value a reader of the band should
    have to discover.

    ⚠ **`doc_coverage_floor = 0.0` is the ENGINE DEFAULT and is not reported.**
    That clause ships off — decision 13's own comment says `0.0 = the clause is
    OFF` — so firing on it would fire on every repo in the world. Only
    `separation_floor` has a non-zero default to be tuned away from, and only a
    `doc_coverage_floor` that was raised and then returned to zero would be
    interesting, which is not something the file can tell us.
    """
    from .. import tune as tune_mod

    try:
        resolved = tune_mod.load(root, enabled=True)
    except (FuxError, OSError):
        return Check("confidence floors", True, "tune.toml not parsed here - see its own row")
    if getattr(resolved, "separation_floor", None) != 0.0:
        return Check(
            "confidence floors",
            True,
            f"separation_floor = {getattr(resolved, 'separation_floor', '?')} - "
            "`weak` can still be reached",
        )
    return Check("confidence floors", False, FLOOR_OFF_NOTE, level="warn")


def _accelerator(root: Path) -> Check:
    """The derived accelerator: present, fresh, and genuinely not committed.

    A **warning**, never an error. The accelerator is disposable by design —
    `ask` answers correctly from the scan without it — so a missing or stale
    one costs speed, not correctness. Reporting it as a failure would train
    people to ignore a red doctor.
    """
    from ..derive import format as derive_fmt
    from ..derive.accel import is_fresh

    directory = derive_fmt.runtime_dir(root)
    if not (directory / derive_fmt.STATS_NAME).exists():
        return Check(
            "accelerator",
            True,
            "not built - `ask` uses the reference scan; run `fux build` for the fast path",
            level="warn",
        )

    tracked = _is_git_tracked(root, directory)
    if tracked:
        return Check(
            "accelerator",
            False,
            ".fux/runtime/ is TRACKED by git - it is a derived plane and must not be "
            "committed; check .fux/.gitignore lists `runtime/` (SR-DOTFUX)",
            level="warn",
        )

    if not is_fresh(root):
        return Check(
            "accelerator",
            True,
            "stale (the committed index changed since it was built) - `ask` falls back "
            "to the scan; run `fux build`",
            level="warn",
        )
    drifted = _shards_drifted(root, directory)
    if drifted:
        return Check(
            "accelerator",
            False,
            f"{len(drifted)} committed shard(s) do not match the sha the build recorded "
            f"(first: {drifted[0]}) although size and mtime "
            "agree - a byte edit that preserved both; `ask` may read a plane built from other "
            "bytes. Run `fux build`",
            level="warn",
        )
    return Check("accelerator", True, f"fresh, derived, untracked ({directory})", level="warn")


def _shards_drifted(root: Path, directory: Path) -> list[str]:
    """Shards whose bytes no longer hash to the sha `manifest.json` recorded at build time.

    **The deep check `accel.is_fresh` deliberately does not do**
    ([SR-RUNTIME-STAMP](../../records/0124_runtime-stamp.md) Consequences): `is_fresh`
    compares size and mtime, which a byte flip that preserves both defeats, and a
    re-hash on the query path would land inside R3's budget. `doctor` is not on that
    path, so it can afford the content-hash that is the real guarantee. A manifest
    that cannot be read is another row's finding, not drift. W-246 (B-086).
    """
    from .. import store as store_mod
    from ..derive import format as derive_fmt

    try:
        recorded = json.loads((directory / derive_fmt.MANIFEST_NAME).read_bytes())["shards"]
    except (OSError, ValueError, KeyError, TypeError):
        return []
    drifted = []
    # W-236: section shards are pinned under `sections/<name>` beside the rest.
    for path in [*store_mod.iter_shard_paths(root), *store_mod.iter_section_paths(root)]:
        name = derive_fmt.stamp_name(path)
        want = recorded.get(name)
        try:
            have = store_mod.content_sha(path.read_bytes())
        except OSError:
            continue
        if want is not None and want != have:
            drifted.append(name)
    return sorted(drifted)


#: This layer's rows, by the name `health.ROWS` gives them.
ROWS = {
    "_journal_size": _journal_size,
    "_confidence_floors": _confidence_floors,
    "_accelerator": _accelerator,
    "_no_op_priors": _no_op_priors,
    "_priority_keys": _priority_keys,
    "_freshness_share": _freshness_share,
}


def cmd_doctor(args) -> int:
    """`fux doctor` where the reader is installed and the engine is not."""
    if getattr(args, "fix", False):
        raise FuxError("`fux doctor --fix` writes the missing config keys, and writing is fux-writer's — install fux-engine")
    from ..health import provenance_counts, render, run_rows

    checks = run_rows(None, ROWS, progress=getattr(args, "progress", None))
    return render(args, checks, {"freshness": freshness_counts, "provenance": provenance_counts})
