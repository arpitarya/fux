"""`fux doctor` — install/environment health check, every row.

Checks today: python version, repo root found, `.fux/` writable, which `fux`
PATH resolves (SR-NODE-SEARCH R1a), and the two
layout assertions from SR-DOTFUX — the committed index is not git-ignored, and
nothing undeclared sits at the top level of `.fux/`.

The index check exists because the failure it catches is silent: a `.fux/*`
line in any `.gitignore` up the tree, or a consumer-edited `.fux/.gitignore`,
drops the committed index out of git with no error anywhere. Doctor stays
offline — it never touches the fetcher or the network.

**Engine layer since W-282.** The rows live by what they import — core in
`health.py`, the reader's in `query/health.py`, the writer's in
`ingest/health.py` — and the identifier-family rows here, because they read
`inspect/`. This module runs all of them in `health.ROWS` order and re-exports
every row, so `doctor._pii_timing` and its siblings keep their callers.
"""

from __future__ import annotations

from pathlib import Path

from .errors import FuxError
from . import health
from .config import find_root  # noqa: F401  (callers patch and read it here)
from .query.confidence import FLOOR_OFF_NOTE  # noqa: F401  (one sentence, two surfaces)
from .health import (  # noqa: F401  (every row keeps its doctor.* name)
    Check,
    DECODER_NETWORK_MODULES,
    PY_MIN,
    RETIRED_REFUSAL_STARTERS,
    _JSON_INDENT,
    _PROSE_SUFFIXES,
    _RETIRED_AGENT_DIRS,
    _SHIM_SUFFIXES,
    _acquired_health,
    _config_loads,
    _decoder_bindings,
    _decoder_imports,
    _dirs_exclusions_migrated,
    _dirs_file,
    _fetcher_bindings,
    _fetcher_capabilities,
    _fetcher_config_tables,
    _fetcher_routes,
    _fetchers_declaring_parallelism,
    _fux_on_path,
    _fux_on_path_row,
    _glob_suffix,
    _headings,
    _ignore_health,
    _ignore_reachable,
    _index_not_ignored,
    _index_temp_ignored,
    _installed_reader,
    _is_git_ignored,
    _is_git_tracked,
    _is_node_shim,
    _layout_declared,
    _listed_dirs_exist,
    _node_reader,
    _observed_types,
    _observers,
    _output_config_health,
    _parallel_policy,
    _pii_health,
    _pii_timing,
    _pinned_fetchers,
    _pinned_note,
    _pinned_without_bytes,
    _provenance,
    _python_version,
    _readme_current,
    _recency_prior,
    _records,
    _redaction_note,
    _refusal_health,
    _retired_agent_folders,
    _section_mode,
    _shadowed_rules,
    _starter_refusals_untouched,
    _suspended_pins,
    _thin_urls,
    _tune_config_health,
    _types_health,
    _unbound_types,
    _unfetched_note,
    _url_decoders,
    _url_health,
    _writable,
    provenance_counts,
)
from .ingest import health as writer_health
from .ingest.health import (  # noqa: F401
    _background_runner,
    _git_hooks,
    _daemon,
    _register,
    _meta_fields,
    _stale_redaction,
    _seeded_copies_current,
    _frozen_keys,
    _queue_no_decoder,
    _fix,
)
from .query import health as reader_health
from .query.health import (  # noqa: F401
    _no_op_priors,
    _intent_weight_part,
    _priority_keys,
    freshness_counts,
    _freshness_share,
    _journal_size,
    _confidence_floors,
    _accelerator,
    _shards_drifted,
    _NO_OP_PRIORS,
    AS_INGESTED_VETO_SHARE,
)


def _identifiers(root: Path) -> list[Check]:
    """W-233 — `.fux/identifiers.toml`: loads, the index agrees, families current,
    and a `[user]` regex behaves the same in both readers (F1–F3).

    **Four rows, and only the second is about the index.** A file that does not
    load stops `ingest`, `ask` and `find` alike, so it is an error. An index
    built under other families is an error too: the committed postings and the
    committed file disagree, and a question is analyzed under the file — which
    is exactly the state `fux ingest --check` fails CI on. New families found
    since the last write are a warning (F2): nothing is wrong, fux has only
    noticed something. The parity row runs only when a `[user]` regex exists;
    a template's two readers are held equal by the engine's own shared fixture.
    """
    from . import store as store_mod
    from .text import identifiers as ids_mod

    try:
        rules = ids_mod.load(root)
    except FuxError as exc:
        return [Check(
            "identifiers.toml loads",
            False,
            f"{exc} - `ingest`, `ask` and `find` refuse while this stands; "
            "`fux doctor --fix` restores a missing file",
        )]
    user_regex = [r for r in rules.rules if r.kind == "regex"]
    checks = [Check(
        "identifiers.toml loads",
        True,
        f"{ids_mod.FILE}: {len(rules.rules)} famil{'y' if len(rules.rules) == 1 else 'ies'}"
        + (f", {len(user_regex)} of them [user] regex" if user_regex else ""),
    )]
    header = store_mod.index_header(root)
    if header is None:
        return checks
    built = header.get(store_mod.IDENTIFIERS_KEY, "")
    checks.append(Check(
        "identifier families indexed",
        built == rules.digest,
        "the index was built under the families in the file"
        if built == rules.digest
        else f"the index was built under OTHER identifier families than {ids_mod.FILE} holds "
        "- run `fux ingest`; until then a question gains canonical terms the index lacks",
    ))
    checks.append(_identifier_families_current(root))
    if user_regex:
        checks.append(_identifier_regex_parity(root, user_regex))
    return checks


def _identifier_families_current(root: Path) -> Check:
    """F2: `[detected]` against what the lens finds now. A warning, never an error."""
    import tomllib

    from .inspect._scan import read_index_view
    from .inspect.idfamilies import identifier_families
    from .text import identifiers as ids_mod

    try:
        view = read_index_view(root, progress=health._PROGRESS)
        found = {f.template for f in identifier_families(root, view, examples=0, progress=health._PROGRESS).families}
        data = tomllib.loads(ids_mod.path(root).read_bytes().decode("utf-8-sig"))
    except (FuxError, OSError) as exc:
        return Check("identifier families current", True, f"skipped: {exc}", level="warn")
    on_disk = set((data.get("detected") or {}).get("families") or [])
    new, gone = found - on_disk, on_disk - found
    if not (new or gone):
        return Check("identifier families current", True, f"[detected] matches the {len(found)} the lens finds", level="warn")
    return Check(
        "identifier families current",
        False,
        f"{len(new)} new famil{'y' if len(new) == 1 else 'ies'} since the last write"
        + (f" (e.g. {sorted(new)[0]})" if new else "")
        + (f", {len(gone)} no longer detected" if gone else "")
        + " - `fux identifiers` shows them, `fux identifiers --write` records them",
        level="warn",
    )


def _identifier_regex_parity(root: Path, regexes) -> Check:
    """F3: each `[user]` regex, run by BOTH regex engines over this corpus.

    The first `inspect.toml [identifiers] parity_sample` indexed documents, in id
    order, are matched by Python `re` and by `node` running the same compiled
    source; any difference in the spans found is a FAIL naming the regex and
    the document. That is the one thing the static guard cannot prove: that two
    engines read an admitted pattern the same way on this corpus's text.
    """
    from itertools import islice

    from .inspect._scan import read_index_view
    from .inspect.idfamilies import corpus_texts, regex_parity
    from .text.identifiers import IdentifierRules

    view = read_index_view(root)
    texts = list(islice(corpus_texts(root, view), view.config.parity_sample))
    for rule in regexes:
        parity = regex_parity(IdentifierRules(rules=(rule,)), texts)
        if not parity.ran:
            return Check("identifier regex parity", True, "skipped: needs `node` on PATH", level="warn")
        if not parity.agree:
            return Check("identifier regex parity", False,
                         f"[user] regex {rule.source!r}: {parity.diff} - rewrite it as a template, or narrow it")
    return Check("identifier regex parity", True,
                 f"{len(regexes)} [user] regex agree in Python and Node over {len(texts)} documents")


#: Every non-core row, by the name `health.ROWS` gives it — the engine has all.
ROWS = {**reader_health.ROWS, **writer_health.ROWS, "_identifiers": _identifiers}


def run(start: Path | None = None, *, progress=None) -> list[Check]:
    return health.run_rows(start, ROWS, progress=progress)


def cmd_doctor(args) -> int:
    if getattr(args, "fix", False):
        _fix()
    checks = run(progress=getattr(args, "progress", None))
    return health.render(args, checks, {
        "runner": writer_health.runner_status,
        "freshness": freshness_counts,
        "provenance": provenance_counts,
    })
