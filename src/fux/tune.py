"""`.fux/tune.toml` — every knob that changes ORDER, plus `[index]`: the two that change the index.

[SR-TUNE](../../records/0135_tuning.md) is the record. What this module is:

- **The loader.** Every key is required. An absent file, table or key stops
  the command naming it ([L12](../../records/0014_LAW-12-values-live-in-config.md)
  decision 3) — fux holds no copy of these values in code. The shipped values
  live in one place, `templates/tune.toml.txt`, which `fux setup` writes,
  `fux doctor --fix` restores keys from, and `--no-tune` reads.
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
[index] -> same index` is the L4 that holds — the shape `[decode]
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
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from .constants import fixed
from .errors import FuxError
from .query.bm25f import Scoring
from .store import TF_FIELDS

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .query.rerank import Proximity

__all__ = [
    "TUNE_NAME",
    "Tune",
    "INDEX_TABLE",
    "IndexLimits",
    "index_limits",
    "load",
    "specimen",
    "template_text",
]

#: Committed, and written once by `fux setup` (decision 2 and 3).
TUNE_NAME = fixed("files", "tune")

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

#: The one table whose keys change `.fux/index/`. Named so the boundary test
#: and `index_limits()` refer to the same thing.
INDEX_TABLE = "index"

#: The closed key set. Table -> keys. Adding a key here is a change to
#: SR-TUNE, not a convenience (decision 5).
_SCHEMA: dict[str, tuple[str, ...]] = {
    "bm25f": ("k1", "b", *_FIELD_KEYS, "anchor"),
    "ranking": (
        "rerank_weight",
        "rerank_depth",
        "rerank_coverage_power",
        "rerank_base",
        "rerank_span",
        "rerank_adjacency",
        "expand_weight",
        "mined_weight",
        "intent_weight",
    ),
    "graph": (
        "damping",
        "iterations",
        "laziness",
        "hop_decay",
        "expand_limit",
        "seed_depth",
        "path_limit",
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
    "refer": (
        "budget",
        "per_doc_fraction",
        "min_passage_bytes",
        "max_passage_bytes",
        "citation_overhead",
        "table_rows_per_passage",
    ),
    "confidence": ("separation_floor", "doc_coverage_floor"),
    "enrich": ("self_retrieval_k",),
    # ⚠ THE EXCEPTION TO DECISION 1 — read by ingest, changes committed bytes,
    # untouched by `--no-tune`. See the module docstring.
    INDEX_TABLE: ("max_phrases", "max_table_rows"),
    # `[priority]` is the one open table: its keys are the consumer's own
    # source entries, which fux cannot know in advance (decision 8).
    "priority": (),
    # W-168 step 9 (D2): glob → document type, the consumer's own patterns.
    # Open for the same reason — fux cannot know a consumer's file names.
    "doctype": (),
}

_OPEN_TABLES = frozenset({"priority", "doctype"})

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
    ("ranking", "rm3_weight"): (
        "was REMOVED on 2026-09-27 (W-224). RM3 -- ten feedback terms borrowed "
        "from fux's own top ten -- FAILED its pre-registered run twice, on drift: "
        "every weight lost 6 to 13 questions that were right at rank 1 "
        "(work/regression/2026-09-23-rm3/VERDICT.md, "
        "work/regression/2026-09-25-rm3-boosted/VERDICT.md). Delete the key; "
        "ranking is unchanged, because it shipped at 0.0 (off). Removed a second "
        "time on 2026-10-03 (W-237): RM3 gated on a `grounded` first pass FAILED "
        "too, with no gain (work/regression/2026-09-30-rm3-grounded/VERDICT.md). "
        "Supplying the words yourself is untouched: `--expand`, weighted by "
        "`expand_weight`."
    ),
}



@dataclass(frozen=True)
class Tune:
    """Every tunable, resolved. Construct via `load()`; there are no defaults.

    [L12](../../records/0014_LAW-12-values-live-in-config.md): every field is
    read from `.fux/tune.toml`, or — under `--no-tune` — from the template
    `fux setup` writes (`src/fux/templates/tune.toml.txt`). What each value is
    and why is said beside its key in that template, once.
    """

    # [bm25f]
    k1: float
    b: float
    #: Aligned index-for-index with `TF_FIELDS`, the five fields a record
    #: COMMITS an `flen` for.
    field_weights: tuple[float, ...]
    #: W-168 step 1 — the anchor field. ⚠ **Not in `field_weights`,
    #: deliberately**: anchor is folded at read time out of other documents'
    #: edges and has no committed slot — see `query/bm25f.py`.
    anchor_weight: float

    # [ranking]
    #: ⚠ **Three document priors stood here and all three are GONE** (SR-TUNE
    #: decision 15): `superseded_weight`, `archived_weight`,
    #: `recency_half_life_days`. The FACTS they read are untouched.
    rerank_weight: float
    rerank_depth: int
    rerank_coverage_power: float
    rerank_base: float
    rerank_span: float
    rerank_adjacency: float
    #: W-109. ⚠ **A no-op unless a caller passes `--expand`.**
    expand_weight: float
    #: W-168 step 4 — a spelling the CORPUS supplies. Its own key and not
    #: `expand_weight`, because a sweep of `expand_weight` would move every
    #: caller's `--expand` too.
    mined_weight: float
    #: W-168 step 9 — the intent → doc-type prior. A document whose `[doctype]`
    #: type is the one the question's cue prefers is scaled by
    #: `1 + intent_weight`. ⚠ **Inert without a `[doctype]` table**, whatever
    #: its value.
    intent_weight: float

    # [graph]
    damping: float
    iterations: int
    laziness: float
    hop_decay: float
    expand_limit: int
    seed_depth: int
    #: How many routes `fux path` returns, best first.
    path_limit: int
    # [graph] — the W-161 graph tier on `ask`. 🔴 **Both arms are UNMEASURED.**
    ask_boost: bool
    ask_related: bool
    ask_kinds: str
    ask_link_idf: bool
    ask_max_hops: int
    ask_related_limit: int

    # [confidence]
    #: ⚠ **The only tunable here UNMEASURED at its shipped value** (R10).
    separation_floor: float
    doc_coverage_floor: float

    # [refer]
    budget: int
    per_doc_fraction: float
    min_passage_bytes: int
    max_passage_bytes: int
    citation_overhead: int
    table_rows_per_passage: int

    # [enrich]
    self_retrieval_k: int

    #: `[priority]`, sorted longest-key-first so a reader can stop at the first
    #: match. **The resolution itself lives on `query.rank.Weighting`**, not
    #: here — one implementation, next to the bound that has to agree with it.
    priority: tuple[tuple[str, float], ...]
    #: `[doctype]`, sorted longest-pattern-first, ties by code point, so the
    #: first match is the rule (`query/intent.py::type_for`).
    doctype: tuple[tuple[str, str], ...]

    @property
    def scoring(self) -> Scoring:
        """The three-part BM25F parameter set, as one object."""
        return Scoring(
            k1=self.k1, b=self.b, weights=self.field_weights, anchor=self.anchor_weight
        )

    @property
    def proximity(self) -> "Proximity":
        """The reranker's passage arithmetic — coverage power and the mix."""
        from .query.rerank import Proximity

        return Proximity(
            coverage_power=self.rerank_coverage_power,
            base=self.rerank_base,
            span=self.rerank_span,
            adjacency=self.rerank_adjacency,
        )

    def chunk_bounds(self) -> dict[str, int]:
        """`[refer]`'s three passage bounds, as `refer._chunk.chunk` takes them."""
        return {
            "min_passage_bytes": self.min_passage_bytes,
            "max_passage_bytes": self.max_passage_bytes,
            "table_rows_per_passage": self.table_rows_per_passage,
        }


@dataclass(frozen=True)
class IndexLimits:
    """`[index]`, resolved. Deliberately NOT a field of `Tune`: `Tune` is what
    `--no-tune` replaces with the template's, and these cannot be replaced at
    query time without disagreeing with the index they built."""

    max_phrases: int
    max_table_rows: int


class _Collector:
    """Gathers semantic errors so a hand-edited file reports them together."""

    def __init__(self, label: "Path | str") -> None:
        self.label = label
        self.errors: list[str] = []
        self.missing = False

    def add(self, message: str) -> None:
        self.errors.append(message)

    def absent(self, table: str, key: str) -> None:
        """L12 decision 3 — a missing key is an error that names it."""
        self.missing = True
        self.errors.append(f"[{table}] {key} is missing")

    def raise_if_any(self) -> None:
        if not self.errors:
            return
        shown = self.errors[:_MAX_REPORTED]
        more = len(self.errors) - len(shown)
        tail = f"\n  ... and {more} more" if more > 0 else ""
        if self.missing:
            tail += f"\n  {_FIX_HINT}"
        raise FuxError(f"{self.label}:\n  " + "\n  ".join(shown) + tail)


#: What a missing key's error tells the reader to do. One sentence, both
#: runtimes (`config/tune.mjs`).
_FIX_HINT = "`fux doctor --fix` writes every missing key from the template `fux setup` uses"


def _boolean(c: _Collector, table: str, key: str, value: object) -> object:
    """A strict boolean. `1`/`0` are refused rather than coerced.

    ⚠ **`isinstance(1, bool)` is False but `isinstance(True, int)` is True**,
    which is why every numeric validator already excludes `bool` by name. This
    is the same fence from the other side: a consumer who writes
    `ask_boost = 1` gets told the key is a boolean, instead of getting a silent
    `True` from a file that does not say so.
    """
    if not isinstance(value, bool):
        c.add(f"[{table}] {key} must be true or false (got {value!r})")
    return value


def _edge_kinds(c: _Collector, table: str, key: str, value: object) -> object:
    """A comma-separated list of edge kinds the index actually mints.

    Validated **here**, at load, rather than where the walk runs: an unknown
    kind silently walks nothing, and a walk over no edges returns an empty
    neighbourhood that is indistinguishable from a corpus with no links. The
    same reasoning `graph --kinds` applies at the CLI boundary
    (`graph/__init__.py::_walk_parameters`), applied to the committed file.
    """
    if not isinstance(value, str):
        c.add(f"[{table}] {key} must be a string (got {value!r})")
        return value
    from .graph import walk as walk_mod

    named = [k.strip() for k in value.split(",") if k.strip()]
    if not named:
        c.add(f"[{table}] {key} names no edge kind; the kinds this index mints are "
              f"{', '.join(walk_mod.EDGE_KINDS)}")
        return value
    unknown = sorted(set(named) - set(walk_mod.EDGE_KINDS))
    if unknown:
        c.add(f"[{table}] {key} names {', '.join(unknown)}, which is not an edge kind; "
              f"the kinds this index mints are {', '.join(walk_mod.EDGE_KINDS)}")
        return value
    return ",".join(named)


def _number(c: _Collector, table: str, key: str, value: object) -> object:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        c.add(f"[{table}] {key} must be a number (got {value!r})")
        return value
    return float(value)


def _positive(c: _Collector, table: str, key: str, value: object) -> object:
    v = _number(c, table, key, value)
    if isinstance(v, float) and v <= 0:
        c.add(f"[{table}] {key} must be greater than zero — at zero the term it scales vanishes (got {v})")
    return v


def _non_negative(c: _Collector, table: str, key: str, value: object) -> object:
    v = _number(c, table, key, value)
    if isinstance(v, float) and v < 0:
        c.add(
            f"[{table}] {key} must not be negative — a negative multiplier inverts "
            f"the ordering, which is broken rather than aggressive (got {v})"
        )
    return v


def _fraction(c: _Collector, table: str, key: str, value: object) -> object:
    v = _number(c, table, key, value)
    if isinstance(v, float) and not 0.0 <= v <= 1.0:
        c.add(
            f"[{table}] {key} must be between 0 and 1 — 0 turns the effect off "
            f"entirely, 1 applies it in full (got {v})"
        )
    return v


def _whole(c: _Collector, table: str, key: str, value: object) -> object:
    """A TOML integer, at least one. `3.0` is refused: it is not one in TOML."""
    if isinstance(value, bool) or not isinstance(value, int):
        c.add(f"[{table}] {key} must be a whole number (got {value!r})")
        return value
    if value < 1:
        c.add(f"[{table}] {key} must be at least 1 (got {value})")
    return value


def _read(c: _Collector, data: dict, table: str, key: str, check) -> object:
    """`[table] key`, validated by `check` — or recorded as missing."""
    t = data.get(table)
    if not isinstance(t, dict) or key not in t:
        c.absent(table, key)
        return None
    return check(c, table, key, t[key])


def _index_values(c: _Collector, data: dict) -> "IndexLimits":
    """Validate `[index]`'s values. Shared by `load()` and `index_limits()`, so
    `fux ask` and `fux ingest` cannot disagree about what a legal value is."""
    return IndexLimits(
        max_phrases=_read(c, data, INDEX_TABLE, "max_phrases", _whole),
        max_table_rows=_read(c, data, INDEX_TABLE, "max_table_rows", _whole),
    )


def _read_text(path: Path) -> str:
    """The file's text. Absent is an error that names it (L12 decision 3)."""
    if not path.is_file():
        raise FuxError(
            f"{path} is missing - `fux setup` writes it, and `fux doctor --fix` "
            "restores a deleted one. fux holds no copy of its values in code"
        )
    # Windows editors write a BOM; `tomllib.load` reads binary and fails with a
    # decode error that names nothing useful (decision 10c).
    text = path.read_bytes().decode("utf-8-sig")
    _reject_conflict_markers(path, text)
    return text


def _parse(text: str, label: "Path | str") -> dict:
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise FuxError(f"{label}: invalid TOML ({exc})") from exc


def index_limits(root: Path) -> IndexLimits:
    """`[index]` alone — what `fux ingest` and the decoders read.

    **Reads only `[index]`**: a typo in `[bm25f]` is `fux ask`'s error to
    report, never a reason an ingest or a git hook fails. **Takes no
    `enabled`**: `--no-tune` does not reach these keys (module docstring).
    An absent file, table or key is an error naming it.
    """
    path = root / TUNE_NAME
    data = _parse(_read_text(path), path)
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
    limits = _index_values(c, data)
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


def template_text() -> str:
    """The file `fux setup` writes — `src/fux/templates/tune.toml.txt`, verbatim.

    Also what `--no-tune` reads (L12 decision 7) and what `fux tune` prints.
    """
    return (Path(__file__).parent / "templates" / fixed("templates", "tune")).read_text(
        encoding="utf-8"
    )


#: How `--no-tune`'s source is named in an error: never the consumer's path,
#: because under `--no-tune` their file is not what was read.
_TEMPLATE_LABEL = "the packaged tune.toml template (--no-tune)"


def load(root: Path, *, enabled: bool) -> Tune:
    """Read `.fux/tune.toml` — every key required.

    `enabled=False` is `--no-tune`: the consumer's file is not read at all and
    the packaged template is read in its place, so the answer is the one a
    fresh `fux setup` would give — *"is it me or the config?"* as a single flag
    rather than an experiment (decision 11; L12 decision 7).
    """
    if not enabled:
        return _resolve(_parse(template_text(), _TEMPLATE_LABEL), _TEMPLATE_LABEL)
    path = root / TUNE_NAME
    return _resolve(_parse(_read_text(path), path), path)


def _resolve(data: dict, label: "Path | str") -> Tune:
    """Validate a parsed tune file and build the `Tune` — or raise, naming every fault."""
    if "dense" in data:
        # Removed 2026-08-25 with the embedding model and the lane it fed.
        # A bare "unknown table" error would read as a typo; this file is the
        # one place a consumer configured the lane, so it is where they find
        # out it is gone.
        raise FuxError(
            f"{label}: [dense] was REMOVED on 2026-08-25 along with the embedding model, "
            "the committed per-chunk vectors and `ask --hybrid`. The lane never earned "
            "its cost -- DENSE-CHUNK measured 0 fixed / 2 broken at every setting that "
            "fires (work/regression/2026-08-24-dense-lane-gate/). Delete the table; "
            "ranking is unchanged, because `mode` defaulted to `off`"
        )
    unknown_tables = [k for k in data if k not in _SCHEMA]
    if unknown_tables:
        raise FuxError(
            f"{label}: unknown table(s) {sorted(unknown_tables)} — known: {sorted(_SCHEMA)}. "
            "The key set is closed on purpose: this is the one file that can change "
            "every answer without changing a byte of the index (all but [index]), so a "
            "typo here must not fail silently"
        )
    for name, value in data.items():
        if not isinstance(value, dict):
            raise FuxError(
                f"{label}: `{name}` must be a table (a `[{name}]` section), not a bare key"
            )
        if name in _OPEN_TABLES:
            continue
        unknown_keys = [k for k in value if k not in _SCHEMA[name]]
        if unknown_keys:
            # A key fux removed is named as removed. Sorted so two removed keys
            # in one table report the same one every run (L4 reaches errors too).
            removed = sorted(k for k in unknown_keys if (name, k) in _REMOVED_KEYS)
            if removed:
                raise FuxError(f"{label}: [{name}] `{removed[0]}` {_REMOVED_KEYS[(name, removed[0])]}")
            # A file written against v2.0.0-alpha.1 spelled these
            # `<field>_weight`; name the rename rather than report a typo.
            renamed = sorted(k for k in unknown_keys if k in _LEGACY_FIELD_KEYS)
            if name == "bm25f" and renamed:
                pairs = ", ".join(f"`{k}` -> `{_LEGACY_FIELD_KEYS[k]}`" for k in renamed)
                raise FuxError(
                    f"{label}: [bm25f] field weights lost the `_weight` suffix in "
                    f"v2.0.0-alpha.2 -- rename {pairs}. Inside a table already named "
                    f"`bm25f` the suffix was noise, and `k1`/`b` never carried one. "
                    f"`[ranking]` is unchanged and keeps its suffixes."
                )
            raise FuxError(
                f"{label}: [{name}] has unknown key(s) {sorted(unknown_keys)} — "
                f"known: {list(_SCHEMA[name])}"
            )

    c = _Collector(label)

    def read(table: str, key: str, check) -> object:
        return _read(c, data, table, key, check)

    values: dict[str, object] = {
        "k1": read("bm25f", "k1", _positive),
        "b": read("bm25f", "b", _fraction),
        # Zero is legal for a field weight and means *ignore this field* —
        # a ranking choice, not the source exclusion decision 9a refuses.
        "field_weights": tuple(read("bm25f", key, _non_negative) for key in _FIELD_KEYS),
        "anchor_weight": read("bm25f", "anchor", _non_negative),
        "rerank_weight": read("ranking", "rerank_weight", _non_negative),
        "rerank_depth": read("ranking", "rerank_depth", _whole),
        "rerank_coverage_power": read("ranking", "rerank_coverage_power", _positive),
        "rerank_base": read("ranking", "rerank_base", _fraction),
        "rerank_span": read("ranking", "rerank_span", _fraction),
        "rerank_adjacency": read("ranking", "rerank_adjacency", _fraction),
        "expand_weight": read("ranking", "expand_weight", _non_negative),
        "mined_weight": read("ranking", "mined_weight", _non_negative),
        "intent_weight": read("ranking", "intent_weight", _non_negative),
        "damping": read("graph", "damping", _fraction),
        "iterations": read("graph", "iterations", _whole),
        "laziness": read("graph", "laziness", _fraction),
        "hop_decay": read("graph", "hop_decay", _fraction),
        "expand_limit": read("graph", "expand_limit", _whole),
        "seed_depth": read("graph", "seed_depth", _whole),
        "path_limit": read("graph", "path_limit", _whole),
        "ask_boost": read("graph", "ask_boost", _boolean),
        "ask_related": read("graph", "ask_related", _boolean),
        "ask_kinds": read("graph", "ask_kinds", _edge_kinds),
        "ask_link_idf": read("graph", "ask_link_idf", _boolean),
        "ask_max_hops": read("graph", "ask_max_hops", _whole),
        "ask_related_limit": read("graph", "ask_related_limit", _whole),
        "separation_floor": read("confidence", "separation_floor", _fraction),
        "doc_coverage_floor": read("confidence", "doc_coverage_floor", _fraction),
        "budget": read("refer", "budget", _whole),
        "per_doc_fraction": read("refer", "per_doc_fraction", _fraction),
        "min_passage_bytes": read("refer", "min_passage_bytes", _whole),
        "max_passage_bytes": read("refer", "max_passage_bytes", _whole),
        "citation_overhead": read("refer", "citation_overhead", _whole),
        "table_rows_per_passage": read("refer", "table_rows_per_passage", _whole),
        "self_retrieval_k": read("enrich", "self_retrieval_k", _whole),
    }
    low, high = values["min_passage_bytes"], values["max_passage_bytes"]
    if isinstance(low, int) and isinstance(high, int) and low >= high:
        c.add(
            f"[refer] min_passage_bytes ({low}) must be smaller than "
            f"max_passage_bytes ({high}) — the first is the floor below which a "
            "passage is not worth citing, the second the ceiling above which it is cut"
        )

    # Validated here too, so `fux ask` reports a bad `[index]` value, but NOT
    # carried on `Tune` — see `IndexLimits`.
    _index_values(c, data)

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

    from .query.intent import TYPES

    doctype: list[tuple[str, str]] = []
    for pattern, kind in data.get("doctype", {}).items():
        if not isinstance(kind, str) or kind not in TYPES:
            c.add(
                f'[doctype] "{pattern}" must be one of {sorted(TYPES)} (got {kind!r}) — '
                "the types an intent cue can prefer (src/fux/constants.toml [intent.type])"
            )
            continue
        doctype.append((pattern, kind))
    # Longest first, ties by code point: two patterns of one length can both
    # match a path, and the answer must not depend on file order (L4).
    doctype.sort(key=lambda pair: (-len(pair[0]), pair[0]))

    c.raise_if_any()
    return Tune(**values, priority=tuple(priority), doctype=tuple(doctype))


def specimen() -> str:
    """The file `fux setup` writes and `fux tune` prints — the template, verbatim.

    **Live lines, not comments** (Arpit, 2026-08-27): a consumer should be able
    to read what fux will do without reading fux's source. ⚠ **`[priority]`
    stays commented**: its keys are the consumer's own source entries, not
    values with a shipped setting.
    """
    return template_text()
