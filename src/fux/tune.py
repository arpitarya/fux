"""`.fux/tune.toml` — every knob that changes ORDER, plus `[index]`: the two that change the index.

[SR-TUNE](../../records/0135_tuning.md) is the record. What this module is:

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
`tests/test_tune_boundary.py` runs it over every key — **except the keys of
`[index]`, which are the rule's one declared exception.**

⚠ **`[index]` — `max_phrases` and `max_table_rows` — DOES change the index.**
Ruled by Arpit 2026-09-11, moving both out of `fux.toml` (SR-TUNE decision 13).
Three things follow and none is optional:

1. **`fux ingest` reads `[index]`, through `index_limits()` and nothing else.**
   It never calls `load()`, so a bad `[bm25f]` value cannot fail an ingest or a
   hook; a bad `[index]` value does, loudly.
2. **`--no-tune` does not reach `[index]`.** `load(enabled=False)` still skips
   the file, but the index was built under these values, and `refer` decodes
   fetched bytes under them too (`decode/_limits.py`), so "ignore my tunables"
   cannot un-build what was built. `index_limits()` takes no `enabled`.
3. **The boundary test proves the exception is real** — it asserts that
   mutating an `[index]` key DOES move a committed byte after a re-ingest,
   so the table cannot quietly become a hiding place for index decisions.

⚠ **`[confidence]` is the first table that changes no ORDER either** — it moves
the *band*, which is what fux says *about* an answer, never which documents come
back or in what sequence. It passes the boundary rule trivially and is here
because the rule is about the index, not about ranking
([SR-CONFIDENCE](../../records/0141_confidence.md) decision 13, which reverses
decision 7). **The knob it exposes is a real one:** a floor low enough turns
every `weak` into `grounded`, and the guard is publication (the block emits the
floor it was judged under) plus `--no-tune`, not a clamp.

**Nothing outside `[index]` is read on the maintenance path.** Not by
`ingest`, not by `build`, not by the hooks. `[index]` is read by ingest because
it has to be: the file is committed, so `same sources + same committed tune.toml
[index] -> same index` is the L3 that holds — the shape `[decode]
max_table_rows` had while it lived in `fux.toml`.

## Why `k1`, `b` and the field weights arrive as one `Scoring` object

They appear on both sides of one fraction. Passing them separately makes it
possible to reweight a numerator against a denominator computed under the old
weights — fux's own LUCENE-6819, which
[SR-TUNE](../../records/0135_tuning.md) decision 6 recorded when the weights
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
    "DEFAULT_MAX_PHRASES",
    "DEFAULT_MAX_TABLE_ROWS",
    "INDEX_TABLE",
    "IndexLimits",
    "index_limits",
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

#: `[index] max_phrases` — how many of a document's headings are committed as
#: its `phrases`, in document order. **Display only**: `heading` tf is built
#: from every heading whatever this is (SR-EXTRACTED). **Raised 12 -> 32 on
#: 2026-09-11 (Arpit)**: at 12, 87 of 563 markdown documents in fux's own corpus
#: lost 1 055 headings, and 262 of their 1 584 slots held template headings
#: (`Context`, `Decision`) — the headings that told documents apart were the
#: ones cut. At 32, 98.2 % keep every heading for ~0.3 % more index.
DEFAULT_MAX_PHRASES = 32

#: `[index] max_table_rows` — data rows admitted from one table (per SHEET for
#: `.xlsx`). Rows past it are not decoded, not indexed and not citable
#: (SR-TABULAR). Raised 500 -> 20 000 on 2026-09-06; moved here from
#: `fux.toml [decode]` on 2026-09-11.
DEFAULT_MAX_TABLE_ROWS = 20_000

#: The one table whose keys change `.fux/index/`. Named so the boundary test
#: and `index_limits()` refer to the same thing.
INDEX_TABLE = "index"

#: The closed key set. Table -> keys. Adding a key here is a change to
#: SR-TUNE, not a convenience (decision 5).
_SCHEMA: dict[str, tuple[str, ...]] = {
    "bm25f": ("k1", "b", *_FIELD_KEYS, "anchor"),
    "ranking": ("rerank_weight", "expand_weight"),
    "graph": (
        "damping",
        "iterations",
        "laziness",
        "hop_decay",
        "expand_limit",
        "seed_depth",
        # W-161. The six `ask_*` keys are the graph tier's, and they are in the
        # `[graph]` table rather than in `[ranking]` because the walk they
        # configure is the graph plane's walk. **They do not move `fux graph`**
        # — that verb keeps `kinds = ALL_KINDS`, `link_idf_on = False`,
        # `max_hops = None`, because orientation and answering want different
        # walks and the compare doc ruled they may differ.
        "ask_boost",
        "ask_related",
        "ask_kinds",
        "ask_link_idf",
        "ask_max_hops",
        "ask_related_limit",
    ),
    "refer": ("budget", "per_doc_fraction", "min_passage_bytes", "max_passage_bytes"),
    "confidence": ("separation_floor", "doc_coverage_floor"),
    # ⚠ THE EXCEPTION TO DECISION 1 — read by ingest, changes committed bytes,
    # untouched by `--no-tune`. See the module docstring.
    INDEX_TABLE: ("max_phrases", "max_table_rows"),
    # `[priority]` is the one open table: its keys are the consumer's own
    # source entries, which fux cannot know in advance (decision 8).
    "priority": (),
}

_OPEN_TABLES = frozenset({"priority"})

#: Keys fux ITSELF shipped and then removed. `(table, key) -> the rest of the
#: sentence`, so the error names the removal and its date instead of reporting
#: an unknown key on a line the consumer copied out of fux's own specimen.
#:
#: ⚠ **Same reasoning as the `[dense]` refusal below, one level down.** A silent
#: *"unknown key"* on a key `fux setup` wrote into `.fux/tune.toml` sends
#: somebody hunting for a typo in a line they never typed. This table is the
#: only place a removal is announced, so a key leaves the schema and arrives
#: here in the same change or the removal is a trap.
#: The half of the removal message the three document priors share: the reason
#: it is safe to delete, and the measurement behind the ruling.
_PRIORS_REMOVED = (
    "Each of the three document priors shipped as a no-op, so DELETING the key "
    "changes nothing you can measure; what went is a global multiplier no single "
    "value can set correctly -- measured across 26 intent-split probes, every "
    "value that perfects current-seeking dismantles history-seeking one probe "
    "for one (work/regression/2026-09-12-priors-and-tables/VERDICT-W143.md)"
)

_REMOVED_KEYS: dict[tuple[str, str], str] = {
    ("ranking", "archived_weight"): (
        "was REMOVED on 2026-09-13 (W-152). Being retired is a FACT, not a weight. "
        "Delete the key; ranking is unchanged, because it shipped at 1.0. The FACT "
        "is untouched and already reaches you: `archived=true` in .fux/sources/dirs, "
        "the `archived` record property, the `[archived]` marker in prose output and "
        "`archived: bool` on every JSON hit -- BRANCH ON THAT. " + _PRIORS_REMOVED
    ),
    ("ranking", "recency_half_life_days"): (
        "was REMOVED on 2026-09-13 (W-152). At a half-life of a year or less it took "
        "history-seeking queries to ZERO of thirteen: a per-document decay cannot "
        "carry a per-query distinction, because `what do we do now?` and `what did we "
        "do before?` want opposite orderings out of one corpus. Delete the key; "
        "ranking is unchanged, because it shipped at 0.0 (off). `mtime` is still "
        "committed on every record and still breaks a tie in favour of the newer "
        "document. " + _PRIORS_REMOVED
    ),
    ("ranking", "superseded_weight"): (
        "was REMOVED on 2026-09-13 (W-151). Supersession is a FACT, not a weight: "
        "no multiplier decides which document supersedes another, and the only band "
        "of values that ordered a corpus sensibly had its lower edge set by an "
        "UNRELATED document -- so adding a document moved the correct value. Delete "
        "the key; ranking is unchanged, because it shipped at 1.0. The FACT is "
        "untouched: `supersedes:` in frontmatter, the `superseded` record property, "
        "the graph edge, `fux explain`, and the declared tie-break that puts a live "
        "document above a retired one at an equal score. " + _PRIORS_REMOVED
    ),
}



@dataclass(frozen=True)
class Tune:
    """Every tunable, resolved. Construct via `load()`; the defaults are the engine's."""

    # [bm25f]
    k1: float = K1
    b: float = B
    field_weights: tuple[float, ...] = FIELD_WEIGHTS
    #: W-168 step 1 — the anchor field: what other documents call this one when
    #: they link to it. **`0.0` is OFF and is the default**, per SR-RS decision
    #: 19: a ranking change ships behind a tunable at zero and is defaulted on
    #: only by a PASS on a frozen pre-registration. Unmeasured today.
    #:
    #: ⚠ **Not in `field_weights`, deliberately.** That tuple is aligned
    #: index-for-index with `TF_FIELDS`, the five fields a record COMMITS an
    #: `flen` for; anchor is folded at read time out of other documents' edges
    #: and has no committed slot. Padding it in would claim a sixth committed
    #: field and leave every `flen` one short — see `query/bm25f.py`.
    anchor_weight: float = 0.0

    # [ranking]
    #: ⚠ **Three document priors stood here and all three are GONE**, ruled by
    #: Arpit on 2026-09-13 (SR-TUNE decision 15): `superseded_weight` (W-151),
    #: then `archived_weight` and `recency_half_life_days` (W-152). Each shipped
    #: as a no-op, so nothing ranks differently; what went is three global
    #: multipliers no single value can set correctly. The FACTS they read —
    #: `archived`, `superseded`, `mtime` — are all untouched and still reach a
    #: caller.
    rerank_weight: float = 0.0
    #: W-109 — what an agent-supplied `--expand` term is worth against a term
    #: the user actually typed. **`0.2` is Query2doc's 1:5 ratio** (arXiv
    #: 2303.07678 §3.2 repeats the query five times beside one pseudo-passage),
    #: ratified by Arpit 2026-09-05 and **documented as unmeasured on this
    #: corpus until a graded run says otherwise**.
    #:
    #: ⚠ Unlike every other key in this table, this one **is a no-op unless a
    #: caller passes `--expand`** — it cannot change the ranking of a query
    #: nobody expanded. `0` turns expansion off entirely even when a caller
    #: does pass one, which is the off-switch a consumer needs when they
    #: distrust the agent writing the expansions.
    expand_weight: float = 0.2


    # [graph]
    damping: float = 0.85
    iterations: int = 3
    laziness: float = 0.5
    hop_decay: float = 0.5
    expand_limit: int = 10
    seed_depth: int = 5

    # [graph] — the W-161 graph tier on `ask`. Six keys, and the two booleans
    # at the top are the ones that exist so the pre-registration's two arms can
    # be removed independently of each other
    # (`work/regression/2026-09-14-graph-ask/PRE-REGISTRATION.md`).
    #
    # 🔴 **Both ship ON and both are UNMEASURED**, which is the state the
    # ratified compare doc puts them in, not an oversight: Arpit accepted the
    # two-tier `ask` on 2026-09-13 and the measurement needs link-dependent
    # golden questions that only Codex may author (2026-09-30). The keys are how
    # a failing arm is withdrawn without touching the other.
    #: Arm A — re-order the lexical window by `RRF(lexical rank, PPR rank)`.
    ask_boost: bool = True
    #: Arm B — the labelled `related` list of link-reached documents with no
    #: lexical match. `--no-related` is the per-call opt-out.
    ask_related: bool = True
    #: Which edge kinds the `ask` walk follows. `ref` alone by default:
    #: a `tag` edge makes the graph bipartite and one shared tag becomes a
    #: 200-document hub, which is a hub pulling unrelated documents together
    #: rather than a link anybody drew between two documents.
    ask_kinds: str = "ref"
    #: Hub damping, ON for `ask` and off for `graph`. A link everybody makes
    #: says little about the document it comes from.
    ask_link_idf: bool = True
    #: One hop. For orientation two is right; for an answer a second-hop
    #: document is a guess about a guess.
    ask_max_hops: int = 1
    #: The cap on the `related` list. `related` is a length cost on every
    #: query, including every one it never helps, which is why the
    #: pre-registration measures median length across the whole set and not
    #: across the subset the tier is for.
    ask_related_limit: int = 5

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
        return Scoring(
            k1=self.k1, b=self.b, weights=self.field_weights, anchor=self.anchor_weight
        )

    @property
    def trivial(self) -> bool:
        """True when nothing was set — used to skip work, never to skip a check."""
        return self == DEFAULT_TUNE


DEFAULT_TUNE = Tune()


@dataclass(frozen=True)
class IndexLimits:
    """`[index]`, resolved. Deliberately NOT a field of `Tune`: `Tune` is what
    `--no-tune` replaces with the defaults, and these cannot be replaced at
    query time without disagreeing with the index they built."""

    max_phrases: int = DEFAULT_MAX_PHRASES
    max_table_rows: int = DEFAULT_MAX_TABLE_ROWS


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


def _boolean(c: _Collector, table: str, key: str, value: object, default: bool) -> bool:
    """A strict boolean. `1`/`0` are refused rather than coerced.

    ⚠ **`isinstance(1, bool)` is False but `isinstance(True, int)` is True**,
    which is why every numeric validator above already excludes `bool` by name.
    This is the same fence from the other side: a consumer who writes
    `ask_boost = 1` gets told the key is a boolean, instead of getting a silent
    `True` from a file that does not say so.
    """
    if not isinstance(value, bool):
        c.add(f"[{table}] {key} must be true or false (got {value!r})")
        return default
    return value


def _edge_kinds(c: _Collector, table: str, key: str, value: object, default: str) -> str:
    """A comma-separated list of edge kinds the index actually mints.

    Validated **here**, at load, rather than where the walk runs: an unknown
    kind silently walks nothing, and a walk over no edges returns an empty
    neighbourhood that is indistinguishable from a corpus with no links. The
    same reasoning `graph --kinds` applies at the CLI boundary
    (`graph/__init__.py::_walk_parameters`), applied to the committed file.
    """
    if not isinstance(value, str):
        c.add(f"[{table}] {key} must be a string (got {value!r})")
        return default
    from .graph import walk as walk_mod

    named = [k.strip() for k in value.split(",") if k.strip()]
    if not named:
        c.add(f"[{table}] {key} names no edge kind; the kinds this index mints are "
              f"{', '.join(walk_mod.EDGE_KINDS)}")
        return default
    unknown = sorted(set(named) - set(walk_mod.EDGE_KINDS))
    if unknown:
        c.add(f"[{table}] {key} names {', '.join(unknown)}, which is not an edge kind; "
              f"the kinds this index mints are {', '.join(walk_mod.EDGE_KINDS)}")
        return default
    return ",".join(named)


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


def _index_values(c: _Collector, table: object) -> IndexLimits:
    """Validate `[index]`'s values. Shared by `load()` and `index_limits()`, so
    `fux ask` and `fux ingest` cannot disagree about what a legal value is."""
    t = table if isinstance(table, dict) else {}
    max_phrases = (
        _at_least(c, INDEX_TABLE, "max_phrases", t["max_phrases"], DEFAULT_MAX_PHRASES, 1)
        if "max_phrases" in t
        else DEFAULT_MAX_PHRASES
    )
    max_table_rows = (
        _at_least(c, INDEX_TABLE, "max_table_rows", t["max_table_rows"], DEFAULT_MAX_TABLE_ROWS, 1)
        if "max_table_rows" in t
        else DEFAULT_MAX_TABLE_ROWS
    )
    return IndexLimits(max_phrases=max_phrases, max_table_rows=max_table_rows)


def _read_text(path: Path) -> str:
    text = path.read_bytes().decode("utf-8-sig")
    _reject_conflict_markers(path, text)
    return text


def index_limits(root: Path) -> IndexLimits:
    """`[index]` alone — what `fux ingest` and the decoders read.

    **Reads only `[index]`**: a typo in `[bm25f]` is `fux ask`'s error to
    report, never a reason an ingest or a git hook fails. **Takes no
    `enabled`**: `--no-tune` does not reach these keys (module docstring).
    Absent file, absent table, absent key -> the defaults.
    """
    path = root / TUNE_NAME
    if not path.is_file():
        return IndexLimits()
    try:
        data = tomllib.loads(_read_text(path))
    except tomllib.TOMLDecodeError as exc:
        raise FuxError(f"{path}: invalid TOML ({exc})") from exc
    table = data.get(INDEX_TABLE, {})
    if not isinstance(table, dict):
        raise FuxError(f"{path}: `{INDEX_TABLE}` must be a table (a `[{INDEX_TABLE}]` section), not a bare key")
    unknown = [k for k in table if k not in _SCHEMA[INDEX_TABLE]]
    if unknown:
        raise FuxError(
            f"{path}: [{INDEX_TABLE}] has unknown key(s) {sorted(unknown)} — "
            f"known: {list(_SCHEMA[INDEX_TABLE])}"
        )
    c = _Collector(path)
    limits = _index_values(c, table)
    c.raise_if_any()
    return limits


def _reject_conflict_markers(path: Path, text: str) -> None:
    """A committed file that people edit will eventually carry `<<<<<<<`.

    `.fux/` has a merge story ([SR-MERGE-DRIVER]) and this file is inside it,
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
            "every answer without changing a byte of the index (all but [index]), so a "
            "typo here must not fail silently"
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
            # A key fux removed is named as removed. Sorted so two removed keys
            # in one table report the same one every run (L3 reaches errors too).
            removed = sorted(k for k in unknown_keys if (name, k) in _REMOVED_KEYS)
            if removed:
                raise FuxError(f"{path}: [{name}] `{removed[0]}` {_REMOVED_KEYS[(name, removed[0])]}")
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
    anchor_weight = (
        _non_negative(c, "bm25f", "anchor", bm25f["anchor"], 0.0)
        if "anchor" in bm25f
        else 0.0
    )

    ranking = data.get("ranking", {})
    rerank_weight = (
        _non_negative(c, "ranking", "rerank_weight", ranking["rerank_weight"], 0.0)
        if "rerank_weight" in ranking
        else 0.0
    )
    expand_weight = (
        _non_negative(c, "ranking", "expand_weight", ranking["expand_weight"], 0.2)
        if "expand_weight" in ranking
        else 0.2
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
    ask_boost = (
        _boolean(c, "graph", "ask_boost", graph["ask_boost"], True) if "ask_boost" in graph else True
    )
    ask_related = (
        _boolean(c, "graph", "ask_related", graph["ask_related"], True)
        if "ask_related" in graph
        else True
    )
    ask_kinds = (
        _edge_kinds(c, "graph", "ask_kinds", graph["ask_kinds"], "ref")
        if "ask_kinds" in graph
        else "ref"
    )
    ask_link_idf = (
        _boolean(c, "graph", "ask_link_idf", graph["ask_link_idf"], True)
        if "ask_link_idf" in graph
        else True
    )
    ask_max_hops = (
        _at_least(c, "graph", "ask_max_hops", graph["ask_max_hops"], 1, 1)
        if "ask_max_hops" in graph
        else 1
    )
    ask_related_limit = (
        _at_least(c, "graph", "ask_related_limit", graph["ask_related_limit"], 5, 1)
        if "ask_related_limit" in graph
        else 5
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

    # Validated here too, so `fux ask` reports a bad `[index]` value, but NOT
    # carried on `Tune` — see `IndexLimits`.
    _index_values(c, data.get(INDEX_TABLE, {}))

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
        anchor_weight=anchor_weight,
        b=b,
        field_weights=tuple(weights),
        rerank_weight=rerank_weight,
        expand_weight=expand_weight,
        damping=damping,
        iterations=iterations,
        laziness=laziness,
        hop_decay=hop_decay,
        expand_limit=expand_limit,
        seed_depth=seed_depth,
        ask_boost=ask_boost,
        ask_related=ask_related,
        ask_kinds=ask_kinds,
        ask_link_idf=ask_link_idf,
        ask_max_hops=ask_max_hops,
        ask_related_limit=ask_related_limit,
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

    Ruled by Arpit 2026-08-27, the same ruling `.fux/formats.toml` and
    `.fux/output.toml` got the same day: a file of nothing but comments is a
    menu, and a consumer should be able to read what fux will do without
    reading fux's source. Every value here is `Tune`'s own default, so a repo
    with this file and a repo without it rank identically.

    ⚠ **The cost, stated rather than hidden: the tunables FREEZE at setup.**
    `fux setup` is write-if-missing, so a later change to `K1`, `B`,
    `FIELD_WEIGHTS` or a `Tune` field reaches a repo that has never run setup
    and does not reach one that has. Same trade as `.fux/formats.toml`; same
    remedy, and SR-DOTFUX decision 6 names it -- **a loader refusal or a `fux
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
    # 🔴 **TOML spells a boolean lowercase and Python's `repr` does not**, so an
    # f-string interpolating a `bool` writes `True` — which this module's own
    # loader then refuses as an unknown bare word. The specimen is asserted
    # round-trippable by `tests/test_tune.py`; without this it would have
    # shipped a file `fux setup` writes and `fux ask` cannot read.
    ask_boost = str(d.ask_boost).lower()
    ask_related = str(d.ask_related).lower()
    ask_link_idf = str(d.ask_link_idf).lower()
    return f"""\
# .fux/tune.toml -- HOW results are ordered, plus [index]: how much of a
# document is indexed.
#
# Written once by `fux setup`; fux never rewrites it. Every value here is the
# engine's own default, spelled out rather than implied: delete the file and
# nothing changes, edit a line and exactly that line changes.
#
# The rule for every table EXCEPT [index] is mechanical: changing a value
# leaves `.fux/index/` byte-identical, and nothing in it is read by `ingest`,
# `build` or the hooks.
#
# `fux ask --no-tune` ignores this file, which is the "is it me or the
# config?" switch -- for everything EXCEPT [index], which built the index and
# cannot be un-built at query time.

[bm25f]
k1                      = {K1}      # term-frequency saturation
b                       = {B}     # length normalisation, 0 = off, 1 = full
# The five field weights, in index order. 0 means "ignore this field".
{fields}
# The sixth field is ANCHOR: what OTHER documents call this one when they link
# to it (W-168 step 1). Folded in at read time from their edges -- it is in no
# committed posting, so moving this needs no re-ingest. 0 = OFF, and off is the
# default: UNMEASURED, and it turns on only on a passing pre-registered run.
anchor                  = {d.anchor_weight}

[ranking]
rerank_weight           = {d.rerank_weight}   # 0 = off; the proximity reranker's uplift
# What an agent-supplied `--expand` term is worth against a term you typed.
# A NO-OP unless a caller passes `--expand`; 0 turns expansion off entirely.
expand_weight           = {d.expand_weight}   # Query2doc's 1:5; unmeasured on your corpus

[graph]                         # explain / graph / path
damping      = {d.damping}
iterations   = {d.iterations}
laziness     = {d.laziness}
hop_decay    = {d.hop_decay}
expand_limit = {d.expand_limit}
seed_depth   = {d.seed_depth}
# The graph tier on `ask` (W-161). The two booleans are separate so a failing
# arm can be withdrawn without touching the other; both are UNMEASURED today.
ask_boost         = {ask_boost}   # arm A: re-order the window by RRF(lexical, PPR)
ask_related       = {ask_related}   # arm B: the labelled `related` list
ask_kinds         = "{d.ask_kinds}"    # `ref` alone; a `tag` edge is a hub, not a link
ask_link_idf      = {ask_link_idf}   # hub damping, ON here and off for `fux graph`
ask_max_hops      = {d.ask_max_hops}      # one hop; a second-hop document is a guess
ask_related_limit = {d.ask_related_limit}

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

[index]                         # ⚠ CHANGES THE INDEX -- read by `fux ingest`
# The one table here that changes `.fux/index/`. Changing either key
# re-extracts every document on the next `fux ingest`, and `--no-tune` does
# not undo it.
#
# max_phrases: how many of a document's headings are committed as its
#   `phrases` -- what `fux ask` shows as sections. DISPLAY ONLY: ranking reads
#   every heading regardless. Was a hard-coded 12 until 2026-09-11; at 12,
#   template headings like `Context` filled the slots.
# max_table_rows: data rows admitted per table (per SHEET for .xlsx), header
#   never counted. Rows past it are not indexed and NOT CITABLE. Raising it
#   costs query latency: refer splits a table one passage per row, and rescore
#   is O(passages) -- ~63 ms/doc/query at 500 rows, ~2.6 s at 20 000.
max_phrases    = {DEFAULT_MAX_PHRASES}
max_table_rows = {DEFAULT_MAX_TABLE_ROWS}

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
