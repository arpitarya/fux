"""`fux doctor`'s rows that need neither the reader nor the writer — and the run.

Core layer (W-282). Doctor's checks are split by what each one imports: the
ones here read only core (config, the store, the source plane, decoders); the
reader's live in `query/health.py`, the writer's in `ingest/health.py`, and the
engine's identifier rows in `doctor.py`, which runs all of them. **The row
order is stated once, below, as `ROWS`**, so every install prints its rows in
the same order `fux-engine` does. Doctor stays offline and read-only: it never
touches a fetcher or the network ([SR-DOCTOR](../../records/0152_doctor.md)).
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from . import __version__
from . import config as config_mod
from .config import DEFAULT_TYPES_FILE, FETCHERS_DIR, find_root
from .errors import FuxError
from . import output_config
from .store import fuxdir
from .constants import fixed


PY_MIN = tuple(fixed("python", "min"))


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    level: str = "error"  # "error" fails the command; "warn" only reports


#: The committed index, parsed once per `run()`. Three checks need per-record
#: fields (`mtime` for the recency prior, `loc` for the decoder bindings, the
#: `url:` prefix for URL health) and a 10 000-document corpus parsed three
#: times is a diagnostic command that feels broken. Reset at the top of every
#: `run()` rather than memoized forever: `doctor` is called twice in one
#: process by the test suite, and a cache that outlived a re-ingest would
#: report the previous index.
_RECORDS: dict[str, dict] | None = None


def _records(root: Path) -> dict[str, dict]:
    """Every committed record, or `{}` when the index is absent or unreadable.

    **Never raises**, exactly like every other reader on this path: an index
    that cannot be read is another check's finding, and a traceback out of a
    health command is the worst possible answer to *"what is wrong"*.
    """
    global _RECORDS
    if _RECORDS is None:
        try:
            from .store import reader

            _RECORDS = reader.read_index(root)
        except Exception:
            _RECORDS = {}
    return _RECORDS


#: The invocation's `Progress`, held for the run like `_RECORDS` rather than
#: threaded through every check (W-238). Only the identifier-family check reads
#: it: it re-reads every document, and it is nearly all of doctor's time.
_PROGRESS = None


def _section_mode(root: Path) -> Check:
    """Which mode built the index, and does ranking agree? (W-274, SR-SECTIONS d11.)

    Three facts, one row: `fux.toml [index] section_records`, whether the
    committed index holds a section plane, and `tune.toml [ranking]
    section_weight`. **An error** when the weight is on and the key is off,
    because `ask` refuses then too. **A warning** when the key and the plane
    disagree, because the next delta ingest refuses and names `--full`.
    Read-only: it names the command and runs nothing.
    """
    import tomllib

    from .config import section_records
    from .store import iter_section_paths
    from .tune import TUNE_NAME

    try:
        wanted = section_records(root)
    except Exception as exc:  # `fux.toml loads` names the fault; one report per cause
        return Check("section records", False, str(exc), level="warn")
    try:
        ranking = tomllib.loads((root / TUNE_NAME).read_text(encoding="utf-8")).get("ranking", {})
        weight = float(ranking.get("section_weight", 0.0))
    except Exception:
        weight = 0.0  # `tune.toml loads` is the row for a broken tune file
    has_plane = bool(iter_section_paths(root))
    if weight > 0 and not wanted:
        return Check(
            "section records",
            False,
            "[ranking] section_weight > 0 but fux.toml [index] section_records = false - "
            "`fux ask` refuses. Set section_records = true and run `fux ingest --full`, "
            "or set section_weight = 0.0",
        )
    if has_plane and not wanted:
        return Check(
            "section records",
            False,
            "off in fux.toml, but the committed index holds section records - "
            "run `fux ingest --full`",
            level="warn",
        )
    if wanted and not has_plane:
        return Check(
            "section records",
            True,
            "on - no document has two or more sections yet (if the key was just "
            "switched on, run `fux ingest --full`)",
            level="warn",
        )
    mode = "on - documents and their sections" if wanted else "off - whole documents only"
    return Check("section records", True, mode, level="warn")


def _python_version() -> Check:
    ok = sys.version_info[: len(PY_MIN)] >= PY_MIN
    have = f"{sys.version_info.major}.{sys.version_info.minor}"
    return Check(
        "python version",
        ok,
        f"{have} (need >= {'.'.join(map(str, PY_MIN))})" if not ok else f"{have}, fux {__version__}",
    )


def _config_loads(root: Path) -> Check:
    """Does `fux.toml` actually load? An **error**, and the loader's own message.

    🔴 **Without this row, `fux doctor` reported `[OK]` for a repo where every
    other verb exits 1.** A `fux.toml` the loader refuses — an unknown key, a
    missing `max_parallel`, malformed TOML — takes `ingest`, `ask` and the rest
    out, while `doctor` printed `fetcher optional functions: skipped (no
    readable fux.toml)` at **warn** level and called the run green. The one verb
    whose job is to name the fix was the one verb that did not name it.

    - **The loader's message is reproduced verbatim, not paraphrased.** It
      already names the key and what is wrong with it; a second wording of the
      same failure is a restatement that can drift from the thing enforcing it.
    - **`error`, not `warn`.** Every downstream check that touches config
      degrades to a skipped warning by design — each is individually correct to
      do so, and collectively they made the whole command green. This row is
      what makes the *cause* fail, so the skips can stay warnings.
    - **A missing `fux.toml` is NOT this check's failure.** `find_root` accepts
      a `.git`-only directory, and a repo with no `fux.toml` has nothing to
      refuse — that is `repo root`'s finding, and `fux setup`'s job.
    """
    from .config import load as load_config

    name = "fux.toml loads"
    if not (root / fixed("files", "config")).is_file():
        # `find_root` accepts a bare `.git` checkout. Nothing to load, nothing
        # to refuse — reporting a failure here would fire on every repo that
        # simply has not run `fux setup` yet.
        return Check(name, True, "no fux.toml (run `fux setup` to write one)", level="warn")
    try:
        load_config(root)
    except FuxError as exc:
        # Verbatim, and the only place doctor renders a loader error. It may
        # carry an em-dash, which is why nothing here interpolates it into an
        # ASCII-by-invariant string.
        return Check(name, False, str(exc))
    return Check(name, True, fixed("files", "config"))


def _pii_health(root: Path) -> Check:
    """`.fux/config/pii.toml` — do the rules load, and do the patterns compile?

    ⚠ **Offline and read-only, like every check here: it compiles the patterns
    and never runs them over a corpus.** Compiling catches the fault that
    matters (a rule that would stop an ingest dead), and it costs microseconds.
    Running them would mean reading the whole corpus inside the command a
    person runs *because something is already wrong*.

    **What this check CANNOT tell you** is the failure that actually bites: a
    rule that is well-formed and too broad. That removes real vocabulary from
    the index silently -- nothing errors, documents just stop being findable by
    the words that would have found them. `tools/pii-probe/` is where that is
    visible, and no offline check substitutes for reading what a rule caught.
    """
    from .acquire import pii

    # SR-PII decision 17: a missing file is an ERROR row -- `load` raises and
    # says what to run. `doctor` is exempt from the CLI gate so that it gets
    # here and names the fix, not so that the fault reads as healthy.
    try:
        rules = pii.load(root)
    except FuxError as exc:
        return Check("pii rules", False, str(exc))
    if not rules:
        return Check(
            "pii rules", True, ".fux/config/pii.toml declares no rules", level="warn"
        )
    names = ", ".join(rule.name for rule in rules)
    detail = (
        f"{len(rules)} rule(s) compile: {names}. Redaction applies to "
        f".fux/index/ only - acquired bytes and answer quotes are unredacted"
    )
    return Check("pii rules", True, f"{detail}. {_redaction_note(root, rules)}")


def _pii_timing(root: Path) -> Check:
    """`pii timing` -- each rule over fixed adversarial strings, worst time per rule.

    **This is where the wall-clock lives** (SR-PII decision 23). The load-time
    linter refuses the exponential shapes by reading the pattern; it cannot see
    the polynomial class (the shipped email rule is quadratic on a long run with
    no `@`). Timing it here is legal because a doctor row is never a committed
    byte, and nothing on the ingest path reads a clock.

    ⚠ **Advisory, and machine-dependent by nature.** A slow machine warns on a
    rule a fast one does not. It never fails the run and never repairs a rule.
    """
    from time import perf_counter

    from .constants import fixed
    from .acquire import pii

    name = "pii timing"
    try:
        rules = pii.load(root)
    except FuxError:
        return Check(name, True, "skipped (the pii rules row owns that)", level="warn")
    if not rules:
        return Check(name, True, "no rules to time")
    try:
        budget = config_mod.load(root).doctor.pii_rule_budget_ms
    except FuxError:
        return Check(name, True, "skipped (fux.toml does not load - see that row)", level="warn")
    length = fixed("pii", "stress_len")
    strings = [(unit * length)[:length] for unit in fixed("pii", "stress_units")]
    ms = fixed("pii", "ms_per_s")
    worst: list[tuple[float, str]] = []
    for rule in rules:
        slowest = 0.0
        for text in strings:
            start = perf_counter()
            rule.apply(text)
            slowest = max(slowest, (perf_counter() - start) * ms)
        worst.append((slowest, rule.name))
    slow = [f"{n} {t:.0f} ms" for t, n in sorted(worst, reverse=True) if t > budget]
    per_rule = ", ".join(f"{n} {t:.1f}" for t, n in worst)
    detail = f"worst of {len(strings)} stress strings of {length} chars, ms per rule: {per_rule}"
    if slow:
        return Check(
            name,
            True,
            f"over the {budget:g} ms budget ([doctor] pii_rule_budget_ms): "
            f"{', '.join(slow)}. {detail}. A rule this slow on a long line can stall "
            "an ingest; anchor it or bound its repeats",
            level="warn",
        )
    return Check(name, True, f"{detail}; all within {budget:g} ms")


def _redaction_note(root: Path, rules) -> str:
    """What the last ingest actually redacted — W-101 item 4.

    `redact()` has always returned per-rule hit counts and `run()` has always
    summed them; **nothing read the sum**, so a consumer could not tell a rule
    that is protecting them from a rule that has never matched anything. The
    counts are now recorded by every ingest (`pii.record_counts`) and this is
    where they surface.

    ⚠ **Absent and zero are different answers and stay apart.** No recorded
    counts means no ingest has run since the counter existed; zero means the
    rules ran and matched nothing. Collapsing them would let a repo whose rules
    have never executed read as a repo whose rules found nothing, which is the
    more dangerous of the two.

    ⚠ **The enrichment half is partial on an incremental ingest** and says so:
    enrichment is redacted inside the extract loop, which a reused document
    skips. The body half is a complete census on every run.

    ⚠ **A large count is a hint, not a finding.** An over-broad rule and a
    correct rule on a corpus that really does contain that much PII produce the
    same number. `tools/pii-probe/` is the instrument; this is the pointer to
    it.
    """
    from .acquire import pii

    counts = pii.read_counts(root)
    if counts is None:
        return "No ingest has recorded redaction counts yet - run `fux ingest`"
    if counts.total == 0:
        return (
            f"The last ingest redacted NOTHING across {counts.documents} document(s): "
            f"every rule compiled and none matched. That is a rule that is not doing "
            f"what it was written for as often as it is a clean corpus"
        )
    body = ", ".join(f"{name} x{n}" for name, n in sorted(counts.body.items()))
    note = (
        f"The last ingest redacted {counts.total} value(s) across "
        f"{counts.documents} document(s)"
    )
    if body:
        note += f" - body: {body}"
    if counts.enrichment:
        enrichment = ", ".join(f"{name} x{n}" for name, n in sorted(counts.enrichment.items()))
        note += f"; enrichment: {enrichment}"
        if counts.partial:
            note += (
                " (enrichment counts cover the documents that run re-extracted, not the "
                "whole corpus - `fux ingest --full` counts all of them)"
            )
    # ⚠ **`tools/pii-probe/` is in the fux REPOSITORY, not in the wheel**
    # (W-140 row 18): `packages = ["src/fux"]`. Pointing a consumer at a path
    # they do not have is worse than pointing at nothing, so this names the
    # skill `fux setup` wrote into their repo, which carries a copy.
    note += ". A big number is a hint, not a finding: probe it (the `fux-pii` skill carries the script)"
    return note


def _fetcher_names(root: Path) -> list[str]:
    """Every `fetch=` name this repo can run, or `[]` when the declaration does
    not read -- the `plugins` row reports that, once (SR-PLUGINS)."""
    from . import plugins

    try:
        return plugins.fetcher_names(root)
    except FuxError:
        try:
            return sorted(p.stem for p in (root / FETCHERS_DIR).glob("*.py"))
        except OSError:  # pragma: no cover - an unreadable directory
            return []


def _package_source(module: str) -> "Path | None":
    """The file a package's import name resolves to -- `find_spec`, which does
    not execute it (L5: doctor never imports a fetcher)."""
    import importlib.util

    try:
        spec = importlib.util.find_spec(module)
    except (ImportError, ValueError):
        return None
    return Path(spec.origin) if spec is not None and spec.origin else None


def _fetcher_config_tables(root: Path) -> Check:
    """`[sources.url.config.<name>]` sub-tables that name no fetcher file.

    **The whole point of the two-level table is that a key reaches exactly one
    fetcher** — so a sub-table whose name matches no `.py` in the fetchers
    directory reaches *none*, silently. That is the defect
    [SR-CONFIG](../../records/0113_config.md) decision 14 exists for, one level
    down: a setting its author believes is in force.

    ⚠ **A row here rather than a refusal in `config.load`**, and the reason is
    which module may touch the disk. The loader parses a file; deciding whether
    `[sources.url.config.wiki]` is a typo means listing
    `.fux/fetchers/` — a filesystem question, in a function whose job is TOML.
    `doctor` is the module that already asks filesystem questions about config.
    """
    from .config import load as load_config

    name = "fetcher config tables"
    try:
        config = load_config(root)
    except FuxError:
        return Check(name, True, "no readable fux.toml - another check owns that")
    if config.url is None or not config.url.config:
        return Check(name, True, "no [sources.url.config] to check")

    named = sorted(k for k, v in config.url.config.items() if isinstance(v, dict))
    if not named:
        return Check(name, True, "only shared keys - every fetcher gets them")

    fetchers_dir = root / FETCHERS_DIR
    # SR-PLUGINS P8: a fetcher is a file in `.fux/fetchers/` OR a declared package.
    stems = set(_fetcher_names(root))
    orphans = [n for n in named if n not in stems]
    if not orphans:
        return Check(name, True, f"{len(named)} per-fetcher table(s), each naming a fetcher this repo has")
    return Check(
        name,
        False,
        f"[sources.url.config.{orphans[0]}]"
        + (f" and {len(orphans) - 1} more" if len(orphans) > 1 else "")
        + f" name(s) no fetcher: {fetchers_dir}/ and the declared packages have "
        f"{sorted(stems) or 'nothing'}. "
        "These keys reach NO fetcher and nothing else says so - rename the table "
        "to the fetcher's filename without .py, or delete it",
    )


def _fetcher_routes(root: Path) -> Check:
    """The host-to-fetcher map — SR-FETCHER decision 16's three faults.

    🔴 **Offline, and it never imports a fetcher.** `ROUTES` is read with `ast`
    (`ingest/routes.claims`), for the reason `_fetcher_capabilities` reads a
    fetcher as text: importing consumer Python on `doctor`'s path is L5 lost
    where nothing would notice — a fetcher is free to open a session at import.

    Three faults, and the levels differ because the costs do:

    - **failure** — a route naming no file on disk. Every URL it matches is
      unfetchable and `fux add` will refuse.
    - **failure** — a claim collision: two `ROUTES` patterns matching one host.
      There is no non-arbitrary order between two regexes, and guessing one
      builds a **plausible index retrieved by the wrong fetcher**, which nothing
      downstream detects.
    - **finding** — a route matching no listed URL. Usually a typo, occasionally
      a table written before the URLs are added, so it is never an error alone.
    """
    from .config import load as load_config
    from .acquire import routes as routes_mod
    from .acquire import sourcelist

    name = "fetcher routes"
    try:
        config = load_config(root)
    except FuxError:
        # ⚠ **The exception is NOT quoted into the detail.** A `FuxError`'s
        # message is prose written for a person and may hold an em dash, and a
        # detail must be ASCII for a Windows console
        # (`test_every_check_detail_is_ascii_in_every_branch`). The `fux.toml
        # loads` row already prints the real message, so quoting it here would
        # be a second copy that can crash the command exactly when the repo is
        # already broken.
        return Check(name, True, "skipped (fux.toml does not load - see that row)", level="warn")
    if config.url is None:
        return Check(name, True, "skipped (no [sources.url] - this repo does not fetch)", level="warn")

    table = dict(getattr(config.url, "routes", {}) or {})
    fetchers_dir = root / FETCHERS_DIR
    try:
        claimed = routes_mod.claims(fetchers_dir)
    except FuxError as exc:
        return Check(name, False, str(exc))
    if not table and not claimed:
        return Check(name, True, "no routes and no ROUTES claim - every line is a pin", level="warn")

    stems = set(_fetcher_names(root))

    dangling = sorted(
        f"{pattern} -> {stem}"
        for pattern, stem in list(table.items()) + [(p, s) for p, (s, _) in claimed.items()]
        if stem not in stems
    )
    if dangling:
        return Check(
            name, False,
            f"{len(dangling)} route(s) name a fetcher that is neither in {FETCHERS_DIR}/ "
            f"nor a declared package: "
            f"{', '.join(dangling)}. Every URL they match is unfetchable",
        )

    try:
        entries = sourcelist.parse(
            (root / config.url.urls_file).read_text(encoding="utf-8"),
            sourcelist.URLS, origin=config.url.urls_file,
        )
    except (OSError, FuxError):
        entries = []

    hosts = {routes_mod.normalise_host(e.value) for e in entries if not e.exclude}
    merged = {**{p: s for p, (s, _) in claimed.items()}, **table}
    try:
        compiled = routes_mod.validate(merged, where=f"{root}: routes")
    except FuxError as exc:
        return Check(name, False, str(exc))
    for host in sorted(hosts):
        try:
            routes_mod.resolve(host, compiled, where=f"{root}: routes")
        except FuxError as exc:
            return Check(name, False, str(exc))

    unused = sorted(
        pattern for pattern, (_, compiled_re) in compiled.items()
        if not any(routes_mod._matches(pattern, compiled_re, h) for h in hosts)
    )
    total = len(compiled)
    if not unused:
        return Check(name, True, f"{total} route(s), each matching a listed URL")
    return Check(
        name, False,
        f"{total} route(s); {len(unused)} match no listed URL: {', '.join(unused)}. "
        f"Usually a typo, occasionally a table written before the URLs",
        level="warn",
    )


def _pinned_fetchers(root: Path) -> Check:
    """Lines whose `fetch=` pin disagrees with what the routes table now says.

    🔴 **The whole cost of SR-URL-LIST decision 16, made visible.** Arpit ruled
    that every line states a resolved stem, so a route changed later moves
    nothing — this row is the only thing that tells a consumer their table and
    their list have drifted apart, and it names the one-line fix per line.

    ⚠ **It reports and never rewrites.** fux editing the meaning of a committed
    file is what this repository refused when it declined an
    `ingest --unpin-default`.
    """
    from .config import load as load_config
    from .acquire import routes as routes_mod
    from .acquire import sourcelist

    name = "pinned fetchers"
    try:
        config = load_config(root)
    except FuxError:
        return Check(name, True, "skipped (fux.toml does not load)", level="warn")
    if config.url is None:
        return Check(name, True, "skipped (no [sources.url])", level="warn")
    table = dict(getattr(config.url, "routes", {}) or {})
    if not table:
        return Check(name, True, "no routes table - nothing for a pin to disagree with", level="warn")
    try:
        entries = sourcelist.parse(
            (root / config.url.urls_file).read_text(encoding="utf-8"),
            sourcelist.URLS, origin=config.url.urls_file,
        )
        compiled = routes_mod.validate(table, where="fux.toml: [sources.url.routes]")
    except (OSError, FuxError):
        return Check(name, True, "skipped (the list or the table does not read)", level="warn")

    drifted = []
    for entry in entries:
        if entry.exclude:
            continue
        pinned = entry.attrs.get("fetch")
        try:
            routed = routes_mod.resolve(
                routes_mod.normalise_host(entry.value), compiled,
                where="fux.toml: [sources.url.routes]",
            )
        except FuxError:
            continue
        if routed is not None and pinned != routed:
            drifted.append(f"{entry.value} pins {pinned}, routes say {routed}")
    if not drifted:
        return Check(name, True, f"{len(entries)} line(s), every pin agreeing with the routes table")
    return Check(
        name, False,
        f"{len(drifted)} line(s) pin a fetcher the routes table would now resolve differently: "
        f"{'; '.join(drifted[:5])}"
        f"{'' if len(drifted) <= 5 else f', and {len(drifted) - 5} more'}. "
        f"Every line is a pin by design - edit the line, or leave it",
        level="warn",
    )


def _url_decoders(root: Path) -> Check:
    """`decoder=` on a URL line that names no decoder module.

    **The pipe ruling's doctor row** (W-199 DoD 10), and the exact mirror of
    `_fetcher_bindings` one screen up: the grammar checks the SHAPE of a stem
    and cannot check that a module of that name exists, because reaching the
    registry from the parser would make reading a committed file depend on
    importing every decoder. So `decoder=xlxs` is a perfectly legal line naming
    a module nobody wrote, and without this row it is discovered by the next
    person's ingest skipping that document with `no decoder module named
    'xlxs'`.

    ⚠ **It reads the LIST, not the index**, for `_fetcher_bindings`' reason: a
    `decoder=` is wrong the moment the line is written, which is the moment it
    is cheap to fix.

    ⚠ **A CONSUMER module is checked by name on disk, never imported.** A
    decoder whose dependency is missing is SR-DECODE decision 7's loud ingest
    failure and deliberately not this row's business (the pipe ruling, §3 edge
    case 3): `doctor` is what somebody runs when the repo is already broken, and
    it reports that a stem is absent, not that a library is.
    """
    from .config import load as load_config
    from .decode import BUILTIN_MODULES, CONSUMER_DIR, PROSE_DECODER
    from .acquire import sourcelist

    name = "url decoders"
    try:
        config = load_config(root)
    except FuxError:
        return Check(name, True, "skipped (fux.toml does not load - see that row)", level="warn")
    if config.url is None:
        return Check(name, True, "no [sources.url] - no URL lines to resolve")

    path = root / config.url.urls_file
    if not path.is_file():
        return Check(name, True, f"no {config.url.urls_file} yet")
    try:
        entries = sourcelist.parse(
            path.read_text(encoding="utf-8"), sourcelist.URLS, origin=config.url.urls_file
        )
    except (FuxError, OSError):
        return Check(
            name, True,
            f"skipped ({config.url.urls_file} does not parse - the fetcher bindings row "
            "reports that)",
            level="warn",
        )
    lines = [e for e in entries if not e.exclude]
    if not lines:
        return Check(name, True, "no URL lines listed")

    try:
        on_disk = {p.stem for p in (root / CONSUMER_DIR).glob("*.py")}
    except OSError:
        on_disk = set()
    known = set(BUILTIN_MODULES) | on_disk | {PROSE_DECODER}

    missing = sorted({e.attrs["decoder"] for e in lines} - known)
    # W-289, SR-PLUGINS P3: a first-party module is known, but reads nothing
    # until its package is declared (or a consumer file of its name exists).
    from . import plugins

    try:
        undeclared = sorted(
            n for n in {e.attrs["decoder"] for e in lines} & set(BUILTIN_MODULES)
            if n not in on_disk and plugins.for_decoder_module(root, n) is None
        )
    except FuxError:
        undeclared = []
    if undeclared and not missing:
        packages = sorted({plugins.package_for_module(n).name for n in undeclared})
        return Check(
            name, False,
            f"`decoder=` {', '.join(undeclared)} name(s) a module no declared package "
            f"carries - declare {', '.join(packages)} in {fixed('plugins', 'file')} "
            "(`fux setup` adds it); until then every URL on those lines is skipped at ingest",
        )
    if not missing:
        return Check(
            name, True,
            f"{len(lines)} URL line(s), every `decoder=` naming a module that exists",
        )
    shown = ", ".join(missing[:3])
    more = f" (+{len(missing) - 3} more)" if len(missing) > 3 else ""
    return Check(
        name, False,
        f"{len(missing)} `decoder=` name(s) resolve to nothing: {shown}{more}. "
        f"Built-ins are {', '.join(sorted(BUILTIN_MODULES))}, plus {PROSE_DECODER} for bytes "
        f"that are already text; {CONSUMER_DIR}/ has {sorted(on_disk) or 'nothing'}. "
        "Every URL on one of these lines is skipped at ingest - fix the `decoder=`",
    )


def _observed_types(root: Path) -> Check:
    """A line's declared `decoder=` against the type its last response carried.

    🔴 **W-200's second provenance finding, which waited on the `decoder=` half
    of the pipe ruling to have a field to read.** The manifest in
    `.fux/acquired/` records the `Content-Type` of the bytes fux actually
    retained; the line records how fux reads them. The pipe ruling says **the
    line wins and the header loses, silently** (§3 edge case 5) — so a
    disagreement is never an error, and this row is the only place anybody finds
    out it exists.

    ⚠ **Both directions of it are one finding, deliberately.** A page that moved
    from HTML to a PDF export and a line typed wrong on the day it was added
    look identical from here, and only the person who wrote the line can tell
    them apart. It names the pair and stops.

    Offline: it reads the committed list and a JSON manifest, and imports no
    decoder.
    """
    from .config import load as load_config
    from .acquire import sourcelist, urlsrc
    from .store import acquired

    name = "observed types"
    try:
        config = load_config(root)
    except FuxError:
        return Check(name, True, "skipped (fux.toml does not load - see that row)", level="warn")
    if config.url is None:
        return Check(name, True, "no [sources.url] - nothing is fetched")
    try:
        entries = sourcelist.parse(
            (root / config.url.urls_file).read_text(encoding="utf-8"),
            sourcelist.URLS, origin=config.url.urls_file,
        )
    except (FuxError, OSError):
        return Check(name, True, "skipped (the URL list does not read)", level="warn")
    blobs = acquired.read_manifest(root)
    if not blobs:
        return Check(
            name, True,
            "nothing retained yet - a line's declared type is compared against the bytes "
            "`keep=true` kept, and there are none",
            level="warn",
        )

    drifted = []
    checked = 0
    for entry in entries:
        if entry.exclude:
            continue
        blob = blobs.get(entry.value)
        if blob is None:
            continue
        checked += 1
        declared = entry.attrs["decoder"]
        observed = urlsrc.propose_decoder(blob.content_type, entry.value, root)
        if observed is not None and observed != declared:
            drifted.append(f"{entry.value} declares {declared}, last came back as {observed}")
    if not checked:
        return Check(
            name, True, "no listed URL has retained bytes to compare against", level="warn"
        )
    if not drifted:
        return Check(
            name, True, f"{checked} retained URL(s), each declaring the type it came back as"
        )
    return Check(
        name, False,
        f"{len(drifted)} URL(s) whose declared `decoder=` disagrees with the last observed "
        f"content type: {'; '.join(drifted[:5])}"
        f"{'' if len(drifted) <= 5 else f', and {len(drifted) - 5} more'}. "
        "The line wins by design and the header loses silently - so this is a finding, not "
        "an error. Re-add the URL to re-observe it, or leave it",
        level="warn",
    )


def _fetcher_bindings(root: Path) -> Check:
    """`fetch=<name>` on a URL line that names no fetcher file.

    **W-178, the mirror of `_decoder_bindings`.** Since `fetch=` became a typed
    attribute the grammar accepts any module-stem name, which is what lets a
    consumer drop `.fux/fetchers/glassbox.py` in and write `fetch=glassbox`. The
    price of an open set is that a **typo** now parses: `fetch=glasbox` is a
    perfectly legal line naming a file nobody wrote.

    🔴 **Without this row, that line is discovered by the next person's ingest
    dying.** `urlsrc._fetcher_path()` raises with a clear message — at fetch
    time, on somebody else's machine, mid-run. **Exactly the argument W-101
    item 2 made for `_decoder_bindings`**, and the reason the two are a pair.

    ⚠ **It reads the LIST, not the index**, which is the opposite choice from
    `_decoder_bindings` and is right for a different reason. A binding is
    interesting when it matches no *document*; a fetcher name is wrong when it
    matches no *file*, and that is true the moment the line is written — before
    any ingest, which is the moment a person can still fix it cheaply.

    ⚠ **Offline, like every doctor check.** It lists a directory and never
    imports a fetcher: importing one runs consumer code that may `connect()`,
    and [SR-DOCTOR](../../records/0152_doctor.md) is the command somebody runs
    when something is already wrong.
    """
    from .config import load as load_config
    from .acquire import sourcelist, urlsrc

    name = "fetcher bindings"
    try:
        config = load_config(root)
    except FuxError:
        return Check(name, True, "no readable fux.toml - another check owns that")
    if config.url is None:
        return Check(name, True, "no [sources.url] - no URL lines to resolve")

    path = root / config.url.urls_file
    if not path.is_file():
        return Check(name, True, f"no {config.url.urls_file} yet")
    try:
        entries = sourcelist.parse(
            path.read_text(encoding="utf-8"), sourcelist.URLS, origin=config.url.urls_file
        )
    except (FuxError, OSError) as exc:
        return Check(name, False, f"{config.url.urls_file}: {exc}")

    resolved = urlsrc.resolve_urls(entries, config.url)
    if not resolved:
        return Check(name, True, "no URL lines listed")

    fetchers_dir = root / FETCHERS_DIR
    # SR-PLUGINS P8: the consumer's file, else a declared package.
    stems = set(_fetcher_names(root))

    wanted = sorted({e.fetch for e in resolved})
    missing = [n for n in wanted if n not in stems]
    if not missing:
        return Check(
            name,
            True,
            f"{len(wanted)} fetcher name(s) in use, each resolving to a file in "
            f"{fetchers_dir.name}/ or a declared package",
        )
    shown = ", ".join(missing[:3])
    more = f" (+{len(missing) - 3} more)" if len(missing) > 3 else ""
    return Check(
        name,
        False,
        f"{len(missing)} URL line(s) name a fetcher with no file: {shown}{more}. "
        f"{fetchers_dir}/ and the declared packages have {sorted(stems) or 'nothing'}. Every "
        "fetch through one of these fails at ingest time - declare its package (`fux setup`), "
        "write the module, or fix the `fetch=` name",
    )


def _pinned_without_bytes(root: Path) -> Check:
    """`fetch_at_answer = false` with URLs that have no retained bytes.

    **The disclosure SR-URL-FRESHNESS decision 16 chose over a refusal**
    (Arpit, 2026-09-14). `[sources.url] fetch_at_answer = false` says *never
    open a socket at answer time*; a URL with nothing in `.fux/acquired/` then
    has nothing to verify against, and every citation from it comes back
    `unverified` — honest, and silently much weaker than the consumer thinks.

    ⚠ **Refusing at load would have been the wrong shape**, and the precedent
    is this plane's own: [SR-ACQUIRED](../../records/0145_acquired-plane.md)
    resolves the equally lossy `update=never keep=false` pair as *disclosed,
    never refused*, because the combination is coherent for a document that
    genuinely never changes and merely surprising to have chosen by accident.
    A repo mid-migration — `fetch_at_answer` set before a re-ingest with
    `keep=true` — would be locked out by a refusal for no benefit.

    **Silent when the flag is on**, which is the default: there is nothing to
    warn about while fux may still go and look.
    """
    from .config import load as load_config
    from .acquire import urlsrc
    from .store import acquired

    name = "pinned url bytes"
    try:
        config = load_config(root)
    except FuxError:
        return Check(name, True, "no readable fux.toml - another check owns that")
    if config.url is None or config.url.fetch_at_answer:
        return Check(name, True, "fetch_at_answer is on - answers may verify against the source")

    try:
        entries = urlsrc.resolve_urls(urlsrc.read_urls(root, config.url.urls_file), config.url)
    except (FuxError, OSError):
        return Check(name, True, "no readable url list - another check owns that")
    if not entries:
        return Check(name, True, "fetch_at_answer is off, and no url is listed")

    try:
        manifest = acquired.read_manifest(root)
    except (FuxError, OSError):
        manifest = {}
    missing = sorted(e.url for e in entries if e.url not in manifest)
    if not missing:
        return Check(
            name,
            True,
            f"fetch_at_answer is off; all {len(entries)} url(s) have retained bytes - "
            "citations verify as `as-ingested`",
        )
    # 🔴 **`ok=False`, or this row renders `[OK]`** — see `_suspended_pins`.
    # It shipped as `ok=True, level="warn"` on 2026-09-14 and printed `[OK]`
    # beside *every citation from these will be `unverified`*, which is the
    # disclosure decision 16 chose over a refusal saying nothing at all.
    return Check(
        name,
        False,
        f"fetch_at_answer is off and {len(missing)} of {len(entries)} url(s) have NO retained "
        f"bytes: {', '.join(missing[:3])}"
        + (f" (+{len(missing) - 3} more)" if len(missing) > 3 else "")
        + " - every citation from these will be `unverified`. Set keep = true and re-ingest",
        level="warn",
    )


def _observers(root: Path) -> Check:
    """W-170. What is in `.fux/observers/`, and whether each one fired.

    🔴 **A present-but-never-firing observer is the failure this row exists
    for**, and it is silent by construction: the dispatcher is fail-open, so an
    observer that raises on every run is skipped on every run and fux answers
    normally. Without this row a consumer's analytics can be dead for weeks
    while every query looks perfect — the same shape as a suspended pin, and
    the same remedy: say so, and let a person decide.

    ⚠ **`warn`, never `error`.** A broken observer answers no question wrongly.
    The repository is not broken; somebody's telemetry is, and conflating the
    two would make `fux doctor` exit non-zero in CI over a consumer's own file.

    ⚠ **The liveness file describes the LAST run, so a first-ever `doctor` in a
    repo that has never answered a query reports `not yet observed`** — which
    is true and is not a finding. Reporting it as one would make every fresh
    clone look broken.
    """
    name = "observers"
    try:
        from . import observe
    except Exception:  # pragma: no cover - a check must not take out the command
        return Check(name, True, "not available in this build")
    try:
        present = [p.name for p in observe.observers_in(root)]
    except Exception:
        return Check(name, True, "could not read .fux/observers/")
    if not present:
        return Check(name, True, "none installed - `fux observers init` to add one")
    state = observe.liveness(root)
    if not state:
        return Check(name, True, f"{len(present)} installed; not yet observed a run")
    fired = set(state.get("fired", ()))
    silent = sorted(n for n in present if n not in fired)
    if not silent:
        return Check(name, True, f"{len(present)} installed, all fired on the last run")
    return Check(
        name,
        False,
        f"{len(silent)} of {len(present)} observer(s) did NOT fire on the last run: "
        f"{', '.join(silent)} - they raised or exceeded [observe] max_ms, and a "
        "failing observer is skipped silently by design. Re-run with FUX_DEBUG=1 "
        "to see which",
        level="warn",
    )


def _suspended_pins(root: Path) -> Check:
    """W-162. A `fux correct --pin` whose document has moved under it.

    **A suspended pin is silent at query time, deliberately** — the query
    simply ranks normally — so without this row a person who pinned a question
    months ago has no way to learn that their pin stopped applying. That is the
    exact shape of failure `fux doctor` exists for: something that *was* true,
    is not, and says nothing.

    ⚠ **`warn`, never `error`.** A stale pin answers correctly — it answers
    with the ranking — so the repository is not broken. And the remedy needs a
    human to read the document and decide, which `doctor` must not do for them.
    """
    name = "correction pins"
    try:
        from .store.corrections import load_corrections, suspended_pins
    except Exception:  # pragma: no cover - a check must not take out the command
        return Check(name, True, "not available in this build")
    try:
        rows = load_corrections(root)
    except Exception:
        return Check(name, True, "no readable corrections file")
    pins = [c for c in rows if c.pin]
    if not rows:
        return Check(name, True, "no corrections filed")
    if not pins:
        return Check(name, True, f"{len(rows)} correction(s), no pins")
    try:
        stale = suspended_pins(root)
    except Exception:
        return Check(name, True, f"{len(pins)} pin(s); could not read the index to check them")
    if not stale:
        return Check(name, True, f"{len(pins)} pin(s), all applying")
    shown = "; ".join(f"{c.loc} ({why})" for c, why in stale[:3])
    more = f" (+{len(stale) - 3} more)" if len(stale) > 3 else ""
    # 🔴 **`ok=False` with `level="warn"` is what renders `[WARN]`.** `cmd_doctor`
    # reads `ok` for the mark and `level` for the exit code, so `ok=True,
    # level="warn"` prints `[OK]` — which is right for an informational row
    # (*idle, nothing pending*) and wrong for a finding. The first cut of this
    # row had it that way and disclosed a suspended pin as `[OK]`.
    return Check(
        name,
        False,
        f"{len(stale)} of {len(pins)} pin(s) SUSPENDED and silently not applying: {shown}{more}"
        " - read the document, then `fux correct --reaffirm \"<question>\" <doc>`,"
        " or `--no-pin` to keep the correction without the pin",
        level="warn",
    )


def _acquired_health(root: Path) -> Check:
    """`.fux/acquired/` — how much is retained, and whether it is gitignored.

    ⚠ **Two questions, and the second is the one that matters.** The size is
    housekeeping; whether the plane is ignored by git is a data-exposure
    question, because this directory holds SOURCE BYTES. `_layout` already
    refuses an undeclared child of `.fux/`, and `_ignore_health` checks the
    index is *not* ignored — neither of them asks whether a plane that must be
    ignored actually is. This does.

    **A `warn`, never an `error`, on size.** SR-ACQUIRED decision 8 bounds the
    store and evicts; a store near its cap is working as designed, not broken.
    An UNIGNORED plane is a different matter and fails.
    """
    from .store import acquired

    plane = acquired.plane(root)
    if not plane.is_dir():
        return Check(
            "acquired plane",
            True,
            "nothing retained (no .fux/acquired/) - `keep=false` on every line, or nothing fetched yet",
            level="warn",
        )

    blobs = acquired.blobs_on_disk(root)
    total = sum(size for _, size in blobs)
    manifest = acquired.read_manifest(root)
    orphans = len(blobs) - len({b.sha for b in manifest.values()} & {p.name.split(".", 1)[0] for p, _ in blobs})

    ignored = _is_git_ignored(root, plane)
    if ignored is False:
        # The one failing case: retained source bytes that git can see.
        return Check(
            "acquired plane",
            False,
            f"{len(blobs)} blob(s), {total:,} bytes - AND .fux/acquired/ IS NOT GITIGNORED. "
            "It holds the bytes fetched from your sources; add `acquired/` to .fux/.gitignore "
            "(fux writes that line, so this means it was edited away)",
        )

    detail = f"{len(blobs)} blob(s), {total:,} bytes, {len(manifest)} in the manifest"
    if ignored is None:
        detail += " (gitignore unchecked: not a git checkout)"
    if orphans > 0:
        detail += f" - {orphans} unreferenced, swept on the next `fux ingest`"
    # The cap is `[sources.url] acquired_max_bytes` (SR-ACQUIRED decision 8).
    # No `[sources.url]`, or a fux.toml that does not load, means there is no
    # cap to compare against here — the store has no default of its own.
    from .config import load as load_config

    try:
        url = load_config(root).url
    except FuxError:
        url = None
    cap = url.acquired_max_bytes if url is not None else None
    share = config_mod.load(root).doctor.acquired_warn_share if cap is not None else None
    if cap is not None and total > cap * share:
        return Check(
            "acquired plane",
            True,
            f"{detail} - past 80% of the {cap:,}-byte cap; eviction will start "
            "dropping the oldest re-acquirable blobs",
            level="warn",
        )
    return Check("acquired plane", True, detail)


def _refusal_health(root: Path) -> Check:
    """`.fux/config/refusals.toml` — do the rules load, and has any of them ever fired?

    **W-101 item 3.** A refusal rule is the one piece of consumer policy whose
    correct behaviour and whose catastrophic behaviour look identical from
    outside: a rule that matches every response empties the `url:` half of the
    corpus, and an empty corpus looks exactly like a corpus nobody has ingested
    yet. Until now the only surface was a run's own output, which scrolls away.

    Two numbers, and the second is the one that matters:

    * **How many rules load**, which catches the file that was never valid —
      the same thing `_pii_health` catches for `pii.toml`.
    * **How many responses each has refused**, cumulative across networked runs
      from `urlstate.refused`. A rule at zero is a rule that has never done
      anything, which is what a typo'd `body_contains` looks like; a rule whose
      count is the size of the corpus is the over-broad rule.

    ⚠ **Offline, and the count is therefore about the PAST.** Doctor never
    fetches, so it reports what networked runs recorded. A repo that has never
    run `fux ingest` has nothing here and is told that rather than shown a zero
    it would read as *"nothing was refused"*.

    ⚠ **A warning, never an error.** Refusing sign-in walls is the feature
    working. The one loud shape — refusals recorded and no `url:` document
    surviving — is still a `warn`, because a corpus of only unreachable
    intranet pages is a legitimate state of the world and failing `doctor` on
    it would train people to ignore a red one.
    """
    from .acquire import refusals

    if not refusals.rules_path(root).is_file():
        return Check(
            "refusal rules",
            True,
            "no .fux/config/refusals.toml - only the always-on magic-byte floor applies",
            level="warn",
        )
    try:
        rules = refusals.load(root)
    except FuxError as exc:
        return Check("refusal rules", False, str(exc))

    try:
        from .acquire import urlstate

        counted = dict(urlstate.read(root).refused)
    except Exception:
        counted = {}

    if not rules:
        return Check(
            "refusal rules", True, ".fux/config/refusals.toml declares no rules", level="warn"
        )

    total = sum(counted.values())
    parts = [f"{len(rules)} rule(s) load"]
    if not counted:
        parts.append(
            "no networked run has recorded a refusal yet - the count starts at the "
            "next `fux ingest`"
        )
        return Check("refusal rules", True, ", ".join(parts), level="warn")

    worst = sorted(counted.items(), key=lambda kv: (-kv[1], kv[0]))
    named = ", ".join(f"{name} x{count}" for name, count in worst[:5])
    parts.append(f"{total} response(s) refused across networked runs: {named}")
    silent = [rule.name for rule in rules if rule.name not in counted]
    if silent:
        # Named, not counted: a rule that has never fired is either unneeded or
        # a typo, and only the consumer can tell which — but they need the name
        # to look at the line.
        parts.append(
            f"never fired: {', '.join(sorted(silent))} (unneeded, or a condition that "
            "never matches)"
        )

    indexed_urls = sum(1 for doc_id in _records(root) if doc_id.startswith("url:"))
    if total and indexed_urls == 0:
        return Check(
            "refusal rules",
            False,
            ", ".join(parts)
            + " - AND NO url: DOCUMENT SURVIVED. A rule that matches everything empties "
            "the URL half of the corpus and leaves it looking like a corpus nobody has "
            "ingested; check the rule with the largest count against one real response",
            level="warn",
        )
    return Check("refusal rules", True, ", ".join(parts), level="warn")




def provenance_counts(root: Path) -> dict:
    """`{rows, stale_decoders}` for `doctor --json`, or `{}` when no ledger exists.

    ⚠ **`{}` means UNKNOWN, not clean**, and that distinction is the whole
    reason this is a block rather than two keys that default to zero. A repo
    that has not ingested since W-200 landed has no ledger, and a caller told
    `stale_decoders: 0` there would be told something nothing checked.

    **Never raises.** A caller reading `doctor --json` in CI must not have its
    pipeline broken by an advisory, derived file.
    """
    from .acquire import decoderdigest, ingestlog

    try:
        if not ingestlog.path_for(root).is_file():
            return {}
        return {
            "rows": len(ingestlog.read(root)),
            "stale_decoders": ingestlog.stale_decoder_count(
                root, decoderdigest.binding_digests(root)
            ),
        }
    except (OSError, FuxError):
        return {}


def _provenance(root: Path) -> Check:
    """Do the records in the index still match the decoders that made them? (W-200)

    Reads `.fux/runtime/provenance.jsonl` — one row per document the last
    ingest consumed, naming the decoder digest that produced it — and compares
    each row against the digest that decoder carries **now**.

    🔴 **This is the case a plain `fux ingest` does NOT fix, which is the whole
    reason for the row.** The reuse key catches a decoder whose digest *moved*
    since the last run ([W-166](../../archive/open/W-166-decoder-digest.md)) and
    re-extracts its documents. It cannot catch a record written **before the
    binding existed**, or one carried through a run where the digest map could
    not be read: those records agree with nothing and no delta run will look at
    them again. `fux ingest --full` is the fix, and the row says so.

    ⚠ **Absent is not a finding.** A repo that has not ingested since this
    landed has no ledger, and reporting that as a problem would put a warning
    in front of every consumer on upgrade for a file that is advisory, derived
    and one `fux ingest` from existing. **`warn`, never `error`**, for the same
    reason: nothing about the index is wrong, only possibly stale.

    Read-only and offline. It opens two runtime files and imports no decoder.
    """
    from .acquire import decoderdigest, ingestlog

    if not ingestlog.path_for(root).is_file():
        return Check(
            "provenance",
            True,
            "no ledger yet - `.fux/runtime/provenance.jsonl` is written by the next "
            "`fux ingest`. Advisory and derived; nothing reads it at query time",
            level="warn",
        )
    try:
        current = decoderdigest.binding_digests(root)
    except FuxError as exc:
        return Check("provenance", False, f"decoder bindings do not resolve: {exc}")

    stale = ingestlog.stale_decoder_count(root, current)
    if stale:
        return Check(
            "provenance",
            False,
            f"{stale} record(s) were produced by a decoder whose digest differs from "
            "the tree's - run `fux ingest --full` to re-extract them. A plain "
            "`fux ingest` will NOT: the reuse key only catches a decoder that moved "
            "since the last run",
            level="warn",
        )
    rows = len(ingestlog.read(root))
    return Check(
        "provenance",
        True,
        f"{rows} record(s) match the decoders that produced them",
    )


def _decoder_bindings(root: Path) -> Check:
    """`[decoders]` in `.fux/config/formats.toml` — does every binding still resolve?

    **W-101 item 2.** `registry()` refuses a binding that names a module which
    does not exist, and one that takes an extension away from the decoder that
    claims it — but it refuses them **on the next `fux ingest`**. A consumer
    who deletes `.fux/decoders/confluence.py` and commits learns about the
    line still naming it when the next person's ingest dies.

    ⚠ **The third fault is one only `doctor` can catch**, and it is why this is
    not simply "call `registry()` early". A binding on an extension **no
    document in the corpus has** — a typo'd `jsno = "json"` — resolves perfectly:
    extending is legal by design (SR-DECODE, `_bind`), so nothing errors, and
    the line indexes nothing forever. That is deliberately not an ingest
    failure, and a report is the right weight for it.

    ⚠ **Counted against the INDEX, not against a directory walk.** The
    committed index is what fux actually holds; walking the tree would report a
    binding as live because an excluded or ignored file happens to carry the
    extension, which is the opposite of the answer. The cost is stated: a
    binding added before the first ingest reads as matching nothing, which is
    true of the index and is what the line says.
    """
    from . import decode

    try:
        decode.registry(root)
    except FuxError as exc:
        return Check("decoder bindings", False, str(exc))

    bindings = decode.declared_bindings(root)
    if not bindings:
        return Check(
            "decoder bindings",
            True,
            f"none declared in {DEFAULT_TYPES_FILE} - every extension resolves through "
            "the decoder modules themselves",
        )

    records = _records(root)
    if not records:
        return Check(
            "decoder bindings",
            True,
            f"{len(bindings)} binding(s) resolve; no index to check them against yet",
            level="warn",
        )
    present = {
        ("." + str(record.get("loc", "")).rsplit(".", 1)[-1]).lower()
        for record in records.values()
        if "." in str(record.get("loc", ""))
    }
    # ⚠ **Only bindings a HUMAN wrote can be reported**, and this line is the
    # whole difference between a check and a wall. `fux setup` writes the
    # entire built-in table into the generated types file, so on a corpus of
    # markdown 27 of 36 bindings match nothing — every one of them correct and
    # none of them news. A check that fires on a fresh, healthy repo is a check
    # people learn to skip, which is the failure `_url_health` and
    # `_accelerator` both record. A binding that differs from the built-in
    # default for its extension is a line somebody typed, and that is the only
    # place a typo can be.
    default = decode.builtin_bindings()
    unused = sorted(
        ext
        for ext, name in bindings.items()
        if ext not in present and default.get(ext) != name
    )
    generated = len(bindings) - len(unused)
    detail = f"{len(bindings)} binding(s) resolve"
    if not unused:
        return Check("decoder bindings", True, detail)
    listed = ", ".join(f"{ext}={bindings[ext]}" for ext in unused[:5])
    more = f" (+{len(unused) - 5} more)" if len(unused) > 5 else ""
    return Check(
        "decoder bindings",
        False,
        f"{detail}; {len(unused)} that is not the built-in default for its extension "
        f"matches no indexed document: {listed}{more}. Extending a decoder to a new "
        f"extension is legal, so this is not an error - but a typo in the extension "
        f"looks exactly like this and indexes nothing. "
        f"({generated} generated binding(s) not checked: an unused one is what a fresh "
        f"`fux setup` writes)",
        level="warn",
    )


def _recency_prior(root: Path) -> Check:
    """Does any document carry an `mtime` — i.e. is the recency prior alive?

    **Filed 2026-09-05 while checking W-111's tie-break, and it is a silent
    total loss.** `mtime` is written by `ingest/priors.py` from
    `git_commit_times`, which walks git. A corpus **copied out of** its
    repository is a plain directory, so **every** document loses its `mtime`
    and the whole recency prior switches off with nothing anywhere reporting
    it. `fux-benchmark`'s 10 000-document corpus is exactly that, and every
    measurement over it that touched recency measured the prior turned off.

    ⚠ **The knob this used to be about is GONE, and the check is not.**
    `recency_half_life_days` was removed on 2026-09-13 (W-152), so a missing
    `mtime` no longer switches a configured prior off. What it still costs is
    real and now MORE visible, not less:

    - **`mtime` reaches the caller**, on every `ask` hit (W-153) — so a corpus
      with none hands every consumer a null date and no way to sort by age.
    - **`mtime` is the second key of the declared tie-break** in
      `query/rank.py`, which is now one of only two routes by which a document
      fact reaches ranking at all. With no `mtime` anywhere, that key is inert
      and ties fall through to `priority` and then `id`.

    A **warning**, never an error: a corpus with no git history is a legitimate
    corpus, and this is a fact about the input rather than a broken install.
    """
    records = _records(root)
    if not records:
        return Check("recency prior", True, "no readable index", level="warn")
    with_mtime = sum(1 for record in records.values() if record.get("mtime"))
    total = len(records)
    if with_mtime == total:
        return Check(
            "recency prior", True, f"every one of {total} document(s) carries an mtime"
        )
    if with_mtime == 0:
        return Check(
            "recency prior",
            False,
            "NO document carries an mtime, so no date reaches a caller and the "
            "tie-break's date key is inert for the whole corpus. mtime is derived "
            "from git commit times, so a corpus copied out of its repository - or "
            "one that was never in git - has none",
            level="warn",
        )
    return Check(
        "recency prior",
        True,
        f"{with_mtime} of {total} document(s) carry an mtime; the other "
        f"{total - with_mtime} are outside git history and reach a caller with no date",
        level="warn",
    )


def _output_config_health(root: Path) -> Check:
    """Will `.fux/config/output.toml` load — every verb that renders reads it.

    Since L12 (W-225) an absent file is an ERROR, not the warning it used to be:
    there is no engine default behind it any more, so every verb that resolves
    an output key stops, naming the file. `fux doctor --fix` writes it from the
    template. ⚠ **A key the file lacks is `output.toml current`'s to report**;
    this row answers only whether the file exists and parses.
    """
    from .errors import FuxError as _FuxError

    try:
        output_config.load(root, enabled=True)
    except _FuxError as exc:
        return Check("output.toml present", False, f"{exc}")
    return Check("output.toml present", True, f"{output_config.OUTPUT_NAME}: parsed, every key valid")


def _tune_config_health(root: Path) -> Check:
    """Will `.fux/config/tune.toml` load — the file whose breakage doctor could not see.

    ⚠ **A broken tune file left `doctor` green** until 2026-09-11 (W-140 row
    13), and that is the worst shape for this particular file: `fux ingest`
    reads only `[index]` through `index_limits`, so a bad ranking knob **does
    not stop an ingest by design** ([SR-TUNE](../../records/0135_tuning.md)
    decision 13) — while `ask`, `find` and `answer` refuse. So the repo indexes
    cleanly, doctor says every row is fine, and every query fails.

    **A hard error, not a warning**, unlike `output.toml` being absent. An
    absent tune file is a repo running engine defaults, which is legitimate and
    common; a tune file that does not load is a file somebody wrote and nothing
    reads, and every query in the repo is already failing.

    The check calls `tune.load` itself rather than re-parsing: a second parser
    would answer a question the real one does not ask.
    """
    from . import tune as tune_mod

    try:
        tune_mod.load(root, enabled=True)
    except FuxError as exc:
        return Check(
            "tune.toml loads",
            False,
            f"{exc} - `ask`, `find` and `answer` refuse while this stands; "
            "`fux doctor --fix` writes a missing key, `fux tune > .fux/config/tune.toml` "
            "rewrites the whole file, and `--no-tune` reads the template for one command",
        )
    return Check("tune.toml loads", True, f"{tune_mod.TUNE_NAME}: parsed, every key valid")


def _types_health(root: Path) -> Check:
    """Will the committed types list load — the shape that stops ingest.

    Three ways it cannot, each of which `read_types` refuses:

    1. **A leftover `.fux/sources/types`.** The list moved to `.fux/config/formats.toml`
       on 2026-09-11 (SR-TYPES decision 12), and a repo that ran `fux setup`
       before then still has the old file. SR-DOTFUX decision 6: when a change
       must reach existing repos the mechanism is *a loader refusal or a
       `doctor` check, never a rewrite* — this row is the check, and it names
       the command that converts.
    2. **A file that does not parse or breaks the closed key set.**
    3. **A file that admits nothing.** A present file replaces the built-in
       default entirely (SR-TYPES decision 2), so an empty one would silently
       empty the index — `fux setup` once wrote exactly that, and **`setup`
       then `ingest` failed on every fresh repo** until 2026-08-27.
    """
    from .acquire import typesfile

    try:
        listed = typesfile.read(root, DEFAULT_TYPES_FILE)
    except FuxError as exc:
        return Check("types list usable", False, str(exc))
    except OSError as exc:
        return Check("types list usable", False, f"{DEFAULT_TYPES_FILE}: {exc}")
    if listed.allow:
        return Check(
            "types list usable",
            True,
            f"{DEFAULT_TYPES_FILE}: {len(listed.include)} include glob(s), "
            f"{len(listed.decoders)} decoder binding(s)",
        )
    return Check(
        "types list usable",
        False,
        f"{DEFAULT_TYPES_FILE} admits nothing - `include` and `[decoders]` are both empty - so "
        "`fux ingest` refuses to run. Delete the file to take the built-in default, or re-run "
        "`fux setup` after deleting it to get the default written out",
    )


def _fetcher_capabilities(root: Path) -> Check:
    """Which optional fetcher functions the consumer's own file implements.

    **The gap this closes, measured 2026-08-28:** a repo created before
    [SR-FETCHER](../../records/0117_fetcher.md) decision 12 learned **0 of 7**
    `validate()` tokens until its `http.py` was replaced by hand. `fux setup` is
    write-if-missing and never rewrites a consumer's fetcher — the freeze
    SR-DOTFUX decision 6 names — so a new optional function reaches new repos
    only, silently, and the optimisation that never runs is indistinguishable
    from one that ran and found nothing.

    ⚠ **A NOTICE, never a rewrite.** SR-DOTFUX decision 6 names the mechanism
    for a change that must reach an existing repo: *a loader refusal or a
    `doctor` check, never a rewrite.* `_types_health` is the precedent. Rewriting
    a consumer's committed fetcher would be a worse problem than the one it
    solves, which is why the record left this stated-as-a-cost rather than
    proposing a loader that edits their file.

    A **warning**, never an error: every function checked here is optional by
    contract, a fetcher without them is correct and supported, and reporting a
    supported configuration as a failure trains people to ignore a red doctor —
    the same reasoning `_url_health` and `_accelerator` record.
    """
    from .config import load as load_config

    name = "fetcher optional functions"
    try:
        url_source = load_config(root).url
    except FuxError:
        # An unreadable/absent `fux.toml` is `_repo_root`'s business, not this
        # check's. The message is NOT interpolated: a FuxError carries an
        # em-dash, and every detail here is ASCII by invariant.
        return Check(name, True, "skipped (no readable fux.toml)", level="warn")
    if url_source is None:
        # No `[sources.url]` at all: this repo does not fetch, so which
        # optional functions its fetcher implements is not a fact about it.
        return Check(name, True, "skipped (no [sources.url] - this repo does not fetch)", level="warn")
    # ⚠ **`[sources.url] fetcher` is deleted** (W-199 D2), so there is no one
    # fetcher to read any more. This row reports the optional functions of the
    # fetchers actually on disk, and names the shipped plain-GET one when it is
    # there, because that is the file a consumer is most likely asking about.
    # SR-PLUGINS P8: the consumer's `http.py` if there is one, else the declared
    # package's source -- LOCATED, never imported.
    from . import plugins

    try:
        resolved = plugins.resolve(root, "fetcher", "http")
    except FuxError:  # an unreadable declaration is the `plugins` row's finding
        resolved = plugins.Resolution(None, "http")
    if resolved.how == "override":
        rel, path = f"{FETCHERS_DIR}/http.py", resolved.path
    elif resolved.how == "package":
        rel, path = resolved.declared.name, _package_source(resolved.declared.package.module)
    else:
        rel, path = f"{FETCHERS_DIR}/http.py", None
    if path is None or not path.is_file():
        return Check(
            name, True,
            f"{rel}: absent - declare fux-fetcher-http (`fux setup`) or write the file",
            level="warn",
        )

    # Read the source; never import it. Importing a consumer's fetcher runs
    # their module-level code, and `doctor` is offline by this module's
    # contract -- a fetcher is free to open a session at import time.
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return Check(name, False, f"{rel}: {exc}", level="warn")

    #: Optional by contract, each with the record that added it and what a
    #: consumer forfeits by not having it. `fetch` is NOT here -- it is
    #: mandatory and `load_fetcher` already refuses without it.
    optional = [
        ("validate", "SR-FETCHER decision 12", "re-fetches every URL body even when unchanged"),
        ("is_rate_limited", "SR-FETCHER decision 13", "cannot tell a 429 from a hard failure"),
    ]
    missing = [(fn, rec, cost) for fn, rec, cost in optional if f"def {fn}(" not in text]
    if not missing:
        return Check(name, True, f"{rel}: implements {', '.join(fn for fn, _, _ in optional)}", level="warn")
    return Check(
        name,
        True,  # optional by contract: absence is legal, so this never fails the command
        f"{rel} does not implement "
        + "; ".join(f"`{fn}()` ({rec}) - {cost}" for fn, rec, cost in missing)
        + ". Your fetcher is yours and fux will not rewrite it: copy the function from "
        "`fux setup`'s current template, or ignore this if it does not suit your network",
        level="warn",
    )


def _ignore_health(root: Path) -> Check:
    """`.fux/.fuxignore` parses, and states nothing the old lists also state.

    **Two failures, one check, and neither is fatal to `doctor`'s exit code by
    accident.** A `.fuxignore` that will not parse stops `fux ingest` outright,
    so it is an `error`; a pattern written in both `.fuxignore` and a
    `sources/` `!` line changes nothing today and is a `warn`.

    ⚠ **The duplicate is worth a line precisely because it is currently
    harmless.** `!` subtracts in `sources/` and re-includes in `.fuxignore`, so
    the two copies agree only for as long as nobody edits either one. The day
    someone puts a `!` in front of the `.fuxignore` copy they get the opposite
    of what the other file says, silently. This check is early for that.
    """
    from .acquire import fuxignore

    path = root / fuxignore.IGNORE_FILE
    if not path.is_file():
        return Check("fuxignore usable", True, f"{fuxignore.IGNORE_FILE} absent - nothing ignored")
    try:
        rules = fuxignore.read(root).rules
    except (FuxError, OSError) as exc:
        return Check("fuxignore usable", False, f"{fuxignore.IGNORE_FILE}: {exc}")
    dirs_file = _dirs_file(root)
    duplicates = (
        fuxignore.duplicate_warnings(root, dirs_file=dirs_file) if dirs_file is not None else []
    )
    if duplicates:
        return Check(
            "fuxignore usable",
            False,
            f"{len(duplicates)} pattern(s) stated in both {fuxignore.IGNORE_FILE} and "
            f"{dirs_file} - run `fux ingest --list-skipped` for the detail",
            level="warn",
        )
    active = sum(1 for r in rules if not r.negate)
    return Check(
        "fuxignore usable",
        True,
        f"{fuxignore.IGNORE_FILE}: {active} ignore rule(s), {len(rules) - active} re-include(s)",
    )


def _shadowed_rules(rules) -> list[tuple[object, object]]:
    """`(shadowed, by)` for every hand rule a LATER rule makes unreachable.

    **Last match wins** in `.fuxignore` ([`fuxignore.Ignores._last_match`]), so
    the rule that never decides anything is the EARLIER one, and what shadows
    it is a later rule that matches everything it matches. (The backlog wording
    said "shadowed by an earlier rule"; with this matcher that is the one
    direction in which it cannot happen.)

    **Conservative on purpose: only provable containment is flagged.** Rule B
    covers rule A when they carry the same `body` and the same anchoring - the
    same compiled pattern - and B is not narrower in kind: `B.dir_only` is
    false (it matches files and directories) or both are directory-only. The
    negation of either is irrelevant: whichever sign B has, B decides every
    path A could. Anything cleverer (`*.log` over `a.log`, `**` overlaps)
    needs regex containment and is left alone.
    """
    out: list[tuple[object, object]] = []
    for i, early in enumerate(rules):
        for late in rules[i + 1 :]:
            if (
                late.body == early.body
                and late.anchored == early.anchored
                and (not late.dir_only or early.dir_only)
            ):
                out.append((early, late))
                break
    return out


def _ignore_reachable(root: Path) -> Check:
    """A `.fuxignore` rule a later rule always overrides (SR-FUXIGNORE, W-246).

    The one observable symptom of a wrong reorder: moving a line below its
    twin leaves it dead, and nothing complains. **Not full coverage** - only an
    identical pattern (or a directory-only one overridden by the same pattern
    without the trailing `/`) is recognised; a broader glob below a narrower
    one is a shadow this does not see.
    """
    from .acquire import fuxignore

    name = "fuxignore reachable"
    if not (root / fuxignore.IGNORE_FILE).is_file():
        return Check(name, True, f"{fuxignore.IGNORE_FILE} absent - nothing to shadow")
    try:
        rules = fuxignore.read(root).rules
    except (FuxError, OSError):
        return Check(name, True, "not assessed - see `fuxignore usable`")
    shadowed = _shadowed_rules(rules)
    if not shadowed:
        return Check(name, True, f"{len(rules)} rule(s), none overridden by an identical later one")
    return Check(
        name,
        False,
        f"{len(shadowed)} rule(s) never decide anything because a later rule matches the same paths "
        "(last match wins): "
        + "; ".join(
            f"{fuxignore.IGNORE_FILE}:{a.lineno} `{a.raw}` is overridden by :{b.lineno} `{b.raw}`"
            for a, b in shadowed[:5]
        )
        + (f"; and {len(shadowed) - 5} more" if len(shadowed) > 5 else "")
        + ". Delete the dead line, or move it below the one that overrides it",
        level="warn",
    )


def _dirs_exclusions_migrated(root: Path) -> Check:
    """`!` lines still in `.fux/sources/dirs`, and the one-line move for each.

    **`fux remove` stopped writing them on 2026-09-14** (W-165 fix 1): the
    exclusion goes to `.fux/.fuxignore`, which SR-FUXIGNORE made the one place a
    path is kept out of the index. The `!` lines already written keep being read
    — SR-DIR-LIST decision 2a, and breaking them would be a silent re-inclusion,
    which is the worse direction — so this is a `warn` and never an error.

    ⚠ **Not the same finding as `_ignore_health`'s duplicate.** That one fires
    when a pattern is in *both* files and is about the two spellings drifting
    apart. This fires on *every* survivor, duplicated or not, because the
    migration is owed for the ones nothing duplicates too — and those are the
    ones no other check would ever mention.

    **ASCII only** - it is printed, and printed text reaches a Windows console.
    """
    from .acquire import fuxignore

    dirs_file = _dirs_file(root)
    if dirs_file is None:
        return Check("dirs exclusions migrated", True, "not checked - fux.toml does not load; see its row")
    try:
        notes = fuxignore.dirs_exclusion_notes(root, dirs_file=dirs_file)
    except (FuxError, OSError) as exc:
        return Check("dirs exclusions migrated", False, f"{dirs_file}: {exc}", level="warn")
    if not notes:
        return Check(
            "dirs exclusions migrated",
            True,
            f"no `!` lines in {dirs_file} - exclusions live in {fuxignore.IGNORE_FILE}",
        )
    return Check(
        "dirs exclusions migrated",
        False,
        f"{len(notes)} `!` line(s) left in {dirs_file}. " + " ".join(notes),
        level="warn",
    )


# -- W-163: the setup-drift rows -------------------------------------------
#
# 🔴 **One cause, eight rows.** `fux setup` writes once and NEVER rewrites
# ([SR-DOTFUX](../../records/0102_fux-directory.md) decision 6), so everything
# that ships in a template **freezes in every repo that ran setup before the
# template changed**, and nothing tells the repo. Five records each named
# `fux doctor` as the place that should say so and none was built; three more
# name checks doctor can run today over declarations it already reads.
#
# ⚠ **Report-only, every one of them.** Decision 1 of SR-DOCTOR: doctor names,
# it never rewrites. A row that grew a `--fix` would be taking decision 6's fork
# without anybody ruling it.
#
# ⚠ **`warn`, every one of them.** None of these stops a verb. A frozen tunable
# is a repo running an older default, a missing directory is a line somebody
# has yet to create — these are drift, not breakage, and an error here would
# make `doctor` red on working repos, which is how people learn to ignore it.


#: Skill directories a vendor stopped reading. `(path, why, what to do)`.
#:
#: SR-AGENT-POLICY decision 16 (2026-09-12): Codex and Copilot both read
#: `.agents/skills/`, so the two vendor-specific copies were retired. A repo set
#: up before that still has them, and **Copilot then sees two copies of every
#: skill** — the duplicate is the defect, not the folder.
_RETIRED_AGENT_DIRS = (
    (".codex/skills", "Codex reads `.agents/skills/` now"),
    (".github/skills", "Copilot reads `.agents/skills/` now, and sees DUPLICATES while this exists"),
)


def _retired_agent_folders(root: Path) -> Check:
    """Skill folders a vendor stopped reading, left behind by an older `setup`.

    **The duplicate is the defect.** `.github/skills/` is not merely unread —
    Copilot reads `.agents/skills/` *and* it, so every skill appears twice, with
    the older copy free to disagree with the newer one while both look correct.

    **Delete is the whole remedy**, which is why this is a row and not a rewrite:
    the folder may hold a consumer's own files, and `fux setup` removing a
    directory it did not write is not a thing it has ever been allowed to do.
    """
    present = [(rel, why) for rel, why in _RETIRED_AGENT_DIRS if (root / rel).is_dir()]
    if not present:
        return Check("retired agent folders", True, "none - skills live in `.agents/skills/`")
    return Check(
        "retired agent folders",
        False,
        "; ".join(
            f"`{rel}` still exists ({why}); delete it - `fux setup` will not, "
            "because it may hold files fux did not write"
            for rel, why in present
        ),
        level="warn",
    )


def _readme_current(root: Path) -> Check:
    """`.fux/README.md`'s section set against the template's.

    **Sections, not bytes.** The file is a consumer's to annotate — SR-DOTFUX
    decision 6 is write-if-missing precisely so their edits survive — so a byte
    comparison would fire on every repo where someone added a note, which is a
    row that is wrong more often than it is right. A **missing section** is the
    thing that means "this predates a change to what `.fux/` holds".

    ⚠ **Extra sections are NOT reported.** A consumer heading fux never wrote is
    the feature, not drift.
    """
    from .store import fuxdir

    path = root / fixed("fuxdir", "dir") / fixed("fuxdir", "readme")
    if not path.is_file():
        return Check("README.md current", True, "absent - nothing to be stale")
    builder = getattr(fuxdir, "_readme", None)
    if builder is None:  # pragma: no cover - the template is not optional today
        return Check("README.md current", True, "no template to compare against")
    try:
        template = builder()
    except Exception:  # pragma: no cover - a template that will not build is its own bug
        return Check("README.md current", True, "the template did not build")
    missing = sorted(_headings(template) - _headings(path.read_text(encoding="utf-8", errors="replace")))
    if not missing:
        return Check("README.md current", True, "every section the template carries is present")
    return Check(
        "README.md current",
        False,
        f"{len(missing)} section(s) the current template carries are absent: "
        + ", ".join(f"`{m}`" for m in missing[:4])
        + (f" and {len(missing) - 4} more" if len(missing) > 4 else "")
        + ". `fux setup` writes this file once and never rewrites it, so it froze when "
        "this repo was set up; copy the missing sections in, or delete the file and "
        "re-run `fux setup` to get the current one",
        level="warn",
    )


def _headings(text: str) -> set[str]:
    """Markdown ATX headings, normalised. Shared by the README row and its test."""
    return {
        line.lstrip("#").strip()
        for line in text.splitlines()
        if line.startswith("#") and line.lstrip("#").strip()
    }


#: sha256 of every refusal starter fux has SHIPPED AND REPLACED.
#:
#: 🔴 **Append the outgoing digest here in the same change that edits
#: `templates/refusals.toml.txt`.** That is the whole mechanism, and without it
#: this row cannot fire: fux ships exactly one starter, so *"byte-equal to a
#: PREVIOUS starter"* — the condition SR-REFUSAL names — is unanswerable from
#: the tree alone. A repo whose file matches the current starter is **new**, not
#: frozen, and reporting the two alike would make the row wrong on every fresh
#: `fux setup`.
#:
#: ⚠ **Empty today, and that is correct rather than unfinished.** The starter
#: has not been replaced since it shipped, so there is no superseded digest to
#: hold. `tests/test_doctor.py::test_the_current_refusal_starter_is_not_listed_as_retired`
#: fails if the current one is ever added here by mistake, which would report
#: every repo in the world as frozen.
RETIRED_REFUSAL_STARTERS: tuple[str, ...] = ()


def _starter_refusals_untouched(root: Path) -> Check:
    """`.fux/config/refusals.toml` byte-equal to a starter fux has since replaced.

    **Byte equality is the right test here, and the opposite call from the
    README row above.** These are rules that decide what enters the index,
    shipped as a starting point for a consumer to adapt to their own sign-in
    pages. A file identical to a *retired* starter is one nobody ever looked at,
    still refusing by rules fux itself stopped shipping.

    ⚠ **Matching the CURRENT starter is not a finding.** A repo set up yesterday
    is supposed to look exactly like that. The row fires only on a digest in
    `RETIRED_REFUSAL_STARTERS`, which is the only shape that means *frozen* as
    opposed to *new* — and which is why that tuple has to be appended to by
    hand when the starter changes.
    """
    import hashlib

    path = root / fixed("files", "refusals")
    if not path.is_file():
        return Check("refusal rules current", True, "`.fux/config/refusals.toml` absent")
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        return Check("refusal rules current", True, f"`.fux/config/refusals.toml`: {exc}")
    if digest not in RETIRED_REFUSAL_STARTERS:
        return Check(
            "refusal rules current",
            True,
            "`.fux/config/refusals.toml` is not a starter fux has retired",
        )
    return Check(
        "refusal rules current",
        False,
        "`.fux/config/refusals.toml` is byte-identical to a starter fux has since REPLACED - "
        "it has never been edited, and the rules it carries are ones fux stopped "
        "shipping. Compare it against `fux setup`'s current starter and take what "
        "applies to your sign-in pages; `fux setup` will not rewrite it",
        level="warn",
    )


def _dirs_file(root: Path) -> "str | None":
    """`[sources] dirs_file` as `fux.toml` names it — `None` when the file does
    not load, which its own row reports. There is no default path to fall back
    to (SR-LAW-12), and checking one the repo does not use would be a row about
    the wrong file."""
    from .config import load as load_config

    try:
        return load_config(root).dirs_file
    except FuxError:
        return None


def _unbound_types(root: Path) -> Check:
    """A declared type that resolves to no decoder at all.

    ⚠ **Not the same finding as SR-DECODE's `decoder bindings` row**, which
    fires on a `[decoders]` binding whose extension no indexed document has.
    This one fires on a **declared include glob** that reaches a format nothing
    can read: the documents match, get walked, and are skipped or indexed as raw
    bytes — with the type list saying, in a committed file, that they are
    documents.

    **Markdown and plain text are exempt and always will be.** They are read by
    `extract.py`, not by a decoder, so *having no decoder* is their normal state
    rather than a fault.
    """
    from . import decode as decode_mod
    from .acquire import typesfile

    try:
        listed = typesfile.read(root, DEFAULT_TYPES_FILE)
    except (FuxError, OSError):
        return Check("declared types are readable", True, "types list not parsed here - see its own row")
    if not listed.allow:
        return Check("declared types are readable", True, "no declared types to check")

    try:
        known = set(decode_mod.registry(root)) | _PROSE_SUFFIXES
    except (FuxError, OSError):
        # A binding naming a module that does not exist, or a consumer decoder
        # that will not import. **`decoder bindings` is the row for that** — it
        # names the module and the fix. Reporting it here as well, in different
        # words, is how a reader learns to trust neither row.
        return Check(
            "declared types are readable",
            True,
            "the decoder registry did not build - see the `decoder bindings` row",
        )
    unbound = sorted(
        {
            suffix
            for glob in listed.include
            if (suffix := _glob_suffix(glob)) and suffix not in known
        }
    )
    if not unbound:
        return Check(
            "declared types are readable",
            True,
            f"every declared type resolves to a decoder or is prose ({len(listed.include)} glob(s))",
        )
    return Check(
        "declared types are readable",
        False,
        f"{len(unbound)} declared type(s) resolve to no decoder and are not prose: "
        + ", ".join(f"`{s}`" for s in unbound[:6])
        + (f" and {len(unbound) - 6} more" if len(unbound) > 6 else "")
        + ". Matching documents are walked and then indexed as raw bytes or skipped, "
        "while `.fux/config/formats.toml` says they are documents. Write a decoder in "
        "`.fux/decoders/`, or drop the glob",
        level="warn",
    )


#: Read by `extract.py` rather than by a decoder, so having none is correct.
_PROSE_SUFFIXES = frozenset({".md", ".markdown", ".txt", ".rst", ".adoc", ".org"})


def _glob_suffix(glob: str) -> str:
    """`*.pdf` -> `.pdf`. `""` for a glob that names no single extension.

    A glob like `docs/**` or `*` claims no extension, so there is nothing to
    resolve and nothing to report — reporting one would be inventing a claim the
    consumer did not make.
    """
    name = glob.rsplit("/", 1)[-1]
    if not name.startswith("*.") or "*" in name.removeprefix("*.") or "?" in name or "[" in name:
        return ""
    return name[1:].lower()


def _listed_dirs_exist(root: Path) -> Check:
    """A line in `.fux/sources/dirs` naming a path that is not on disk.

    🔴 **This is not cosmetic: `walk_sources` RAISES on it**, so the next
    `fux ingest` in this repo exits 1 — which is why `fux add` refuses a path
    that does not exist. A line that got there another way (a hand edit, a
    branch switch, a directory someone moved) has nothing checking it until the
    ingest fails.

    **Still a `warn`.** Doctor reports; the ingest is where it stops, and it
    already says so clearly. Making this an error would mean `doctor` and
    `ingest` both refuse on a branch where a documented directory is simply not
    checked out, which is a legitimate state to be in for an afternoon.

    ⚠ **Exclusions are not checked.** A `!` line names a pattern, not a path,
    and a pattern matching nothing today is exactly what a pattern is for.
    """
    from .acquire import sourcelist

    dirs_file = _dirs_file(root)
    if dirs_file is None:
        return Check("listed directories exist", True, "not checked - fux.toml does not load; see its row")
    path = root / dirs_file
    if not path.is_file():
        return Check("listed directories exist", True, f"{dirs_file} absent")
    try:
        entries = sourcelist.parse(
            path.read_text(encoding="utf-8"), sourcelist.DIRS, origin=str(path)
        )
    except (FuxError, OSError) as exc:
        return Check("listed directories exist", False, f"{dirs_file}: {exc}", level="warn")

    gone = [e.value for e in entries if not e.exclude and not (root / e.value).exists()]
    if not gone:
        return Check(
            "listed directories exist",
            True,
            f"every listed path is on disk ({len(entries)} entr(y/ies))",
        )
    return Check(
        "listed directories exist",
        False,
        f"{len(gone)} listed path(s) are not on disk: "
        + ", ".join(f"`{g}`" for g in gone[:5])
        + (f" and {len(gone) - 5} more" if len(gone) > 5 else "")
        + f". `fux ingest` RAISES on this, so the next one will exit 1 - "
        f"`fux remove <path>` drops the line, or restore the directory",
        level="warn",
    )


#: A `url:` record whose extracted text is below this share of its retained
#: bytes is *suspiciously thin* — almost certainly a page whose real content
#: arrived by JavaScript the `http` fetcher does not run.
#:
#: ⚠ **Advisory, and a SHARE rather than a byte count.** A genuinely short page
#: is fine; a 400 KB HTML document that extracted 300 characters is a sign-in
#: wall or an app shell. The floor is deliberately generous: this row exists to
#: surface the obvious case, never to adjudicate extraction quality, and a
#: tighter number would need evidence nobody has gathered. The share is
#: `fux.toml [doctor] thin_url_share`; below `[doctor] thin_url_chars`
#: characters the share is meaningless and the absolute number is the signal
#: (W-225 stage 5e).


def _thin_urls(root: Path) -> Check:
    """`url:` documents that extracted almost nothing from a large fetch.

    **The shape it catches:** the `http` fetcher runs no JavaScript, so a
    single-page app returns a full-size HTML shell and decodes to a nav bar.
    The document indexes, the run reports success, and the page is in the corpus
    answering nothing — [SR-HTTP-FETCHER](../../records/0119_http-fetcher.md)
    named `doctor` as where that should be visible.

    **Read from the committed index and `.fux/acquired/`**, both already on
    disk. No fetch, no network, no second opinion about the page.

    ⚠ **Advisory and deliberately loose.** It reports; `cdp.py` is the remedy
    for a page that needs a browser, and whether a given page needs one is the
    consumer's call about their own wiki.
    """
    from .store import acquired

    try:
        manifest = acquired.read_manifest(root)
    except (FuxError, OSError):
        return Check("url extraction depth", True, "no acquired plane to compare against")
    if not manifest:
        return Check("url extraction depth", True, "no retained url bytes to compare against")

    try:
        bounds = config_mod.load(root).doctor
    except FuxError:
        return Check("url extraction depth", True, "skipped (fux.toml does not load)")
    thin: list[str] = []
    for doc_id, record in _records(root).items():
        if not doc_id.startswith("url:"):
            continue
        blob = manifest.get(record.get("loc", ""))
        if blob is None:
            continue
        raw = getattr(blob, "bytes", None) or getattr(blob, "size", 0)
        extracted = sum(record.get("flen", ())) if record.get("flen") else 0
        if not raw or extracted >= bounds.thin_url_chars:
            continue
        if extracted / raw < bounds.thin_url_share:
            thin.append(record.get("loc", doc_id))

    if not thin:
        return Check("url extraction depth", True, "no url document extracted suspiciously little")
    return Check(
        "url extraction depth",
        False,
        f"{len(thin)} url document(s) extracted almost nothing from a full-size fetch: "
        + ", ".join(sorted(thin)[:3])
        + (f" and {len(thin) - 3} more" if len(thin) > 3 else "")
        + ". The `http` fetcher runs no JavaScript, so an app shell decodes to its nav bar. "
        "`fux add <url> --cdp` fetches through a signed-in Chrome instead",
        level="warn",
    )


def _url_health(root: Path) -> Check:
    """The `url:` half of the corpus, reported (W-82 §3.1).

    Doctor had **no URL check at all**, which is the defect: a URL that has
    failed every fetch for a month looked exactly like one fetched a minute ago.
    [SR-URL-INGEST](../../records/0107_url-ingest.md) decision 4 keeps the
    prior record on a failed fetch — correct, because a flaky network must never
    present as a deletion — and the cost of that rule is that **a permanently
    dead URL lives in the index forever**. This makes the cost visible.

    **Report, never auto-delete**, and **never fetch**: doctor stays offline
    (this module's contract), so every number here comes from the committed
    index and a gitignored counter file. It says what the last networked run
    saw; it does not go looking.

    A **warning**, never an error. A stale or failing URL means the index is
    behind, which is a fact about the world rather than a broken install, and
    reporting it as a failure would train people to ignore a red doctor —
    the same reasoning `_accelerator` records.
    """
    from .acquire import urlstate

    try:
        from .store import reader

        indexed = [doc_id.removeprefix("url:") for doc_id in reader.read_index(root) if doc_id.startswith("url:")]
    except Exception:
        # An unreadable or absent index is another check's business, not this
        # one's. Reporting "cannot tell" beats a traceback on a health command.
        return Check("url sources", True, "skipped (no readable index)", level="warn")

    state = urlstate.read(root)
    try:
        url_source = config_mod.load(root).url
    except FuxError:
        url_source = None  # `fux.toml loads` is the row that reports this
    streak = url_source.failing_streak if url_source is not None else None
    summary = urlstate.summarize(state, indexed, failing_streak=streak)
    policy = _parallel_policy(root)

    def _rate_limit_note() -> str | None:
        """W-82 ruling 12, cumulative across runs.

        ⚠ **Reported in BOTH branches, deliberately.** A host refusing you is a
        fact about the host, not about how many URLs are indexed — and the
        no-URLs branch is exactly where a rate limit is most likely to be the
        REASON nothing is indexed.

        ⚠ **Reaching both branches took two fixes, and the second was worse.**
        The note was first built into the populated branch only, so it was
        invisible in the one case that produces it. Adding the empty branch
        then put the caller's `", ".join(parts)` ABOVE the append, which killed
        it in the populated branch instead — a working report in the rare case
        and a dead one in the common case, for a whole release. Neither was
        caught by a test, because until now there was none; both were found by
        reading the code, which is the weakest way to find either.

        **Never names a number to set `max_parallel` to.** That is the
        consumer's call; fux picking it would be the clamping ruling 12
        refused.
        """
        if not state.rate_limited:
            return None
        worst = sorted(state.rate_limited.items(), key=lambda kv: (-kv[1], kv[0]))
        return "rate-limited by " + ", ".join(f"{host} x{count}" for host, count in worst[:3])

    if not summary.has_urls:
        # ⚠ The concurrency belongs in THIS branch above all (W-83). An empty
        # corpus with `[sources.url]` configured is a repo about to run its
        # first `fux add <URL>` — the moment the number matters most and the
        # only moment nobody can look it up from a previous run.
        bits = ["none indexed"]
        # ⚠ This branch above all: "none indexed" with five URLs listed is a
        # repo whose whole corpus is waiting on a fetch nobody has run, and it
        # read as an empty, healthy configuration.
        bits.extend(_unfetched_note(root, indexed))
        if policy is not None:
            bits.append(policy)
        note = _rate_limit_note()
        if note is not None:
            bits.append(note)
        return Check("url sources", True, ", ".join(bits), level="warn")

    parts = [f"{summary.indexed} url: record(s)"]
    if summary.run_seq == 0:
        parts.append("no networked run recorded yet - run `fux ingest`")
    else:
        parts.append(f"{summary.confirmed_last_run} confirmed by the last run")
    if summary.never_confirmed:
        parts.append(f"{summary.never_confirmed} never re-fetched since first ingest")
    if summary.failing:
        parts.append(f"{summary.failing} failing")
    if policy is not None:
        parts.append(policy)
    parts.extend(_unfetched_note(root, indexed))
    parts.extend(_pinned_note(root))
    note = _rate_limit_note()
    if note is not None:
        parts.append(note)
    # ⚠ The join stays BELOW every append. It sat above the rate-limit
    # append once, and the note was built, appended to a list nothing read
    # again, and silently dropped -- correct in the empty branch, dead here.
    detail = ", ".join(parts)
    if summary.failing_urls:
        # Named, not just counted: a count tells you something is wrong and a
        # name tells you which line of `.fux/sources/urls` to go and look at.
        listed = ", ".join(summary.failing_urls[:5])
        more = f" (+{len(summary.failing_urls) - 5} more)" if len(summary.failing_urls) > 5 else ""
        detail += (
            f" - failed {streak}+ runs in a row: {listed}{more}. "
            "fux never deletes a URL record; remove the line from .fux/sources/urls yourself"
        )
    return Check("url sources", not summary.failing_urls, detail, level="warn")


def _unfetched_note(root: Path, indexed: list[str]) -> list[str]:
    """URLs listed in `.fux/sources/urls` that have never produced a record.

    🔴 **[SR-MAINTENANCE](../records/0129_hooks.md) decision 5a leaned on this
    and it did not exist** (W-140 row 13, built 2026-09-12). 5a refuses to let
    any git hook touch the network, and pays for that refusal with one sentence:
    *"URLs added by hand-editing `.fux/sources/urls` are not fetched at commit
    time… That is a delay, not a silence — `fux doctor` reports them."* **It did
    not report them.** Every other row of `url sources` is computed from `url:`
    records **in the index**, and a line that has never been fetched has no
    record — so the one case the law's cost depends on was the one case the
    check could not see. The silence 5a promised was not a silence was a
    silence.

    **Listed minus indexed**, read off the committed list. No network, like
    everything else here.
    """
    from .config import load as load_config
    from .acquire import urlsrc

    try:
        config = load_config(root)
        if config.url is None:
            return []
        listed = [e.value for e in urlsrc.read_urls(root, config.url.urls_file)]
    except Exception:
        # The list or the config is another row's finding — `fux.toml loads`
        # and `url sources` both name it. Never two reports for one cause.
        return []
    have = set(indexed)
    missing = sorted(url for url in listed if url not in have)
    if not missing:
        return []
    shown = ", ".join(missing[:3])
    more = f" (+{len(missing) - 3} more)" if len(missing) > 3 else ""
    return [
        f"{len(missing)} listed URL(s) have never been fetched, so they are not in "
        f"the index at all: {shown}{more} - run `fux ingest` (no hook will do it: "
        f"SR-MAINTENANCE decision 5a)"
    ]


def _pinned_note(root: Path) -> list[str]:
    """`update=never` lines, counted — and the lossy pair named (W-113).

    A pinned URL is a URL `fux ingest` will never go out for again, which is a
    fact somebody looking at a stale corpus needs and could otherwise learn only
    by reading every line of `.fux/sources/urls`.

    ⚠ **`update=never` + `keep=false` is legal and lossy, so it is DISCLOSED
    and never refused.** With no retained bytes there is nothing for `fux
    answer` to verify a citation against and nothing to re-derive from: the
    document is frozen at whatever statistics its last ingest produced. That is
    a coherent thing to want for a document that genuinely never changes, and a
    surprising thing to have chosen by accident — which is exactly the shape
    that belongs in a warning rather than in a refusal.

    Reads the committed list, never the network, and resolves through the same
    three layers everything else does so a source-wide `update = "never"` is
    counted too.
    """
    from .config import load as load_config
    from .acquire import urlsrc

    try:
        config = load_config(root)
        if config.url is None:
            return []
        resolved = urlsrc.resolve_urls(urlsrc.read_urls(root, config.url.urls_file), config.url)
    except Exception:
        # The list or the config is another row's finding -- `fux.toml loads`
        # and `url sources` both name it. Never two reports for one cause.
        return []
    pinned = [e for e in resolved if e.update == "never"]
    if not pinned:
        return []
    parts = [f"{len(pinned)} pinned (update=never; never re-fetched)"]
    lossy = sorted(e.url for e in pinned if not e.keep)
    if lossy:
        shown = ", ".join(lossy[:3])
        more = f" (+{len(lossy) - 3} more)" if len(lossy) > 3 else ""
        parts.append(
            f"{len(lossy)} of them keep=false, so there are no retained bytes to verify "
            f"a citation against: {shown}{more}"
        )
    return parts


def _parallel_policy(root: Path) -> str | None:
    """How many URLs a networked verb may open at once — W-83.

    **The number a person needs before running `fux ingest` over a corporate
    wiki**, said by the one command whose job is to tell them what will happen.
    Without it the only way to learn the concurrency was to read `config.py`.

    ⚠ **This reports POLICY and refuses to compute the product**, and that is a
    constraint rather than laziness. The effective value is
    `min(configured, declared)`, and `declared` lives in a **consumer-owned
    Python file** — reading it means importing it, which runs whatever is at
    that file's module level. `fux doctor` is the command a person runs when
    something is already wrong; it may not be the command that executes their
    fetcher. So it names the rule and lets `fux ingest` apply it.
    """
    from .config import load

    try:
        url = load(root).url
    except Exception:
        # No readable fux.toml is `_config`'s finding to report, not this
        # function's, and a health command must not raise twice for one cause.
        # ⚠ Since W-85 this also swallows the *missing `max_parallel`* refusal —
        # correctly: that error belongs to whichever command the person actually
        # ran, stated once, not repeated as a doctor line.
        return None
    if url is None:
        # No `[sources.url]` at all: there is no fetching to bound, and a
        # concurrency figure for a source that does not exist is noise on a
        # command whose whole value is that its output is worth reading.
        return None
    # No "unset" branch since W-85: `max_parallel` is required, so a loaded
    # `UrlSource` always carries a real number. A fallback here would be dead
    # code that reads like reassurance.
    named = _fetchers_declaring_parallelism(root)
    return (
        f"fetches <= {url.max_parallel} at a time "
        "(max_parallel; also capped by your fetcher's MAX_PARALLEL)"
        + (
            "; fetchers declaring MAX_PARALLEL > 1 (each claims its fetch() is reentrant): "
            + ", ".join(f"{stem}={n}" for stem, n in named)
            if named
            else ""
        )
    )


def _fetchers_declaring_parallelism(root: Path) -> list[tuple[str, int]]:
    """`(stem, N)` for every `.fux/fetchers/*.py` whose module-level `MAX_PARALLEL` is a literal > 1.

    [SR-LAW-4](../../records/0006_LAW-4-deterministic.md) Consequences: the laws do not
    protect against a non-reentrant fetcher, and the defence is the *declared*
    `MAX_PARALLEL`, so `doctor` names who declared one. **Read with `ast`, never
    imported** -- for the reason `_parallel_policy` gives: a fetcher is consumer
    Python and `doctor` may not execute it. A non-literal declaration is not
    named (it cannot be read without running it), and a file that does not parse
    is `fetcher optional functions`' business.
    """
    import ast

    out: list[tuple[str, int]] = []
    try:
        paths = sorted((root / FETCHERS_DIR).glob("*.py"))
    except OSError:
        return out
    # SR-PLUGINS P8: a declared fetcher package with no consumer file of its
    # name runs too, so its source is read the same way -- located, not imported.
    named = [(p.stem, p) for p in paths]
    on_disk = {stem for stem, _ in named}
    from . import plugins

    try:
        declared = plugins.declared(root)
    except FuxError:
        declared = {}
    for decl in declared.values():
        stem = decl.package.fetch
        if stem and stem not in on_disk:
            source = _package_source(decl.package.module)
            if source is not None:
                named.append((stem, source))
    for stem, path in sorted(named):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, ValueError):
            continue
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "MAX_PARALLEL" for t in node.targets
            ):
                value = node.value
                if (
                    isinstance(value, ast.Constant)
                    and isinstance(value.value, int)
                    and not isinstance(value.value, bool)
                    and value.value > fixed("fetch", "undeclared_max_parallel")
                ):
                    out.append((stem, value.value))
    return out


#: Modules a decoder has no business importing (L5: ingest is offline).
DECODER_NETWORK_MODULES = tuple(fixed("doctor", "decoder_network_modules"))


def _decoder_imports(root: Path) -> Check:
    """A `.fux/decoders/*.py` that imports a network module (SR-DECODE, W-246).

    ⚠ **A TRIPWIRE, NEVER COVERAGE.** It reads each file with `ast` (never
    imports it) and names a static `import`/`from ... import` of a module in
    `DECODER_NETWORK_MODULES` (`urllib.request`, not `urllib.parse`, which is
    string handling and which the shipped drawio decoder uses). A decoder reaching the network through
    `importlib.import_module`, `__import__`, an alias of an allowed module or
    `exec` passes. It exists to catch the careless import, not to prove a
    decoder offline; L5's real fence is the import test on the engine.
    """
    import ast

    name = "decoder imports"
    try:
        paths = sorted((root / fixed("decoders", "consumer_dir")).glob("*.py"))
    except OSError:
        paths = []
    hits: list[str] = []
    for path in paths:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, ValueError):
            continue
        found: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                # `from urllib import request` names the submodule only as an alias.
                names = [node.module, *(f"{node.module}.{a.name}" for a in node.names)]
            else:
                continue
            for mod in names:
                for banned in DECODER_NETWORK_MODULES:
                    if mod == banned or mod.startswith(banned + "."):
                        found.add(banned)
        if found:
            hits.append(f"{path.name} ({', '.join(sorted(found))})")
    if not hits:
        return Check(name, True, f"{len(paths)} decoder module(s), none statically importing a network module")
    return Check(
        name,
        False,
        "decoder(s) importing a network module: " + "; ".join(hits)
        + ". A decoder runs at ingest, which is offline by law (L5). "
        "This is a tripwire: a dynamic import is not seen",
        level="warn",
    )


def _node_reader(root: Path) -> Check:
    """Is a Node reader an earlier `fux setup` vendored still in this repository?

    🔴 **Since W-292 (Arpit, 2026-10-21) the Node reader installs from npm
    alone** — `npm install fux-engine` — and `fux setup` writes nothing for it.
    **A repository with no Node reader is the normal state**, so the row passes.
    It warns on a leftover `.fux/node/` or `.fux/fux` from a setup before then:
    a vendored bundle frozen at the version that wrote it, which nothing
    rewrites any more and which reads an index it may no longer understand.
    `fux setup` removes what it wrote; ingest never does (SR-NODE-SEARCH).

    A **warning**, never an error: Python answers without it.
    """
    from .store import fuxdir

    found = fuxdir.vendored_leftovers(root)
    if not found:
        return Check(
            "node reader", True, "none vendored - `npm install fux-engine` installs one", level="warn"
        )
    names = ", ".join(
        f"{p.relative_to(root).as_posix()}{'/' if p.is_dir() else ''}" for p in found
    )
    return Check(
        "node reader",
        False,
        f"{names} left by an earlier `fux setup` - run `fux setup` to remove "
        "(the Node reader is `npm install fux-engine` now)",
        level="warn",
    )


#: Extensions a launcher shim can have, across the platforms fux ships on.
#:
#: ⚠ **`.exe` is deliberately absent, and that is a correctness fix, not tidying**
#: (W-159). The classifier read whatever `shutil.which` returned as text with
#: `errors="replace"` and asked whether the word `node` appeared in the first
#: 512 bytes. A Windows console script IS a `.exe` — a small binary launcher —
#: and three letters occurring by chance in its bytes would have reported a
#: perfectly ordinary Python `fux` as the Node reader. A compiled binary is not
#: a shim and is never read.
_SHIM_SUFFIXES = frozenset({"", ".cmd", ".bat", ".ps1", ".mjs", ".js", ".sh"})


def _is_node_shim(path: Path) -> bool:
    """Does this launcher hand off to node? **Read, never run** (W-159).

    Doctor never executes a binary it found on PATH — that is an arbitrary
    executable chosen by the environment, and shelling out to ask what it is
    would be the diagnostic tool doing the unsafe thing it exists to warn about.

    **Two shapes, because npm writes two.** On Unix the bin is a symlink to a
    `#!/usr/bin/env node` script; on Windows it is a `fux.cmd` whose body names
    `node` — *there is no shebang there at all*, which is why "look for a
    shebang" was never the rule, only ever the Unix half of one.

    **Split out of `_fux_on_path` so it can be tested on every platform.** The
    end-to-end row needs `shutil.which` to resolve a shim, and `which` honours
    PATHEXT — so an extensionless `fux` is invisible on Windows and a `fux.cmd`
    is invisible to a Unix lookup of `fux`. Neither shape can be exercised
    end-to-end on both platforms, and the classification is the part that was
    actually wrong.
    """
    try:
        target = path.resolve()
    except OSError:
        return False
    suffix = target.suffix.lower()
    if suffix == ".mjs":
        return True
    if suffix not in _SHIM_SUFFIXES:
        return False  # a compiled launcher; not a shim, and not read as text
    try:
        head = target.read_text(encoding="utf-8", errors="replace")[: fixed("bundle", "shim_sniff_chars")]
    except OSError:
        return False
    return "node" in head


def _fux_on_path() -> Check:
    """Which `fux` does this shell resolve -- Python's, or the Node reader's?

    **SR-NODE-SEARCH R1a mitigation 3.** `npm i -g fux-engine` puts a `fux` on
    PATH beside Python's, **with a different verb set**, and whichever resolves
    first wins. So `fux ingest` can answer *"this only reads"* on a machine
    where Python fux is installed and would have worked.

    ⚠ **This row was deferred, and the reason it was deferred is gone.** R1a
    originally ruled *"No global bin ships in the first npm release"*, and the
    row was left unbuilt because nothing would shadow Python's `fux`.
    `fux-engine` 2.0.0-alpha.7 went to npm on 2026-09-12 **carrying the bin**,
    and Arpit ruled the bin stays -- so the shadowing is real and this is the
    only one of R1a's three mitigations that speaks to a person who has both
    installed and cannot tell which one they are typing. The other two
    (`--version` naming the runtime, an unsupported verb signposting) live in
    the Node half and cannot report on a Python that is not running.

    A **warning**, never an error, on the `_node_reader` precedent: having both
    installed is a legitimate setup, not a broken repo.

    **No subprocess.** Doctor never runs a binary it found on PATH -- that is
    an arbitrary executable chosen by the environment, and shelling out to it
    to ask what it is would be the diagnostic tool doing the unsafe thing it
    exists to warn about. `_is_node_shim` reads the launcher instead.

    ⚠ **Amended 2026-09-14 (W-159): this said "the shebang answers the
    question", and on Windows there is no shebang.** npm writes a `fux.cmd`
    whose body names `node`; `shutil.which` finds it, because PATHEXT is exactly
    what it resolves through. **So the row does fire on Windows for the real npm
    shape** — what could not be constructed there was the TEST's extensionless
    shim, and the item that filed this read the skipped test as evidence about
    the row. One of those was broken and it was the fixture.
    """
    import shutil

    found = shutil.which("fux")
    if found is None:
        # Not on PATH at all: someone is running `python -m fux`, or a venv
        # `fux` that PATH does not see. Nothing can shadow what is not there.
        return Check("fux on PATH", True, "no `fux` on PATH - nothing to shadow", level="warn")

    ours = Path(sys.executable).parent / Path(found).name
    try:
        if ours.exists() and Path(found).samefile(ours):
            return Check("fux on PATH", True, f"{found} (this interpreter's)", level="warn")
    except OSError:
        pass

    node_ish = _is_node_shim(Path(found))

    if not node_ish:
        return Check(
            "fux on PATH",
            True,
            f"{found} - not this interpreter's, but not the Node reader either",
            level="warn",
        )

    return Check(
        "fux on PATH",
        False,
        f"{found} is the NODE reader (fux-engine), and it resolves before "
        f"{ours} - it only READS, so write verbs will refuse. Run `fux --version` "
        "to see which you get, or call this one as `python -m fux`",
        level="warn",
    )


def _is_git_tracked(root: Path, path: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", str(path)],
            cwd=root,
            capture_output=True,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def _index_temp_ignored(root: Path) -> Check:
    """`.fux/index/<shard>.jsonl.tmp` must be gitignored (W-185, 2026-09-15).

    🔴 **Because this row exists for the repositories the fix cannot reach.**
    `.fux/.gitignore` is write-if-missing ([SR-DOTFUX](records/0102) decision
    6a: engine-owned, annotatable), so a repository set up before 2026-09-15 has
    a `.gitignore` without the line and **will never be given one**. A row is
    the only thing that reaches it.

    **What goes wrong without it.** `store/writer.py::_atomic_write` writes the
    temp file beside the shard, inside a committed directory, and `post-commit`
    defers — so a consumer's next `git add -A` overlaps a live writer, lists the
    temp file and cannot stat it::

        fatal: unable to stat '.fux/index/ad.jsonl.tmp': No such file or directory

    Measured at **2 335 failures in 3 933 `git add -A` runs** against a writer
    renaming shards, and **0 in 3 871** with the rule in place.

    ⚠ **`warn`, not `error`.** Nothing is wrong with the index, no answer is
    affected, and the failure needs a concurrent writer — a repository that
    never commits twice in a row will never see it. It is still worth a line,
    because when it does fire the message is about fux's internals and the
    consumer has no way to connect the two.
    """
    name = "index temp files ignored"
    probe = root / fuxdir.FUX_DIR / "index" / "00.jsonl.tmp"
    ignored = _is_git_ignored(root, probe)
    if ignored is None:
        return Check(name, True, "skipped (not a git checkout)")
    if ignored:
        return Check(name, True, "a write in flight cannot break a concurrent `git add`")
    return Check(
        name,
        False,
        "add `index/*.jsonl.tmp` to .fux/.gitignore - a background re-index "
        "leaves a temp file in the committed index directory, and a `git add -A` "
        "running at that moment fails with `unable to stat` (W-185)",
        level="warn",
    )


def _is_git_ignored(root: Path, path: Path) -> bool | None:
    """True/False from `git check-ignore`, or None when git can't answer."""
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", "--", str(path)],
            cwd=root,
            capture_output=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None  # 128: not a repository, or any other git failure


# --------------------------------------------------------------------------
# SR-PLUGINS: the declared packages
# --------------------------------------------------------------------------


def _plugins_declared(root: Path) -> Check:
    """`.fux/config/plugins.toml` — present, and readable (SR-PLUGINS P2).

    🔴 **One line when it is missing, with the lever** (W-289's first hazard):
    a repository without the file runs no plugin package at all, and every row
    that would list what that costs says nothing more until this one is fixed.
    """
    from . import plugins

    name = "plugins declared"
    rel = fixed("plugins", "file")
    try:
        found = plugins.read(root)
    except FuxError as exc:
        return Check(name, False, _ascii(str(exc)))
    if found is None:
        return Check(
            name, False,
            f"no {rel} - only Markdown and plain text are read: this repo declares no "
            "decoder or fetcher package. Run `fux setup`: it proposes the packages your "
            "sources need and prints the one install line",
            level="warn",
        )
    first = sum(1 for d in found.values() if d.package.first_party)
    third = len(found) - first
    listed = ", ".join(found) or "none"
    return Check(
        name, True,
        f"{len(found)} package(s) declared ({first} first-party, {third} third-party): {listed}",
    )


def _plugins_installed(root: Path) -> Check:
    """Every declared package installed at its pinned version and digest (P4),
    its dependencies declared, and HTML readable wherever a fetcher is (P10).

    **An error**, because the verb that needs the package refuses: a declared
    package that is missing or drifted is the machine drift L2 exists to stop.
    Located and hashed, never imported (L5).
    """
    from . import plugins

    name = "plugins installed"
    try:
        found = plugins.read(root)
    except FuxError:
        return Check(name, True, "skipped (the declaration does not read - see that row)", level="warn")
    if not found:
        return Check(name, True, "nothing declared", level="warn")
    problems = plugins.problems(root)
    if not problems:
        return Check(name, True, f"{len(found)} declared package(s), each installed at its pin")
    more = f" (+{len(problems) - 1} more)" if len(problems) > 1 else ""
    return Check(name, False, _ascii(problems[0]) + more)


def _plugins_undeclared(root: Path) -> Check:
    """A suffix in the configured sources that no declared package reads (P5).

    **Never silent** (SR-DECODE decision 10's *"must not silently stop indexing
    PDFs"*): a corpus that loses its PDFs looks exactly like one that never had
    any. Names the package and the count. Offline: it lists names and opens no
    file.
    """
    from . import plugins

    name = "plugins cover sources"
    try:
        found = plugins.read(root)
    except FuxError:
        return Check(name, True, "skipped (the declaration does not read - see that row)", level="warn")
    if found is None:
        return Check(name, True, f"skipped (no {fixed('plugins', 'file')} - see that row)", level="warn")
    try:
        missing = plugins.unread(root)
    except FuxError:
        return Check(name, True, "skipped (the source list does not read)", level="warn")
    if not missing:
        return Check(name, True, "every format in the sources has a declared package")
    shown = "; ".join(f"{count} {suffix} ({package})" for suffix, (count, package) in missing.items())
    packages = sorted({package for _, package in missing.values()})
    return Check(
        name, False,
        f"{len(missing)} format(s) in the sources have no declared package: {shown}. "
        f"Declare {', '.join(packages)} - `fux setup` adds them - or ignore those files",
        level="warn",
    )


def _ascii(text: str) -> str:
    """A doctor detail reaches a Windows console (SR-CLI veto 7)."""
    return text.replace("—", "-").encode("ascii", "replace").decode("ascii")


# --------------------------------------------------------------------------
# the run: every row, in the order `fux doctor` prints them
# --------------------------------------------------------------------------

#: **The order is stated here, once, for every install** (W-282). Each row is
#: `(layer, check)`: a core row always runs; a reader, writer or engine row runs
#: where that layer is installed — `fux-engine` runs every row, in this order,
#: exactly as before the split, and `fux-reader` or `fux-writer` alone run the
#: core rows and their own. `tests/test_package_layers.py` holds each name to
#: the module of the layer it claims. Every check takes the root and returns a
#: `Check`, a list of them, or `None` (a row that does not apply here).
ROWS: tuple[tuple[str, str], ...] = (
    # W-295 -- first, because every row below reads from `.fux/config/` and a
    # repo that has not run `fux setup` since the move would read as one with
    # no policy.
    ("core", "_config_files_moved"),
    ("core", "_index_not_ignored"),
    ("core", "_index_temp_ignored"),
    ("core", "_layout_declared"),
    # W-289 — the declared packages, before any row that would need one.
    ("core", "_plugins_declared"),
    ("core", "_plugins_installed"),
    ("core", "_plugins_undeclared"),
    ("core", "_output_config_health"),
    ("reader", "_journal_size"),
    ("core", "_tune_config_health"),
    ("engine", "_identifiers"),
    ("core", "_types_health"),
    ("core", "_ignore_health"),
    ("core", "_ignore_reachable"),
    ("core", "_dirs_exclusions_migrated"),
    ("writer", "_stale_redaction"),
    # W-163 — the setup-drift rows. Grouped here, after the files they read
    # have each had their own "does it load" row: a stale key set is only worth
    # reporting about a file that parses, and two rows saying different things
    # about one broken file is how a reader learns to trust neither.
    ("core", "_retired_agent_folders"),
    ("core", "_readme_current"),
    ("core", "_starter_refusals_untouched"),
    ("writer", "_seeded_copies_removable"),
    ("writer", "_frozen_keys"),
    ("core", "_unbound_types"),
    ("core", "_listed_dirs_exist"),
    ("core", "_thin_urls"),
    ("reader", "_confidence_floors"),
    ("core", "_fetcher_capabilities"),
    ("reader", "_accelerator"),
    ("core", "_node_reader"),
    ("core", "_fux_on_path_row"),
    ("writer", "_git_hooks"),
    ("core", "_section_mode"),
    ("writer", "_background_runner"),
    ("writer", "_daemon"),
    ("core", "_url_health"),
    ("core", "_acquired_health"),
    ("core", "_pinned_without_bytes"),
    ("core", "_fetcher_config_tables"),
    ("core", "_fetcher_bindings"),
    ("core", "_fetcher_routes"),
    ("core", "_pinned_fetchers"),
    ("core", "_url_decoders"),
    ("core", "_observed_types"),
    ("writer", "_register"),
    ("core", "_suspended_pins"),
    ("core", "_observers"),
    ("core", "_pii_health"),
    ("core", "_pii_timing"),
    ("core", "_refusal_health"),
    ("core", "_decoder_bindings"),
    ("core", "_decoder_imports"),
    ("writer", "_queue_no_decoder"),
    ("writer", "_meta_fields"),
    ("core", "_provenance"),
    ("core", "_recency_prior"),
    ("reader", "_no_op_priors"),
    ("reader", "_priority_keys"),
    ("reader", "_freshness_share"),
)


def run_rows(start: Path | None, installed: dict, *, progress=None) -> list[Check]:
    """Run every row this install has, in `ROWS` order.

    `installed` maps a non-core check's name to its function — what the calling
    package (`doctor`, `query.health`, `ingest.health`) could import. A core row
    is always here; a row whose layer is absent is skipped, never failed.
    """
    global _RECORDS, _PROGRESS
    _RECORDS = None
    _PROGRESS = progress
    try:
        checks = [_python_version()]
        root = find_root(start)
        if root is None:
            checks.append(Check("repo root", False, "no fux.toml or .git found above the current directory"))
            return checks
        checks += [Check("repo root", True, str(root)), _config_loads(root), _writable(root)]
        here = globals()
        for layer, name in ROWS:
            check = here[name] if layer == "core" else installed.get(name)
            if check is None:
                continue
            found = check(root)
            if found is None:
                continue
            checks.extend(found if isinstance(found, list) else [found])
    finally:
        _PROGRESS = None
    return checks


def _config_files_moved(root: Path) -> Check:
    """W-295: no policy file is still at its pre-move address `.fux/<name>.toml`.

    An **error**: every other verb refuses while one is there, and `doctor` is
    exempt from that gate only so it can name the fix. There is no fallback
    reader -- `fux setup` moves the files, byte for byte, and that is the repair.
    """
    from . import configfiles

    name = "config files at the pre-W-295 address"
    stale = configfiles.at_old_address(root)
    if not stale:
        return Check(name, True, "none - every policy file is under " + fixed("files", "config_dir"))
    exc = configfiles.moved_error(root, stale)
    return Check(name, False, str(exc))


def _writable(root: Path) -> Check:
    """Is `.fux/` writable — probed without creating it.

    🔴 **This CREATED `.fux/` until 2026-09-12** (W-140 row 7). `doctor` is
    read-only by contract — it is the first line of this record and of the
    README — and a health command that materialises the directory it is
    reporting on has already changed the answer. On a repo with no `.fux/` it
    left `.fux/` behind, and (through `maintain/daemon.py`'s path helper)
    `.fux/runtime/CACHEDIR.TAG` with it.

    **The writability question is still answered**, on the directory that
    would have to be written: `.fux/` when it exists, the repo root when it
    does not — which is exactly what `fux setup` or the next `ingest` needs.
    The probe file is removed on every path, including failure.
    """
    fux_dir = root / fixed("fuxdir", "dir")
    target = fux_dir if fux_dir.is_dir() else root
    note = "" if target == fux_dir else " (.fux/ absent — probing the repo root)"
    probe = target / ".doctor-probe"
    try:
        probe.write_text("", encoding="utf-8")
        return Check(".fux/ writable", True, str(target) + note)
    except OSError as exc:
        return Check(".fux/ writable", False, str(exc))
    finally:
        try:
            probe.unlink()
        except OSError:
            pass


def _index_not_ignored(root: Path) -> Check:
    """SR-DOTFUX: the committed index must not be git-ignored."""
    ignored = _is_git_ignored(root, root / fuxdir.FUX_DIR / "index")
    if ignored is None:
        return Check("index not gitignored", True, "skipped (not a git checkout)")
    return Check(
        "index not gitignored",
        not ignored,
        ".fux/index is committed, not derived - remove the ignore rule "
        "(a `.fux/*` blanket is the usual cause)"
        if ignored
        else "the committed index is tracked",
    )


def _layout_declared(root: Path) -> Check:
    """SR-DOTFUX: `.fux/` holds only declared entries."""
    fux_dir = root / fuxdir.FUX_DIR
    extras = sorted(p.name for p in fux_dir.iterdir() if p.name not in fuxdir.DECLARED) if fux_dir.is_dir() else []
    return Check(
        ".fux/ layout declared",
        not extras,
        f"undeclared entries: {', '.join(extras)} - see .fux/README.md and SR-DOTFUX"
        if extras
        else "every entry is declared",
        level="warn",
    )


def _fux_on_path_row(root: Path) -> Check:
    """`_fux_on_path` takes no root; this is its row."""
    return _fux_on_path()


_JSON_INDENT = fixed("json", "indent")


def render(args, checks: list[Check], blocks: dict) -> int:
    """Print the rows, or the `--json` payload, and return the exit code.

    `blocks` maps a payload key to a function of the root — the parts of the
    `--json` object beside `checks` that the calling install can compute.
    """
    exit_code = 0 if all(c.ok for c in checks if c.level == "error") else 1

    if getattr(args, "json", False):
        # W-66 Phase 4 / SR-CLI, 2026-08-22: `doctor` had no machine-readable
        # form, and a status an agent cannot parse is not a status for this
        # product's actual audience. The runner, freshness and provenance
        # blocks are lifted out beside the checks rather than left as prose
        # inside `detail`: a caller asking "is a re-index pending" or checking
        # SR-ACQUIRED's veto must not have to parse an English sentence.
        # **Absent counts and zero counts are different** — an empty object
        # means nothing was journalled, which is *unknown*, not *clean*.
        root = find_root()
        payload = {
            "ok": exit_code == 0,
            "version": __version__,
            "checks": [
                {"name": c.name, "ok": c.ok, "level": c.level, "detail": c.detail} for c in checks
            ],
        }
        if root is not None:
            for key, block in blocks.items():
                payload[key] = block(root)
        print(json.dumps(payload, indent=_JSON_INDENT, sort_keys=True))
        return exit_code

    for check in checks:
        # ASCII only — Windows' default console codepage (cp1252/"charmap")
        # can't encode U+2714/U+2717 and the process crashes on print()
        # rather than degrading; caught by CI's windows runners.
        mark = "OK" if check.ok else ("WARN" if check.level == "warn" else "FAIL")
        print(f"[{mark}] {check.name}: {check.detail}")
    return exit_code
