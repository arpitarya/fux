"""`.fux/tune.toml` — every knob that changes ORDER, and none that changes the index.

[ADR-TUNE](../../docs/adr/0038_tuning.md) is the record. What this module is:

- **The loader.** Absent, empty, or every key commented out means every
  default — no error, no warning, no file required. `$0` stays `$0`.
- **The validator.** The key set is **closed**: an unknown table or key is a
  loud error, because this is the one file that can silently change every
  answer (decision 5).
- **The weight resolver.** `[priority]` maps a source entry to a
  multiplicative, query-time weight; the **longest matching entry wins**
  (decision 8a).

## The boundary rule, which is mechanical rather than a taste

A value belongs here if and only if changing it leaves `.fux/index/`
**byte-identical** (decision 1). That is a test, not a judgement, and
`tests/test_tune_boundary.py` runs it over every key.

⚠ **`[confidence]` is the first table that changes no ORDER either** — it moves
the *band*, which is what fux says *about* an answer, never which documents come
back or in what sequence. It passes the boundary rule trivially and is here
because the rule is about the index, not about ranking
([ADR-CONFIDENCE](../../docs/adr/0045_confidence.md) decision 13, which reverses
decision 7). **The knob it exposes is a real one:** a floor low enough turns
every `weak` into `grounded`, and the guard is publication (the block emits the
floor it was judged under) plus `--no-tune`, not a clamp.

**Nothing here is read on the maintenance path.** Not by `ingest`, not by
`build`, not by the hooks. `fux ingest` never imports this module — L3 says no
maintenance output may depend on anything but the sources, and a tunable is by
definition not a source.

## Why `k1`, `b` and the field weights arrive as one `Scoring` object

They appear on both sides of one fraction. Passing them separately makes it
possible to reweight a numerator against a denominator computed under the old
weights — fux's own LUCENE-6819, which
[ADR-TUNE](../../docs/adr/0038_tuning.md) decision 6 recorded when the weights
were still baked into a committed field. `query.bm25f.Scoring` makes that
unrepresentable.

## There is no writer, deliberately

`tomllib` reads; nothing in the stdlib writes TOML, and adding a writer would
mean fux editing a file it promised never to rewrite (decision 3b). `fux tune`
**prints** what it would set and the human pastes it.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .errors import FuxError
from .query.bm25f import B, FIELD_WEIGHTS, K1, Scoring
from .query.confidence import DOC_COVERAGE_FLOOR, SEPARATION_FLOOR
from .store import TF_FIELDS

__all__ = [
    "TUNE_NAME",
    "Tune",
    "DEFAULT_TUNE",
    "load",
    "specimen",
]

#: Committed, and written once by `fux setup` (decision 2 and 3).
TUNE_NAME = ".fux/tune.toml"

#: At most this many semantic errors are reported together. One at a time
#: turns a hand-edited file into a guessing game; an unbounded list buries the
#: first one, which is usually the cause of the rest (decision 10b).
_MAX_REPORTED = 10

#: The `[bm25f]` field-weight keys ARE the field names. Ruled by Arpit
#: 2026-08-27 (W-82 §5.3 ruling 4): inside a table already named `bm25f`, a
#: `_weight` suffix is noise, and `k1`/`b` never carried one — the table was
#: internally inconsistent. `[ranking]` keeps its suffixes, where they
#: genuinely disambiguate (`archived_weight` is not `archived`).
#:
#: ⚠ **Breaking for `.fux/tune.toml` written against v2.0.0-alpha.1.**
#: `_LEGACY_FIELD_KEYS` exists only so the error can name the replacement
#: instead of reporting an unknown key; nothing reads the old spelling.
_FIELD_KEYS = tuple(TF_FIELDS)

#: Old spelling -> new, for the migration message only. Deleted once alpha.1 is
#: far enough back that nobody is carrying a file written against it.
_LEGACY_FIELD_KEYS = {f"{name}_weight": name for name in TF_FIELDS}

#: The closed key set. Table -> keys. Adding a key here is a change to
#: ADR-TUNE, not a convenience (decision 5).
_SCHEMA: dict[str, tuple[str, ...]] = {
    "bm25f": ("k1", "b", *_FIELD_KEYS),
    "ranking": (
        "archived_weight",
        "superseded_weight",
        "recency_half_life_days",
        "rerank_weight",
    ),
    "graph": (
        "damping",
        "iterations",
        "laziness",
        "hop_decay",
        "expand_limit",
        "seed_depth",
    ),
    "refer": ("budget", "per_doc_fraction", "min_passage_bytes", "max_passage_bytes"),
    "confidence": ("separation_floor", "doc_coverage_floor"),
    # `[priority]` is the one open table: its keys are the consumer's own
    # source entries, which fux cannot know in advance (decision 8).
    "priority": (),
}

_OPEN_TABLES = frozenset({"priority"})



@dataclass(frozen=True)
class Tune:
    """Every tunable, resolved. Construct via `load()`; the defaults are the engine's."""

    # [bm25f]
    k1: float = K1
    b: float = B
    field_weights: tuple[float, ...] = FIELD_WEIGHTS

    # [ranking]
    archived_weight: float = 1.0
    superseded_weight: float = 1.0
    recency_half_life_days: float = 0.0
    rerank_weight: float = 0.0


    # [graph]
    damping: float = 0.85
    iterations: int = 3
    laziness: float = 0.5
    hop_decay: float = 0.5
    expand_limit: int = 10
    seed_depth: int = 5

    # [confidence]
    #: ⚠ **The `grounded`/`weak` cutoff, and the only tunable in this class that
    #: is UNMEASURED at its default.** R10 is still owed; a repo-local value is
    #: a preference, never a calibration.
    separation_floor: float = SEPARATION_FLOOR
    #: `0.0` = the clause is off, which is a MEASURED ruling (2026-08-28), not a
    #: placeholder. At `1.0`, 19 of 50 correct answers turn `partial`.
    doc_coverage_floor: float = DOC_COVERAGE_FLOOR

    # [refer]
    budget: int = 8000
    per_doc_fraction: float = 0.5
    min_passage_bytes: int = 120
    max_passage_bytes: int = 4000

    #: `[priority]`, sorted longest-key-first so a reader can stop at the first
    #: match. **The resolution itself lives on `query.rank.Weighting`**, not
    #: here — one implementation, next to the bound that has to agree with it.
    #: This class carries the data; the scorer carries the rule.
    priority: tuple[tuple[str, float], ...] = field(default_factory=tuple)

    @property
    def scoring(self) -> Scoring:
        """The three-part BM25F parameter set, as one object."""
        return Scoring(k1=self.k1, b=self.b, weights=self.field_weights)

    @property
    def trivial(self) -> bool:
        """True when nothing was set — used to skip work, never to skip a check."""
        return self == DEFAULT_TUNE


DEFAULT_TUNE = Tune()


class _Collector:
    """Gathers semantic errors so a hand-edited file reports them together."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.errors: list[str] = []

    def add(self, message: str) -> None:
        self.errors.append(message)

    def raise_if_any(self) -> None:
        if not self.errors:
            return
        shown = self.errors[:_MAX_REPORTED]
        more = len(self.errors) - len(shown)
        tail = f"\n  ... and {more} more" if more > 0 else ""
        raise FuxError(f"{self.path}:\n  " + "\n  ".join(shown) + tail)


def _number(c: _Collector, table: str, key: str, value: object, default: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        c.add(f"[{table}] {key} must be a number (got {value!r})")
        return default
    return float(value)


def _positive(c: _Collector, table: str, key: str, value: object, default: float) -> float:
    v = _number(c, table, key, value, default)
    if v <= 0:
        c.add(f"[{table}] {key} must be greater than zero — at zero the term it scales vanishes (got {v})")
        return default
    return v


def _non_negative(c: _Collector, table: str, key: str, value: object, default: float) -> float:
    v = _number(c, table, key, value, default)
    if v < 0:
        c.add(
            f"[{table}] {key} must not be negative — a negative multiplier inverts "
            f"the ordering, which is broken rather than aggressive (got {v})"
        )
        return default
    return v


def _fraction(c: _Collector, table: str, key: str, value: object, default: float) -> float:
    v = _number(c, table, key, value, default)
    if not 0.0 <= v <= 1.0:
        c.add(
            f"[{table}] {key} must be between 0 and 1 — 0 turns the effect off "
            f"entirely, 1 applies it in full (got {v})"
        )
        return default
    return v


def _at_least(c: _Collector, table: str, key: str, value: object, default: int, floor: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        c.add(f"[{table}] {key} must be a whole number (got {value!r})")
        return default
    if value < floor:
        c.add(f"[{table}] {key} must be at least {floor} (got {value})")
        return default
    return value


def _reject_conflict_markers(path: Path, text: str) -> None:
    """A committed file that people edit will eventually carry `<<<<<<<`.

    `.fux/` has a merge story ([ADR-MERGE-DRIVER]) and this file is inside it,
    so the confusing outcome is real: `tomllib` reports an invalid-TOML syntax
    error pointing at a line that looks fine, and the actual cause is three
    lines above (decision 10c).
    """
    for marker in ("<<<<<<< ", "=======\n", ">>>>>>> "):
        if marker in text:
            raise FuxError(
                f"{path}: unresolved merge conflict — the file still carries conflict markers. "
                "Resolve it by hand and keep one side; fux never rewrites this file"
            )
            break


def load(root: Path, *, enabled: bool = True) -> Tune:
    """Read `.fux/tune.toml`. Absent, empty or all-commented means every default.

    `enabled=False` is `--no-tune`: the file is not read at all, so the answer
    is the engine's own, which is what makes *"is it me or the config?"* a
    single flag rather than an experiment (decision 11).
    """
    if not enabled:
        return DEFAULT_TUNE

    path = root / TUNE_NAME
    if not path.is_file():
        return DEFAULT_TUNE

    raw = path.read_bytes()
    # Windows editors write a BOM; `tomllib.load` reads binary and fails with a
    # decode error that names nothing useful. Windows-first fleets are in the
    # litmus, so this is stripped rather than diagnosed (decision 10c).
    text = raw.decode("utf-8-sig")
    _reject_conflict_markers(path, text)

    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise FuxError(f"{path}: invalid TOML ({exc})") from exc

    if not data:
        return DEFAULT_TUNE

    c = _Collector(path)

    if "dense" in data:
        # Removed 2026-08-25 with the embedding model and the lane it fed.
        # A bare "unknown table" error would read as a typo; this file is the
        # one place a consumer configured the lane, so it is where they find
        # out it is gone.
        raise FuxError(
            f"{path}: [dense] was REMOVED on 2026-08-25 along with the embedding model, "
            "the committed per-chunk vectors and `ask --hybrid`. The lane never earned "
            "its cost -- DENSE-CHUNK measured 0 fixed / 2 broken at every setting that "
            "fires (work/regression/2026-08-24-dense-lane-gate/). Delete the table; "
            "ranking is unchanged, because `mode` defaulted to `off`"
        )
    unknown_tables = [k for k in data if k not in _SCHEMA]
    if unknown_tables:
        raise FuxError(
            f"{path}: unknown table(s) {sorted(unknown_tables)} — known: {sorted(_SCHEMA)}. "
            "The key set is closed on purpose: this is the one file that can change "
            "every answer without changing a byte of the index, so a typo here must "
            "not fail silently"
        )
    for name, value in data.items():
        if not isinstance(value, dict):
            raise FuxError(
                f"{path}: `{name}` must be a table (a `[{name}]` section), not a bare key"
            )
        if name in _OPEN_TABLES:
            continue
        unknown_keys = [k for k in value if k not in _SCHEMA[name]]
        if unknown_keys:
            # A file written against v2.0.0-alpha.1 spelled these
            # `<field>_weight`. Reporting them as merely *unknown* would send a
            # consumer hunting for a typo in a key they copied correctly from
            # the shipped specimen, so name the rename instead.
            renamed = sorted(k for k in unknown_keys if k in _LEGACY_FIELD_KEYS)
            if name == "bm25f" and renamed:
                pairs = ", ".join(f"`{k}` -> `{_LEGACY_FIELD_KEYS[k]}`" for k in renamed)
                raise FuxError(
                    f"{path}: [bm25f] field weights lost the `_weight` suffix in "
                    f"v2.0.0-alpha.2 -- rename {pairs}. Inside a table already named "
                    f"`bm25f` the suffix was noise, and `k1`/`b` never carried one. "
                    f"`[ranking]` is unchanged and keeps its suffixes."
                )
            raise FuxError(
                f"{path}: [{name}] has unknown key(s) {sorted(unknown_keys)} — "
                f"known: {list(_SCHEMA[name])}"
            )

    bm25f = data.get("bm25f", {})
    k1 = _positive(c, "bm25f", "k1", bm25f["k1"], K1) if "k1" in bm25f else K1
    b = _fraction(c, "bm25f", "b", bm25f["b"], B) if "b" in bm25f else B
    weights = list(FIELD_WEIGHTS)
    for i, key in enumerate(_FIELD_KEYS):
        if key in bm25f:
            # Zero is legal here and means *ignore this field* — that is a
            # ranking choice, not the source exclusion decision 9a refuses.
            weights[i] = _non_negative(c, "bm25f", key, bm25f[key], FIELD_WEIGHTS[i])

    ranking = data.get("ranking", {})
    archived_weight = (
        _non_negative(c, "ranking", "archived_weight", ranking["archived_weight"], 1.0)
        if "archived_weight" in ranking
        else 1.0
    )
    superseded_weight = (
        _non_negative(c, "ranking", "superseded_weight", ranking["superseded_weight"], 1.0)
        if "superseded_weight" in ranking
        else 1.0
    )
    half_life = (
        _non_negative(
            c, "ranking", "recency_half_life_days", ranking["recency_half_life_days"], 0.0
        )
        if "recency_half_life_days" in ranking
        else 0.0
    )
    rerank_weight = (
        _non_negative(c, "ranking", "rerank_weight", ranking["rerank_weight"], 0.0)
        if "rerank_weight" in ranking
        else 0.0
    )

    graph = data.get("graph", {})
    damping = _fraction(c, "graph", "damping", graph["damping"], 0.85) if "damping" in graph else 0.85
    iterations = (
        _at_least(c, "graph", "iterations", graph["iterations"], 3, 1) if "iterations" in graph else 3
    )
    laziness = (
        _fraction(c, "graph", "laziness", graph["laziness"], 0.5) if "laziness" in graph else 0.5
    )
    hop_decay = (
        _fraction(c, "graph", "hop_decay", graph["hop_decay"], 0.5) if "hop_decay" in graph else 0.5
    )
    expand_limit = (
        _at_least(c, "graph", "expand_limit", graph["expand_limit"], 10, 1)
        if "expand_limit" in graph
        else 10
    )
    seed_depth = (
        _at_least(c, "graph", "seed_depth", graph["seed_depth"], 5, 1) if "seed_depth" in graph else 5
    )

    conf = data.get("confidence", {})
    separation_floor = (
        _fraction(c, "confidence", "separation_floor", conf["separation_floor"], SEPARATION_FLOOR)
        if "separation_floor" in conf
        else SEPARATION_FLOOR
    )
    doc_coverage_floor = (
        _fraction(
            c, "confidence", "doc_coverage_floor", conf["doc_coverage_floor"], DOC_COVERAGE_FLOOR
        )
        if "doc_coverage_floor" in conf
        else DOC_COVERAGE_FLOOR
    )

    refer = data.get("refer", {})
    budget = _at_least(c, "refer", "budget", refer["budget"], 8000, 1) if "budget" in refer else 8000
    per_doc_fraction = (
        _fraction(c, "refer", "per_doc_fraction", refer["per_doc_fraction"], 0.5)
        if "per_doc_fraction" in refer
        else 0.5
    )
    min_passage = (
        _at_least(c, "refer", "min_passage_bytes", refer["min_passage_bytes"], 120, 1)
        if "min_passage_bytes" in refer
        else 120
    )
    max_passage = (
        _at_least(c, "refer", "max_passage_bytes", refer["max_passage_bytes"], 4000, 1)
        if "max_passage_bytes" in refer
        else 4000
    )
    if min_passage >= max_passage:
        c.add(
            f"[refer] min_passage_bytes ({min_passage}) must be smaller than "
            f"max_passage_bytes ({max_passage}) — the first is the floor below which a "
            "passage is not worth citing, the second the ceiling above which it is cut"
        )
        min_passage, max_passage = 120, 4000

    priority: list[tuple[str, float]] = []
    for entry, value in data.get("priority", {}).items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            c.add(f'[priority] "{entry}" must be a number (got {value!r})')
            continue
        weight = float(value)
        if weight < 0:
            c.add(
                f'[priority] "{entry}" must not be negative — a negative multiplier '
                f"inverts the ordering, which is broken rather than aggressive (got {weight})"
            )
            continue
        if weight == 0:
            c.add(
                f'[priority] "{entry}" is zero, which means EXCLUDE — and exclusion '
                f'already has one home: prefix the entry with `!` in .fux/sources/. '
                "Two ways to do one thing is how they drift apart"
            )
            continue
        priority.append((entry, weight))
    # Longest first, so `priority_for` can return on the first match. The tie
    # case cannot occur: TOML keys are unique.
    priority.sort(key=lambda pair: (-len(pair[0]), pair[0]))

    c.raise_if_any()

    return Tune(
        k1=k1,
        b=b,
        field_weights=tuple(weights),
        archived_weight=archived_weight,
        superseded_weight=superseded_weight,
        recency_half_life_days=half_life,
        rerank_weight=rerank_weight,
        damping=damping,
        iterations=iterations,
        laziness=laziness,
        hop_decay=hop_decay,
        expand_limit=expand_limit,
        seed_depth=seed_depth,
        separation_floor=separation_floor,
        doc_coverage_floor=doc_coverage_floor,
        budget=budget,
        per_doc_fraction=per_doc_fraction,
        min_passage_bytes=min_passage,
        max_passage_bytes=max_passage,
        priority=tuple(priority),
    )


def specimen() -> str:
    """The file `fux setup` writes -- **live lines, not comments.**

    Ruled by Arpit 2026-08-27, the same ruling `.fux/sources/types` and
    `.fux/output.toml` got the same day: a file of nothing but comments is a
    menu, and a consumer should be able to read what fux will do without
    reading fux's source. Every value here is `Tune`'s own default, so a repo
    with this file and a repo without it rank identically.

    ⚠ **The cost, stated rather than hidden: the tunables FREEZE at setup.**
    `fux setup` is write-if-missing, so a later change to `K1`, `B`,
    `FIELD_WEIGHTS` or a `Tune` field reaches a repo that has never run setup
    and does not reach one that has. Same trade as `.fux/sources/types`; same
    remedy, and ADR-DOTFUX decision 6 names it -- **a loader refusal or a `fux
    doctor` check, never a rewrite.**

    ⚠ **`[priority]` stays commented, and that is not an inconsistency.** Its
    keys are the consumer's own source entries, not tunables with defaults --
    an uncommented line there would silently reweight a corpus rather than
    restate a default. Everything unlisted is already `1.0`, which IS the
    default, spelled out by the table being empty.

    One string, so the writer and `fux tune`'s output cannot drift apart, and
    the numbers are interpolated from the engine constants rather than typed,
    so the file and the behaviour cannot drift either (W-83's lesson).
    """
    d = DEFAULT_TUNE
    fields = "\n".join(
        f"{key:<23} = {FIELD_WEIGHTS[i]}" for i, key in enumerate(_FIELD_KEYS)
    )
    return f"""\
# .fux/tune.toml -- HOW results are ordered. Never WHAT is indexed.
#
# Written once by `fux setup`; fux never rewrites it. Every value here is the
# engine's own default, spelled out rather than implied: delete the file and
# nothing changes, edit a line and exactly that line changes.
#
# The rule for what may live here is mechanical: changing any value below
# leaves `.fux/index/` byte-identical. Nothing here is read by `ingest`,
# `build` or the hooks.
#
# `fux ask --no-tune` ignores this file entirely, which is the
# "is it me or the config?" switch.

[bm25f]
k1                      = {K1}      # term-frequency saturation
b                       = {B}     # length normalisation, 0 = off, 1 = full
# The five field weights, in index order. 0 means "ignore this field".
{fields}

[ranking]
archived_weight         = {d.archived_weight}   # multiplier for a source declared archived
superseded_weight       = {d.superseded_weight}   # multiplier for a document another supersedes
recency_half_life_days  = {d.recency_half_life_days}   # 0 = off; decays on the committed `mtime`
rerank_weight           = {d.rerank_weight}   # 0 = off; the proximity reranker's uplift

[graph]                         # explain / graph / path
damping      = {d.damping}
iterations   = {d.iterations}
laziness     = {d.laziness}
hop_decay    = {d.hop_decay}
expand_limit = {d.expand_limit}
seed_depth   = {d.seed_depth}

[refer]                         # answer, and the refer plane
budget            = {d.budget}       # bytes of assembled passage
per_doc_fraction  = {d.per_doc_fraction}
min_passage_bytes = {d.min_passage_bytes}
max_passage_bytes = {d.max_passage_bytes}

[confidence]                    # the BAND -- what fux says ABOUT an answer
# Neither key can move a score or an ordering. They move the band only, so
# `.fux/index/` and the result list are byte-identical either way.
#
# separation_floor: how far ahead of the runner-up the top result must be
#   before the band may read `grounded`. LOWERING THIS DOES NOT MAKE ANSWERS
#   BETTER -- it makes fux quieter about not knowing. At 0.0 nothing is ever
#   `weak`. The default is PROVISIONAL and UNMEASURED (prediction R10): it is
#   a defensible starting point, not a calibrated one.
# doc_coverage_floor: how much of the question the TOP-RANKED DOCUMENT must
#   itself contain. 0.0 = OFF, and that is a measured ruling, not an omission.
#   Measured on 50 goldens + 15 decoys: at 1.0, NINETEEN of the fifty correct
#   answers turn `partial`, and the single decoy this clause could catch sits
#   at 0.710 -- inside the goldens' range. There is no gap to pick a number in.
#
# Both floors are PUBLISHED in the confidence block, so an answer states which
# floor judged it. `fux ask --no-tune` recomputes the band at the defaults.
separation_floor   = {d.separation_floor}
doc_coverage_floor = {d.doc_coverage_floor}

[priority]
# ⚠ THE ONE TABLE THAT STAYS COMMENTED, and not for consistency's sake: these
# are not tunables with defaults. A key is a multiplicative weight per SOURCE
# ENTRY, exactly as it appears in .fux/sources/dirs or .fux/sources/urls, so
# an uncommented line here would silently REWEIGHT YOUR CORPUS rather than
# restate a default. Anything unlisted is 1.0 -- an empty table IS the
# default. When two entries both match, the LONGER one wins.
#
# Either direction is allowed and fux states the cost rather than clamping it.
# Two values are refused, and neither is a preference being denied: a negative
# weight inverts the ordering, and zero means EXCLUDE -- which already has a
# home, the `!` prefix in .fux/sources/.
#"docs/"   = 1.5
#"vendor/" = 0.3
"""
