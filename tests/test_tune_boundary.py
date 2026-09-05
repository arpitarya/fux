"""ADR-TUNE decision 1's membership test, executed rather than asserted.

**The rule is mechanical, not a taste:** a value may live in `.fux/tune.toml`
if and only if changing it leaves `.fux/index/` **byte-identical**. Decision 1b
says that is *"enforced, not asserted: a test mutates every key in
`tune.toml`"*. This is that test.

It carries a second obligation, decision 12's: **a weight must reach the
accelerator's BOUND, not only its scorer.** W-73 closed that for the
document-level multipliers. The field weights and `k1`/`b` reopened it — they
are inputs to `block_bound` as well as to `score_record` — so the differential
law is re-checked here at *non-default* scoring, which is the only place the
divergence could appear.

**Why one module and not two.** Both questions are answered by the same
fixture, and separating them invites a future session to run one and believe it
ran the other.
"""

from __future__ import annotations

import pytest

from fux.derive import accel, build, format as fmt
from fux.query import scan
from fux.store import iter_shard_paths, term_hash, write_index
from fux.tune import TUNE_NAME, _SCHEMA, load

TOPS = (1, 5, 20)

#: One line per key, in the form the loader accepts, chosen to be FAR from the
#: default — a mutation that barely moves cannot prove a byte did not change.
#: Every key in `_SCHEMA` must appear here; `test_every_key_is_exercised`
#: fails if one is added to the record and not to this list.
MUTATIONS: dict[str, dict[str, str]] = {
    "bm25f": {
        "k1": "2.4",
        "b": "0.1",
        "body": "7.0",
        "heading": "0.25",
        "title": "11.0",
        "path": "0.0",
        "ctx": "5.5",
    },
    "ranking": {
        "archived_weight": "0.1",
        "superseded_weight": "0.2",
        "recency_half_life_days": "30.0",
        "rerank_weight": "0.75",
        # W-109. ⚠ A value that CANNOT move a committed byte for a second
        # reason on top of every other key's: nothing reads it unless a caller
        # passes `--expand`, and `fux ingest` never does.
        "expand_weight": "0.75",
    },
    "graph": {
        "damping": "0.25",
        "iterations": "9",
        "laziness": "0.9",
        "hop_decay": "0.1",
        "expand_limit": "3",
        "seed_depth": "17",
    },
    "refer": {
        "budget": "512",
        "per_doc_fraction": "0.9",
        "min_passage_bytes": "20",
        "max_passage_bytes": "900",
    },
    # ⚠ These two move the BAND, never a score or an ordering — so unlike every
    # other table here, the boundary test proves something weaker than it looks:
    # of course the index is byte-identical, nothing downstream of the band
    # exists. They are listed because `_SCHEMA` is the contract and an
    # unexercised key is an untested one, not because the proof is interesting.
    "confidence": {
        "separation_floor": "0.95",
        "doc_coverage_floor": "1.0",
    },
    "priority": {'"alpha.md"': "6.0", '"beta.md"': "0.2"},
}


def _rec(doc_id, title, flen, terms) -> dict:
    return {
        "id": doc_id,
        "src": "git",
        "loc": doc_id.removeprefix("file:"),
        "mode": "extracted",
        "meta": "plain",
        "title": title,
        "phrases": [],
        "terms": terms,
        "flen": flen,
        "edges": [],
    }


def _spread(**counts) -> list[int]:
    from fux.store import TF_FIELDS

    out = [0] * len(TF_FIELDS)
    for name, value in counts.items():
        out[TF_FIELDS.index(name)] = value
    return out


@pytest.fixture
def corpus(tmp_path):
    """Documents that disagree about WHERE their terms sit.

    Every field carries weight somewhere, so no single field weight is a no-op
    on this corpus — a mutation test over a corpus that only uses `body` would
    pass while proving nothing about the other four.
    """
    alpha, beta, gamma = (term_hash(t) for t in ("alpha", "beta", "gamma"))
    records = [
        _rec(
            "file:alpha.md",
            "Alpha",
            _spread(body=40, heading=6, title=2, path=2, ctx=8),
            {alpha: _spread(heading=4), beta: _spread(body=9)},
        ),
        _rec(
            "file:beta.md",
            "Beta",
            _spread(body=44, heading=1, title=3, path=2, ctx=1),
            {alpha: _spread(body=12), beta: _spread(title=3, ctx=5)},
        ),
        _rec(
            "file:gamma.md",
            "Gamma",
            _spread(body=12, heading=3, title=2, path=4, ctx=2),
            {gamma: _spread(path=6), alpha: _spread(ctx=4, body=1)},
        ),
    ]
    write_index(tmp_path, records)
    build(tmp_path)
    return tmp_path


def _scoring(**overrides):
    """A `Scoring` from keyword overrides — `k1`, `b` and the field names.

    ⚠ **The field keys are bare field names since 2026-08-27** (W-82 §5.3
    ruling 4 dropped the `_weight` suffix inside `[bm25f]`). This dispatched on
    `name.endswith("_weight")`, which after the rename would have matched
    nothing and silently applied **no override at all** — every sweep case
    scoring identically to the default and still passing. Dispatching on
    membership in `TF_FIELDS` makes an unknown key a `ValueError` instead.
    """
    from fux.query.bm25f import DEFAULT_SCORING
    from fux.store import TF_FIELDS

    weights = list(DEFAULT_SCORING.weights)
    for name, value in overrides.items():
        if name in TF_FIELDS:
            weights[TF_FIELDS.index(name)] = value
        elif name not in ("k1", "b"):
            raise ValueError(f"unknown scoring override {name!r} — fields: {TF_FIELDS}")
    return DEFAULT_SCORING.__class__(
        k1=overrides.get("k1", DEFAULT_SCORING.k1),
        b=overrides.get("b", DEFAULT_SCORING.b),
        weights=tuple(weights),
    )


def _index_bytes(root) -> bytes:
    """Every committed shard, order-independent. This is what L2 protects."""
    return b"".join(sorted(p.read_bytes() for p in iter_shard_paths(root)))


def _write_tune(root, table: str, key: str, value: str) -> None:
    path = root / TUNE_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"[{table}]\n{key} = {value}\n", encoding="utf-8")


# -- decision 1: the membership test -----------------------------------------


@pytest.mark.parametrize(
    ("table", "key", "value"),
    [(t, k, v) for t, keys in MUTATIONS.items() for k, v in keys.items()],
)
def test_mutating_a_key_touches_no_committed_byte(corpus, table, key, value):
    """The rule that decides what may live in this file, run per key."""
    before = _index_bytes(corpus)
    _write_tune(corpus, table, key, value)
    # The read path is exercised so the value is genuinely consumed rather
    # than merely parsed — a key that nothing reads would pass this test for
    # the wrong reason.
    scan.ask(corpus, "alpha beta", top=5)
    assert _index_bytes(corpus) == before, (
        f"[{table}] {key} changed a committed byte — it is an INDEX decision, "
        "not a tunable, and belongs in a record rather than in tune.toml"
    )


def test_every_key_is_exercised():
    """A key added to the loader and not to `MUTATIONS` is an untested key."""
    missing = [
        f"[{table}] {key}"
        for table, keys in _SCHEMA.items()
        if table != "priority"
        for key in keys
        if key not in MUTATIONS.get(table, {})
    ]
    assert not missing, f"add these to MUTATIONS: {missing}"
    assert set(MUTATIONS) == set(_SCHEMA), (set(MUTATIONS), set(_SCHEMA))


def test_mutating_a_key_needs_no_rebuild(corpus):
    """A tunable that required `fux build` would be a rebuild in disguise.

    The runtime plane stored a pre-weighted `total_wlen` until 2026-08-24,
    which made `avg_wlen` a function of the field weights on the accelerator
    path and not on the scan path. It now stores `total_flen`, raw, and this
    asserts the derived bytes stay put when a weight moves.
    """
    directory = fmt.runtime_dir(corpus)
    before = b"".join(
        sorted(
            p.read_bytes()
            for p in directory.rglob("*")
            if p.is_file() and p.name != fmt.STAMP_NAME
        )
    )
    _write_tune(corpus, "bm25f", "heading", "0.25")
    accel.ask(corpus, "alpha beta", top=5)
    after = b"".join(
        sorted(
            p.read_bytes()
            for p in directory.rglob("*")
            if p.is_file() and p.name != fmt.STAMP_NAME
        )
    )
    assert after == before


# -- decision 12: the weight must reach the BOUND ----------------------------


SCORING_SWEEP = [
    {"k1": 0.4},
    {"k1": 3.0},
    {"b": 0.0},
    {"b": 1.0},
    {"heading": 0.1},
    {"heading": 40.0},
    {"ctx": 60.0},
    {"ctx": 0.02},
    {"title": 25.0},
    {"path": 0.0},
    {"k1": 2.2, "b": 0.2, "heading": 15.0, "ctx": 30.0},
]


def _adversarial(n: int = 600) -> list[dict]:
    """A corpus on which an UNWEIGHTED block bound provably loses a document.

    Finding this shape took a parameter search, and the reason it is narrow is
    worth writing down, because it is the thing that makes a naive sweep
    useless here:

    **BM25 saturates, so the bound is insensitive to a field weight whenever
    `tf` is large.** At `tf = 90` the contribution is already within a percent
    of its `idf * (k1 + 1)` ceiling, so computing the bound at weight `1.0`
    instead of `60.0` barely moves it and nothing diverges. The gap only opens
    when weighted `tf` is comparable to `k1` — which means **small counts**.
    Every `tf` here is 1 or 2 on purpose.

    Three further properties, each of which a plausible fixture gets wrong:

    1. **`common` must be the DEFERRED term**, so its blocks are the ones
       bounded rather than opened. Terms are opened rarest-first, so it is in
       half the corpus and `rare` is in thirty documents.
    2. **`theta` must be low enough that an unseen document could clear it** —
       the `rare` documents are very long (`body = 600`), so length
       normalisation keeps their scores down.
    3. **The `common` documents must be short** (`body = 10`), so the ctx
       weight is what decides them.

    Verified by mutation: reverting `block_bound`'s `scoring` argument makes
    this diverge at `top = 20`. A fixture that does not fail under that
    mutation certifies an unsound bound as proven, which is the trap
    `tests/derive/test_differential.py` already paid for once.
    """
    rare, common = term_hash("rare"), term_hash("common")
    records = []
    for i in range(n):
        terms: dict = {}
        flen = _spread(body=100, ctx=2)
        if i < 30:
            terms[rare] = _spread(body=1)
            flen = _spread(body=600, ctx=2)
        if i % 2 == 0:
            terms[common] = _spread(ctx=1)
            flen = _spread(body=10, ctx=1)
        if not terms:
            terms[term_hash(f"filler{i}")] = _spread(body=2)
        records.append(_rec(f"file:d{i:04d}.md", f"D{i}", flen, terms))
    return records


@pytest.fixture
def adversarial(tmp_path):
    write_index(tmp_path, _adversarial())
    build(tmp_path)
    return tmp_path


@pytest.mark.parametrize("overrides", SCORING_SWEEP)
def test_the_differential_law_holds_at_every_scoring(adversarial, overrides):
    """`ask --fast` and `ask --scan` must agree at ANY configured scoring.

    This is W-73's argument on a different multiplier. The accelerator prunes
    blocks on a bound; if the bound is computed at the engine defaults while
    the scorer runs at the configured weights, a block whose document would
    have won is skipped — and the failure is silent, ordered, and plausible.

    Both directions are swept deliberately: a weight above the default makes an
    unseen document reachable that the stale ceiling says is not, and one below
    it lowers the real threshold after the pruning that used the old one.
    """
    scoring = _scoring(**overrides)
    for query in ("rare common", "common rare", "rare", "common"):
        for top in (1, 5, 20, 50):
            expected = [r.id for r in scan.ask(adversarial, query, top=top, scoring=scoring)]
            for skipping in (False, True):
                got = [
                    r.id
                    for r in accel.ask(
                        adversarial, query, top=top, skipping=skipping, scoring=scoring
                    )
                ]
                assert got == expected, (
                    f"differential broken at {overrides}: query={query!r} "
                    f"top={top} skipping={skipping}\nscan={expected}\naccel={got}"
                )


def test_the_adversarial_fixture_actually_prunes(adversarial):
    """A sweep over a corpus that never skips a block proves nothing.

    The guard that keeps the module above honest: if a future change makes
    `_cannot_reach` unreachable on this fixture, the differential sweep goes
    green while testing the unpruned path twice.
    """
    calls = {"n": 0}
    real = accel._cannot_reach

    def spy(*args, **kwargs):
        calls["n"] += 1
        return real(*args, **kwargs)

    accel._cannot_reach = spy
    try:
        accel.ask(adversarial, "rare common", top=20, skipping=True, scoring=_scoring(ctx=60.0))
    finally:
        accel._cannot_reach = real
    assert calls["n"] > 0, "the fixture never reached the pruning decision"


def test_per_source_priority_reaches_both_paths(corpus):
    """`[priority]` is a document multiplier, so it rides `Weighting` (decision 8b)."""
    from fux.query.rank import Weighting

    promoted = Weighting(priority=(("alpha.md", 40.0),))
    for top in TOPS:
        expected = [r.id for r in scan.ask(corpus, "alpha beta", top=top, weighting=promoted)]
        got = [r.id for r in accel.ask(corpus, "alpha beta", top=top, weighting=promoted)]
        assert got == expected


def test_priority_actually_moves_the_ranking(corpus):
    """A knob that changes nothing observable is not a knob."""
    from fux.query.rank import Weighting

    default = [r.id for r in scan.ask(corpus, "alpha", top=3)]
    demoted = [
        r.id
        for r in scan.ask(corpus, "alpha", top=3, weighting=Weighting(priority=(("alpha.md", 0.01),)))
    ]
    assert default != demoted, "a 100x demotion must be visible in the order"


def test_longest_matching_priority_entry_wins(corpus):
    """Order-independent resolution — the source lists are loader-sorted."""
    from fux.query.rank import Weighting

    w = Weighting(priority=(("a/b/c/", 4.0), ("a/b/", 3.0), ("a/", 2.0)))
    assert w.priority_for("a/b/c/deep.md") == 4.0
    assert w.priority_for("a/b/other.md") == 3.0
    assert w.priority_for("a/x.md") == 2.0
    assert w.priority_for("z/x.md") == 1.0


def test_priority_raises_the_bound_ceiling_but_a_demotion_does_not_lower_it(corpus):
    """`1.0` is always attainable, because an unlisted document is never scaled."""
    from fux.query.rank import Weighting

    assert Weighting(priority=(("docs/", 4.0),)).maximum == 4.0
    assert Weighting(priority=(("docs/", 0.25),)).maximum == 1.0
    assert Weighting(priority=(("docs/", 0.25),)).trivial is False


def test_the_default_tune_changes_nothing(corpus):
    """The no-op case survives: a corpus with no file orders as it always did."""
    baseline = [r.id for r in scan.ask(corpus, "alpha beta", top=5)]
    (corpus / TUNE_NAME).parent.mkdir(parents=True, exist_ok=True)
    (corpus / TUNE_NAME).write_text("", encoding="utf-8")
    assert load(corpus).trivial
    assert [r.id for r in scan.ask(corpus, "alpha beta", top=5)] == baseline
