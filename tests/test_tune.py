"""`.fux/tune.toml` — the loader, the closed key set, and the two refusals.

[ADR-TUNE](../docs/adr/0038_tuning.md) is the record. The boundary rule it
turns on — *changing any key here leaves `.fux/index/` byte-identical* — has
its own module, `tests/test_tune_boundary.py`, because it needs a built corpus
and these do not.
"""

from __future__ import annotations

import pytest

from fux.errors import FuxError
from fux.query.bm25f import B, FIELD_WEIGHTS, K1
from fux.tune import DEFAULT_TUNE, TUNE_NAME, Tune, load, specimen


def _write(root, text: str):
    path = root / TUNE_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return root


# -- absent, empty, and off ---------------------------------------------------


def test_no_file_is_every_default(tmp_path):
    """The `$0` path: a corpus that configures nothing needs no file at all."""
    assert load(tmp_path) == DEFAULT_TUNE
    assert load(tmp_path).trivial


def test_an_empty_file_is_every_default(tmp_path):
    _write(tmp_path, "")
    assert load(tmp_path) == DEFAULT_TUNE


def test_an_all_comments_file_is_every_default(tmp_path):
    """What `fux setup` writes must itself parse back to the defaults.

    If the shipped specimen ever set something, every new repo would silently
    inherit a ranking nobody chose.
    """
    _write(tmp_path, specimen())
    assert load(tmp_path) == DEFAULT_TUNE


def test_no_tune_does_not_read_the_file_at_all(tmp_path):
    """`--no-tune` is the "is it me or the config?" switch (decision 11).

    It must not merely ignore the values — a file that cannot be parsed must
    not error either, or the flag would be useless in exactly the situation
    that makes someone reach for it.
    """
    _write(tmp_path, "this is not TOML at all {{{")
    assert load(tmp_path, enabled=False) == DEFAULT_TUNE
    with pytest.raises(FuxError):
        load(tmp_path)


# -- the closed key set -------------------------------------------------------


def test_an_unknown_table_is_a_loud_error(tmp_path):
    _write(tmp_path, "[rankings]\narchived_weight = 0.5\n")
    with pytest.raises(FuxError, match="unknown table"):
        load(tmp_path)


def test_an_unknown_key_is_a_loud_error_and_names_the_known_ones(tmp_path):
    _write(tmp_path, "[bm25f]\nk2 = 1.4\n")
    with pytest.raises(FuxError, match=r"unknown key.*k2") as exc:
        load(tmp_path)
    assert "k1" in str(exc.value), "the message must name what WAS available"


def test_a_bare_key_outside_a_table_is_refused(tmp_path):
    _write(tmp_path, "priority = 2\n")
    with pytest.raises(FuxError, match="must be a table"):
        load(tmp_path)


def test_priority_is_the_one_open_table(tmp_path):
    """Its keys are the consumer's own source entries; fux cannot know them."""
    _write(tmp_path, '[priority]\n"anything/at/all" = 2.0\n')
    assert load(tmp_path).priority == (("anything/at/all", 2.0),)


# -- validation ---------------------------------------------------------------


def test_k1_must_be_positive(tmp_path):
    _write(tmp_path, "[bm25f]\nk1 = 0\n")
    with pytest.raises(FuxError, match="k1 must be greater than zero"):
        load(tmp_path)


def test_b_is_a_fraction_and_the_message_says_what_the_ends_mean(tmp_path):
    _write(tmp_path, "[bm25f]\nb = 1.5\n")
    with pytest.raises(FuxError, match="0 turns the effect off") as exc:
        load(tmp_path)
    assert "between 0 and 1" in str(exc.value)


def test_a_field_weight_of_zero_is_legal_and_means_ignore_the_field(tmp_path):
    """Distinct from a `[priority]` zero, which is exclusion and is refused."""
    _write(tmp_path, "[bm25f]\nheading_weight = 0\n")
    assert load(tmp_path).field_weights[1] == 0.0


def test_a_non_integer_field_weight_is_legal(tmp_path):
    """The record refused this, on a premise W-76 Phase 1 removed.

    Decision 9a called a fractional `heading_weight` an error because it
    "breaks the accelerator's u32 block maximum". The block extrema are stored
    per field and RAW since W-76 Phase 1, and `block_bound` recombines them in
    float at query time, so nothing integral is stored any more. Amended in the
    record rather than carried as folklore.
    """
    _write(tmp_path, "[bm25f]\nheading_weight = 2.5\n")
    assert load(tmp_path).field_weights[1] == 2.5


def test_min_passage_must_be_below_max_passage(tmp_path):
    _write(tmp_path, "[refer]\nmin_passage_bytes = 5000\nmax_passage_bytes = 100\n")
    with pytest.raises(FuxError, match="must be smaller than"):
        load(tmp_path)


def test_a_bool_is_not_a_number(tmp_path):
    """`bool` is an `int` subclass in Python — `true` is not a weight."""
    _write(tmp_path, "[ranking]\narchived_weight = true\n")
    with pytest.raises(FuxError, match="must be a number"):
        load(tmp_path)


def test_semantic_errors_are_reported_together(tmp_path):
    """One at a time turns a hand-edited file into a guessing game (decision 10b)."""
    _write(tmp_path, "[bm25f]\nk1 = -1\nb = 9\n[graph]\niterations = 0\n")
    with pytest.raises(FuxError) as exc:
        load(tmp_path)
    message = str(exc.value)
    assert "k1" in message and "b" in message and "iterations" in message


def test_the_error_list_is_capped(tmp_path):
    """An unbounded list buries the first error, which is usually the cause."""
    lines = "\n".join(f'"entry-{i}" = -1' for i in range(25))
    _write(tmp_path, f"[priority]\n{lines}\n")
    with pytest.raises(FuxError, match="and 15 more"):
        load(tmp_path)


# -- the two refusals (decision 9a) -------------------------------------------


def test_a_negative_priority_is_refused_as_broken_not_as_aggressive(tmp_path):
    _write(tmp_path, '[priority]\n"docs/" = -2.0\n')
    with pytest.raises(FuxError, match="inverts the ordering"):
        load(tmp_path)


def test_a_zero_priority_is_refused_and_names_the_exclusion_prefix(tmp_path):
    """Zero means exclude, and exclusion already has exactly one home."""
    _write(tmp_path, '[priority]\n"vendor/" = 0\n')
    with pytest.raises(FuxError, match=r"prefix the entry with `!`"):
        load(tmp_path)


def test_a_large_priority_is_allowed_and_not_clamped(tmp_path):
    """Both directions are the consumer's call; fux states the cost, not a limit."""
    _write(tmp_path, '[priority]\n"docs/" = 50.0\n"vendor/" = 0.01\n')
    tune = load(tmp_path)
    assert dict(tune.priority) == {"docs/": 50.0, "vendor/": 0.01}


# -- the two built-in failure modes (decision 10c) ----------------------------


def test_a_merge_conflict_gets_its_own_message(tmp_path):
    _write(
        tmp_path,
        "[bm25f]\n<<<<<<< HEAD\nk1 = 1.2\n=======\nk1 = 1.5\n>>>>>>> theirs\n",
    )
    with pytest.raises(FuxError, match="unresolved merge conflict"):
        load(tmp_path)


def test_a_utf8_bom_is_stripped_rather_than_diagnosed(tmp_path):
    """Windows editors write them; Windows-first fleets are in the litmus."""
    path = tmp_path / TUNE_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xef\xbb\xbf[bm25f]\nk1 = 1.5\n")
    assert load(tmp_path).k1 == 1.5


def test_invalid_toml_says_so(tmp_path):
    _write(tmp_path, "[bm25f\nk1 = 1.2\n")
    with pytest.raises(FuxError, match="invalid TOML"):
        load(tmp_path)


# -- resolution ---------------------------------------------------------------


def test_scoring_carries_k1_b_and_the_weights_as_one_object(tmp_path):
    _write(tmp_path, "[bm25f]\nk1 = 1.5\nb = 0.4\ntitle_weight = 9\n")
    scoring = load(tmp_path).scoring
    assert (scoring.k1, scoring.b) == (1.5, 0.4)
    assert scoring.weights[2] == 9.0
    assert not scoring.trivial


def test_the_default_scoring_is_the_engine_default(tmp_path):
    scoring = load(tmp_path).scoring
    assert (scoring.k1, scoring.b, scoring.weights) == (K1, B, FIELD_WEIGHTS)
    assert scoring.trivial


def test_priority_is_sorted_longest_key_first(tmp_path):
    """Longest-match-wins is implemented by ordering, so the order is the contract."""
    _write(tmp_path, '[priority]\n"a/" = 2.0\n"a/b/c/" = 4.0\n"a/b/" = 3.0\n')
    assert [entry for entry, _ in load(tmp_path).priority] == ["a/b/c/", "a/b/", "a/"]


def test_an_unset_table_leaves_its_keys_at_the_defaults(tmp_path):
    """Setting one key must not reset its neighbours to zero."""
    _write(tmp_path, "[bm25f]\nk1 = 1.9\n")
    tune = load(tmp_path)
    assert tune.k1 == 1.9
    assert tune.b == DEFAULT_TUNE.b
    assert tune.field_weights == DEFAULT_TUNE.field_weights
    assert tune.budget == DEFAULT_TUNE.budget


def test_tune_is_frozen(tmp_path):
    """Two code paths must never be handed a policy that drifted between them."""
    with pytest.raises(Exception):
        load(tmp_path).k1 = 2.0  # type: ignore[misc]


def test_every_specimen_table_is_in_the_schema():
    """The file `fux setup` writes cannot contain a table the loader refuses."""
    from fux.tune import _SCHEMA

    tables = [
        line.strip().strip("[]").split("]")[0]
        for line in specimen().splitlines()
        if line.startswith("[")
    ]
    assert tables, "the specimen must actually declare tables"
    assert set(tables) == set(_SCHEMA), (set(tables), set(_SCHEMA))


def test_every_schema_key_appears_in_the_specimen():
    """A key nobody can discover is a key nobody uses (decision 4)."""
    from fux.tune import _SCHEMA

    text = specimen()
    missing = [
        f"[{table}] {key}"
        for table, keys in _SCHEMA.items()
        for key in keys
        if f"#{key}" not in text.replace(" ", "").replace("#", "#")
        and f"#{key} " not in text
        and f"#{key}=" not in text.replace(" ", "")
    ]
    assert not missing, missing


def test_the_dense_mode_set_is_closed(tmp_path):
    _write(tmp_path, '[dense]\nmode = "sometimes"\n')
    with pytest.raises(FuxError, match="mode must be one of"):
        load(tmp_path)


def test_a_tune_can_be_constructed_directly_for_tests(tmp_path):
    """The dataclass is the seam programmatic callers use; no file required."""
    tune = Tune(archived_weight=0.5, priority=(("docs/", 2.0),))
    assert tune.archived_weight == 0.5
    assert not tune.trivial
